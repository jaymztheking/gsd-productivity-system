"""The user's local calendar day.

Routine check-offs belong to a local date, not a UTC one: a tick at 9pm in
Denver is still "today" there even though UTC has already rolled over. All
day arithmetic goes through here so there is one definition of "today".
"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.config import settings


def user_tz() -> ZoneInfo:
    return ZoneInfo(settings.USER_TIMEZONE)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def local_today(now: datetime | None = None) -> date:
    return (now or utc_now()).astimezone(user_tz()).date()


def next_local_midnight(today: date) -> datetime:
    """The UTC instant at which ``today`` ends in the user's timezone.

    Built from the local wall-clock midnight rather than by adding 24 hours,
    so days that are 23 or 25 hours long across DST changes come out right.
    """
    midnight = datetime.combine(today + timedelta(days=1), time(), user_tz())
    return midnight.astimezone(timezone.utc)


async def get_today() -> date:
    """FastAPI dependency, overridden in tests to pin the date."""
    return local_today()
