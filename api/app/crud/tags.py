from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


async def list_tags(session: AsyncSession) -> list[Tag]:
    stmt = select(Tag).order_by(Tag.category, Tag.sort_order)
    result = await session.execute(stmt)
    return list(result.scalars().all())
