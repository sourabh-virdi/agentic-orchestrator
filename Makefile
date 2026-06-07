.PHONY: dev test lint build seed train bench clean help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Start development environment (Docker Compose + API with reload)
	docker compose up -d postgres redis chromadb prometheus grafana jaeger
	@echo "Waiting for services to start..."
	@sleep 5
	uvicorn src.api.main:app --reload --port 8000

test: ## Run full test suite with coverage
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests (requires Docker services)
	pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end smoke tests
	pytest tests/e2e/ -v -m e2e

lint: ## Run linters (ruff + mypy)
	ruff check src/ tests/
	ruff format --check src/ tests/
	mypy src/ --ignore-missing-imports

format: ## Auto-format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

build: ## Build Docker image
	docker build -t agentic-orchestrator:latest .

seed: ## Seed synthetic data
	python scripts/seed_data.py

train: ## Run toy policy training loop
	python -m src.policy.trainer

bench: ## Run load tests with Locust
	locust -f benchmarks/locust/locustfile.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000

up: ## Start all services with Docker Compose
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## Tail Docker Compose logs
	docker compose logs -f

clean: ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/ *.egg-info
