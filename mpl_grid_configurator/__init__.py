"""Start a webapp for adjusting a matplotlib layout."""

from __future__ import annotations

import inspect
import io
import logging
from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import Any, ForwardRef, Literal, TypeAlias

import matplotlib.pyplot as plt
from doctyper._typing import eval_type
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure
from typing_extensions import TypedDict

__version__ = "0.2.0"

logger = logging.getLogger(__name__)

PARENT = Path(__file__).parent
FRONTEND_DIR = PARENT / "frontend"

DRAWING_FUNC: TypeAlias = (
    Callable[[Figure | SubFigure], Axes]
    | Callable[[Figure | SubFigure], str]
    | Callable[[Figure | SubFigure], tuple[str, Axes]]
)
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
    svg_mapping: MutableMapping[str, str],
) -> None:
    """Render a node recursively."""
    from mpl_grid_configurator.unnested_skunk import connect

    if isinstance(layout, str):
        func_name: str = layout
        func = DRAWING_FUNCS.get(func_name)
        if func:
            return_type = get_return_type(func)
            if return_type == "axes":
                func(container)
                return

            if return_type == "tuple":
                svg, ax = func(container)
            else:
                svg = func(container)
                ax = draw_empty(container)

            connect(ax, func_name)
            svg_mapping[func_name] = svg

    else:
        node: LayoutNode = layout
        left_up_subfig, right_down_subfig = typed_subfigures(
            container,
            node["orient"],
            node["ratios"],
        )
        left_up, right_down = node["children"]
        render_recursive(left_up_subfig, left_up, svg_mapping)
        render_recursive(right_down_subfig, right_down, svg_mapping)


def render_layout(layout_data: LayoutData) -> tuple[Figure, Callable[[str], str]]:
    """Render a layout."""
    from mpl_grid_configurator.unnested_skunk import insert

    layout = layout_data["layout"]
    width, height = layout_data["figsize"]

    # Use layout="constrained" to ensure subplots respect the ratio boundaries
    fig = Figure(figsize=(width, height), layout="constrained")

    svg_mapping: dict[str, str] = {}
    render_recursive(fig, layout, svg_mapping)

    if not svg_mapping:
        return fig, lambda svg: svg

    def svg_callback(final_svg: str) -> str:
        return insert(svg_mapping, final_svg)

    return fig, svg_callback


def _eval_annotation(annotation: type | str) -> type:
    """Evaluate a type annotation."""
    if isinstance(annotation, str):
        return eval_type(ForwardRef(annotation), globals(), locals())
    return annotation


def verify_single_fig_param(func: Callable) -> Callable[[Figure | SubFigure], Any]:
    """Verify that a function accepts a single parameter of type Figure | SubFigure."""
    sig = inspect.signature(func)
    if len(sig.parameters) != 1:
        raise SignatureError(sig.parameters, Figure | SubFigure)
    annotation = next(iter(sig.parameters.values())).annotation
    param_type = _eval_annotation(annotation)
    if param_type != Figure | SubFigure:
        raise SignatureError(param_type, Figure | SubFigure)
    return func


def get_return_type(func: Callable[[Figure | SubFigure], Any]) -> Literal["str", "axes", "tuple"]:
    """Get the return type of a function."""
    sig = inspect.signature(func)
    return_type = _eval_annotation(sig.return_annotation)
    if return_type == str:  # noqa: E721
        return "str"
    if return_type == Axes:
        return "axes"
    if return_type == tuple[str, Axes]:
        return "tuple"
    raise SignatureError(return_type, (str, Axes, tuple[str, Axes]))


def register(func: Callable) -> None:
    """Register a drawing function."""
    if func in DRAWING_FUNCS.values():
        logger.warning("Function %s is already registered.", func.__name__)
        return

    # verify signature
    func = verify_single_fig_param(func)
    get_return_type(func)

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
        fig, svg_callback = render_layout(layout_data)
        buf = io.BytesIO()
        fig.savefig(buf, format="svg")
        plt.close(fig)
        final_svg = buf.getvalue().decode("utf-8")
        fixed_svg = svg_callback(final_svg)
    except Exception as e:
        logger.exception("Error during rendering")
        raise HTTPException(status_code=400, detail=str(e)) from e
    else:
        return {"svg": fixed_svg}


def start_app(port: int = 8000) -> None:
    """Start the backend and the frontend."""
    import threading
    import time

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

    time.sleep(0.5)  # give the servers time to start
    print(  # noqa: T201
        f"To configure your grid, open http://localhost:{port}/index.html in your browser."
    )

    # wait for the backend thread and the frontend process to finish
    backend.join()
    frontend.join()
