"""Small learned policy network for planner improvement via REINFORCE."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class PlannerPolicy(nn.Module):
    """2-layer MLP policy that selects task templates given a goal state vector."""

    def __init__(self, state_dim: int = 32, hidden_dim: int = 64, action_dim: int = 8) -> None:
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, action_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return F.softmax(self.fc3(x), dim=-1)


def create_goal_state_vector(
    goal_embedding: list[float] | None = None,
    num_channels: int = 1,
    budget_normalized: float = 0.5,
    progress: float = 0.0,
    state_dim: int = 32,
) -> torch.Tensor:
    """Encode goal features into a fixed-size state vector for the policy."""
    state = torch.zeros(state_dim)
    if goal_embedding:
        embed_len = min(len(goal_embedding), state_dim - 4)
        state[:embed_len] = torch.tensor(goal_embedding[:embed_len])
    state[-4] = float(num_channels) / 10.0
    state[-3] = budget_normalized
    state[-2] = progress
    state[-1] = 1.0  # bias
    return state
