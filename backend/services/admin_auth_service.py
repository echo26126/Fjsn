import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any


class AdminAuthService:
    def __init__(self):
        self.path = Path(__file__).resolve().parents[1] / "data" / "admin_sessions.json"
        self.session_hours = 12

    def _required_secret(self) -> str:
        return os.getenv("ADMIN_TOKEN", "admin-local-token")

    def _load(self) -> Dict[str, Any]:
        data = {"sessions": {}}
        if self.path.exists():
            try:
                file_data = json.loads(self.path.read_text(encoding="utf-8"))
                data.update(file_data)
            except Exception:
                pass
        return data

    def _save(self, data: Dict[str, Any]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def login(self, admin_secret: str, operator: str) -> Dict[str, Any]:
        if not admin_secret or admin_secret.strip() != self._required_secret():
            raise ValueError("invalid_secret")
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.session_hours)
        session_id = secrets.token_urlsafe(32)
        data = self._load()
        sessions = data.get("sessions", {})
        sessions[session_id] = {
            "operator": operator or "admin",
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        data["sessions"] = sessions
        self._save(data)
        return {"session_id": session_id, "expires_at": expires_at.isoformat()}

    def validate(self, session_id: str) -> bool:
        if not session_id:
            return False
        data = self._load()
        sessions = data.get("sessions", {})
        info = sessions.get(session_id)
        if not info:
            return False
        expires_at = info.get("expires_at")
        if not expires_at:
            return False
        if datetime.now(timezone.utc) >= datetime.fromisoformat(expires_at):
            sessions.pop(session_id, None)
            data["sessions"] = sessions
            self._save(data)
            return False
        return True

    def logout(self, session_id: str):
        if not session_id:
            return
        data = self._load()
        sessions = data.get("sessions", {})
        sessions.pop(session_id, None)
        data["sessions"] = sessions
        self._save(data)


admin_auth_service = AdminAuthService()
