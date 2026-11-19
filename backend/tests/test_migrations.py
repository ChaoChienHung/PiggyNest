"""Tests for Alembic schema migrations and pre-Alembic SQLite bridging."""

from alembic import command
from sqlalchemy import create_engine, inspect, text

from app.db.migrations import BASELINE_REVISION, _build_alembic_config, run_migrations


EXPECTED_TABLES = {
    "users",
    "piggy_banks",
    "transactions",
    "categories",
    "currency_rates",
    "recovery_challenges",
    "alembic_version",
}


def test_run_migrations_on_fresh_database(tmp_path):
    db_path = tmp_path / "fresh.db"
    engine = create_engine(f"sqlite:///{db_path}")

    run_migrations(engine)
    # Second invocation must be idempotent
    run_migrations(engine)

    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES.issubset(tables)

    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == BASELINE_REVISION
    engine.dispose()


def test_run_migrations_bridges_pre_alembic_database_without_data_loss(tmp_path):
    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}")

    # Simulate an older pre-Alembic database missing newer columns and using float amount
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE piggy_banks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name VARCHAR(50) NOT NULL,
                currency VARCHAR(10) NOT NULL DEFAULT 'NTD'
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                piggy_bank_id INTEGER NOT NULL,
                amount FLOAT NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'expense',
                category VARCHAR(100),
                description VARCHAR(255),
                date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.exec_driver_sql(
            "INSERT INTO users (id, username, email, hashed_password) VALUES (1, 'alice', 'alice@example.com', 'hash')"
        )
        conn.exec_driver_sql(
            "INSERT INTO piggy_banks (id, user_id, name, currency) VALUES (1, 1, 'Wallet', 'NTD')"
        )
        conn.exec_driver_sql(
            "INSERT INTO transactions (id, piggy_bank_id, amount, type, category, description) "
            "VALUES (1, 1, -12.34, 'expense', 'Food', 'Lunch')"
        )

    run_migrations(engine)

    inspector = inspect(engine)
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))

    user_cols = {col["name"] for col in inspector.get_columns("users")}
    assert {"token_version", "transactions_per_page", "date_format", "display_currency", "net_worth_hidden"}.issubset(
        user_cols
    )

    tx_cols = {col["name"] for col in inspector.get_columns("transactions")}
    assert "amount_minor" in tx_cols
    assert "transfer_group_id" in tx_cols
    assert "amount" not in tx_cols

    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        row = conn.execute(text("SELECT amount_minor, description FROM transactions WHERE id = 1")).one()

    assert version == BASELINE_REVISION
    assert row == (-1234, "Lunch")
    engine.dispose()


def test_alembic_downgrade_and_reupgrade(tmp_path):
    db_path = tmp_path / "roundtrip.db"
    engine = create_engine(f"sqlite:///{db_path}")

    run_migrations(engine)
    cfg = _build_alembic_config(engine)

    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "base")

    tables_after_downgrade = set(inspect(engine).get_table_names())
    assert "users" not in tables_after_downgrade
    assert "transactions" not in tables_after_downgrade

    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")

    assert EXPECTED_TABLES.issubset(set(inspect(engine).get_table_names()))
    engine.dispose()
