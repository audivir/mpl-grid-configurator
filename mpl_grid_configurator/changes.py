"""Check for changes in layout binary trees."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from mpl_grid_configurator.merge import almost_equal

if TYPE_CHECKING:
    from mpl_grid_configurator.types import Layout, LayoutNode


def are_nodes_equal(node_a: Layout, node_b: Layout) -> bool:
    """Check if two nodes are equal."""
    if isinstance(node_a, str) or isinstance(node_b, str):
        return node_a == node_b

    return (
        node_a["orient"] == node_b["orient"]
        and almost_equal(node_a["ratios"][0], node_b["ratios"][0])
        and almost_equal(node_a["ratios"][1], node_b["ratios"][1])
        and are_nodes_equal(node_a["children"][0], node_b["children"][0])
        and are_nodes_equal(node_a["children"][1], node_b["children"][1])
    )


class NodeChanges(TypedDict):
    """Stores the changes to a node."""

    full: set[tuple[int, ...]]
    resize: set[tuple[int, ...]]
    swap: set[tuple[int, ...]]


def find_changed_nodes(  # noqa: C901
    prev: LayoutNode | str,
    curr: LayoutNode | str,
    path: tuple[int, ...] = (),
    changes: NodeChanges | None = None,
) -> NodeChanges:
    """Identify if a node was resized, swapped, or changed completely.

    Uses Sets to avoid duplicate path reporting during recursion.
    """
    if changes is None:
        changes = {"full": set(), "resize": set(), "swap": set()}

    # 1. If nodes are identical, no work needed
    if are_nodes_equal(prev, curr):
        return changes

    # 2. If one is a leaf (string) and other is a node, or both are different strings
    if isinstance(prev, str) or isinstance(curr, str):
        if prev != curr:
            # We mark the parent of this leaf as a full change because a child changed type
            if path:
                changes["full"].add(path[:-1])
            else:
                changes["full"].add(())
        return changes

    # 3. Structural Change Check (Orientation or Type Mismatch)
    if prev["orient"] != curr["orient"]:
        changes["full"].add(path)
        return changes

    prev_a, prev_b = prev["children"]
    curr_a, curr_b = curr["children"]

    # are children equal
    if are_nodes_equal(prev_a, curr_a) and are_nodes_equal(prev_b, curr_b):
        if prev["ratios"] != curr["ratios"]:
            changes["resize"].add(path)
        return changes

    # If children are swapped but children themselves are identical to their swapped counterparts
    if are_nodes_equal(prev_a, curr_b) and are_nodes_equal(prev_b, curr_a):
        changes["swap"].add(path)
        return changes

    # If children are structurally the same (same types/orientations) but ratios differ
    ratios_changed = prev["ratios"] != curr["ratios"]

    # Recurse into children to see if they have deep changes
    before_recursion_full = len(changes["full"])
    find_changed_nodes(prev_a, curr_a, (*path, 0), changes)
    find_changed_nodes(prev_b, curr_b, (*path, 1), changes)
    after_recursion_full = len(changes["full"])

    # If children had "Full" changes, this parent effectively has a structural change
    if after_recursion_full > before_recursion_full:
        # Note: Depending on your backend, you might just want the specific child
        # to update, but usually a full child change requires a parent redraw.
        pass
    elif ratios_changed:
        changes["resize"].add(path)

    return changes
