"""Toy REINFORCE training loop for the planner policy."""

from __future__ import annotations

import json
from pathlib import Path

import structlog
import torch

from src.agents.planner import PlannerAgent
from src.core.models import Goal, GoalConstraints, GoalStatus
from src.core.task_graph import TaskGraph
from src.policy.network import PlannerPolicy, create_goal_state_vector
from src.simulator.engine import Simulator, SimulatorConfig

logger = structlog.get_logger(__name__)

ACTION_NAMES = [
    "segment_audience",
    "design_content",
    "personalize",
    "schedule",
    "monitor",
    "analyze",
    "optimize",
    "report",
]


def compute_discounted_returns(rewards: list[float], gamma: float = 0.99) -> list[float]:
    """Compute discounted cumulative returns from a list of step rewards."""
    returns = []
    g = 0.0
    for r in reversed(rewards):
        g = r + gamma * g
        returns.insert(0, g)
    # normalize
    mean = sum(returns) / len(returns) if returns else 0
    std = (sum((r - mean) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 1
    if std < 1e-8:
        std = 1.0
    return [(r - mean) / std for r in returns]


def train_policy(
    num_episodes: int = 1000,
    gamma: float = 0.99,
    lr: float = 0.001,
    state_dim: int = 32,
    action_dim: int = 8,
    save_path: str = "models/policy_best.pt",
    seed: int = 42,
) -> dict:
    """Train the planner policy using REINFORCE on simulated episodes."""
    policy = PlannerPolicy(state_dim=state_dim, action_dim=action_dim)
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)
    sim_config = SimulatorConfig(seed=seed, failure_rate=0.1)

    best_reward = float("-inf")
    episode_rewards = []
    losses = []

    for episode in range(num_episodes):
        goal = Goal(
            title=f"Training Goal {episode}",
            description=f"Synthetic campaign goal for training episode {episode}",
            constraints=GoalConstraints(
                budget_usd=1000 + (episode % 10) * 500,
                channels=["email", "in-app"][:1 + episode % 2],
                audience="enterprise",
            ),
            status=GoalStatus.PENDING,
        )

        planner = PlannerAgent()
        import asyncio
        task_graph = asyncio.get_event_loop().run_until_complete(
            planner.plan(goal, [])
        ) if False else planner._plan_heuristic(goal)

        simulator = Simulator(sim_config)
        state = simulator.reset(goal, task_graph)

        log_probs: list[torch.Tensor] = []
        rewards: list[float] = []

        while not state.done:
            state_vec = create_goal_state_vector(
                num_channels=len(goal.constraints.channels),
                budget_normalized=min(goal.constraints.budget_usd or 0, 10000) / 10000,
                progress=state.step / max(sim_config.max_steps, 1),
                state_dim=state_dim,
            )

            action_probs = policy(state_vec.unsqueeze(0)).squeeze()
            dist = torch.distributions.Categorical(action_probs)
            action = dist.sample()
            log_probs.append(dist.log_prob(action))

            state, reward = simulator.step()
            rewards.append(reward)

        total_reward = sum(rewards)
        episode_rewards.append(total_reward)

        if log_probs and rewards:
            returns = compute_discounted_returns(rewards, gamma)
            loss = torch.tensor(0.0, requires_grad=True)
            policy_loss = sum(-lp * torch.tensor(r) for lp, r in zip(log_probs, returns))
            if isinstance(policy_loss, torch.Tensor):
                loss = policy_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        if total_reward > best_reward:
            best_reward = total_reward
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            torch.save(policy.state_dict(), save_path)

        if (episode + 1) % 100 == 0:
            avg = sum(episode_rewards[-100:]) / min(100, len(episode_rewards))
            logger.info(
                "training_progress",
                episode=episode + 1,
                avg_reward_100=f"{avg:.2f}",
                best_reward=f"{best_reward:.2f}",
            )

    metrics = {
        "total_episodes": num_episodes,
        "best_reward": best_reward,
        "final_avg_reward_100": sum(episode_rewards[-100:]) / min(100, len(episode_rewards)),
        "model_path": save_path,
    }

    metrics_path = Path(save_path).parent / "training_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    logger.info("training_complete", **metrics)
    return metrics


if __name__ == "__main__":
    train_policy()
