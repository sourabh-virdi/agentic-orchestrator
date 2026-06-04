# Contributing to Agentic Orchestrator

Thank you for your interest in contributing! This document provides guidelines
and information for contributors.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/agentic-orchestrator.git
   cd agentic-orchestrator
   ```
3. **Set up** the development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -e ".[dev]"
   ```
4. **Start** infrastructure:
   ```bash
   docker compose up -d postgres redis chromadb
   ```

## Development Workflow

### Branching Strategy

- `main` — stable, release-ready code
- `develop` — integration branch for features
- `feature/<name>` — new features
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation changes

### Making Changes

1. Create a feature branch from `develop`:
   ```bash
   git checkout -b feature/my-feature develop
   ```
2. Make your changes, following the code style guidelines below
3. Write or update tests for your changes
4. Run the full test suite:
   ```bash
   make test
   ```
5. Run linting:
   ```bash
   make lint
   ```

### Code Style

- **Python:** Follow PEP 8, enforced by `ruff`
- **Type hints:** Required for all public functions
- **Docstrings:** Google style for all public modules, classes, and functions
- **Imports:** Sorted by `isort` (integrated in `ruff`)
- **Max line length:** 100 characters

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

Examples:
```
feat(planner): add budget-aware task decomposition
fix(executor): handle timeout in retry loop
docs(readme): update quickstart instructions
```

### Pull Request Process

1. Update the `CHANGELOG.md` with your changes under `[Unreleased]`
2. Ensure all CI checks pass
3. Request review from at least one maintainer
4. Squash and merge once approved

## Testing

- **Unit tests:** `pytest tests/unit/` — fast, no external dependencies
- **Integration tests:** `pytest tests/integration/` — requires Docker services
- **E2E tests:** `pytest tests/e2e/` — full system smoke test
- **Coverage target:** 80% for new code

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test file
pytest tests/unit/test_planner.py -v
```

## Reporting Issues

- Use GitHub Issues with the appropriate template
- Include: Python version, OS, Docker version, steps to reproduce
- For security issues, see [SECURITY.md](SECURITY.md)

## License

By contributing, you agree that your contributions will be licensed under the
MIT License.
