"""Create core tables: tags, projects, next_actions, next_action_tags

Revision ID: 001
Revises:
Create Date: 2025-02-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum types
action_status = sa.Enum("inbox", "active", "pending", "complete", name="action_status")
project_status = sa.Enum("active", "complete", name="project_status")
tag_category = sa.Enum("context", "time", "energy", name="tag_category")


def upgrade() -> None:
    # --- tags ---
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("category", tag_category, nullable=False),
    )

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", project_status, nullable=False, server_default="active"),
        sa.Column("index_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # --- next_actions ---
    op.create_table(
        "next_actions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", action_status, nullable=False, server_default="inbox"),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_next_actions_status", "next_actions", ["status"])
    op.create_index("ix_next_actions_project_id", "next_actions", ["project_id"])

    # --- next_action_tags (junction) ---
    op.create_table(
        "next_action_tags",
        sa.Column(
            "next_action_id",
            sa.Uuid(),
            sa.ForeignKey("next_actions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Uuid(),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_next_action_tags_next_action_id",
        "next_action_tags",
        ["next_action_id"],
    )
    op.create_index(
        "ix_next_action_tags_tag_id", "next_action_tags", ["tag_id"]
    )


def downgrade() -> None:
    op.drop_table("next_action_tags")
    op.drop_table("next_actions")
    op.drop_table("projects")
    op.drop_table("tags")
    action_status.drop(op.get_bind(), checkfirst=True)
    project_status.drop(op.get_bind(), checkfirst=True)
    tag_category.drop(op.get_bind(), checkfirst=True)
