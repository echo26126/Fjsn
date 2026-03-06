import json
from pathlib import Path
from typing import Dict, Any


class PermissionService:
    def __init__(self):
        self.path = Path(__file__).resolve().parents[1] / "data" / "user_permissions.json"

    def _default(self) -> Dict[str, Any]:
        return {
            "roles": [
                {"role_id": "admin", "role_name": "管理员", "permissions": ["*"]},
                {"role_id": "analyst", "role_name": "分析员", "permissions": ["agent.config.read", "cockpit.region_config.read"]},
                {"role_id": "viewer", "role_name": "访客", "permissions": ["cockpit.region_config.read"]},
            ],
            "users": [
                {"user_id": "u_admin", "user_name": "系统管理员", "roles": ["admin"], "enabled": True},
                {"user_id": "u_ops", "user_name": "运营人员", "roles": ["analyst"], "enabled": True},
                {"user_id": "u_guest", "user_name": "访客用户", "roles": ["viewer"], "enabled": True},
            ],
        }

    def get_bundle(self) -> Dict[str, Any]:
        data = self._default()
        if self.path.exists():
            try:
                file_data = json.loads(self.path.read_text(encoding="utf-8"))
                data.update(file_data)
            except Exception:
                pass
        data["roles"] = data.get("roles", [])
        data["users"] = data.get("users", [])
        return data

    def _save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def _validate_roles(self, data: Dict[str, Any], roles: list[str]):
        role_ids = {r.get("role_id") for r in data.get("roles", [])}
        for role in roles:
            if role not in role_ids:
                raise ValueError("role_not_found")

    def update_user_roles(self, user_id: str, roles: list[str]) -> Dict[str, Any]:
        data = self.get_bundle()
        self._validate_roles(data, roles)
        users = data.get("users", [])
        for user in users:
            if user.get("user_id") == user_id:
                user["roles"] = roles
                break
        else:
            raise ValueError("user_not_found")
        return self._save(data)

    def add_user(self, user_id: str, user_name: str, roles: list[str], enabled: bool = True) -> Dict[str, Any]:
        data = self.get_bundle()
        self._validate_roles(data, roles)
        users = data.get("users", [])
        if any(u.get("user_id") == user_id for u in users):
            raise ValueError("user_exists")
        users.append({
            "user_id": user_id,
            "user_name": user_name,
            "roles": roles,
            "enabled": enabled,
        })
        return self._save(data)

    def update_user(self, user_id: str, user_name: str | None = None, roles: list[str] | None = None, enabled: bool | None = None) -> Dict[str, Any]:
        data = self.get_bundle()
        users = data.get("users", [])
        if roles is not None:
            self._validate_roles(data, roles)
        for user in users:
            if user.get("user_id") == user_id:
                if user_name is not None and user_name:
                    user["user_name"] = user_name
                if roles is not None:
                    user["roles"] = roles
                if enabled is not None:
                    user["enabled"] = enabled
                return self._save(data)
        raise ValueError("user_not_found")

    def delete_user(self, user_id: str) -> Dict[str, Any]:
        if user_id == "u_admin":
            raise ValueError("cannot_delete_admin")
        data = self.get_bundle()
        users = data.get("users", [])
        original = len(users)
        data["users"] = [u for u in users if u.get("user_id") != user_id]
        if len(data["users"]) == original:
            raise ValueError("user_not_found")
        return self._save(data)


permission_service = PermissionService()
