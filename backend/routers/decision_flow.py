from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from routers.auth import read_users_me
from schemas.auth import UserRead
from services.decision_flow_service import decision_flow_service
from services.decision_action_config_service import decision_action_config_service


router = APIRouter()


class AlertIn(BaseModel):
    alert_id: Optional[str] = None
    alert_level: str = "P2"
    alert_type: str = "履约风险"
    alert_status: str = "新建"
    source_type: str = "auto"
    alert_title: str = ""
    alert_content: str = ""
    severity_tag: str = "警告"
    context_json: str = ""
    affected_org_name: str = ""
    sku_name: str = ""
    gap_qty_ton: float = 0
    fulfillment_rate_pred: float = 0
    recommendation_ref_id: str = ""
    owner_user: str = ""
    assignee_user: str = ""
    process_status: str = "待跟进"
    process_result: str = ""
    action_deadline: str = ""
    note: str = ""


class AlertPatch(BaseModel):
    alert_level: Optional[str] = None
    alert_type: Optional[str] = None
    alert_status: Optional[str] = None
    source_type: Optional[str] = None
    alert_title: Optional[str] = None
    alert_content: Optional[str] = None
    severity_tag: Optional[str] = None
    context_json: Optional[str] = None
    affected_org_name: Optional[str] = None
    sku_name: Optional[str] = None
    gap_qty_ton: Optional[float] = None
    fulfillment_rate_pred: Optional[float] = None
    recommendation_ref_id: Optional[str] = None
    owner_user: Optional[str] = None
    assignee_user: Optional[str] = None
    process_status: Optional[str] = None
    process_result: Optional[str] = None
    action_deadline: Optional[str] = None
    note: Optional[str] = None


class FollowupIn(BaseModel):
    action_type: str = "跟进"
    content: str
    result_status: str = ""


class RecommendationIn(BaseModel):
    recommendation_id: Optional[str] = None
    alert_id: str = ""
    recommendation_role: str = "PRIMARY"
    recommendation_summary: str = ""
    action_type: str = ""
    from_org_name: str = ""
    to_org_name: str = ""
    action_qty_ton: float = 0
    est_net_gain: float = 0
    decision_status: str = "待确认"
    decision_reason: str = ""
    decision_user: str = ""
    decision_time: str = ""


class RecommendationDecisionPatch(BaseModel):
    decision_status: str
    decision_reason: Optional[str] = ""


class AiAnalysisModel(BaseModel):
    risk: str
    root_cause: str
    plan: str
    impact: str
    suggestion: dict
    meta: dict


class ExecutionIn(BaseModel):
    execution_id: Optional[str] = None
    recommendation_id: str = ""
    status: str = "待确认"
    owner: str = ""
    plan_qty_ton: float = 0
    actual_qty_ton: float = 0
    due_date: str = ""
    note: str = ""


class ExecutionPatch(BaseModel):
    status: Optional[str] = None
    owner: Optional[str] = None
    plan_qty_ton: Optional[float] = None
    actual_qty_ton: Optional[float] = None
    due_date: Optional[str] = None
    note: Optional[str] = None


class DecisionActionConfigModel(BaseModel):
    assign_actions: list[str]
    process_actions: list[str]


@router.get("/alerts")
def list_alerts(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    _ = current_user
    rows = decision_flow_service.list_alerts(db, limit=limit)
    return {"items": rows}


@router.post("/alerts/regenerate-simulated")
def regenerate_simulated_alerts(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    rows = decision_flow_service.regenerate_simulated_alerts(db, operator=current_user.username)
    return {"items": rows, "count": len(rows), "operator": current_user.username}


@router.post("/alerts")
def create_alert(
    payload: AlertIn,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    row = decision_flow_service.create_alert(db, payload.model_dump())
    return {"item": row, "operator": current_user.username}


@router.get("/action-config")
def get_action_config(current_user: UserRead = Depends(read_users_me)):
    _ = current_user
    return decision_action_config_service.get_config()


@router.put("/action-config", response_model=DecisionActionConfigModel)
def update_action_config(
    payload: DecisionActionConfigModel,
    current_user: UserRead = Depends(read_users_me),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="仅管理员可修改动作配置")
    return decision_action_config_service.update_config(payload.model_dump())


@router.patch("/alerts/{alert_id}")
def patch_alert(
    alert_id: str,
    payload: AlertPatch,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    row = decision_flow_service.update_alert(db, alert_id, payload.model_dump())
    if not row:
        raise HTTPException(status_code=404, detail="预警不存在")
    return {"item": row, "operator": current_user.username}


@router.get("/alerts/{alert_id}/followups")
def list_alert_followups(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    _ = current_user
    rows = decision_flow_service.list_followups(db, alert_id=alert_id)
    return {"items": rows}


@router.post("/alerts/{alert_id}/followups")
def create_alert_followup(
    alert_id: str,
    payload: FollowupIn,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    row = decision_flow_service.create_followup(
        db,
        alert_id=alert_id,
        payload={
            "action_type": payload.action_type,
            "content": payload.content,
            "result_status": payload.result_status,
            "operator": current_user.username,
        },
    )
    return {"item": row, "operator": current_user.username}


@router.post("/alerts/{alert_id}/model-suggest")
def create_alert_model_suggest(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    row = decision_flow_service.create_model_recommendation(
        db,
        alert_id=alert_id,
        operator=current_user.username,
    )
    if not row:
        raise HTTPException(status_code=404, detail="预警不存在")
    return {"item": row, "operator": current_user.username}


@router.get("/alerts/{alert_id}/ai-analysis", response_model=AiAnalysisModel)
async def get_alert_ai_analysis(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    _ = current_user
    result = await decision_flow_service.build_ai_analysis(db, alert_id=alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="预警不存在")
    return result


@router.get("/recommendations")
def list_recommendations(
    alert_id: str = "",
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    _ = current_user
    rows = decision_flow_service.list_recommendations(db, alert_id=alert_id, limit=limit)
    return {"items": rows}


@router.post("/recommendations")
def create_recommendation(
    payload: RecommendationIn,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    data = payload.model_dump()
    if not data.get("decision_user"):
        data["decision_user"] = current_user.username
    row = decision_flow_service.create_recommendation(db, data)
    return {"item": row, "operator": current_user.username}


@router.patch("/recommendations/{recommendation_id}/decision")
def patch_recommendation_decision(
    recommendation_id: str,
    payload: RecommendationDecisionPatch,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    row = decision_flow_service.update_recommendation_decision(
        db,
        recommendation_id,
        {
            "decision_status": payload.decision_status,
            "decision_reason": payload.decision_reason,
            "decision_user": current_user.username,
        },
    )
    if not row:
        raise HTTPException(status_code=404, detail="建议不存在")
    return {"item": row, "operator": current_user.username}


@router.get("/executions")
def list_executions(
    recommendation_id: str = "",
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    _ = current_user
    rows = decision_flow_service.list_executions(db, recommendation_id=recommendation_id, limit=limit)
    return {"items": rows}


@router.post("/executions")
def create_execution(
    payload: ExecutionIn,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    row = decision_flow_service.create_execution(db, payload.model_dump())
    return {"item": row, "operator": current_user.username}


@router.patch("/executions/{execution_id}")
def patch_execution(
    execution_id: str,
    payload: ExecutionPatch,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(read_users_me),
):
    row = decision_flow_service.update_execution(db, execution_id, payload.model_dump())
    if not row:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return {"item": row, "operator": current_user.username}
