"""Start a webapp for adjusting a matplotlib layout."""

from __future__ import annotations

import io
import logging
from typing import IO, TYPE_CHECKING, Any, TypeVar

from matplotlib.figure import Figure

from mpl_grid_configurator.types import (
    Layout,
    LayoutNode,
    Orientation,
    is_str_draw_func,
    is_tuple_draw_func,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, MutableMapping

    from _typeshed import StrPath
    from matplotlib.axes import Axes

    from mpl_grid_configurator.types import Figure_, SubFigure_

logger = logging.getLogger(__name__)


T = TypeVar("T")


def new_root(figsize: tuple[int, int] = (8, 8)) -> tuple[Figure_, SubFigure_]:
    """Create a new constrained Figure_ and its root figure."""
    fig: Figure_ = Figure(figsize, constrained_layout=True)  # type: ignore[assignment]
    fig.patch.set_visible(False)
    root: SubFigure_ = fig.subfigures()  # type: ignore[assignment]
    root.patch.set_visible(False)
    return fig, root


def split_figure(
    container: Figure_ | SubFigure_,
    orient: Orientation,
    ratios: tuple[float, float],
) -> tuple[SubFigure_, SubFigure_]:
    """Split a figure into two subfigures with the given ratios and orientation."""
    is_row = orient == "row"
    sfs: tuple[SubFigure_, SubFigure_] = container.subfigures(  # type: ignore[assignment]
        nrows=1 if is_row else 2,
        ncols=2 if is_row else 1,
        width_ratios=ratios if is_row else None,
        height_ratios=ratios if not is_row else None,
    )
    sf1, sf2 = sfs
    sf1.patch.set_visible(False)
    sf2.patch.set_visible(False)
    return sf1, sf2


def run_draw_func(
    func_name: str,
    func: Callable,
    container: SubFigure_,
    svg_mapping: MutableMapping[str, str] | None = None,
) -> Callable[[str], str]:
    """Run a draw function."""
    from mpl_grid_configurator.unnested_skunk import connect, insert

    if is_tuple_draw_func(func):
        svg, ax = func(container)
    elif is_str_draw_func(func):
        svg = func()
        ax = draw_empty(container)
    else:  # it's axes draw func
        func(container)
        return lambda final_svg: final_svg
    connect(ax, func_name)
    if svg_mapping is not None:
        svg_mapping[func_name] = svg
    return lambda final_svg: insert({func_name: svg}, final_svg)


def render_recursive(
    container: SubFigure_,
    layout: Layout,
    draw_funcs: Mapping[str, Callable],
    svg_mapping: MutableMapping[str, str] | None = None,
) -> None:
    """Render a node recursively."""
    if isinstance(layout, str):
        func_name: str = layout
        if func := draw_funcs.get(func_name):
            run_draw_func(func_name, func, container, svg_mapping)
        else:
            raise ValueError(f"No draw function found for {func_name}")
    else:
        node: LayoutNode = layout
        sf1, sf2 = split_figure(
            container,
            node["orient"],
            node["ratios"],
        )
        child1, child2 = node["children"]
        render_recursive(sf1, child1, draw_funcs, svg_mapping)
        render_recursive(sf2, child2, draw_funcs, svg_mapping)


def render_layout(
    layout: Layout, figsize: tuple[float, float], draw_funcs: Mapping[str, Callable]
) -> tuple[SubFigure_, Callable[[str], str]]:
    """Render a layout."""
    from matplotlib.figure import Figure

    from mpl_grid_configurator.unnested_skunk import insert

    width, height = figsize

    # Use constrained_layout=True to ensure subplots respect the ratio boundaries
    # and redraws the figure when the layout changes
    fig: Figure_ = Figure(figsize=(width, height), constrained_layout=True)  # type: ignore[assignment]
    root: SubFigure_ = fig.subfigures()  # type: ignore[assignment]

    svg_mapping: dict[str, str] = {}
    render_recursive(root, layout, draw_funcs, svg_mapping)

    if not svg_mapping:
        return root, lambda svg: svg

    def svg_callback(final_svg: str) -> str:
        return insert(svg_mapping, final_svg)

    return root, svg_callback


def render_svg(root: Figure_ | SubFigure_, svg_callback: Callable[[str], str]) -> str:
    """Save a figure to svg, apply a callback and return the svg."""
    buf = io.BytesIO()
    root.patch.set_visible(False)
    savefig(root, buf, format="svg")
    final_svg = buf.getvalue().decode("utf-8")
    return svg_callback(final_svg)


def draw_empty(container: SubFigure_) -> Axes:
    """Draw an empty plot."""
    ax = container.subplots()
    ax.axis("off")
    return ax


def savefig(fig: Figure_ | SubFigure_, fname: StrPath | IO, **kwargs: Any) -> None:
    """Save the root figure of the given figure to the given file."""
    while not isinstance(fig, Figure):
        fig = fig._parent  # noqa: SLF001
    fig.savefig(fname, **kwargs)
