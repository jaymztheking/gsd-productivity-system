from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ActionStatus
from app.schemas.project import ProjectOut
from app.schemas.tag import TagOut


class NextActionCreate(BaseModel):
    title: str
    notes: str | None = None
    status: ActionStatus = ActionStatus.inbox
    project_id: UUID | None = None
    tag_ids: list[UUID] = []


class NextActionUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    status: ActionStatus | None = None
    project_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class NextActionOut(BaseModel):
    id: UUID
    title: str
    notes: str | None
    status: ActionStatus
    project_id: UUID | None
    tags: list[TagOut]
    project: ProjectOut | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
