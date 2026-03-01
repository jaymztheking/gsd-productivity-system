"""Seed tag taxonomy: context, time, energy tags

Revision ID: 002
Revises: 001
Create Date: 2025-02-28
"""
from typing import Sequence, Union
from uuid import UUID, uuid5

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed namespace for deterministic UUIDs — same IDs across all environments
GSD_NAMESPACE = UUID("d1b0e1a2-3c4d-5e6f-7a8b-9c0d1e2f3a4b")

TAGS = [
    # Context tags (@)
    {"name": "@home", "category": "context"},
    {"name": "@online", "category": "context"},
    {"name": "@errands", "category": "context"},
    {"name": "@calls", "category": "context"},
    # Time horizon tags (#)
    {"name": "#now", "category": "time"},
    {"name": "#today", "category": "time"},
    {"name": "#week", "category": "time"},
    {"name": "#month", "category": "time"},
    {"name": "#someday", "category": "time"},
    # Energy tags (+)
    {"name": "+easy", "category": "energy"},
    {"name": "+routine", "category": "energy"},
    {"name": "+focused", "category": "energy"},
    {"name": "+peak", "category": "energy"},
]


def upgrade() -> None:
    tags_table = sa.table(
        "tags",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("category", sa.String()),
    )
    op.bulk_insert(
        tags_table,
        [
            {
                "id": uuid5(GSD_NAMESPACE, tag["name"]),
                "name": tag["name"],
                "category": tag["category"],
            }
            for tag in TAGS
        ],
    )


def downgrade() -> None:
    tag_ids = [str(uuid5(GSD_NAMESPACE, tag["name"])) for tag in TAGS]
    op.execute(
        sa.text("DELETE FROM tags WHERE id = ANY(:ids)").bindparams(
            ids=tag_ids
        )
    )
