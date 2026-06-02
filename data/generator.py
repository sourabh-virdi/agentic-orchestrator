"""Synthetic data generator with anonymization knobs for campaign goals and outcomes."""

from __future__ import annotations

import csv
import json
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class GeneratorConfig:
    num_goals: int = 100
    num_memory_docs: int = 50
    seed: int = 42
    anonymize_names: bool = True
    anonymize_emails: bool = True
    hash_identifiers: bool = False
    output_dir: str = "data"


CHANNELS = ["email", "in-app", "sms", "push", "social"]
AUDIENCES = ["enterprise", "smb", "consumer", "churned", "new_user", "power_user"]
GOAL_TEMPLATES = [
    "Increase {metric} by {pct}% for {audience} segment",
    "Launch {channel} campaign for {audience} customers",
    "Re-engage {audience} users with targeted {channel} content",
    "Drive {metric} through {channel} optimization",
    "Improve {metric} across {channel} and {channel2} channels",
]
METRICS = ["open_rate", "click_rate", "conversion_rate", "engagement", "retention", "revenue"]
NAMES = [
    "Campaign Alpha", "Project Beta", "Initiative Gamma", "Program Delta",
    "Effort Epsilon", "Sprint Zeta", "Drive Eta", "Push Theta",
]


def _anonymize(value: str, do_anonymize: bool) -> str:
    if not do_anonymize:
        return value
    return f"ANON_{uuid.uuid4().hex[:8]}"


def generate_goals(config: GeneratorConfig) -> list[dict]:
    """Generate synthetic campaign goals."""
    rng = random.Random(config.seed)
    goals = []

    for i in range(config.num_goals):
        channels = rng.sample(CHANNELS, k=rng.randint(1, 3))
        audience = rng.choice(AUDIENCES)
        metric = rng.choice(METRICS)
        pct = rng.randint(5, 50)
        template = rng.choice(GOAL_TEMPLATES)
        description = template.format(
            metric=metric, pct=pct, audience=audience,
            channel=channels[0], channel2=channels[-1],
        )
        budget = round(rng.uniform(500, 50000), 2)
        deadline_days = rng.randint(14, 180)
        deadline = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")

        goal = {
            "id": str(uuid.uuid4()) if not config.hash_identifiers else uuid.uuid4().hex,
            "title": f"{_anonymize(rng.choice(NAMES), config.anonymize_names)} {i + 1}",
            "description": description,
            "constraints": {
                "budget_usd": budget,
                "deadline": deadline,
                "channels": channels,
                "audience": audience,
            },
            "expected_metric": metric,
            "expected_improvement_pct": pct,
        }
        goals.append(goal)

    return goals


def generate_memory_docs(config: GeneratorConfig) -> list[dict]:
    """Generate synthetic vector memory documents."""
    rng = random.Random(config.seed + 1)
    docs = []

    doc_templates = [
        "Previous {channel} campaign achieved {pct}% {metric}. Target audience was {audience}.",
        "Best practice: {channel} campaigns for {audience} should include personalization.",
        "Historical data shows {metric} improves by {pct}% with optimal send timing on {channel}.",
        "A/B testing on {channel} revealed {pct}% lift in {metric} for {audience} segment.",
    ]

    for i in range(config.num_memory_docs):
        channel = rng.choice(CHANNELS)
        audience = rng.choice(AUDIENCES)
        metric = rng.choice(METRICS)
        pct = rng.randint(5, 40)
        template = rng.choice(doc_templates)
        content = template.format(channel=channel, audience=audience, metric=metric, pct=pct)

        doc = {
            "id": f"mem_{i:04d}",
            "content": content,
            "metadata": {
                "type": rng.choice(["campaign_result", "best_practice", "historical_data"]),
                "channel": channel,
                "audience": audience,
            },
        }
        docs.append(doc)

    return docs


def save_data(config: GeneratorConfig) -> dict[str, str]:
    """Generate and save all synthetic data."""
    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    goals = generate_goals(config)
    goals_path = out / "synthetic_goals.json"
    goals_path.write_text(json.dumps(goals, indent=2))

    goals_csv_path = out / "synthetic_goals.csv"
    with open(goals_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "description", "budget_usd", "deadline", "channels", "audience"])
        writer.writeheader()
        for g in goals:
            writer.writerow({
                "id": g["id"],
                "title": g["title"],
                "description": g["description"],
                "budget_usd": g["constraints"]["budget_usd"],
                "deadline": g["constraints"]["deadline"],
                "channels": ",".join(g["constraints"]["channels"]),
                "audience": g["constraints"]["audience"],
            })

    docs = generate_memory_docs(config)
    docs_path = out / "synthetic_memory.json"
    docs_path.write_text(json.dumps(docs, indent=2))

    paths = {
        "goals_json": str(goals_path),
        "goals_csv": str(goals_csv_path),
        "memory_json": str(docs_path),
    }
    print(f"Generated {len(goals)} goals → {goals_path}")
    print(f"Generated {len(goals)} goals → {goals_csv_path}")
    print(f"Generated {len(docs)} memory docs → {docs_path}")
    return paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic data")
    parser.add_argument("--goals", type=int, default=100, help="Number of goals")
    parser.add_argument("--docs", type=int, default=50, help="Number of memory documents")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--no-anonymize", action="store_true", help="Disable anonymization")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    config = GeneratorConfig(
        num_goals=args.goals,
        num_memory_docs=args.docs,
        seed=args.seed,
        anonymize_names=not args.no_anonymize,
        anonymize_emails=not args.no_anonymize,
        output_dir=args.output,
    )
    save_data(config)
