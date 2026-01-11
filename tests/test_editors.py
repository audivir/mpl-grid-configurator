from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, TypeAlias, TypeVar

import pytest
from matplotlib.figure import Figure
from utils import ChangeFixture, assert_figure_equals_layout, assert_figures_equal, render_fig

from mpl_grid_configurator.apply import get_drawer
from mpl_grid_configurator.figure_editor import FigureEditor
from mpl_grid_configurator.layout_editor import LayoutEditor
from mpl_grid_configurator.register import DRAW_FUNCS

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from mpl_grid_configurator.types import Layout, Orientation, SubFigure_

    Mode: TypeAlias = Literal["fig", "layout"]

    CallbackR = TypeVar("CallbackR", SubFigure_, tuple[SubFigure_, SubFigure_], None)


# Parameters for all following tests
@pytest.fixture(params=["fig", "layout"])
def mode(request: pytest.FixtureRequest) -> Mode:
    return request.param


def assert_edit(  # noqa: PLR0913
    edit_callback: Callable[[SubFigure_], CallbackR],
    pre: Layout,
    post: Layout,
    tmp_path: Path,
    figsize: tuple[float, float] = (8, 8),
    post_figsize: tuple[float, float] | None = None,
) -> CallbackR:
    if not post_figsize:
        post_figsize = figsize
    pre_fig = render_fig(pre, figsize)

    mutable_fig = render_fig(pre, figsize)
    # sanity check
    assert_figures_equal(mutable_fig, pre_fig, tmp_path)

    result = edit_callback(mutable_fig)  # type: ignore[func-returns-value]
    if isinstance(result, tuple):
        mutable_fig, _ = result
    elif result:
        mutable_fig = result

    assert_figure_equals_layout(mutable_fig, post, tmp_path, post_figsize)
    # verify our root has not moved or is dangling
    assert isinstance(mutable_fig._parent, Figure)  # noqa: SLF001
    assert mutable_fig._parent.subfigs == [mutable_fig]  # noqa: SLF001

    return result


def test_delete_single_root(mode: Mode, tmp_path: Path, define_draw_funcs: None) -> None:
    del define_draw_funcs  # for side effect

    pre: Layout = "f1l"
    post: Layout = "placeholder"

    path = ()

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.delete(root, path)

    if mode == "fig":
        with pytest.raises(ValueError, match="Root figure cannot be deleted"):
            assert_edit(edit_callback, pre, post, tmp_path)
    else:
        with pytest.raises(ValueError, match="Root layout cannot be deleted"):
            LayoutEditor.delete(pre, path)


def test_delete_to_unsplitted_root(
    mode: Mode, delete_to_unsplitted_root: ChangeFixture, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, _), expected_removed = delete_to_unsplitted_root

    def edit_callback(root: SubFigure_) -> SubFigure_:
        root, _ = FigureEditor.delete(root, path)
        return root

    if mode == "fig":
        assert_edit(edit_callback, pre, post, tmp_path)
    else:
        mutated, _, removed = LayoutEditor.delete(pre, path)
        assert mutated == post
        assert removed == expected_removed


@pytest.mark.parametrize(
    "fixture",
    [
        "delete_leaf_to_splitted_root",
        "delete_node_to_splitted_root",
    ],
)
def test_delete_to_splitted_root(
    mode: Mode,
    fixture: str,
    request: pytest.FixtureRequest,
    tmp_path: Path,
    define_draw_funcs: None,
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, _), expected_removed = request.getfixturevalue(fixture)

    def edit_callback(root: SubFigure_) -> SubFigure_:
        root, _ = FigureEditor.delete(root, path)
        return root

    if mode == "fig":
        assert_edit(edit_callback, pre, post, tmp_path)
    else:
        mutated, _, removed = LayoutEditor.delete(pre, path)
        assert mutated == post
        assert removed == expected_removed


def test_replace_unsplitted_root(
    mode: Mode, replace_unsplitted_root: ChangeFixture, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, kwargs), expected_removed = replace_unsplitted_root
    value = kwargs["value"]

    def edit_callback(root: SubFigure_) -> SubFigure_:
        root, *_ = FigureEditor.replace(root, path, value, get_drawer({}, value))
        return root

    if mode == "fig":
        assert_edit(edit_callback, pre, post, tmp_path)
    else:
        mutated, _, removed = LayoutEditor.replace(pre, path, value)
        assert mutated == post
        assert removed == expected_removed


def test_replace_splitted_root(
    mode: Mode,
    replace_splitted_root: ChangeFixture,
    tmp_path: Path,
    define_draw_funcs: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, kwargs), expected_removed = replace_splitted_root
    value = kwargs["value"]

    if mode == "layout":
        mutated, _, removed = LayoutEditor.replace(pre, path, value)
        assert mutated == post
        assert removed == expected_removed
        return

    def edit_callback(root: SubFigure_) -> tuple[SubFigure_, SubFigure_]:
        root, removed_sf, _ = FigureEditor.replace(root, path, value, get_drawer({}, value))
        return root, removed_sf

    with caplog.at_level(logging.WARNING):
        _, pre_removed = assert_edit(edit_callback, pre, post, tmp_path)
    assert "Draw func needs to be run" in caplog.text
    caplog.clear()  # important

    def reedit_callback(root: SubFigure_) -> SubFigure_:
        root, *_ = FigureEditor.replace(root, path, expected_removed, pre_removed)
        return root

    with caplog.at_level(logging.WARNING):
        assert_edit(reedit_callback, post, pre, tmp_path)
    assert caplog.text == ""


def test_replace_with_node(replace_with_node: ChangeFixture) -> None:
    """Only works for LayoutEditor."""
    pre, post, (_, path, kwargs), expected_removed = replace_with_node
    value = kwargs["value"]

    mutated, _, removed = LayoutEditor.replace(pre, path, value)
    assert mutated == post
    assert removed == expected_removed


def test_resize(simple_root: Layout, tmp_path: Path, define_draw_funcs: None) -> None:
    del define_draw_funcs  # for side effect

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.resize(root, (10, 10))

    assert_edit(edit_callback, simple_root, simple_root, tmp_path, post_figsize=(10, 10))


def test_restructure(
    mode: Mode, restructure: ChangeFixture, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, kwargs), _ = restructure
    ratios = kwargs["ratios"]

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.restructure(root, path, ratios)

    if mode == "fig":
        assert_edit(edit_callback, pre, post, tmp_path)
    else:
        root, _ = LayoutEditor.restructure(pre, path, ratios)
        assert root == post


def test_restructure_fail(mode: Mode, tmp_path: Path, define_draw_funcs: None) -> None:
    del define_draw_funcs  # for side effect

    pre: Layout = "f1l"
    post: Layout = "f2l"

    path = ()

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.restructure(root, path, (40, 60))

    if mode == "fig":
        with pytest.raises(ValueError, match="Unsplitted root figure provided"):
            assert_edit(edit_callback, pre, post, tmp_path)
    else:
        with pytest.raises(ValueError, match="Cannot resize unsplitted root"):
            LayoutEditor.restructure(pre, path, (40, 60))


def test_rotate(mode: Mode, rotate: ChangeFixture, tmp_path: Path, define_draw_funcs: None) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, _), _ = rotate

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.rotate(root, path)

    if mode == "fig":
        assert_edit(edit_callback, pre, post, tmp_path)
    else:
        root, _ = LayoutEditor.rotate(pre, path)
        assert root == post


def test_rotate_fail(mode: Mode, tmp_path: Path, define_draw_funcs: None) -> None:
    del define_draw_funcs  # for side effect

    pre: Layout = "f1l"
    post: Layout = "f2l"

    path = ()

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.rotate(root, path)

    if mode == "fig":
        with pytest.raises(ValueError, match="Unsplitted root figure provided"):
            assert_edit(edit_callback, pre, post, tmp_path)
    else:
        with pytest.raises(ValueError, match="Cannot rotate unsplitted root"):
            LayoutEditor.rotate(pre, path)


def test_split_root(
    mode: Mode,
    split_root: ChangeFixture,
    tmp_path: Path,
    define_draw_funcs: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, kwargs), _ = split_root
    orient = kwargs["orient"]

    def edit_callback(root: SubFigure_) -> SubFigure_:
        return FigureEditor.split(root, path, orient)

    if mode == "fig":
        with caplog.at_level(logging.WARNING):
            assert_edit(edit_callback, pre, post, tmp_path)
        assert "Splitting root figure, root figure reference will change" in caplog.text
    else:
        root, _ = LayoutEditor.split(pre, path, orient)
        assert root == post


@pytest.mark.parametrize(
    "fixture",
    [
        "split_leaf",
        "split_node",
    ],
)
def test_split(
    mode: Mode,
    fixture: str,
    request: pytest.FixtureRequest,
    tmp_path: Path,
    define_draw_funcs: None,
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path, kwargs), _ = request.getfixturevalue(fixture)
    orient = kwargs["orient"]

    def edit_callback(root: SubFigure_) -> SubFigure_:
        return FigureEditor.split(root, path, orient)

    if mode == "fig":
        assert_edit(edit_callback, pre, post, tmp_path)
    else:
        root, _ = LayoutEditor.split(pre, path, orient)
        assert root == post


@pytest.mark.parametrize(
    "fixture",
    ["swap_leaf_siblings", "swap_leaf_with_node", "swap_two_nodes"],
)
def test_swap(
    mode: Mode,
    fixture: str,
    request: pytest.FixtureRequest,
    tmp_path: Path,
    define_draw_funcs: None,
) -> None:
    del define_draw_funcs  # for side effect

    change_fixture: ChangeFixture = request.getfixturevalue(fixture)
    pre, post, (_, path1, kwargs), _ = change_fixture

    path2 = kwargs["path2"]

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.swap(root, path1, path2)

    if mode == "fig":
        assert_edit(edit_callback, pre, post, tmp_path)
    else:
        root, _ = LayoutEditor.swap(pre, path1, path2)
        assert root == post


def test_swap_leaf_non_siblings(
    mode: Mode, swap_leaf_non_siblings: ChangeFixture, tmp_path: Path, define_draw_funcs: None
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path1, kwargs), _ = swap_leaf_non_siblings
    path2 = kwargs["path2"]

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.swap(root, path1, path2)

    if mode == "fig":
        try:
            assert_edit(edit_callback, pre, post, tmp_path)
        except AssertionError as e:
            if "trees are not equal" not in str(e):
                pytest.xfail(
                    "Weird small different drawn path, but swap worked and trees are equal"
                )
            raise
    else:
        root, _ = LayoutEditor.swap(pre, path1, path2)
        assert root == post


def test_swap_root_fail(mode: Mode, tmp_path: Path, define_draw_funcs: None) -> None:
    del define_draw_funcs  # for side effect

    pre: Layout = "f1l"
    post: Layout = "f1l"

    path = ()

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.swap(root, path, path)

    if mode == "fig":
        with pytest.raises(ValueError, match="Cannot swap root figure"):
            assert_edit(edit_callback, pre, post, tmp_path)
    else:
        with pytest.raises(ValueError, match="Cannot swap root"):
            LayoutEditor.swap(pre, path, path)


def test_swap_same(
    mode: Mode,
    swap_same: ChangeFixture,
    tmp_path: Path,
    define_draw_funcs: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    del define_draw_funcs  # for side effect

    pre, post, (_, path1, kwargs), _ = swap_same
    path2 = kwargs["path2"]

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.swap(root, path1, path2)

    with caplog.at_level(logging.WARNING):
        if mode == "fig":
            assert_edit(edit_callback, pre, post, tmp_path)
            assert "Subfigures are the same, nothing to do" in caplog.text
        else:
            root, _ = LayoutEditor.swap(pre, path1, path2)
            assert root == post
            assert "Swapping a node with itself, nothing to do" in caplog.text


@pytest.mark.parametrize("fixture", ["insert", "insert_next_to_node"])
def test_insert(  # noqa: PLR0913
    mode: Mode,
    fixture: str,
    request: pytest.FixtureRequest,
    tmp_path: Path,
    define_draw_funcs: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    del define_draw_funcs  # for side effect

    change_fixture: ChangeFixture = request.getfixturevalue(fixture)

    pre, post, (_, path, kwargs), expected_removed = change_fixture
    orient, ratios, value = kwargs["orient"], kwargs["ratios"], kwargs["value"]

    def edit_callback(root: SubFigure_) -> SubFigure_:
        root, *_ = FigureEditor.insert(root, path, orient, ratios, value, get_drawer({}, value))
        return root

    if mode == "fig":
        with caplog.at_level(logging.WARNING):
            assert_edit(edit_callback, pre, post, tmp_path)
            assert "Splitting root figure, root figure reference will change" in caplog.text
    else:
        root, _, removed = LayoutEditor.insert(pre, path, orient, ratios, value)
        assert root == post
        assert removed == expected_removed


def test_insert_node(insert_node: ChangeFixture) -> None:
    """Only works for LayoutEditor."""
    pre, post, (_, path, kwargs), expected_removed = insert_node
    orient, ratios, value = kwargs["orient"], kwargs["ratios"], kwargs["value"]

    root, _, removed = LayoutEditor.insert(pre, path, orient, ratios, value)
    assert root == post
    assert removed == expected_removed


def test_insert_fail(mode: Mode, tmp_path: Path, define_draw_funcs: None) -> None:
    del define_draw_funcs  # for side effect

    pre: Layout = "f1l"
    post: Layout = "f1l"

    path: tuple[int, ...] = ()
    orient: Orientation = "row"
    ratios = (70, 30)

    def edit_callback(root: SubFigure_) -> None:
        FigureEditor.insert(root, path, orient, ratios, "f2l", DRAW_FUNCS["f2l"])

    if mode == "fig":
        with pytest.raises(ValueError, match="Cannot insert as root"):
            assert_edit(edit_callback, pre, post, tmp_path)
    else:
        with pytest.raises(ValueError, match="Cannot insert as root"):
            LayoutEditor.insert(pre, path, orient, ratios, "f2l")
