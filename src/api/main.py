"""FastAPI application — REST API for the Agentic Orchestrator."""

from __future__ import annotations

import asyncio
import uuid

import structlog
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.retriever import RetrieverAgent
from src.agents.verifier import VerifierAgent
from src.audit.logger import AuditLogger
from src.core.config import settings
from src.core.models import (
    GoalCreate,
    GoalResponse,
    GoalStatus,
    HealthResponse,
    SimulateRequest,
    TaskResponse,
)
from src.core.orchestrator import Orchestrator
from src.simulator.engine import Simulator, SimulatorConfig

logger = structlog.get_logger(__name__)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])
GOALS_SUBMITTED = Counter("goals_submitted_total", "Total goals submitted")
GOALS_COMPLETED = Counter("goals_completed_total", "Total goals completed")

app = FastAPI(
    title="Agentic Orchestrator API",
    description="Turn strategic goals into sequenced, monitored actions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audit = AuditLogger()
planner = PlannerAgent()
retriever = RetrieverAgent()
executor = ExecutorAgent(simulate=True)
verifier = VerifierAgent()
orchestrator = Orchestrator(planner, retriever, executor, verifier, audit)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    import time
    start = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(elapsed)
    return response


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={"api": "up", "audit": "up"},
    )


@app.post("/api/v1/goals", response_model=GoalResponse, status_code=202)
async def submit_goal(goal_create: GoalCreate, background_tasks: BackgroundTasks):
    goal = await orchestrator.submit_goal(goal_create)
    GOALS_SUBMITTED.inc()
    background_tasks.add_task(_execute_goal, goal.id)
    return GoalResponse(
        id=goal.id,
        status=goal.status,
        task_count=goal.task_count,
        created_at=goal.created_at,
    )


async def _execute_goal(goal_id: uuid.UUID) -> None:
    try:
        goal = await orchestrator.plan_and_execute(goal_id)
        if goal.status == GoalStatus.COMPLETED:
            GOALS_COMPLETED.inc()
    except Exception as exc:
        logger.error("goal_execution_failed", goal_id=str(goal_id), error=str(exc))


@app.get("/api/v1/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: uuid.UUID):
    goal = orchestrator.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalResponse(
        id=goal.id,
        status=goal.status,
        task_count=goal.task_count,
        created_at=goal.created_at,
    )


@app.get("/api/v1/goals/{goal_id}/tasks", response_model=list[TaskResponse])
async def get_goal_tasks(goal_id: uuid.UUID):
    graph = orchestrator.get_graph(goal_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Goal not found")
    return [
        TaskResponse(
            id=t.id,
            name=t.name,
            agent_type=t.agent_type,
            status=t.status,
            dependencies=t.dependencies,
            result=t.result,
            retries=t.retries,
            created_at=t.created_at,
            completed_at=t.completed_at,
        )
        for t in graph.tasks.values()
    ]


@app.get("/api/v1/goals/{goal_id}/audit")
async def get_goal_audit(goal_id: uuid.UUID):
    events = await audit.get_events(goal_id=goal_id)
    return [
        {
            "id": str(e.id),
            "agent": e.agent,
            "action": e.action,
            "payload": e.payload,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]


@app.post("/api/v1/goals/{goal_id}/cancel")
async def cancel_goal(goal_id: uuid.UUID):
    try:
        goal = await orchestrator.cancel_goal(goal_id)
        return {"id": str(goal.id), "status": goal.status.value}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/v1/simulate")
async def simulate_goal(request: SimulateRequest):
    from src.agents.planner import PlannerAgent as P
    from src.core.models import Goal

    goal = Goal(
        title=request.goal.title,
        description=request.goal.description,
        constraints=request.goal.constraints,
    )
    p = P()
    task_graph = p._plan_heuristic(goal)
    sim = Simulator(SimulatorConfig(seed=request.seed, failure_rate=request.failure_rate))
    sim.reset(goal, task_graph)
    state = sim.run_to_completion()
    return {
        "goal_id": str(goal.id),
        "steps": state.step,
        "total_reward": state.total_reward,
        "trace": state.trace,
        "dag": task_graph.to_dict(),
    }


@app.get("/api/v1/replay/{goal_id}")
async def get_replay_data(goal_id: uuid.UUID):
    graph = orchestrator.get_graph(goal_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Goal not found")
    timeline = await audit.get_timeline(goal_id)
    return {
        "goal_id": str(goal_id),
        "dag": graph.to_dict(),
        "timeline": timeline,
    }


@app.get("/api/v1/metrics")
async def prometheus_metrics():
    return Response(content=generate_latest(), media_type="text/plain")


def run() -> None:
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=settings.app_port, reload=settings.app_debug)


if __name__ == "__main__":
    run()
