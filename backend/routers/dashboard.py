import os
from fastapi import APIRouter, Query, HTTPException, Header, Depends
from typing import Optional
import random
from pydantic import BaseModel

from services.region_config_service import region_config_service
from services.audit_service import audit_service
from routers.auth import read_users_me
from schemas.auth import UserRead

router = APIRouter()

BASES = ["安砂建福", "永安建福", "顺昌炼石", "福州炼石", "宁德建福", "金银湖水泥"]
class RegionConfigModel(BaseModel):
    region_city_map: dict
    metric_units: dict
    region_coords: dict
    region_colors: dict


@router.get("/kpi")
def get_kpi(start_date: Optional[str] = None, end_date: Optional[str] = None):
    return {
        "production": {"value": 68.4, "unit": "万吨", "change": 5.2, "plan": 87.5, "percent": 78},
        "sales": {"value": 62.1, "unit": "万吨", "change": 3.8, "target": 73.0, "percent": 85},
        "inventory": {"value": 32.6, "unit": "万吨", "change": -1.2, "capacity": 52.5, "percent": 62},
        "balance_index": {"value": 0.92, "level": "良好", "components": {
            "production_sales_ratio": 0.95,
            "inventory_health": 0.88,
            "demand_fulfillment": 0.94,
        }},
    }


@router.get("/production")
def get_production(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = Query(None),
):
    base_production = [6.3, 10.4, 6.1, 4.8, 3.3, 0.0]
    base_capacity = [21.2, 5.9, 16.64, 5.5, 5.15, 15.7]
    base_inventory = [4.53, 3.69, 3.68, 2.0, 0.59, 3.68]
    return {
        "bases": [
            {
                "name": name,
                "lng": lng, "lat": lat,
                "production": prod,
                "capacity": cap,
                "utilization": round(prod / cap * 100, 1) if cap else 0,
                "utilization_val": round(prod / cap * 100, 1) if cap else 0,
                "inventory": stock,
            }
            for (name, prod, cap, stock), (lng, lat) in zip(
                zip(BASES, base_production, base_capacity, base_inventory),
                [(117.47, 26.72), (117.37, 25.98), (117.81, 26.80), (119.31, 26.08), (119.53, 26.66), (117.99, 24.71)]
            )
        ],
        "trend": {
            "months": [f"2025-{m:02d}" for m in range(1, 13)],
            "production": [58, 52, 61, 64, 59, 68, 72, 70, 65, 68, 71, 68],
            "sales": [55, 50, 58, 60, 56, 65, 69, 67, 62, 64, 68, 62],
        },
    }


@router.get("/sales")
def get_sales(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    region: Optional[str] = Query(None),
):
    config = region_config_service.get_config()
    regions = list((config.get("region_city_map") or {}).keys())
    sales_data = [11.2, 10.5, 9.8, 7.6, 6.4, 5.9, 4.8, 3.5, 4.2]
    if len(regions) > len(sales_data):
        sales_data.extend([round(3.2 + random.uniform(0, 1.6), 1) for _ in range(len(regions) - len(sales_data))])
    return {
        "regions": [
            {
                "name": name,
                "qty": qty,
                "avg_price": round(350 + random.uniform(0, 80), 0),
                "amount": round(qty * (350 + random.uniform(0, 80)), 0),
            }
            for idx, name in enumerate(regions)
            for qty in [sales_data[idx]]
        ],
        "category_split": {"水泥": 42.5, "熟料": 18.3, "骨料": 7.6},
        "package_split": {"散装": 38.5, "袋装": 23.6},
    }


@router.get("/region-config")
def get_region_config():
    return region_config_service.get_config()


@router.put("/region-config", response_model=RegionConfigModel)
def update_region_config(
    payload: RegionConfigModel,
    current_user: UserRead = Depends(read_users_me),
):
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="仅管理员可修改区域配置")
    
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    updated = region_config_service.update_config(data)
    audit_service.record(
        action="dashboard.region_config.update",
        operator=current_user.username,
        details={"keys": ["region_city_map", "metric_units", "region_coords", "region_colors"]},
    )
    return updated
