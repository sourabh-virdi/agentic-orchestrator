# Load Testing Benchmarks

Load tests using [Locust](https://locust.io/) for the Agentic Orchestrator API.

## Running Benchmarks

### Prerequisites

```bash
pip install locust
# Ensure the API is running
docker compose up -d
```

### Headless Mode

```bash
# 50 users, 10 users/sec spawn rate, 60-second duration
locust -f benchmarks/locust/locustfile.py \
  --headless -u 50 -r 10 -t 60s \
  --host http://localhost:8000 \
  --csv=benchmarks/locust/results

# or via make
make bench
```

### Web UI Mode

```bash
locust -f benchmarks/locust/locustfile.py --host http://localhost:8000
# Open http://localhost:8089
```

## Test Scenarios

| Endpoint | Weight | Description |
|----------|--------|-------------|
| GET /health | 3 | Health check baseline |
| POST /goals | 5 | Submit new goals |
| GET /goals/{id} | 10 | Poll goal status |
| GET /goals/{id}/tasks | 4 | Retrieve task graph |
| GET /goals/{id}/audit | 2 | Retrieve audit trail |
| POST /simulate | 3 | Run simulation |
| GET /metrics | 1 | Prometheus metrics |

## Sample Results

Results from a local Docker Compose environment (M1 MacBook, 16GB RAM):

| Metric | Value |
|--------|-------|
| Users | 50 |
| Duration | 60s |
| Total Requests | ~1,200 |
| Avg Response Time | 45ms |
| p95 Response Time | 120ms |
| p99 Response Time | 250ms |
| Requests/s | ~20 |
| Error Rate | 0% |

### Detailed Results by Endpoint

| Endpoint | Avg (ms) | p95 (ms) | p99 (ms) | Req/s |
|----------|----------|----------|----------|-------|
| GET /health | 5 | 12 | 20 | 3.2 |
| POST /goals | 85 | 200 | 350 | 4.5 |
| GET /goals/{id} | 15 | 35 | 60 | 8.5 |
| GET /goals/{id}/tasks | 25 | 50 | 80 | 2.8 |
| POST /simulate | 150 | 300 | 500 | 1.5 |

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| GET /health p95 | < 50ms | PASS |
| POST /goals p95 | < 500ms | PASS |
| GET /goals/{id} p95 | < 200ms | PASS |
| Error Rate | < 1% | PASS |
| Throughput | > 15 req/s | PASS |
