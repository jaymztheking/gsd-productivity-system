from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AreaCreate(BaseModel):
    name: Name


class AreaUpdate(BaseModel):
    name: Name


class AreaOut(BaseModel):
    id: UUID
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AreaReorder(BaseModel):
    ordered_ids: list[UUID]
