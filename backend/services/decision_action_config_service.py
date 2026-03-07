import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_ASSIGN_ACTIONS = ["常规指派", "加急处理", "跨区协同", "升级处理"]
DEFAULT_PROCESS_ACTIONS = ["进展反馈", "完成处置", "风险复核", "现场核验"]


class DecisionActionConfigService:
    def __init__(self):
        self.config_path = Path(__file__).resolve().parents[1] / "data" / "decision_action_config.json"

    def _default_config(self) -> Dict[str, List[str]]:
        return {
            "assign_actions": list(DEFAULT_ASSIGN_ACTIONS),
            "process_actions": list(DEFAULT_PROCESS_ACTIONS),
        }

    def get_config(self) -> Dict[str, List[str]]:
        config = self._default_config()
        if self.config_path.exists():
            try:
                file_data = json.loads(self.config_path.read_text(encoding="utf-8"))
                if isinstance(file_data.get("assign_actions"), list) and file_data["assign_actions"]:
                    config["assign_actions"] = [str(x) for x in file_data["assign_actions"]]
                if isinstance(file_data.get("process_actions"), list) and file_data["process_actions"]:
                    config["process_actions"] = [str(x) for x in file_data["process_actions"]]
            except Exception:
                pass
        return config

    def update_config(self, payload: Dict[str, Any]) -> Dict[str, List[str]]:
        config = self.get_config()
        if isinstance(payload.get("assign_actions"), list) and payload["assign_actions"]:
            config["assign_actions"] = [str(x) for x in payload["assign_actions"]]
        if isinstance(payload.get("process_actions"), list) and payload["process_actions"]:
            config["process_actions"] = [str(x) for x in payload["process_actions"]]
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return config


decision_action_config_service = DecisionActionConfigService()
