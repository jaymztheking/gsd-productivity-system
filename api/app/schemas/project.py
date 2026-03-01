from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    index_notes: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    status: ProjectStatus | None = None
    index_notes: str | None = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    status: ProjectStatus
    index_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
