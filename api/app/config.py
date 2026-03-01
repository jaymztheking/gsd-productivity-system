from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Synchronous URL for Alembic migrations (swaps asyncpg for psycopg2)."""
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")


settings = Settings()
