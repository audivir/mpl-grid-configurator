from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from matplotlib.axes import Axes

from mpl_grid_configurator.types import (
    Edge,
    get_n_params,
    get_return_type,
    is_str_draw_func,
    is_tuple_draw_func,
)

if TYPE_CHECKING:
    from matplotlib.figure import Figure, SubFigure

    from mpl_grid_configurator.types import DrawFunc


def tuple_draw_func(fig: Figure | SubFigure) -> tuple[Axes, str]:
    return fig.add_subplot(), "test"


def axes_draw_func(fig: Figure | SubFigure) -> Axes:
    return fig.add_subplot()


def str_draw_func() -> str:
    return ""


def test_edge() -> None:
    min_val, max_val = 0.5, 1.5
    edge = Edge(min_val, max_val)

    assert edge.min == min_val
    assert edge.max == max_val
    assert edge.size == max_val - min_val
    unpack_min, unpack_max = edge
    assert unpack_min == min_val
    assert unpack_max == max_val


@pytest.mark.parametrize(
    ("func", "expected"),
    [
        (tuple_draw_func, True),
        (axes_draw_func, False),
        (str_draw_func, False),
    ],
)
def test_is_tuple_draw_func(func: DrawFunc, expected: bool) -> None:
    assert is_tuple_draw_func(func) == expected


@pytest.mark.parametrize(
    ("func", "expected"),
    [
        (tuple_draw_func, False),
        (axes_draw_func, False),
        (str_draw_func, True),
    ],
)
def test_is_str_draw_func(func: DrawFunc, expected: bool) -> None:
    assert is_str_draw_func(func) == expected


@pytest.mark.parametrize(
    ("func", "expected"),
    [
        (tuple_draw_func, tuple[Axes, str]),
        (axes_draw_func, Axes),
        (str_draw_func, str),
    ],
)
def test_return_type(func: DrawFunc, expected: type) -> None:
    assert get_return_type(func) == expected


@pytest.mark.parametrize(
    ("func", "expected"),
    [
        (tuple_draw_func, 1),
        (axes_draw_func, 1),
        (str_draw_func, 0),
    ],
)
def test_get_n_params(func: DrawFunc, expected: int) -> None:
    assert get_n_params(func) == expected
