from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context

# Enterprise-only metadata
from db_enterprise import create_enterprise_engine
from models.enterprise_models import EnterpriseBase

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Only manage the enterprise models here
target_metadata = EnterpriseBase.metadata


def _default_url() -> str:
    url = os.getenv("DB_URL")
    if url:
        return url
    sqlite_path = os.getenv(
        "VALOR_DB_PATH", os.path.join(os.getcwd(), "instance", "valor.db")
    )
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def run_migrations_offline() -> None:
    url = _default_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_enterprise_engine()
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
