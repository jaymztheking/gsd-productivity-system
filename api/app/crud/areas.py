from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.models.next_action import NextAction
from app.models.project import Project
from app.schemas.area import AreaCreate, AreaUpdate


async def list_areas(session: AsyncSession) -> list[Area]:
    stmt = select(Area).order_by(Area.sort_order, Area.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_area(session: AsyncSession, area_id: UUID) -> Area | None:
    return await session.get(Area, area_id)


async def create_area(session: AsyncSession, data: AreaCreate) -> Area:
    # New areas go last, so existing columns keep their places
    last = await session.scalar(select(func.max(Area.sort_order)))
    area = Area(name=data.name, sort_order=0 if last is None else last + 1)
    session.add(area)
    await _commit_unique_name(session)
    await session.refresh(area)
    return area


async def update_area(
    session: AsyncSession, area: Area, data: AreaUpdate
) -> Area:
    area.name = data.name
    await _commit_unique_name(session)
    await session.refresh(area)
    return area


async def delete_area(session: AsyncSession, area: Area) -> None:
    """Delete the area; its tasks and projects become unassigned.

    The foreign keys are ON DELETE SET NULL, but unassigning explicitly keeps
    the behaviour independent of the database enforcing them (SQLite in the
    tests does not by default).
    """
    for model in (NextAction, Project):
        await session.execute(
            update(model).where(model.area_id == area.id).values(area_id=None)
        )
    await session.delete(area)
    await session.commit()


async def reorder_areas(session: AsyncSession, ordered_ids: list[UUID]) -> None:
    """Set the display order. Every area must be listed exactly once."""
    areas = await list_areas(session)
    by_id = {a.id: a for a in areas}
    if len(ordered_ids) != len(set(ordered_ids)) or set(ordered_ids) != set(by_id):
        raise HTTPException(
            status_code=422,
            detail="ordered_ids must list every area exactly once",
        )
    for idx, area_id in enumerate(ordered_ids):
        by_id[area_id].sort_order = idx
    await session.commit()


async def require_area(session: AsyncSession, area_id: UUID | None) -> None:
    """422 if ``area_id`` names no area, rather than a foreign key error."""
    if area_id is not None and await session.get(Area, area_id) is None:
        raise HTTPException(status_code=422, detail="Area not found")


async def _commit_unique_name(session: AsyncSession) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="An area with that name already exists"
        )
