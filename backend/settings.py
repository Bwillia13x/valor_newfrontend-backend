from pydantic import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///valor_ivx.db"
    DB_URL: str = ""  # Production database URL (PostgreSQL, etc.)
    VALOR_DB_PATH: str = ""  # Alternative database path
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me"
    JWT_SECRET_KEY: str = "change-me"

    # External APIs
    ALPHA_VANTAGE_API_KEY: str = ""

    # Feature Flags
    ENABLE_ML_MODELS: bool = True
    ENABLE_COLLABORATION: bool = True
    # Collaboration engine (Phase 4)
    COLLAB_ENABLE_OT_ENGINE: bool = True
    COLLAB_SNAPSHOT_INTERVAL: int = 50
    COLLAB_REDIS_CHANNEL_PREFIX: str = "collab"
    COLLAB_MAX_ROOM_SIZE: int = 50
    COLLAB_RATE_LIMIT_OPS_PER_MIN: int = 120
    COLLAB_ENABLE_ALLOWLIST: bool = False
    COLLAB_TENANT_ALLOWLIST: list[str] = []

    # Observability / Logging
    LOG_JSON: bool = True
    LOG_LEVEL: str = "INFO"
    FEATURE_PROMETHEUS_METRICS: bool = True
    # When true, adds {model, variant} labels to model metrics. Beware label cardinality.
    FEATURE_MODEL_VARIANT_METRICS: bool = False
    METRICS_ROUTE: str = "/metrics"
    PROMETHEUS_MULTIPROC_DIR: str = ""  # set when running with gunicorn workers

    # ML model selection / experimentation
    REVENUE_MODEL_NAME: str = "revenue_predictor"
    PORTFOLIO_OPTIMIZER_NAME: str = "portfolio_optimizer"
    REVENUE_MODEL_VARIANT: str = ""  # e.g., "v2", "ab_group_b"
    PORTFOLIO_OPTIMIZER_VARIANT: str = ""  # e.g., "risk_parity", "min_var_v2"

    class Config:
        env_file = ".env"


settings = Settings()
