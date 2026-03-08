import logging
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from services.december_report_service import december_report_service, BASE_NAMES
from services.december_sales_service import december_sales_service
from services.data_paths import resolve_data_file

logger = logging.getLogger(__name__)


class DBService:
    def __init__(self):
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._loaded = False

    def _build_production_df(self) -> pd.DataFrame:
        cement_rows = december_report_service.get_production_report(period="month", point="2025-12", base="", category="")
        clinker_rows = december_report_service.get_production_report(period="month", point="2025-12", base="", category="clinker")
        rows = list(cement_rows or []) + list(clinker_rows or [])
        if not rows:
            return pd.DataFrame(columns=["base", "category", "period", "plan_qty", "actual_qty", "variance_pct", "utilization"])
        return pd.DataFrame(rows)

    def _build_inventory_df(self) -> pd.DataFrame:
        parsed = december_report_service._parse_daily_data().get("inventory", {})
        rows: List[Dict[str, Any]] = []
        for base in BASE_NAMES:
            hit = parsed.get(base, {"clinker_inventory": [], "cement_inventory": []})
            clinker_series = list(hit.get("clinker_inventory", []) or [])
            cement_series = list(hit.get("cement_inventory", []) or [])
            clinker = float(clinker_series[-1]) / 10000 if clinker_series else 0.0
            cement = float(cement_series[-1]) / 10000 if cement_series else 0.0
            rows.append({"base": base, "category": "熟料", "period": "2025-12", "end_qty": round(clinker, 2)})
            rows.append({"base": base, "category": "水泥", "period": "2025-12", "end_qty": round(cement, 2)})
        return pd.DataFrame(rows)

    def _build_sales_df(self) -> pd.DataFrame:
        payload = december_sales_service.get_sales_payload(base="", region="", month="2025-12")
        items = payload.get("items", []) or []
        if not items:
            return pd.DataFrame(columns=["base", "region", "spec", "package", "qty", "avg_price", "amount", "period"])
        df = pd.DataFrame(items)
        df["period"] = "2025-12"
        return df

    def _build_orders_df(self) -> pd.DataFrame:
        path = resolve_data_file("12月销售订单数据.xls")
        if not path.exists():
            return pd.DataFrame(columns=["base", "region", "material_name", "spec", "package", "order_qty", "outbound_qty", "period"])
        df = pd.read_excel(path, sheet_name=0)
        required_cols = ["库存组织", "部门", "物料名称", "型号", "规格", "主数量", "出库主数量", "单据日期"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        local_alias = {
            "福建安砂建福水泥有限公司": "安砂建福",
            "福建永安建福水泥有限公司": "永安建福",
            "福建顺昌炼石水泥有限公司": "顺昌炼石",
            "福州炼石水泥有限公司": "福州炼石",
            "福建省永安 金银湖水泥有限公司": "金银湖水泥",
            "福建安砂建福水泥有限公司德化分公司": "安砂建福",
            "安砂建福德化分公司": "安砂建福",
        }
        out = pd.DataFrame()
        out["base"] = df["库存组织"].astype(str).str.strip().map(lambda x: local_alias.get(x, x))
        out["region"] = df["部门"].astype(str).str.strip()
        out["material_name"] = df["物料名称"].astype(str).str.strip()
        out["spec"] = df["型号"].astype(str).str.strip()
        out["package"] = df["规格"].astype(str).str.strip()
        out["order_qty"] = pd.to_numeric(df["主数量"], errors="coerce").fillna(0) / 10000
        out["outbound_qty"] = pd.to_numeric(df["出库主数量"], errors="coerce").fillna(0) / 10000
        dt = pd.to_datetime(df["单据日期"], errors="coerce")
        out["period"] = dt.dt.strftime("%Y-%m").fillna("2025-12")
        out = out[out["period"] == "2025-12"].copy()
        return out

    def _ensure_loaded(self):
        if self._loaded:
            return
        production_df = self._build_production_df()
        inventory_df = self._build_inventory_df()
        sales_df = self._build_sales_df()
        orders_df = self._build_orders_df()
        production_df.to_sql("fact_production", self._conn, if_exists="replace", index=False)
        inventory_df.to_sql("fact_inventory", self._conn, if_exists="replace", index=False)
        sales_df.to_sql("fact_sales", self._conn, if_exists="replace", index=False)
        orders_df.to_sql("fact_orders", self._conn, if_exists="replace", index=False)
        self._loaded = True

    def get_schema_info(self) -> str:
        self._ensure_loaded()
        return """
Table: fact_production
Columns: base (TEXT), category (TEXT), period (TEXT), plan_qty (REAL), actual_qty (REAL), variance_pct (REAL), utilization (REAL), daily_prod (REAL), month_prod (REAL), year_prod (REAL), daily_out (REAL), month_out (REAL), year_out (REAL), month_sale (REAL), year_sale (REAL)
Description: 生产月报数据（2025-12，单位万吨）。

Table: fact_inventory
Columns: base (TEXT), category (TEXT), period (TEXT), end_qty (REAL)
Description: 12月末库存数据（单位万吨）。

Table: fact_sales
Columns: base (TEXT), region (TEXT), spec (TEXT), package (TEXT), qty (REAL), avg_price (REAL), amount (REAL), period (TEXT)
Description: 12月销售汇总数据（qty/amount 为万吨）。

Table: fact_orders
Columns: base (TEXT), region (TEXT), material_name (TEXT), spec (TEXT), package (TEXT), order_qty (REAL), outbound_qty (REAL), period (TEXT)
Description: 12月销售订单执行数据（单位万吨）。

Base Alias:
安砂=安砂建福, 永安=永安建福, 顺昌=顺昌炼石, 福州=福州炼石, 宁德=宁德建福, 金银湖=金银湖水泥
"""

    def _rewrite_base_alias(self, sql: str) -> str:
        alias_map = {
            "安砂": "安砂建福",
            "永安": "永安建福",
            "顺昌": "顺昌炼石",
            "福州": "福州炼石",
            "宁德": "宁德建福",
            "金银湖": "金银湖水泥",
        }
        text = sql
        for alias, target in alias_map.items():
            pattern = rf"(?i)\b(base|base_name)\s*=\s*'({re.escape(alias)})'"
            text = re.sub(pattern, rf"\1 LIKE '%{target}%'", text)
            pattern_dq = rf'(?i)\b(base|base_name)\s*=\s*"({re.escape(alias)})"'
            text = re.sub(pattern_dq, rf"\1 LIKE '%{target}%'", text)
        return text

    def _extract_day(self, question: str) -> int | None:
        text = str(question or "").replace(" ", "")
        patterns = [
            r"(?:12月|2025-12-)([0-3]?\d)(?:日|号)?",
            r"12[./-]([0-3]?\d)(?:日|号)?",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if not m:
                continue
            day = int(m.group(1))
            if 1 <= day <= 31:
                return day
        return None

    def _extract_base(self, question: str) -> str:
        text = str(question or "")
        alias_map = {
            "安砂": "安砂建福",
            "安砂建福": "安砂建福",
            "永安": "永安建福",
            "永安建福": "永安建福",
            "顺昌": "顺昌炼石",
            "顺昌炼石": "顺昌炼石",
            "福州": "福州炼石",
            "福州炼石": "福州炼石",
            "宁德": "宁德建福",
            "宁德建福": "宁德建福",
            "金银湖": "金银湖水泥",
            "金银湖水泥": "金银湖水泥",
        }
        for key, val in alias_map.items():
            if key in text:
                return val
        return ""

    def build_file_context(self, question: str) -> Dict[str, Any]:
        day = self._extract_day(question)
        base = self._extract_base(question)
        report_path = Path(december_report_service.report_path)
        sales_path = Path(december_sales_service.sales_path)
        orders_path = resolve_data_file("12月销售订单数据.xls")
        source_status = {
            "production_report": report_path.exists(),
            "sales_file": sales_path.exists(),
            "orders_file": orders_path.exists(),
        }
        inventory_daily: List[Dict[str, Any]] = []
        for base_name in BASE_NAMES:
            if base and base_name != base:
                continue
            series = december_report_service.get_base_daily_inventory(base_name)
            clinker = list(series.get("clinker_inventory", []) or [])
            cement = list(series.get("cement_inventory", []) or [])
            if day:
                idx = day - 1
                if idx < len(clinker) and idx < len(cement):
                    inventory_daily.append(
                        {
                            "base": base_name,
                            "day": f"2025-12-{day:02d}",
                            "clinker_inventory_ton": round(float(clinker[idx]), 2),
                            "cement_inventory_ton": round(float(cement[idx]), 2),
                            "clinker_inventory_wt": round(float(clinker[idx]) / 10000, 2),
                            "cement_inventory_wt": round(float(cement[idx]) / 10000, 2),
                        }
                    )
            else:
                if clinker and cement:
                    inventory_daily.append(
                        {
                            "base": base_name,
                            "day": "2025-12-31",
                            "clinker_inventory_ton": round(float(clinker[-1]), 2),
                            "cement_inventory_ton": round(float(cement[-1]), 2),
                            "clinker_inventory_wt": round(float(clinker[-1]) / 10000, 2),
                            "cement_inventory_wt": round(float(cement[-1]) / 10000, 2),
                        }
                    )
        if inventory_daily and all(
            float(item.get("clinker_inventory_wt") or 0.0) == 0.0 and float(item.get("cement_inventory_wt") or 0.0) == 0.0
            for item in inventory_daily
        ):
            inventory_daily = []
        point = f"2025-12-{(day or 31):02d}"
        production_rows = december_report_service.get_production_report(period="day", point=point, base=base, category="")
        production_rows = production_rows[:20]
        if production_rows and all(
            float(item.get("actual_qty") or 0.0) == 0.0 and float(item.get("month_prod") or 0.0) == 0.0
            for item in production_rows
        ):
            production_rows = []
        sales_payload = december_sales_service.get_sales_payload(base=base, region="", month="2025-12")
        sales_items = list(sales_payload.get("items", []) or [])[:40]
        if sales_items and all(
            float(item.get("qty") or 0.0) == 0.0 and float(item.get("amount") or 0.0) == 0.0
            for item in sales_items
        ):
            sales_items = []
        orders_df = self._build_orders_df()
        if base and not orders_df.empty:
            orders_df = orders_df[orders_df["base"] == base]
        order_rows: List[Dict[str, Any]] = []
        if not orders_df.empty:
            grouped = (
                orders_df.groupby("base", dropna=False)
                .agg(order_qty=("order_qty", "sum"), outbound_qty=("outbound_qty", "sum"))
                .reset_index()
                .sort_values("order_qty", ascending=False)
            )
            order_rows = [
                {
                    "base": str(row["base"]),
                    "order_qty": round(float(row["order_qty"]), 2),
                    "outbound_qty": round(float(row["outbound_qty"]), 2),
                }
                for _, row in grouped.head(20).iterrows()
            ]
        if order_rows and all(
            float(item.get("order_qty") or 0.0) == 0.0 and float(item.get("outbound_qty") or 0.0) == 0.0
            for item in order_rows
        ):
            order_rows = []
        if not source_status["orders_file"]:
            order_rows = []
        available_sections = {
            "inventory_daily": bool(inventory_daily),
            "production_daily": bool(production_rows),
            "sales_items": bool(sales_items),
            "orders_summary": bool(order_rows),
        }
        core_ready = bool(inventory_daily) or bool(production_rows) or bool(sales_items) or bool(order_rows)
        return {
            "scope": "2025-12",
            "question": question,
            "base_hint": base,
            "day_hint": day,
            "sources": [
                "福建水泥2025年12月生产日报表.xlsx",
                "12月销售数据.xls",
                "12月销售订单数据.xls",
            ],
            "unit_hint": {
                "inventory_daily_primary": "万吨（*_wt）",
                "inventory_daily_backup": "吨（*_ton）",
                "production_daily": "万吨",
                "sales_items": "qty/amount为万吨",
                "orders_summary": "万吨",
            },
            "inventory_daily": inventory_daily,
            "production_daily": production_rows,
            "sales_items": sales_items,
            "orders_summary": order_rows,
            "data_status": {
                "source_status": source_status,
                "available_sections": available_sections,
                "ready": core_ready,
                "missing_sources": [k for k, v in source_status.items() if not v],
            },
        }

    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        text = (sql or "").strip()
        if not text:
            return []
        normalized = text.lower()
        if not normalized.startswith("select"):
            raise ValueError("仅允许执行SELECT查询")
        text = self._rewrite_base_alias(text)
        try:
            cursor = self._conn.execute(text)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as exc:
            logger.error(f"SQL execute failed: {exc}; sql={text}")
            raise RuntimeError(f"SQL执行失败: {exc}")

db_service = DBService()
