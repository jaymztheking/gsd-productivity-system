from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import next_actions, projects, tags

app = FastAPI(title="GSD API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tags.router, tags=["tags"])
app.include_router(projects.router, tags=["projects"])
app.include_router(next_actions.router, tags=["next-actions"])


@app.get("/health")
async def health():
    return {"status": "ok"}
