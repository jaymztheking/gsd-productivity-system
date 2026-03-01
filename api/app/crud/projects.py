from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.next_action import NextAction
from app.models.project import Project
from app.models.project_link import ProjectLink
from app.schemas.project import ProjectCreate, ProjectUpdate


async def list_projects(
    session: AsyncSession, root_only: bool = True
) -> list[Project]:
    stmt = select(Project).options(
        selectinload(Project.children),
        selectinload(Project.links),
        selectinload(Project.next_actions),
    )
    if root_only:
        stmt = stmt.where(Project.parent_id.is_(None))
    stmt = stmt.order_by(Project.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_project(session: AsyncSession, project_id: UUID) -> Project | None:
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.children),
            selectinload(Project.links),
            selectinload(Project.next_actions),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_project(
    session: AsyncSession, data: ProjectCreate
) -> Project:
    # Validate nesting depth — max 2 levels
    if data.parent_id is not None:
        parent = await session.get(Project, data.parent_id)
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent project not found")
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=422,
                detail="Cannot nest deeper than 2 levels (project → sub-project)",
            )

    project = Project(
        name=data.name,
        description=data.description,
        parent_id=data.parent_id,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def update_project(
    session: AsyncSession, project: Project, data: ProjectUpdate
) -> Project:
    if data.name is not None:
        project.name = data.name
    if data.status is not None:
        project.status = data.status
    if data.description is not None:
        project.description = data.description
    if data.parent_id is not None:
        # Validate nesting depth
        parent = await session.get(Project, data.parent_id)
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent project not found")
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=422,
                detail="Cannot nest deeper than 2 levels",
            )
        project.parent_id = data.parent_id
    await session.commit()
    await session.refresh(project)
    return project


async def delete_project(session: AsyncSession, project: Project) -> None:
    # Re-parent children to root level
    stmt = (
        select(Project)
        .where(Project.parent_id == project.id)
    )
    result = await session.execute(stmt)
    for child in result.scalars().all():
        child.parent_id = None

    await session.delete(project)
    await session.commit()


# --- Project Tasks ---


async def list_project_tasks(
    session: AsyncSession, project_id: UUID
) -> list[NextAction]:
    """Active (non-deleted) tasks for a project, ordered by sort order."""
    stmt = (
        select(NextAction)
        .where(
            NextAction.project_id == project_id,
            NextAction.deleted_at.is_(None),
        )
        .options(
            selectinload(NextAction.tags),
            selectinload(NextAction.project),
        )
        .order_by(NextAction.project_sort_order.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_project_history(
    session: AsyncSession, project_id: UUID
) -> list[NextAction]:
    """Completed and deleted tasks — the project's task history log."""
    stmt = (
        select(NextAction)
        .where(
            NextAction.project_id == project_id,
            or_(
                NextAction.status == "complete",
                NextAction.deleted_at.isnot(None),
            ),
        )
        .options(
            selectinload(NextAction.tags),
            selectinload(NextAction.project),
        )
        .order_by(NextAction.updated_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def reorder_project_tasks(
    session: AsyncSession, project_id: UUID, ordered_ids: list[UUID]
) -> None:
    # Verify all IDs belong to this project
    stmt = (
        select(NextAction)
        .where(
            NextAction.project_id == project_id,
            NextAction.id.in_(ordered_ids),
        )
    )
    result = await session.execute(stmt)
    tasks = {t.id: t for t in result.scalars().all()}

    if len(tasks) != len(ordered_ids):
        raise HTTPException(
            status_code=422,
            detail="Some task IDs do not belong to this project",
        )

    for idx, task_id in enumerate(ordered_ids):
        tasks[task_id].project_sort_order = idx

    await session.commit()
