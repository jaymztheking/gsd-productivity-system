"""Areas of focus, assignable to next actions and projects

Revision ID: 008
Revises: 007
Create Date: 2026-10-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "areas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    # Deleting an area unassigns its tasks and projects rather than
    # deleting them
    for table in ("next_actions", "projects"):
        op.add_column(
            table,
            sa.Column(
                "area_id",
                sa.Uuid(),
                sa.ForeignKey("areas.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
        op.create_index(f"ix_{table}_area_id", table, ["area_id"])


def downgrade() -> None:
    for table in ("projects", "next_actions"):
        op.drop_index(f"ix_{table}_area_id", table_name=table)
        op.drop_column(table, "area_id")
    op.drop_table("areas")
