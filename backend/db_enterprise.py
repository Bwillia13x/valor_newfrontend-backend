"""
Database configuration for enterprise models
Provides engine and session factory for enterprise tables
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from models.enterprise_models import EnterpriseBase


def get_database_url():
    """
    Get database URL with fallback logic:
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


# Create engine with appropriate configuration
def create_enterprise_engine():
    """Create SQLAlchemy engine for enterprise models"""
    db_url = get_database_url()
    
    if db_url.startswith('sqlite'):
        # SQLite configuration for development
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False  # Set to True for SQL debugging
        )
    else:
        # Production database (PostgreSQL, etc.)
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
    
    return engine


# Create engine instance
enterprise_engine = create_enterprise_engine()

# Create session factory
enterprise_session_factory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=enterprise_engine
)

# Create scoped session for thread safety
enterprise_session = scoped_session(enterprise_session_factory)


def get_enterprise_session():
    """Get enterprise database session"""
    return enterprise_session()


def init_enterprise_db():
    """
    Initialize enterprise database tables
    Note: This should only be used for development/testing
    Production should use Alembic migrations
    """
    EnterpriseBase.metadata.create_all(bind=enterprise_engine)


def close_enterprise_db():
    """Close enterprise database connections"""
    enterprise_session.remove()
    enterprise_engine.dispose()
