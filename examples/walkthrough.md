# Reviewer Walkthrough

A step-by-step guide to reproduce the key flows of the Agentic Orchestrator.

## Prerequisites

- Docker and Docker Compose v2+ installed
- Python 3.11+ (for non-Docker demos)
- ~4 GB free RAM

## Walkthrough Steps

### Step 1: Clone and Configure (30 seconds)

```bash
git clone https://github.com/sourabh-virdi/agentic-orchestrator.git
cd agentic-orchestrator
cp .env.example .env
```

### Step 2: Start All Services (2 minutes)

```bash
docker compose up -d
```

Wait for health check:
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy","version":"1.0.0","services":{"api":"up","audit":"up"}}
```

### Step 3: Submit a Campaign Goal (10 seconds)

```bash
curl -X POST http://localhost:8000/api/v1/goals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q2 Email Engagement Campaign",
    "description": "Increase email open rates by 20% for enterprise segment",
    "constraints": {
      "budget_usd": 5000,
      "channels": ["email", "in-app"],
      "audience": "enterprise"
    }
  }'
```

**Expected output:**
```json
{
  "id": "<uuid>",
  "status": "planning",
  "task_count": 0,
  "created_at": "2026-03-14T..."
}
```

Save the `id` value as `$GOAL_ID`.

### Step 4: Check Goal Status (wait 3 seconds, then run)

```bash
curl http://localhost:8000/api/v1/goals/$GOAL_ID
```

**Expected:** Status transitions from `planning` → `executing` → `completed`.

### Step 5: View Task Graph

```bash
curl http://localhost:8000/api/v1/goals/$GOAL_ID/tasks
```

**Expected:** 10 tasks (5 per channel: email + in-app), all with `"status": "completed"`.

### Step 6: View Audit Trail

```bash
curl http://localhost:8000/api/v1/goals/$GOAL_ID/audit
```

**Expected:** 5+ audit events including `goal_submitted`, `planning_started`, `dag_created`, `execution_started`, `verification_passed`.

### Step 7: Run Deterministic Simulation

```bash
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "goal": {"title": "Sim Test", "description": "Test", "constraints": {"channels": ["email"]}},
    "seed": 42,
    "failure_rate": 0.0
  }'
```

**Expected:** All steps complete with `total_reward > 0`. Running the same request again produces identical results (deterministic).

### Step 8: Open Replay UI

Navigate to http://localhost:8501 in your browser.

1. Enter the Goal ID from Step 3
2. Click "Load Replay"
3. Observe the DAG visualization and timeline

### Step 9: Run CLI Demo (no Docker needed)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python demo/demo_cli.py
```

**Expected:** Full pipeline output showing goal submission, task execution, audit trail, and simulation.

### Step 10: Run Tests

```bash
make test
```

**Expected:** All tests pass with 80%+ coverage.

### Step 11: View Grafana Dashboard

Navigate to http://localhost:3000 (admin/admin).

1. Go to Dashboards → Agentic Orchestrator
2. See request rates, latencies, and goal metrics

### Step 12: Cleanup

```bash
docker compose down -v
```

## Time Estimate

| Step | Time |
|------|------|
| Setup | 3 min |
| Goal lifecycle | 1 min |
| Simulation | 30 sec |
| Replay UI | 2 min |
| Tests | 2 min |
| **Total** | **~10 min** |
