"""Unit tests for core data models."""

import uuid

import pytest

from src.core.models import (
    AgentType,
    AuditEvent,
    Goal,
    GoalConstraints,
    GoalCreate,
    GoalStatus,
    TaskNode,
    TaskStatus,
)


@pytest.mark.unit
class TestGoalCreate:
    def test_valid_goal_create(self):
        gc = GoalCreate(title="Test", description="Test description")
        assert gc.title == "Test"
        assert gc.description == "Test description"
        assert gc.constraints.budget_usd is None

    def test_goal_create_with_constraints(self):
        gc = GoalCreate(
            title="Campaign",
            description="Details",
            constraints=GoalConstraints(budget_usd=5000, channels=["email"]),
        )
        assert gc.constraints.budget_usd == 5000
        assert gc.constraints.channels == ["email"]

    def test_goal_create_title_required(self):
        with pytest.raises(Exception):
            GoalCreate(title="", description="Test")


@pytest.mark.unit
class TestGoal:
    def test_goal_defaults(self):
        g = Goal(title="Test", description="Desc")
        assert g.status == GoalStatus.PENDING
        assert g.task_count == 0
        assert isinstance(g.id, uuid.UUID)

    def test_goal_status_transitions(self):
        g = Goal(title="Test", description="Desc")
        g.status = GoalStatus.PLANNING
        assert g.status == GoalStatus.PLANNING
        g.status = GoalStatus.EXECUTING
        assert g.status == GoalStatus.EXECUTING


@pytest.mark.unit
class TestTaskNode:
    def test_task_node_defaults(self):
        t = TaskNode(
            goal_id=uuid.uuid4(),
            name="test_task",
            agent_type=AgentType.EXECUTOR,
        )
        assert t.status == TaskStatus.PENDING
        assert t.retries == 0
        assert t.max_retries == 3
        assert t.dependencies == []

    def test_task_node_with_dependencies(self):
        dep_id = uuid.uuid4()
        t = TaskNode(
            goal_id=uuid.uuid4(),
            name="test_task",
            agent_type=AgentType.EXECUTOR,
            dependencies=[dep_id],
        )
        assert dep_id in t.dependencies


@pytest.mark.unit
class TestAuditEvent:
    def test_audit_event_creation(self):
        goal_id = uuid.uuid4()
        e = AuditEvent(goal_id=goal_id, agent="planner", action="dag_created")
        assert e.goal_id == goal_id
        assert e.agent == "planner"
        assert e.task_id is None
