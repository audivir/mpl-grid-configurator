from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import pytest
from matplotlib.figure import Figure, SubFigure

from mpl_grid_configurator.render import new_root, split_figure
from mpl_grid_configurator.traverse import (
    TraversalError,
    adjust_node_id,
    almost_equal,
    are_nodes_equal,
    assert_node,
    assert_root,
    find_path_by_id,
    get_at,
    get_lca,
    get_lca_path,
    get_leaf,
    get_node,
    get_subfig,
    is_root,
    set_node,
)

if TYPE_CHECKING:
    from mpl_grid_configurator.types import Layout, LayoutNode, SubFigure_


@pytest.fixture(
    params=[
        ((0, 1, 0), (0, 1, 1), (0, 1)),
        ((0, 1, 0), (0, 0), (0,)),
        ((0, 1, 0), (1, 0), ()),
    ]
)
def lca_request(
    request: pytest.FixtureRequest,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """Existing paths in the `simple_root` fixture."""
    return request.param


def get_nested_subfigures() -> tuple[SubFigure_, dict[tuple[int, ...], SubFigure_]]:
    _, root = new_root()
    s0, s1 = split_figure(root, "column", (50, 50))
    s00, s01 = split_figure(s0, "row", (50, 50))
    return root, {
        (0,): s0,
        (0, 0): s00,
        (0, 1): s01,
        (1,): s1,
    }


@pytest.fixture
def nested_subfigures() -> tuple[SubFigure_, dict[tuple[int, ...], SubFigure_]]:
    """Create a figure with a nested subfigures layout.

    Represents:
        >>> fig
        >>> |-s0
        >>> | |-s00
        >>> | `-s01
        >>> `-s1
    """
    return get_nested_subfigures()


def test_almost_equal() -> None:
    assert almost_equal(0.2 * 7, 1.4)
    assert not almost_equal(0.2 * 7, 1.41)


@pytest.mark.parametrize("path", [(0,), (0, 0), (0, 1), (1,)])
def test_get_subfig(
    path: tuple[int, ...], nested_subfigures: tuple[Figure, dict[tuple[int, ...], SubFigure]]
) -> None:
    fig, subfigures_mapping = nested_subfigures
    assert get_subfig(fig, path) == subfigures_mapping[path]  # type: ignore[arg-type]


def test_get_subfig_fail(
    nested_subfigures: tuple[SubFigure_, dict[tuple[int, ...], SubFigure_]],
) -> None:
    fig, _ = nested_subfigures
    with pytest.raises(TraversalError, match="Root figure is not a subfigure"):
        get_subfig(fig, ())
    with pytest.raises(TraversalError, match="Root figure has too few subfigures"):
        get_subfig(fig, (2,))
    with pytest.raises(TraversalError, match="Subfigure has too few subfigures"):
        get_subfig(fig, (0, 2))


@pytest.fixture
def node_paths() -> list[tuple[int, ...]]:
    return [
        (),
        (0,),
        (1,),
        (0, 1),
        (1, 1),
    ]


@pytest.fixture
def leaf_paths() -> list[tuple[int, ...]]:
    return [
        (0, 0),
        (0, 1, 0),
        (0, 1, 1),
        (1, 0),
        (1, 1, 0),
        (1, 1, 1),
    ]


def test_get_at_node(
    simple_root: LayoutNode,
    simple_root_node_item: tuple[tuple[int, ...], LayoutNode],
) -> None:
    path, node = simple_root_node_item
    assert get_at(simple_root, path) == node


def test_get_at_leaf(
    simple_root: LayoutNode,
    simple_root_leaf_item: tuple[tuple[int, ...], str],
) -> None:
    path, leaf = simple_root_leaf_item
    assert get_at(simple_root, path) == leaf


def test_get_at_root_leaf() -> None:
    assert get_at("root", ()) == "root"


def test_get_at_fail(simple_root: LayoutNode) -> None:
    with pytest.raises(TraversalError, match="Path contains invalid index"):
        get_at(simple_root, (2,))
    with pytest.raises(TraversalError, match="Path reached a leaf during traversal"):
        get_at(simple_root, (1, 1, 1, 1))
    with pytest.raises(TraversalError, match="Root is a leaf and path is not empty"):
        get_at("root", (1,))


def test_get_node(
    simple_root: LayoutNode, simple_root_node_item: tuple[tuple[int, ...], LayoutNode]
) -> None:
    path, node = simple_root_node_item
    assert get_node(simple_root, path) == node


def test_get_node_fail(
    simple_root: LayoutNode, simple_root_leaf_item: tuple[tuple[int, ...], str]
) -> None:
    path, _ = simple_root_leaf_item
    with pytest.raises(TraversalError, match="Path leads to a leaf"):
        get_node(simple_root, path)


def test_get_leaf(
    simple_root: LayoutNode, simple_root_leaf_item: tuple[tuple[int, ...], str]
) -> None:
    path, leaf = simple_root_leaf_item
    assert get_leaf(simple_root, path) == leaf


def test_get_leaf_fail(
    simple_root: LayoutNode, simple_root_node_item: tuple[tuple[int, ...], LayoutNode]
) -> None:
    path, _ = simple_root_node_item
    with pytest.raises(TraversalError, match="Path leads to a node"):
        get_leaf(simple_root, path)


def test_set_node_leaf(simple_root: LayoutNode) -> None:
    expected = deepcopy(simple_root)
    _, child2 = expected["children"]
    expected["children"] = ("new_leaf", child2)
    new_root = set_node(simple_root, (0,), "new_leaf")
    assert new_root == expected


def test_set_node_node(simple_root: LayoutNode, simple_left: LayoutNode) -> None:
    expected = deepcopy(simple_root)
    parent = get_node(expected, (0,))
    _, child2 = parent["children"]
    parent["children"] = (simple_left, child2)
    new_root = set_node(simple_root, (0, 0), simple_left)
    assert new_root == expected


def test_set_node_fail(simple_root: LayoutNode) -> None:
    with pytest.raises(TraversalError, match="Path reached a leaf during traversal"):
        set_node(simple_root, (0, 0, 0, 0), "new_leaf")


def test_set_node_root(simple_root: LayoutNode, simple_left: LayoutNode) -> None:
    leaf_root = set_node("root", (), "new_root")
    assert leaf_root == "new_root"

    new_root = set_node(simple_root, (), "new_root")
    assert new_root == "new_root"

    node_root = set_node("root", (), simple_root)
    assert node_root == simple_root

    node_root = set_node(simple_root, (), simple_left)
    assert node_root == simple_left


def test_set_node_root_fail() -> None:
    with pytest.raises(TraversalError, match="Root is a leaf and path is not empty"):
        set_node("root", (1,), "new_root")


def test_get_lca_path(
    lca_request: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]],
) -> None:
    path1, path2, expected = lca_request
    assert get_lca_path(path1, path2) == expected


def test_get_lca_path_fail() -> None:
    with pytest.raises(TraversalError, match="Path contains invalid index"):
        get_lca_path((0, 1, 2), (0, 1, 3))


def test_get_lca(
    simple_root: LayoutNode, lca_request: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]
) -> None:
    path1, path2, expected = lca_request
    elem1 = get_at(simple_root, path1)
    elem2 = get_at(simple_root, path2)
    lca, lca_path, adj_path1, adj_path2 = get_lca(simple_root, path1, path2)
    assert lca_path == expected
    assert get_at(lca, adj_path1) == elem1
    assert get_at(lca, adj_path2) == elem2


def test_assert_node_node(simple_root_node_item: tuple[tuple[int, ...], LayoutNode]) -> None:
    _, node = simple_root_node_item
    assert assert_node(node) == node


def test_assert_node_leaf(simple_root_leaf_item: tuple[tuple[int, ...], str]) -> None:
    _, leaf = simple_root_leaf_item
    with pytest.raises(ValueError, match="Layout must be a node"):
        assert_node(leaf)


def test_is_root(
    nested_subfigures: tuple[SubFigure_, dict[tuple[int, ...], SubFigure_]],
) -> None:
    fig, _ = nested_subfigures
    assert is_root(fig)


@pytest.mark.parametrize("sf", get_nested_subfigures()[1].values())
def test_is_root_false(sf: SubFigure_) -> None:
    assert not is_root(sf)


def test_assert_root(
    nested_subfigures: tuple[SubFigure_, dict[tuple[int, ...], SubFigure_]],
) -> None:
    fig, _ = nested_subfigures
    root = assert_root(fig)
    assert root == fig._parent  # noqa: SLF001
    assert isinstance(root, Figure)


@pytest.mark.parametrize("sf", get_nested_subfigures()[1].values())
def test_assert_root_fail(sf: SubFigure_) -> None:
    with pytest.raises(ValueError, match="Non-root figure provided"):
        assert_root(sf)


# TODO(tihoph): test_are_nodes_equal


def get_node_id_mapping(node: LayoutNode) -> dict[str, str]:
    """Get a mapping of node ids to original names. Asserts that ids and values are unique."""
    node_id_mapping: dict[str, str] = {}

    def add_node_id(node: Layout) -> None:
        if isinstance(node, str):
            orig_name, node_id = node.rsplit(":::", 1)
            assert node_id not in node_id_mapping
            node_id_mapping[node_id] = orig_name
        else:
            add_node_id(node["children"][0])
            add_node_id(node["children"][1])

    add_node_id(node)

    # for testing purposes also verify no duplicate values
    assert len(node_id_mapping) == len(set(node_id_mapping.values()))

    return node_id_mapping


def test_adjust_node_id(simple_left: LayoutNode) -> None:
    with_ids = adjust_node_id(simple_left, mode="add")
    assert not are_nodes_equal(simple_left, with_ids)

    get_node_id_mapping(with_ids)

    without_ids = adjust_node_id(with_ids, mode="remove")
    assert are_nodes_equal(simple_left, without_ids)


@pytest.mark.parametrize("use_full_id", [False, True])
def test_find_path_by_id(simple_left: LayoutNode, use_full_id: bool) -> None:
    simple_left = adjust_node_id(simple_left, mode="add")
    node_id_mapping = get_node_id_mapping(simple_left)
    for node_id, orig_name in node_id_mapping.items():
        full_id = f"{orig_name}:::{node_id}"
        used_id = full_id if use_full_id else node_id
        found_path = find_path_by_id(simple_left, used_id, use_full_id=use_full_id)
        assert found_path is not None
        assert get_leaf(simple_left, found_path) == full_id
