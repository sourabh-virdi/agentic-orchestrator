"""DAG-based task graph engine for managing task execution order and state."""

from __future__ import annotations

import asyncio
import uuid
from typing import Callable

import networkx as nx
import structlog

from src.core.models import TaskNode, TaskStatus

logger = structlog.get_logger(__name__)


class TaskGraph:
    """Manages a directed acyclic graph of tasks with dependency-aware execution."""

    def __init__(self) -> None:
        self._graph = nx.DiGraph()
        self._tasks: dict[uuid.UUID, TaskNode] = {}

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    @property
    def tasks(self) -> dict[uuid.UUID, TaskNode]:
        return dict(self._tasks)

    def add_task(self, task: TaskNode) -> None:
        self._tasks[task.id] = task
        self._graph.add_node(task.id, task=task)
        for dep_id in task.dependencies:
            if dep_id not in self._graph:
                raise ValueError(f"Dependency {dep_id} not found in graph")
            self._graph.add_edge(dep_id, task.id)
        if not nx.is_directed_acyclic_graph(self._graph):
            self._graph.remove_node(task.id)
            del self._tasks[task.id]
            raise ValueError("Adding this task would create a cycle")

    def get_ready_tasks(self) -> list[TaskNode]:
        """Return tasks whose dependencies are all completed."""
        ready = []
        for task_id, task in self._tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
            predecessors = list(self._graph.predecessors(task_id))
            if all(
                self._tasks[p].status == TaskStatus.COMPLETED for p in predecessors
            ):
                ready.append(task)
        return ready

    def update_task_status(self, task_id: uuid.UUID, status: TaskStatus, result: dict | None = None) -> None:
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        task = self._tasks[task_id]
        task.status = status
        if result is not None:
            task.result = result
        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            from datetime import datetime
            task.completed_at = datetime.utcnow()

    def mark_downstream_skipped(self, failed_task_id: uuid.UUID) -> list[uuid.UUID]:
        """Mark all tasks downstream of a failed task as skipped."""
        skipped = []
        for descendant in nx.descendants(self._graph, failed_task_id):
            self._tasks[descendant].status = TaskStatus.SKIPPED
            skipped.append(descendant)
        return skipped

    def is_complete(self) -> bool:
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.FAILED)
            for t in self._tasks.values()
        )

    def has_failures(self) -> bool:
        return any(t.status == TaskStatus.FAILED for t in self._tasks.values())

    def execution_order(self) -> list[uuid.UUID]:
        return list(nx.topological_sort(self._graph))

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "agent_type": t.agent_type.value,
                    "status": t.status.value,
                    "dependencies": [str(d) for d in t.dependencies],
                    "result": t.result,
                }
                for t in self._tasks.values()
            ],
            "edges": [
                {"from": str(u), "to": str(v)} for u, v in self._graph.edges()
            ],
        }

    async def execute(
        self,
        run_task: Callable[[TaskNode], dict],
        on_status_change: Callable[[uuid.UUID, TaskStatus, dict | None], None] | None = None,
    ) -> None:
        """Execute the graph respecting dependencies, running independent tasks concurrently."""
        while not self.is_complete():
            ready = self.get_ready_tasks()
            if not ready:
                if not self.is_complete():
                    logger.warning("No ready tasks but graph not complete — possible deadlock")
                break

            async def _run_single(task: TaskNode) -> None:
                self.update_task_status(task.id, TaskStatus.RUNNING)
                if on_status_change:
                    on_status_change(task.id, TaskStatus.RUNNING, None)
                try:
                    result = await asyncio.to_thread(run_task, task)
                    self.update_task_status(task.id, TaskStatus.COMPLETED, result)
                    if on_status_change:
                        on_status_change(task.id, TaskStatus.COMPLETED, result)
                except Exception as exc:
                    logger.error("task_failed", task_id=str(task.id), error=str(exc))
                    task.retries += 1
                    if task.retries < task.max_retries:
                        task.status = TaskStatus.PENDING
                    else:
                        self.update_task_status(task.id, TaskStatus.FAILED, {"error": str(exc)})
                        self.mark_downstream_skipped(task.id)
                        if on_status_change:
                            on_status_change(task.id, TaskStatus.FAILED, {"error": str(exc)})

            await asyncio.gather(*[_run_single(t) for t in ready])
