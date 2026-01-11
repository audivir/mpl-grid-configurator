"""Handle session management."""

from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Annotated

import dotenv
import jwt
import msgspec
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

if TYPE_CHECKING:
    from collections.abc import Callable

    from mpl_grid_configurator.backend.types import FullResponse
    from mpl_grid_configurator.types import Layout, SubFigure_

logger = logging.getLogger(__name__)
dotenv.load_dotenv()
DEFAULT_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"


def get_secret_key() -> str:
    """Get the secret key from the environment or generate a random one."""
    if secret_key := os.getenv("JWT_SECRET_KEY"):
        return secret_key
    logger.warning("JWT_SECRET_KEY is not set, generating a random key")
    return secrets.token_urlsafe(32)


SECRET_KEY = get_secret_key()
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", DEFAULT_EXPIRE_MINUTES))
auth_scheme = HTTPBearer()

FIGURE_SESSIONS: dict[str, Session] = {}


class SessionData(msgspec.Struct):
    """Session figure."""

    figsize: tuple[float, float]
    layout: Layout
    fig: SubFigure_
    subfigs: dict[str, list[SubFigure_]]
    svg_callback: Callable[[str], str]


class Session(msgspec.Struct):
    """Session."""

    token: str
    data: SessionData | None

    @property
    def fdata(self) -> SessionData:
        """Forced data."""
        if self.data is None:
            raise ValueError("Can't access data from an empty session")
        return self.data

    def response(self) -> FullResponse:
        """Create a full response from the current session."""
        from mpl_grid_configurator.render import render_svg  # circular import

        d = self.fdata

        return {
            "token": self.token,
            "figsize": d.figsize,
            "layout": d.layout,
            "svg": render_svg(d.fig, d.svg_callback),
        }


def create_session_token(session_id: str) -> str:
    """Create a session token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode({"sub": session_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_session(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(auth_scheme)],
) -> Session:
    """Get the session from the authorization header."""
    if not auth.credentials:
        raise HTTPException(status_code=401, detail="No authorization header")

    try:
        payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        session_id = payload["sub"]
        if session := FIGURE_SESSIONS.get(session_id):
            return session
        raise HTTPException(status_code=401, detail="Session not found")

    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="Expired token") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
