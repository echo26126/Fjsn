from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

router = APIRouter()


@router.get("/templates")
def get_templates():
    return {
        "templates": [
            {"key": "production_daily", "name": "生产日报模板", "desc": "基地/品类/日期/产量", "fields": ["base", "category", "date", "qty"]},
            {"key": "monthly_plan", "name": "月度计划模板", "desc": "基地/品类/月份/计划产量", "fields": ["base", "category", "month", "plan_qty"]},
            {"key": "yearly_plan", "name": "年度计划模板", "desc": "基地或区域/品类/年份/计划量", "fields": ["entity", "category", "year", "plan_qty"]},
            {"key": "sales_target", "name": "销售目标模板", "desc": "区域/型号/袋散/月份/目标量", "fields": ["region", "spec", "package", "month", "target_qty"]},
            {"key": "cost_data", "name": "成本数据模板", "desc": "基地/品类/月份/单位成本", "fields": ["base", "category", "month", "unit_cost"]},
            {"key": "logistics_cost", "name": "物流成本模板", "desc": "起点基地/终点区域/距离/单位成本", "fields": ["from_base", "to_region", "distance", "unit_cost"]},
            {"key": "inventory_params", "name": "库存参数模板", "desc": "基地/品类/安全库存/仓容上限", "fields": ["base", "category", "safety_qty", "capacity"]},
        ]
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    template_type: str = Form(...),
):
    contents = await file.read()
    file_size = len(contents)

    return {
        "status": "preview",
        "filename": file.filename,
        "template_type": template_type,
        "file_size": file_size,
        "preview": {
            "total": 18,
            "valid": 16,
            "errors": 2,
            "rows": [
                {"base": "龙岩基地", "category": "水泥", "date": "2026-02-01", "value": 8.52, "error": None},
                {"base": "三明基地", "category": "熟料", "date": "2026-02-01", "value": 5.34, "error": None},
                {"base": "南平基地", "category": "水泥", "date": "2026-02-01", "value": 15.20, "error": "产量超出产能上限"},
                {"base": "泉州基地", "category": "水泥", "date": "2026-02-01", "value": 6.78, "error": None},
            ],
        },
    }


@router.get("/upload-records")
def get_upload_records(page: int = 1, page_size: int = 20):
    return {
        "total": 4,
        "items": [
            {"id": 1, "time": "2026-03-01 14:30", "template": "生产日报", "filename": "龙岩基地2月生产日报.xlsx", "rows": 56, "operator": "张三", "status": "已入库"},
            {"id": 2, "time": "2026-03-01 10:15", "template": "月度计划", "filename": "3月月度生产计划.xlsx", "rows": 27, "operator": "李四", "status": "已入库"},
            {"id": 3, "time": "2026-02-28 16:45", "template": "成本数据", "filename": "2月成本数据.xlsx", "rows": 18, "operator": "王五", "status": "待审核"},
            {"id": 4, "time": "2026-02-27 09:20", "template": "物流成本", "filename": "运输成本矩阵更新.xlsx", "rows": 81, "operator": "张三", "status": "已入库"},
        ],
    }
