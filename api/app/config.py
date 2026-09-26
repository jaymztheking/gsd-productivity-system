from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    # Shared secret required on every data endpoint. Deliberately has no
    # default: the API should fail to start rather than come up unprotected.
    API_TOKEN: str

    # Comma-separated browser origins allowed to call the API cross-origin.
    # Normally empty — the UI reaches the API through a same-origin proxy
    # (ui/nginx.conf in production, vite.config.ts in dev), so no browser
    # request is cross-origin and no origin needs allowing.
    CORS_ALLOW_ORIGINS: str = ""

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Synchronous URL for Alembic migrations (swaps asyncpg for psycopg2)."""
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    @property
    def cors_allow_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]


settings = Settings()
