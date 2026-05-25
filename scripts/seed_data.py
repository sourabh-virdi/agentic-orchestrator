"""Seed synthetic data into the system for development and demos."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.executor import ExecutorAgent
from src.agents.planner import PlannerAgent
from src.agents.retriever import RetrieverAgent
from src.agents.verifier import VerifierAgent
from src.audit.logger import AuditLogger
from src.core.models import GoalCreate, GoalConstraints
from src.core.orchestrator import Orchestrator
from src.memory.vector_store import VectorStore

SAMPLE_GOALS = [
    GoalCreate(
        title="Q2 Email Engagement Campaign",
        description="Increase email open rates by 20% for enterprise segment through personalized content and optimal send times.",
        constraints=GoalConstraints(budget_usd=5000, deadline="2026-06-30", channels=["email"], audience="enterprise"),
    ),
    GoalCreate(
        title="Product Launch Multi-Channel Push",
        description="Drive awareness for new product launch across email and in-app channels targeting existing customers.",
        constraints=GoalConstraints(budget_usd=10000, deadline="2026-05-15", channels=["email", "in-app"], audience="existing_customers"),
    ),
    GoalCreate(
        title="Win-Back Campaign for Churned Users",
        description="Re-engage users who have been inactive for 90+ days with targeted offers.",
        constraints=GoalConstraints(budget_usd=3000, deadline="2026-04-30", channels=["email"], audience="churned"),
    ),
]

SAMPLE_MEMORY_DOCS = [
    {
        "id": "mem_001",
        "content": "Previous Q1 email campaign achieved 18% open rate with subject line personalization. Best performing segment was enterprise accounts with 24% open rate.",
        "metadata": {"type": "campaign_result", "channel": "email", "quarter": "Q1-2026"},
    },
    {
        "id": "mem_002",
        "content": "In-app notification campaigns show 3x higher engagement when triggered by user behavior events rather than scheduled sends.",
        "metadata": {"type": "best_practice", "channel": "in-app"},
    },
    {
        "id": "mem_003",
        "content": "Win-back campaigns with 20% discount offers have 12% conversion rate. Personalized product recommendations increase this to 18%.",
        "metadata": {"type": "campaign_result", "channel": "email", "campaign_type": "win-back"},
    },
]


async def seed() -> None:
    print("=== Seeding Agentic Orchestrator ===\n")

    print("1. Seeding vector memory...")
    try:
        store = VectorStore()
        store.connect()
        for doc in SAMPLE_MEMORY_DOCS:
            store.add(ids=[doc["id"]], documents=[doc["content"]], metadatas=[doc["metadata"]])
        print(f"   Added {len(SAMPLE_MEMORY_DOCS)} documents to vector memory")
    except Exception as exc:
        print(f"   Vector memory seeding skipped (ChromaDB not available): {exc}")

    print("\n2. Processing sample goals...")
    audit = AuditLogger()
    planner = PlannerAgent()
    retriever = RetrieverAgent()
    executor = ExecutorAgent(simulate=True)
    verifier = VerifierAgent()
    orchestrator = Orchestrator(planner, retriever, executor, verifier, audit)

    for goal_create in SAMPLE_GOALS:
        goal = await orchestrator.submit_goal(goal_create)
        print(f"   Submitted: {goal.title} (ID: {goal.id})")

        try:
            result = await orchestrator.plan_and_execute(goal.id)
            print(f"   Status: {result.status.value} | Tasks: {result.task_count}")
        except Exception as exc:
            print(f"   Execution error: {exc}")

    print(f"\n3. Audit log: {audit.event_count} events recorded")
    print("\n=== Seeding Complete ===")


if __name__ == "__main__":
    asyncio.run(seed())
