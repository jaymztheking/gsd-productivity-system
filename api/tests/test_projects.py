"""API tests for filtering the project list by status (TASK-013).

GET /projects used to ignore ?status=, so the weekly digest's request for
active projects returned completed ones too, each flagged NO NEXT ACTION.
Requests go through the real router and crud functions against a SQLite
database file.

    PYTHONPATH=api pytest api/tests/test_projects.py -v
"""

import asyncio
import os

import pytest

TEST_TOKEN = "test-token-not-a-real-secret"
os.environ.setdefault("API_TOKEN", TEST_TOKEN)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://unused:unused@localhost:5432/unused"
)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from app.auth import API_TOKEN_HEADER  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture
def client(tmp_path):
    # A file rather than :memory:, and no pooling, so every request's
    # session sees the same database regardless of which loop it runs on.
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'projects.db'}", poolclass=NullPool
    )

    async def create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(create())
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def sqlite_db():
        async with sessions() as session:
            yield session

    # test_auth.py installs its own stub at import time; put it back after.
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = sqlite_db
    try:
        with TestClient(app, headers={API_TOKEN_HEADER: TEST_TOKEN}) as c:
            yield c
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        asyncio.run(engine.dispose())


def _create(client, name, status="active", parent_id=None):
    payload = {"name": name}
    if parent_id:
        payload["parent_id"] = parent_id
    res = client.post("/projects", json=payload)
    assert res.status_code == 201, res.text
    project = res.json()
    if status != "active":
        res = client.patch(f"/projects/{project['id']}", json={"status": status})
        assert res.status_code == 200, res.text
        project = res.json()
    return project


def _names(client, **params):
    res = client.get("/projects", params=params)
    assert res.status_code == 200, res.text
    return {p["name"] for p in res.json()}


@pytest.fixture
def projects(client):
    _create(client, "Plan trip")
    _create(client, "Paint fence", status="complete")
    parent = _create(client, "House")
    _create(client, "Fix gutters", parent_id=parent["id"])
    _create(client, "Clean garage", status="complete", parent_id=parent["id"])


def test_active_filter_excludes_completed_projects(client, projects):
    # The exact request the weekly digest makes.
    assert _names(client, status="active") == {"Plan trip", "House"}


def test_complete_filter_returns_only_completed_projects(client, projects):
    assert _names(client, status="complete") == {"Paint fence"}


def test_no_status_returns_every_status(client, projects):
    # What the UI sends: its project lists must be unchanged.
    assert _names(client) == {"Plan trip", "Paint fence", "House"}
    assert _names(client, root_only="false") == {
        "Plan trip", "Paint fence", "House", "Fix gutters", "Clean garage",
    }


def test_status_combines_with_root_only(client, projects):
    assert _names(client, status="active", root_only="false") == {
        "Plan trip", "House", "Fix gutters",
    }
    assert _names(client, status="complete", root_only="false") == {
        "Paint fence", "Clean garage",
    }


def test_unknown_status_is_rejected_not_ignored(client, projects):
    res = client.get("/projects", params={"status": "archived"})
    assert res.status_code == 422, res.text


def test_completing_a_project_drops_it_from_the_active_list(client):
    project = _create(client, "Write report")
    assert _names(client, status="active") == {"Write report"}
    res = client.patch(f"/projects/{project['id']}", json={"status": "complete"})
    assert res.status_code == 200, res.text
    assert _names(client, status="active") == set()
