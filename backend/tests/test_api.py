import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_dashboard_stats():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "total_predictions" in data

def test_coa_endpoint():
    response = client.get("/api/transactions/coa")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
