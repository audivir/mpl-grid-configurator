"""Start a webapp for adjusting a matplotlib layout."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

from mpl_grid_configurator.types import (
    Layout,
    LayoutNode,
    Orientation,
    is_str_draw_func,
    is_tuple_draw_func,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, MutableMapping

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure, SubFigure

logger = logging.getLogger(__name__)


T = TypeVar("T")


def split_figure(
    container: Figure | SubFigure,
    orient: Orientation,
    ratios: tuple[float, float],
) -> tuple[SubFigure, SubFigure]:
    """Split a figure into two subfigures with the given ratios and orientation."""
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
    draw_funcs: Mapping[str, Callable],
) -> None:
    """Render a node recursively."""
    from mpl_grid_configurator.unnested_skunk import connect

    if isinstance(layout, str):
        func_name: str = layout
        func = draw_funcs.get(func_name)
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
        left_up_subfig, right_down_subfig = split_figure(
            container,
            node["orient"],
            node["ratios"],
        )
        left_up, right_down = node["children"]
        render_recursive(left_up_subfig, left_up, svg_mapping, draw_funcs)
        render_recursive(right_down_subfig, right_down, svg_mapping, draw_funcs)


def render_layout(
    layout: Layout, figsize: tuple[float, float], draw_funcs: Mapping[str, Callable]
) -> tuple[Figure, Callable[[str], str]]:
    """Render a layout."""
    from matplotlib.figure import Figure

    from mpl_grid_configurator.unnested_skunk import insert

    width, height = figsize

    # Use layout="constrained" to ensure subplots respect the ratio boundaries
    fig = Figure(figsize=(width, height), layout="constrained")

    svg_mapping: dict[str, str] = {}
    render_recursive(fig, layout, svg_mapping, draw_funcs)

    if not svg_mapping:
        return fig, lambda svg: svg

    def svg_callback(final_svg: str) -> str:
        return insert(svg_mapping, final_svg)

    return fig, svg_callback


def draw_empty(container: Figure | SubFigure) -> Axes:
    """Draw an empty plot."""
    ax = container.subplots()
    ax.axis("off")
    return ax
