"""End-to-end smoke tests — validates the full system works together."""

import time

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.mark.e2e
class TestE2ESmoke:
    @pytest.fixture(autouse=True)
    def client(self):
        self.client = TestClient(app)

    def test_full_goal_lifecycle(self):
        """Smoke test: submit goal → poll status → check tasks → check audit."""
        # Submit
        resp = self.client.post("/api/v1/goals", json={
            "title": "E2E Smoke Test Campaign",
            "description": "Full lifecycle smoke test",
            "constraints": {
                "budget_usd": 5000,
                "channels": ["email", "in-app"],
                "audience": "enterprise",
            },
        })
        assert resp.status_code == 202
        goal_id = resp.json()["id"]

        # Wait for processing
        time.sleep(2)

        # Check status
        resp = self.client.get(f"/api/v1/goals/{goal_id}")
        assert resp.status_code == 200
        goal = resp.json()
        assert goal["status"] in ("planning", "executing", "completed", "failed")

        # Check tasks
        resp = self.client.get(f"/api/v1/goals/{goal_id}/tasks")
        assert resp.status_code == 200

        # Check audit
        resp = self.client.get(f"/api/v1/goals/{goal_id}/audit")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) >= 1

    def test_simulation_determinism(self):
        """Verify simulation produces identical results with same seed."""
        payload = {
            "goal": {
                "title": "Determinism Test",
                "description": "Same seed should give same results",
                "constraints": {"channels": ["email"]},
            },
            "seed": 42,
            "failure_rate": 0.1,
        }

        resp1 = self.client.post("/api/v1/simulate", json=payload)
        resp2 = self.client.post("/api/v1/simulate", json=payload)

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["steps"] == resp2.json()["steps"]
        assert resp1.json()["total_reward"] == resp2.json()["total_reward"]

    def test_health_and_metrics_available(self):
        """Verify observability endpoints respond."""
        health = self.client.get("/api/v1/health")
        assert health.status_code == 200

        metrics = self.client.get("/api/v1/metrics")
        assert metrics.status_code == 200
        assert "http_requests_total" in metrics.text
