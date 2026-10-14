"""Someday/Maybe becomes a next-action status; retire the #someday tag

Revision ID: 007
Revises: 006
Create Date: 2026-10-13
"""
from typing import Sequence, Union
from uuid import UUID, uuid5

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Same namespace as the seed migration, so this is the seeded #someday tag
GSD_NAMESPACE = UUID("d1b0e1a2-3c4d-5e6f-7a8b-9c0d1e2f3a4b")
SOMEDAY_TAG_ID = str(uuid5(GSD_NAMESPACE, "#someday"))


def upgrade() -> None:
    # Postgres will not use a new enum value inside the transaction that
    # added it, so the ALTER has to commit before the UPDATE below runs.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE action_status ADD VALUE IF NOT EXISTS 'someday'")

    # Open items tagged #someday move to the new status. Completed ones keep
    # their status; they only lose the tag.
    op.execute(
        sa.text(
            "UPDATE next_actions SET status = 'someday' "
            "WHERE status <> 'complete' AND id IN "
            "(SELECT next_action_id FROM next_action_tags WHERE tag_id = :tag)"
        ).bindparams(tag=SOMEDAY_TAG_ID)
    )
    # next_action_tags rows go with it (ON DELETE CASCADE)
    op.execute(
        sa.text("DELETE FROM tags WHERE id = :tag").bindparams(tag=SOMEDAY_TAG_ID)
    )


def downgrade() -> None:
    # Postgres cannot drop an enum value, so 'someday' stays in the type but
    # nothing uses it once items are moved back to active with the tag.
    op.execute(
        sa.text(
            "INSERT INTO tags (id, name, category, sort_order) "
            "VALUES (:tag, '#someday', 'time', 4)"
        ).bindparams(tag=SOMEDAY_TAG_ID)
    )
    # #someday was the item's time tag, and the UI allows one per category
    op.execute(
        "DELETE FROM next_action_tags WHERE next_action_id IN "
        "(SELECT id FROM next_actions WHERE status = 'someday') AND tag_id IN "
        "(SELECT id FROM tags WHERE category = 'time')"
    )
    op.execute(
        sa.text(
            "INSERT INTO next_action_tags (next_action_id, tag_id) "
            "SELECT id, :tag FROM next_actions WHERE status = 'someday'"
        ).bindparams(tag=SOMEDAY_TAG_ID)
    )
    op.execute("UPDATE next_actions SET status = 'active' WHERE status = 'someday'")
