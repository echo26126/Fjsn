from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import random
from services.region_config_service import region_config_service
from services.december_report_service import december_report_service

router = APIRouter()

BASES = ["安砂建福", "永安建福", "顺昌炼石", "福州炼石", "宁德建福", "金银湖水泥"]


@router.get("/production")
def query_production(
    period: str = "month",
    base: Optional[str] = None,
    category: Optional[str] = None,
    point: Optional[str] = None,
):
    if period in ("day", "month"):
        default_point = "2025-12-31" if period == "day" else "2025-12"
        rows = december_report_service.get_production_report(
            period=period,
            point=point or default_point,
            base=base or "",
            category=category or "",
        )
        return {"items": rows}
    plan_values = [6.5, 10.9, 6.4, 5.0, 3.6, 0.2]
    actual_values = [6.3, 10.4, 6.1, 4.8, 3.3, 0.0]
    category_factors = [("水泥", 0.7), ("熟料", 0.3)]
    if category == "cement":
        category_factors = [("水泥", 1)]
    elif category == "clinker":
        category_factors = [("熟料", 1)]
    return {
        "items": [
            {
                "base": name,
                "category": cat,
                "period": "2026-02",
                "plan_qty": round(plan * factor, 1),
                "actual_qty": round(actual * factor, 1),
                "variance_pct": round((actual * factor / (plan * factor) - 1) * 100, 1),
                "utilization": round(75 + random.uniform(0, 20), 1),
            }
            for (name, plan, actual) in zip(BASES, plan_values, actual_values)
            for cat, factor in category_factors
        ]
    }


@router.get("/production-report")
def query_production_report(
    period: str = "day",
    base: Optional[str] = None,
    category: Optional[str] = None,
    point: Optional[str] = None,
):
    default_point = "2025-12-31" if period == "day" else "2025-12"
    rows = december_report_service.get_production_report(
        period=period,
        point=point or default_point,
        base=base or "",
        category=category or "",
    )
    avg_utilization = round(sum(float(item.get("utilization", 0.0)) for item in rows) / max(1, len(rows)), 1)
    total_kiln_stop_hours = round(sum(float(item.get("kiln_stop_hours", 0.0)) for item in rows), 1)
    total_kiln_stop_times = int(sum(float(item.get("kiln_stop_times", 0.0)) for item in rows))
    return {
        "period": period,
        "point": point or default_point,
        "summary": {
            "avg_utilization": avg_utilization,
            "total_kiln_stop_hours": total_kiln_stop_hours,
            "total_kiln_stop_times": total_kiln_stop_times,
        },
        "items": rows,
    }


@router.get("/production-equipment")
def query_production_equipment(
    base: Optional[str] = None,
    point: Optional[str] = None,
):
    resolved_point = point or "2025-12-31"
    rows = december_report_service.get_equipment_summary(point=resolved_point, base=base or "")
    return {
        "point": resolved_point,
        "items": rows,
    }


@router.get("/production-equipment-detail")
def query_production_equipment_detail(
    base: Optional[str] = None,
    point: Optional[str] = None,
):
    resolved_point = point or "2025-12-31"
    rows = december_report_service.get_equipment_detail(point=resolved_point, base=base or "")
    return {
        "point": resolved_point,
        "items": rows,
    }


@router.get("/production-stop-reasons")
def query_production_stop_reasons(
    base: Optional[str] = None,
    point: Optional[str] = None,
):
    resolved_point = point or "2025-12-31"
    rows = december_report_service.get_stop_reason_summary(point=resolved_point, base=base or "")
    return {
        "point": resolved_point,
        "items": rows,
    }


@router.get("/inventory")
def query_inventory(base: Optional[str] = None, category: Optional[str] = None):
    inventory_data = [
        {"base": "安砂建福", "category": "熟料", "end_qty": 4.53, "capacity": 21.2},
        {"base": "安砂建福", "category": "水泥", "end_qty": 8.98, "capacity": 15.7},
        {"base": "永安建福", "category": "熟料", "end_qty": 3.69, "capacity": 5.9},
        {"base": "永安建福", "category": "水泥", "end_qty": 2.04, "capacity": 5.5},
        {"base": "顺昌炼石", "category": "熟料", "end_qty": 3.68, "capacity": 16.64},
        {"base": "顺昌炼石", "category": "水泥", "end_qty": 3.32, "capacity": 5.5},
        {"base": "福州炼石", "category": "熟料", "end_qty": 2.0, "capacity": 5.5},
        {"base": "福州炼石", "category": "水泥", "end_qty": 3.81, "capacity": 5.9},
        {"base": "宁德建福", "category": "熟料", "end_qty": 0.59, "capacity": 5.15},
        {"base": "宁德建福", "category": "水泥", "end_qty": 1.39, "capacity": 5.15},
        {"base": "金银湖水泥", "category": "水泥", "end_qty": 3.68, "capacity": 15.7},
    ]
    category_map = {"cement": "水泥", "clinker": "熟料"}
    filtered_items = [
        item for item in inventory_data
        if (not base or item["base"] == base)
        and (not category or item["category"] == category_map.get(category))
    ]
    months = ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02"]
    clinker_inventory = [12.8, 13.2, 14.1, 14.6, 14.3, 14.49]
    cement_inventory = [15.2, 16.1, 17.5, 18.3, 17.8, 18.11]
    base_category_trend = {}
    for item in filtered_items:
        end_qty = float(item["end_qty"])
        factor = 1.0 + (hash(item["base"] + item["category"]) % 7 - 3) / 100
        series = [round(end_qty * factor * (0.88 + i * 0.03), 2) for i in range(len(months))]
        base_category_trend[f"{item['base']}|{item['category']}"] = series
    return {
        "items": [
            {
                "base": item["base"],
                "category": item["category"],
                "begin_qty": round(item["end_qty"] + random.uniform(-0.6, 0.8), 2),
                "end_qty": item["end_qty"],
                "available_qty": round(item["end_qty"] * 0.92, 2),
                "capacity": item["capacity"],
                "ratio_pct": round(item["end_qty"] / item["capacity"] * 100, 1),
                "safety_qty": round(item["capacity"] * 0.25, 2),
                "status": "高位" if item["end_qty"] / item["capacity"] > 0.85 else ("低位" if item["end_qty"] / item["capacity"] < 0.3 else "正常"),
            }
            for item in filtered_items
        ],
        "trend": {
            "months": months,
            "total_inventory": [28, 30, 33, 35, 34, 32.6],
            "clinker_inventory": clinker_inventory,
            "cement_inventory": cement_inventory,
            "base_category_trend": base_category_trend,
            "safety_line": 15,
        },
    }


@router.get("/sales")
def query_sales(
    period: str = "month",
    base: Optional[str] = None,
    region: Optional[str] = None,
):
    region_config = region_config_service.get_config()
    regions = list((region_config.get("region_city_map") or {}).keys())
    return {
        "items": [
            {
                "base": BASES[i % len(BASES)],
                "region": regions[j],
                "spec": "P.O 42.5",
                "package": "散装" if (i + j) % 2 == 0 else "袋装",
                "qty": round(2 + random.uniform(0, 3), 2),
                "avg_price": round(350 + random.uniform(0, 80)),
                "amount": round(800 + random.uniform(0, 500)),
            }
            for i in range(min(5, len(BASES)))
            for j in range(len(regions))
        ],
        "price_trend": {
            "months": ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02"],
            "qty": [55, 58, 60, 62, 64, 62.1],
            "avg_price": [385, 390, 388, 395, 402, 398],
        },
    }


@router.get("/inventory-daily")
def query_inventory_daily(base: str = Query(...), month: str = Query("2025-12")):
    if month != "2025-12":
        raise HTTPException(status_code=400, detail="当前仅支持 2025-12 日报数据")
    data = december_report_service.get_base_daily_inventory(base)
    if not data["days"]:
        raise HTTPException(status_code=404, detail=f"未找到基地 {base} 的日报库存数据")
    return {
        "base": base,
        "month": month,
        "days": data["days"],
        "clinker_inventory": data["clinker_inventory"],
        "cement_inventory": data["cement_inventory"],
    }
