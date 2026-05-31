"""Unit tests for the deterministic simulator."""

import pytest

from src.agents.planner import PlannerAgent
from src.core.models import Goal, GoalConstraints, GoalStatus
from src.simulator.engine import Simulator, SimulatorConfig


@pytest.mark.unit
class TestSimulator:
    def _create_goal_and_graph(self):
        goal = Goal(
            title="Sim Test",
            description="Test simulation",
            constraints=GoalConstraints(channels=["email"]),
            status=GoalStatus.PENDING,
        )
        planner = PlannerAgent()
        graph = planner._plan_heuristic(goal)
        return goal, graph

    def test_reset(self):
        sim = Simulator(SimulatorConfig(seed=42))
        goal, graph = self._create_goal_and_graph()
        state = sim.reset(goal, graph)
        assert state.step == 0
        assert not state.done
        assert state.total_reward == 0.0

    def test_single_step(self):
        sim = Simulator(SimulatorConfig(seed=42, failure_rate=0.0))
        goal, graph = self._create_goal_and_graph()
        sim.reset(goal, graph)
        state, reward = sim.step()
        assert state.step == 1
        assert reward == 1.0

    def test_run_to_completion(self):
        sim = Simulator(SimulatorConfig(seed=42, failure_rate=0.0))
        goal, graph = self._create_goal_and_graph()
        sim.reset(goal, graph)
        state = sim.run_to_completion()
        assert state.done
        assert state.step > 0
        assert state.total_reward > 0

    def test_deterministic_replay(self):
        """Same seed + same goal should produce identical traces."""
        goal, graph1 = self._create_goal_and_graph()
        _, graph2 = self._create_goal_and_graph()

        sim1 = Simulator(SimulatorConfig(seed=123, failure_rate=0.1))
        sim1.reset(goal, graph1)
        state1 = sim1.run_to_completion()

        sim2 = Simulator(SimulatorConfig(seed=123, failure_rate=0.1))
        sim2.reset(goal, graph2)
        state2 = sim2.run_to_completion()

        assert state1.step == state2.step
        assert state1.total_reward == state2.total_reward
        assert len(state1.trace) == len(state2.trace)

    def test_failure_injection(self):
        sim = Simulator(SimulatorConfig(seed=42, failure_rate=1.0))
        goal, graph = self._create_goal_and_graph()
        sim.reset(goal, graph)
        state = sim.run_to_completion()
        assert state.done
        has_failure = any(t["status"] in ("failed", "retrying") for t in state.trace)
        assert has_failure

    def test_get_trace(self):
        sim = Simulator(SimulatorConfig(seed=42, failure_rate=0.0))
        goal, graph = self._create_goal_and_graph()
        sim.reset(goal, graph)
        sim.run_to_completion()
        trace = sim.get_trace()
        assert len(trace) > 0
        assert "step" in trace[0]
        assert "task_name" in trace[0]

    def test_not_initialized_raises(self):
        sim = Simulator()
        with pytest.raises(RuntimeError, match="not initialized"):
            sim.step()
