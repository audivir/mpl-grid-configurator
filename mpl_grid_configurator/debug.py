"""Debugging tools."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING

from matplotlib.figure import Figure, SubFigure

from mpl_grid_configurator.register import DRAW_FUNCS
from mpl_grid_configurator.render import render_recursive, savefig
from mpl_grid_configurator.traverse import almost_equal, find_path_by_id

if TYPE_CHECKING:
    from _typeshed import StrPath

    from mpl_grid_configurator.types import (
        BoundingBox,
        Figure_,
        FigureTree,
        Layout,
        LayoutNode,
        LPath,
        SubFigure_,
    )


def print_tree(node: Layout, _depth: int = 0, _path: LPath = ()) -> None:
    """Print the tree in a human-readable format. Debugging tool."""
    if _depth == 0 and isinstance(node, str):
        print(f"Root: {_path} {node}")  # noqa: T201
        return

    print(f"{'  ' * _depth}| {_path} {node['orient']}")  # type: ignore[index] # noqa: T201
    for ix, child in enumerate(node["children"]):  # type: ignore[index]
        if isinstance(child, str):
            print(f"{'  ' * (_depth + 1)}* {(*_path, ix)} {child}: {round(node['ratios'][ix], 2)}")  # type: ignore[index,arg-type] # noqa: T201
        else:
            print_tree(child, _depth + 1, (*_path, ix))


def build_fig_tree(fig: Figure_ | SubFigure_, _forward: bool = False) -> FigureTree:
    """Build a tree of the figure and its subfigures."""
    if not _forward:
        while not isinstance(fig, Figure):
            fig = fig._parent  # noqa: SLF001

    # fig.axes has all axes of the figure and its subfigures, we want only direct children
    n_ax = sum(ax._parent_figure is fig for ax in fig.axes)  # type: ignore[attr-defined] # noqa: SLF001

    return (
        type(fig).__name__,
        len(fig.subfigs),
        n_ax,
        tuple(build_fig_tree(sf, _forward=True) for sf in fig.subfigs),
    )


def print_fig_tree(
    fig_tree: FigureTree,
    _depth: int = 0,
    _path: LPath = (),
) -> None:
    """Print the figure tree in a human-readable format. Debugging tool."""
    name, _, n_ax, children = fig_tree
    axes_str = f" ({n_ax} axes)" if n_ax > 0 else ""
    if name == "Figure":
        print(f"{'  ' * _depth}> {name}{axes_str}")  # noqa: T201
    else:
        print(f"{'  ' * _depth}| {_path[1:]}: {name}{axes_str}")  # noqa: T201
    for ix, sf in enumerate(children):
        if not sf[-1]:  # if subfigure has no children
            axes_str = f" ({sf[2]} axes)" if sf[2] > 0 else ""
            print(f"{'  ' * (_depth + 1)}* {(*_path[1:], ix)}: {sf[0]}{axes_str}")  # noqa: T201
        else:
            print_fig_tree(sf, _depth + 1, (*_path, ix))


def are_siblings(root: LayoutNode, id1: str, id2: str, *, use_full_id: bool = False) -> bool:
    """Check if two leafs are siblings by id."""
    path1 = find_path_by_id(root, id1, use_full_id=use_full_id)
    path2 = find_path_by_id(root, id2, use_full_id=use_full_id)
    if path1 is None or path2 is None:
        raise ValueError("Node not found")
    return path1[:-1] == path2[:-1]


def are_bbox_mappings_equal(a: Mapping[str, BoundingBox], b: Mapping[str, BoundingBox]) -> bool:
    """Check if two bounding box mappings are equal."""
    return set(a) == set(b) and all(
        almost_equal(a[key].x_min, b[key].x_min)
        and almost_equal(a[key].x_max, b[key].x_max)
        and almost_equal(a[key].y_min, b[key].y_min)
        and almost_equal(a[key].y_max, b[key].y_max)
        for key in a
    )


def draw_text(fig: Figure | SubFigure, text: str) -> None:
    """Draw `text` in the center of the figure."""
    ax = fig.add_subplot()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.3, text, ha="center", va="center")


class TextDrawer(Mapping[str, Callable]):
    """Mocks a mapping of drawing functions for testing."""

    def __iter__(self) -> Iterator[str]:
        return iter([])

    def __len__(self) -> int:
        return 0

    def __getitem__(self, key: str) -> Callable:
        return lambda fig: draw_text(fig, key.rsplit(":::", 1)[0])


def draw_tree(
    node: LayoutNode, file: StrPath, mock_draws: bool = False, verbose: bool = False
) -> Figure_:
    """Draw the tree using the function names as text. Debugging tool.

    Args:
        node: The layout tree.
        file: The file to save the figure to.
        mock_draws: If True, use mock `TextDrawer`.
        verbose: If True, print the tree.
    """
    from matplotlib.figure import Figure

    if verbose:
        print_tree(node)
    fig = Figure(figsize=(8, 8), constrained_layout=True)
    root: SubFigure_ = fig.subfigures()  # type: ignore[assignment]
    render_recursive(root, node, TextDrawer() if mock_draws else DRAW_FUNCS, {})
    savefig(root, file)

    return fig  # type: ignore[return-value]


def draw_bboxes(bbox_mapping: Mapping[str, BoundingBox], file: StrPath) -> None:
    """Draw the bounding boxes of every node. Debugging tool."""
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle

    fig = Figure(figsize=(8, 8), constrained_layout=True)
    ax = fig.add_subplot()
    # mirror y axis as 1 is at the bottom
    ax.invert_yaxis()
    for key, bbox in bbox_mapping.items():
        width, height = bbox.x_max - bbox.x_min, bbox.y_max - bbox.y_min
        ax.add_patch(Rectangle((bbox.x_min, bbox.y_min), width, height, alpha=0.5, color="red"))
        ax.text(bbox.x_min + width / 2, bbox.y_min + height / 2, key, color="black", fontsize=12)

    fig.savefig(file)


def get_subfigure_path(cont: Figure_ | SubFigure_) -> LPath:
    """Get the path of a subfigure. If `cont` is a figure, return an empty tuple."""
    if isinstance(cont, Figure):  # root
        return ()
    parent = cont._parent  # noqa: SLF001
    curr_ix = parent.subfigs.index(cont)
    return (*get_subfigure_path(parent), curr_ix)
