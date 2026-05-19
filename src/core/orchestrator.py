"""Main orchestrator engine — coordinates subagents to execute goal-derived task graphs."""

from __future__ import annotations

import uuid

import structlog

from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.retriever import RetrieverAgent
from src.agents.verifier import VerifierAgent
from src.audit.logger import AuditLogger
from src.core.models import (
    AgentType,
    AuditEvent,
    Goal,
    GoalCreate,
    GoalStatus,
    TaskNode,
    TaskStatus,
)
from src.core.task_graph import TaskGraph

logger = structlog.get_logger(__name__)


class Orchestrator:
    """Accepts goals, plans task DAGs, and coordinates execution through subagents."""

    def __init__(
        self,
        planner: PlannerAgent,
        retriever: RetrieverAgent,
        executor: ExecutorAgent,
        verifier: VerifierAgent,
        audit: AuditLogger,
    ) -> None:
        self._planner = planner
        self._retriever = retriever
        self._executor = executor
        self._verifier = verifier
        self._audit = audit
        self._goals: dict[uuid.UUID, Goal] = {}
        self._graphs: dict[uuid.UUID, TaskGraph] = {}

    @property
    def goals(self) -> dict[uuid.UUID, Goal]:
        return dict(self._goals)

    @property
    def graphs(self) -> dict[uuid.UUID, TaskGraph]:
        return dict(self._graphs)

    async def submit_goal(self, goal_create: GoalCreate) -> Goal:
        goal = Goal(
            title=goal_create.title,
            description=goal_create.description,
            constraints=goal_create.constraints,
            status=GoalStatus.PENDING,
        )
        self._goals[goal.id] = goal
        await self._audit.log(AuditEvent(
            goal_id=goal.id, agent="orchestrator", action="goal_submitted",
            payload={"title": goal.title},
        ))
        logger.info("goal_submitted", goal_id=str(goal.id), title=goal.title)
        return goal

    async def plan_and_execute(self, goal_id: uuid.UUID) -> Goal:
        goal = self._goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")

        goal.status = GoalStatus.PLANNING
        await self._audit.log(AuditEvent(
            goal_id=goal.id, agent="orchestrator", action="planning_started",
        ))

        context = await self._retriever.retrieve(goal.description)
        task_graph = await self._planner.plan(goal, context)
        self._graphs[goal.id] = task_graph
        goal.task_count = len(task_graph.tasks)

        await self._audit.log(AuditEvent(
            goal_id=goal.id, agent="planner", action="dag_created",
            payload={"task_count": goal.task_count},
        ))

        goal.status = GoalStatus.EXECUTING
        await self._audit.log(AuditEvent(
            goal_id=goal.id, agent="orchestrator", action="execution_started",
        ))

        def run_task(task: TaskNode) -> dict:
            return self._executor.execute_sync(task)

        def on_status_change(task_id: uuid.UUID, status: TaskStatus, result: dict | None) -> None:
            logger.info("task_status_changed", task_id=str(task_id), status=status.value)

        await task_graph.execute(run_task, on_status_change)

        verification = await self._verifier.verify(goal, task_graph)

        if verification.get("passed", False):
            goal.status = GoalStatus.COMPLETED
            await self._audit.log(AuditEvent(
                goal_id=goal.id, agent="verifier", action="verification_passed",
                payload=verification,
            ))
        else:
            if verification.get("confidence", 0) < 0.7:
                goal.status = GoalStatus.FAILED
                await self._audit.log(AuditEvent(
                    goal_id=goal.id, agent="verifier", action="verification_failed",
                    payload=verification,
                ))
            else:
                goal.status = GoalStatus.COMPLETED

        logger.info("goal_finished", goal_id=str(goal.id), status=goal.status.value)
        return goal

    async def cancel_goal(self, goal_id: uuid.UUID) -> Goal:
        goal = self._goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        goal.status = GoalStatus.CANCELLED
        await self._audit.log(AuditEvent(
            goal_id=goal.id, agent="orchestrator", action="goal_cancelled",
        ))
        return goal

    def get_goal(self, goal_id: uuid.UUID) -> Goal | None:
        return self._goals.get(goal_id)

    def get_graph(self, goal_id: uuid.UUID) -> TaskGraph | None:
        return self._graphs.get(goal_id)
