"""Operations to traverse the layout tree."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from mpl_grid_configurator.types import Figure_, LayoutNode, SubFigure_


T = TypeVar("T")


class TraversalError(ValueError):
    """Provided path is invalid for the given operation."""


def get_subfig(fig: Figure_ | SubFigure_, path: tuple[int, ...]) -> Figure_ | SubFigure_:
    """Get the subfigure at the given path."""
    if not path:
        return fig
    curr = fig.subfigs[path[0]]
    for ix in path[1:]:
        curr = curr.subfigs[ix]
    return curr


def get_at(node: LayoutNode, path: tuple[int, ...]) -> LayoutNode | str:
    """Get the node or leaf at the given path.

    Raises:
        TraversalError: If the path leads to a leaf before the end.
    """
    if not path:
        return node
    curr: LayoutNode | str = node
    for ix in path:
        if isinstance(curr, str):
            raise TraversalError("Path reached a leaf during traversal")
        curr = curr["children"][ix]
    return curr


def get_node(node: LayoutNode, path: tuple[int, ...]) -> LayoutNode:
    """Get the node at the given path.

    Raises:
        TraversalError: If the path leads to a leaf during or after the traversal.
    """
    elem = get_at(node, path)
    if isinstance(elem, str):
        raise TraversalError("Path leads to a leaf")
    return elem


def get_leaf(node: LayoutNode, path: tuple[int, ...]) -> str:
    """Get the leaf at the given path.

    Raises:
        TraversalError: If the path leads to a leaf during traversal or a node after the end.
    """
    elem = get_at(node, path)
    if not isinstance(elem, str):
        raise TraversalError("Path leads to a node")
    return elem


def set_node(node: LayoutNode, path: tuple[int, ...], value: LayoutNode | str) -> None:
    """Set the node or leaf at the given path.

    Raises:
        ValueError: If the path is empty.
        TraversalError: If the path leads to a leaf during or after the traversal.
    """
    if not path:
        raise ValueError("Root must be set externally")
    for ix in path[:-1]:
        child = node["children"][ix]
        if isinstance(child, str):
            raise TraversalError("Path reached or leads to a leaf")
        node = child
    children = node["children"]
    node["children"] = (value, children[1]) if path[-1] == 0 else (children[0], value)


def get_lca_path(path_a: tuple[int, ...], path_b: tuple[int, ...]) -> tuple[int, ...]:
    """Get the path to the lowest common ancestor of two paths."""
    common: list[int] = []
    for ix, jx in zip(path_a, path_b, strict=False):
        if ix != jx:
            break
        common.append(ix)
    return tuple(common)


def get_lca(
    node: LayoutNode, path_a: tuple[int, ...], path_b: tuple[int, ...]
) -> tuple[LayoutNode, tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """Get the lowest common ancestor of two paths.

    Returns:
        A tuple with the LCA node, the LCA path, and the two adjusted paths.
    """
    lca_path = get_lca_path(path_a, path_b)
    lca = get_node(node, lca_path)
    return (
        lca,
        lca_path,
        path_a[len(lca_path) :],
        path_b[len(lca_path) :],
    )
