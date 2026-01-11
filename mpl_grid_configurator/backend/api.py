"""Define API endpoints."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from copy import deepcopy
from typing import TYPE_CHECKING, Annotated, TypeVar

from fastapi import Depends, FastAPI, HTTPException

from mpl_grid_configurator.apply import get_drawer, wrap_svg_callback
from mpl_grid_configurator.backend.sessions import (
    FIGURE_SESSIONS,
    Session,
    SessionData,
    create_session_token,
    get_session,
)
from mpl_grid_configurator.backend.types import (  # noqa: TC001
    FullResponse,
    InsertRequest,
    LayoutRequest,
    MergeResponse,
    PathOrientRequest,
    PathRequest,
    PathsRequest,
    ReplaceRequest,
    ResizeRequest,
    RestructureRequest,
    SVGResponse,
    UnmergeRequest,
)
from mpl_grid_configurator.figure_editor import FigureEditor
from mpl_grid_configurator.layout_editor import LayoutEditor
from mpl_grid_configurator.merge import MergeError
from mpl_grid_configurator.merge_editor import merge, unmerge
from mpl_grid_configurator.register import DRAW_FUNCS
from mpl_grid_configurator.render import render_layout, render_svg
from mpl_grid_configurator.traverse import are_nodes_equal

if TYPE_CHECKING:
    from mpl_grid_configurator.types import SubFigure_

R = TypeVar("R")
logger = logging.getLogger()


# Order: functions, health, render, session
class MainApi:
    """Endpoints for creating a session and rendering a figure."""

    @classmethod
    def add_endpoints(cls, app: FastAPI) -> None:
        """Add main endpoints to the FastAPI app."""
        app.get("/functions")(cls.functions)
        app.get("/health")(cls.health)
        app.post("/render")(cls.render)
        app.post("/session")(cls.session)

    @staticmethod
    async def functions() -> list[str]:
        """Get a list of available functions."""
        return list(DRAW_FUNCS.keys())

    @staticmethod
    async def health(session: Annotated[Session, Depends(get_session)]) -> bool:
        """Check if the session is valid."""
        del session  # unused
        return True

    @staticmethod
    async def render(
        layout_request: LayoutRequest, session: Annotated[Session, Depends(get_session)]
    ) -> SVGResponse:
        """Render a layout."""
        layout, figsize = layout_request["layout"], layout_request["figsize"]

        d = session.data
        if d:
            logger.warning("Session already has data, fast-tracking")

            def fast_callback() -> SVGResponse:
                svg = render_svg(d.fig, d.svg_callback)
                return {"token": session.token, "svg": svg}

            if figsize == d.figsize and are_nodes_equal(d.layout, layout):
                return await wrapped(fast_callback, "rendering without changes")

        def callback() -> SVGResponse:
            fig, svg_callback = render_layout(layout, figsize, DRAW_FUNCS)
            fixed_svg = render_svg(fig, svg_callback)
            subfigs: dict[str, list[SubFigure_]] = {}

            session.data = SessionData(
                layout=layout,
                figsize=figsize,
                fig=fig,
                subfigs=subfigs,
                svg_callback=svg_callback,
            )
            return {"token": session.token, "svg": fixed_svg}

        return await wrapped(callback, "rendering")

    @staticmethod
    async def session(layout_request: LayoutRequest) -> SVGResponse:
        """Create a session and render the layout."""
        session_id = str(uuid.uuid4())
        token = create_session_token(session_id)
        session = Session(token=token, data=None)
        FIGURE_SESSIONS[session_id] = session
        return await MainApi.render(layout_request, session)


# Order: delete, merge, replace, resize, restructure, rotate, split, swap
class EditApi:
    """Endpoints for editing the layout."""

    @classmethod
    def add_endpoints(cls, app: FastAPI) -> None:
        """Add edit endpoints to the FastAPI app."""
        app.post("/edit/delete")(cls.delete)
        app.post("/edit/insert")(cls.insert)
        app.post("/edit/merge")(cls.merge)
        app.post("/edit/replace")(cls.replace)
        app.post("/edit/resize")(cls.resize)
        app.post("/edit/restructure")(cls.restructure)
        app.post("/edit/rotate")(cls.rotate)
        app.post("/edit/split")(cls.split)
        app.post("/edit/swap")(cls.swap)
        app.post("/edit/unmerge")(cls.unmerge)

    @staticmethod
    async def delete(
        path_request: PathRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Delete a leaf."""
        d = session.fdata
        path = path_request["path"]

        layout, _, removed = LayoutEditor.delete(deepcopy(d.layout), path)
        if not isinstance(removed, str):
            raise HTTPException(status_code=400, detail="Cannot delete nodes via API")
        d.layout = layout
        d.fig, removed_sf = FigureEditor.delete(d.fig, path)  # mutates fig
        d.subfigs.setdefault(removed, []).append(removed_sf)

        return await wrapped(session.response, "deleting")

    @staticmethod
    async def insert(
        insert_request: InsertRequest,
        session: Annotated[Session, Depends(get_session)],
    ) -> FullResponse:
        """Insert a new leaf."""
        d = session.fdata
        path, value = insert_request["path"], insert_request["value"]
        orient, ratios = insert_request["orient"], insert_request["ratios"]

        d.layout, _, removed = LayoutEditor.insert(d.layout, path, orient, ratios, value)

        drawer = get_drawer(d.subfigs, value)
        d.fig, removed_sf, svg_callback = FigureEditor.insert(
            d.fig, path, orient, ratios, value, drawer
        )

        d.subfigs.setdefault(removed, []).append(removed_sf)
        d.svg_callback = wrap_svg_callback(d.svg_callback, svg_callback)
        return await wrapped(session.response, "inserting")

    @staticmethod
    async def merge(
        paths_request: PathsRequest,
        session: Annotated[Session, Depends(get_session)],
    ) -> MergeResponse:
        """Merge two paths."""
        d = session.fdata
        path1, path2 = paths_request["pathA"], paths_request["pathB"]
        try:
            d.layout, d.fig, inverse, d.svg_callback = merge(
                d.layout, d.fig, path1, path2, d.subfigs, d.svg_callback
            )
        except MergeError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        def merge_callback() -> MergeResponse:
            svg_response = session.response()
            return {
                **svg_response,
                "inverse": inverse,
            }

        return await wrapped(merge_callback, "merging")

    @staticmethod
    async def replace(
        replace_request: ReplaceRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Replace a node."""
        d = session.fdata
        path, value = replace_request["path"], replace_request["value"]

        layout, _, removed = LayoutEditor.replace(deepcopy(d.layout), path, value)
        if not isinstance(removed, str):
            raise HTTPException(status_code=400, detail="Cannot replace nodes via API")

        d.layout = layout

        drawer = get_drawer(d.subfigs, value)
        d.fig, removed_sf, svg_callback = FigureEditor.replace(d.fig, path, value, drawer)

        d.subfigs.setdefault(removed, []).append(removed_sf)
        d.svg_callback = wrap_svg_callback(d.svg_callback, svg_callback)

        return await wrapped(session.response, "replacing")

    @staticmethod
    async def resize(
        resize_request: ResizeRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Resize a node."""
        d = session.fdata
        d.figsize = resize_request["figsize"]
        FigureEditor.resize(d.fig, d.figsize)
        return await wrapped(session.response, "resizing")

    @staticmethod
    async def restructure(
        restructure_request: RestructureRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Resize a node."""
        d = session.fdata
        if restructure_info := restructure_request["rowRestructureInfo"]:
            d.layout, _ = LayoutEditor.restructure(d.layout, *restructure_info)
            FigureEditor.restructure(d.fig, *restructure_info)
        if restructure_info := restructure_request["columnRestructureInfo"]:
            d.layout, _ = LayoutEditor.restructure(d.layout, *restructure_info)
            FigureEditor.restructure(d.fig, *restructure_info)
        return await wrapped(session.response, "restructuring")

    @staticmethod
    async def rotate(
        path_request: PathRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Rotate a parent."""
        path = path_request["path"]
        d = session.fdata
        d.layout, _ = LayoutEditor.rotate(d.layout, path)
        FigureEditor.rotate(d.fig, path)
        return await wrapped(session.response, "rotating")

    @staticmethod
    async def split(
        path_orient_request: PathOrientRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Split a node."""
        path, orient = path_orient_request["path"], path_orient_request["orient"]
        d = session.fdata
        d.layout, _ = LayoutEditor.split(d.layout, path, orient)
        d.fig = FigureEditor.split(d.fig, path, orient)
        return await wrapped(session.response, "splitting")

    @staticmethod
    async def swap(
        paths_request: PathsRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Swap two leaves."""
        path1, path2 = paths_request["pathA"], paths_request["pathB"]
        d = session.fdata
        d.layout, _ = LayoutEditor.swap(d.layout, path1, path2)
        FigureEditor.swap(d.fig, path1, path2)
        return await wrapped(session.response, "swapping")

    @staticmethod
    async def unmerge(
        unmerge_request: UnmergeRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Unmerge two paths."""
        inverse = unmerge_request["inverse"]
        d = session.fdata
        d.layout, d.fig, d.svg_callback = unmerge(
            d.layout, d.fig, inverse, d.subfigs, d.svg_callback
        )
        return await wrapped(session.response, "unmerging")


async def wrapped(func: Callable[..., R] | Callable[[], Awaitable[R]], name: str) -> R:
    """Wrap a function to catch exceptions."""
    try:
        result = func()
        if isinstance(result, Awaitable):
            return await result
    except Exception as e:
        logger.exception("Unexpected error during %s", name)
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return result
