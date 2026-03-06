
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to sys.path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_health_check():
    """Verify the health check endpoint returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

def test_dashboard_kpi():
    """Verify the dashboard KPI endpoint returns 200 OK and expected structure."""
    response = client.get("/api/cockpit/kpi")
    assert response.status_code == 200
    data = response.json()
    assert "production" in data
    assert "sales" in data
    assert "inventory" in data
    assert "balance_index" in data

def test_dashboard_production():
    """Verify the dashboard production endpoint returns 200 OK and expected structure."""
    response = client.get("/api/cockpit/production")
    assert response.status_code == 200
    data = response.json()
    assert "bases" in data
    assert isinstance(data["bases"], list)
    assert "trend" in data

def test_dashboard_sales():
    """Verify the dashboard sales endpoint returns 200 OK and expected structure."""
    response = client.get("/api/cockpit/sales")
    assert response.status_code == 200
    data = response.json()
    assert "regions" in data
    assert isinstance(data["regions"], list)
    assert "category_split" in data
