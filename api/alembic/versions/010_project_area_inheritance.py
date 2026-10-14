"""Tasks in a project take the project's area

Revision ID: 010
Revises: 009
Create Date: 2026-10-13
"""
from typing import Sequence, Union

from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Until now a project task's area was only defaulted from the project and
    # could drift; from here on the API keeps it equal, so align it once.
    op.execute(
        "UPDATE next_actions SET area_id = projects.area_id FROM projects "
        "WHERE next_actions.project_id = projects.id "
        "AND next_actions.area_id IS DISTINCT FROM projects.area_id"
    )


def downgrade() -> None:
    # Data-only; the aligned areas are valid under the old rules too
    pass
