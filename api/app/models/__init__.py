from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so Alembic can discover them
from app.models.tag import Tag  # noqa: E402, F401
from app.models.project import Project  # noqa: E402, F401
from app.models.next_action import NextAction, next_action_tags  # noqa: E402, F401
