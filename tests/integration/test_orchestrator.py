"""Integration tests for the full orchestration pipeline."""

import pytest

from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.retriever import RetrieverAgent
from src.agents.verifier import VerifierAgent
from src.audit.logger import AuditLogger
from src.core.models import GoalConstraints, GoalCreate
from src.core.orchestrator import Orchestrator


@pytest.mark.integration
class TestOrchestratorIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline_single_channel(self):
        orch = Orchestrator(
            PlannerAgent(), RetrieverAgent(), ExecutorAgent(simulate=True),
            VerifierAgent(), AuditLogger(),
        )
        goal = await orch.submit_goal(GoalCreate(
            title="Pipeline Test",
            description="Full pipeline integration test",
            constraints=GoalConstraints(channels=["email"]),
        ))
        result = await orch.plan_and_execute(goal.id)
        assert result.status.value in ("completed", "failed")
        assert result.task_count > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_multi_channel(self):
        orch = Orchestrator(
            PlannerAgent(), RetrieverAgent(), ExecutorAgent(simulate=True),
            VerifierAgent(), AuditLogger(),
        )
        goal = await orch.submit_goal(GoalCreate(
            title="Multi-channel Test",
            description="Multi-channel pipeline test",
            constraints=GoalConstraints(channels=["email", "in-app"]),
        ))
        result = await orch.plan_and_execute(goal.id)
        assert result.task_count > 5

    @pytest.mark.asyncio
    async def test_cancel_goal(self):
        orch = Orchestrator(
            PlannerAgent(), RetrieverAgent(), ExecutorAgent(simulate=True),
            VerifierAgent(), AuditLogger(),
        )
        goal = await orch.submit_goal(GoalCreate(
            title="Cancel Test", description="To be cancelled",
        ))
        cancelled = await orch.cancel_goal(goal.id)
        assert cancelled.status.value == "cancelled"

    @pytest.mark.asyncio
    async def test_audit_trail_populated(self):
        audit = AuditLogger()
        orch = Orchestrator(
            PlannerAgent(), RetrieverAgent(), ExecutorAgent(simulate=True),
            VerifierAgent(), audit,
        )
        goal = await orch.submit_goal(GoalCreate(
            title="Audit Test", description="Check audit",
            constraints=GoalConstraints(channels=["email"]),
        ))
        await orch.plan_and_execute(goal.id)
        events = await audit.get_events(goal_id=goal.id)
        assert len(events) >= 3
        actions = [e.action for e in events]
        assert "goal_submitted" in actions
        assert "dag_created" in actions
