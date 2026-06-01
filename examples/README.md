# Examples

Minimal examples demonstrating key flows of the Agentic Orchestrator.

## Prerequisites

Start the API server:
```bash
docker compose up -d
# or
make dev
```

## Python Client

```bash
pip install httpx
python examples/client_python.py
```

Demonstrates: health check, goal submission, status polling, task graph retrieval, audit trail, and simulation.

## curl Examples

```bash
bash examples/client_curl.sh
```

Same flow using curl for quick testing.

## Expected Output

After submitting a goal, you should see:
1. Goal accepted with status `planning`
2. Status transitions: `planning` → `executing` → `completed`
3. Task graph with 5-10 tasks per channel
4. Audit trail with events from all subagents
5. Simulation results with step-by-step trace

## Reproducing Key Flows

### Flow 1: Simple Email Campaign
```bash
curl -X POST http://localhost:8000/api/v1/goals \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","description":"Email test","constraints":{"channels":["email"]}}'
```

### Flow 2: Multi-Channel with Budget
```bash
curl -X POST http://localhost:8000/api/v1/goals \
  -H "Content-Type: application/json" \
  -d '{"title":"Multi","description":"Multi-channel","constraints":{"channels":["email","in-app"],"budget_usd":5000}}'
```

### Flow 3: Deterministic Simulation
```bash
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"goal":{"title":"Sim","description":"Test"},"seed":42,"failure_rate":0.0}'
```
Running twice with the same seed produces identical results.
