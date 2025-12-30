"""Start a webapp for adjusting a matplotlib layout."""

from __future__ import annotations

import inspect
import io
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, ForwardRef, Literal, TypeAlias

import matplotlib.pyplot as plt
from doctyper._typing import eval_type
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure
from typing_extensions import TypedDict

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

PARENT = Path(__file__).parent
FRONTEND_DIR = PARENT / "frontend"

DRAWING_FUNC: TypeAlias = Callable[[Figure | SubFigure], Axes]
DRAWING_FUNCS: dict[str, DRAWING_FUNC] = {}


class MissingBinaryError(RuntimeError):
    """Binary not found."""


class SignatureError(ValueError):
    """Drawing function has an invalid signature."""

    def __init__(self, got: Any, accepted: Any) -> None:
        """Initialize the exception."""
        super().__init__(
            f"Function must accept a single parameter of type {accepted}, got: {got}",
        )


class LayoutNode(TypedDict):
    """Node for the layout."""

    orient: Literal["row", "column"]
    children: tuple[LayoutNode | str, LayoutNode | str]
    ratios: tuple[float, float]


Layout: TypeAlias = LayoutNode | str


class LayoutData(TypedDict):
    """Layout and figure size."""

    layout: Layout
    figsize: tuple[float, float]


class SVGResponse(TypedDict):
    """SVG response."""

    svg: str


def typed_subfigures(
    container: Figure | SubFigure,
    orient: Literal["row", "column"],
    ratios: tuple[float, float],
) -> tuple[SubFigure, SubFigure]:
    """Create subfigures with the correct type."""
    is_row = orient == "row"
    left_up_subfig, right_down_subfig = container.subfigures(
        nrows=1 if is_row else 2,
        ncols=2 if is_row else 1,
        width_ratios=ratios if is_row else None,
        height_ratios=ratios if not is_row else None,
    )
    return left_up_subfig, right_down_subfig


def render_recursive(
    container: Figure | SubFigure,
    layout: Layout,
) -> None:
    """Render a node recursively."""
    if isinstance(layout, str):
        func = DRAWING_FUNCS.get(layout)
        if func:
            func(container)
    else:
        node: LayoutNode = layout
        left_up_subfig, right_down_subfig = typed_subfigures(
            container,
            node["orient"],
            node["ratios"],
        )
        left_up, right_down = node["children"]
        render_recursive(left_up_subfig, left_up)
        render_recursive(right_down_subfig, right_down)


def render_layout(layout_data: LayoutData) -> Figure:
    """Render a layout."""
    layout = layout_data["layout"]
    width, height = layout_data["figsize"]

    # Use layout="constrained" to ensure subplots respect the ratio boundaries
    fig = Figure(figsize=(width, height), layout="constrained")
    render_recursive(fig, layout)
    return fig


def _eval_annotation(annotation: type | str) -> type:
    """Evaluate a type annotation."""
    if isinstance(annotation, str):
        return eval_type(ForwardRef(annotation), globals(), locals())
    return annotation


def register(func: DRAWING_FUNC) -> None:
    """Register a drawing function."""
    # verify signature
    sig = inspect.signature(func)

    if len(sig.parameters) == 1:
        annotation = next(iter(sig.parameters.values())).annotation
        param_type = _eval_annotation(annotation)
        if param_type != Figure | SubFigure:
            raise SignatureError(param_type, Figure | SubFigure)
    else:
        raise SignatureError(sig.parameters, Figure | SubFigure)
    # verify return type
    return_type = _eval_annotation(sig.return_annotation)
    if return_type != Axes:
        raise SignatureError(return_type, Axes)

    if func in DRAWING_FUNCS.values():
        logger.warning("Function %s is already registered.", func.__name__)
        return

    # register with unique name
    name = func.__name__
    count = 1
    while name in DRAWING_FUNCS:
        name = f"{func.__name__}_{count}"
        count += 1
    DRAWING_FUNCS[name] = func


def draw_empty(container: Figure | SubFigure) -> Axes:
    """Draw an empty plot."""
    ax = container.subplots()
    ax.axis("off")
    return ax


async def get_functions() -> list[str]:
    """Get a list of available functions."""
    return list(DRAWING_FUNCS.keys())


async def render_svg(layout_data: LayoutData) -> SVGResponse:
    """Render a layout."""
    from fastapi import HTTPException

    try:
        fig = render_layout(layout_data)
        buf = io.BytesIO()
        fig.savefig(buf, format="svg")
        plt.close(fig)
        return {"svg": buf.getvalue().decode("utf-8")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def start_app(port: int = 8000) -> None:
    """Start the backend and the frontend."""
    import threading
    import webbrowser

    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from servestatic import ServeStaticASGI

    backend_app = FastAPI()

    # Enable CORS for React development
    backend_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    backend_app.get("/functions")(get_functions)
    backend_app.post("/render")(render_svg)

    if draw_empty not in DRAWING_FUNCS.values():
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

    webbrowser.open(f"http://localhost:{port}/index.html")

    # wait for the backend thread and the frontend process to finish
    backend.join()
    frontend.join()
