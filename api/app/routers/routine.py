from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import get_today, next_local_midnight
from app.crud.routine import (
    create_routine_item,
    delete_routine_item,
    get_history,
    get_routine_item,
    list_routine_items,
    list_today,
    reorder_routine_items,
    set_completion,
    update_routine_item,
)
from app.database import get_db
from app.schemas.routine import (
    RoutineCompletionSet,
    RoutineHistory,
    RoutineHistoryItem,
    RoutineItemCreate,
    RoutineItemOut,
    RoutineItemUpdate,
    RoutineReorder,
    RoutineToday,
    RoutineTodayItem,
)

router = APIRouter(prefix="/routine")

# Default and maximum span for GET /routine/history
HISTORY_DEFAULT_DAYS = 30
HISTORY_MAX_DAYS = 366


async def _get_or_404(session: AsyncSession, item_id: UUID):
    item = await get_routine_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Routine item not found")
    return item


@router.get("/today", response_model=RoutineToday)
async def get_routine_today(
    today: date = Depends(get_today),
    session: AsyncSession = Depends(get_db),
):
    rows = await list_today(session, today)
    return RoutineToday(
        date=today,
        weekday=today.weekday(),
        next_reset_at=next_local_midnight(today),
        items=[
            RoutineTodayItem(
                **RoutineItemOut.model_validate(item).model_dump(),
                completed=completed,
            )
            for item, completed in rows
        ],
    )


@router.get("/items", response_model=list[RoutineItemOut])
async def get_routine_items(session: AsyncSession = Depends(get_db)):
    return await list_routine_items(session)


@router.post("/items", response_model=RoutineItemOut, status_code=201)
async def post_routine_item(
    data: RoutineItemCreate,
    today: date = Depends(get_today),
    session: AsyncSession = Depends(get_db),
):
    return await create_routine_item(session, data, today)


@router.put("/items/order", status_code=204)
async def put_routine_order(
    data: RoutineReorder, session: AsyncSession = Depends(get_db)
):
    await reorder_routine_items(session, data.ordered_ids)


@router.patch("/items/{item_id}", response_model=RoutineItemOut)
async def patch_routine_item(
    item_id: UUID,
    data: RoutineItemUpdate,
    session: AsyncSession = Depends(get_db),
):
    item = await _get_or_404(session, item_id)
    return await update_routine_item(session, item, data)


@router.delete("/items/{item_id}", status_code=204)
async def remove_routine_item(
    item_id: UUID, session: AsyncSession = Depends(get_db)
):
    item = await _get_or_404(session, item_id)
    await delete_routine_item(session, item)


@router.put("/items/{item_id}/completion", status_code=204)
async def put_routine_completion(
    item_id: UUID,
    data: RoutineCompletionSet,
    today: date = Depends(get_today),
    session: AsyncSession = Depends(get_db),
):
    item = await _get_or_404(session, item_id)
    if data.date != today:
        # Most likely a page left open across midnight. Refusing makes the
        # client reload today's list instead of silently ticking the wrong day.
        raise HTTPException(
            status_code=409,
            detail=f"Only today ({today.isoformat()}) can be changed",
        )
    if data.completed and not item.is_scheduled_on(today):
        raise HTTPException(
            status_code=422, detail="Item is not scheduled for today"
        )
    await set_completion(session, item, today, data.completed)


@router.get("/history", response_model=RoutineHistory)
async def get_routine_history(
    start: date | None = None,
    end: date | None = None,
    today: date = Depends(get_today),
    session: AsyncSession = Depends(get_db),
):
    end = end or today
    start = start or end - timedelta(days=HISTORY_DEFAULT_DAYS - 1)
    if start > end:
        raise HTTPException(status_code=422, detail="start must not be after end")
    if (end - start).days + 1 > HISTORY_MAX_DAYS:
        raise HTTPException(
            status_code=422,
            detail=f"Range may span at most {HISTORY_MAX_DAYS} days",
        )

    rows = await get_history(session, start, end)
    return RoutineHistory(
        start=start,
        end=end,
        items=[
            RoutineHistoryItem(
                id=item.id,
                title=item.title,
                weekdays=item.weekdays,
                created_on=item.created_on,
                deleted_at=item.deleted_at,
                completed_dates=dates,
            )
            for item, dates in rows
        ],
    )
