# Demo

Quick demonstrations of the Agentic Orchestrator.

## CLI Demo (No Docker Required)

```bash
# From project root
python demo/demo_cli.py
```

This runs the full orchestration pipeline in-memory:
1. Submits a campaign goal
2. Plans a task DAG
3. Executes tasks via simulated executor
4. Verifies results
5. Shows audit trail
6. Runs a deterministic simulation

## API Demo (Docker Required)

```bash
# Start services
docker compose up -d

# Wait for services, then run
python examples/client_python.py
# or
bash examples/client_curl.sh
```

## Notebook Demo

See `notebooks/demo_walkthrough.ipynb` for an interactive walkthrough.

## Expected Outputs

The CLI demo should produce output similar to:
- 10 tasks created (5 per channel for email + in-app)
- All tasks completed successfully
- 5+ audit events recorded
- Simulation completes in ~5 steps with positive reward
