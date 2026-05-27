# Model Card — Planner Policy v1.0

## Model Details

| Field | Value |
|-------|-------|
| **Name** | Planner Policy (REINFORCE) |
| **Version** | 1.0.0 |
| **Type** | Reinforcement Learning Policy (classification) |
| **Architecture** | 2-layer MLP (32 → 64 → 32 → 8) |
| **Framework** | PyTorch 2.2+ |
| **Parameters** | ~3,400 |
| **Training Algorithm** | REINFORCE with baseline |
| **File** | `policy_sample.pt` |

## Intended Use

This is a **toy model** for demonstrating how a learned policy can improve the planner agent's task decomposition decisions. It is trained entirely on synthetic data and is **not intended for production use** without further training and validation.

### Primary Use Case
- Selecting task templates during goal decomposition
- Research and experimentation with RL-based planning

### Out of Scope
- Production campaign management decisions
- Any scenario with real financial consequences

## Training Data

- **Source:** Synthetic goals from `data/generator.py`
- **Size:** 1,000 episodes (configurable)
- **Seed:** 42 (deterministic)
- **Splits:** No explicit train/val/test — evaluated on simulator reward

### Data Characteristics
- 100 unique goal templates × channel combinations
- Budget range: $500–$50,000
- Channels: email, in-app, sms, push, social
- Audiences: enterprise, smb, consumer, churned, new_user, power_user

## Metrics

| Metric | Value |
|--------|-------|
| Best Episode Reward | ~5.0 (on synthetic goals) |
| Average Reward (last 100 episodes) | ~3.2 |
| Training Loss (final) | ~-1.5 |
| Episodes | 1,000 |

## Limitations

1. **Toy model only** — trained on synthetic data with simplified reward
2. **No real-world validation** — performance on real campaigns is unknown
3. **Small state space** — 32-dimensional state vector is a simplification
4. **No safety constraints** — the policy does not enforce budget or ethical limits
5. **Overfitting risk** — limited training diversity

## Ethical Considerations

- The model makes no decisions about real users or real budgets
- All training data is synthetic — no privacy concerns
- Should not be deployed for automated decision-making without human oversight

## Versioning

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-03-14 | Initial toy model release |

Models are saved as PyTorch state dicts. Load with:
```python
from src.policy.network import PlannerPolicy
import torch

policy = PlannerPolicy(state_dim=32, action_dim=8)
policy.load_state_dict(torch.load("models/policy_sample.pt"))
```
