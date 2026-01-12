"""Check for changes in layout binary trees."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_grid_configurator.apply import apply_to_figure, apply_to_layout, rebuild
from mpl_grid_configurator.merge import merge_paths

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping

    from mpl_grid_configurator.types import (
        Change,
        Layout,
        LPath,
        SubFigure_,
    )


def merge(  # noqa: PLR0913
    layout: Layout,
    root: SubFigure_,
    path1: LPath,
    path2: LPath,
    subfigs: MutableMapping[str, list[SubFigure_]],
    svg_callback: Callable[[str], str],
) -> tuple[Layout, SubFigure_, list[Change], Callable[[str], str]]:
    """Merge two non-sibling nodes to a new parent."""
    if isinstance(layout, str):
        raise ValueError("Cannot merge root")  # noqa: TRY004

    target_layout, lca_path = merge_paths(layout, path1, path2)
    rebuilt, forward, backward = rebuild(layout, lca_path, target_layout)
    rebuilt2, backward2, forward_removed = apply_to_layout(layout, forward)
    if rebuilt != rebuilt2 != target_layout or backward != backward2:
        raise ValueError("Rebuilding failed")
    # we do not check for compatibility - as rebuild should not produce incompatible steps
    root, svg_callback = apply_to_figure(
        root,
        forward,
        forward_removed,  # type: ignore[arg-type]
        subfigs,
        svg_callback,
    )

    return target_layout, root, backward, svg_callback


def unmerge(
    layout: Layout,
    root: SubFigure_,
    inverse: list[Change],
    subfigs: MutableMapping[str, list[SubFigure_]],
    svg_callback: Callable[[str], str],
) -> tuple[Layout, SubFigure_, Callable[[str], str]]:
    """Undo a previous merge."""
    layout, _, forward_removed = apply_to_layout(layout, inverse)
    # we do not check for compatibility - as rebuild should not produce incompatible steps
    root, svg_callback = apply_to_figure(
        root,
        inverse,
        forward_removed,  # type: ignore[arg-type]
        subfigs,
        svg_callback,
    )
    return layout, root, svg_callback


# ruff: noqa: ERA001
# TODO(tihoph): static type arguments for Change?
# class DeleteKwargs(TypedDict):
#     path: LPath


# class InsertKwargs(TypedDict):
#     path: LPath
#     orient: Orient
#     ratios: Ratios
#     value: str


# class ReplaceKwargs(TypedDict):
#     path: LPath
#     value: str


# class RestructureKwargs(TypedDict):
#     path: LPath
#     ratios: Ratios


# class RotateKwargs(TypedDict):
#     path: LPath


# class SplitKwargs(TypedDict):
#     path: LPath
#     orient: Orient


# Change: TypeAlias = (
#     tuple[Literal["delete"], DeleteKwargs]
#     | tuple[Literal["insert"], InsertKwargs]
#     | tuple[Literal["replace"], ReplaceKwargs]
#     | tuple[Literal["restructure"], RestructureKwargs]
#     | tuple[Literal["rotate"], RotateKwargs]
#     | tuple[Literal["split"], SplitKwargs]
# )
