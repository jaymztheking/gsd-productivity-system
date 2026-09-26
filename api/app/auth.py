"""Shared-secret authentication for the GSD API.

The token travels in a custom header rather than as a bearer credential
because the primary client is an iOS Shortcut, which can set arbitrary
headers but cannot complete an interactive login. The same header is
attached server-side by the UI's proxy, so the browser never receives
the secret.
"""

import secrets

from fastapi import Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings

API_TOKEN_HEADER = "X-API-Token"


async def require_token(
    x_api_token: str | None = Header(default=None, alias=API_TOKEN_HEADER),
) -> None:
    """Reject the request unless it carries the shared secret.

    Compared with secrets.compare_digest so that a wrong token cannot be
    recovered by timing how long the comparison takes. Missing and wrong
    tokens return the same response, so the error reveals nothing about
    which of the two happened.
    """
    if x_api_token is None or not secrets.compare_digest(
        x_api_token, settings.API_TOKEN
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )


# Paths reachable without a token. /health is called by the k8s probes; the
# rest are the OpenAPI schema and its viewers, which expose endpoint shapes
# but no task data.
PUBLIC_PATHS = frozenset(
    {"/health", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
)


async def token_auth_middleware(request, call_next):
    """Reject unauthenticated requests before the body is read.

    The per-router dependency alone is not quite enough. FastAPI decodes the
    request body before it resolves dependencies, so an unauthenticated
    caller sending malformed JSON receives a 422 that confirms the endpoint
    exists and spends parsing effort on their behalf. Checking here means
    such a request is refused before anything reads its body.

    It also fails safe: a router added later without the dependency is still
    covered, rather than silently shipping an open endpoint.

    OPTIONS is allowed through so CORS preflight still works; a preflight
    carries no data and cannot set custom headers.
    """
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    supplied = request.headers.get(API_TOKEN_HEADER)
    if supplied is None or not secrets.compare_digest(supplied, settings.API_TOKEN):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API token"},
        )
    return await call_next(request)
