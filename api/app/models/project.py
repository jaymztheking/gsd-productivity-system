import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", create_constraint=True),
        nullable=False,
        default=ProjectStatus.active,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    parent = relationship(
        "Project", remote_side="Project.id", back_populates="children"
    )
    children = relationship("Project", back_populates="parent", lazy="selectin")
    next_actions = relationship(
        "NextAction", back_populates="project", lazy="selectin"
    )
    links = relationship(
        "ProjectLink",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ProjectLink.sort_order",
    )
