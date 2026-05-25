#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== Agentic Orchestrator — Local Development Setup ==="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required but not found"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required but not found"; exit 1; }

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -e ".[dev]" --quiet

# Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
fi

echo "Starting infrastructure services..."
docker compose up -d postgres redis chromadb

echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U orchestrator >/dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    sleep 1
done

echo "Seeding sample data..."
python scripts/seed_data.py

echo ""
echo "=== Setup Complete ==="
echo "API:       http://localhost:8000"
echo "Docs:      http://localhost:8000/docs"
echo "Health:    http://localhost:8000/api/v1/health"
echo ""
echo "Starting API server..."
uvicorn src.api.main:app --reload --port 8000
