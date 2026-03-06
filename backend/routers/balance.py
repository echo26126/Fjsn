from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import random

router = APIRouter()


@router.get("/alerts")
def get_alerts():
    return {
        "alerts": [
            {"id": 1, "level": "danger", "title": "宁德区域缺货风险",
             "description": "库存1.2万吨，低于安全库存2.0万吨，本月需求预测3.5万吨，缺口约2.3万吨",
             "created_at": "2026-03-03 08:00"},
            {"id": 2, "level": "danger", "title": "厦门基地库存高位",
             "description": "当前库存4.5万吨，库容占比90%，建议增加外发或减产",
             "created_at": "2026-03-03 08:00"},
            {"id": 3, "level": "warning", "title": "南平基地产销偏差",
             "description": "本月实际产量偏离计划-8.2%，连续两月低于计划",
             "created_at": "2026-03-02 14:30"},
            {"id": 4, "level": "warning", "title": "泉州区域价格波动",
             "description": "本月均价环比下降3.2%，利润贡献度下降",
             "created_at": "2026-03-02 10:00"},
            {"id": 5, "level": "info", "title": "龙岩基地产能利用高",
             "description": "产能利用率92%，接近上限，排产空间有限",
             "created_at": "2026-03-01 16:00"},
        ],
        "summary": {"danger": 2, "warning": 2, "info": 1},
    }


@router.get("/suggestions")
def get_suggestions():
    return {
        "suggestions": [
            {"id": 1, "type": "调配建议", "content": "将厦门基地多余库存1.5万吨调往宁德区域，解决宁德缺货风险",
             "priority": "高", "impact": 120, "status": "待确认"},
            {"id": 2, "type": "排产建议", "content": "南平基地水泥产量提升至计划的95%，补充区域供应缺口",
             "priority": "高", "impact": 85, "status": "待确认"},
            {"id": 3, "type": "减产建议", "content": "厦门基地减产5%，降低库存压力，节省库存持有成本",
             "priority": "中", "impact": 45, "status": "待确认"},
            {"id": 4, "type": "定价建议", "content": "泉州区域散装水泥价格可适当上调2%，提升利润贡献",
             "priority": "中", "impact": 36, "status": "待确认"},
        ],
        "total_profit_increase": 286,
    }


class OptimizeRequest(BaseModel):
    scenario: Optional[str] = "standard"
    params: Optional[dict] = None


@router.post("/optimize")
def run_optimize(req: OptimizeRequest):
    return {
        "status": "completed",
        "solve_time_ms": 1850,
        "objective_value": 28600,
        "allocation": [
            {"from_base": "龙岩基地", "to_region": "泉州区域", "product": "水泥", "qty": 4.2},
            {"from_base": "龙岩基地", "to_region": "厦漳区域", "product": "水泥", "qty": 3.5},
            {"from_base": "龙岩基地", "to_region": "宁德区域", "product": "水泥", "qty": 1.5},
            {"from_base": "三明基地", "to_region": "福州区域", "product": "水泥", "qty": 4.8},
            {"from_base": "三明基地", "to_region": "宁德区域", "product": "水泥", "qty": 2.0},
            {"from_base": "厦门基地", "to_region": "厦漳区域", "product": "水泥", "qty": 3.0},
            {"from_base": "南平基地", "to_region": "福州区域", "product": "水泥", "qty": 3.2},
        ],
        "constraints_analysis": {
            "binding": ["宁德区域最低保供约束", "龙岩基地产能上限"],
            "slack": ["厦门基地仓容（剩余10%）", "漳州基地产能（剩余22%）"],
        },
    }


class WhatifRequest(BaseModel):
    base: str
    delta_qty: float
    product: Optional[str] = "水泥"


@router.post("/whatif")
def run_whatif(req: WhatifRequest):
    delta = req.delta_qty
    return {
        "profit_delta": round(delta * 60 if delta > 0 else delta * 45),
        "inventory_impact": f"库存{'增加' if delta > 0 else '减少'}约{abs(delta * 0.3):.1f}万吨",
        "transport_delta": f"{'+'if delta > 0 else ''}{delta * 8:.0f}万元",
        "recommendation": "推荐" if 0 < delta <= 2 else "需谨慎",
        "explanation": f"模拟{req.base}产量{'增加' if delta > 0 else '减少'}{abs(delta)}万吨后的综合评估结果。",
    }
