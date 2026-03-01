from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.projects import (
    create_project,
    get_project,
    list_projects,
    update_project,
)
from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter()


@router.get("/projects", response_model=list[ProjectOut])
async def get_projects(session: AsyncSession = Depends(get_db)):
    return await list_projects(session)


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def post_project(
    data: ProjectCreate, session: AsyncSession = Depends(get_db)
):
    return await create_project(session, data)


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def patch_project(
    project_id: UUID,
    data: ProjectUpdate,
    session: AsyncSession = Depends(get_db),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await update_project(session, project, data)
