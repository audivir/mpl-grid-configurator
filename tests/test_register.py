from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mpl_grid_configurator.register import DRAW_FUNCS, register
from mpl_grid_configurator.render import draw_empty

if TYPE_CHECKING:
    import pytest


def draw_svg() -> str:
    return ""


def draw_svg_copy() -> str:
    return ""


def draw_svg_another_copy() -> str:
    return ""


def test_draw_empty_registered() -> None:
    assert "draw_empty" in DRAW_FUNCS
    assert DRAW_FUNCS["draw_empty"] == draw_empty


draw_svg_copy.__name__ = "draw_svg"
draw_svg_another_copy.__name__ = "draw_svg"


def test_register(reset_draw_funcs: None, caplog: pytest.LogCaptureFixture) -> None:
    del reset_draw_funcs
    register(draw_empty)

    with caplog.at_level(logging.WARNING):
        register(draw_empty)
    assert "draw_empty is already registered" in caplog.text

    register(draw_svg)

    with caplog.at_level(logging.WARNING):
        register(draw_svg)
    assert "draw_svg is already registered" in caplog.text

    register(draw_svg_copy)
    register(draw_svg_another_copy)

    expected = {
        "draw_empty": draw_empty,
        "draw_svg": draw_svg,
        "draw_svg_1": draw_svg_copy,
        "draw_svg_2": draw_svg_another_copy,
    }
    assert DRAW_FUNCS == expected  # noqa: SIM300
