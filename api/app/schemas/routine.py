from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# 0 = Monday ... 6 = Sunday, matching Python's date.weekday()
Weekday = Annotated[int, Field(ge=0, le=6)]


def _check_weekdays(value: list[int] | None) -> list[int] | None:
    if value is None:
        return value
    if not value:
        raise ValueError("schedule the item on at least one day")
    return sorted(set(value))


class RoutineItemCreate(BaseModel):
    title: Title
    weekdays: list[Weekday]

    _weekdays = field_validator("weekdays")(_check_weekdays)


class RoutineItemUpdate(BaseModel):
    title: Title | None = None
    weekdays: list[Weekday] | None = None

    _weekdays = field_validator("weekdays")(_check_weekdays)


class RoutineItemOut(BaseModel):
    id: UUID
    title: str
    weekdays: list[int]
    sort_order: int
    created_on: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoutineTodayItem(RoutineItemOut):
    completed: bool


class RoutineToday(BaseModel):
    date: date
    weekday: int
    # When today ends in the user's timezone, so the UI can refresh then
    next_reset_at: datetime
    items: list[RoutineTodayItem]


class RoutineCompletionSet(BaseModel):
    # The day the client is showing. Must equal the server's local today, so
    # a page left open past midnight cannot tick yesterday's list into today.
    date: date
    completed: bool


class RoutineReorder(BaseModel):
    ordered_ids: list[UUID]


class RoutineHistoryItem(BaseModel):
    id: UUID
    title: str
    weekdays: list[int]
    created_on: date
    deleted_at: datetime | None
    completed_dates: list[date]


class RoutineHistory(BaseModel):
    start: date
    end: date
    items: list[RoutineHistoryItem]
