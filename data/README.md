# Synthetic Data

This directory contains synthetic data generators and generated datasets for the Agentic Orchestrator.

## Privacy & Anonymization

**All data in this directory is synthetic** — no real user data is stored or processed.

The generator (`generator.py`) includes the following privacy controls:

| Knob | Default | Description |
|------|---------|-------------|
| `anonymize_names` | `True` | Replace campaign names with anonymous identifiers |
| `anonymize_emails` | `True` | Replace any email-like fields with anonymous values |
| `hash_identifiers` | `False` | Use hex hashes instead of UUIDs for IDs |
| `seed` | `42` | Fixed seed for reproducibility |

### Privacy Design Choices

1. **No PII:** Generated data uses random templates, not real user data
2. **Deterministic generation:** Fixed seeds ensure reproducibility without storing data
3. **Anonymization by default:** All name fields are anonymized unless explicitly disabled
4. **No external data sources:** The generator is self-contained with no network calls
5. **Configurable granularity:** Audience segments use broad categories (enterprise, smb, consumer), never individual identifiers

## Usage

```bash
# Generate with defaults (100 goals, 50 memory docs, anonymized)
python data/generator.py

# Custom generation
python data/generator.py --goals 500 --docs 200 --seed 123

# Without anonymization (for debugging only)
python data/generator.py --no-anonymize
```

## Output Files

| File | Description |
|------|-------------|
| `synthetic_goals.json` | Campaign goals with constraints |
| `synthetic_goals.csv` | Same goals in CSV format |
| `synthetic_memory.json` | Vector memory documents |

## Data Schema

### Goal
```json
{
  "id": "uuid",
  "title": "Anonymous campaign name",
  "description": "Goal description with metric targets",
  "constraints": {
    "budget_usd": 5000.0,
    "deadline": "2026-06-30",
    "channels": ["email", "in-app"],
    "audience": "enterprise"
  }
}
```

### Memory Document
```json
{
  "id": "mem_0001",
  "content": "Historical campaign insight text",
  "metadata": {
    "type": "campaign_result",
    "channel": "email",
    "audience": "enterprise"
  }
}
```
