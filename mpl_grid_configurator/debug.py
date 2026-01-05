"""Debugging tools."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING

from mpl_grid_configurator.merge import almost_equal, find_path_by_id
from mpl_grid_configurator.render import render_recursive

if TYPE_CHECKING:
    from _typeshed import StrPath
    from matplotlib.figure import SubFigure

    from mpl_grid_configurator.types import BoundingBox, LayoutNode


def print_tree(node: LayoutNode, depth: int = 0, path: tuple[int, ...] = ()) -> None:
    """Print the tree in a human-readable format. Debugging tool."""
    print(f"{'  ' * depth}| {path} {node['orient']}")  # noqa: T201
    for ix, child in enumerate(node["children"]):
        if isinstance(child, str):
            print(f"{'  ' * (depth + 1)}* {(*path, ix)} {child}: {round(node['ratios'][ix], 2)}")  # noqa: T201
        else:
            print_tree(child, depth + 1, (*path, ix))


def are_siblings(root: LayoutNode, id_a: str, id_b: str, *, use_full_id: bool = False) -> bool:
    """Check if two leafs are siblings by id."""
    path_a = find_path_by_id(root, id_a, use_full_id=use_full_id)
    path_b = find_path_by_id(root, id_b, use_full_id=use_full_id)
    if path_a is None or path_b is None:
        raise ValueError("Node not found")
    return path_a[:-1] == path_b[:-1]


def are_nodes_equal(node_a: LayoutNode | str, node_b: LayoutNode | str) -> bool:
    """Check if two nodes are equal."""
    if isinstance(node_a, str) or isinstance(node_b, str):
        return node_a == node_b

    return (
        node_a["orient"] == node_b["orient"]
        and almost_equal(node_a["ratios"][0], node_b["ratios"][0])
        and almost_equal(node_a["ratios"][1], node_b["ratios"][1])
        and are_nodes_equal(node_a["children"][0], node_b["children"][0])
        and are_nodes_equal(node_a["children"][1], node_b["children"][1])
    )


def are_bbox_mappings_equal(a: Mapping[str, BoundingBox], b: Mapping[str, BoundingBox]) -> bool:
    """Check if two bounding box mappings are equal."""
    return set(a) == set(b) and all(
        almost_equal(a[key].x_min, b[key].x_min)
        and almost_equal(a[key].x_max, b[key].x_max)
        and almost_equal(a[key].y_min, b[key].y_min)
        and almost_equal(a[key].y_max, b[key].y_max)
        for key in a
    )


def draw_tree(root: LayoutNode, file: StrPath) -> None:
    """Draw the tree using the function names as text. Debugging tool."""
    from matplotlib.figure import Figure

    def draw_text(fig: Figure | SubFigure, text: str) -> None:
        """Draw text in the center of the figure."""
        ax = fig.add_subplot()
        ax.axis("off")
        ax.text(0.5, 0.5, text, ha="center", va="center")

    class TextDrawer(Mapping[str, Callable]):
        """Mocks a mapping of drawing functions for testing."""

        def __iter__(self) -> Iterator[str]:
            return iter([])

        def __len__(self) -> int:
            return 0

        def __getitem__(self, key: str) -> Callable:
            return lambda fig: draw_text(fig, key.rsplit(":::", 1)[0])

    print_tree(root)
    fig = Figure(figsize=(8, 8), constrained_layout=True)
    render_recursive(fig, root, {}, TextDrawer())
    fig.savefig(file)


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
