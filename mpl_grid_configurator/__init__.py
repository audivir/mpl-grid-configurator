"""Start a webapp for adjusting a matplotlib layout."""

from __future__ import annotations

import inspect
import io
import logging
from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import Any, ForwardRef, Literal, TypeAlias, TypeVar, get_origin

import matplotlib.pyplot as plt
from doctyper._typing import eval_type
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure
from typing_extensions import TypedDict, TypeIs

__version__ = "0.2.1"

logger = logging.getLogger(__name__)

PARENT = Path(__file__).parent
FRONTEND_DIR = PARENT / "frontend"

T = TypeVar("T")

AxesDrawFunc: TypeAlias = Callable[[Figure | SubFigure], Axes]
TupleDrawFunc: TypeAlias = Callable[[Figure | SubFigure], tuple[str, Axes]]
StrDrawFunc: TypeAlias = Callable[[], str]
DrawFunc: TypeAlias = AxesDrawFunc | TupleDrawFunc | StrDrawFunc
DrawFuncT = TypeVar("DrawFuncT", bound=DrawFunc)
DRAW_FUNCS: dict[str, DrawFunc] = {}


class MissingBinaryError(RuntimeError):
    """Binary not found."""


class SignatureError(ValueError):
    """Drawing function has an invalid signature."""

    def __init__(self, func: Callable) -> None:
        """Initialize the exception."""
        super().__init__(f"Drawing function {func.__name__} has an invalid signature.")


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
        func = DRAW_FUNCS.get(func_name)
        if func:
            if is_tuple_draw_func(func):
                svg, ax = func(container)
            elif is_str_draw_func(func):
                svg = func()
                ax = draw_empty(container)
            else:  # it's axes draw func
                func(container)
                return

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


def get_return_type(func: Callable[..., T]) -> type[T]:
    """Get the return type of a function."""
    sig = inspect.signature(func)
    return _eval_annotation(sig.return_annotation)


def get_n_params(func: Callable[..., Any]) -> int:
    """Get the number of parameters of a function."""
    sig = inspect.signature(func)
    return len(sig.parameters)


def is_tuple_draw_func(func: DrawFuncT) -> TypeIs[TupleDrawFunc]:  # type: ignore[narrowed-type-not-subtype]
    """Check if a function returns a tuple."""
    return get_origin(get_return_type(func)) is tuple


def is_str_draw_func(func: DrawFuncT) -> TypeIs[StrDrawFunc]:  # type: ignore[narrowed-type-not-subtype]
    """Check if a function returns a string."""
    return get_return_type(func) is str


def register(func: DrawFuncT) -> DrawFuncT:
    """
    Register a drawing function. Can be used as a decorator.

    A drawing function can be:
    * Variant 1: a function that takes a Matplotlib figure, draws on it and returns any of its axes.
    * Variant 2: a function that takes a Matplotlib figure,
        draws on it, returns its SVG as a string and one of its axes.
    * Variant 3: a function that takes no parameters and returns its SVG as a string.

    If the function takes no parameters, Variant 3 is assumed, if the function returns a tuple,
    Variant 2 is assumed, otherwise Variant 1 is assumed.

    ```python
    from mpl_grid_configurator import register
    from matplotlib.figure import Figure, SubFigure
    from matplotlib.axes import Axes

    @register
    def draw_func(container: Figure | SubFigure) -> Axes:
        ...
    ```

    Args:
        func: The drawing function to register.

    Returns:
        The registered function.

    Raises:
        SignatureError: If the function does not have the correct signature.

    """
    if func in DRAW_FUNCS.values():
        logger.warning("Function %s is already registered.", func.__name__)
        return func

    # register with unique name
    name = func.__name__
    count = 1
    while name in DRAW_FUNCS:
        name = f"{func.__name__}_{count}"
        count += 1
    DRAW_FUNCS[name] = func

    return func


def draw_empty(container: Figure | SubFigure) -> Axes:
    """Draw an empty plot."""
    ax = container.subplots()
    ax.axis("off")
    return ax


async def get_functions() -> list[str]:
    """Get a list of available functions."""
    return list(DRAW_FUNCS.keys())


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
    backend_app.post("/render")(render_svg)

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

    # wait for the backend thread and the frontend process to finish
    backend.join()
    frontend.join()
