"""Add pending_transactions, notifications, recurring_rules, and recurring_executions.

Revision ID: 0003_pending_notif_recurring
Revises: 0002_add_piggy_bank_pin
Create Date: 2026-11-20 21:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_pending_notif_recurring"
down_revision: Union[str, None] = "0002_add_piggy_bank_pin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recurring_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("piggy_bank_id", sa.Integer(), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False, server_default="expense"),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("start_date", sa.String(length=10), nullable=False),
        sa.Column("next_run_date", sa.String(length=10), nullable=False),
        sa.Column("end_date", sa.String(length=10), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["piggy_bank_id"], ["piggy_banks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recurring_rules_id", "recurring_rules", ["id"])
    op.create_index("ix_recurring_rules_user_id", "recurring_rules", ["user_id"])
    op.create_index("ix_recurring_rules_piggy_bank_id", "recurring_rules", ["piggy_bank_id"])
    op.create_index("ix_recurring_rules_next_run_date", "recurring_rules", ["next_run_date"])
    op.create_index("ix_recurring_rules_status", "recurring_rules", ["status"])

    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("recurring_rule_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_transactions_recurring_rule_id", ["recurring_rule_id"])
        batch_op.create_foreign_key(
            "fk_transactions_recurring_rule_id",
            "recurring_rules",
            ["recurring_rule_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "recurring_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.String(length=10), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["rule_id"], ["recurring_rules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_id", "scheduled_date", name="uq_recurring_rule_date"),
    )
    op.create_index("ix_recurring_executions_id", "recurring_executions", ["id"])
    op.create_index("ix_recurring_executions_rule_id", "recurring_executions", ["rule_id"])

    op.create_table(
        "pending_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("piggy_bank_id", sa.Integer(), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False, server_default="expense"),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("expected_date", sa.String(length=10), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("confirmed_transaction_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["piggy_bank_id"], ["piggy_banks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["confirmed_transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pending_transactions_id", "pending_transactions", ["id"])
    op.create_index("ix_pending_transactions_user_id", "pending_transactions", ["user_id"])
    op.create_index("ix_pending_transactions_piggy_bank_id", "pending_transactions", ["piggy_bank_id"])
    op.create_index("ix_pending_transactions_status", "pending_transactions", ["status"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False, server_default="info"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("event_key", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_key", name="uq_notification_user_event_key"),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("pending_transactions")
    op.drop_table("recurring_executions")

    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.drop_constraint("fk_transactions_recurring_rule_id", type_="foreignkey")
        batch_op.drop_index("ix_transactions_recurring_rule_id")
        batch_op.drop_column("recurring_rule_id")

    op.drop_table("recurring_rules")
