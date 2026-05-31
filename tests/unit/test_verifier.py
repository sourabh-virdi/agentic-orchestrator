"""Unit tests for the Verifier agent."""

import uuid

import pytest

from src.agents.verifier import VerifierAgent
from src.core.models import AgentType, Goal, GoalConstraints, GoalStatus, TaskNode, TaskStatus
from src.core.task_graph import TaskGraph


@pytest.mark.unit
class TestVerifierAgent:
    def _make_graph(self, goal, statuses):
        graph = TaskGraph()
        prev_id = None
        for i, status in enumerate(statuses):
            t = TaskNode(
                goal_id=goal.id,
                name=f"task_{i}",
                agent_type=AgentType.EXECUTOR,
                params={"channel": "email"},
                dependencies=[prev_id] if prev_id else [],
            )
            graph.add_task(t)
            graph.update_task_status(t.id, status, {"ok": True} if status == TaskStatus.COMPLETED else None)
            prev_id = t.id
        return graph

    @pytest.mark.asyncio
    async def test_all_completed_passes(self, sample_goal):
        verifier = VerifierAgent()
        graph = self._make_graph(sample_goal, [TaskStatus.COMPLETED] * 4)
        result = await verifier.verify(sample_goal, graph)
        assert result["passed"]
        assert result["confidence"] >= 0.7
        assert result["completion_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_all_failed_fails(self, sample_goal):
        verifier = VerifierAgent()
        graph = self._make_graph(sample_goal, [TaskStatus.FAILED] * 4)
        result = await verifier.verify(sample_goal, graph)
        assert not result["passed"]
        assert result["completion_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_budget_compliance(self):
        goal = Goal(
            title="Test",
            description="Test",
            constraints=GoalConstraints(budget_usd=100, channels=["email"]),
            status=GoalStatus.PENDING,
        )
        verifier = VerifierAgent()
        graph = TaskGraph()
        t = TaskNode(
            goal_id=goal.id, name="task_0", agent_type=AgentType.EXECUTOR,
            params={"channel": "email"},
        )
        graph.add_task(t)
        graph.update_task_status(t.id, TaskStatus.COMPLETED, {"cost_usd": 50})
        result = await verifier.verify(goal, graph)
        budget_check = next(c for c in result["checks"] if c["name"] == "budget_compliance")
        assert budget_check["passed"]

    @pytest.mark.asyncio
    async def test_channel_coverage(self):
        goal = Goal(
            title="Test",
            description="Test",
            constraints=GoalConstraints(channels=["email", "in-app"]),
            status=GoalStatus.PENDING,
        )
        verifier = VerifierAgent()
        graph = TaskGraph()
        t = TaskNode(
            goal_id=goal.id, name="task_0", agent_type=AgentType.EXECUTOR,
            params={"channel": "email"},
        )
        graph.add_task(t)
        graph.update_task_status(t.id, TaskStatus.COMPLETED)
        result = await verifier.verify(goal, graph)
        channel_check = next(c for c in result["checks"] if c["name"] == "channel_coverage")
        assert not channel_check["passed"]
        assert "in-app" in channel_check["missing"]
