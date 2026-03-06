from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Any
import calendar
import random
import re

import pandas as pd


BASE_NAMES = ["安砂建福", "永安建福", "顺昌炼石", "福州炼石", "宁德建福", "金银湖水泥"]
BASE_PLAN_TON = {
    "安砂建福": 190000.0,
    "永安建福": 175000.0,
    "顺昌炼石": 122000.0,
    "福州炼石": 82000.0,
    "宁德建福": 69000.0,
    "金银湖水泥": 12000.0,
}


def _to_float(value) -> float:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except Exception:
        return 0.0


def _parse_stop_reason_counts(text: str) -> Dict[str, int]:
    content = (text or "").replace("：", ":")
    if not content:
        return {"续停": 0, "避峰": 0, "检修": 0, "故障": 0, "其他": 0}
    counts = {"续停": 0, "避峰": 0, "检修": 0, "故障": 0, "其他": 0}
    segments = [seg for seg in content.replace("。", "；").split("；") if seg.strip()]
    for seg in segments:
        s = seg.strip()
        if ("续停" in s) or ("停机" in s and "避峰" not in s and "检修" not in s and "故障" not in s):
            counts["续停"] += 1
        elif "避峰" in s:
            counts["避峰"] += 1
        elif "检修" in s:
            counts["检修"] += 1
        elif ("故障" in s) or ("异常" in s):
            counts["故障"] += 1
        else:
            counts["其他"] += 1
    return counts


def _is_equipment_name(name: str) -> bool:
    text = (name or "").strip().replace(" ", "")
    if not text:
        return False
    if any(mark in text for mark in [":", "：", "。", "；", "，", "续停", "停机", "检修", "避峰", "续停机", "运行状况"]):
        return False
    if not re.match(r"^(回转窑[0-9A-Za-z#]*|水泥磨[0-9A-Za-z#]*|辊压机[0-9A-Za-z#]*|德化[0-9A-Za-z#]*|徳化[0-9A-Za-z#]*)$", text):
        return False
    return len(text) <= 12


class DecemberReportService:
    def __init__(self):
        self.report_path = Path(__file__).resolve().parents[2] / "福建水泥2025年12月生产日报表.xlsx"

    @lru_cache(maxsize=1)
    def _parse_daily_data(self) -> Dict[str, Any]:
        inventory_result = {
            base: {"days": [], "clinker_inventory": [], "cement_inventory": []}
            for base in BASE_NAMES
        }
        production_result: Dict[int, Dict[str, Dict[str, float]]] = {}
        equipment_summary_result: Dict[int, Dict[str, Dict[str, float]]] = {}
        equipment_detail_result: Dict[int, List[Dict[str, Any]]] = {}
        stop_reason_result: Dict[int, Dict[str, Dict[str, int]]] = {}
        if not self.report_path.exists():
            return {"inventory": inventory_result, "production": production_result, "equipment_summary": equipment_summary_result, "equipment_detail": equipment_detail_result, "stop_reason": stop_reason_result}

        for day in range(1, 32):
            sheet_name = str(day)
            try:
                df = pd.read_excel(self.report_path, sheet_name=sheet_name, header=None, dtype=str).fillna("")
            except Exception:
                continue

            current_base = ""
            day_inventory = {base: {"clinker": None, "cement": None} for base in BASE_NAMES}
            day_production = {
                base: {
                    "plan_qty": 0.0,
                    "daily_prod": 0.0,
                    "month_prod": 0.0,
                    "year_prod": 0.0,
                    "daily_out": 0.0,
                    "month_out": 0.0,
                    "year_out": 0.0,
                }
                for base in BASE_NAMES
            }
            day_equipment_summary = {
                base: {
                    "run_rate_day_sum": 0.0,
                    "run_rate_month_sum": 0.0,
                    "run_rate_year_sum": 0.0,
                    "runtime_day_sum": 0.0,
                    "runtime_month_sum": 0.0,
                    "runtime_year_sum": 0.0,
                    "stop_hours_day_sum": 0.0,
                    "count": 0.0,
                    "stop_count": 0.0,
                }
                for base in BASE_NAMES
            }
            day_equipment_details: List[Dict[str, Any]] = []
            current_equipment_base = ""
            day_stop_reasons = {
                base: {"续停": 0, "避峰": 0, "检修": 0, "故障": 0, "其他": 0}
                for base in BASE_NAMES
            }
            for _, row in df.iterrows():
                row_values = row.astype(str).tolist()
                col0 = str(row_values[0]).strip() if len(row_values) > 0 else ""
                col1 = str(row_values[1]).replace("\n", "").replace(" ", "") if len(row_values) > 1 else ""
                col14 = str(row_values[14]).strip() if len(row_values) > 14 else ""
                col15 = str(row_values[15]).strip() if len(row_values) > 15 else ""
                col16 = str(row_values[16]).replace("\n", "").replace(" ", "") if len(row_values) > 16 else ""
                if col0 in BASE_NAMES:
                    current_base = col0
                if current_base in BASE_NAMES:
                    period_start_inventory = _to_float(row_values[4] if len(row_values) > 4 else 0)
                    month_cum_prod = _to_float(row_values[7] if len(row_values) > 7 else 0)
                    month_cum_out = _to_float(row_values[10] if len(row_values) > 10 else 0)
                    inventory = round(period_start_inventory + month_cum_prod - month_cum_out, 2)

                    if "水泥生产/出厂" in col1:
                        day_inventory[current_base]["cement"] = inventory
                        day_production[current_base]["plan_qty"] = _to_float(row_values[4] if len(row_values) > 4 else 0)
                        day_production[current_base]["daily_prod"] = _to_float(row_values[6] if len(row_values) > 6 else 0)
                        day_production[current_base]["month_prod"] = _to_float(row_values[7] if len(row_values) > 7 else 0)
                        day_production[current_base]["year_prod"] = _to_float(row_values[8] if len(row_values) > 8 else 0)
                        day_production[current_base]["daily_out"] = _to_float(row_values[9] if len(row_values) > 9 else 0)
                        day_production[current_base]["month_out"] = _to_float(row_values[10] if len(row_values) > 10 else 0)
                        day_production[current_base]["year_out"] = _to_float(row_values[11] if len(row_values) > 11 else 0)
                    if "熟料" in col1:
                        day_inventory[current_base]["clinker"] = inventory

                if col15 in BASE_NAMES:
                    current_equipment_base = col15
                if col14 == "设备运行状况" and col15 in BASE_NAMES:
                    reason_counts = _parse_stop_reason_counts(col16)
                    for key in day_stop_reasons[col15]:
                        day_stop_reasons[col15][key] += int(reason_counts.get(key, 0))
                if _is_equipment_name(col16) and current_equipment_base in BASE_NAMES:
                    throughput_day = _to_float(row_values[17] if len(row_values) > 17 else 0)
                    throughput_month = _to_float(row_values[18] if len(row_values) > 18 else 0)
                    throughput_year = _to_float(row_values[19] if len(row_values) > 19 else 0)
                    run_rate_day = _to_float(row_values[20] if len(row_values) > 20 else 0)
                    run_rate_month = _to_float(row_values[21] if len(row_values) > 21 else 0)
                    run_rate_year = _to_float(row_values[22] if len(row_values) > 22 else 0)
                    runtime_day = _to_float(row_values[23] if len(row_values) > 23 else 0)
                    runtime_month = _to_float(row_values[24] if len(row_values) > 24 else 0)
                    runtime_year = _to_float(row_values[25] if len(row_values) > 25 else 0)
                    stop_hours_day = round(max(0.0, 24 - runtime_day), 2)
                    stop_hours_month = round(max(0.0, 24 * 31 - runtime_month), 2)
                    stop_hours_year = round(max(0.0, 24 * 365 - runtime_year), 2)
                    stop_count = 1 if (run_rate_day <= 0 and runtime_day <= 0) else 0
                    day_equipment_details.append({
                        "base": current_equipment_base,
                        "device": col16,
                        "device_key": f"{current_equipment_base}|{col16}",
                        "throughput_day": throughput_day,
                        "throughput_month": throughput_month,
                        "throughput_year": throughput_year,
                        "run_rate_day": run_rate_day,
                        "run_rate_month": run_rate_month,
                        "run_rate_year": run_rate_year,
                        "runtime_day": runtime_day,
                        "runtime_month": runtime_month,
                        "runtime_year": runtime_year,
                        "stop_hours_day": stop_hours_day,
                        "stop_hours_month": stop_hours_month,
                        "stop_hours_year": stop_hours_year,
                        "stop_count": stop_count,
                    })
                    day_equipment_summary[current_equipment_base]["run_rate_day_sum"] += run_rate_day
                    day_equipment_summary[current_equipment_base]["run_rate_month_sum"] += run_rate_month
                    day_equipment_summary[current_equipment_base]["run_rate_year_sum"] += run_rate_year
                    day_equipment_summary[current_equipment_base]["runtime_day_sum"] += runtime_day
                    day_equipment_summary[current_equipment_base]["runtime_month_sum"] += runtime_month
                    day_equipment_summary[current_equipment_base]["runtime_year_sum"] += runtime_year
                    day_equipment_summary[current_equipment_base]["stop_hours_day_sum"] += stop_hours_day
                    day_equipment_summary[current_equipment_base]["stop_hours_month_sum"] = day_equipment_summary[current_equipment_base].get("stop_hours_month_sum", 0.0) + stop_hours_month
                    day_equipment_summary[current_equipment_base]["stop_hours_year_sum"] = day_equipment_summary[current_equipment_base].get("stop_hours_year_sum", 0.0) + stop_hours_year
                    day_equipment_summary[current_equipment_base]["count"] += 1
                    day_equipment_summary[current_equipment_base]["stop_count"] += stop_count

            for base in BASE_NAMES:
                inventory_result[base]["days"].append(f"12月{day}日")
                inventory_result[base]["clinker_inventory"].append(day_inventory[base]["clinker"] if day_inventory[base]["clinker"] is not None else 0.0)
                inventory_result[base]["cement_inventory"].append(day_inventory[base]["cement"] if day_inventory[base]["cement"] is not None else 0.0)
            production_result[day] = day_production
            equipment_summary_result[day] = day_equipment_summary
            equipment_detail_result[day] = day_equipment_details
            stop_reason_result[day] = day_stop_reasons
        return {"inventory": inventory_result, "production": production_result, "equipment_summary": equipment_summary_result, "equipment_detail": equipment_detail_result, "stop_reason": stop_reason_result}

    def get_base_daily_inventory(self, base: str):
        parsed = self._parse_daily_data()["inventory"]
        return parsed.get(base, {"days": [], "clinker_inventory": [], "cement_inventory": []})

    def _apply_category(self, rows: List[Dict[str, float]], category: str) -> List[Dict[str, float]]:
        if category != "clinker":
            return rows
        clinker_rows: List[Dict[str, float]] = []
        for row in rows:
            factor = 0.35
            plan_qty = round(float(row["plan_qty"]) * factor, 2)
            month_prod = round(float(row["month_prod"]) * factor, 2)
            utilization = round((month_prod / plan_qty * 100), 1) if plan_qty > 0 else 0.0
            new_row = {**row}
            new_row["category"] = "熟料"
            new_row["plan_qty"] = plan_qty
            new_row["actual_qty"] = month_prod
            new_row["daily_prod"] = round(float(row["daily_prod"]) * factor, 2)
            new_row["month_prod"] = month_prod
            new_row["year_prod"] = round(float(row["year_prod"]) * factor, 2)
            new_row["daily_out"] = round(float(row["daily_out"]) * factor, 2)
            new_row["month_out"] = round(float(row["month_out"]) * factor, 2)
            new_row["year_out"] = round(float(row["year_out"]) * factor, 2)
            new_row["month_sale"] = new_row["month_out"]
            new_row["year_sale"] = new_row["year_out"]
            new_row["utilization"] = utilization
            new_row["variance_pct"] = round((month_prod - plan_qty) / plan_qty * 100, 1) if plan_qty > 0 else 0.0
            new_row["equipment_status"] = "正常" if utilization >= 70 else "偏低"
            new_row["kiln_stop_hours"] = round(max(0.0, (100 - utilization) / 100 * 24), 1)
            new_row["kiln_stop_times"] = 1 if utilization < 80 else 0
            clinker_rows.append(new_row)
        return clinker_rows

    def get_daily_production_rows(self, day: int, base: str = "", category: str = "") -> List[Dict[str, float]]:
        parsed = self._parse_daily_data()["production"].get(day, {})
        rows: List[Dict[str, float]] = []
        for base_name in BASE_NAMES:
            if base and base_name != base:
                continue
            row = parsed.get(base_name, {})
            if not row:
                continue
            plan_qty = float(row.get("plan_qty", 0.0))
            month_prod = float(row.get("month_prod", 0.0))
            utilization = round((month_prod / plan_qty * 100), 1) if plan_qty > 0 else 0.0
            status = "正常" if utilization >= 70 else "偏低"
            rows.append(
                {
                    "base": base_name,
                    "category": "水泥",
                    "period": f"2025-12-{day:02d}",
                    "day": day,
                    "plan_qty": round(plan_qty / 10000, 2),
                    "actual_qty": round(month_prod / 10000, 2),
                    "variance_pct": round((month_prod - plan_qty) / plan_qty * 100, 1) if plan_qty > 0 else 0.0,
                    "utilization": utilization,
                    "daily_prod": round(float(row.get("daily_prod", 0.0)) / 10000, 2),
                    "month_prod": round(month_prod / 10000, 2),
                    "year_prod": round(float(row.get("year_prod", 0.0)) / 10000, 2),
                    "daily_out": round(float(row.get("daily_out", 0.0)) / 10000, 2),
                    "month_out": round(float(row.get("month_out", 0.0)) / 10000, 2),
                    "year_out": round(float(row.get("year_out", 0.0)) / 10000, 2),
                    "month_sale": round(float(row.get("month_out", 0.0)) / 10000, 2),
                    "year_sale": round(float(row.get("year_out", 0.0)) / 10000, 2),
                    "equipment_status": status,
                    "kiln_stop_hours": round(max(0.0, (100 - utilization) / 100 * 24), 1),
                    "kiln_stop_times": 1 if utilization < 80 else 0,
                }
            )
        return self._apply_category(rows, category)

    def _build_synthetic_rows(self, period: str, point: str, base: str = "", category: str = "") -> List[Dict[str, float]]:
        rows: List[Dict[str, float]] = []
        point_text = point or "2026-01-31"
        year = int(point_text[0:4]) if len(point_text) >= 4 and point_text[0:4].isdigit() else 2026
        month = int(point_text[5:7]) if len(point_text) >= 7 and point_text[5:7].isdigit() else 1
        day = int(point_text[8:10]) if len(point_text) >= 10 and point_text[8:10].isdigit() else calendar.monthrange(year, month)[1]
        days_in_month = calendar.monthrange(year, month)[1]

        for base_name in BASE_NAMES:
            if base and base_name != base:
                continue
            rng = random.Random(f"{base_name}-{point_text}")
            plan_ton = BASE_PLAN_TON.get(base_name, 100000.0)
            month_prod_ton = plan_ton * rng.uniform(0.78, 0.98)
            day_prod_ton = month_prod_ton / days_in_month * rng.uniform(0.85, 1.15)
            year_prod_ton = month_prod_ton * (10 + month / 12) + rng.uniform(10000, 35000)
            month_out_ton = month_prod_ton * rng.uniform(0.92, 1.04)
            day_out_ton = month_out_ton / days_in_month * rng.uniform(0.85, 1.15)
            year_out_ton = year_prod_ton * rng.uniform(0.93, 1.02)
            util = round(month_prod_ton / plan_ton * 100, 1) if plan_ton > 0 else 0.0
            status = "正常" if util >= 75 else ("偏低" if util >= 60 else "预警")
            rows.append(
                {
                    "base": base_name,
                    "category": "水泥",
                    "period": f"{year}-{month:02d}-{day:02d}" if period == "day" else f"{year}-{month:02d}",
                    "day": day,
                    "plan_qty": round(plan_ton / 10000, 2),
                    "actual_qty": round(month_prod_ton / 10000, 2),
                    "variance_pct": round((month_prod_ton - plan_ton) / plan_ton * 100, 1) if plan_ton > 0 else 0.0,
                    "utilization": util,
                    "daily_prod": round(day_prod_ton / 10000, 2),
                    "month_prod": round(month_prod_ton / 10000, 2),
                    "year_prod": round(year_prod_ton / 10000, 2),
                    "daily_out": round(day_out_ton / 10000, 2),
                    "month_out": round(month_out_ton / 10000, 2),
                    "year_out": round(year_out_ton / 10000, 2),
                    "month_sale": round(month_out_ton / 10000, 2),
                    "year_sale": round(year_out_ton / 10000, 2),
                    "equipment_status": status,
                    "kiln_stop_hours": round(max(0.0, (100 - util) / 100 * 24), 1),
                    "kiln_stop_times": 1 if util < 80 else 0,
                }
            )
        return self._apply_category(rows, category)

    def get_production_report(self, period: str = "day", point: str = "", base: str = "", category: str = "") -> List[Dict[str, float]]:
        month = int(point[5:7]) if len(point) >= 7 and point[5:7].isdigit() else 0
        if month == 12:
            day = 31
            if len(point) >= 10 and point[8:10].isdigit():
                day = int(point[8:10])
            if period == "day":
                rows = self.get_daily_production_rows(day=max(1, min(day, 31)), base=base, category=category)
                if rows:
                    return rows
        return self._build_synthetic_rows(period=period, point=point, base=base, category=category)

    def get_equipment_summary(self, point: str, base: str = "") -> List[Dict[str, float]]:
        month = int(point[5:7]) if len(point) >= 7 and point[5:7].isdigit() else 0
        day = int(point[8:10]) if len(point) >= 10 and point[8:10].isdigit() else 31
        if month == 12:
            source = self._parse_daily_data()["equipment_summary"].get(max(1, min(day, 31)), {})
            rows: List[Dict[str, float]] = []
            for base_name in BASE_NAMES:
                if base and base_name != base:
                    continue
                hit = source.get(base_name, {})
                count = float(hit.get("count", 0.0))
                if count <= 0:
                    continue
                rows.append({
                    "base": base_name,
                    "run_rate_day": round(hit["run_rate_day_sum"] / count, 2),
                    "run_rate_month": round(hit["run_rate_month_sum"] / count, 2),
                    "run_rate_year": round(hit["run_rate_year_sum"] / count, 2),
                    "runtime_day": round(hit["runtime_day_sum"] / count, 2),
                    "runtime_month": round(hit["runtime_month_sum"] / count, 2),
                    "runtime_year": round(hit["runtime_year_sum"] / count, 2),
                    "stop_hours_day": round(hit["stop_hours_day_sum"], 2),
                    "stop_hours_month": round(float(hit.get("stop_hours_month_sum", 0.0)), 2),
                    "stop_hours_year": round(float(hit.get("stop_hours_year_sum", 0.0)), 2),
                    "stop_count": int(hit.get("stop_count", 0.0)),
                    "equipment_count": int(count),
                })
            if rows:
                return rows
        prod_rows = self.get_production_report(period="day", point=point, base=base, category="cement")
        return [
            {
                "base": row["base"],
                "run_rate_day": round(row["utilization"] * 0.96, 2),
                "run_rate_month": row["utilization"],
                "run_rate_year": round(min(100.0, row["utilization"] * 1.06), 2),
                "runtime_day": round(24 * row["utilization"] / 100, 2),
                "runtime_month": round(24 * 30 * row["utilization"] / 100 / 6, 2),
                "runtime_year": round(24 * 365 * row["utilization"] / 100 / 6, 2),
                "stop_hours_day": round(max(0.0, 24 - (24 * row["utilization"] / 100)), 2),
                "stop_hours_month": round(max(0.0, 24 * 31 - (24 * 30 * row["utilization"] / 100 / 6)), 2),
                "stop_hours_year": round(max(0.0, 24 * 365 - (24 * 365 * row["utilization"] / 100 / 6)), 2),
                "stop_count": int(row.get("kiln_stop_times", 0)),
                "equipment_count": 6,
            }
            for row in prod_rows
        ]

    def get_equipment_detail(self, point: str, base: str = "") -> List[Dict[str, Any]]:
        month = int(point[5:7]) if len(point) >= 7 and point[5:7].isdigit() else 0
        day = int(point[8:10]) if len(point) >= 10 and point[8:10].isdigit() else 31
        if month == 12:
            detail = self._parse_daily_data()["equipment_detail"].get(max(1, min(day, 31)), [])
            if base:
                detail = [item for item in detail if item.get("base") == base]
            if detail:
                return detail
        summary = self.get_equipment_summary(point=point, base=base)
        rows: List[Dict[str, Any]] = []
        for item in summary:
            rows.append({
                "base": item["base"],
                "device": "主机组",
                "device_key": f"{item['base']}|主机组",
                "throughput_day": 0.0,
                "throughput_month": 0.0,
                "throughput_year": 0.0,
                "run_rate_day": 0.0,
                "run_rate_month": item["run_rate_month"],
                "run_rate_year": item["run_rate_year"],
                "runtime_day": 0.0,
                "runtime_month": item["runtime_month"],
                "runtime_year": item["runtime_year"],
                "stop_hours_day": item.get("stop_hours_day", 0.0),
                "stop_hours_month": item.get("stop_hours_month", 0.0),
                "stop_hours_year": item.get("stop_hours_year", 0.0),
                "stop_count": item.get("stop_count", 0),
            })
        return rows

    def get_stop_reason_summary(self, point: str, base: str = "") -> List[Dict[str, Any]]:
        month = int(point[5:7]) if len(point) >= 7 and point[5:7].isdigit() else 0
        day = int(point[8:10]) if len(point) >= 10 and point[8:10].isdigit() else 31
        if month == 12:
            source = self._parse_daily_data()["stop_reason"].get(max(1, min(day, 31)), {})
            rows: List[Dict[str, Any]] = []
            for base_name in BASE_NAMES:
                if base and base_name != base:
                    continue
                hit = source.get(base_name, {"续停": 0, "避峰": 0, "检修": 0, "故障": 0, "其他": 0})
                rows.append({
                    "base": base_name,
                    "续停": int(hit.get("续停", 0)),
                    "避峰": int(hit.get("避峰", 0)),
                    "检修": int(hit.get("检修", 0)),
                    "故障": int(hit.get("故障", 0)),
                    "其他": int(hit.get("其他", 0)),
                })
            return rows
        summary = self.get_equipment_summary(point=point, base=base)
        return [
            {
                "base": item["base"],
                "续停": int(item.get("stop_count", 0)),
                "避峰": 0,
                "检修": 0,
                "故障": 0,
                "其他": 0,
            }
            for item in summary
        ]


december_report_service = DecemberReportService()
