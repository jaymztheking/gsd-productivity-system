from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.tags import list_tags
from app.database import get_db
from app.schemas.tag import TagOut

router = APIRouter()


@router.get("/tags", response_model=list[TagOut])
async def get_tags(session: AsyncSession = Depends(get_db)):
    return await list_tags(session)
