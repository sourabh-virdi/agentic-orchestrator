"""Shared test fixtures for the Agentic Orchestrator test suite."""

from __future__ import annotations

import uuid

import pytest

from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.retriever import RetrieverAgent
from src.agents.verifier import VerifierAgent
from src.audit.logger import AuditLogger
from src.core.models import (
    AgentType,
    Goal,
    GoalConstraints,
    GoalCreate,
    GoalStatus,
    TaskNode,
)
from src.core.orchestrator import Orchestrator
from src.core.task_graph import TaskGraph
from src.simulator.engine import Simulator, SimulatorConfig


@pytest.fixture
def sample_goal_create() -> GoalCreate:
    return GoalCreate(
        title="Test Email Campaign",
        description="Increase email engagement by 15%",
        constraints=GoalConstraints(
            budget_usd=2000,
            deadline="2026-06-30",
            channels=["email"],
            audience="enterprise",
        ),
    )


@pytest.fixture
def sample_goal() -> Goal:
    return Goal(
        title="Test Email Campaign",
        description="Increase email engagement by 15%",
        constraints=GoalConstraints(
            budget_usd=2000,
            deadline="2026-06-30",
            channels=["email"],
            audience="enterprise",
        ),
        status=GoalStatus.PENDING,
    )


@pytest.fixture
def sample_task_graph(sample_goal: Goal) -> TaskGraph:
    graph = TaskGraph()
    t1 = TaskNode(
        goal_id=sample_goal.id,
        name="email_segment_audience",
        agent_type=AgentType.EXECUTOR,
    )
    t2 = TaskNode(
        goal_id=sample_goal.id,
        name="email_design_template",
        agent_type=AgentType.EXECUTOR,
        dependencies=[t1.id],
    )
    t3 = TaskNode(
        goal_id=sample_goal.id,
        name="email_monitor_delivery",
        agent_type=AgentType.VERIFIER,
        dependencies=[t2.id],
    )
    graph.add_task(t1)
    graph.add_task(t2)
    graph.add_task(t3)
    return graph


@pytest.fixture
def audit_logger() -> AuditLogger:
    return AuditLogger()


@pytest.fixture
def planner() -> PlannerAgent:
    return PlannerAgent()


@pytest.fixture
def retriever() -> RetrieverAgent:
    return RetrieverAgent()


@pytest.fixture
def executor() -> ExecutorAgent:
    return ExecutorAgent(simulate=True)


@pytest.fixture
def verifier() -> VerifierAgent:
    return VerifierAgent()


@pytest.fixture
def orchestrator(planner, retriever, executor, verifier, audit_logger) -> Orchestrator:
    return Orchestrator(planner, retriever, executor, verifier, audit_logger)


@pytest.fixture
def simulator() -> Simulator:
    return Simulator(SimulatorConfig(seed=42, failure_rate=0.0))
