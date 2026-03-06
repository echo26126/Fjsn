import os
import sys
import time
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


client = TestClient(app)


def test_agent_config_requires_admin_for_update():
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    payload = {
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "api_key": "",
        "temperature": 0.3,
        "sql_prompt": "sql prompt",
        "analysis_prompt": "analysis prompt",
    }
    forbidden = client.put("/api/agent/config", json=payload)
    assert forbidden.status_code == 403
    ok = client.put(
        "/api/agent/config",
        json=payload,
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert ok.status_code == 200
    assert ok.json()["model"] == "deepseek-chat"


def test_agent_config_read_masks_key_for_non_admin():
    masked = client.get("/api/agent/config")
    assert masked.status_code == 200
    assert "api_key" in masked.json()


def test_region_config_update_requires_admin():
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    current = client.get("/api/cockpit/region-config")
    assert current.status_code == 200
    data = current.json()
    data["metric_units"]["sales"] = "万吨"
    forbidden = client.put("/api/cockpit/region-config", json=data)
    assert forbidden.status_code == 403
    ok = client.put(
        "/api/cockpit/region-config",
        json=data,
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert ok.status_code == 200
    assert "region_city_map" in ok.json()
    assert "安砂销售部" in ok.json()["region_city_map"]


def test_permission_endpoints_require_admin_on_update():
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    read_res = client.get("/api/agent/permissions")
    assert read_res.status_code == 200
    assert "users" in read_res.json()
    deny = client.put("/api/agent/permissions/users/u_guest", json={"roles": ["viewer"]})
    assert deny.status_code == 403
    ok = client.put(
        "/api/agent/permissions/users/u_guest",
        json={"roles": ["analyst"]},
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert ok.status_code == 200
    user_id = f"u_new_{int(time.time() * 1000)}"
    add_user = client.post(
        "/api/agent/permissions/users",
        json={"user_id": user_id, "user_name": "新用户", "roles": ["viewer"], "enabled": True},
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert add_user.status_code == 200
    duplicated = client.post(
        "/api/agent/permissions/users",
        json={"user_id": user_id, "user_name": "重复用户", "roles": ["viewer"], "enabled": True},
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert duplicated.status_code == 409
    patch_user = client.patch(
        f"/api/agent/permissions/users/{user_id}",
        json={"enabled": False},
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert patch_user.status_code == 200
    delete_user = client.delete(
        f"/api/agent/permissions/users/{user_id}",
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert delete_user.status_code == 200


def test_agent_config_model_normalization():
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    updated = client.put(
        "/api/agent/config",
        json={
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
            "model": "gpt-4.1",
            "api_key": "",
            "temperature": 0.4,
            "sql_prompt": "sql prompt",
            "analysis_prompt": "analysis prompt",
        },
        headers={"x-admin-token": "test-admin-token", "x-operator": "qa-user"},
    )
    assert updated.status_code == 200
    assert updated.json()["model"] == "deepseek-chat"


def test_admin_session_login_and_access():
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    login = client.post("/api/agent/admin/login", json={"admin_secret": "test-admin-token", "operator": "qa-user"})
    assert login.status_code == 200
    session_id = login.json()["session_id"]
    check = client.get("/api/agent/admin/session", headers={"x-admin-session": session_id})
    assert check.status_code == 200
    assert check.json()["valid"] is True
    config = client.get("/api/agent/config", headers={"x-admin-session": session_id})
    assert config.status_code == 200
    logout = client.post("/api/agent/admin/logout", headers={"x-admin-session": session_id})
    assert logout.status_code == 200
