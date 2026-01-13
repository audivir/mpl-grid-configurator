from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from test_merge import merge_paths_by_id
from utils import ChangeFixture, assert_figure_equals_layout, render_fig

from mpl_grid_configurator.apply import (
    apply_to_figure,
    apply_to_layout,
    rebuild,
)

if TYPE_CHECKING:
    from pathlib import Path

    from mpl_grid_configurator.types import Layout, LayoutNode, LPath


def test_apply_to_layout(change_fixture: ChangeFixture) -> None:
    pre, post, change, expected_removed = change_fixture
    pre_copy = deepcopy(pre)

    layout, backward, forward_removed = apply_to_layout(pre, [change])

    assert layout == post
    assert forward_removed == [expected_removed]

    if change[0] in ("rotate", "swap"):
        assert backward == [change]
    else:
        assert backward != [change]

    reverse, forward_changes, _ = apply_to_layout(layout, backward)

    assert reverse == pre_copy
    assert forward_changes == [change]


def test_apply_to_figure(
    change_fixture: ChangeFixture, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # just for side effect

    pre, post, change, _ = change_fixture
    root = render_fig(pre)

    _, backward, forward_removed = apply_to_layout(pre, [change])

    root, _ = apply_to_figure(root, [change], forward_removed, {}, lambda svg: svg)  # type: ignore[arg-type]

    assert_figure_equals_layout(root, post, tmp_path)

    if change[0] in ("rotate", "swap"):
        assert backward == [change]
    else:
        assert backward != [change]

    _, _, backward_removed = apply_to_layout(post, backward)

    root, _ = apply_to_figure(root, backward, backward_removed, {}, lambda svg: svg)

    assert_figure_equals_layout(root, pre, tmp_path)


def assert_rebuild(layout: Layout, lca_path: LPath, target_layout: Layout, tmp_path: Path) -> None:
    rebuilt, forward, backward = rebuild(layout, lca_path, target_layout)
    assert rebuilt == target_layout

    rebuilt2, backward2, forward_removed = apply_to_layout(layout, forward)
    assert rebuilt2 == target_layout
    assert backward2 == backward

    backward_rebuilt, forward2, backward_removed = apply_to_layout(target_layout, backward)
    assert forward2 == forward
    assert backward_rebuilt == layout

    forward_fig = render_fig(layout)
    # we do not check for compatibility - as rebuild should not produce incompatible steps
    forward_fig, _ = apply_to_figure(forward_fig, forward, forward_removed, {}, lambda svg: svg)  # type: ignore[arg-type]

    assert_figure_equals_layout(forward_fig, target_layout, tmp_path)

    backward_fig = render_fig(target_layout)
    # we do not check for compatibility - as rebuild should not produce incompatible steps
    backward_fig, _ = apply_to_figure(backward_fig, backward, backward_removed, {}, lambda svg: svg)  # type: ignore[arg-type]
    assert_figure_equals_layout(backward_fig, layout, tmp_path)


def test_rebuild_single_step(
    change_fixture: ChangeFixture, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # just for side effect
    pre, post, _, _ = change_fixture

    assert_rebuild(pre, (), post, tmp_path)


def test_rebuild_merge_simple(
    simple_root: LayoutNode, tmp_path: Path, define_draw_funcs: None
) -> None:
    """Test that rebuilding a mutated tree from the original tree works."""
    del define_draw_funcs  # just for the side effect

    mutated_root, lca_path = merge_paths_by_id(simple_root, "f2l", "f4r")
    assert lca_path == ()

    assert_rebuild(simple_root, lca_path, mutated_root, tmp_path)


def test_rebuild_merge_lca(lca_root: LayoutNode, tmp_path: Path, define_draw_funcs: None) -> None:
    """Test that rebuilding a mutated tree from the original tree works."""
    del define_draw_funcs  # just for the side effect
    mutated_root, lca_path = merge_paths_by_id(lca_root, "f2l", "f4r")
    assert lca_path == (0,)

    assert_rebuild(lca_root, lca_path, mutated_root, tmp_path)
