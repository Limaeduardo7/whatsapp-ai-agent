from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from src.config import get_settings


def _constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


async def require_admin_api_key(
    x_admin_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin_api_key_not_configured",
        )

    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()

    candidate = x_admin_api_key or bearer
    if not candidate or not _constant_time_equals(candidate, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_admin_api_key")


def validate_shared_secret(candidate: str | None, expected: str, detail: str) -> None:
    if expected and (not candidate or not _constant_time_equals(candidate, expected)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
