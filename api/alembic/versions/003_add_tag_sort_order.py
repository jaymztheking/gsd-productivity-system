"""Add sort_order column to tags for ordinal ordering

Revision ID: 003
Revises: 002
Create Date: 2026-03-01
"""
from typing import Sequence, Union
from uuid import UUID, uuid5

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Same namespace as seed migration
GSD_NAMESPACE = UUID("d1b0e1a2-3c4d-5e6f-7a8b-9c0d1e2f3a4b")

# Ordinal sort order per category
TAG_ORDER = {
    # Context — alphabetical is fine, but explicit for user reordering later
    "@calls": 0,
    "@errands": 1,
    "@home": 2,
    "@online": 3,
    # Time horizon — urgency order
    "#now": 0,
    "#today": 1,
    "#week": 2,
    "#month": 3,
    "#someday": 4,
    # Energy — ascending effort
    "+easy": 0,
    "+routine": 1,
    "+focused": 2,
    "+peak": 3,
}


def upgrade() -> None:
    op.add_column(
        "tags",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    # Set correct sort order for each seeded tag
    for name, order in TAG_ORDER.items():
        tag_id = str(uuid5(GSD_NAMESPACE, name))
        op.execute(
            sa.text(
                "UPDATE tags SET sort_order = :order WHERE id = :id"
            ).bindparams(order=order, id=tag_id)
        )


def downgrade() -> None:
    op.drop_column("tags", "sort_order")
