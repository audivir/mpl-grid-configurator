from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mpl_grid_configurator.register import DRAW_FUNCS, register
from mpl_grid_configurator.render import DEFAULT_DRAW_FUNC, DEFAULT_LEAF

if TYPE_CHECKING:
    import pytest


def draw_svg() -> str:
    return ""


def draw_svg_copy() -> str:
    return ""


def draw_svg_another_copy() -> str:
    return ""


def test_draw_func_registered() -> None:
    assert DEFAULT_LEAF in DRAW_FUNCS
    assert DRAW_FUNCS[DEFAULT_LEAF] == DEFAULT_DRAW_FUNC


draw_svg_copy.__name__ = "draw_svg"
draw_svg_another_copy.__name__ = "draw_svg"


def test_register(reset_draw_funcs: None, caplog: pytest.LogCaptureFixture) -> None:
    del reset_draw_funcs
    register(DEFAULT_DRAW_FUNC)

    with caplog.at_level(logging.WARNING):
        register(DEFAULT_DRAW_FUNC)
    assert f"{DEFAULT_LEAF} is already registered" in caplog.text

    register(draw_svg)

    with caplog.at_level(logging.WARNING):
        register(draw_svg)
    assert "draw_svg is already registered" in caplog.text

    register(draw_svg_copy)
    register(draw_svg_another_copy)

    expected = {
        DEFAULT_LEAF: DEFAULT_DRAW_FUNC,
        "draw_svg": draw_svg,
        "draw_svg_1": draw_svg_copy,
        "draw_svg_2": draw_svg_another_copy,
    }
    assert DRAW_FUNCS == expected  # noqa: SIM300
