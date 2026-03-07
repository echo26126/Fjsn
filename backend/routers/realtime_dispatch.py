from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from routers.auth import read_users_me
from schemas.auth import UserRead
from services.realtime_dispatch_service import realtime_dispatch_service


router = APIRouter()


class DispatchOrderIn(BaseModel):
    order_id: Optional[str] = None
    region: str
    product: str = "散装"
    qty_ton: float
    priority: Optional[int] = 2
    due_time: Optional[str] = ""
    source: Optional[str] = "manual"


class IngestRequest(BaseModel):
    orders: List[DispatchOrderIn]


class RecommendRequest(BaseModel):
    order_ids: Optional[List[str]] = None


class ActionRequest(BaseModel):
    reason: Optional[str] = ""


@router.post("/orders/ingest")
def ingest_orders(req: IngestRequest, current_user: UserRead = Depends(read_users_me)):
    rows = [o.model_dump() for o in req.orders]
    result = realtime_dispatch_service.ingest_orders(rows)
    result["operator"] = current_user.username
    return result


@router.get("/snapshot")
def get_snapshot(current_user: UserRead = Depends(read_users_me)):
    return realtime_dispatch_service.get_snapshot()


@router.post("/recommend")
def recommend(req: RecommendRequest, current_user: UserRead = Depends(read_users_me)):
    try:
        result = realtime_dispatch_service.recommend(order_ids=req.order_ids)
        result["operator"] = current_user.username
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成建议失败: {str(e)}")


@router.post("/recommend/{recommendation_id}/confirm")
def confirm_recommendation(recommendation_id: str, current_user: UserRead = Depends(read_users_me)):
    try:
        return realtime_dispatch_service.update_recommendation(
            recommendation_id=recommendation_id,
            status="CONFIRMED",
            operator=current_user.username,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="建议不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认失败: {str(e)}")


@router.post("/recommend/{recommendation_id}/reject")
def reject_recommendation(recommendation_id: str, req: ActionRequest, current_user: UserRead = Depends(read_users_me)):
    try:
        return realtime_dispatch_service.update_recommendation(
            recommendation_id=recommendation_id,
            status="REJECTED",
            operator=current_user.username,
            reason=req.reason or "",
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="建议不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"驳回失败: {str(e)}")
