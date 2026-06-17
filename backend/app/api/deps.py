import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db import get_session
from app.models import User
from app.services.tmdb import TMDBClient

bearer_scheme = HTTPBearer(auto_error=False)

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_tmdb(request: Request) -> TMDBClient:
    return request.app.state.tmdb


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    # auto_error=False means a missing/blank Authorization header arrives as
    # None here; surface that as 401 (not HTTPBearer's default 403).
    if credentials is None:
        raise _credentials_error
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _credentials_error

    user = await session.get(User, user_id)
    if user is None:
        raise _credentials_error
    # Reject tokens minted before the user's token_version was last bumped
    # (password reset / log-out-everywhere). Tokens from before this field
    # existed carry no "ver" and default to 0, matching a fresh account.
    if int(payload.get("ver", 0)) != user.token_version:
        raise _credentials_error
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Like get_current_user, but returns None instead of raising when the
    request is unauthenticated or the token is invalid. For endpoints that are
    public but personalize their response for signed-in users."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    user = await session.get(User, user_id)
    if user is not None and int(payload.get("ver", 0)) != user.token_version:
        return None  # stale token → treat as anonymous
    return user
