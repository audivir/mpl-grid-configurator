from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mpl_grid_configurator.render import DEFAULT_LEAF

if TYPE_CHECKING:
    from utils import ChangeFixture

    from mpl_grid_configurator.types import Layout, LayoutNode, LPath, Orient, Ratios


@pytest.fixture
def delete_to_unsplitted_root() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (70, 30)}
    post: Layout = "f2l"

    path = (0,)
    return pre, post, ("delete", path, {}), "f1l"


def _get_delete_to_splitted_root(post: Layout, path: LPath) -> ChangeFixture:
    pre: Layout = {
        "orient": "row",
        "children": ("f1l", {"orient": "row", "children": ("f2l", "f3l"), "ratios": (70, 30)}),
        "ratios": (70, 30),
    }
    expected_removed = pre["children"][path[-1]]  # type: ignore[index]
    return pre, post, ("delete", path, {}), expected_removed


@pytest.fixture
def delete_leaf_to_splitted_root() -> ChangeFixture:
    post: Layout = {"orient": "row", "children": ("f2l", "f3l"), "ratios": (70, 30)}
    path = (0,)
    return _get_delete_to_splitted_root(post, path)


@pytest.fixture
def delete_node_to_splitted_root() -> ChangeFixture:
    post: Layout = "f1l"
    path = (1,)
    return _get_delete_to_splitted_root(post, path)


@pytest.fixture
def replace_unsplitted_root() -> ChangeFixture:
    pre: Layout = "f1l"
    post: Layout = "f2l"

    path = ()
    return pre, post, ("replace", path, {"value": "f2l"}), "f1l"


@pytest.fixture
def replace_splitted_root() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (70, 30)}
    post: Layout = {"orient": "row", "children": ("f3l", "f2l"), "ratios": (70, 30)}

    path = (0,)
    return pre, post, ("replace", path, {"value": "f3l"}), "f1l"


@pytest.fixture
def replace_with_node() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (70, 30)}
    new_node: LayoutNode = {"orient": "row", "children": ("f3l", "f4l"), "ratios": (40, 60)}
    post: Layout = {"orient": "row", "children": ("f1l", new_node), "ratios": (70, 30)}

    path = (1,)
    return pre, post, ("replace", path, {"value": new_node}), "f2l"


@pytest.fixture
def restructure() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (70, 30)}
    post: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (40, 60)}

    path = ()
    return pre, post, ("restructure", path, {"ratios": (40, 60)}), None


@pytest.fixture
def restructure_unchanged() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (70, 30)}
    post: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (70, 30)}

    return pre, post, ("restructure", (), {"ratios": (70, 30)}), None


@pytest.fixture
def rotate() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (70, 30)}
    post: Layout = {"orient": "column", "children": ("f1l", "f2l"), "ratios": (70, 30)}

    path = ()
    return pre, post, ("rotate", path, {}), None


@pytest.fixture
def split_root() -> ChangeFixture:
    pre: Layout = "f1l"
    post: Layout = {"orient": "row", "children": ("f1l", DEFAULT_LEAF), "ratios": (50, 50)}

    orient: Orient = "row"
    path = ()
    return pre, post, ("split", path, {"orient": orient}), None


@pytest.fixture
def split_leaf() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (40, 60)}
    post: Layout = {
        "orient": "row",
        "children": (
            {"orient": "row", "children": ("f1l", DEFAULT_LEAF), "ratios": (50, 50)},
            "f2l",
        ),
        "ratios": (40, 60),
    }

    orient: Orient = "row"
    path = (0,)
    return pre, post, ("split", path, {"orient": orient}), None


@pytest.fixture
def split_node() -> ChangeFixture:
    pre: Layout = {
        "orient": "row",
        "children": (
            {"orient": "row", "children": ("f1l", "f2l"), "ratios": (40, 60)},
            "f3l",
        ),
        "ratios": (30, 70),
    }
    post: Layout = {
        "orient": "row",
        "children": (
            {
                "orient": "row",
                "children": (
                    {"orient": "row", "children": ("f1l", "f2l"), "ratios": (40, 60)},
                    DEFAULT_LEAF,
                ),
                "ratios": (50, 50),
            },
            "f3l",
        ),
        "ratios": (30, 70),
    }

    orient: Orient = "row"
    path = (0,)
    return pre, post, ("split", path, {"orient": orient}), None


@pytest.fixture
def swap_leaf_siblings() -> ChangeFixture:
    pre: Layout = {
        "orient": "row",
        "children": ("f1l", "f2l"),
        "ratios": (40, 60),
    }
    post: Layout = {
        "orient": "row",
        "children": ("f2l", "f1l"),
        "ratios": (40, 60),
    }

    path1 = (0,)
    path2 = (1,)
    return pre, post, ("swap", path1, {"path2": path2}), None


@pytest.fixture
def swap_leaf_with_node() -> ChangeFixture:
    pre: Layout = {
        "orient": "row",
        "children": ("f1l", {"orient": "row", "children": ("f2l", "f3l"), "ratios": (40, 60)}),
        "ratios": (30, 70),
    }
    post: Layout = {
        "orient": "row",
        "children": ({"orient": "row", "children": ("f2l", "f3l"), "ratios": (40, 60)}, "f1l"),
        "ratios": (30, 70),
    }

    return pre, post, ("swap", (0,), {"path2": (1,)}), None


@pytest.fixture
def swap_two_nodes() -> ChangeFixture:
    pre: Layout = {
        "orient": "row",
        "children": (
            {"orient": "row", "children": ("f1l", "f2l"), "ratios": (80, 20)},
            {"orient": "row", "children": ("f3l", "f4l"), "ratios": (40, 60)},
        ),
        "ratios": (30, 70),
    }
    post: Layout = {
        "orient": "row",
        "children": (
            {"orient": "row", "children": ("f3l", "f4l"), "ratios": (40, 60)},
            {"orient": "row", "children": ("f1l", "f2l"), "ratios": (80, 20)},
        ),
        "ratios": (30, 70),
    }

    return pre, post, ("swap", (0,), {"path2": (1,)}), None


@pytest.fixture
def swap_leaf_non_siblings() -> ChangeFixture:
    pre: Layout = {
        "orient": "row",
        "children": ("f1l", {"orient": "row", "children": ("f2l", "f3l"), "ratios": (40, 60)}),
        "ratios": (30, 70),
    }
    post: Layout = {
        "orient": "row",
        "children": (
            "f2l",
            {"orient": "row", "children": ("f1l", "f3l"), "ratios": (40, 60)},
        ),
        "ratios": (30, 70),
    }

    return pre, post, ("swap", (0,), {"path2": (1, 0)}), None


@pytest.fixture
def swap_same() -> ChangeFixture:
    pre: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (40, 60)}
    post: Layout = {"orient": "row", "children": ("f1l", "f2l"), "ratios": (40, 60)}

    path = (0,)
    return pre, post, ("swap", path, {"path2": path}), None


@pytest.fixture
def insert() -> ChangeFixture:
    pre: Layout = "f1l"
    post: Layout = {
        "orient": "row",
        "children": ("f1l", "f2l"),
        "ratios": (70, 30),
    }

    path: LPath = (1,)
    orient: Orient = "row"
    ratios: Ratios = (70, 30)
    value = "f2l"
    return (
        pre,
        post,
        ("insert", path, {"orient": orient, "ratios": ratios, "value": value}),
        DEFAULT_LEAF,
    )


@pytest.fixture
def insert_next_to_node() -> ChangeFixture:
    pre: Layout = {
        "orient": "row",
        "children": ("f1l", "f2l"),
        "ratios": (70, 30),
    }
    post: Layout = {
        "orient": "row",
        "children": (
            {
                "orient": "row",
                "children": ("f1l", "f2l"),
                "ratios": (70, 30),
            },
            "f3l",
        ),
        "ratios": (60, 40),
    }

    path: LPath = (1,)
    orient: Orient = "row"
    ratios = (60, 40)
    value = "f3l"
    return (
        pre,
        post,
        ("insert", path, {"orient": orient, "ratios": ratios, "value": value}),
        DEFAULT_LEAF,
    )


@pytest.fixture
def insert_node() -> ChangeFixture:
    pre: Layout = "f1l"
    new_node: Layout = {
        "orient": "row",
        "children": ("f1l", "f2l"),
        "ratios": (60, 40),
    }
    post: Layout = {
        "orient": "row",
        "children": ("f1l", new_node),
        "ratios": (70, 30),
    }

    path: LPath = (1,)
    orient: Orient = "row"
    ratios = (70, 30)
    value = new_node
    return (
        pre,
        post,
        ("insert", path, {"orient": orient, "ratios": ratios, "value": value}),
        DEFAULT_LEAF,
    )


FIXTURES = [
    "delete_to_unsplitted_root",
    "delete_leaf_to_splitted_root",
    "delete_node_to_splitted_root",
    "replace_unsplitted_root",
    "replace_splitted_root",
    "replace_with_node",
    "restructure",
    # "restructure_unchanged",
    "rotate",
    "split_root",
    "split_leaf",
    "split_node",
    "swap_leaf_siblings",
    "swap_leaf_with_node",
    "swap_two_nodes",
    "swap_leaf_non_siblings",
    "swap_same",
    "insert",
    "insert_next_to_node",
    "insert_node",
]


@pytest.fixture(params=FIXTURES)
def change_fixture(request: pytest.FixtureRequest) -> ChangeFixture:
    """All changes as single fixture."""
    return request.getfixturevalue(request.param)
