"""Daily routine items and their per-day completions

Revision ID: 006
Revises: 005
Create Date: 2026-10-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "routine_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        # Bit 0 = Monday ... bit 6 = Sunday
        sa.Column("weekday_mask", sa.SmallInteger(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_on", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "weekday_mask BETWEEN 1 AND 127", name="ck_routine_items_weekday_mask"
        ),
    )

    op.create_table(
        "routine_completions",
        sa.Column(
            "item_id",
            sa.Uuid(),
            sa.ForeignKey("routine_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("completed_on", sa.Date(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    # History queries scan by date range across all items
    op.create_index(
        "ix_routine_completions_completed_on",
        "routine_completions",
        ["completed_on"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_routine_completions_completed_on", table_name="routine_completions"
    )
    op.drop_table("routine_completions")
    op.drop_table("routine_items")
