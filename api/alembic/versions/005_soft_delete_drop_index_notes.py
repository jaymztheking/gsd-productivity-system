"""Soft delete for next_actions, drop index_notes from projects

Revision ID: 005
Revises: 004
Create Date: 2026-03-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Soft delete: instead of removing rows, set deleted_at timestamp
    op.add_column(
        "next_actions",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    # Drop index_notes — replaced by task history log
    op.drop_column("projects", "index_notes")


def downgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("index_notes", sa.Text(), nullable=True),
    )
    op.drop_column("next_actions", "deleted_at")
