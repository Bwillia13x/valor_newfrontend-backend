"""
Database configuration for enterprise models
Provides engine and session factory for enterprise tables with performance optimizations
"""

import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from models.enterprise_models import EnterpriseBase

# Configure logging
logger = logging.getLogger(__name__)


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


def create_enterprise_engine():
    """Create SQLAlchemy engine for enterprise models with performance optimizations"""
    db_url = get_database_url()
    
    if db_url.startswith('sqlite'):
        # SQLite configuration for development with optimizations
        engine = create_engine(
            db_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,  # Connection timeout
                "isolation_level": None,  # Autocommit mode for better performance
            },
            poolclass=StaticPool,
            echo=False,  # Set to True for SQL debugging
            # SQLite-specific optimizations
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Enable SQLite performance optimizations
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes
            cursor.execute("PRAGMA cache_size=10000")  # Larger cache
            cursor.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
            cursor.close()
            
    else:
        # Production database (PostgreSQL, etc.) with connection pooling
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=20,  # Number of connections to maintain
            max_overflow=30,  # Additional connections when pool is full
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,  # Recycle connections every hour
            pool_timeout=30,  # Wait time for available connection
            echo=False,
            # Performance optimizations
            connect_args={
                "connect_timeout": 10,
                "application_name": "valor_ivx_backend",
            }
        )
        
        # Enable query logging for performance monitoring
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop()
            if total > 1.0:  # Log slow queries (>1 second)
                logger.warning(f"Slow query detected ({total:.2f}s): {statement[:100]}...")
    
    return engine


# Create engine instance
enterprise_engine = create_enterprise_engine()

# Create session factory with performance optimizations
enterprise_session_factory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=enterprise_engine,
    # Session optimization
    expire_on_commit=False,  # Keep objects loaded after commit
)

# Create scoped session for thread safety
enterprise_session = scoped_session(enterprise_session_factory)


@contextmanager
def get_enterprise_session():
    """Get enterprise database session with automatic cleanup"""
    session = enterprise_session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error: {str(e)}")
        raise
    finally:
        session.close()


def get_enterprise_session_simple():
    """Get enterprise database session (simple version for backward compatibility)"""
    return enterprise_session()


def init_enterprise_db():
    """
    Initialize enterprise database tables
    Note: This should only be used for development/testing
    Production should use Alembic migrations
    """
    try:
        EnterpriseBase.metadata.create_all(bind=enterprise_engine)
        logger.info("Enterprise database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize enterprise database: {str(e)}")
        raise


def close_enterprise_db():
    """Close enterprise database connections"""
    try:
        enterprise_session.remove()
        enterprise_engine.dispose()
        logger.info("Enterprise database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")


def health_check_db():
    """Perform database health check"""
    try:
        with get_enterprise_session() as session:
            # Simple query to test connection
            result = session.execute(text("SELECT 1"))
            result.fetchone()
            return True, "Database connection healthy"
    except Exception as e:
        return False, f"Database health check failed: {str(e)}"


def get_db_stats():
    """Get database connection pool statistics"""
    try:
        pool = enterprise_engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {str(e)}")
        return {}


# Import time module for query timing
import time
