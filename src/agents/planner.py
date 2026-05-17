"""Planner agent — decomposes goals into task DAGs using heuristic rules and optional RL policy."""

from __future__ import annotations

import uuid
from typing import Any

import structlog

from src.agents.base import BaseAgent
from src.core.models import AgentType, Goal, TaskNode
from src.core.task_graph import TaskGraph

logger = structlog.get_logger(__name__)

TASK_TEMPLATES = {
    "email": [
        {"name": "segment_audience", "agent_type": AgentType.EXECUTOR},
        {"name": "design_email_template", "agent_type": AgentType.EXECUTOR},
        {"name": "personalize_content", "agent_type": AgentType.EXECUTOR},
        {"name": "schedule_send", "agent_type": AgentType.EXECUTOR},
        {"name": "monitor_delivery", "agent_type": AgentType.VERIFIER},
    ],
    "in-app": [
        {"name": "define_in_app_placement", "agent_type": AgentType.EXECUTOR},
        {"name": "create_in_app_content", "agent_type": AgentType.EXECUTOR},
        {"name": "configure_targeting", "agent_type": AgentType.EXECUTOR},
        {"name": "activate_campaign", "agent_type": AgentType.EXECUTOR},
        {"name": "monitor_engagement", "agent_type": AgentType.VERIFIER},
    ],
    "default": [
        {"name": "analyze_requirements", "agent_type": AgentType.RETRIEVER},
        {"name": "generate_action_plan", "agent_type": AgentType.EXECUTOR},
        {"name": "execute_actions", "agent_type": AgentType.EXECUTOR},
        {"name": "validate_results", "agent_type": AgentType.VERIFIER},
    ],
}


class PlannerAgent(BaseAgent):
    """Decomposes a Goal into a TaskGraph using heuristic templates and context."""

    def __init__(self, policy: Any | None = None) -> None:
        super().__init__("planner")
        self._policy = policy

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        goal = input_data["goal"]
        context = input_data.get("context", [])
        graph = await self.plan(goal, context)
        return {"task_graph": graph.to_dict()}

    async def plan(self, goal: Goal, context: list[dict] | None = None) -> TaskGraph:
        if self._policy is not None:
            return await self._plan_with_policy(goal, context)
        return self._plan_heuristic(goal)

    def _plan_heuristic(self, goal: Goal) -> TaskGraph:
        """Build a task DAG from heuristic template matching."""
        graph = TaskGraph()
        channels = goal.constraints.channels or ["default"]

        for channel in channels:
            templates = TASK_TEMPLATES.get(channel, TASK_TEMPLATES["default"])
            prev_id: uuid.UUID | None = None

            for template in templates:
                task = TaskNode(
                    goal_id=goal.id,
                    name=f"{channel}_{template['name']}",
                    agent_type=template["agent_type"],
                    params={"channel": channel, "goal_title": goal.title},
                    dependencies=[prev_id] if prev_id else [],
                )
                graph.add_task(task)
                prev_id = task.id

        logger.info("heuristic_plan_created", goal_id=str(goal.id), tasks=len(graph.tasks))
        return graph

    async def _plan_with_policy(self, goal: Goal, context: list[dict] | None) -> TaskGraph:
        """Use learned RL policy to select task templates (falls back to heuristic)."""
        try:
            if self._policy and hasattr(self._policy, "select_actions"):
                actions = self._policy.select_actions(goal, context)
                graph = TaskGraph()
                prev_id = None
                for action in actions:
                    task = TaskNode(
                        goal_id=goal.id,
                        name=action["name"],
                        agent_type=AgentType(action.get("agent_type", "executor")),
                        params=action.get("params", {}),
                        dependencies=[prev_id] if prev_id else [],
                    )
                    graph.add_task(task)
                    prev_id = task.id
                return graph
        except Exception:
            logger.warning("policy_planning_failed_falling_back_to_heuristic")
        return self._plan_heuristic(goal)
