from __future__ import annotations

import re
from typing import TYPE_CHECKING

from matplotlib.figure import Figure, SubFigure
from utils import assert_files_equal

from mpl_grid_configurator.render import draw_empty, new_root, render_svg, savefig, split_figure

if TYPE_CHECKING:
    from pathlib import Path


def test_new_root() -> None:
    fig, root = new_root()
    assert not fig.patch.get_visible()
    assert not root.patch.get_visible()

    assert isinstance(fig, Figure)
    assert isinstance(root, SubFigure)


def test_split_figure_row() -> None:
    _, root = new_root()
    sf1, sf2 = split_figure(root, "row", (50, 50))
    assert not sf1.patch.get_visible()
    assert not sf2.patch.get_visible()

    gs = sf1._subplotspec.get_gridspec()  # type: ignore[attr-defined] # noqa: SLF001
    assert gs._nrows == 1  # type: ignore[attr-defined] # noqa: SLF001
    assert gs._ncols == 2  # type: ignore[attr-defined] # noqa: SLF001,PLR2004
    assert gs.get_width_ratios() == (50, 50)
    assert gs.get_height_ratios() == [1]


def test_split_figure_column() -> None:
    _, root = new_root()
    sf1, sf2 = split_figure(root, "column", (50, 50))
    assert not sf1.patch.get_visible()
    assert not sf2.patch.get_visible()

    gs = sf1._subplotspec.get_gridspec()  # type: ignore[attr-defined] # noqa: SLF001
    assert gs._nrows == 2  # type: ignore[attr-defined] # noqa: SLF001,PLR2004
    assert gs._ncols == 1  # type: ignore[attr-defined] # noqa: SLF001
    assert gs.get_width_ratios() == [1]
    assert gs.get_height_ratios() == (50, 50)


# TODO(tihoph): run_draw_func
# TODO(tihoph): render_recursive
# TODO(tihoph): render_layout


def test_render_svg(tmp_path: Path) -> None:
    fig, _ = new_root()
    fig.patch.set_visible(False)
    fig.add_subplot()

    fig.savefig(tmp_path / "fig.svg")
    expected = (tmp_path / "fig.svg").read_text()

    # replace all xlink:href="#...." with xlink:href="#"
    # replace <dc:date> ... </dc:date> with ""
    def clean_references(svg: str) -> str:
        svg = re.sub(r'xlink:href="#\w+"', 'xlink:href="#"', svg)
        svg = re.sub(r'path id="\w+"', 'path id="#"', svg)
        return re.sub(r"<dc:date>.*?</dc:date>", "", svg)

    assert render_svg(fig, clean_references) == clean_references(expected)

    def make_empty(_: str) -> str:
        return ""

    assert render_svg(fig, make_empty) == ""


def test_draw_empty() -> None:
    _, root = new_root()
    draw_empty(root)
    assert (
        ' <g id="figure_1">\n  <g id="subfigure_1">\n   <g id="axes_1"/>\n  </g>\n </g>'
        in render_svg(root, lambda svg: svg)
    )


def test_savefig(tmp_path: Path) -> None:
    fig, root = new_root()
    savefig(fig, tmp_path / "fig.png")
    savefig(root, tmp_path / "sf.png")
    assert_files_equal(tmp_path / "fig.png", tmp_path / "sf.png")
