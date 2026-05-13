"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "agentic-orchestrator"
    app_env: str = "development"
    app_debug: bool = False
    app_port: int = 8000
    app_log_level: str = "INFO"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "orchestrator"
    postgres_user: str = "orchestrator"
    postgres_password: str = "change_me_in_production"
    database_url: str = (
        "postgresql+asyncpg://orchestrator:change_me_in_production@localhost:5432/orchestrator"
    )

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8100
    chroma_url: str = "http://localhost:8100"

    # Security
    jwt_secret: str = "replace-with-a-256-bit-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    api_rate_limit: int = 100

    # Observability
    otel_service_name: str = "agentic-orchestrator"
    otel_exporter_jaeger_endpoint: str = "http://localhost:14268/api/traces"

    # Simulator
    simulator_default_seed: int = 42
    simulator_failure_rate: float = 0.1
    simulator_latency_mean: float = 0.5
    simulator_latency_std: float = 0.2

    # Training
    training_episodes: int = 1000
    training_gamma: float = 0.99
    training_lr: float = 0.001

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
