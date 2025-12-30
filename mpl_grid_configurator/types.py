"""Functions to parse function signatures."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ForwardRef, Literal, TypeAlias, TypeVar, get_origin

from doctyper._typing import eval_type
from typing_extensions import TypedDict, TypeIs

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure, SubFigure

T = TypeVar("T")

AxesDrawFunc: TypeAlias = "Callable[[Figure | SubFigure], Axes]"
TupleDrawFunc: TypeAlias = "Callable[[Figure | SubFigure], tuple[str, Axes]]"
StrDrawFunc: TypeAlias = Callable[[], str]
DrawFunc: TypeAlias = "AxesDrawFunc | TupleDrawFunc | StrDrawFunc"
DrawFuncT = TypeVar("DrawFuncT", bound=DrawFunc)


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
