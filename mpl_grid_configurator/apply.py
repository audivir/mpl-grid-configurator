"""Apply edits and rebuild tree."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING

from mpl_grid_configurator.figure_editor import FigureEditor
from mpl_grid_configurator.layout_editor import LayoutEditor
from mpl_grid_configurator.register import DRAW_FUNCS
from mpl_grid_configurator.traverse import almost_equal, assert_node, get_at, get_node

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping, Sequence

    from mpl_grid_configurator.types import Change, DrawFunc, Layout, LPath, SubFigure_

logger = logging.getLogger(__name__)


def wrap_svg_callback(
    prev: Callable[[str], str], curr: Callable[[str], str]
) -> Callable[[str], str]:
    """Wrap a svg callback to apply a new callback on top of an existing one."""

    def wrapped_svg_callback(value: str) -> str:
        return curr(prev(value))

    return wrapped_svg_callback


def is_compatible(
    changes: Sequence[Change], layout_removed: Sequence[Layout | None]
) -> tuple[bool, list[str | None] | None]:
    """Check if the removed elements are compatible for applying to the figure."""
    changes_compatible = True
    for _, _, kwargs in changes:
        if "value" in kwargs and not isinstance(kwargs["value"], str):
            changes_compatible = False

    compatible_removed: list[str | None] = []

    for elem in layout_removed:
        if elem and not isinstance(elem, str):
            return changes_compatible, None
        compatible_removed.append(elem)
    return changes_compatible, compatible_removed


def get_drawer(subfigs: MutableMapping[str, list[SubFigure_]], value: str) -> DrawFunc | SubFigure_:
    """Get a cached drawer or create a new one from the registry."""
    cache = subfigs.get(value, [])
    logger.warning("Cache size for %s: %d", value, len(cache))
    if not cache:
        return DRAW_FUNCS[value]
    return cache.pop()


def apply_to_layout(
    layout: Layout,
    changes: Sequence[Change],
) -> tuple[Layout, list[Change], list[Layout | None]]:
    """Apply a list of changes to a layout. Does not mutate the input."""
    layout = deepcopy(layout)

    backward: list[Change] = []
    removed_elems: list[Layout | None] = []

    for key, path, kwargs in changes:
        removed: Layout | None = None
        match key:
            case "delete":
                layout, inverse, removed = LayoutEditor.delete(layout, path)
            case "insert":
                layout, inverse, removed = LayoutEditor.insert(layout, path, **kwargs)
            case "replace":
                layout, inverse, removed = LayoutEditor.replace(layout, path, **kwargs)
            case "restructure":
                layout, inverse = LayoutEditor.restructure(layout, path, **kwargs)
            case "rotate":
                layout, inverse = LayoutEditor.rotate(layout, path)
            case "split":
                layout, inverse = LayoutEditor.split(layout, path, **kwargs)
            case "swap":
                layout, inverse = LayoutEditor.swap(layout, path, **kwargs)
            case _:
                raise ValueError(f"Unknown change type: {key}")
        backward.append(inverse)
        removed_elems.append(removed)

    return layout, backward[::-1], removed_elems


def apply_to_figure(  # noqa: C901,PLR0912
    root: SubFigure_,
    changes: Sequence[Change],
    layout_removed: Sequence[str | None],
    subfigs: MutableMapping[str, list[SubFigure_]],
    svg_callback: Callable[[str], str],
) -> tuple[SubFigure_, Callable[[str], str]]:
    """Apply a list of changes to a figure."""
    for (key, path, kwargs), removed in zip(changes, layout_removed, strict=True):
        if removed and not isinstance(removed, str):
            raise ValueError("Cannot remove nodes in figures")
        match key:
            case "delete":
                root, removed_sf = FigureEditor.delete(root, path)
                if removed:
                    subfigs.setdefault(removed, []).append(removed_sf)
            case "insert":
                value = kwargs["value"]
                if not isinstance(value, str):
                    raise ValueError("Cannot insert nodes in figures")  # noqa: TRY004
                drawer = get_drawer(subfigs, value)
                root, removed_sf, curr_svg_callback = FigureEditor.insert(
                    root, path, drawer=drawer, **kwargs
                )
                if removed:
                    subfigs.setdefault(removed, []).append(removed_sf)
                svg_callback = wrap_svg_callback(svg_callback, curr_svg_callback)
            case "replace":
                value = kwargs["value"]
                if not isinstance(value, str):
                    raise ValueError("Cannot replace elements with nodes in figures")  # noqa: TRY004
                drawer = get_drawer(subfigs, value)
                root, removed_sf, curr_svg_callback = FigureEditor.replace(
                    root, path, drawer=drawer, **kwargs
                )
                if removed:
                    subfigs.setdefault(removed, []).append(removed_sf)
                svg_callback = wrap_svg_callback(svg_callback, curr_svg_callback)
            case "restructure":
                FigureEditor.restructure(root, path, **kwargs)
            case "rotate":
                FigureEditor.rotate(root, path)
            case "split":
                root = FigureEditor.split(root, path, **kwargs)
            case "swap":
                FigureEditor.swap(root, path, **kwargs)
            case _:
                raise ValueError(f"Unknown change type: {key}")

    return root, svg_callback


def rebuild(
    layout: Layout,
    lca_path: LPath,
    target_layout: Layout,
) -> tuple[Layout, list[Change], list[Change]]:
    """Rebuild the tree by removing the LCA and its children and then adding the new layout.

    Does not mutate the input node.
    """
    # possible ideas to optimize this:
    # * do not just compare leafs, but whole trees if they were swapped somewhere else,
    # so we do not have to rebuilt them later

    forward: list[Change] = []
    backward: list[Change] = []

    def add_step(layout: Layout, forward_step: Change) -> Layout:
        layout, (backward_step,), _ = apply_to_layout(layout, [forward_step])
        forward.append(forward_step)
        backward.append(backward_step)
        return layout

    def recursive_rebuild(
        layout: Layout, elem: Layout, target_elem: Layout, curr_path: LPath
    ) -> Layout:
        if isinstance(elem, str):
            if isinstance(target_elem, str):
                if elem == target_elem:
                    # we're finished for this leaf
                    return layout
                # replace elem with new_layout_here
                return add_step(layout, ("replace", curr_path, {"value": target_elem}))
            # split elem in target direction
            layout = add_step(layout, ("split", curr_path, {"orient": target_elem["orient"]}))
            # update elem
            elem = get_node(assert_node(layout), curr_path)
        elif isinstance(target_elem, str):
            # delete child2
            layout = add_step(layout, ("delete", (*curr_path, 1), {}))
            # update elem if is not correct yet
            elem = get_at(layout, curr_path)
            if elem == target_elem:
                return layout
            return add_step(layout, ("replace", curr_path, {"value": target_elem}))
        # rotate if necessary
        if elem["orient"] != target_elem["orient"]:
            layout = add_step(layout, ("rotate", curr_path, {}))

        # adjust the split ratio if necessary
        if not almost_equal(elem["ratios"][0], target_elem["ratios"][0]) or not almost_equal(
            elem["ratios"][1], target_elem["ratios"][1]
        ):
            layout = add_step(layout, ("restructure", curr_path, {"ratios": target_elem["ratios"]}))

        child1, child2 = elem["children"]
        target1, target2 = target_elem["children"]

        layout = recursive_rebuild(layout, child1, target1, (*curr_path, 0))
        return recursive_rebuild(layout, child2, target2, (*curr_path, 1))

    layout = deepcopy(layout)

    start_elem = get_node(assert_node(layout), lca_path) if lca_path else layout
    start_target = get_node(assert_node(target_layout), lca_path) if lca_path else target_layout

    layout = recursive_rebuild(layout, start_elem, start_target, lca_path)

    return layout, forward, backward[::-1]
