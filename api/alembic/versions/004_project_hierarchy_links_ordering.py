"""Add project hierarchy (parent_id), description, links table, task ordering

Revision ID: 004
Revises: 003
Create Date: 2026-03-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Add description to projects ---
    op.add_column(
        "projects",
        sa.Column("description", sa.Text(), nullable=True),
    )

    # --- Add parent_id to projects (self-referential FK) ---
    op.add_column(
        "projects",
        sa.Column(
            "parent_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_projects_parent_id", "projects", ["parent_id"])

    # --- Create project_links table ---
    op.create_table(
        "project_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_project_links_project_id", "project_links", ["project_id"]
    )

    # --- Add project_sort_order to next_actions ---
    op.add_column(
        "next_actions",
        sa.Column(
            "project_sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("next_actions", "project_sort_order")
    op.drop_table("project_links")
    op.drop_index("ix_projects_parent_id", table_name="projects")
    op.drop_column("projects", "parent_id")
    op.drop_column("projects", "description")
