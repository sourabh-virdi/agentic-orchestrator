"""Executor agent — runs individual tasks with retry logic."""

from __future__ import annotations

import time
from typing import Any

import structlog

from src.agents.base import BaseAgent
from src.core.models import TaskNode

logger = structlog.get_logger(__name__)


class ExecutorAgent(BaseAgent):
    """Executes task nodes against real or simulated backends."""

    def __init__(self, simulate: bool = False) -> None:
        super().__init__("executor")
        self._simulate = simulate
        self._handlers: dict[str, Any] = {}

    def register_handler(self, task_name_prefix: str, handler: Any) -> None:
        """Register a handler function for tasks matching a name prefix."""
        self._handlers[task_name_prefix] = handler

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task = input_data["task"]
        result = self.execute_sync(task)
        return result

    def execute_sync(self, task: TaskNode) -> dict:
        """Execute a single task synchronously (called from asyncio.to_thread)."""
        start = time.monotonic()
        logger.info("task_executing", task_id=str(task.id), task_name=task.name)

        try:
            for prefix, handler in self._handlers.items():
                if task.name.startswith(prefix):
                    result = handler(task)
                    elapsed = time.monotonic() - start
                    logger.info("task_completed", task_id=str(task.id), elapsed=f"{elapsed:.3f}s")
                    return {**result, "elapsed_seconds": elapsed}

            result = self._default_execute(task)
            elapsed = time.monotonic() - start
            logger.info("task_completed", task_id=str(task.id), elapsed=f"{elapsed:.3f}s")
            return {**result, "elapsed_seconds": elapsed}

        except Exception as exc:
            elapsed = time.monotonic() - start
            logger.error("task_execution_failed", task_id=str(task.id), error=str(exc))
            raise

    def _default_execute(self, task: TaskNode) -> dict:
        """Default execution: simulate or return a mock success."""
        if self._simulate:
            time.sleep(0.01)
        return {
            "status": "success",
            "task_name": task.name,
            "message": f"Executed {task.name} for goal {task.goal_id}",
            "output": task.params,
        }
