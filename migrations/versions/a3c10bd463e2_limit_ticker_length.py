"""Limit ticker length to the ORM contract.

Revision ID: a3c10bd463e2
Revises: ad3ee0b73215
Create Date: 2026-08-01 19:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a3c10bd463e2"
down_revision: str | Sequence[str] | None = "ad3ee0b73215"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Constrain tickers without silently truncating existing values."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM ticks WHERE char_length(ticker) > 16
                    ) THEN
                        RAISE EXCEPTION
                            'ticks.ticker contains values longer than 16 characters';
                    END IF;
                END
                $$
                """
            )
        )

    with op.batch_alter_table("ticks") as batch_op:
        batch_op.alter_column(
            "ticker",
            existing_type=sa.String(),
            type_=sa.String(length=16),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Restore the unconstrained ticker string type."""
    with op.batch_alter_table("ticks") as batch_op:
        batch_op.alter_column(
            "ticker",
            existing_type=sa.String(length=16),
            type_=sa.String(),
            existing_nullable=False,
        )
