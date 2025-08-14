try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import List


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
    
    # Data Provider Settings (Phase 7)
    ALPHA_VANTAGE_RATE_LIMIT: int = 5
    ALPHA_VANTAGE_BACKUP_KEYS: List[str] = []
    
    # Circuit Breaker Settings (Phase 7)
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    
    # Retry Settings (Phase 7)
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 60.0

    # Feature Flags
    ENABLE_ML_MODELS: bool = True
    ENABLE_COLLABORATION: bool = True
    
    # Phase 9: Advanced Analytics and Machine Learning
    ENABLE_ADVANCED_ANALYTICS: bool = True
    ENABLE_AI_INSIGHTS: bool = True
    ENABLE_REAL_TIME_PROCESSING: bool = True
    ENABLE_STREAM_ANALYTICS: bool = True
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
    
    # Phase 9: Advanced Analytics Configuration
    ANALYTICS_UPDATE_INTERVAL: int = 1000  # milliseconds
    AI_INSIGHTS_CACHE_TTL: int = 300  # seconds
    REAL_TIME_STREAM_INTERVAL: float = 1.0  # seconds
    SENTIMENT_ANALYSIS_ENABLED: bool = True
    ANOMALY_DETECTION_ENABLED: bool = True
    PREDICTIVE_ANALYTICS_ENABLED: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
