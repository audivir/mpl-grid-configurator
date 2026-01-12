"""Operations to traverse the layout tree."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Literal, TypeVar, overload

from matplotlib.figure import Figure

if TYPE_CHECKING:
    from mpl_grid_configurator.types import Figure_, Layout, LayoutNode, LayoutT, LPath, SubFigure_


T = TypeVar("T")

EPSILON = 1e-9


class TraversalError(ValueError):
    """Provided path is invalid for the given operation."""


def almost_equal(a: float, b: float) -> bool:
    """Check if two floats are almost equal."""
    return abs(a - b) < EPSILON


def get_subfig(fig: SubFigure_, path: LPath) -> SubFigure_:
    """Get the subfigure at the given path."""
    if not path:
        raise TraversalError("Root figure is not a subfigure")
    try:
        curr = fig.subfigs[path[0]]
    except IndexError as e:
        raise TraversalError("Root figure has too few subfigures") from e
    try:
        for ix in path[1:]:
            curr = curr.subfigs[ix]
    except IndexError as e:
        raise TraversalError("Subfigure has too few subfigures") from e
    return curr


def get_at(node: Layout, path: LPath) -> Layout:
    """Get the node or leaf at the given path.

    Raises:
        TraversalError: If the path leads to a leaf before the end.
    """
    if isinstance(node, str):
        if path:
            raise TraversalError("Root is a leaf and path is not empty")
        return node
    curr: Layout = node
    for ix in path:
        if ix not in (0, 1):
            raise TraversalError("Path contains invalid index")
        if isinstance(curr, str):
            raise TraversalError("Path reached a leaf during traversal")
        curr = curr["children"][ix]
    return curr


def get_node(node: LayoutNode, path: LPath) -> LayoutNode:
    """Get the node at the given path.

    Raises:
        TraversalError: If the path leads to a leaf during or after the traversal.
    """
    elem = get_at(node, path)
    if isinstance(elem, str):
        raise TraversalError("Path leads to a leaf")
    return elem


def get_leaf(node: Layout, path: LPath) -> str:
    """Get the leaf at the given path.

    Raises:
        TraversalError: If the path leads to a leaf during traversal or a node after the end.
    """
    elem = get_at(node, path)
    if not isinstance(elem, str):
        raise TraversalError("Path leads to a node")
    return elem


@overload
def set_node(node: LayoutNode, path: LPath, value: LayoutNode) -> LayoutNode: ...
@overload
def set_node(node: str, path: LPath, value: LayoutT) -> LayoutT: ...
@overload
def set_node(node: LayoutNode, path: LPath, value: str) -> Layout: ...  # depends on path


def set_node(node: Layout, path: LPath, value: Layout) -> Layout:
    """Set the node or leaf at the given path.

    Raises:
        TraversalError: If the path leads to a leaf during or after the traversal.
    """
    if not path:
        return value
    if isinstance(node, str):
        raise TraversalError("Root is a leaf and path is not empty")
    parent_path = path[:-1]
    parent = get_node(node, parent_path)
    child1, child2 = parent["children"]
    parent["children"] = (value, child2) if path[-1] == 0 else (child1, value)
    return node


def get_lca_path(path1: LPath, path2: LPath) -> LPath:
    """Get the path to the lowest common ancestor of two paths."""
    common: list[int] = []
    for ix, jx in zip(path1, path2, strict=False):
        if ix not in (0, 1) or jx not in (0, 1):
            raise TraversalError("Path contains invalid index")
        if ix != jx:
            break
        common.append(ix)
    return tuple(common)


def get_lca(node: LayoutNode, path1: LPath, path2: LPath) -> tuple[LayoutNode, LPath, LPath, LPath]:
    """Get the lowest common ancestor of two paths.

    Returns:
        A tuple with the LCA node, the LCA path, and the two adjusted paths.
    """
    lca_path = get_lca_path(path1, path2)
    lca = get_node(node, lca_path)
    return (
        lca,
        lca_path,
        path1[len(lca_path) :],
        path2[len(lca_path) :],
    )


def assert_node(layout: Layout) -> LayoutNode:
    """Assert that the layout is a node."""
    if isinstance(layout, str):
        raise ValueError("Layout must be a node")  # noqa: TRY004
    return layout


def is_root(sf: SubFigure_) -> bool:
    """Check if the subfigure is the root figure."""
    return isinstance(sf._parent, Figure)  # noqa: SLF001


def assert_root(sf: SubFigure_) -> Figure_:
    """Assert that the subfigure is the root figure."""
    parent = sf._parent  # noqa: SLF001
    if not isinstance(parent, Figure):
        raise ValueError("Non-root figure provided")  # noqa: TRY004
    return parent


def are_nodes_equal(node1: Layout, node2: Layout) -> bool:
    """Check if two nodes are equal."""
    if isinstance(node1, str) or isinstance(node2, str):
        return node1 == node2

    return (
        node1["orient"] == node2["orient"]
        and almost_equal(node1["ratios"][0], node2["ratios"][0])
        and almost_equal(node1["ratios"][1], node2["ratios"][1])
        and are_nodes_equal(node1["children"][0], node2["children"][0])
        and are_nodes_equal(node1["children"][1], node2["children"][1])
    )


def adjust_node_id(node: LayoutT, mode: Literal["add", "remove"] = "add") -> LayoutT:
    """Add or remove a unique id to every node.

    Returns:
        A copy of the node with adjusted ids.
    """
    if isinstance(node, str):
        if mode == "add":
            return f"{node}:::{uuid.uuid4()}"
        return node.rsplit(":::", 1)[0]
    children = node["children"]
    return {
        "orient": node["orient"],
        "children": (adjust_node_id(children[0], mode), adjust_node_id(children[1], mode)),  # type: ignore[type-var]
        "ratios": node["ratios"],
    }


def find_path_by_id(
    node: LayoutNode | str,
    id_to_find: str,
    path: LPath = (),
    *,
    use_full_id: bool = False,
) -> LPath | None:
    """Find the path to the node with the given id.

    Args:
        node: The node to search in.
        id_to_find: The id to search for.
        path: The current path.
        use_full_id: Whether to use the full id (function name + optional uuid)
            or just the uuid.

    Returns:
        The path to the node with the given id or None if no such node exists.
    """
    if isinstance(node, str):
        curr_id = node if use_full_id else node.rsplit(":::", 1)[1]
        return path if curr_id == id_to_find else None

    for ix, child in enumerate(node["children"]):
        result = find_path_by_id(child, id_to_find, (*path, ix), use_full_id=use_full_id)
        if result is not None:
            return result
    return None
