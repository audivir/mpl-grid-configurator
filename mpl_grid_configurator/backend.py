"""FastAPI backend for mpl-grid-configurator."""

import logging
import os
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import dotenv
import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from mpl_grid_configurator.changes import are_nodes_equal, find_changed_nodes
from mpl_grid_configurator.fasttrack import fast_resize, fast_swap, resize_fig
from mpl_grid_configurator.merge import MergeError, merge_paths
from mpl_grid_configurator.register import DRAW_FUNCS, register
from mpl_grid_configurator.render import draw_empty, render_layout, render_svg
from mpl_grid_configurator.traverse import get_node, get_subfig
from mpl_grid_configurator.types import (
    FullResponse,
    LayoutRequest,
    Session,
    SessionData,
    SVGResponse,
)

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

PARENT = Path(__file__).parent
FRONTEND_DIR = PARENT / "frontend"


SECRET_KEY = os.environ["JWT_SECRET_KEY"]
DEFAULT_EXPIRE_MINUTES = 30
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", DEFAULT_EXPIRE_MINUTES))
ALGORITHM = "HS256"
auth_scheme = HTTPBearer()

FIGURE_SESSIONS: dict[str, Session] = {}


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


async def health_check(session: Annotated[Session, Depends(get_session)]) -> bool:
    """Check if the session is valid."""
    del session  # unused
    return True


async def session_api(layout_request: LayoutRequest) -> SVGResponse:
    """Create a session and render the layout."""
    session_id = str(uuid.uuid4())
    token = create_session_token(session_id)
    session: Session = {"token": token, "data": None}
    FIGURE_SESSIONS[session_id] = session
    return await render_api(layout_request, session)


async def get_functions() -> list[str]:
    """Get a list of available functions."""
    return list(DRAW_FUNCS.keys())


def wrapped_render(
    session: Session, render_callback: Callable[[], tuple[SessionData, str]], name: str
) -> SVGResponse:
    """Wrap the render callback."""
    try:
        data, svg = render_callback()
    except Exception as e:
        logger.exception("Unexpected error during %s", name)
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        session["data"] = data
        return {"token": session["token"], "svg": svg}


def try_fast_track(session: Session, layout_request: LayoutRequest) -> SVGResponse | None:
    """Fast-track if possible.

    Returns:
        A SVGResponse if fast-tracking was possible, None otherwise.
    """
    prev_data = session["data"]
    if prev_data is None:
        return None
    prev_layout, prev_figsize, fig = prev_data["layout"], prev_data["figsize"], prev_data["fig"]
    layout, figsize = layout_request["layout"], layout_request["figsize"]

    def fast_callback() -> tuple[SessionData, str]:
        svg_callback = prev_data["svg_callback"]
        svg = render_svg(fig, svg_callback)
        return {
            "layout": layout,
            "figsize": figsize,
            "fig": fig,
            "svg_callback": svg_callback,
        }, svg

    if figsize == prev_figsize and are_nodes_equal(prev_layout, layout):
        return wrapped_render(session, fast_callback, "rendering without changes")

    changed_nodes = find_changed_nodes(prev_layout, layout)

    if isinstance(prev_layout, str) or isinstance(layout, str) or changed_nodes["full"]:
        # semantic changes need currently always a full render
        return None

    for path in changed_nodes["swap"]:
        node = get_node(prev_layout, path)
        node["children"] = (node["children"][1], node["children"][0])
        subfig = get_subfig(fig, path)  # type: ignore[arg-type]
        fast_swap(subfig)

    for path in changed_nodes["resize"]:
        node = get_node(prev_layout, path)
        new_node = get_node(layout, path)
        node["ratios"] = new_node["ratios"]
        subfig = get_subfig(fig, path)  # type: ignore[arg-type]
        fast_resize(subfig, node["orient"], new_node["ratios"])

    if figsize != prev_figsize:
        fig = resize_fig(fig, figsize)

    # verify
    if not are_nodes_equal(prev_layout, layout):
        raise ValueError("Layouts do not match")

    return wrapped_render(session, fast_callback, "fast-tracking")


async def render_api(
    layout_request: LayoutRequest, session: Annotated[Session, Depends(get_session)]
) -> SVGResponse:
    """Render a layout."""
    layout, figsize = layout_request["layout"], layout_request["figsize"]

    if svg_response := try_fast_track(session, layout_request):
        return svg_response

    def render_callback() -> tuple[SessionData, str]:
        fig, svg_callback = render_layout(layout, figsize, DRAW_FUNCS)
        fixed_svg = render_svg(fig, svg_callback)
        return {
            "layout": layout,
            "figsize": figsize,
            "fig": fig,
            "svg_callback": svg_callback,
        }, fixed_svg

    return wrapped_render(session, render_callback, name="rendering")


async def merge_api(
    layout_request: LayoutRequest,
    path_a: tuple[int, ...],
    path_b: tuple[int, ...],
    session: Annotated[Session, Depends(get_session)],
) -> FullResponse:
    """Merge two paths."""
    from fastapi import HTTPException

    layout = layout_request["layout"]
    if isinstance(layout, str):
        raise HTTPException(status_code=400, detail="Cannot merge a leaf")

    try:
        new_layout = merge_paths(layout, path_a, path_b)
    except MergeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error during merge")
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        svg = await render_api(
            {"layout": new_layout, "figsize": layout_request["figsize"]}, session
        )

    return {"token": session["token"], "layout": new_layout, "svg": svg["svg"]}


def start_app(port: int = 8000) -> None:
    """Start the backend and the frontend."""
    import threading
    import time

    import uvicorn
    from fastapi.middleware.cors import CORSMiddleware
    from servestatic import ServeStaticASGI  # type: ignore[import-untyped]

    backend_app = FastAPI()

    # Enable CORS for React development
    backend_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    backend_app.get("/functions")(get_functions)
    backend_app.get("/health")(health_check)
    backend_app.post("/session")(session_api)
    backend_app.post("/render")(render_api)
    backend_app.post("/merge")(merge_api)

    if draw_empty not in DRAW_FUNCS.values():
        register(draw_empty)

    # start the backend in a thread
    backend = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": backend_app, "port": 8765},
        daemon=True,
    )
    backend.start()

    frontend_app = ServeStaticASGI(None, root=FRONTEND_DIR)

    frontend = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": frontend_app, "port": port},
        daemon=True,
    )
    frontend.start()

    time.sleep(0.5)  # give the servers time to start
    print(  # noqa: T201
        f"To configure your grid, open http://localhost:{port}/index.html in your browser."
    )

    # allow ctrl-c to stop the servers
    while True:
        time.sleep(0.1)

    # wait for the backend thread and the frontend process to finish
    backend.join()
    frontend.join()
