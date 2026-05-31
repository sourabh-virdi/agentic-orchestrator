"""Unit tests for the Executor agent."""

import uuid

import pytest

from src.agents.executor import ExecutorAgent
from src.core.models import AgentType, TaskNode


@pytest.mark.unit
class TestExecutorAgent:
    def test_default_execute(self):
        executor = ExecutorAgent(simulate=True)
        task = TaskNode(
            goal_id=uuid.uuid4(),
            name="test_task",
            agent_type=AgentType.EXECUTOR,
            params={"channel": "email"},
        )
        result = executor.execute_sync(task)
        assert result["status"] == "success"
        assert "elapsed_seconds" in result
        assert result["task_name"] == "test_task"

    def test_custom_handler(self):
        executor = ExecutorAgent()

        def custom_handler(task):
            return {"status": "custom_success", "data": 42}

        executor.register_handler("custom_", custom_handler)
        task = TaskNode(
            goal_id=uuid.uuid4(),
            name="custom_task",
            agent_type=AgentType.EXECUTOR,
        )
        result = executor.execute_sync(task)
        assert result["status"] == "custom_success"
        assert result["data"] == 42

    @pytest.mark.asyncio
    async def test_run_interface(self):
        executor = ExecutorAgent(simulate=True)
        task = TaskNode(
            goal_id=uuid.uuid4(),
            name="test_task",
            agent_type=AgentType.EXECUTOR,
        )
        result = await executor.run({"task": task})
        assert result["status"] == "success"

    def test_handler_exception_propagates(self):
        executor = ExecutorAgent()

        def failing_handler(task):
            raise RuntimeError("Task exploded")

        executor.register_handler("fail_", failing_handler)
        task = TaskNode(
            goal_id=uuid.uuid4(),
            name="fail_task",
            agent_type=AgentType.EXECUTOR,
        )
        with pytest.raises(RuntimeError, match="Task exploded"):
            executor.execute_sync(task)
