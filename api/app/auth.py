"""Shared-secret authentication for the GSD API.

The token travels in a custom header rather than as a bearer credential
because the primary client is an iOS Shortcut, which can set arbitrary
headers but cannot complete an interactive login. The same header is
attached server-side by the UI's proxy, so the browser never receives
the secret.
"""

import secrets

from fastapi import Header, HTTPException, status

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
