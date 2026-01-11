"""Edit a layout tree."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from mpl_grid_configurator.traverse import (
    almost_equal,
    get_at,
    get_node,
    set_node,
)

if TYPE_CHECKING:
    from mpl_grid_configurator.types import (
        Change,
        Layout,
        LayoutNode,
        LayoutT,
        Orientation,
    )


logger = logging.getLogger(__name__)


class LayoutEditor:
    """Layout editor. Methods currently mutate the layout."""

    @staticmethod
    def delete(layout: Layout, path: tuple[int, ...]) -> tuple[Layout, Change, Layout]:
        """Delete a leaf from the layout.

        Returns:
            A tuple with the new layout and the deleted node/leaf.
        """
        if isinstance(layout, str) or not path:
            raise ValueError("Root layout cannot be deleted")
        parent_path = path[:-1]
        curr_ix = path[-1]
        sibling_ix = 1 - curr_ix

        parent = get_node(layout, parent_path)
        removed = get_at(parent, (curr_ix,))
        sibling = parent["children"][sibling_ix]

        if curr_ix == 1 and parent["ratios"] == (50, 50) and removed == "draw_empty":
            backward: Change = (
                "split",
                parent_path,
                {"orient": parent["orient"]},
            )
        else:
            backward = (
                "insert",
                path,
                {"orient": parent["orient"], "ratios": parent["ratios"], "value": removed},
            )

        if not parent_path:
            return sibling, backward, removed

        grandpa_path = parent_path[:-1]
        grandpa_node = get_node(layout, grandpa_path)
        children = grandpa_node["children"]

        if parent_path[-1]:
            grandpa_node["children"] = (children[0], sibling)
        else:
            grandpa_node["children"] = (sibling, children[1])

        return layout, backward, removed

    @classmethod
    def insert(
        cls,
        layout: Layout,
        path: tuple[int, ...],
        orient: Orientation,
        ratios: tuple[float, float],
        value: Layout,
    ) -> tuple[Layout, Change, Literal["draw_empty"]]:
        """Prepare the layout and figure for an insert."""
        if not path:
            raise ValueError("Cannot insert as root")

        parent_path = path[:-1]
        curr_ix = path[-1]

        layout, _ = cls.split(layout, parent_path, orient)
        layout, _ = cls.restructure(layout, parent_path, ratios)

        if curr_ix == 0:
            layout, _ = cls.swap(layout, (*parent_path, 0), (*parent_path, 1))

        layout, _, _ = cls.replace(layout, path, value)  # type: ignore[type-var]
        return layout, ("delete", path, {}), "draw_empty"

    @staticmethod
    def replace(
        layout: Layout,
        path: tuple[int, ...],
        value: LayoutT,
    ) -> tuple[Layout, Change, Layout]:
        """Replace a leaf in the layout only.

        Returns:
            A tuple with the new layout and the replaced node/leaf.
        """
        removed = get_at(layout, path)
        layout = set_node(layout, path, value)
        if value == removed:
            raise ValueError("Replaced with same content")
        backward: Change = ("replace", path, {"value": removed})
        return layout, backward, removed

    @staticmethod
    def restructure(
        layout: Layout, path: tuple[int, ...], ratios: tuple[float, float]
    ) -> tuple[Layout, Change]:
        """Restructure a node."""
        if isinstance(layout, str):
            raise ValueError("Cannot resize unsplitted root")  # noqa: TRY004

        node = get_node(layout, path)
        prev = node["ratios"]
        if almost_equal(prev[0], ratios[0]) and almost_equal(prev[1], ratios[1]):
            raise ValueError("No or too small ratios change")

        node["ratios"] = ratios

        return set_node(layout, path, node), ("restructure", path, {"ratios": prev})

    @staticmethod
    def rotate(layout: Layout, path: tuple[int, ...]) -> tuple[Layout, Change]:
        """Rotate a node."""
        if isinstance(layout, str):
            raise ValueError("Cannot rotate unsplitted root")  # noqa: TRY004

        node = get_node(layout, path)
        node["orient"] = "column" if node["orient"] == "row" else "row"

        return set_node(layout, path, node), ("rotate", path, {})

    @staticmethod
    def split(layout: Layout, path: tuple[int, ...], orient: Orientation) -> tuple[Layout, Change]:
        """Split a leaf into two leaves."""
        elem = get_at(layout, path)
        new_node: LayoutNode = {
            "orient": orient,
            "children": (elem, "draw_empty"),
            "ratios": (50, 50),
        }

        return set_node(layout, path, new_node), ("delete", (*path, 1), {})

    @staticmethod
    def swap(
        layout: Layout, path1: tuple[int, ...], path2: tuple[int, ...]
    ) -> tuple[Layout, Change]:
        """Swap two elements in the layout."""
        if isinstance(layout, str):
            raise ValueError("Cannot swap root")  # noqa: TRY004
        backward: Change = "swap", path1, {"path2": path2}
        if path1 == path2:
            logger.warning("Swapping a node with itself, nothing to do")
            return layout, backward
        elem1 = get_at(layout, path1)
        elem2 = get_at(layout, path2)

        layout = set_node(layout, path1, elem2)
        return set_node(layout, path2, elem1), backward
