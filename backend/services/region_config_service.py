import json
from pathlib import Path
from typing import Dict, Any


DEFAULT_REGION_CITY_MAP = {
    "安砂销售部": "三明市（永安市）",
    "福州北销售区域": "福州市（北部片区）",
    "福州南销售区域": "福州市（南部片区）",
    "南平销售区域": "南平市",
    "宁德销售区域": "宁德市",
    "莆田销售区域": "莆田市",
    "泉州销售区域": "泉州市",
    "三明销售区域": "三明市",
    "厦漳销售区域": "厦门市、漳州市",
}

DEFAULT_METRIC_UNITS = {
    "production": "万吨",
    "sales": "万吨",
    "inventory": "万吨",
    "avg_price": "元/吨",
    "amount": "万元",
}

DEFAULT_REGION_COORDS = {
    "安砂销售部": [117.37, 25.98],
    "福州北销售区域": [119.30, 26.12],
    "福州南销售区域": [119.30, 25.98],
    "南平销售区域": [118.18, 26.64],
    "宁德销售区域": [119.53, 26.66],
    "莆田销售区域": [119.01, 25.43],
    "泉州销售区域": [118.58, 24.93],
    "三明销售区域": [117.63, 26.26],
    "厦漳销售区域": [117.95, 24.55],
}

DEFAULT_REGION_COLORS = {
    "安砂销售部": "#2F54EB",
    "福州北销售区域": "#08979C",
    "福州南销售区域": "#13C2C2",
    "南平销售区域": "#597EF7",
    "宁德销售区域": "#85A5FF",
    "莆田销售区域": "#006D75",
    "泉州销售区域": "#1890FF",
    "三明销售区域": "#2F54EB",
    "厦漳销售区域": "#0050B3",
}


class RegionConfigService:
    def __init__(self):
        self.config_path = Path(__file__).resolve().parents[1] / "data" / "region_config.json"

    def _default_config(self) -> Dict[str, Any]:
        return {
            "region_city_map": DEFAULT_REGION_CITY_MAP,
            "metric_units": DEFAULT_METRIC_UNITS,
            "region_coords": DEFAULT_REGION_COORDS,
            "region_colors": DEFAULT_REGION_COLORS,
        }

    def get_config(self) -> Dict[str, Any]:
        config = self._default_config()
        if self.config_path.exists():
            try:
                file_data = json.loads(self.config_path.read_text(encoding="utf-8"))
                for key in ["region_city_map", "metric_units", "region_coords", "region_colors"]:
                    if isinstance(file_data.get(key), dict):
                        config[key] = {**config[key], **file_data[key]}
            except Exception:
                pass
        city_map = config.get("region_city_map") or {}
        if "福州区域" in city_map or "厦门区域" in city_map:
            config["region_city_map"] = DEFAULT_REGION_CITY_MAP
            config["region_coords"] = DEFAULT_REGION_COORDS
            config["region_colors"] = DEFAULT_REGION_COLORS
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return config

    def update_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        config = self.get_config()
        for key in ["region_city_map", "metric_units", "region_coords", "region_colors"]:
            if key in payload and isinstance(payload[key], dict):
                config[key] = payload[key]
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return config


region_config_service = RegionConfigService()
