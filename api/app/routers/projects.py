from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.project_links import (
    create_link,
    delete_link,
    get_link,
    reorder_links,
    update_link,
)
from app.crud.projects import (
    create_project,
    delete_project,
    list_project_history,
    get_project,
    list_project_tasks,
    list_projects,
    reorder_project_tasks,
    update_project,
)
from app.database import get_db
from app.schemas.next_action import NextActionOut
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailOut,
    ProjectOut,
    ProjectUpdate,
    ReorderRequest,
)
from app.schemas.project_link import (
    ProjectLinkCreate,
    ProjectLinkOut,
    ProjectLinkUpdate,
)

router = APIRouter()


# --- Projects CRUD ---


@router.get("/projects", response_model=list[ProjectOut])
async def get_projects(
    root_only: bool = Query(True),
    session: AsyncSession = Depends(get_db),
):
    return await list_projects(session, root_only=root_only)


@router.get("/projects/{project_id}", response_model=ProjectDetailOut)
async def get_project_detail(
    project_id: UUID, session: AsyncSession = Depends(get_db)
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


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


@router.delete("/projects/{project_id}", status_code=204)
async def remove_project(
    project_id: UUID, session: AsyncSession = Depends(get_db)
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await delete_project(session, project)


# --- Project Tasks ---


@router.get(
    "/projects/{project_id}/tasks", response_model=list[NextActionOut]
)
async def get_project_tasks(
    project_id: UUID, session: AsyncSession = Depends(get_db)
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await list_project_tasks(session, project_id)


@router.get(
    "/projects/{project_id}/history", response_model=list[NextActionOut]
)
async def get_project_history(
    project_id: UUID, session: AsyncSession = Depends(get_db)
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await list_project_history(session, project_id)


@router.put("/projects/{project_id}/tasks/order")
async def reorder_tasks(
    project_id: UUID,
    body: ReorderRequest,
    session: AsyncSession = Depends(get_db),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await reorder_project_tasks(session, project_id, body.ordered_ids)
    return {"ok": True}


# --- Project Links ---


@router.post(
    "/projects/{project_id}/links",
    response_model=ProjectLinkOut,
    status_code=201,
)
async def post_link(
    project_id: UUID,
    data: ProjectLinkCreate,
    session: AsyncSession = Depends(get_db),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await create_link(session, project_id, data)


@router.patch(
    "/projects/{project_id}/links/{link_id}",
    response_model=ProjectLinkOut,
)
async def patch_link(
    project_id: UUID,
    link_id: UUID,
    data: ProjectLinkUpdate,
    session: AsyncSession = Depends(get_db),
):
    link = await get_link(session, link_id)
    if not link or link.project_id != project_id:
        raise HTTPException(status_code=404, detail="Link not found")
    return await update_link(session, link, data)


@router.delete(
    "/projects/{project_id}/links/{link_id}", status_code=204
)
async def remove_link(
    project_id: UUID,
    link_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    link = await get_link(session, link_id)
    if not link or link.project_id != project_id:
        raise HTTPException(status_code=404, detail="Link not found")
    await delete_link(session, link)


@router.put("/projects/{project_id}/links/order")
async def reorder_project_links(
    project_id: UUID,
    body: ReorderRequest,
    session: AsyncSession = Depends(get_db),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await reorder_links(session, project_id, body.ordered_ids)
    return {"ok": True}
