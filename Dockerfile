FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install . 2>/dev/null || pip install \
    fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy[asyncio] asyncpg alembic redis chromadb \
    networkx torch --index-url https://download.pytorch.org/whl/cpu \
    sentence-transformers streamlit prometheus-client \
    opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger \
    opentelemetry-instrumentation-fastapi httpx structlog \
    python-jose[cryptography] passlib[bcrypt] tenacity numpy

FROM base AS production

COPY src/ ./src/
COPY scripts/ ./scripts/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()"

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
