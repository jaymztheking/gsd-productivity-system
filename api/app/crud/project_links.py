from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_link import ProjectLink
from app.schemas.project_link import ProjectLinkCreate, ProjectLinkUpdate


async def create_link(
    session: AsyncSession, project_id: UUID, data: ProjectLinkCreate
) -> ProjectLink:
    # Auto-set sort_order to next available
    stmt = select(func.coalesce(func.max(ProjectLink.sort_order), -1) + 1).where(
        ProjectLink.project_id == project_id
    )
    result = await session.execute(stmt)
    next_order = result.scalar()

    link = ProjectLink(
        project_id=project_id,
        url=data.url,
        label=data.label,
        sort_order=next_order,
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def get_link(
    session: AsyncSession, link_id: UUID
) -> ProjectLink | None:
    return await session.get(ProjectLink, link_id)


async def update_link(
    session: AsyncSession, link: ProjectLink, data: ProjectLinkUpdate
) -> ProjectLink:
    if data.url is not None:
        link.url = data.url
    if data.label is not None:
        link.label = data.label
    await session.commit()
    await session.refresh(link)
    return link


async def delete_link(session: AsyncSession, link: ProjectLink) -> None:
    await session.delete(link)
    await session.commit()


async def reorder_links(
    session: AsyncSession, project_id: UUID, ordered_ids: list[UUID]
) -> None:
    stmt = (
        select(ProjectLink)
        .where(
            ProjectLink.project_id == project_id,
            ProjectLink.id.in_(ordered_ids),
        )
    )
    result = await session.execute(stmt)
    links = {l.id: l for l in result.scalars().all()}

    if len(links) != len(ordered_ids):
        raise HTTPException(
            status_code=422,
            detail="Some link IDs do not belong to this project",
        )

    for idx, link_id in enumerate(ordered_ids):
        links[link_id].sort_order = idx

    await session.commit()
