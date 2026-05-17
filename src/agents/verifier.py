"""Verifier agent — validates execution results against goal constraints."""

from __future__ import annotations

from typing import Any

import structlog

from src.agents.base import BaseAgent
from src.core.models import Goal, TaskStatus
from src.core.task_graph import TaskGraph

logger = structlog.get_logger(__name__)


class VerifierAgent(BaseAgent):
    """Validates that task execution results satisfy the original goal constraints."""

    def __init__(self, confidence_threshold: float = 0.7) -> None:
        super().__init__("verifier")
        self._confidence_threshold = confidence_threshold

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        goal = input_data["goal"]
        task_graph = input_data["task_graph"]
        return await self.verify(goal, task_graph)

    async def verify(self, goal: Goal, task_graph: TaskGraph) -> dict:
        """Run verification checks on completed task graph."""
        tasks = task_graph.tasks
        total = len(tasks)
        completed = sum(1 for t in tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks.values() if t.status == TaskStatus.FAILED)
        skipped = sum(1 for t in tasks.values() if t.status == TaskStatus.SKIPPED)

        completion_rate = completed / total if total > 0 else 0

        checks = []
        checks.append(self._check_completion_rate(completion_rate))
        checks.append(self._check_no_critical_failures(tasks))
        checks.append(self._check_budget_compliance(goal, tasks))
        checks.append(self._check_channel_coverage(goal, tasks))

        passed_checks = sum(1 for c in checks if c["passed"])
        confidence = passed_checks / len(checks) if checks else 0

        passed = confidence >= self._confidence_threshold

        result = {
            "passed": passed,
            "confidence": confidence,
            "completion_rate": completion_rate,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "checks": checks,
        }

        logger.info(
            "verification_complete",
            goal_id=str(goal.id),
            passed=passed,
            confidence=f"{confidence:.2f}",
        )
        return result

    def _check_completion_rate(self, rate: float) -> dict:
        return {
            "name": "completion_rate",
            "passed": rate >= 0.8,
            "value": rate,
            "threshold": 0.8,
            "message": f"Completion rate: {rate:.0%}",
        }

    def _check_no_critical_failures(self, tasks: dict) -> dict:
        critical_failures = [
            t for t in tasks.values()
            if t.status == TaskStatus.FAILED and "monitor" in t.name
        ]
        return {
            "name": "no_critical_failures",
            "passed": len(critical_failures) == 0,
            "value": len(critical_failures),
            "message": f"Critical failures: {len(critical_failures)}",
        }

    def _check_budget_compliance(self, goal: Goal, tasks: dict) -> dict:
        budget = goal.constraints.budget_usd
        if budget is None:
            return {"name": "budget_compliance", "passed": True, "message": "No budget constraint"}
        total_cost = sum(
            t.result.get("cost_usd", 0) for t in tasks.values()
            if t.result and isinstance(t.result.get("cost_usd"), (int, float))
        )
        return {
            "name": "budget_compliance",
            "passed": total_cost <= budget,
            "value": total_cost,
            "threshold": budget,
            "message": f"Spent ${total_cost:.2f} of ${budget:.2f} budget",
        }

    def _check_channel_coverage(self, goal: Goal, tasks: dict) -> dict:
        required_channels = set(goal.constraints.channels)
        if not required_channels:
            return {"name": "channel_coverage", "passed": True, "message": "No channel constraint"}
        covered = set()
        for t in tasks.values():
            if t.status == TaskStatus.COMPLETED and t.params.get("channel"):
                covered.add(t.params["channel"])
        missing = required_channels - covered
        return {
            "name": "channel_coverage",
            "passed": len(missing) == 0,
            "value": list(covered),
            "missing": list(missing),
            "message": f"Covered {len(covered)}/{len(required_channels)} channels",
        }
