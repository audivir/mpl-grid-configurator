from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

from mpl_grid_configurator.debug import build_fig_tree
from mpl_grid_configurator.register import DRAW_FUNCS
from mpl_grid_configurator.render import render_layout, savefig

if TYPE_CHECKING:
    from _typeshed import StrPath

    from mpl_grid_configurator.apply import Change
    from mpl_grid_configurator.types import Layout, SubFigure_

ChangeFixture: TypeAlias = "tuple[Layout, Layout, Change, Any]"


def assert_files_equal(file1: StrPath, file2: StrPath) -> None:
    """Assert that two files are equal by comparing their SHA256 hash."""
    assert (
        hashlib.sha256(Path(file1).read_bytes()).hexdigest()
        == hashlib.sha256(Path(file2).read_bytes()).hexdigest()
    )


def assert_figures_equal(fig1: SubFigure_, fig2: SubFigure_, tmp_path: Path) -> None:
    """Assert that two figures are equal by comparing their tree and their PNG representation."""
    # assert that the element structure is exactly the same
    tree1 = build_fig_tree(fig1)
    tree2 = build_fig_tree(fig2)
    assert tree1 == tree2, "trees are not equal"

    # assert that the visuals are exactly the same
    file1 = tmp_path / f"{uuid.uuid4()}.png"
    savefig(fig1, file1)
    file2 = tmp_path / f"{uuid.uuid4()}.png"
    savefig(fig2, file2)
    try:
        assert_files_equal(file1, file2)
    except AssertionError:
        savefig(fig1, file1.with_suffix(".svg"))
        savefig(fig2, file2.with_suffix(".svg"))
        print("diff", file1.with_suffix(".svg"), file2.with_suffix(".svg"))  # noqa: T201
        raise


def assert_figure_equals_layout(
    fig_to_compare: SubFigure_,
    layout_to_compare_to: Layout,
    tmp_path: Path,
    figsize: tuple[float, float] = (8, 8),
) -> None:
    file1 = tmp_path / f"{uuid.uuid4()}.png"
    savefig(fig_to_compare, file1)
    fig2 = render_fig(layout_to_compare_to, figsize)

    assert_figures_equal(fig_to_compare, fig2, tmp_path)


def render_fig(root: Layout, figsize: tuple[float, float] = (8, 8)) -> SubFigure_:
    fig, _ = render_layout(root, figsize, DRAW_FUNCS)
    return fig
