"""Unit tests for the learned policy network."""

import pytest
import torch

from src.policy.network import PlannerPolicy, create_goal_state_vector
from src.policy.trainer import compute_discounted_returns


@pytest.mark.unit
class TestPlannerPolicy:
    def test_forward_shape(self):
        policy = PlannerPolicy(state_dim=32, hidden_dim=64, action_dim=8)
        x = torch.randn(1, 32)
        out = policy(x)
        assert out.shape == (1, 8)
        assert torch.allclose(out.sum(), torch.tensor(1.0), atol=1e-5)

    def test_forward_batch(self):
        policy = PlannerPolicy(state_dim=32, hidden_dim=64, action_dim=8)
        x = torch.randn(16, 32)
        out = policy(x)
        assert out.shape == (16, 8)

    def test_gradients_flow(self):
        policy = PlannerPolicy(state_dim=32, hidden_dim=64, action_dim=8)
        x = torch.randn(1, 32)
        out = policy(x)
        loss = -torch.log(out[0, 0])
        loss.backward()
        assert policy.fc1.weight.grad is not None


@pytest.mark.unit
class TestCreateGoalStateVector:
    def test_default_state(self):
        state = create_goal_state_vector()
        assert state.shape == (32,)
        assert state[-1] == 1.0  # bias

    def test_with_embedding(self):
        embedding = [0.1] * 20
        state = create_goal_state_vector(goal_embedding=embedding, state_dim=32)
        assert state[0] == pytest.approx(0.1)

    def test_normalized_features(self):
        state = create_goal_state_vector(num_channels=5, budget_normalized=0.8, progress=0.5)
        assert state[-4] == pytest.approx(0.5)
        assert state[-3] == pytest.approx(0.8)
        assert state[-2] == pytest.approx(0.5)


@pytest.mark.unit
class TestDiscountedReturns:
    def test_single_reward(self):
        returns = compute_discounted_returns([1.0])
        assert len(returns) == 1

    def test_multiple_rewards(self):
        returns = compute_discounted_returns([1.0, 1.0, 1.0], gamma=0.99)
        assert len(returns) == 3

    def test_empty_rewards(self):
        returns = compute_discounted_returns([])
        assert returns == []

    def test_normalization(self):
        returns = compute_discounted_returns([1.0, 2.0, 3.0])
        mean = sum(returns) / len(returns)
        assert abs(mean) < 1e-5
