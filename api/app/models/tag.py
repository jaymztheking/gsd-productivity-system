import uuid

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.enums import TagCategory


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    category: Mapped[TagCategory] = mapped_column(
        Enum(TagCategory, name="tag_category", create_constraint=True),
        nullable=False,
    )
