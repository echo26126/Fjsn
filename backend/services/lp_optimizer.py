"""
产销平衡 LP 优化引擎 V2
支持品种维度（散装/袋装）× 基地 × 区域 三维决策变量
两层架构：约束参数（可配置）+ 权重配置（可手工设置）
What-if 多因素联动模拟 + 因素贡献分解
基于福建水泥2025年12月真实数据
"""
import time
import copy
from typing import Optional
from pulp import (
    LpProblem, LpMaximize, LpVariable, lpSum, LpStatus,
    PULP_CBC_CMD, value
)

# ─────────────────────────────────────────────
# 维度定义
# ─────────────────────────────────────────────

BASES = ["安砂建福", "永安建福", "顺昌炼石", "福州炼石", "金银湖", "德化分公司"]
REGIONS = ["福州区域", "厦漳区域", "泉州区域", "三明区域", "南平区域", "宁德区域", "莆田区域", "龙岩区域"]
PRODUCTS = ["散装", "袋装"]

# ─────────────────────────────────────────────
# 第一层：约束参数（计算基础，可配置）
# ─────────────────────────────────────────────

# 各基地各品种月产能上限（万吨）
# 散装约占总产能60%，袋装约占40%
DEFAULT_CAPACITY = {
    "安砂建福":   {"散装": 15.0, "袋装": 10.0},
    "永安建福":   {"散装": 10.0, "袋装": 7.0},
    "顺昌炼石":   {"散装": 9.5,  "袋装": 6.5},
    "福州炼石":   {"散装": 8.5,  "袋装": 5.5},
    "金银湖":     {"散装": 2.0,  "袋装": 1.5},
    "德化分公司": {"散装": 1.0,  "袋装": 1.0},
}

# 各区域各品种需求预测（万吨/月）
# 总计：散装约42万吨，袋装约28万吨，合计70万吨
DEFAULT_DEMAND = {
    "福州区域": {"散装": 9.0,  "袋装": 6.0},
    "厦漳区域": {"散装": 7.0,  "袋装": 5.0},
    "泉州区域": {"散装": 6.0,  "袋装": 4.0},
    "三明区域": {"散装": 5.0,  "袋装": 3.0},
    "南平区域": {"散装": 3.5,  "袋装": 2.5},
    "宁德区域": {"散装": 3.0,  "袋装": 2.0},
    "莆田区域": {"散装": 2.5,  "袋装": 1.5},
    "龙岩区域": {"散装": 6.0,  "袋装": 4.0},
}

# 各区域各品种最低保供量（万吨）
DEFAULT_MIN_SUPPLY = {
    "福州区域": {"散装": 6.0,  "袋装": 4.0},
    "厦漳区域": {"散装": 5.0,  "袋装": 3.0},
    "泉州区域": {"散装": 4.0,  "袋装": 3.0},
    "三明区域": {"散装": 3.0,  "袋装": 2.0},
    "南平区域": {"散装": 2.0,  "袋装": 1.0},
    "宁德区域": {"散装": 1.5,  "袋装": 0.5},
    "莆田区域": {"散装": 1.5,  "袋装": 0.5},
    "龙岩区域": {"散装": 4.0,  "袋装": 2.0},
}

# 各区域各品种售价（元/吨）
# 袋装比散装高约35~40元/吨（包装溢价）
DEFAULT_PRICE = {
    "福州区域": {"散装": 375, "袋装": 415},
    "厦漳区域": {"散装": 355, "袋装": 395},
    "泉州区域": {"散装": 365, "袋装": 405},
    "三明区域": {"散装": 345, "袋装": 385},
    "南平区域": {"散装": 340, "袋装": 380},
    "宁德区域": {"散装": 350, "袋装": 390},
    "莆田区域": {"散装": 360, "袋装": 400},
    "龙岩区域": {"散装": 335, "袋装": 375},
}

# 各基地各品种生产成本（元/吨）
# 袋装比散装高约12元/吨（包装材料+人工）
DEFAULT_PROD_COST = {
    "安砂建福":   {"散装": 278, "袋装": 290},
    "永安建福":   {"散装": 273, "袋装": 285},
    "顺昌炼石":   {"散装": 283, "袋装": 295},
    "福州炼石":   {"散装": 288, "袋装": 300},
    "金银湖":     {"散装": 293, "袋装": 305},
    "德化分公司": {"散装": 298, "袋装": 310},
}

# 运输成本矩阵（元/吨）—— 基础运费，不区分品种
DEFAULT_TRANSPORT_COST = {
    "安砂建福": {
        "福州区域": 25, "厦漳区域": 45, "泉州区域": 40,
        "三明区域": 5,  "南平区域": 20, "宁德区域": 35,
        "莆田区域": 30, "龙岩区域": 35,
    },
    "永安建福": {
        "福州区域": 30, "厦漳区域": 40, "泉州区域": 35,
        "三明区域": 8,  "南平区域": 25, "宁德区域": 40,
        "莆田区域": 28, "龙岩区域": 30,
    },
    "顺昌炼石": {
        "福州区域": 20, "厦漳区域": 55, "泉州区域": 50,
        "三明区域": 25, "南平区域": 5,  "宁德区域": 25,
        "莆田区域": 35, "龙岩区域": 50,
    },
    "福州炼石": {
        "福州区域": 5,  "厦漳区域": 50, "泉州区域": 45,
        "三明区域": 30, "南平区域": 20, "宁德区域": 15,
        "莆田区域": 20, "龙岩区域": 55,
    },
    "金银湖": {
        "福州区域": 8,  "厦漳区域": 52, "泉州区域": 47,
        "三明区域": 32, "南平区域": 22, "宁德区域": 18,
        "莆田区域": 22, "龙岩区域": 57,
    },
    "德化分公司": {
        "福州区域": 35, "厦漳区域": 30, "泉州区域": 5,
        "三明区域": 40, "南平区域": 50, "宁德区域": 55,
        "莆田区域": 25, "龙岩区域": 35,
    },
}

# 袋装运输附加费（元/吨）—— 袋装装卸更复杂
BAG_TRANSPORT_PREMIUM = 6

# 期初库存（万吨）
DEFAULT_INIT_INVENTORY = {
    "安砂建福":   {"散装": 5.0,  "袋装": 3.5},
    "永安建福":   {"散装": 2.5,  "袋装": 1.7},
    "顺昌炼石":   {"散装": 2.3,  "袋装": 1.5},
    "福州炼石":   {"散装": 1.3,  "袋装": 0.8},
    "金银湖":     {"散装": 0.5,  "袋装": 0.4},
    "德化分公司": {"散装": 0.5,  "袋装": 0.4},
}

# 仓容上限（万吨）
DEFAULT_MAX_INVENTORY = {
    "安砂建福":   {"散装": 9.0,  "袋装": 6.0},
    "永安建福":   {"散装": 5.0,  "袋装": 3.0},
    "顺昌炼石":   {"散装": 4.0,  "袋装": 3.0},
    "福州炼石":   {"散装": 2.5,  "袋装": 2.0},
    "金银湖":     {"散装": 1.2,  "袋装": 0.8},
    "德化分公司": {"散装": 0.8,  "袋装": 0.7},
}

# 安全库存下限（万吨）
DEFAULT_MIN_INVENTORY = {
    "安砂建福":   {"散装": 1.2,  "袋装": 0.8},
    "永安建福":   {"散装": 0.9,  "袋装": 0.6},
    "顺昌炼石":   {"散装": 0.9,  "袋装": 0.6},
    "福州炼石":   {"散装": 0.6,  "袋装": 0.4},
    "金银湖":     {"散装": 0.2,  "袋装": 0.1},
    "德化分公司": {"散装": 0.1,  "袋装": 0.1},
}

INVENTORY_HOLDING_COST = 8  # 元/吨/月

# ─────────────────────────────────────────────
# 第二层：权重配置（可手工设置）
# ─────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "capacity_ratio":    1.0,   # 产能利用率上限（0.7~1.0）
    "inv_min_ratio":     1.0,   # 安全库存下限倍数（0.3~2.0）
    "demand_max_ratio":  1.0,   # 需求上限弹性（0.8~1.2）
    "demand_flex":       0.85,  # 最低保供率（0.5~1.0）
    "inventory_penalty": 1.0,   # 库存惩罚系数（0.1~5.0）
    "transport_penalty": 1.0,   # 运输成本敏感度（0.5~2.0）
}

# 预设方案权重组合（通过约束结构差异化，而非目标函数缩放）
PRESET_WEIGHTS = {
    "conservative": {
        "capacity_ratio":    0.85,
        "inv_min_ratio":     1.5,
        "demand_max_ratio":  0.90,
        "demand_flex":       0.95,
        "inventory_penalty": 3.0,
        "transport_penalty": 1.3,
    },
    "balanced": {
        "capacity_ratio":    1.0,
        "inv_min_ratio":     1.0,
        "demand_max_ratio":  1.0,
        "demand_flex":       0.85,
        "inventory_penalty": 1.0,
        "transport_penalty": 1.0,
    },
    "aggressive": {
        "capacity_ratio":    1.0,
        "inv_min_ratio":     0.4,
        "demand_max_ratio":  1.15,
        "demand_flex":       0.70,
        "inventory_penalty": 0.3,
        "transport_penalty": 0.7,
    },
}

# What-if 快捷模板
WHATIF_TEMPLATES = [
    {
        "id": "peak_demand",
        "label": "旺季需求+15%",
        "adjustments": [
            {"type": "demand", "region": r, "product": p, "mode": "pct", "value": 15}
            for r in REGIONS for p in PRODUCTS
        ],
    },
    {
        "id": "expand_anzha",
        "label": "安砂扩产+3万吨",
        "adjustments": [
            {"type": "capacity", "base": "安砂建福", "product": "散装", "mode": "abs", "value": 2.0},
            {"type": "capacity", "base": "安砂建福", "product": "袋装", "mode": "abs", "value": 1.0},
        ],
    },
    {
        "id": "price_up",
        "label": "全线涨价+10元/吨",
        "adjustments": [
            {"type": "price", "region": r, "product": p, "mode": "abs", "value": 10}
            for r in REGIONS for p in PRODUCTS
        ],
    },
    {
        "id": "transport_down",
        "label": "运输成本降低10%",
        "adjustments": [
            {"type": "transport", "base": b, "region": r, "mode": "pct", "value": -10}
            for b in BASES for r in REGIONS
        ],
    },
]


# ─────────────────────────────────────────────
# 参数构建
# ─────────────────────────────────────────────

def build_params(overrides: Optional[dict] = None) -> dict:
    """构建模型参数，支持外部覆盖"""
    params = {
        "bases": list(BASES),
        "regions": list(REGIONS),
        "products": list(PRODUCTS),
        "capacity":       {b: dict(v) for b, v in DEFAULT_CAPACITY.items()},
        "init_inventory": {b: dict(v) for b, v in DEFAULT_INIT_INVENTORY.items()},
        "max_inventory":  {b: dict(v) for b, v in DEFAULT_MAX_INVENTORY.items()},
        "min_inventory":  {b: dict(v) for b, v in DEFAULT_MIN_INVENTORY.items()},
        "demand":         {r: dict(v) for r, v in DEFAULT_DEMAND.items()},
        "min_supply":     {r: dict(v) for r, v in DEFAULT_MIN_SUPPLY.items()},
        "price":          {r: dict(v) for r, v in DEFAULT_PRICE.items()},
        "prod_cost":      {b: dict(v) for b, v in DEFAULT_PROD_COST.items()},
        "transport_cost": {b: dict(v) for b, v in DEFAULT_TRANSPORT_COST.items()},
        "bag_transport_premium": BAG_TRANSPORT_PREMIUM,
        "holding_cost":   INVENTORY_HOLDING_COST,
        "weights":        dict(DEFAULT_WEIGHTS),
    }
    if overrides:
        for key, val in overrides.items():
            if key == "weights" and isinstance(val, dict):
                params["weights"].update(val)
            elif key in params and isinstance(val, dict) and isinstance(params[key], dict):
                # 二级字典合并
                for k2, v2 in val.items():
                    if k2 in params[key] and isinstance(v2, dict):
                        params[key][k2].update(v2)
                    else:
                        params[key][k2] = v2
            elif key in params:
                params[key] = val
    return params


def apply_adjustments(params: dict, adjustments: list) -> dict:
    """
    将 What-if 调整项应用到参数副本上
    adjustments: [
      {"type": "capacity",  "base": "安砂建福", "product": "散装", "mode": "abs"|"pct", "value": 2.0},
      {"type": "price",     "region": "福州区域", "product": "袋装", "mode": "abs", "value": 10},
      {"type": "demand",    "region": "泉州区域", "product": "散装", "mode": "pct", "value": 15},
      {"type": "prod_cost", "base": "安砂建福", "product": "散装", "mode": "abs", "value": -5},
      {"type": "transport", "base": "安砂建福", "region": "福州区域", "mode": "pct", "value": -10},
    ]
    """
    p = copy.deepcopy(params)
    for adj in adjustments:
        t = adj.get("type")
        mode = adj.get("mode", "abs")  # abs=绝对值变化, pct=百分比变化
        val = adj.get("value", 0)

        def apply_delta(original, delta, mode):
            if mode == "pct":
                return original * (1 + delta / 100)
            else:
                return original + delta

        if t == "capacity":
            b, prod = adj.get("base"), adj.get("product")
            if b and prod and b in p["capacity"] and prod in p["capacity"][b]:
                p["capacity"][b][prod] = max(0, apply_delta(p["capacity"][b][prod], val, mode))
            elif b and not prod:  # 不指定品种则全部调整
                for pr in PRODUCTS:
                    if pr in p["capacity"].get(b, {}):
                        p["capacity"][b][pr] = max(0, apply_delta(p["capacity"][b][pr], val, mode))

        elif t == "price":
            r, prod = adj.get("region"), adj.get("product")
            if r and prod and r in p["price"] and prod in p["price"][r]:
                p["price"][r][prod] = max(0, apply_delta(p["price"][r][prod], val, mode))
            elif r and not prod:
                for pr in PRODUCTS:
                    if pr in p["price"].get(r, {}):
                        p["price"][r][pr] = max(0, apply_delta(p["price"][r][pr], val, mode))

        elif t == "demand":
            r, prod = adj.get("region"), adj.get("product")
            if r and prod and r in p["demand"] and prod in p["demand"][r]:
                p["demand"][r][prod] = max(0, apply_delta(p["demand"][r][prod], val, mode))
            elif r and not prod:
                for pr in PRODUCTS:
                    if pr in p["demand"].get(r, {}):
                        p["demand"][r][pr] = max(0, apply_delta(p["demand"][r][pr], val, mode))

        elif t == "prod_cost":
            b, prod = adj.get("base"), adj.get("product")
            if b and prod and b in p["prod_cost"] and prod in p["prod_cost"][b]:
                p["prod_cost"][b][prod] = max(0, apply_delta(p["prod_cost"][b][prod], val, mode))
            elif b and not prod:
                for pr in PRODUCTS:
                    if pr in p["prod_cost"].get(b, {}):
                        p["prod_cost"][b][pr] = max(0, apply_delta(p["prod_cost"][b][pr], val, mode))

        elif t == "transport":
            b, r = adj.get("base"), adj.get("region")
            if b and r and b in p["transport_cost"] and r in p["transport_cost"][b]:
                p["transport_cost"][b][r] = max(0, apply_delta(p["transport_cost"][b][r], val, mode))
            elif b and not r:
                for rr in REGIONS:
                    if rr in p["transport_cost"].get(b, {}):
                        p["transport_cost"][b][rr] = max(0, apply_delta(p["transport_cost"][b][rr], val, mode))

    return p


# ─────────────────────────────────────────────
# LP 求解核心
# ─────────────────────────────────────────────

def solve_lp(params: dict, weights: Optional[dict] = None) -> dict:
    """
    运行 LP 求解器（品种维度版本）
    params: 约束参数（第一层）
    weights: 权重配置（第二层），None 则使用 params 中的 weights
    """
    t0 = time.time()

    bases = params["bases"]
    regions = params["regions"]
    products = params["products"]
    capacity = params["capacity"]
    init_inv = params["init_inventory"]
    max_inv = params["max_inventory"]
    min_inv = params["min_inventory"]
    demand = params["demand"]
    min_supply = params["min_supply"]
    price = params["price"]
    prod_cost = params["prod_cost"]
    transport_cost = params["transport_cost"]
    bag_premium = params.get("bag_transport_premium", BAG_TRANSPORT_PREMIUM)
    holding_cost = params.get("holding_cost", INVENTORY_HOLDING_COST)

    # 权重：优先使用传入的 weights，其次用 params 中的，最后用默认值
    w = dict(DEFAULT_WEIGHTS)
    if params.get("weights"):
        w.update(params["weights"])
    if weights:
        w.update(weights)

    # ── 建模 ──
    prob = LpProblem("cement_balance_v2", LpMaximize)

    # 决策变量：x[基地][区域][品种] = 供应量（万吨）
    x = {
        (b, r, p): LpVariable(
            f"x_{b}_{r}_{p}".replace(" ", "_").replace("装", "z"),
            lowBound=0
        )
        for b in bases for r in regions for p in products
    }

    # 期末库存变量：s[基地][品种]
    s = {
        (b, p): LpVariable(
            f"s_{b}_{p}".replace(" ", "_").replace("装", "z"),
            lowBound=0
        )
        for b in bases for p in products
    }

    # ── 目标函数：利润最大化 ──
    # 收入
    revenue = lpSum(
        price[r][p] * x[(b, r, p)]
        for b in bases for r in regions for p in products
    )
    # 生产成本
    prod_cost_total = lpSum(
        prod_cost[b][p] * x[(b, r, p)]
        for b in bases for r in regions for p in products
    )
    # 运输成本（袋装附加运费）
    transport_cost_total = lpSum(
        (transport_cost[b][r] + (bag_premium if p == "袋装" else 0))
        * w["transport_penalty"] * x[(b, r, p)]
        for b in bases for r in regions for p in products
    )
    # 库存持有成本
    inventory_cost = lpSum(
        holding_cost * w["inventory_penalty"] * s[(b, p)]
        for b in bases for p in products
    )

    prob += revenue - prod_cost_total - transport_cost_total - inventory_cost

    # ── 约束条件 ──
    constraint_names = {}

    # 1. 各基地各品种产能约束
    for b in bases:
        for p in products:
            cname = f"cap_{b}_{p}".replace(" ", "_").replace("装", "z")
            eff_cap = capacity[b][p] * w["capacity_ratio"]
            prob += lpSum(x[(b, r, p)] for r in regions) <= eff_cap, cname
            constraint_names[cname] = f"{b}·{p}产能上限"

    # 2. 库存平衡：期末库存 = 期初库存 + (产能 - 发运量) × 0.3
    for b in bases:
        for p in products:
            cname = f"inv_bal_{b}_{p}".replace(" ", "_").replace("装", "z")
            total_ship = lpSum(x[(b, r, p)] for r in regions)
            eff_cap = capacity[b][p] * w["capacity_ratio"]
            prob += s[(b, p)] == init_inv[b][p] + (eff_cap - total_ship) * 0.3, cname
            constraint_names[cname] = f"{b}·{p}库存平衡"

    # 3. 仓容上限
    for b in bases:
        for p in products:
            cname = f"inv_max_{b}_{p}".replace(" ", "_").replace("装", "z")
            prob += s[(b, p)] <= max_inv[b][p], cname
            constraint_names[cname] = f"{b}·{p}仓容上限"

    # 4. 安全库存下限（按权重调整）
    for b in bases:
        for p in products:
            cname = f"inv_min_{b}_{p}".replace(" ", "_").replace("装", "z")
            eff_min = min_inv[b][p] * w["inv_min_ratio"]
            prob += s[(b, p)] >= eff_min, cname
            constraint_names[cname] = f"{b}·{p}安全库存下限"

    # 5. 区域各品种需求上限（按权重调整）
    for r in regions:
        for p in products:
            cname = f"dem_max_{r}_{p}".replace(" ", "_").replace("装", "z")
            eff_dem = demand[r][p] * w["demand_max_ratio"]
            prob += lpSum(x[(b, r, p)] for b in bases) <= eff_dem, cname
            constraint_names[cname] = f"{r}·{p}需求上限"

    # 6. 区域各品种最低保供（按权重调整）
    for r in regions:
        for p in products:
            cname = f"dem_min_{r}_{p}".replace(" ", "_").replace("装", "z")
            min_val = min_supply[r][p] * w["demand_flex"]
            prob += lpSum(x[(b, r, p)] for b in bases) >= min_val, cname
            constraint_names[cname] = f"{r}·{p}最低保供"

    # ── 求解 ──
    solver = PULP_CBC_CMD(msg=0, timeLimit=30)
    prob.solve(solver)

    elapsed_ms = int((time.time() - t0) * 1000)
    status = LpStatus[prob.status]

    return _extract_result(prob, x, s, bases, regions, products,
                           price, prod_cost, transport_cost, bag_premium,
                           holding_cost, demand, max_inv, min_inv,
                           constraint_names, status, elapsed_ms)


def _extract_result(prob, x, s, bases, regions, products,
                    price, prod_cost, transport_cost, bag_premium,
                    holding_cost, demand, max_inv, min_inv,
                    constraint_names, status, elapsed_ms) -> dict:
    """提取求解结果"""
    obj_val = value(prob.objective) or 0

    # 调配方案
    allocation = []
    for b in bases:
        for r in regions:
            for p in products:
                qty = value(x[(b, r, p)]) or 0
                if qty > 0.01:
                    tc = transport_cost[b][r] + (bag_premium if p == "袋装" else 0)
                    margin = price[r][p] - prod_cost[b][p] - tc
                    allocation.append({
                        "from_base": b,
                        "to_region": r,
                        "product": p,
                        "qty": round(qty, 2),
                        "revenue": round(price[r][p] * qty, 1),
                        "margin_per_ton": round(margin, 1),
                        "profit": round(margin * qty, 1),
                    })

    # 期末库存
    inventory_result = {}
    for b in bases:
        inventory_result[b] = {}
        for p in products:
            sv = value(s[(b, p)]) or 0
            inventory_result[b][p] = {
                "end_inventory": round(sv, 2),
                "max_inventory": max_inv[b][p],
                "min_inventory": min_inv[b][p],
                "utilization_pct": round(sv / max_inv[b][p] * 100, 1) if max_inv[b][p] > 0 else 0,
            }

    # 影子价格
    shadow_prices = []
    for cname, label in constraint_names.items():
        if cname in prob.constraints:
            c = prob.constraints[cname]
            pi = c.pi if hasattr(c, "pi") and c.pi is not None else 0
            slack = c.slack if hasattr(c, "slack") and c.slack is not None else 0
            is_binding = abs(slack) < 0.001
            shadow_prices.append({
                "constraint": label,
                "constraint_key": cname,
                "shadow_price": round(pi, 2),
                "slack": round(slack, 3),
                "is_binding": is_binding,
                "interpretation": _interpret_shadow_price(label, pi, slack, is_binding),
            })
    shadow_prices.sort(key=lambda x: (-abs(x["shadow_price"]), -x["is_binding"]))

    # 利润分解
    total_revenue = sum(a["revenue"] for a in allocation)
    total_prod_cost = sum(
        prod_cost[b][p] * (value(x[(b, r, p)]) or 0)
        for b in bases for r in regions for p in products
    )
    total_transport = sum(
        (transport_cost[b][r] + (bag_premium if p == "袋装" else 0)) * (value(x[(b, r, p)]) or 0)
        for b in bases for r in regions for p in products
    )
    total_inv_cost = sum(
        holding_cost * (value(s[(b, p)]) or 0)
        for b in bases for p in products
    )
    profit_breakdown = {
        "revenue": round(total_revenue, 1),
        "prod_cost": round(total_prod_cost, 1),
        "transport_cost": round(total_transport, 1),
        "inventory_cost": round(total_inv_cost, 1),
        "net_profit": round(total_revenue - total_prod_cost - total_transport - total_inv_cost, 1),
    }

    # 供需缺口（按品种）
    gap_analysis = []
    for r in regions:
        for p in products:
            supplied = sum(value(x[(b, r, p)]) or 0 for b in bases)
            dem = demand[r][p]
            gap_analysis.append({
                "region": r,
                "product": p,
                "demand": dem,
                "supplied": round(supplied, 2),
                "gap": round(dem - supplied, 2),
                "fulfillment_rate": round(supplied / dem * 100, 1) if dem > 0 else 0,
            })

    # 按区域汇总供需
    gap_by_region = []
    for r in regions:
        total_dem = sum(demand[r][p] for p in products)
        total_sup = sum(value(x[(b, r, p)]) or 0 for b in bases for p in products)
        gap_by_region.append({
            "region": r,
            "demand": total_dem,
            "supplied": round(total_sup, 2),
            "gap": round(total_dem - total_sup, 2),
            "fulfillment_rate": round(total_sup / total_dem * 100, 1) if total_dem > 0 else 0,
        })

    return {
        "status": status,
        "solve_time_ms": elapsed_ms,
        "objective_value": round(obj_val, 1),
        "allocation": allocation,
        "inventory": inventory_result,
        "shadow_prices": shadow_prices[:20],  # 只返回前20个最重要的
        "profit_breakdown": profit_breakdown,
        "gap_analysis": gap_analysis,
        "gap_by_region": gap_by_region,
        "params_snapshot": {
            "total_capacity": sum(
                DEFAULT_CAPACITY[b][p] for b in bases for p in products
            ),
            "total_demand": sum(
                demand[r][p] for r in regions for p in products
            ),
            "bases_count": len(bases),
            "regions_count": len(regions),
            "products_count": len(products),
        },
    }


# ─────────────────────────────────────────────
# 三方案对比
# ─────────────────────────────────────────────

def solve_three_scenarios(params: dict) -> dict:
    """求解保守/均衡/激进三种预设方案"""
    results = {}
    for scenario, w in PRESET_WEIGHTS.items():
        results[scenario] = solve_lp(params, weights=w)
        results[scenario]["scenario"] = scenario

    labels = {
        "conservative": ("保守方案", "产能×0.85，安全库存×1.5，保供率95%"),
        "balanced":     ("均衡方案（推荐）", "默认参数，保供率85%"),
        "aggressive":   ("激进方案", "安全库存×0.4，允许超额供应，保供率70%"),
    }
    risk = {"conservative": "低", "balanced": "中", "aggressive": "高"}

    return {
        "scenarios": {
            sc: {
                "label": labels[sc][0],
                "description": labels[sc][1],
                "profit": results[sc]["profit_breakdown"]["net_profit"],
                "fulfillment_rate": _avg_fulfillment(results[sc]["gap_by_region"]),
                "inventory_risk": risk[sc],
                "transport_cost": results[sc]["profit_breakdown"]["transport_cost"],
                "solve_status": results[sc]["status"],
                "solve_time_ms": results[sc]["solve_time_ms"],
            }
            for sc in ["conservative", "balanced", "aggressive"]
        },
        "details": results,
        "recommendation": "balanced",
    }


# ─────────────────────────────────────────────
# What-if 多因素模拟
# ─────────────────────────────────────────────

def solve_whatif(
    params: dict,
    adjustments: list,
    weights: Optional[dict] = None,
    decompose: bool = True,
) -> dict:
    """
    What-if 多因素联动模拟
    adjustments: 调整项列表（支持多基地、多区域、多品种同时调整）
    decompose: 是否做因素贡献分解（每个调整项单独求解一次）
    """
    t0 = time.time()

    # 基准求解
    base_result = solve_lp(params, weights=weights)
    base_profit = base_result["profit_breakdown"]["net_profit"]

    # 应用所有调整项后求解
    modified_params = apply_adjustments(params, adjustments)
    new_result = solve_lp(modified_params, weights=weights)
    new_profit = new_result["profit_breakdown"]["net_profit"]
    profit_delta = round(new_profit - base_profit, 1)

    # 因素贡献分解（每个调整项单独求解）
    decomposition = []
    if decompose and len(adjustments) > 0:
        for i, adj in enumerate(adjustments):
            single_params = apply_adjustments(params, [adj])
            single_result = solve_lp(single_params, weights=weights)
            single_profit = single_result["profit_breakdown"]["net_profit"]
            single_delta = round(single_profit - base_profit, 1)

            label = _adj_label(adj)
            decomposition.append({
                "index": i,
                "label": label,
                "profit_delta": single_delta,
                "profit_delta_pct": round(single_delta / base_profit * 100, 2) if base_profit else 0,
                "recommendation": "优先执行" if single_delta > 50 else ("可执行" if single_delta > 0 else "谨慎"),
            })
        # 按贡献排序
        decomposition.sort(key=lambda x: -x["profit_delta"])

    # 调配方案变化（对比基准）
    base_alloc_map = {
        (a["from_base"], a["to_region"], a["product"]): a["qty"]
        for a in base_result["allocation"]
    }
    new_alloc_map = {
        (a["from_base"], a["to_region"], a["product"]): a["qty"]
        for a in new_result["allocation"]
    }
    all_keys = set(base_alloc_map) | set(new_alloc_map)
    allocation_diff = []
    for key in all_keys:
        base_qty = base_alloc_map.get(key, 0)
        new_qty = new_alloc_map.get(key, 0)
        delta = round(new_qty - base_qty, 2)
        if abs(delta) > 0.01:
            allocation_diff.append({
                "from_base": key[0],
                "to_region": key[1],
                "product": key[2],
                "base_qty": round(base_qty, 2),
                "new_qty": round(new_qty, 2),
                "delta": delta,
            })
    allocation_diff.sort(key=lambda x: -abs(x["delta"]))

    # 生成建议文字
    top = decomposition[0] if decomposition else None
    if profit_delta > 0:
        recommendation = (
            f"模拟结果：净利润增加 {profit_delta} 万元（+{round(profit_delta/base_profit*100,1)}%）。"
            + (f"其中「{top['label']}」贡献最大（+{top['profit_delta']}万元），建议优先执行。" if top else "")
        )
    elif profit_delta < 0:
        recommendation = f"模拟结果：净利润减少 {abs(profit_delta)} 万元，不建议执行当前调整组合。"
    else:
        recommendation = "模拟结果：利润无明显变化。"

    return {
        "base_profit": base_profit,
        "new_profit": new_profit,
        "profit_delta": profit_delta,
        "profit_delta_pct": round(profit_delta / base_profit * 100, 2) if base_profit else 0,
        "decomposition": decomposition,
        "allocation_diff": allocation_diff[:15],
        "new_gap_by_region": new_result["gap_by_region"],
        "new_profit_breakdown": new_result["profit_breakdown"],
        "recommendation": recommendation,
        "base_solve_status": base_result["status"],
        "new_solve_status": new_result["status"],
        "total_time_ms": int((time.time() - t0) * 1000),
    }


# ─────────────────────────────────────────────
# 默认参数（供前端展示）
# ─────────────────────────────────────────────

def get_default_params() -> dict:
    return {
        "bases": BASES,
        "regions": REGIONS,
        "products": PRODUCTS,
        "capacity":       DEFAULT_CAPACITY,
        "init_inventory": DEFAULT_INIT_INVENTORY,
        "max_inventory":  DEFAULT_MAX_INVENTORY,
        "min_inventory":  DEFAULT_MIN_INVENTORY,
        "demand":         DEFAULT_DEMAND,
        "min_supply":     DEFAULT_MIN_SUPPLY,
        "price":          DEFAULT_PRICE,
        "prod_cost":      DEFAULT_PROD_COST,
        "transport_cost": DEFAULT_TRANSPORT_COST,
        "bag_transport_premium": BAG_TRANSPORT_PREMIUM,
        "holding_cost":   INVENTORY_HOLDING_COST,
        "weights":        DEFAULT_WEIGHTS,
        "preset_weights": PRESET_WEIGHTS,
        "whatif_templates": WHATIF_TEMPLATES,
        "data_source": "福建水泥2025年12月生产日报表 + 生产运营表",
        "data_period": "2025年12月",
    }


# ─────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────

def _interpret_shadow_price(label: str, pi: float, slack: float, is_binding: bool) -> str:
    if not is_binding:
        return f"松约束，剩余空间{abs(slack):.2f}万吨，当前不影响最优解"
    if pi == 0:
        return "退化约束，对目标函数无直接影响"
    if "产能" in label:
        return f"紧约束：扩产1万吨可增加利润{abs(pi):.1f}万元，建议优先扩产"
    if "保供" in label:
        return f"紧约束：增加1万吨供应可增加利润{abs(pi):.1f}万元，需求旺盛"
    if "安全库存" in label:
        return f"紧约束：降低安全库存1万吨可增加利润{abs(pi):.1f}万元，但需评估风险"
    if "仓容" in label:
        return f"紧约束：扩大仓容1万吨可增加利润{abs(pi):.1f}万元，建议扩仓"
    return f"影子价格{pi:.2f}，{'紧约束' if is_binding else '松约束'}"


def _avg_fulfillment(gap_by_region: list) -> float:
    if not gap_by_region:
        return 0
    return round(sum(g["fulfillment_rate"] for g in gap_by_region) / len(gap_by_region), 1)


def _adj_label(adj: dict) -> str:
    t = adj.get("type", "")
    mode = adj.get("mode", "abs")
    val = adj.get("value", 0)
    sign = "+" if val >= 0 else ""
    unit_map = {
        "capacity": "万吨", "demand": "万吨",
        "price": "元/吨", "prod_cost": "元/吨", "transport": "元/吨"
    }
    unit = "%" if mode == "pct" else unit_map.get(t, "")
    type_map = {
        "capacity": "产能", "demand": "需求",
        "price": "售价", "prod_cost": "生产成本", "transport": "运输成本"
    }
    type_label = type_map.get(t, t)
    obj = adj.get("base") or adj.get("region") or "全部"
    prod = adj.get("product", "")
    prod_str = f"·{prod}" if prod else ""
    return f"{obj}{prod_str}{type_label}{sign}{val}{unit}"