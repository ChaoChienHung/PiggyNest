"""Programmatic Alembic migration runner with pre-Alembic database bridging."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.base import Base
from app.db.money_migration import migrate_money

BASELINE_REVISION = "0001_initial_schema"
BASELINE_TABLES = (
    "users",
    "piggy_banks",
    "transactions",
    "categories",
    "currency_rates",
    "recovery_challenges",
)
BACKEND_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = BACKEND_DIR / "alembic.ini"
ALEMBIC_SCRIPT_DIR = BACKEND_DIR / "migrations"


def _build_alembic_config(engine: Engine) -> Config:
    cfg = Config(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("script_location", str(ALEMBIC_SCRIPT_DIR))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    cfg.attributes["skip_logging_config"] = True
    return cfg


def _bring_pre_alembic_db_to_baseline(engine: Engine) -> None:
    """Upgrade an existing pre-Alembic SQLite database to the 0001 baseline schema."""
    baseline_table_objs = [
        Base.metadata.tables[name]
        for name in BASELINE_TABLES
        if name in Base.metadata.tables
    ]
    Base.metadata.create_all(bind=engine, tables=baseline_table_objs)
    migrate_money(engine)

    inspector = inspect(engine)
    tx_columns = {col["name"] for col in inspector.get_columns("transactions")}
    if "transfer_group_id" not in tx_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN transfer_group_id VARCHAR(36)"))

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    legacy_user_columns = (
        ("token_version", "INTEGER NOT NULL DEFAULT 0"),
        ("transactions_per_page", "INTEGER NOT NULL DEFAULT 20"),
        ("date_format", "VARCHAR(10) NOT NULL DEFAULT 'YYYY-MM-DD'"),
        ("display_currency", "VARCHAR(10) NOT NULL DEFAULT 'NTD'"),
        ("net_worth_hidden", "BOOLEAN NOT NULL DEFAULT 0"),
    )
    for col_name, col_ddl in legacy_user_columns:
        if col_name not in user_columns:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_ddl}"))


def run_migrations(engine: Engine) -> None:
    """Apply versioned Alembic migrations to head, stamping pre-Alembic DBs safely."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    has_alembic_version = "alembic_version" in existing_tables
    has_legacy_schema = "users" in existing_tables and not has_alembic_version

    cfg = _build_alembic_config(engine)

    if has_legacy_schema:
        _bring_pre_alembic_db_to_baseline(engine)
        with engine.begin() as connection:
            cfg.attributes["connection"] = connection
            command.stamp(cfg, BASELINE_REVISION)

    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
