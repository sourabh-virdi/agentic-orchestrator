"""CLI demo — run the full orchestration pipeline locally without Docker."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.retriever import RetrieverAgent
from src.agents.verifier import VerifierAgent
from src.audit.logger import AuditLogger
from src.core.models import GoalConstraints, GoalCreate
from src.core.orchestrator import Orchestrator
from src.simulator.engine import Simulator, SimulatorConfig


async def demo_orchestration():
    print("=" * 60)
    print("  Agentic Orchestrator — CLI Demo")
    print("=" * 60)

    # Set up components
    audit = AuditLogger()
    planner = PlannerAgent()
    retriever = RetrieverAgent()
    executor = ExecutorAgent(simulate=True)
    verifier = VerifierAgent()
    orch = Orchestrator(planner, retriever, executor, verifier, audit)

    # Submit a goal
    goal_create = GoalCreate(
        title="Q2 Email Engagement Campaign",
        description="Increase email open rates by 20% for enterprise segment through personalized content",
        constraints=GoalConstraints(
            budget_usd=5000,
            deadline="2026-06-30",
            channels=["email", "in-app"],
            audience="enterprise",
        ),
    )

    print(f"\n[1] Submitting goal: {goal_create.title}")
    goal = await orch.submit_goal(goal_create)
    print(f"    Goal ID: {goal.id}")
    print(f"    Status:  {goal.status.value}")

    # Execute
    print(f"\n[2] Planning and executing...")
    result = await orch.plan_and_execute(goal.id)
    print(f"    Status:     {result.status.value}")
    print(f"    Task count: {result.task_count}")

    # Show task graph
    graph = orch.get_graph(goal.id)
    if graph:
        print(f"\n[3] Task Graph:")
        for task in graph.tasks.values():
            status_icon = {"completed": "✓", "failed": "✗", "skipped": "⏭"}.get(task.status.value, "○")
            print(f"    {status_icon} {task.name} [{task.agent_type.value}] → {task.status.value}")

    # Show audit
    events = await audit.get_events(goal_id=goal.id)
    print(f"\n[4] Audit Trail ({len(events)} events):")
    for e in sorted(events, key=lambda x: x.timestamp)[:10]:
        print(f"    {e.timestamp.strftime('%H:%M:%S')} | {e.agent:>12} | {e.action}")

    # Run simulation
    print(f"\n[5] Running deterministic simulation...")
    p = PlannerAgent()
    from src.core.models import Goal, GoalStatus
    sim_goal = Goal(
        title="Simulation Test", description="Testing simulation",
        constraints=GoalConstraints(channels=["email"]), status=GoalStatus.PENDING,
    )
    sim_graph = p._plan_heuristic(sim_goal)
    sim = Simulator(SimulatorConfig(seed=42, failure_rate=0.1))
    sim.reset(sim_goal, sim_graph)
    state = sim.run_to_completion()
    print(f"    Steps:        {state.step}")
    print(f"    Total Reward: {state.total_reward:.2f}")
    print(f"    Trace entries: {len(state.trace)}")

    print(f"\n{'=' * 60}")
    print("  Demo complete!")
    print(f"{'=' * 60}")


EXPECTED_OUTPUT = """
Expected output (approximate):
─────────────────────────────
[1] Submitting goal: Q2 Email Engagement Campaign
    Goal ID: <uuid>
    Status:  pending

[2] Planning and executing...
    Status:     completed
    Task count: 10

[3] Task Graph:
    ✓ email_segment_audience [executor] → completed
    ✓ email_design_email_template [executor] → completed
    ✓ email_personalize_content [executor] → completed
    ✓ email_schedule_send [executor] → completed
    ✓ email_monitor_delivery [verifier] → completed
    ✓ in-app_define_in_app_placement [executor] → completed
    ✓ in-app_create_in_app_content [executor] → completed
    ✓ in-app_configure_targeting [executor] → completed
    ✓ in-app_activate_campaign [executor] → completed
    ✓ in-app_monitor_engagement [verifier] → completed

[4] Audit Trail (5+ events):
    HH:MM:SS |  orchestrator | goal_submitted
    HH:MM:SS |  orchestrator | planning_started
    HH:MM:SS |       planner | dag_created
    HH:MM:SS |  orchestrator | execution_started
    HH:MM:SS |      verifier | verification_passed

[5] Running deterministic simulation...
    Steps:        5
    Total Reward: ~4.0-5.0
"""


if __name__ == "__main__":
    asyncio.run(demo_orchestration())
