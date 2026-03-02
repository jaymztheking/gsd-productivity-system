from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectLinkCreate(BaseModel):
    url: str
    label: str


class ProjectLinkUpdate(BaseModel):
    url: str | None = None
    label: str | None = None


class ProjectLinkOut(BaseModel):
    id: UUID
    project_id: UUID
    url: str
    label: str
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
