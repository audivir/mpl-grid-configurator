"""Functions to parse function signatures."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator, MutableMapping
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    ForwardRef,
    Literal,
    NamedTuple,
    TypeAlias,
    TypeVar,
    get_origin,
)

from doctyper._typing import eval_type
from matplotlib.figure import Figure, SubFigure  # noqa: TC002
from typing_extensions import TypedDict, TypeIs

if TYPE_CHECKING:
    from datetime import datetime

    from matplotlib.axes import Axes
    from matplotlib.gridspec import SubplotSpec

    class SubplotSpec_(SubplotSpec):  # noqa: N801
        """Custom SubplotSpec."""

        _num2: int

    class Figure_(Figure):  # noqa: N801
        """Custom Figure."""

        subfigs: list[SubFigure_]  # type: ignore[assignment]

    class SubFigure_(SubFigure):  # noqa: N801
        """Custom SubFigure."""

        _parent: Figure_ | SubFigure_
        _subplotspec: SubplotSpec_
        subfigs: list[SubFigure_]  # type: ignore[assignment]


T = TypeVar("T")


AxesDrawFunc: TypeAlias = "Callable[[Figure | SubFigure], Axes]"
TupleDrawFunc: TypeAlias = "Callable[[Figure | SubFigure], tuple[str, Axes]]"
StrDrawFunc: TypeAlias = Callable[[], str]
DrawFunc: TypeAlias = "AxesDrawFunc | TupleDrawFunc | StrDrawFunc"
DrawFuncT = TypeVar("DrawFuncT", bound=DrawFunc)

Orientation: TypeAlias = Literal["row", "column"]


class LayoutNode(TypedDict):
    """Node for the JSON layout."""

    orient: Orientation
    children: tuple[LayoutNode | str, LayoutNode | str]
    ratios: tuple[float, float]


LayoutT = TypeVar("LayoutT", LayoutNode, str)
Layout: TypeAlias = LayoutNode | str

LayoutNode({"orient": "row", "children": ("a", "b"), "ratios": (1, 1)})


class LayoutRequest(TypedDict):
    """Layout and figure size."""

    layout: Layout
    figsize: tuple[float, float]


class TokenResponse(TypedDict):
    """Token response."""

    token: str


class SVGResponse(TokenResponse):
    """SVG response."""

    svg: str


class LayoutResponse(TokenResponse):
    """Layout response."""

    layout: Layout


class FullResponse(TokenResponse):
    """Response containing both layout and svg."""

    svg: str
    layout: Layout


class SessionData(TypedDict):
    """Session figure."""

    figsize: tuple[float, float]
    layout: Layout
    fig: Figure
    svg_callback: Callable[[str], str]


class Session(TypedDict):
    """Session."""

    token: str
    data: SessionData | None


class Payload(TypedDict):
    """JWT payload."""

    sub: str
    exp: datetime


@dataclass
class Edge:
    """Edge of a rectangle (min, max)."""

    min: float
    max: float

    def __iter__(self) -> Iterator[float]:
        yield self.min
        yield self.max

    @property
    def size(self) -> float:
        """Size of the edge."""
        return self.max - self.min


class BoundingBox(NamedTuple):
    """Bounding box of a rectangle (x_min, x_max, y_min, y_max)."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float


BoundingBoxMappingT = TypeVar("BoundingBoxMappingT", bound=MutableMapping[str, BoundingBox])


class Touch(NamedTuple):
    """Touching edges (orient, full)."""

    orient: Orientation
    touch_ratio: float


def is_tuple_draw_func(func: DrawFuncT) -> TypeIs[TupleDrawFunc]:  # type: ignore[narrowed-type-not-subtype]
    """Check if a function returns a tuple."""
    return get_origin(get_return_type(func)) is tuple


def is_str_draw_func(func: DrawFuncT) -> TypeIs[StrDrawFunc]:  # type: ignore[narrowed-type-not-subtype]
    """Check if a function takes no parameters."""
    return get_n_params(func) == 0


def get_return_type(func: Callable[..., T]) -> type[T]:
    """Get the return type of a function."""
    # For parsing type annotations with __future__ import annotations
    # we need to import matplotlib types here
    from matplotlib.axes import Axes  # noqa: F401
    from matplotlib.figure import Figure, SubFigure  # noqa: F401

    sig = inspect.signature(func)
    annotation = sig.return_annotation
    if isinstance(annotation, str):
        return eval_type(ForwardRef(annotation), globals(), locals())
    return annotation


def get_n_params(func: Callable[..., Any]) -> int:
    """Get the number of parameters of a function."""
    sig = inspect.signature(func)
    return len(sig.parameters)
