from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


async def list_projects(session: AsyncSession) -> list[Project]:
    stmt = select(Project).order_by(Project.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_project(session: AsyncSession, project_id: UUID) -> Project | None:
    return await session.get(Project, project_id)


async def create_project(
    session: AsyncSession, data: ProjectCreate
) -> Project:
    project = Project(name=data.name, index_notes=data.index_notes)
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
    if data.index_notes is not None:
        project.index_notes = data.index_notes
    await session.commit()
    await session.refresh(project)
    return project
