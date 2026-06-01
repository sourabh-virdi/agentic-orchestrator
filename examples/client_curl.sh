#!/usr/bin/env bash
# Example curl commands for the Agentic Orchestrator API

API_BASE="http://localhost:8000/api/v1"

echo "=== Agentic Orchestrator — curl Examples ==="

# 1. Health check
echo -e "\n--- Health Check ---"
curl -s "$API_BASE/health" | python3 -m json.tool

# 2. Submit a goal
echo -e "\n--- Submit Goal ---"
GOAL_RESPONSE=$(curl -s -X POST "$API_BASE/goals" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q2 Email Engagement Campaign",
    "description": "Increase email open rates by 20% for enterprise segment",
    "constraints": {
      "budget_usd": 5000,
      "deadline": "2026-06-30",
      "channels": ["email", "in-app"],
      "audience": "enterprise"
    }
  }')
echo "$GOAL_RESPONSE" | python3 -m json.tool

GOAL_ID=$(echo "$GOAL_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Goal ID: $GOAL_ID"

# 3. Wait and check status
echo -e "\n--- Check Status ---"
sleep 3
curl -s "$API_BASE/goals/$GOAL_ID" | python3 -m json.tool

# 4. Get tasks
echo -e "\n--- Task Graph ---"
curl -s "$API_BASE/goals/$GOAL_ID/tasks" | python3 -m json.tool

# 5. Get audit trail
echo -e "\n--- Audit Trail ---"
curl -s "$API_BASE/goals/$GOAL_ID/audit" | python3 -m json.tool

# 6. Run simulation
echo -e "\n--- Simulation ---"
curl -s -X POST "$API_BASE/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": {
      "title": "Test Campaign",
      "description": "Simulation test",
      "constraints": {"channels": ["email"]}
    },
    "seed": 42,
    "failure_rate": 0.1
  }' | python3 -m json.tool

# 7. Prometheus metrics
echo -e "\n--- Metrics (first 20 lines) ---"
curl -s "$API_BASE/metrics" | head -20

echo -e "\n=== Done ==="
