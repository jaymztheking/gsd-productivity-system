from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.areas import (
    create_area,
    delete_area,
    get_area,
    list_areas,
    reorder_areas,
    update_area,
)
from app.database import get_db
from app.schemas.area import AreaCreate, AreaOut, AreaReorder, AreaUpdate

router = APIRouter(prefix="/areas")


async def _get_or_404(session: AsyncSession, area_id: UUID):
    area = await get_area(session, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    return area


@router.get("", response_model=list[AreaOut])
async def get_areas(session: AsyncSession = Depends(get_db)):
    return await list_areas(session)


@router.post("", response_model=AreaOut, status_code=201)
async def post_area(data: AreaCreate, session: AsyncSession = Depends(get_db)):
    return await create_area(session, data)


@router.put("/order", status_code=204)
async def put_area_order(
    data: AreaReorder, session: AsyncSession = Depends(get_db)
):
    await reorder_areas(session, data.ordered_ids)


@router.patch("/{area_id}", response_model=AreaOut)
async def patch_area(
    area_id: UUID, data: AreaUpdate, session: AsyncSession = Depends(get_db)
):
    area = await _get_or_404(session, area_id)
    return await update_area(session, area, data)


@router.delete("/{area_id}", status_code=204)
async def remove_area(area_id: UUID, session: AsyncSession = Depends(get_db)):
    area = await _get_or_404(session, area_id)
    await delete_area(session, area)
