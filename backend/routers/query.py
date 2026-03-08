from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.december_report_service import december_report_service
from services.december_sales_service import december_sales_service

router = APIRouter()

BASES = ["安砂建福", "永安建福", "顺昌炼石", "福州炼石", "宁德建福", "金银湖水泥"]
INVENTORY_CAPACITY = {
    "安砂建福|熟料": 21.2,
    "安砂建福|水泥": 15.7,
    "永安建福|熟料": 5.9,
    "永安建福|水泥": 5.5,
    "顺昌炼石|熟料": 16.64,
    "顺昌炼石|水泥": 5.5,
    "福州炼石|熟料": 5.5,
    "福州炼石|水泥": 5.9,
    "宁德建福|熟料": 5.15,
    "宁德建福|水泥": 5.15,
    "金银湖水泥|熟料": 0.0,
    "金银湖水泥|水泥": 15.7,
}


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
    return {"items": []}


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
def query_inventory(
    period: str = "month",
    point: Optional[str] = None,
    base: Optional[str] = None,
    category: Optional[str] = None,
):
    point_text = str(point or "")
    mode = "year" if period == "year" else "month"
    year = 2025
    month = 12
    if len(point_text) >= 4 and point_text[:4].isdigit():
        year = int(point_text[:4])
    if len(point_text) >= 7 and point_text[5:7].isdigit():
        month = max(1, min(12, int(point_text[5:7])))

    inventory_source = december_report_service._parse_inventory_sheet()
    category_map = {"cement": "水泥", "clinker": "熟料"}
    target_category = category_map.get(category or "", category or "")
    category_list = ["熟料", "水泥"] if not target_category else [target_category]

    def _to_wan_series(raw_series):
        return [round(float(v) / 10000, 2) for v in list(raw_series or [])]

    def _empty_or_zero(length: int, enabled: bool):
        return [0.0 for _ in range(length)] if enabled else [None for _ in range(length)]

    items = []
    base_category_trend = {}

    if mode == "year":
        labels = [f"{year}-{m:02d}" for m in range(1, 13)]
        clinker_total = [None for _ in range(12)]
        cement_total = [None for _ in range(12)]
        total_safety = 0.0

        for base_name in BASES:
            if base and base_name != base:
                continue
            base_daily = inventory_source.get(base_name, {"clinker_inventory": [], "cement_inventory": []})
            clinker_series = _to_wan_series(base_daily.get("clinker_inventory", []))
            cement_series = _to_wan_series(base_daily.get("cement_inventory", []))
            clinker_dec = clinker_series[-1] if clinker_series else 0.0
            cement_dec = cement_series[-1] if cement_series else 0.0
            selected_index = min(month - 1, 11)

            for cat in category_list:
                capacity = float(INVENTORY_CAPACITY.get(f"{base_name}|{cat}", 0.0))
                safety_qty = round(capacity * 0.25, 2)
                total_safety += safety_qty

                month_series = [None for _ in range(12)]
                if year == 2025 and selected_index >= 11:
                    month_series[11] = round(clinker_dec if cat == "熟料" else cement_dec, 2)
                base_category_trend[f"{base_name}|{cat}"] = month_series

                end_qty = month_series[selected_index] if month_series[selected_index] is not None else 0.0
                begin_qty = month_series[selected_index - 1] if selected_index > 0 and month_series[selected_index - 1] is not None else 0.0
                ratio = (end_qty / capacity * 100) if capacity > 0 else 0.0
                items.append({
                    "base": base_name,
                    "category": cat,
                    "period": labels[selected_index],
                    "begin_qty": round(begin_qty, 2),
                    "end_qty": round(end_qty, 2),
                    "available_qty": round(end_qty * 0.95, 2),
                    "capacity": round(capacity, 2),
                    "ratio_pct": round(ratio, 1),
                    "safety_qty": safety_qty,
                    "status": "高位" if ratio > 85 else ("低位" if ratio < 30 else "正常"),
                })

                for idx in range(12):
                    val = month_series[idx]
                    if val is None:
                        continue
                    if cat == "熟料":
                        clinker_total[idx] = round((clinker_total[idx] or 0) + val, 2)
                    else:
                        cement_total[idx] = round((cement_total[idx] or 0) + val, 2)

        total_inventory = []
        for idx in range(12):
            c1 = clinker_total[idx]
            c2 = cement_total[idx]
            if c1 is None and c2 is None:
                total_inventory.append(None)
            else:
                total_inventory.append(round((c1 or 0) + (c2 or 0), 2))

        return {
            "period": "year",
            "point": f"{year}-{month:02d}",
            "items": items,
            "trend": {
                "months": labels,
                "total_inventory": total_inventory,
                "clinker_inventory": clinker_total if target_category != "水泥" else _empty_or_zero(12, True),
                "cement_inventory": cement_total if target_category != "熟料" else _empty_or_zero(12, True),
                "base_category_trend": base_category_trend,
                "safety_line": round(total_safety, 2),
            },
        }

    month_label = f"{year}-{month:02d}"
    labels = []
    clinker_total = []
    cement_total = []
    total_safety = 0.0
    max_len = 0
    base_series_pack = {}

    for base_name in BASES:
        if base and base_name != base:
            continue
        base_daily = inventory_source.get(base_name, {"days": [], "clinker_inventory": [], "cement_inventory": []})
        days = list(base_daily.get("days", []))
        clinker_series = _to_wan_series(base_daily.get("clinker_inventory", []))
        cement_series = _to_wan_series(base_daily.get("cement_inventory", []))
        if not labels and days:
            labels = days
        max_len = max(max_len, len(days), len(clinker_series), len(cement_series))
        base_series_pack[base_name] = {
            "days": days,
            "clinker": clinker_series,
            "cement": cement_series,
        }

    if not labels and max_len > 0:
        labels = [f"{month}月{i + 1}日" for i in range(max_len)]

    clinker_total = [0.0 for _ in range(len(labels))]
    cement_total = [0.0 for _ in range(len(labels))]

    for base_name, pack in base_series_pack.items():
        clinker_series = pack["clinker"]
        cement_series = pack["cement"]
        for cat in category_list:
            capacity = float(INVENTORY_CAPACITY.get(f"{base_name}|{cat}", 0.0))
            safety_qty = round(capacity * 0.25, 2)
            total_safety += safety_qty
            series = clinker_series if cat == "熟料" else cement_series
            normalized = [round(series[i], 2) if i < len(series) else None for i in range(len(labels))]
            base_category_trend[f"{base_name}|{cat}"] = normalized

            end_qty = normalized[-1] if normalized and normalized[-1] is not None else 0.0
            begin_qty = normalized[-2] if len(normalized) >= 2 and normalized[-2] is not None else 0.0
            ratio = (end_qty / capacity * 100) if capacity > 0 else 0.0
            items.append({
                "base": base_name,
                "category": cat,
                "period": month_label,
                "date": labels[-1] if labels else "",
                "begin_qty": round(begin_qty, 2),
                "end_qty": round(end_qty, 2),
                "available_qty": round(end_qty * 0.95, 2),
                "capacity": round(capacity, 2),
                "ratio_pct": round(ratio, 1),
                "safety_qty": safety_qty,
                "status": "高位" if ratio > 85 else ("低位" if ratio < 30 else "正常"),
            })

            for idx in range(len(labels)):
                val = normalized[idx]
                if val is None:
                    continue
                if cat == "熟料":
                    clinker_total[idx] = round(clinker_total[idx] + val, 2)
                else:
                    cement_total[idx] = round(cement_total[idx] + val, 2)

    total_inventory = [round(clinker_total[idx] + cement_total[idx], 2) for idx in range(len(labels))]
    return {
        "period": "month",
        "point": month_label,
        "items": items,
        "trend": {
            "months": labels,
            "total_inventory": total_inventory,
            "clinker_inventory": clinker_total if target_category != "水泥" else [0.0 for _ in range(len(labels))],
            "cement_inventory": cement_total if target_category != "熟料" else [0.0 for _ in range(len(labels))],
            "base_category_trend": base_category_trend,
            "safety_line": round(total_safety, 2),
        },
    }


@router.get("/sales")
def query_sales(
    period: str = "month",
    base: Optional[str] = None,
    region: Optional[str] = None,
    point: Optional[str] = None,
):
    resolved_month = "2025-12"
    if period == "year" and point and len(point) >= 4 and point[:4].isdigit():
        if point[:4] == "2025":
            resolved_month = "2025-12"
    elif point and len(point) >= 7:
        month_text = point[:7]
        if month_text.startswith("2025-") and month_text[5:7].isdigit():
            month_num = int(month_text[5:7])
            if 1 <= month_num <= 12:
                resolved_month = month_text
    payload = december_sales_service.get_sales_payload(
        base=base or "",
        region=region or "",
        month=resolved_month,
    )
    return {
        "period": period,
        "point": resolved_month,
        "items": payload["items"],
        "price_trend": payload["price_trend"],
        "model_stats": payload.get("model_stats", []),
        "customer_mix": payload.get("customer_mix", {"by_type": [], "by_region_type": []}),
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
