"""API tests for the daily routine (TASK-009).

Requests go through the real routers and crud functions against a SQLite
database file, with the clock pinned by monkeypatching app.clock.utc_now so
day boundaries can be crossed on demand.

    PYTHONPATH=api pytest api/tests/test_routine.py -v
"""

import asyncio
import os
from datetime import date, datetime, timezone

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

from app import clock  # noqa: E402
from app.auth import API_TOKEN_HEADER  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
EVERY_DAY = list(range(7))
NO_SUCH_ID = "00000000-0000-0000-0000-000000000000"

# 2026-10-05 is a Monday. 18:00 UTC is noon in Denver (MDT, UTC-6).
MONDAY = date(2026, 10, 5)
MONDAY_NOON = datetime(2026, 10, 5, 18, 0, tzinfo=timezone.utc)


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


class Clock:
    def __init__(self, now: datetime):
        self.now = now


@pytest.fixture
def now(monkeypatch):
    c = Clock(MONDAY_NOON)
    monkeypatch.setattr(clock, "utc_now", lambda: c.now)
    monkeypatch.setattr(settings, "USER_TIMEZONE", "America/Denver")
    return c


@pytest.fixture
def client(tmp_path, now):
    # A file rather than :memory:, and no pooling, so every request's
    # session sees the same database regardless of which loop it runs on.
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'routine.db'}", poolclass=NullPool
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


def _create(client, title, weekdays):
    res = client.post("/routine/items", json={"title": title, "weekdays": weekdays})
    assert res.status_code == 201, res.text
    return res.json()


def _today(client):
    res = client.get("/routine/today")
    assert res.status_code == 200, res.text
    return res.json()


def _tick(client, item_id, completed=True, day=None):
    return client.put(
        f"/routine/items/{item_id}/completion",
        json={"date": day or _today(client)["date"], "completed": completed},
    )


def _state(client):
    return {i["title"]: i["completed"] for i in _today(client)["items"]}


def _titles(items):
    return [i["title"] for i in items]


def _history(client, start, end):
    res = client.get("/routine/history", params={"start": start, "end": end})
    assert res.status_code == 200, res.text
    return res.json()


# --- CRUD ---


def test_create_and_list_items(client):
    item = _create(client, "Stretch", [WED, MON, MON])
    assert item["title"] == "Stretch"
    assert item["weekdays"] == [MON, WED]  # sorted and de-duplicated
    assert item["created_on"] == MONDAY.isoformat()

    listed = client.get("/routine/items").json()
    assert [i["id"] for i in listed] == [item["id"]]


@pytest.mark.parametrize(
    "body",
    [
        {"title": "   ", "weekdays": [MON]},
        {"title": "Read", "weekdays": []},
        {"title": "Read", "weekdays": [7]},
        {"title": "Read", "weekdays": [-1]},
    ],
)
def test_create_rejects_invalid_input(client, body):
    assert client.post("/routine/items", json=body).status_code == 422


def test_rename_and_reschedule(client):
    item = _create(client, "Stretch", [MON])
    res = client.patch(
        f"/routine/items/{item['id']}",
        json={"title": "  Stretch 10 min ", "weekdays": [TUE, THU]},
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Stretch 10 min"
    assert res.json()["weekdays"] == [TUE, THU]

    # A partial update leaves the other field alone
    res = client.patch(f"/routine/items/{item['id']}", json={"title": "Yoga"})
    assert res.json()["weekdays"] == [TUE, THU]


def test_update_rejects_empty_schedule(client):
    item = _create(client, "Stretch", [MON])
    res = client.patch(f"/routine/items/{item['id']}", json={"weekdays": []})
    assert res.status_code == 422


def test_delete_removes_from_lists_and_blocks_edits(client):
    item = _create(client, "Stretch", EVERY_DAY)
    assert client.delete(f"/routine/items/{item['id']}").status_code == 204

    assert client.get("/routine/items").json() == []
    assert _today(client)["items"] == []
    res = client.patch(f"/routine/items/{item['id']}", json={"title": "x"})
    assert res.status_code == 404
    assert client.delete(f"/routine/items/{item['id']}").status_code == 404


def test_unknown_item_is_404(client):
    assert client.patch(f"/routine/items/{NO_SUCH_ID}", json={}).status_code == 404
    assert _tick(client, NO_SUCH_ID).status_code == 404


# --- Ordering ---


def test_new_items_append_and_full_reorder(client):
    a = _create(client, "A", [MON])
    b = _create(client, "B", [MON])
    c = _create(client, "C", [MON])
    assert _titles(client.get("/routine/items").json()) == ["A", "B", "C"]

    res = client.put(
        "/routine/items/order", json={"ordered_ids": [c["id"], a["id"], b["id"]]}
    )
    assert res.status_code == 204
    assert _titles(client.get("/routine/items").json()) == ["C", "A", "B"]
    assert _titles(_today(client)["items"]) == ["C", "A", "B"]


def test_reordering_one_weekday_keeps_other_items_in_place(client):
    a = _create(client, "A-mon", [MON])
    _create(client, "B-tue", [TUE])
    c = _create(client, "C-mon", [MON])
    _create(client, "D-tue", [TUE])

    # The Monday view swaps its two items; Tuesday's stay where they were
    client.put("/routine/items/order", json={"ordered_ids": [c["id"], a["id"]]})
    assert _titles(client.get("/routine/items").json()) == [
        "C-mon",
        "B-tue",
        "A-mon",
        "D-tue",
    ]


def test_reorder_rejects_unknown_or_duplicate_ids(client):
    a = _create(client, "A", [MON])
    for ids in ([a["id"], NO_SUCH_ID], [a["id"], a["id"]]):
        res = client.put("/routine/items/order", json={"ordered_ids": ids})
        assert res.status_code == 422


# --- Weekday scheduling ---


def test_today_shows_only_items_scheduled_for_this_weekday(client, now):
    _create(client, "Every day", EVERY_DAY)
    _create(client, "Monday only", [MON])
    _create(client, "Tuesday only", [TUE])

    today = _today(client)
    assert today["date"] == MONDAY.isoformat()
    assert today["weekday"] == MON
    assert _titles(today["items"]) == ["Every day", "Monday only"]

    now.now = utc(2026, 10, 6, 18, 0)  # Tuesday
    assert _titles(_today(client)["items"]) == ["Every day", "Tuesday only"]


def test_all_items_listed_regardless_of_weekday(client):
    _create(client, "Monday only", [MON])
    _create(client, "Sunday only", [SUN])
    assert len(client.get("/routine/items").json()) == 2


# --- Ticking ---


def test_tick_and_untick_repeatedly(client):
    item = _create(client, "Stretch", [MON])
    assert _state(client) == {"Stretch": False}

    for completed in (True, True, False, False, True):
        assert _tick(client, item["id"], completed).status_code == 204
        assert _state(client) == {"Stretch": completed}


def test_cannot_tick_an_item_not_scheduled_today(client):
    item = _create(client, "Tuesday only", [TUE])
    assert _tick(client, item["id"], True).status_code == 422
    # Unticking is always allowed, e.g. after rescheduling a ticked item
    assert _tick(client, item["id"], False).status_code == 204


def test_ticking_a_day_other_than_today_is_409(client):
    item = _create(client, "Stretch", EVERY_DAY)
    assert _tick(client, item["id"], True, day="2026-10-04").status_code == 409
    assert _tick(client, item["id"], True, day="2026-10-06").status_code == 409
    assert _state(client) == {"Stretch": False}


def test_editing_the_list_keeps_todays_ticks(client):
    a = _create(client, "A", [MON])
    b = _create(client, "B", [MON, TUE])
    c = _create(client, "C", [MON])
    _tick(client, a["id"])
    _tick(client, b["id"])

    _create(client, "D", [MON])
    client.patch(f"/routine/items/{a['id']}", json={"title": "A renamed"})
    client.patch(f"/routine/items/{b['id']}", json={"weekdays": [MON, WED]})
    client.put(
        "/routine/items/order",
        json={"ordered_ids": [c["id"], b["id"], a["id"]]},
    )
    client.delete(f"/routine/items/{c['id']}")

    assert _state(client) == {"B": True, "A renamed": True, "D": False}


# --- Daily reset ---


def test_new_day_starts_unticked_without_any_action(client, now):
    item = _create(client, "Stretch", EVERY_DAY)
    _tick(client, item["id"])
    assert _state(client) == {"Stretch": True}

    now.now = utc(2026, 10, 6, 14, 0)  # next morning
    assert _state(client) == {"Stretch": False}

    now.now = utc(2026, 10, 13, 14, 0)  # a week later
    assert _state(client) == {"Stretch": False}


def test_reset_follows_denver_midnight_not_utc(client, now):
    item = _create(client, "Stretch", EVERY_DAY)

    # 03:30 UTC on Tuesday is still 21:30 Monday evening in Denver
    now.now = utc(2026, 10, 6, 3, 30)
    today = _today(client)
    assert today["date"] == MONDAY.isoformat()
    assert datetime.fromisoformat(today["next_reset_at"]) == utc(2026, 10, 6, 6, 0)
    _tick(client, item["id"])
    assert _state(client) == {"Stretch": True}

    # 05:59 UTC = 23:59 Denver: still Monday, still ticked
    now.now = utc(2026, 10, 6, 5, 59)
    assert _state(client) == {"Stretch": True}

    # 06:00 UTC = midnight Denver: Tuesday, fresh list
    now.now = utc(2026, 10, 6, 6, 0)
    assert _today(client)["date"] == "2026-10-06"
    assert _state(client) == {"Stretch": False}

    # The tick was filed under Denver's Monday, not UTC's Tuesday
    history = _history(client, "2026-10-05", "2026-10-06")
    assert history["items"][0]["completed_dates"] == ["2026-10-05"]


def test_stale_page_across_midnight_gets_409(client, now):
    item = _create(client, "Stretch", EVERY_DAY)
    shown = _today(client)["date"]  # page loaded on Monday

    now.now = utc(2026, 10, 6, 6, 30)  # Tuesday 00:30 in Denver
    assert _tick(client, item["id"], True, day=shown).status_code == 409


def test_next_reset_handles_dst_change(now):
    # US DST ends at 02:00 on 2026-11-01. Midnight starting Nov 1 is still
    # MDT (UTC-6); midnight starting Nov 2 is MST (UTC-7).
    assert clock.next_local_midnight(date(2026, 10, 31)) == utc(2026, 11, 1, 6, 0)
    assert clock.next_local_midnight(date(2026, 11, 1)) == utc(2026, 11, 2, 7, 0)


# --- History ---


def test_history_returns_completed_dates_schedule_and_created_on(client, now):
    a = _create(client, "Stretch", [MON, TUE, WED])
    _tick(client, a["id"])  # Monday
    now.now = utc(2026, 10, 7, 18, 0)  # Wednesday
    b = _create(client, "Read", [WED])
    _tick(client, a["id"])
    _tick(client, b["id"])

    body = _history(client, "2026-10-01", "2026-10-07")
    assert (body["start"], body["end"]) == ("2026-10-01", "2026-10-07")
    by_title = {i["title"]: i for i in body["items"]}
    assert by_title["Stretch"]["completed_dates"] == ["2026-10-05", "2026-10-07"]
    assert by_title["Stretch"]["weekdays"] == [MON, TUE, WED]
    assert by_title["Stretch"]["created_on"] == "2026-10-05"
    assert by_title["Stretch"]["deleted_at"] is None
    assert by_title["Read"]["completed_dates"] == ["2026-10-07"]
    assert by_title["Read"]["created_on"] == "2026-10-07"

    # Completions outside the range are left out
    body = _history(client, "2026-10-06", "2026-10-07")
    by_title = {i["title"]: i for i in body["items"]}
    assert by_title["Stretch"]["completed_dates"] == ["2026-10-07"]


def test_history_defaults_to_last_30_days(client):
    body = client.get("/routine/history").json()
    assert body["end"] == MONDAY.isoformat()
    assert body["start"] == "2026-09-06"


def test_history_excludes_items_created_after_the_range(client, now):
    now.now = utc(2026, 10, 7, 18, 0)
    _create(client, "New", [WED])
    assert _history(client, "2026-10-01", "2026-10-05")["items"] == []


def test_deleted_item_keeps_its_history(client, now):
    gone = _create(client, "Gone", [MON, TUE])
    never = _create(client, "Never done", [MON])
    _tick(client, gone["id"])
    now.now = utc(2026, 10, 6, 18, 0)
    client.delete(f"/routine/items/{gone['id']}")
    client.delete(f"/routine/items/{never['id']}")

    body = _history(client, "2026-10-01", "2026-10-06")
    assert _titles(body["items"]) == ["Gone"]
    assert body["items"][0]["completed_dates"] == ["2026-10-05"]
    assert body["items"][0]["deleted_at"] is not None


@pytest.mark.parametrize(
    "params",
    [
        {"start": "2026-10-06", "end": "2026-10-05"},
        {"start": "2025-01-01", "end": "2026-10-05"},
    ],
)
def test_history_rejects_bad_ranges(client, params):
    assert client.get("/routine/history", params=params).status_code == 422


# --- Auth ---


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/routine/today"),
        ("GET", "/routine/items"),
        ("POST", "/routine/items"),
        ("PUT", "/routine/items/order"),
        ("PATCH", f"/routine/items/{NO_SUCH_ID}"),
        ("DELETE", f"/routine/items/{NO_SUCH_ID}"),
        ("PUT", f"/routine/items/{NO_SUCH_ID}/completion"),
        ("GET", "/routine/history"),
    ],
)
def test_routine_endpoints_require_token(client, method, path):
    for token in ("", "wrong"):
        res = client.request(method, path, headers={API_TOKEN_HEADER: token}, json={})
        assert res.status_code == 401
