"""Manual order for next actions in Engage

Revision ID: 009
Revises: 008
Create Date: 2026-10-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "next_actions",
        sa.Column(
            "engage_sort_order", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    # Start from the order Engage showed before: oldest first
    op.execute(
        "UPDATE next_actions SET engage_sort_order = ranked.pos FROM ("
        "  SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) - 1 AS pos"
        "  FROM next_actions"
        "  WHERE status IN ('active', 'pending') AND deleted_at IS NULL"
        ") AS ranked WHERE next_actions.id = ranked.id"
    )


def downgrade() -> None:
    op.drop_column("next_actions", "engage_sort_order")
