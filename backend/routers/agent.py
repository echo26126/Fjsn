import os
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from sqlalchemy.orm import Session

from services.llm_service import llm_service
from services.db_service import db_service
from services.audit_service import audit_service
from routers.auth import read_users_me
from schemas.auth import UserRead
from core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    question: str
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    answer: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    chart_type: Optional[str] = None
    error: Optional[str] = None

class AgentConfigModel(BaseModel):
    provider: str
    base_url: str
    model: str
    api_key: str
    temperature: float
    analysis_channel: str = "auto"
    sql_prompt: str
    analysis_prompt: str

class AgentApiKeyUpdate(BaseModel):
    api_key: str

def _is_llm_error(text: str) -> bool:
    return (text or "").strip().startswith("Error:")

def _fmt_num(value: Any, digits: int = 2) -> str:
    try:
        num = float(value)
    except Exception:
        num = 0.0
    text = f"{num:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text

def _missing_data_message(context: Dict[str, Any]) -> str:
    data_status = context.get("data_status") or {}
    missing_sources = list(data_status.get("missing_sources") or [])
    source_label_map = {
        "production_report": "生产日报文件",
        "sales_file": "销售明细文件",
        "orders_file": "订单明细文件",
    }
    if missing_sources:
        labels = [source_label_map.get(k, k) for k in missing_sources]
        return f"当前环境未加载业务数据文件（缺失：{'、'.join(labels)}），为避免误导已停止自动分析。请先完成数据挂载/上传，再进行问答。"
    return "当前环境暂无可用业务数据，为避免误导已停止自动分析。请先完成数据挂载/上传，再进行问答。"

def _fallback_sales_answer(question: str, context: Dict[str, Any]) -> str:
    items = list(context.get("sales_items") or [])
    if not items:
        return "模型服务暂时不可用。当前上下文未提供销售明细，请补充基地或日期后重试。"
    preferred_keys = ["invoice_customer", "order_customer", "destination", "region"]
    customer_key = "region"
    for key in preferred_keys:
        if any(str(it.get(key, "")).strip() for it in items):
            customer_key = key
            break
    agg: Dict[str, Dict[str, float]] = {}
    total_qty = 0.0
    total_amount = 0.0
    for item in items:
        name = str(item.get(customer_key) or item.get("region") or "未命名客户").strip() or "未命名客户"
        qty = float(item.get("qty") or 0.0)
        amount = float(item.get("amount") or 0.0)
        total_qty += qty
        total_amount += amount
        if name not in agg:
            agg[name] = {"qty": 0.0, "amount": 0.0}
        agg[name]["qty"] += qty
        agg[name]["amount"] += amount
    ranking = sorted(agg.items(), key=lambda x: x[1]["amount"], reverse=True)[:5]
    avg_price = (total_amount / total_qty) if total_qty > 0 else 0.0
    base_hint = str(context.get("base_hint") or "").strip() or "全部基地"
    day_hint = context.get("day_hint")
    period = f"2025-12-{int(day_hint):02d}" if isinstance(day_hint, int) and day_hint > 0 else "2025-12"
    lines = [
        f"结论：{period}（{base_hint}）销售样本共 {len(items)} 条，合计销量 {_fmt_num(total_qty)} 万吨，合计金额 {_fmt_num(total_amount)} 万元，均价约 {_fmt_num(avg_price, 0)} 元/吨。"
    ]
    if ranking:
        top_parts = [f"{name}（{_fmt_num(val['amount'])}万元）" for name, val in ranking[:3]]
        lines.append(f"关键客户（按金额）TOP3：{'、'.join(top_parts)}。")
    lines.append("关键数据点：")
    for idx, (name, val) in enumerate(ranking, start=1):
        lines.append(f"{idx}) {name}：销量 {_fmt_num(val['qty'])} 万吨，金额 {_fmt_num(val['amount'])} 万元。")
    return "\n".join(lines)

def _fallback_inventory_answer(context: Dict[str, Any]) -> str:
    rows = list(context.get("inventory_daily") or [])
    if not rows:
        return "模型服务暂时不可用。当前上下文未提供库存数据，请补充日期和基地后重试。"
    total_cement = sum(float(r.get("cement_inventory_wt") or 0.0) for r in rows)
    total_clinker = sum(float(r.get("clinker_inventory_wt") or 0.0) for r in rows)
    ranking = sorted(
        rows,
        key=lambda r: float(r.get("cement_inventory_wt") or 0.0) + float(r.get("clinker_inventory_wt") or 0.0),
        reverse=True
    )[:5]
    day = ranking[0].get("day") if ranking else "2025-12-31"
    lines = [
        f"结论：{day}库存样本显示，水泥库存合计 {_fmt_num(total_cement)} 万吨，熟料库存合计 {_fmt_num(total_clinker)} 万吨，总库存 {_fmt_num(total_cement + total_clinker)} 万吨。"
    ]
    lines.append("关键数据点：")
    for idx, row in enumerate(ranking, start=1):
        base = str(row.get("base") or "未知基地")
        cement = float(row.get("cement_inventory_wt") or 0.0)
        clinker = float(row.get("clinker_inventory_wt") or 0.0)
        lines.append(f"{idx}) {base}：水泥 {_fmt_num(cement)} 万吨，熟料 {_fmt_num(clinker)} 万吨，合计 {_fmt_num(cement + clinker)} 万吨。")
    return "\n".join(lines)

def _fallback_production_answer(context: Dict[str, Any]) -> str:
    rows = list(context.get("production_daily") or [])
    if not rows:
        return "模型服务暂时不可用。当前上下文未提供生产数据，请补充日期和基地后重试。"
    total_daily_prod = sum(float(r.get("daily_prod") or 0.0) for r in rows)
    total_month_prod = sum(float(r.get("month_prod") or r.get("actual_qty") or 0.0) for r in rows)
    avg_util = sum(float(r.get("utilization") or 0.0) for r in rows) / len(rows) if rows else 0.0
    ranking = sorted(rows, key=lambda r: float(r.get("month_prod") or r.get("actual_qty") or 0.0), reverse=True)[:5]
    period = str(rows[0].get("period") or "2025-12")
    lines = [
        f"结论：{period}生产样本合计当日产量 {_fmt_num(total_daily_prod)} 万吨，月累计产量 {_fmt_num(total_month_prod)} 万吨，平均产能利用率 {_fmt_num(avg_util, 1)}%。"
    ]
    lines.append("关键数据点：")
    for idx, row in enumerate(ranking, start=1):
        base = str(row.get("base") or "未知基地")
        month_prod = float(row.get("month_prod") or row.get("actual_qty") or 0.0)
        util = float(row.get("utilization") or 0.0)
        lines.append(f"{idx}) {base}：月累计产量 {_fmt_num(month_prod)} 万吨，产能利用率 {_fmt_num(util, 1)}%。")
    return "\n".join(lines)

def _build_local_fallback_answer(question: str, context: Dict[str, Any]) -> str:
    data_status = context.get("data_status") or {}
    text = str(question or "")
    if any(k in text for k in ["库存", "库容"]):
        if not context.get("inventory_daily"):
            return _missing_data_message(context)
        return _fallback_inventory_answer(context)
    if any(k in text for k in ["产量", "生产", "窑"]):
        if not context.get("production_daily"):
            return _missing_data_message(context)
        return _fallback_production_answer(context)
    if any(k in text for k in ["销售", "客户", "订单", "出库", "均价", "金额"]):
        if not context.get("sales_items") and not context.get("orders_summary"):
            return _missing_data_message(context)
        return _fallback_sales_answer(question, context)
    if not bool(data_status.get("ready")):
        return _missing_data_message(context)
    if context.get("sales_items"):
        return _fallback_sales_answer(question, context)
    if context.get("inventory_daily"):
        return _fallback_inventory_answer(context)
    if context.get("production_daily"):
        return _fallback_production_answer(context)
    return "模型服务暂时不可用。当前上下文数据不足，请补充具体日期、基地和指标后重试。"

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: Optional[UserRead] = Depends(read_users_me)):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        file_context = db_service.build_file_context(question)
        answer = await llm_service.answer_with_file_context(question, file_context)
        if _is_llm_error(answer):
            answer = _build_local_fallback_answer(question, file_context)
        return ChatResponse(
            answer=answer,
            sql=None,
            data=None,
            chart_type="kpi"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return ChatResponse(
            answer="抱歉，处理您的问题时出现错误。",
            error=str(e)
        )


@router.post("/chat-stream")
async def chat_stream(req: ChatRequest, current_user: Optional[UserRead] = Depends(read_users_me)):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def event_gen():
        try:
            file_context = db_service.build_file_context(question)
            answer = await llm_service.answer_with_file_context(question, file_context)
            if _is_llm_error(answer):
                answer = _build_local_fallback_answer(question, file_context)
            payload = {"type": "delta", "content": answer}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            done = {"type": "done", "sql": None, "data": [], "chart_type": "kpi"}
            yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Error processing chat stream request: {e}")
            err = {"type": "error", "message": "抱歉，处理您的问题时出现错误。"}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")

@router.get("/suggest-questions")
def suggest_questions(page: Optional[str] = None):
    base_questions = [
        "本月各基地产量排名",
        "库存最高的基地?",
        "上月出库量同比变化",
        "全省产销平衡指数",
        "哪些区域存在缺货风险?",
    ]

    page_specific = {
        "dashboard": ["各基地产能利用率排名", "本月销售额最高的区域"],
        "production": ["哪些基地产量未达计划?", "产能利用率最低的基地"],
        "inventory": ["库存低于安全线的基地", "库存周转天数排名"],
        "sales": ["各区域均价对比", "袋散比例趋势"],
    }

    questions = page_specific.get(page or "", []) + base_questions
    return {"questions": questions[:8]}

@router.get("/config", response_model=AgentConfigModel)
def get_agent_config(current_user: UserRead = Depends(read_users_me)):
    is_admin = "admin" in current_user.roles
    config = llm_service.get_config(masked=not is_admin)
    if not is_admin:
        audit_service.record(
            action="agent.config.read_denied_edit",
            operator=current_user.username,
            details={"read_only": True}
        )
    return config

@router.put("/config", response_model=AgentConfigModel)
def update_agent_config(
    payload: AgentConfigModel,
    current_user: UserRead = Depends(read_users_me)
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="仅管理员可修改智能体配置")
    
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    before = llm_service.get_config(masked=True)
    updated = llm_service.update_config(data)
    changed_fields = [k for k in ["provider", "base_url", "model", "temperature", "analysis_channel", "sql_prompt", "analysis_prompt"] if before.get(k) != updated.get(k)]
    audit_service.record(
        action="agent.config.update",
        operator=current_user.username,
        details={"changed_fields": changed_fields, "api_key_updated": bool(data.get("api_key"))}
    )
    return updated

@router.patch("/config/api-key", response_model=AgentConfigModel)
def update_agent_api_key(
    payload: AgentApiKeyUpdate,
    current_user: UserRead = Depends(read_users_me)
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="仅管理员可修改模型KEY")
    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="KEY不能为空")
    updated = llm_service.update_config({"api_key": payload.api_key.strip()})
    audit_service.record(
        action="agent.config.update_api_key",
        operator=current_user.username,
        details={"api_key_updated": True}
    )
    return updated

@router.get("/config/audit")
def get_agent_config_audit_logs(
    limit: int = 30,
    current_user: UserRead = Depends(read_users_me)
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="仅管理员可查看审计日志")
    return {"items": audit_service.list_recent(limit=min(max(limit, 1), 200))}
