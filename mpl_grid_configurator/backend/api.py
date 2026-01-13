"""Define API endpoints."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from copy import deepcopy
from typing import Annotated, ParamSpec, TypeVar

from fastapi import Depends, FastAPI, HTTPException

from mpl_grid_configurator.apply import get_drawer, wrap_svg_callback
from mpl_grid_configurator.backend.profiler import SessionProfiler
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
    MergeResponse,
    PathOrientRequest,
    PathRequest,
    PathsRequest,
    ReplaceRequest,
    ResizeRequest,
    RestructureRequest,
    UnmergeRequest,
)
from mpl_grid_configurator.figure_editor import FigureEditor
from mpl_grid_configurator.layout_editor import LayoutEditor
from mpl_grid_configurator.merge import MergeError
from mpl_grid_configurator.merge_editor import merge, unmerge
from mpl_grid_configurator.register import DRAW_FUNCS
from mpl_grid_configurator.render import render_layout
from mpl_grid_configurator.traverse import are_nodes_equal
from mpl_grid_configurator.types import Config  # noqa: TC001

P = ParamSpec("P")
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
        config_request: Config, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Render a layout."""
        prof = SessionProfiler("render")

        layout, figsize = config_request["layout"], config_request["figsize"]

        d = session.data
        if d:
            logger.info("Session already has data, fast-tracking")

            if figsize == d.figsize and are_nodes_equal(d.layout, layout):
                return await wrapped(session.response, "rendering without changes", prof)

        def callback() -> FullResponse:
            with prof.track("render_layout"):
                fig, svg_callback = render_layout(layout, figsize, DRAW_FUNCS)

            session.data = SessionData(
                layout=layout,
                figsize=figsize,
                fig=fig,
                subfigs={},
                svg_callback=svg_callback,
            )

            with prof.track("render_svg"):
                response = session.response()

            prof.finalize()
            return response

        return await wrapped(callback, "rendering", prof=None)

    @staticmethod
    async def session(config_request: Config) -> FullResponse:
        """Create a session and render the layout."""
        session_id = str(uuid.uuid4())
        token = create_session_token(session_id)
        session = Session(token=token, data=None)
        FIGURE_SESSIONS[session_id] = session
        return await MainApi.render(config_request, session)


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
        prof = SessionProfiler("delete")

        d = session.fdata
        path = path_request["path"]

        with prof.track("edit_layout"):
            layout, _, removed = LayoutEditor.delete(deepcopy(d.layout), path)
            if not isinstance(removed, str):
                raise HTTPException(status_code=400, detail="Cannot delete nodes via API")
            d.layout = layout

        with prof.track("edit_figure"):
            d.fig, removed_sf = FigureEditor.delete(d.fig, path)  # mutates fig
            d.subfigs.setdefault(removed, []).append(removed_sf)

        return await wrapped(session.response, "deleting", prof)

    @staticmethod
    async def insert(
        insert_request: InsertRequest,
        session: Annotated[Session, Depends(get_session)],
    ) -> FullResponse:
        """Insert a new leaf."""
        prof = SessionProfiler("insert")

        d = session.fdata
        path, value = insert_request["path"], insert_request["value"]
        orient, ratios = insert_request["orient"], insert_request["ratios"]

        with prof.track("edit_layout"):
            d.layout, _, removed = LayoutEditor.insert(d.layout, path, orient, ratios, value)

        with prof.track("edit_figure"):
            drawer = get_drawer(d.subfigs, value)
            d.fig, removed_sf, svg_callback = FigureEditor.insert(
                d.fig, path, orient, ratios, value, drawer
            )
            d.subfigs.setdefault(removed, []).append(removed_sf)
            d.svg_callback = wrap_svg_callback(d.svg_callback, svg_callback)

        return await wrapped(session.response, "inserting", prof)

    @staticmethod
    async def merge(
        paths_request: PathsRequest,
        session: Annotated[Session, Depends(get_session)],
    ) -> MergeResponse:
        """Merge two paths."""
        prof = SessionProfiler("merge")

        d = session.fdata
        path1, path2 = paths_request["pathA"], paths_request["pathB"]

        with prof.track("merge"):
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

        return await wrapped(merge_callback, "merging", prof)

    @staticmethod
    async def replace(
        replace_request: ReplaceRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Replace a node."""
        prof = SessionProfiler("replace")

        d = session.fdata
        path, value = replace_request["path"], replace_request["value"]

        with prof.track("replace_layout"):
            layout, _, removed = LayoutEditor.replace(deepcopy(d.layout), path, value)
            if not isinstance(removed, str):
                raise HTTPException(status_code=400, detail="Cannot replace nodes via API")
            d.layout = layout

        with prof.track("replace_figure"):
            drawer = get_drawer(d.subfigs, value)
            d.fig, removed_sf, svg_callback = FigureEditor.replace(d.fig, path, value, drawer)
            d.subfigs.setdefault(removed, []).append(removed_sf)
            d.svg_callback = wrap_svg_callback(d.svg_callback, svg_callback)

        return await wrapped(session.response, "replacing", prof)

    @staticmethod
    async def resize(
        resize_request: ResizeRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Resize a node."""
        prof = SessionProfiler("resize")

        d = session.fdata
        d.figsize = resize_request["figsize"]

        with prof.track("edit_figure"):
            FigureEditor.resize(d.fig, d.figsize)

        return await wrapped(session.response, "resizing", prof)

    @staticmethod
    async def restructure(
        restructure_request: RestructureRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Resize a node."""
        prof = SessionProfiler("restructure")

        d = session.fdata

        if restructure_info := restructure_request["rowRestructureInfo"]:
            with prof.track("edit_layout_row"):
                d.layout, _ = LayoutEditor.restructure(d.layout, *restructure_info)
            with prof.track("edit_figure_row"):
                FigureEditor.restructure(d.fig, *restructure_info)
        if restructure_info := restructure_request["columnRestructureInfo"]:
            with prof.track("edit_layout_column"):
                d.layout, _ = LayoutEditor.restructure(d.layout, *restructure_info)
            with prof.track("edit_figure_column"):
                FigureEditor.restructure(d.fig, *restructure_info)

        return await wrapped(session.response, "restructuring", prof)

    @staticmethod
    async def rotate(
        path_request: PathRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Rotate a parent."""
        prof = SessionProfiler("rotate")

        path = path_request["path"]
        d = session.fdata

        with prof.track("edit_layout"):
            d.layout, _ = LayoutEditor.rotate(d.layout, path)

        with prof.track("edit_figure"):
            FigureEditor.rotate(d.fig, path)

        return await wrapped(session.response, "rotating", prof)

    @staticmethod
    async def split(
        path_orient_request: PathOrientRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Split a node."""
        prof = SessionProfiler("split")

        path, orient = path_orient_request["path"], path_orient_request["orient"]
        d = session.fdata

        with prof.track("edit_layout"):
            d.layout, _ = LayoutEditor.split(d.layout, path, orient)

        with prof.track("edit_figure"):
            d.fig = FigureEditor.split(d.fig, path, orient)

        return await wrapped(session.response, "splitting", prof)

    @staticmethod
    async def swap(
        paths_request: PathsRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Swap two leaves."""
        prof = SessionProfiler("swap")

        path1, path2 = paths_request["pathA"], paths_request["pathB"]
        d = session.fdata

        with prof.track("edit_layout"):
            d.layout, _ = LayoutEditor.swap(d.layout, path1, path2)

        with prof.track("edit_figure"):
            FigureEditor.swap(d.fig, path1, path2)

        return await wrapped(session.response, "swapping", prof)

    @staticmethod
    async def unmerge(
        unmerge_request: UnmergeRequest, session: Annotated[Session, Depends(get_session)]
    ) -> FullResponse:
        """Unmerge two paths."""
        prof = SessionProfiler("unmerge")

        inverse = unmerge_request["inverse"]
        d = session.fdata

        with prof.track("unmerge"):
            d.layout, d.fig, d.svg_callback = unmerge(
                d.layout, d.fig, inverse, d.subfigs, d.svg_callback
            )

        return await wrapped(session.response, "unmerging", prof)


async def wrapped(
    func: Callable[..., R] | Callable[[], Awaitable[R]],
    name: str,
    prof: SessionProfiler | None,
) -> R:
    """Wrap a function to catch exceptions."""

    async def run_func() -> R:
        result = func()
        if isinstance(result, Awaitable):
            return await result
        return result

    try:
        if prof:
            with prof.track("render_svg"):
                result = await run_func()
            prof.finalize()
        else:
            result = await run_func()

    except Exception as e:
        logger.exception("Unexpected error during %s", name)
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return result
