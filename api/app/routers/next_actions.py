from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.next_actions import (
    create_next_action,
    delete_next_action,
    get_next_action,
    list_next_actions,
    reorder_engage,
    update_next_action,
)
from app.database import get_db
from app.models.enums import ActionStatus
from app.schemas.next_action import (
    NextActionCreate,
    NextActionOut,
    NextActionReorder,
    NextActionUpdate,
)

router = APIRouter()


@router.get("/next-actions", response_model=list[NextActionOut])
async def get_next_actions(
    status: ActionStatus | None = None,
    tag_ids: list[UUID] | None = Query(None),
    session: AsyncSession = Depends(get_db),
):
    return await list_next_actions(session, status=status, tag_ids=tag_ids)


@router.post("/next-actions", response_model=NextActionOut, status_code=201)
async def post_next_action(
    data: NextActionCreate, session: AsyncSession = Depends(get_db)
):
    return await create_next_action(session, data)


@router.put("/next-actions/order", status_code=204)
async def put_engage_order(
    data: NextActionReorder, session: AsyncSession = Depends(get_db)
):
    await reorder_engage(session, data.ordered_ids)


@router.patch("/next-actions/{action_id}", response_model=NextActionOut)
async def patch_next_action(
    action_id: UUID,
    data: NextActionUpdate,
    session: AsyncSession = Depends(get_db),
):
    action = await get_next_action(session, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Next action not found")
    return await update_next_action(session, action, data)


@router.delete("/next-actions/{action_id}", status_code=204)
async def remove_next_action(
    action_id: UUID, session: AsyncSession = Depends(get_db)
):
    action = await get_next_action(session, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Next action not found")
    await delete_next_action(session, action)
