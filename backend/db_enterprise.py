from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .models.enterprise_models import EnterpriseBase


def get_db_url() -> str:
    """
    Returns the DB connection URL. Prefers DB_URL; falls back to VALOR_DB_PATH SQLite file.
    Example DB_URL:
      - Postgres: postgresql+psycopg2://user:pass@localhost:5432/valor
      - SQLite: sqlite:////absolute/path/to/valor.db
    """
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url

    # Fallback to existing SQLite path if present, otherwise in-repo sqlite file
    sqlite_path = os.getenv("VALOR_DB_PATH", os.path.join(os.getcwd(), "backend", "instance", "valor.db"))
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def create_enterprise_engine(echo: bool = False) -> Engine:
    db_url = get_db_url()
    # For SQLite, enable pragmatic settings via connect_args
    connect_args = {}
    if db_url.startswith("sqlite:///"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(db_url, echo=echo, future=True, connect_args=connect_args)
    return engine


def get_enterprise_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    if engine is None:
        engine = create_enterprise_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


# IMPORTANT:
# We DO NOT call EnterpriseBase.metadata.create_all(engine) here.
# Migrations (Alembic) will manage schema for the EnterpriseBase exclusively.
