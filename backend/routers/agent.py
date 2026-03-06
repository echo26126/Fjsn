import os
import json
import asyncio
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
    sql_prompt: str
    analysis_prompt: str

class AgentApiKeyUpdate(BaseModel):
    api_key: str

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: Optional[UserRead] = Depends(read_users_me)):
    # Chat 接口目前允许登录用户访问，或者根据需求也可以允许匿名（如果 token 是可选的）
    # 这里假设必须登录
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # 1. Get Schema Info
        schema_info = db_service.get_schema_info()
        
        # 2. Generate SQL
        sql = await llm_service.generate_sql(question, schema_info)
        logger.info(f"Generated SQL: {sql}")
        
        # 3. Execute SQL (or Mock)
        if "CANNOT ANSWER" in sql:
            return ChatResponse(
                answer="抱歉，根据现有数据无法回答该问题。",
                sql=None
            )
            
        data = await db_service.execute_query(sql)
        logger.info(f"Query returned {len(data)} rows")
        
        # 4. Generate Answer
        if not data:
            answer = "未找到相关数据。"
        else:
            answer = await llm_service.analyze_data(question, data)
            
        return ChatResponse(
            answer=answer,
            sql=sql,
            data=data,
            chart_type="bar" if len(data) > 1 else "kpi"
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
            schema_info = db_service.get_schema_info()
            sql = await llm_service.generate_sql(question, schema_info)
            if "CANNOT ANSWER" in sql:
                payload = {"type": "delta", "content": "抱歉，根据现有数据无法回答该问题。"}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                done = {"type": "done", "sql": None, "data": [], "chart_type": "kpi"}
                yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
                return
            data = await db_service.execute_query(sql)
            answer = "未找到相关数据。" if not data else await llm_service.analyze_data(question, data)
            chunk_size = 18
            for i in range(0, len(answer), chunk_size):
                payload = {"type": "delta", "content": answer[i:i + chunk_size]}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.015)
            done = {"type": "done", "sql": sql, "data": data, "chart_type": "bar" if len(data) > 1 else "kpi"}
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
    changed_fields = [k for k in ["provider", "base_url", "model", "temperature", "sql_prompt", "analysis_prompt"] if before.get(k) != updated.get(k)]
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
