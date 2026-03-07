from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_ALIAS = {
    "福建安砂建福水泥有限公司": "安砂建福",
    "福建永安建福水泥有限公司": "永安建福",
    "福建顺昌炼石水泥有限公司": "顺昌炼石",
    "福州炼石水泥有限公司": "福州炼石",
    "福建省永安 金银湖水泥有限公司": "金银湖水泥",
    "福建安砂建福水泥有限公司德化分公司": "安砂建福",
    "安砂建福德化分公司": "安砂建福",
}


def _to_float(value: Any) -> float:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except Exception:
        return 0.0


def _normalize_base(name: str) -> str:
    text = str(name or "").strip()
    return BASE_ALIAS.get(text, text)


def _normalize_model(spec: str, material_name: str = "") -> str:
    model = str(spec or "").strip().replace(" ", "")
    if model and model.lower() != "nan":
        return model
    return "熟料"


def _normalize_package(pkg: str, material_name: str = "", spec: str = "") -> str:
    text = str(pkg or "").strip()
    if "熟料" in text or "熟料" in str(material_name or ""):
        return "熟料"
    if "袋" in text:
        return "袋"
    if "散" in text:
        return "散"
    if not str(spec or "").strip():
        return "熟料"
    return ""


class DecemberSalesService:
    def __init__(self):
        self.sales_path = Path(__file__).resolve().parents[2] / "12月销售数据.xls"

    @lru_cache(maxsize=1)
    def _load_rows(self) -> pd.DataFrame:
        if not self.sales_path.exists():
            return pd.DataFrame(columns=["出库日期", "库存组织", "部门", "物料名称", "型号", "规格", "数量", "含税净价", "价税合计"])
        df = pd.read_excel(self.sales_path, sheet_name=0)
        expected_columns = [
            "出库日期",
            "库存组织",
            "部门",
            "订单客户",
            "开票客户",
            "地区分类",
            "客户类型细分",
            "客户类型",
            "到达地",
            "市场类型",
            "物料名称",
            "型号",
            "规格",
            "数量",
            "含税净价",
            "价税合计",
        ]
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_columns].copy()
        df["出库日期"] = pd.to_datetime(df["出库日期"], errors="coerce")
        df["inventory_org"] = df["库存组织"].astype(str).str.strip()
        df["base"] = df["库存组织"].map(_normalize_base)
        df["region"] = df["部门"].astype(str).str.strip()
        df["order_customer"] = df["订单客户"].astype(str).str.strip()
        df["invoice_customer"] = df["开票客户"].astype(str).str.strip()
        df["region_layer"] = df["地区分类"].astype(str).str.strip()
        df["customer_type_detail"] = df["客户类型细分"].astype(str).str.strip()
        df["customer_type"] = df["客户类型"].astype(str).str.strip()
        df["destination"] = df["到达地"].astype(str).str.strip()
        df["market_type"] = df["市场类型"].astype(str).str.strip()
        df["material_name"] = df["物料名称"].astype(str).str.replace(" ", "", regex=False).str.strip()
        df["spec"] = df["型号"].astype(str).str.strip()
        df["package"] = df["规格"].astype(str).str.strip()
        df["model"] = df.apply(lambda row: _normalize_model(row["spec"], row["material_name"]), axis=1)
        df["package_kind"] = df.apply(lambda row: _normalize_package(row["package"], row["material_name"], row["spec"]), axis=1)
        df["qty_ton"] = df["数量"].map(_to_float)
        df["line_amount_yuan"] = df["价税合计"].map(_to_float)
        df["month_key"] = df["出库日期"].dt.strftime("%Y-%m")
        return df

    def get_sales_payload(self, base: str = "", region: str = "", month: str = "2025-12") -> Dict[str, Any]:
        year = str(month)[:4] if len(str(month)) >= 4 else "2025"
        df = self._load_rows().copy()
        if df.empty:
            return {"items": [], "price_trend": {"months": [], "qty": [], "avg_price": []}}
        month_df = df[df["month_key"] == month].copy()
        if base:
            month_df = month_df[month_df["base"] == base]
        if region:
            month_df = month_df[month_df["region"] == region]

        if month_df.empty:
            return {
                "items": [],
                "price_trend": {"months": [month], "qty": [0], "avg_price": [0]},
            }

        group_cols = [
            "inventory_org",
            "base",
            "region",
            "destination",
            "order_customer",
            "invoice_customer",
            "customer_type",
            "customer_type_detail",
            "market_type",
            "material_name",
            "model",
            "package_kind",
        ]
        grouped = (
            month_df.groupby(group_cols, dropna=False)
            .agg(qty_ton=("qty_ton", "sum"), amount_yuan=("line_amount_yuan", "sum"))
            .reset_index()
        )
        grouped["avg_price"] = grouped.apply(
            lambda row: row["amount_yuan"] / row["qty_ton"] if row["qty_ton"] > 0 else 0,
            axis=1,
        )
        items: List[Dict[str, Any]] = [
            {
                "inventory_org": str(row["inventory_org"]),
                "base": str(row["base"]),
                "region": str(row["region"]),
                "destination": str(row["destination"]),
                "order_customer": str(row["order_customer"]),
                "invoice_customer": str(row["invoice_customer"]),
                "customer_type": str(row["customer_type"]),
                "customer_type_detail": str(row["customer_type_detail"]),
                "market_type": str(row["market_type"]),
                "material_name": str(row["material_name"]),
                "spec": str(row["model"]),
                "package": str(row["package_kind"]),
                "qty": round(float(row["qty_ton"]) / 10000, 2),
                "avg_price": round(float(row["avg_price"]), 0),
                "amount": round(float(row["amount_yuan"]) / 10000, 2),
            }
            for _, row in grouped.iterrows()
        ]

        year_months = [f"{year}-{m:02d}" for m in range(1, 13)]
        year_scope = df[df["month_key"].astype(str).str.startswith(f"{year}-")].copy()
        if base:
            year_scope = year_scope[year_scope["base"] == base]
        if region:
            year_scope = year_scope[year_scope["region"] == region]
        monthly_group = (
            year_scope.groupby("month_key", dropna=False)
            .agg(qty_ton=("qty_ton", "sum"), amount_yuan=("line_amount_yuan", "sum"))
            .reset_index()
        )
        month_map = {
            str(row["month_key"]): {
                "qty": float(row["qty_ton"]),
                "amount": float(row["amount_yuan"]),
            }
            for _, row in monthly_group.iterrows()
        }
        trend_qty: List[float] = []
        trend_price: List[float] = []
        for ym in year_months:
            hit = month_map.get(ym, {"qty": 0.0, "amount": 0.0})
            qty = float(hit["qty"])
            amount = float(hit["amount"])
            trend_qty.append(round(qty / 10000, 2))
            trend_price.append(round(amount / qty, 0) if qty > 0 else 0)
        price_trend = {"months": year_months, "qty": trend_qty, "avg_price": trend_price}

        total_qty = float(month_df["qty_ton"].sum())
        total_amount = float(month_df["line_amount_yuan"].sum())
        customer_type_group = (
            month_df.groupby("customer_type", dropna=False)
            .agg(qty_ton=("qty_ton", "sum"), amount_yuan=("line_amount_yuan", "sum"))
            .reset_index()
            .sort_values("amount_yuan", ascending=False)
        )
        by_type = [
            {
                "customer_type": str(row["customer_type"] or "未分类"),
                "qty": round(float(row["qty_ton"]) / 10000, 2),
                "amount": round(float(row["amount_yuan"]) / 10000, 2),
                "qty_ratio": round(float(row["qty_ton"]) / total_qty, 4) if total_qty > 0 else 0.0,
                "amount_ratio": round(float(row["amount_yuan"]) / total_amount, 4) if total_amount > 0 else 0.0,
            }
            for _, row in customer_type_group.iterrows()
        ]
        region_type_group = (
            month_df.groupby(["region", "customer_type"], dropna=False)
            .agg(qty_ton=("qty_ton", "sum"), amount_yuan=("line_amount_yuan", "sum"))
            .reset_index()
        )
        region_totals_map = (
            month_df.groupby("region", dropna=False)
            .agg(region_qty=("qty_ton", "sum"), region_amount=("line_amount_yuan", "sum"))
            .reset_index()
        )
        region_totals = {
            str(row["region"]): {
                "qty": float(row["region_qty"]),
                "amount": float(row["region_amount"]),
            }
            for _, row in region_totals_map.iterrows()
        }
        by_region_type = []
        for _, row in region_type_group.iterrows():
            region_name = str(row["region"] or "")
            region_total = region_totals.get(region_name, {"qty": 0.0, "amount": 0.0})
            qty_val = float(row["qty_ton"])
            amount_val = float(row["amount_yuan"])
            by_region_type.append(
                {
                    "region": region_name,
                    "customer_type": str(row["customer_type"] or "未分类"),
                    "qty": round(qty_val / 10000, 2),
                    "amount": round(amount_val / 10000, 2),
                    "region_qty_ratio": round(qty_val / region_total["qty"], 4) if region_total["qty"] > 0 else 0.0,
                    "region_amount_ratio": round(amount_val / region_total["amount"], 4) if region_total["amount"] > 0 else 0.0,
                    "global_amount_ratio": round(amount_val / total_amount, 4) if total_amount > 0 else 0.0,
                    "global_qty_ratio": round(qty_val / total_qty, 4) if total_qty > 0 else 0.0,
                }
            )

        model_stats_df = (
            month_df.groupby("model", dropna=False)
            .agg(rows=("model", "count"))
            .reset_index()
            .sort_values("rows", ascending=False)
        )
        model_stats = [
            {"model": str(row["model"]), "count": int(row["rows"])}
            for _, row in model_stats_df.iterrows()
            if str(row["model"]).strip()
        ]
        customer_mix = {
            "metric_unit": {"qty": "万吨", "amount": "万元"},
            "total_qty": round(total_qty / 10000, 2),
            "total_amount": round(total_amount / 10000, 2),
            "by_type": by_type,
            "by_region_type": by_region_type,
        }
        return {"items": items, "price_trend": price_trend, "model_stats": model_stats, "customer_mix": customer_mix}


december_sales_service = DecemberSalesService()
