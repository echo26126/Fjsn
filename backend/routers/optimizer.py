"""
运筹优化引擎路由 V2
挂载在 /api/optimizer
支持品种维度（散装/袋装）+ 两层架构（约束参数 + 权重配置）+ What-if 多因素模拟
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from services.lp_optimizer import (
    build_params, solve_lp, solve_three_scenarios,
    solve_whatif, get_default_params, PRESET_WEIGHTS, WHATIF_TEMPLATES
)

router = APIRouter()


# ── 请求体模型 ──

class WeightsModel(BaseModel):
    capacity_ratio:    Optional[float] = None
    inv_min_ratio:     Optional[float] = None
    demand_max_ratio:  Optional[float] = None
    demand_flex:       Optional[float] = None
    inventory_penalty: Optional[float] = None
    transport_penalty: Optional[float] = None


class SolveRequest(BaseModel):
    weights: Optional[dict] = None          # 第二层：权重配置
    params_override: Optional[dict] = None  # 第一层：约束参数覆盖


class ScenariosRequest(BaseModel):
    params_override: Optional[dict] = None


class AdjustmentItem(BaseModel):
    type: str                        # capacity | price | demand | prod_cost | transport
    base: Optional[str] = None       # 基地名称（capacity/prod_cost/transport 时使用）
    region: Optional[str] = None     # 区域名称（price/demand/transport 时使用）
    product: Optional[str] = None    # 品种（散装/袋装，None=全部）
    mode: Optional[str] = "abs"      # abs=绝对值变化, pct=百分比变化
    value: float = 0                 # 调整量


class WhatifRequest(BaseModel):
    adjustments: List[AdjustmentItem]
    weights: Optional[dict] = None
    params_override: Optional[dict] = None
    decompose: Optional[bool] = True  # 是否做因素贡献分解


# ── 接口 1：获取默认参数 ──
@router.get("/params")
def get_params():
    """
    返回当前优化模型的完整参数配置
    包含：约束参数（第一层）+ 权重默认值（第二层）+ 预设方案 + What-if 模板
    """
    return get_default_params()


# ── 接口 2：获取预设权重方案 ──
@router.get("/presets")
def get_presets():
    """返回保守/均衡/激进三种预设权重方案"""
    return {
        "presets": PRESET_WEIGHTS,
        "templates": WHATIF_TEMPLATES,
    }


# ── 接口 3：LP 求解（单次，自定义权重）──
@router.post("/solve")
def solve(req: SolveRequest):
    """
    运行 LP 求解器
    支持自定义权重（第二层）和约束参数覆盖（第一层）
    返回：最优调配方案 + 影子价格 + 利润分解 + 供需缺口（按品种）
    """
    try:
        params = build_params(req.params_override)
        result = solve_lp(params, weights=req.weights)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LP求解失败: {str(e)}")


# ── 接口 4：三方案对比 ──
@router.post("/scenarios")
def scenarios(req: ScenariosRequest):
    """
    同时求解保守/均衡/激进三种预设方案
    返回：三方案对比 + 详细结果
    """
    try:
        params = build_params(req.params_override)
        result = solve_three_scenarios(params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"场景对比求解失败: {str(e)}")


# ── 接口 5：What-if 多因素模拟 ──
@router.post("/whatif")
def whatif(req: WhatifRequest):
    """
    What-if 多因素联动模拟
    支持同时调整：产能/单价/需求/生产成本/运输成本
    支持多基地、多区域、多品种同时调整
    返回：利润变化 + 因素贡献分解 + 调配方案变化 + 建议
    """
    try:
        params = build_params(req.params_override)
        adjustments = [adj.model_dump() for adj in req.adjustments]
        result = solve_whatif(
            params,
            adjustments=adjustments,
            weights=req.weights,
            decompose=req.decompose if req.decompose is not None else True,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if模拟失败: {str(e)}")


# ── 接口 6：快速 What-if（使用模板）──
@router.post("/whatif/template/{template_id}")
def whatif_template(template_id: str, req: SolveRequest):
    """
    使用预设模板快速运行 What-if 模拟
    template_id: peak_demand | expand_anzha | price_up | transport_down
    """
    try:
        template = next((t for t in WHATIF_TEMPLATES if t["id"] == template_id), None)
        if not template:
            raise HTTPException(status_code=404, detail=f"模板 {template_id} 不存在")
        params = build_params(req.params_override)
        result = solve_whatif(
            params,
            adjustments=template["adjustments"],
            weights=req.weights,
            decompose=False,  # 模板调整项太多，不做分解
        )
        result["template_label"] = template["label"]
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板模拟失败: {str(e)}")