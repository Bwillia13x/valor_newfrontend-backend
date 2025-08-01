"""
Production Configuration for Valor IVX Platform
Enterprise-grade settings for security, performance, and scalability
"""

import os
from typing import List, Dict, Any
from pydantic import BaseSettings, validator


class ProductionSettings(BaseSettings):
    """Production configuration settings"""
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis Configuration
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # Security Settings
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = 2592000  # 30 days
    JWT_ALGORITHM: str = "HS256"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 3600
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "1000 per hour"
    RATE_LIMIT_STORAGE_URL: str = "redis://localhost:6379/1"
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str
    ALPHA_VANTAGE_RATE_LIMIT: int = 5
    ALPHA_VANTAGE_BACKUP_KEYS: List[str] = []
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: List[str] = ["requests.exceptions.RequestException"]
    
    # Retry Settings
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 60.0
    RETRY_BACKOFF_MULTIPLIER: float = 2.0
    
    # Caching Configuration
    CACHE_TYPE: str = "redis"
    CACHE_REDIS_URL: str
    CACHE_DEFAULT_TIMEOUT: int = 300
    CACHE_KEY_PREFIX: str = "valor_ivx:"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/app/logs/valor_ivx.log"
    LOG_MAX_SIZE: int = 100 * 1024 * 1024  # 100MB
    LOG_BACKUP_COUNT: int = 5
    
    # Monitoring and Metrics
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    METRICS_PATH: str = "/metrics"
    ENABLE_HEALTH_CHECKS: bool = True
    HEALTH_CHECK_INTERVAL: int = 30
    
    # Performance Settings
    WORKER_PROCESSES: int = 4
    WORKER_THREADS: int = 2
    WORKER_CONNECTIONS: int = 1000
    WORKER_TIMEOUT: int = 120
    WORKER_KEEPALIVE: int = 2
    WORKER_MAX_REQUESTS: int = 1000
    WORKER_MAX_REQUESTS_JITTER: int = 100
    
    # File Upload Settings
    MAX_CONTENT_LENGTH: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER: str = "/app/uploads"
    ALLOWED_EXTENSIONS: List[str] = ["csv", "xlsx", "xls", "json"]
    
    # WebSocket Settings
    WEBSOCKET_PING_INTERVAL: int = 25
    WEBSOCKET_PING_TIMEOUT: int = 10
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    
    # ML Model Settings
    ML_MODEL_CACHE_SIZE: int = 100
    ML_MODEL_TIMEOUT: int = 30
    ML_MODEL_BATCH_SIZE: int = 32
    
    # Feature Flags
    ENABLE_ML_MODELS: bool = True
    ENABLE_COLLABORATION: bool = True
    ENABLE_REAL_TIME_UPDATES: bool = True
    ENABLE_ADVANCED_ANALYTICS: bool = True
    
    # Collaboration Settings
    COLLAB_ENABLE_OT_ENGINE: bool = True
    COLLAB_SNAPSHOT_INTERVAL: int = 50
    COLLAB_REDIS_CHANNEL_PREFIX: str = "collab"
    COLLAB_MAX_ROOM_SIZE: int = 50
    COLLAB_RATE_LIMIT_OPS_PER_MIN: int = 120
    
    # SSL/TLS Settings
    SSL_CERT_FILE: str = "/etc/ssl/certs/cert.pem"
    SSL_KEY_FILE: str = "/etc/ssl/private/key.pem"
    SSL_VERIFY_MODE: str = "CERT_REQUIRED"
    
    # Session Configuration
    SESSION_TYPE: str = "redis"
    SESSION_REDIS: str
    SESSION_KEY_PREFIX: str = "session:"
    SESSION_PERMANENT: bool = False
    SESSION_LIFETIME: int = 3600
    
    # Email Configuration (for notifications)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    
    # CDN Configuration
    CDN_URL: str = ""
    CDN_ENABLED: bool = False
    
    # Backup Configuration
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_S3_BUCKET: str = ""
    
    # Security Headers
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    }
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('ALPHA_VANTAGE_BACKUP_KEYS', pre=True)
    def parse_backup_keys(cls, v):
        if isinstance(v, str):
            return [key.strip() for key in v.split(',') if key.strip()]
        return v
    
    @validator('ALLOWED_EXTENSIONS', pre=True)
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(',')]
        return v
    
    class Config:
        env_file = ".env.production"
        case_sensitive = True


# Initialize production settings
production_settings = ProductionSettings()


def get_database_config() -> Dict[str, Any]:
    """Get database configuration for SQLAlchemy"""
    return {
        'SQLALCHEMY_DATABASE_URI': production_settings.DATABASE_URL,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_size': production_settings.DATABASE_POOL_SIZE,
            'max_overflow': production_settings.DATABASE_MAX_OVERFLOW,
            'pool_timeout': production_settings.DATABASE_POOL_TIMEOUT,
            'pool_recycle': production_settings.DATABASE_POOL_RECYCLE,
            'pool_pre_ping': True,
        },
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }


def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration"""
    return {
        'url': production_settings.REDIS_URL,
        'max_connections': production_settings.REDIS_MAX_CONNECTIONS,
        'socket_timeout': production_settings.REDIS_SOCKET_TIMEOUT,
        'socket_connect_timeout': production_settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        'retry_on_timeout': True,
        'health_check_interval': 30,
    }


def get_gunicorn_config() -> Dict[str, Any]:
    """Get Gunicorn configuration"""
    return {
        'bind': '0.0.0.0:5002',
        'workers': production_settings.WORKER_PROCESSES,
        'worker_class': 'sync',
        'worker_connections': production_settings.WORKER_CONNECTIONS,
        'timeout': production_settings.WORKER_TIMEOUT,
        'keepalive': production_settings.WORKER_KEEPALIVE,
        'max_requests': production_settings.WORKER_MAX_REQUESTS,
        'max_requests_jitter': production_settings.WORKER_MAX_REQUESTS_JITTER,
        'preload_app': True,
        'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
        'accesslog': '/app/logs/gunicorn_access.log',
        'errorlog': '/app/logs/gunicorn_error.log',
        'loglevel': 'info',
    }


def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration"""
    return {
        'CACHE_TYPE': production_settings.CACHE_TYPE,
        'CACHE_REDIS_URL': production_settings.CACHE_REDIS_URL,
        'CACHE_DEFAULT_TIMEOUT': production_settings.CACHE_DEFAULT_TIMEOUT,
        'CACHE_KEY_PREFIX': production_settings.CACHE_KEY_PREFIX,
        'CACHE_OPTIONS': {
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
        }
    }


def get_session_config() -> Dict[str, Any]:
    """Get session configuration"""
    return {
        'SESSION_TYPE': production_settings.SESSION_TYPE,
        'SESSION_REDIS': production_settings.SESSION_REDIS,
        'SESSION_KEY_PREFIX': production_settings.SESSION_KEY_PREFIX,
        'SESSION_PERMANENT': production_settings.SESSION_PERMANENT,
        'PERMANENT_SESSION_LIFETIME': production_settings.SESSION_LIFETIME,
    }


def get_jwt_config() -> Dict[str, Any]:
    """Get JWT configuration"""
    return {
        'JWT_SECRET_KEY': production_settings.JWT_SECRET_KEY,
        'JWT_ACCESS_TOKEN_EXPIRES': production_settings.JWT_ACCESS_TOKEN_EXPIRES,
        'JWT_REFRESH_TOKEN_EXPIRES': production_settings.JWT_REFRESH_TOKEN_EXPIRES,
        'JWT_ALGORITHM': production_settings.JWT_ALGORITHM,
        'JWT_TOKEN_LOCATION': ['headers'],
        'JWT_HEADER_NAME': 'Authorization',
        'JWT_HEADER_TYPE': 'Bearer',
    }
