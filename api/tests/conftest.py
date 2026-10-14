"""Shared fixture for API tests that need a real database.

``api_client`` sends requests through the real routers and crud functions
against a SQLite file. Older test files define their own ``client`` fixture
along the same lines; new ones use this.
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
def api_client(tmp_path):
    # A file rather than :memory:, and no pooling, so every request's
    # session sees the same database regardless of which loop it runs on.
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'api.db'}", poolclass=NullPool
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
