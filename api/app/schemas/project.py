from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: UUID | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    status: ProjectStatus | None = None
    description: str | None = None
    parent_id: UUID | None = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    status: ProjectStatus
    description: str | None
    parent_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailOut(ProjectOut):
    """Extended output with nested relationships for single-project GET."""

    links: list[ProjectLinkOut] = []
    children: list[ProjectOut] = []


class ReorderRequest(BaseModel):
    ordered_ids: list[UUID]


# Import here to resolve forward reference
from app.schemas.project_link import ProjectLinkOut  # noqa: E402

ProjectDetailOut.model_rebuild()
