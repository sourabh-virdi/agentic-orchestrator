"""Locust load testing script for the Agentic Orchestrator API."""

from __future__ import annotations

import random
import uuid

from locust import HttpUser, between, task


class OrchestratorUser(HttpUser):
    """Simulates a user interacting with the orchestrator API."""

    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._goal_ids: list[str] = []

    @task(3)
    def health_check(self):
        self.client.get("/api/v1/health", name="/health")

    @task(5)
    def submit_goal(self):
        channels = random.sample(["email", "in-app", "sms", "push"], k=random.randint(1, 3))
        payload = {
            "title": f"Load Test Campaign {uuid.uuid4().hex[:8]}",
            "description": "Automated load testing goal for benchmark",
            "constraints": {
                "budget_usd": random.uniform(1000, 10000),
                "deadline": "2026-12-31",
                "channels": channels,
                "audience": random.choice(["enterprise", "smb", "consumer"]),
            },
        }
        with self.client.post("/api/v1/goals", json=payload, name="/goals [POST]", catch_response=True) as resp:
            if resp.status_code == 202:
                goal_id = resp.json().get("id")
                if goal_id:
                    self._goal_ids.append(goal_id)
                resp.success()
            else:
                resp.failure(f"Expected 202, got {resp.status_code}")

    @task(10)
    def get_goal_status(self):
        if not self._goal_ids:
            return
        goal_id = random.choice(self._goal_ids)
        self.client.get(f"/api/v1/goals/{goal_id}", name="/goals/{id} [GET]")

    @task(4)
    def get_goal_tasks(self):
        if not self._goal_ids:
            return
        goal_id = random.choice(self._goal_ids)
        self.client.get(f"/api/v1/goals/{goal_id}/tasks", name="/goals/{id}/tasks")

    @task(2)
    def get_goal_audit(self):
        if not self._goal_ids:
            return
        goal_id = random.choice(self._goal_ids)
        self.client.get(f"/api/v1/goals/{goal_id}/audit", name="/goals/{id}/audit")

    @task(3)
    def simulate(self):
        payload = {
            "goal": {
                "title": "Benchmark Simulation",
                "description": "Load test simulation",
                "constraints": {"channels": ["email"]},
            },
            "seed": random.randint(1, 1000),
            "failure_rate": 0.1,
        }
        self.client.post("/api/v1/simulate", json=payload, name="/simulate [POST]")

    @task(1)
    def get_metrics(self):
        self.client.get("/api/v1/metrics", name="/metrics")
