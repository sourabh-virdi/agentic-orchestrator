"""Deterministic simulator for testing orchestration without side effects."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from src.core.models import AgentType, Goal, GoalCreate, GoalConstraints, TaskNode, TaskStatus
from src.core.task_graph import TaskGraph

logger = structlog.get_logger(__name__)


@dataclass
class SimulatorConfig:
    seed: int = 42
    failure_rate: float = 0.1
    latency_mean: float = 0.05
    latency_std: float = 0.02
    max_steps: int = 100


@dataclass
class SimulatorState:
    goal: Goal
    task_graph: TaskGraph
    step: int = 0
    done: bool = False
    total_reward: float = 0.0
    trace: list[dict] = field(default_factory=list)


class Simulator:
    """Deterministic environment for running goal execution without real side effects."""

    def __init__(self, config: SimulatorConfig | None = None) -> None:
        self._config = config or SimulatorConfig()
        self._rng = random.Random(self._config.seed)
        self._state: SimulatorState | None = None

    @property
    def state(self) -> SimulatorState | None:
        return self._state

    def reset(self, goal: Goal, task_graph: TaskGraph) -> SimulatorState:
        """Reset the simulator with a new goal and task graph."""
        self._rng = random.Random(self._config.seed)
        self._state = SimulatorState(goal=goal, task_graph=task_graph)
        logger.info("simulator_reset", goal_id=str(goal.id), seed=self._config.seed)
        return self._state

    def step(self) -> tuple[SimulatorState, float]:
        """Execute one step: pick a ready task and simulate its execution."""
        if self._state is None:
            raise RuntimeError("Simulator not initialized — call reset() first")
        if self._state.done:
            return self._state, 0.0

        ready = self._state.task_graph.get_ready_tasks()
        if not ready:
            self._state.done = True
            return self._state, 0.0

        task = ready[0]
        self._state.step += 1

        latency = max(0, self._rng.gauss(self._config.latency_mean, self._config.latency_std))
        failed = self._rng.random() < self._config.failure_rate

        if failed and task.retries < task.max_retries:
            task.retries += 1
            reward = -0.1
            trace_status = "retrying"
        elif failed:
            self._state.task_graph.update_task_status(task.id, TaskStatus.FAILED, {"error": "simulated_failure"})
            self._state.task_graph.mark_downstream_skipped(task.id)
            reward = -1.0
            trace_status = "failed"
        else:
            result = {
                "status": "success",
                "simulated": True,
                "latency": latency,
                "task_name": task.name,
            }
            self._state.task_graph.update_task_status(task.id, TaskStatus.COMPLETED, result)
            reward = 1.0
            trace_status = "completed"

        self._state.total_reward += reward
        self._state.trace.append({
            "step": self._state.step,
            "task_id": str(task.id),
            "task_name": task.name,
            "status": trace_status,
            "latency": latency,
            "reward": reward,
        })

        if self._state.task_graph.is_complete():
            self._state.done = True

        if self._state.step >= self._config.max_steps:
            self._state.done = True

        return self._state, reward

    def run_to_completion(self) -> SimulatorState:
        """Run the simulator until the task graph is complete or max steps reached."""
        if self._state is None:
            raise RuntimeError("Simulator not initialized — call reset() first")
        while not self._state.done:
            self.step()
        logger.info(
            "simulation_complete",
            steps=self._state.step,
            reward=f"{self._state.total_reward:.2f}",
        )
        return self._state

    def get_trace(self) -> list[dict]:
        if self._state is None:
            return []
        return list(self._state.trace)
