from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.areas import require_area
from app.models.enums import ActionStatus
from app.models.next_action import NextAction, next_action_tags
from app.models.project import Project
from app.models.tag import Tag
from app.schemas.next_action import NextActionCreate, NextActionUpdate

# The statuses shown in Engage, which share one manual order
OPEN_STATUSES = (ActionStatus.active, ActionStatus.pending)


async def list_next_actions(
    session: AsyncSession,
    status: ActionStatus | None = None,
    tag_ids: list[UUID] | None = None,
) -> list[NextAction]:
    stmt = select(NextAction).where(NextAction.deleted_at.is_(None))

    if status is not None:
        stmt = stmt.where(NextAction.status == status)

    if tag_ids:
        # AND logic: action must have ALL specified tags
        stmt = (
            stmt.join(next_action_tags)
            .where(next_action_tags.c.tag_id.in_(tag_ids))
            .group_by(NextAction.id)
            .having(func.count(next_action_tags.c.tag_id) == len(tag_ids))
        )

    if status in OPEN_STATUSES:
        stmt = stmt.order_by(
            NextAction.engage_sort_order.asc(), NextAction.created_at.asc()
        )
    else:
        # Intake works through the inbox oldest first
        stmt = stmt.order_by(NextAction.created_at.asc())
    stmt = stmt.options(
        selectinload(NextAction.tags),
        selectinload(NextAction.project),
    )

    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def get_next_action(
    session: AsyncSession, action_id: UUID
) -> NextAction | None:
    stmt = (
        select(NextAction)
        .where(NextAction.id == action_id)
        .options(
            selectinload(NextAction.tags),
            selectinload(NextAction.project),
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_next_action(
    session: AsyncSession, data: NextActionCreate
) -> NextAction:
    if "area_id" in data.model_fields_set:
        await require_area(session, data.area_id)
        area_id = data.area_id
    else:
        area_id = await _project_area(session, data.project_id)

    action = NextAction(
        title=data.title,
        notes=data.notes,
        status=data.status,
        project_id=data.project_id,
        area_id=area_id,
    )

    if action.status in OPEN_STATUSES:
        action.engage_sort_order = await _bottom_of_engage(session)

    # Attach tags if provided
    if data.tag_ids:
        tags = await _fetch_tags(session, data.tag_ids)
        action.tags = tags

    session.add(action)
    await session.commit()
    await session.refresh(action)
    return action


async def update_next_action(
    session: AsyncSession, action: NextAction, data: NextActionUpdate
) -> NextAction:
    if data.title is not None:
        action.title = data.title
    if data.notes is not None:
        action.notes = data.notes

    # Handle status transitions
    if data.status is not None and data.status != action.status:
        if data.status == ActionStatus.complete:
            action.completed_at = datetime.utcnow()
        elif action.status == ActionStatus.complete:
            # Moving away from complete — clear completed_at
            action.completed_at = None
        # Arriving in Engage puts the task at the bottom of the order.
        # Switching between active and pending keeps its place.
        if data.status in OPEN_STATUSES and action.status not in OPEN_STATUSES:
            action.engage_sort_order = await _bottom_of_engage(session)
        action.status = data.status

    if data.project_id is not None and data.project_id != action.project_id:
        action.project_id = data.project_id
        # An unassigned task moved into a project takes the project's area
        if action.area_id is None and "area_id" not in data.model_fields_set:
            action.area_id = await _project_area(session, data.project_id)

    if "area_id" in data.model_fields_set:
        await require_area(session, data.area_id)
        action.area_id = data.area_id

    # Update tags if provided (replace all). Assigning the collection lets
    # the ORM diff old against new; a raw DELETE first would leave the loaded
    # collection stale, so tags kept across the edit were never re-inserted.
    if data.tag_ids is not None:
        if data.tag_ids:
            action.tags = await _fetch_tags(session, data.tag_ids)
        else:
            action.tags = []

    await session.commit()
    await session.refresh(action)
    return action


async def delete_next_action(
    session: AsyncSession, action: NextAction
) -> None:
    """Soft delete — sets deleted_at instead of removing the row."""
    action.deleted_at = datetime.utcnow()
    await session.commit()


async def reorder_engage(session: AsyncSession, ordered_ids: list[UUID]) -> None:
    """Reorder some or all of the tasks shown in Engage.

    Engage usually shows a subset (filtered by tags, or one area column), so
    it sends only the tasks it shows. They are rearranged within the
    positions they already occupy, and every other open task keeps its place
    and relative order. The whole order is then renumbered densely.
    """
    stmt = (
        select(NextAction)
        .where(
            NextAction.deleted_at.is_(None),
            NextAction.status.in_(OPEN_STATUSES),
        )
        .order_by(NextAction.engage_sort_order, NextAction.created_at)
    )
    tasks = list((await session.execute(stmt)).scalars().all())
    by_id = {t.id: t for t in tasks}

    if (
        not ordered_ids
        or len(set(ordered_ids)) != len(ordered_ids)
        or any(i not in by_id for i in ordered_ids)
    ):
        raise HTTPException(
            status_code=422,
            detail="ordered_ids must be distinct active or pending tasks",
        )

    wanted = set(ordered_ids)
    slots = [idx for idx, t in enumerate(tasks) if t.id in wanted]
    for slot, task_id in zip(slots, ordered_ids):
        tasks[slot] = by_id[task_id]

    for idx, task in enumerate(tasks):
        task.engage_sort_order = idx
    await session.commit()


async def _bottom_of_engage(session: AsyncSession) -> int:
    last = await session.scalar(
        select(func.max(NextAction.engage_sort_order)).where(
            NextAction.deleted_at.is_(None),
            NextAction.status.in_(OPEN_STATUSES),
        )
    )
    return 0 if last is None else last + 1


async def _project_area(
    session: AsyncSession, project_id: UUID | None
) -> UUID | None:
    if project_id is None:
        return None
    project = await session.get(Project, project_id)
    return project.area_id if project else None


async def _fetch_tags(
    session: AsyncSession, tag_ids: list[UUID]
) -> list[Tag]:
    stmt = select(Tag).where(Tag.id.in_(tag_ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())
