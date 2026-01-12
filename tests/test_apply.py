from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import pytest
from test_merge import merge_paths_by_id
from utils import ChangeFixture, assert_figure_equals_layout, render_fig

from mpl_grid_configurator.apply import apply_to_figure, apply_to_layout, is_compatible, rebuild

if TYPE_CHECKING:
    from pathlib import Path

    from mpl_grid_configurator.types import Layout, LayoutNode, LPath


FIXTURES = [
    "delete_to_unsplitted_root",
    "delete_leaf_to_splitted_root",
    "delete_node_to_splitted_root",
    "replace_unsplitted_root",
    "replace_splitted_root",
    "replace_with_node",
    "restructure",
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
    # "insert_node",
]


@pytest.mark.parametrize("fixture", FIXTURES)
def test_apply_to_layout(fixture: str, request: pytest.FixtureRequest) -> None:
    change_fixture: ChangeFixture = request.getfixturevalue(fixture)

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


@pytest.mark.parametrize("fixture", FIXTURES)
def test_apply_to_figure(
    fixture: str, request: pytest.FixtureRequest, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # just for side effect
    change_fixture: ChangeFixture = request.getfixturevalue(fixture)

    pre, post, change, _ = change_fixture
    pre_copy = deepcopy(pre)
    root = render_fig(pre)

    _, backward, layout_removed = apply_to_layout(pre, [change])

    changes_compatible, compatible_removed = is_compatible([change], layout_removed)

    if not changes_compatible or compatible_removed is None:
        with pytest.raises(ValueError, match=r"Cannot .* in figures"):
            apply_to_figure(root, [change], layout_removed, {}, lambda svg: svg)  # type: ignore[arg-type]
        return

    root, _ = apply_to_figure(root, [change], compatible_removed, {}, lambda svg: svg)

    assert_figure_equals_layout(root, post, tmp_path)

    if change[0] in ("rotate", "swap"):
        assert backward == [change]
    else:
        assert backward != [change]

    _, _, backward_removed = apply_to_layout(post, backward)

    changes_compatible, compatible_removed = is_compatible(backward, backward_removed)
    assert changes_compatible
    assert compatible_removed is not None

    root, _ = apply_to_figure(root, backward, compatible_removed, {}, lambda svg: svg)

    assert_figure_equals_layout(root, pre_copy, tmp_path)


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


@pytest.mark.parametrize("fixture", FIXTURES)
def test_rebuild_single_step(
    fixture: str, request: pytest.FixtureRequest, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # just for side effect
    change_fixture: ChangeFixture = request.getfixturevalue(fixture)

    pre, post, _, _ = change_fixture

    try:
        assert_rebuild(pre, (), post, tmp_path)
    except ValueError as e:
        if fixture == "delete_node_to_splitted_root" and e.args == (
            "Cannot remove nodes in figures",
        ):
            pytest.xfail("delete nodes in figure currently not supported")
        raise


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
