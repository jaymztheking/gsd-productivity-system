"""Auth tests for the shared-secret guard.

Runs without a database: get_db is overridden with a stub and the crud
functions the two representative endpoints call are monkeypatched, so
these tests exercise the auth layer in isolation.

    pytest api/tests/test_auth.py -v
"""

import os
import uuid
from datetime import datetime, timezone

import pytest

TEST_TOKEN = "test-token-not-a-real-secret"
os.environ.setdefault("API_TOKEN", TEST_TOKEN)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://unused:unused@localhost:5432/unused"
)

from fastapi.testclient import TestClient  # noqa: E402

from app.auth import API_TOKEN_HEADER  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402

READ_PATH = "/tags"
WRITE_PATH = "/next-actions"


async def _stub_db():
    yield None


app.dependency_overrides[get_db] = _stub_db


@pytest.fixture
def client(monkeypatch):
    """Client whose read and write endpoints succeed without a database."""

    async def fake_list_tags(session):
        return []

    async def fake_create_next_action(session, data):
        now = datetime.now(timezone.utc)
        # Must satisfy every field on NextActionOut, or FastAPI raises a
        # response-validation error and the test fails for the wrong reason.
        return {
            "id": uuid.uuid4(),
            "title": data.title,
            "notes": None,
            "status": "inbox",
            "project_id": None,
            "tags": [],
            "project": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "deleted_at": None,
            "project_sort_order": 0,
        }

    monkeypatch.setattr("app.routers.tags.list_tags", fake_list_tags)
    monkeypatch.setattr(
        "app.routers.next_actions.create_next_action", fake_create_next_action
    )
    with TestClient(app) as c:
        yield c


def auth(token=TEST_TOKEN):
    return {API_TOKEN_HEADER: token}


# --- unauthorized ---------------------------------------------------------

@pytest.mark.parametrize("path", [READ_PATH, WRITE_PATH])
def test_missing_token_is_rejected(client, path):
    resp = client.get(path) if path == READ_PATH else client.post(path, json={"title": "x"})
    assert resp.status_code == 401


@pytest.mark.parametrize("path", [READ_PATH, WRITE_PATH])
def test_wrong_token_is_rejected(client, path):
    h = auth("wrong-token")
    resp = client.get(path, headers=h) if path == READ_PATH else client.post(path, json={"title": "x"}, headers=h)
    assert resp.status_code == 401


def test_rejection_leaks_no_data(client):
    """A refused read must not return task data, only the error envelope."""
    resp = client.get(READ_PATH)
    assert resp.status_code == 401
    assert set(resp.json().keys()) == {"detail"}


def test_missing_and_wrong_token_are_indistinguishable(client):
    """The response must not reveal whether a token was absent or incorrect."""
    absent = client.get(READ_PATH)
    wrong = client.get(READ_PATH, headers=auth("wrong-token"))
    assert absent.status_code == wrong.status_code
    assert absent.json() == wrong.json()


def test_write_is_not_performed_when_unauthorized(client, monkeypatch):
    """Auth must run before the handler, so no write is attempted."""
    called = False

    async def tripwire(session, data):
        nonlocal called
        called = True
        raise AssertionError("handler reached without a valid token")

    monkeypatch.setattr(
        "app.routers.next_actions.create_next_action", tripwire
    )
    resp = client.post(WRITE_PATH, json={"title": "should not be created"})
    assert resp.status_code == 401
    assert called is False


# --- authorized -----------------------------------------------------------

def test_valid_token_allows_read(client):
    resp = client.get(READ_PATH, headers=auth())
    assert resp.status_code == 200
    assert resp.json() == []


def test_valid_token_allows_write(client):
    resp = client.post(WRITE_PATH, json={"title": "authorized write"}, headers=auth())
    assert resp.status_code == 201
    assert resp.json()["title"] == "authorized write"


# --- health ---------------------------------------------------------------

def test_health_needs_no_token(client):
    """k8s probes call /health with no credentials; it must stay open."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_exposes_no_task_data(client):
    assert set(client.get("/health").json().keys()) == {"status"}
