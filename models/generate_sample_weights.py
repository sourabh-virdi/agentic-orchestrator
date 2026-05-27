"""Generate a small sample policy weights file for the repository."""

import json
from pathlib import Path

import torch

from src.policy.network import PlannerPolicy

policy = PlannerPolicy(state_dim=32, hidden_dim=64, action_dim=8)

save_dir = Path(__file__).parent
torch.save(policy.state_dict(), save_dir / "policy_sample.pt")

metrics = {
    "total_episodes": 0,
    "best_reward": 0.0,
    "final_avg_reward_100": 0.0,
    "model_path": "models/policy_sample.pt",
    "note": "Untrained sample weights for demo purposes",
}
(save_dir / "training_metrics.json").write_text(json.dumps(metrics, indent=2))

print(f"Saved sample weights to {save_dir / 'policy_sample.pt'}")
print(f"Saved metrics to {save_dir / 'training_metrics.json'}")
