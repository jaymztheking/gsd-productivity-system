from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ActionStatus
from app.models.next_action import NextAction, next_action_tags
from app.models.tag import Tag
from app.schemas.next_action import NextActionCreate, NextActionUpdate


async def list_next_actions(
    session: AsyncSession,
    status: ActionStatus | None = None,
    tag_ids: list[UUID] | None = None,
) -> list[NextAction]:
    stmt = select(NextAction)

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
    action = NextAction(
        title=data.title,
        notes=data.notes,
        status=data.status,
        project_id=data.project_id,
    )

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
        action.status = data.status

    if data.project_id is not None:
        action.project_id = data.project_id

    # Update tags if provided (replace all)
    if data.tag_ids is not None:
        # Clear existing associations
        await session.execute(
            delete(next_action_tags).where(
                next_action_tags.c.next_action_id == action.id
            )
        )
        await session.flush()

        if data.tag_ids:
            tags = await _fetch_tags(session, data.tag_ids)
            action.tags = tags
        else:
            action.tags = []

    await session.commit()
    await session.refresh(action)
    return action


async def delete_next_action(
    session: AsyncSession, action: NextAction
) -> None:
    await session.delete(action)
    await session.commit()


async def _fetch_tags(
    session: AsyncSession, tag_ids: list[UUID]
) -> list[Tag]:
    stmt = select(Tag).where(Tag.id.in_(tag_ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())
