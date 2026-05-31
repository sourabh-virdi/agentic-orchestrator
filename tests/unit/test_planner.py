"""Unit tests for the Planner agent."""

import pytest

from src.agents.planner import PlannerAgent
from src.core.models import Goal, GoalConstraints, GoalStatus


@pytest.mark.unit
class TestPlannerAgent:
    @pytest.mark.asyncio
    async def test_plan_single_channel(self, sample_goal):
        planner = PlannerAgent()
        graph = await planner.plan(sample_goal)
        assert len(graph.tasks) > 0
        for task in graph.tasks.values():
            assert task.goal_id == sample_goal.id

    @pytest.mark.asyncio
    async def test_plan_multi_channel(self):
        goal = Goal(
            title="Multi-channel",
            description="Test",
            constraints=GoalConstraints(channels=["email", "in-app"]),
            status=GoalStatus.PENDING,
        )
        planner = PlannerAgent()
        graph = await planner.plan(goal)
        task_names = [t.name for t in graph.tasks.values()]
        has_email = any("email" in n for n in task_names)
        has_inapp = any("in-app" in n for n in task_names)
        assert has_email
        assert has_inapp

    @pytest.mark.asyncio
    async def test_plan_default_channel(self):
        goal = Goal(
            title="Default",
            description="Test",
            constraints=GoalConstraints(),
            status=GoalStatus.PENDING,
        )
        planner = PlannerAgent()
        graph = await planner.plan(goal)
        assert len(graph.tasks) > 0

    @pytest.mark.asyncio
    async def test_plan_respects_dependencies(self, sample_goal):
        planner = PlannerAgent()
        graph = await planner.plan(sample_goal)
        order = graph.execution_order()
        assert len(order) == len(graph.tasks)

    @pytest.mark.asyncio
    async def test_run_interface(self, sample_goal):
        planner = PlannerAgent()
        result = await planner.run({"goal": sample_goal, "context": []})
        assert "task_graph" in result
        assert "nodes" in result["task_graph"]
