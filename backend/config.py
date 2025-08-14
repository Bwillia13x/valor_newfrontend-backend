"""
Configuration settings for Valor IVX Backend
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS settings
    CORS_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///valor_ivx_dev.db'
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///valor_ivx.db'
    
    # Security settings for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Only validate in actual production environment
    if os.environ.get('FLASK_ENV') == 'production':
        if not SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required in production")
        if not JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY environment variable is required in production")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

def get_enterprise_database_url():
    """
    Get enterprise database URL with fallback logic:
    1. DB_URL environment variable (for production)
    2. VALOR_DB_PATH environment variable (alternative)
    3. SQLite fallback for development
    """
    # Production database URL
    db_url = os.environ.get('DB_URL')
    if db_url:
        return db_url
    
    # Alternative database path
    valor_db_path = os.environ.get('VALOR_DB_PATH')
    if valor_db_path:
        return f"sqlite:///{valor_db_path}"
    
    # Development fallback
    return "sqlite:///valor_ivx_enterprise.db"


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 