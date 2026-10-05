import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class RoutineItem(Base):
    """A standing daily-routine entry. Never completed, only ticked per day."""

    __tablename__ = "routine_items"
    __table_args__ = (
        CheckConstraint(
            "weekday_mask BETWEEN 1 AND 127",
            name="ck_routine_items_weekday_mask",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    # Days the item is scheduled, as a bitmask: bit 0 = Monday ... bit 6 =
    # Sunday, matching date.weekday(). The API exposes it as a list.
    weekday_mask: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    # The user's local date at creation. Days before it are not "missed".
    created_on: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
    # Soft delete, so past completions stay available to the history view.
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    completions = relationship(
        "RoutineCompletion",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    @property
    def weekdays(self) -> list[int]:
        return [d for d in range(7) if self.weekday_mask & (1 << d)]

    def is_scheduled_on(self, day: date) -> bool:
        return bool(self.weekday_mask & (1 << day.weekday()))


class RoutineCompletion(Base):
    """One tick: item X was done on local date D. Unticking deletes the row.

    Keying on the local date is what makes the daily reset free: a new day
    simply has no rows yet, so nothing has to run at midnight.
    """

    __tablename__ = "routine_completions"

    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("routine_items.id", ondelete="CASCADE"), primary_key=True
    )
    completed_on: Mapped[date] = mapped_column(
        Date, primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    item = relationship("RoutineItem", back_populates="completions")
