from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import pytest

from mpl_grid_configurator.debug import draw_text
from mpl_grid_configurator.register import DRAW_FUNCS, register

if TYPE_CHECKING:
    from collections.abc import Generator

    from matplotlib.axes import Axes

    from mpl_grid_configurator.types import Figure_, LayoutNode, SubFigure_

pytest_plugins = ("changes",)


def register_texts(*texts: str) -> None:
    for text in texts:
        _draw = partial(draw_text, text=text)
        _draw.__name__ = text  # type: ignore[attr-defined]
        register(_draw)  # type: ignore[type-var]


# fixture to reset DRAW_FUNCS to it's initial state
@pytest.fixture
def reset_draw_funcs() -> Generator[None]:
    initial_draw_funcs = DRAW_FUNCS.copy()
    try:
        DRAW_FUNCS.clear()
        yield
    finally:
        DRAW_FUNCS.clear()
        DRAW_FUNCS.update(initial_draw_funcs)


@pytest.fixture
def define_draw_funcs(reset_draw_funcs: None) -> None:
    del reset_draw_funcs

    def draw_axes(fig: Figure_ | SubFigure_) -> Axes:
        return fig.add_subplot()

    DRAW_FUNCS["draw_empty"] = draw_axes  # type: ignore[assignment]

    texts = [f"f{ix}{o}" for ix in range(10) for o in ("l", "r")]
    texts += [f"f{ix}" for ix in range(10)]
    register_texts(*texts)


def get_simple_left() -> LayoutNode:
    sub_right: LayoutNode = {"orient": "column", "children": ("f2l", "f6l"), "ratios": (30, 70)}
    return {"orient": "column", "children": ("f1l", sub_right), "ratios": (30, 70)}


@pytest.fixture
def simple_left() -> LayoutNode:
    """Simple left child of root."""  # noqa: D401
    return get_simple_left()


def get_simple_right() -> LayoutNode:
    sub_right: LayoutNode = {"orient": "column", "children": ("f4r", "f5r"), "ratios": (50, 50)}
    return {"orient": "column", "children": ("f3r", sub_right), "ratios": (30, 70)}


@pytest.fixture
def simple_right() -> LayoutNode:
    """Simple right child of root."""  # noqa: D401
    return get_simple_right()


def get_simple_root() -> LayoutNode:
    return {
        "orient": "row",
        "children": (get_simple_left(), get_simple_right()),
        "ratios": (70, 30),
    }


@pytest.fixture
def simple_root() -> LayoutNode:
    """Simple root node.

    Represents:
        >>> f1l       | f3r
        >>> --------- | ---------
        >>> f2l (30%) | f4r (50%)
        >>> --------- | ---------
        >>> f6l (70%) | f5r (50%)
    """  # noqa: D401
    return get_simple_root()


def get_simple_root_nodes(simple_root: LayoutNode) -> dict[tuple[int, ...], LayoutNode]:
    return {
        (): simple_root,
        (0,): simple_root["children"][0],  # type: ignore[dict-item]
        (1,): simple_root["children"][1],  # type: ignore[dict-item]
        (0, 1): simple_root["children"][0]["children"][1],  # type: ignore[dict-item,index]
        (1, 1): simple_root["children"][1]["children"][1],  # type: ignore[dict-item,index]
    }


@pytest.fixture(
    params=get_simple_root_nodes(get_simple_root()).items(),
    ids=lambda item: f"{item[0]}",
)
def simple_root_node_item(request: pytest.FixtureRequest) -> tuple[tuple[int, ...], LayoutNode]:
    return request.param


def get_simple_root_leafs() -> dict[tuple[int, ...], str]:
    return {
        (0, 0): "f1l",
        (0, 1, 0): "f2l",
        (0, 1, 1): "f6l",
        (1, 0): "f3r",
        (1, 1, 0): "f4r",
        (1, 1, 1): "f5r",
    }


@pytest.fixture
def simple_root_leafs() -> dict[tuple[int, ...], str]:
    return get_simple_root_leafs()


@pytest.fixture(params=get_simple_root_leafs().items(), ids=lambda item: f"{item[0]}->{item[1]}")
def simple_root_leaf_item(request: pytest.FixtureRequest) -> tuple[tuple[int, ...], str]:
    return request.param


@pytest.fixture
def lca_root(simple_root: LayoutNode) -> LayoutNode:
    """Root node with LCA.

    Represents:
        >>> f1l       | f3r       |
        >>> --------- | --------- |
        >>> f2l (30%) | f4r (50%) | f7
        >>> --------- | --------- |
        >>> f6l (70%) | f5r (50%) |
    """
    return {
        "orient": "row",
        "children": (simple_root, "f7"),
        "ratios": (70, 30),
    }
