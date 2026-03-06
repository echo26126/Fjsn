import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class AuditService:
    def __init__(self):
        self.audit_path = Path(__file__).resolve().parents[1] / "data" / "audit_logs.jsonl"

    def record(self, action: str, operator: str, details: Dict[str, Any]):
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "operator": operator or "unknown",
            "details": details,
        }
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def list_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.audit_path.exists():
            return []
        lines = self.audit_path.read_text(encoding="utf-8").splitlines()
        items: List[Dict[str, Any]] = []
        for line in reversed(lines):
            try:
                items.append(json.loads(line))
            except Exception:
                continue
            if len(items) >= limit:
                break
        return items


audit_service = AuditService()
