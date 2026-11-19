"""Add is_pinned column to piggy_banks.

Revision ID: 0002_add_piggy_bank_pin
Revises: 0001_initial_schema
Create Date: 2026-11-19 18:25:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_piggy_bank_pin"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("piggy_banks", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_pinned", sa.Boolean(), server_default="0", nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("piggy_banks", schema=None) as batch_op:
        batch_op.drop_column("is_pinned")
