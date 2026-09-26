"""Regression tests for replacing a next action's tags (TASK-008).

Editing tags on the Engage page sends the full intended tag set, and
update_next_action replaces the stored set with it. Tags present both
before and after the edit were being dropped, so these tests run the real
crud functions against an in-memory SQLite database. Each step uses a
fresh session, as each API request does.

    PYTHONPATH=api pytest api/tests/test_next_action_tags.py -v
"""

import asyncio
import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://unused:unused@localhost:5432/unused"
)

from sqlalchemy.ext.asyncio import (  # noqa: E402
    async_sessionmaker,
    create_async_engine,
)

from app.crud.next_actions import (  # noqa: E402
    create_next_action,
    get_next_action,
    update_next_action,
)
from app.models import Base, Tag  # noqa: E402
from app.models.enums import ActionStatus, TagCategory  # noqa: E402
from app.schemas.next_action import (  # noqa: E402
    NextActionCreate,
    NextActionUpdate,
)


async def _setup():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    tags = {
        "errands": Tag(name="errands", category=TagCategory.context),
        "home": Tag(name="home", category=TagCategory.context),
        "now": Tag(name="now", category=TagCategory.time),
        "easy": Tag(name="easy", category=TagCategory.energy),
    }
    async with sessions() as session:
        session.add_all(tags.values())
        await session.commit()
    return engine, sessions, {name: tag.id for name, tag in tags.items()}


async def _create(sessions, tag_ids):
    async with sessions() as session:
        action = await create_next_action(
            session,
            NextActionCreate(
                title="Buy Anniversary card",
                status=ActionStatus.active,
                tag_ids=tag_ids,
            ),
        )
        return action.id


async def _set_tags(sessions, action_id, tag_ids):
    """Load the action and save a new tag set, as PATCH /next-actions does."""
    async with sessions() as session:
        action = await get_next_action(session, action_id)
        await update_next_action(
            session, action, NextActionUpdate(tag_ids=tag_ids)
        )


async def _stored_tags(sessions, action_id):
    async with sessions() as session:
        action = await get_next_action(session, action_id)
        return {tag.name for tag in action.tags}


def _run(scenario):
    async def main():
        engine, sessions, ids = await _setup()
        try:
            return await scenario(sessions, ids)
        finally:
            await engine.dispose()

    return asyncio.run(main())


def test_kept_tag_survives_when_other_tags_are_added():
    # The reported case: energy=easy only, then add context and time.
    async def scenario(sessions, ids):
        action_id = await _create(sessions, [ids["easy"]])
        await _set_tags(
            sessions, action_id, [ids["errands"], ids["now"], ids["easy"]]
        )
        return await _stored_tags(sessions, action_id)

    assert _run(scenario) == {"errands", "now", "easy"}


def test_resaving_unchanged_tags_keeps_them():
    async def scenario(sessions, ids):
        action_id = await _create(sessions, [ids["errands"], ids["easy"]])
        await _set_tags(sessions, action_id, [ids["errands"], ids["easy"]])
        return await _stored_tags(sessions, action_id)

    assert _run(scenario) == {"errands", "easy"}


def test_deselected_tag_is_removed_and_others_kept():
    async def scenario(sessions, ids):
        action_id = await _create(
            sessions, [ids["errands"], ids["now"], ids["easy"]]
        )
        await _set_tags(sessions, action_id, [ids["errands"], ids["easy"]])
        return await _stored_tags(sessions, action_id)

    assert _run(scenario) == {"errands", "easy"}


def test_empty_tag_list_clears_all_tags():
    async def scenario(sessions, ids):
        action_id = await _create(sessions, [ids["errands"], ids["easy"]])
        await _set_tags(sessions, action_id, [])
        return await _stored_tags(sessions, action_id)

    assert _run(scenario) == set()


def test_omitting_tag_ids_leaves_tags_alone():
    async def scenario(sessions, ids):
        action_id = await _create(sessions, [ids["errands"], ids["easy"]])
        async with sessions() as session:
            action = await get_next_action(session, action_id)
            await update_next_action(
                session, action, NextActionUpdate(title="Renamed")
            )
        return await _stored_tags(sessions, action_id)

    assert _run(scenario) == {"errands", "easy"}


def test_repeated_edits_on_the_same_action():
    async def scenario(sessions, ids):
        action_id = await _create(sessions, [ids["easy"]])
        history = []
        for names in (
            ["errands", "now", "easy"],
            ["home", "now", "easy"],
            ["home", "easy"],
            ["home", "now", "easy"],
        ):
            await _set_tags(sessions, action_id, [ids[n] for n in names])
            history.append(await _stored_tags(sessions, action_id))
        return history

    assert _run(scenario) == [
        {"errands", "now", "easy"},
        {"home", "now", "easy"},
        {"home", "easy"},
        {"home", "now", "easy"},
    ]
