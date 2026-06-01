"""Example Python client for the Agentic Orchestrator API."""

import httpx
import time
import json

API_BASE = "http://localhost:8000/api/v1"


def main():
    print("=== Agentic Orchestrator — Python Client Example ===\n")

    # 1. Health check
    print("1. Checking API health...")
    resp = httpx.get(f"{API_BASE}/health")
    print(f"   Status: {resp.json()['status']}\n")

    # 2. Submit a goal
    print("2. Submitting a campaign goal...")
    goal_payload = {
        "title": "Q2 Email Engagement Campaign",
        "description": "Increase email open rates by 20% for enterprise segment",
        "constraints": {
            "budget_usd": 5000,
            "deadline": "2026-06-30",
            "channels": ["email", "in-app"],
            "audience": "enterprise",
        },
    }
    resp = httpx.post(f"{API_BASE}/goals", json=goal_payload)
    goal = resp.json()
    goal_id = goal["id"]
    print(f"   Goal ID: {goal_id}")
    print(f"   Status: {goal['status']}\n")

    # 3. Poll for completion
    print("3. Waiting for goal execution...")
    for _ in range(30):
        time.sleep(1)
        resp = httpx.get(f"{API_BASE}/goals/{goal_id}")
        status = resp.json()["status"]
        print(f"   Status: {status}")
        if status in ("completed", "failed", "cancelled"):
            break
    print()

    # 4. Get tasks
    print("4. Fetching task graph...")
    resp = httpx.get(f"{API_BASE}/goals/{goal_id}/tasks")
    tasks = resp.json()
    for task in tasks:
        print(f"   [{task['status']:>9}] {task['name']} ({task['agent_type']})")
    print()

    # 5. Get audit trail
    print("5. Fetching audit trail...")
    resp = httpx.get(f"{API_BASE}/goals/{goal_id}/audit")
    events = resp.json()
    for event in events[:5]:
        print(f"   {event['timestamp']} | {event['agent']:>12} | {event['action']}")
    print(f"   ... ({len(events)} total events)\n")

    # 6. Run simulation
    print("6. Running simulation...")
    sim_resp = httpx.post(
        f"{API_BASE}/simulate",
        json={"goal": goal_payload, "seed": 42, "failure_rate": 0.1},
        timeout=30,
    )
    sim = sim_resp.json()
    print(f"   Steps: {sim['steps']}")
    print(f"   Total Reward: {sim['total_reward']:.2f}")
    print(f"   Trace entries: {len(sim.get('trace', []))}\n")

    print("=== Done ===")


if __name__ == "__main__":
    main()
