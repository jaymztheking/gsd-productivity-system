from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import require_token, token_auth_middleware
from app.config import settings
from app.routers import next_actions, projects, tags

app = FastAPI(title="GSD API", version="0.1.0")

# Added before CORSMiddleware so that CORS ends up outermost: Starlette runs
# middleware in reverse registration order, and preflight must be handled
# before anything else.
app.middleware("http")(token_auth_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The token guard is attached per router rather than per route: projects
# alone exposes 12 endpoints, and adding it 17 times invites missing one.
auth = [Depends(require_token)]

app.include_router(tags.router, tags=["tags"], dependencies=auth)
app.include_router(projects.router, tags=["projects"], dependencies=auth)
app.include_router(next_actions.router, tags=["next-actions"], dependencies=auth)


@app.get("/health")
async def health():
    """Unauthenticated on purpose — the k8s probes call it. Exposes no data."""
    return {"status": "ok"}
