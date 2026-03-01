from uuid import UUID

from pydantic import BaseModel

from app.models.enums import TagCategory


class TagOut(BaseModel):
    id: UUID
    name: str
    category: TagCategory

    model_config = {"from_attributes": True}
