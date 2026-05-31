"""Integration tests for the FastAPI REST API."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.mark.integration
class TestAPIIntegration:
    @pytest.fixture(autouse=True)
    def client(self):
        self.client = TestClient(app)

    def test_health_check(self):
        resp = self.client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_submit_goal(self):
        resp = self.client.post("/api/v1/goals", json={
            "title": "Integration Test Campaign",
            "description": "Test goal for integration testing",
            "constraints": {"channels": ["email"], "budget_usd": 1000},
        })
        assert resp.status_code == 202
        data = resp.json()
        assert "id" in data
        assert data["status"] in ("pending", "planning")

    def test_get_nonexistent_goal(self):
        resp = self.client.get("/api/v1/goals/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_submit_and_retrieve_goal(self):
        resp = self.client.post("/api/v1/goals", json={
            "title": "Retrieve Test",
            "description": "Test retrieval",
        })
        goal_id = resp.json()["id"]

        import time
        time.sleep(1)

        resp = self.client.get(f"/api/v1/goals/{goal_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == goal_id

    def test_simulate_endpoint(self):
        resp = self.client.post("/api/v1/simulate", json={
            "goal": {
                "title": "Simulation Test",
                "description": "Test simulation endpoint",
                "constraints": {"channels": ["email"]},
            },
            "seed": 42,
            "failure_rate": 0.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "steps" in data
        assert "total_reward" in data
        assert "trace" in data

    def test_metrics_endpoint(self):
        resp = self.client.get("/api/v1/metrics")
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text

    def test_invalid_goal_validation(self):
        resp = self.client.post("/api/v1/goals", json={"title": "", "description": ""})
        assert resp.status_code == 422

    def test_cancel_nonexistent_goal(self):
        resp = self.client.post("/api/v1/goals/00000000-0000-0000-0000-000000000000/cancel")
        assert resp.status_code == 404
