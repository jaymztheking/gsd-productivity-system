from datetime import date, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.routine import RoutineCompletion, RoutineItem
from app.schemas.routine import RoutineItemCreate, RoutineItemUpdate


def _mask(weekdays: list[int]) -> int:
    mask = 0
    for day in weekdays:
        mask |= 1 << day
    return mask


def _active_items():
    return (
        select(RoutineItem)
        .where(RoutineItem.deleted_at.is_(None))
        .order_by(RoutineItem.sort_order, RoutineItem.created_at)
    )


async def list_routine_items(session: AsyncSession) -> list[RoutineItem]:
    result = await session.execute(_active_items())
    return list(result.scalars().all())


async def get_routine_item(
    session: AsyncSession, item_id: UUID
) -> RoutineItem | None:
    """Active items only; a deleted item is gone as far as editing goes."""
    stmt = select(RoutineItem).where(
        RoutineItem.id == item_id, RoutineItem.deleted_at.is_(None)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_today(
    session: AsyncSession, today: date
) -> list[tuple[RoutineItem, bool]]:
    """Items scheduled on today's weekday, each with whether it is ticked."""
    items = [
        item
        for item in await list_routine_items(session)
        if item.is_scheduled_on(today)
    ]
    done = await _completed_ids(session, [i.id for i in items], today)
    return [(item, item.id in done) for item in items]


async def create_routine_item(
    session: AsyncSession, data: RoutineItemCreate, today: date
) -> RoutineItem:
    max_order = await session.scalar(select(func.max(RoutineItem.sort_order)))
    item = RoutineItem(
        title=data.title,
        weekday_mask=_mask(data.weekdays),
        sort_order=(max_order + 1) if max_order is not None else 0,
        created_on=today,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_routine_item(
    session: AsyncSession, item: RoutineItem, data: RoutineItemUpdate
) -> RoutineItem:
    if data.title is not None:
        item.title = data.title
    if data.weekdays is not None:
        item.weekday_mask = _mask(data.weekdays)
    await session.commit()
    await session.refresh(item)
    return item


async def delete_routine_item(session: AsyncSession, item: RoutineItem) -> None:
    """Soft delete — the item leaves the checklist but keeps its history."""
    item.deleted_at = datetime.utcnow()
    await session.commit()


async def reorder_routine_items(
    session: AsyncSession, ordered_ids: list[UUID]
) -> None:
    """Reorder some or all active items.

    The UI reorders within one weekday's view, so it sends only that subset.
    The subset is rearranged within the positions it already occupies and
    every other item keeps its place; the whole list is then renumbered so
    sort_order stays dense and unambiguous.
    """
    items = await list_routine_items(session)
    by_id = {item.id: item for item in items}

    if len(set(ordered_ids)) != len(ordered_ids) or any(
        i not in by_id for i in ordered_ids
    ):
        raise HTTPException(
            status_code=422,
            detail="ordered_ids must be distinct, existing routine items",
        )

    wanted = set(ordered_ids)
    slots = [idx for idx, item in enumerate(items) if item.id in wanted]
    for slot, item_id in zip(slots, ordered_ids):
        items[slot] = by_id[item_id]

    for idx, item in enumerate(items):
        item.sort_order = idx
    await session.commit()


async def set_completion(
    session: AsyncSession, item: RoutineItem, day: date, completed: bool
) -> None:
    """Idempotently tick or untick ``item`` for ``day``."""
    existing = await session.get(RoutineCompletion, (item.id, day))
    if completed and existing is None:
        session.add(RoutineCompletion(item_id=item.id, completed_on=day))
    elif not completed and existing is not None:
        await session.execute(
            delete(RoutineCompletion).where(
                RoutineCompletion.item_id == item.id,
                RoutineCompletion.completed_on == day,
            )
        )
    await session.commit()


async def get_history(
    session: AsyncSession, start: date, end: date
) -> list[tuple[RoutineItem, list[date]]]:
    """Each item's completed dates within [start, end].

    Covers active items that existed by ``end``, plus deleted items that
    have at least one completion in the range, so removing an item does
    not erase the record of having done it.
    """
    rows = await session.execute(
        select(RoutineCompletion.item_id, RoutineCompletion.completed_on)
        .where(RoutineCompletion.completed_on.between(start, end))
        .order_by(RoutineCompletion.completed_on)
    )
    dates_by_item: dict[UUID, list[date]] = {}
    for item_id, completed_on in rows:
        dates_by_item.setdefault(item_id, []).append(completed_on)

    stmt = (
        select(RoutineItem)
        .where(
            (
                RoutineItem.deleted_at.is_(None)
                & (RoutineItem.created_on <= end)
            )
            | RoutineItem.id.in_(list(dates_by_item))
        )
        .order_by(RoutineItem.sort_order, RoutineItem.created_at)
    )
    items = (await session.execute(stmt)).scalars().all()
    return [(item, dates_by_item.get(item.id, [])) for item in items]


async def _completed_ids(
    session: AsyncSession, item_ids: list[UUID], day: date
) -> set[UUID]:
    if not item_ids:
        return set()
    result = await session.execute(
        select(RoutineCompletion.item_id).where(
            RoutineCompletion.item_id.in_(item_ids),
            RoutineCompletion.completed_on == day,
        )
    )
    return set(result.scalars().all())
