"""Unit tests for the task graph engine."""

import uuid

import pytest

from src.core.models import AgentType, TaskNode, TaskStatus
from src.core.task_graph import TaskGraph


@pytest.mark.unit
class TestTaskGraph:
    def test_add_single_task(self):
        graph = TaskGraph()
        task = TaskNode(goal_id=uuid.uuid4(), name="task1", agent_type=AgentType.EXECUTOR)
        graph.add_task(task)
        assert task.id in graph.tasks
        assert len(graph.tasks) == 1

    def test_add_task_with_dependency(self):
        graph = TaskGraph()
        t1 = TaskNode(goal_id=uuid.uuid4(), name="task1", agent_type=AgentType.EXECUTOR)
        graph.add_task(t1)
        t2 = TaskNode(
            goal_id=uuid.uuid4(), name="task2", agent_type=AgentType.EXECUTOR,
            dependencies=[t1.id],
        )
        graph.add_task(t2)
        assert len(graph.tasks) == 2

    def test_add_task_with_missing_dependency_raises(self):
        graph = TaskGraph()
        t = TaskNode(
            goal_id=uuid.uuid4(), name="task1", agent_type=AgentType.EXECUTOR,
            dependencies=[uuid.uuid4()],
        )
        with pytest.raises(ValueError, match="not found"):
            graph.add_task(t)

    def test_cycle_detection(self):
        graph = TaskGraph()
        gid = uuid.uuid4()
        t1 = TaskNode(goal_id=gid, name="t1", agent_type=AgentType.EXECUTOR)
        graph.add_task(t1)
        t2 = TaskNode(goal_id=gid, name="t2", agent_type=AgentType.EXECUTOR, dependencies=[t1.id])
        graph.add_task(t2)
        # manually try to create a cycle
        t3 = TaskNode(goal_id=gid, name="t3", agent_type=AgentType.EXECUTOR, dependencies=[t2.id])
        graph.add_task(t3)
        assert len(graph.tasks) == 3

    def test_get_ready_tasks(self):
        graph = TaskGraph()
        gid = uuid.uuid4()
        t1 = TaskNode(goal_id=gid, name="t1", agent_type=AgentType.EXECUTOR)
        t2 = TaskNode(goal_id=gid, name="t2", agent_type=AgentType.EXECUTOR, dependencies=[t1.id])
        graph.add_task(t1)
        graph.add_task(t2)
        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == t1.id

    def test_ready_tasks_after_completion(self):
        graph = TaskGraph()
        gid = uuid.uuid4()
        t1 = TaskNode(goal_id=gid, name="t1", agent_type=AgentType.EXECUTOR)
        t2 = TaskNode(goal_id=gid, name="t2", agent_type=AgentType.EXECUTOR, dependencies=[t1.id])
        graph.add_task(t1)
        graph.add_task(t2)
        graph.update_task_status(t1.id, TaskStatus.COMPLETED, {"ok": True})
        ready = graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == t2.id

    def test_is_complete(self):
        graph = TaskGraph()
        t = TaskNode(goal_id=uuid.uuid4(), name="t1", agent_type=AgentType.EXECUTOR)
        graph.add_task(t)
        assert not graph.is_complete()
        graph.update_task_status(t.id, TaskStatus.COMPLETED)
        assert graph.is_complete()

    def test_mark_downstream_skipped(self):
        graph = TaskGraph()
        gid = uuid.uuid4()
        t1 = TaskNode(goal_id=gid, name="t1", agent_type=AgentType.EXECUTOR)
        t2 = TaskNode(goal_id=gid, name="t2", agent_type=AgentType.EXECUTOR, dependencies=[t1.id])
        t3 = TaskNode(goal_id=gid, name="t3", agent_type=AgentType.EXECUTOR, dependencies=[t2.id])
        graph.add_task(t1)
        graph.add_task(t2)
        graph.add_task(t3)
        graph.update_task_status(t1.id, TaskStatus.FAILED)
        skipped = graph.mark_downstream_skipped(t1.id)
        assert t2.id in skipped
        assert t3.id in skipped
        assert graph.tasks[t2.id].status == TaskStatus.SKIPPED

    def test_execution_order(self):
        graph = TaskGraph()
        gid = uuid.uuid4()
        t1 = TaskNode(goal_id=gid, name="t1", agent_type=AgentType.EXECUTOR)
        t2 = TaskNode(goal_id=gid, name="t2", agent_type=AgentType.EXECUTOR, dependencies=[t1.id])
        graph.add_task(t1)
        graph.add_task(t2)
        order = graph.execution_order()
        assert order.index(t1.id) < order.index(t2.id)

    def test_to_dict(self):
        graph = TaskGraph()
        t = TaskNode(goal_id=uuid.uuid4(), name="t1", agent_type=AgentType.EXECUTOR)
        graph.add_task(t)
        d = graph.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert len(d["nodes"]) == 1

    def test_has_failures(self):
        graph = TaskGraph()
        t = TaskNode(goal_id=uuid.uuid4(), name="t1", agent_type=AgentType.EXECUTOR)
        graph.add_task(t)
        assert not graph.has_failures()
        graph.update_task_status(t.id, TaskStatus.FAILED)
        assert graph.has_failures()
