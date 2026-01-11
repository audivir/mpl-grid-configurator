from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from mpl_grid_configurator.changes import are_nodes_equal
from mpl_grid_configurator.debug import (
    are_bbox_mappings_equal,
    are_siblings,
)
from mpl_grid_configurator.merge import find_path_by_id, get_bbox_mapping, merge_paths

if TYPE_CHECKING:
    from mpl_grid_configurator.types import LayoutNode


def assert_layout_equal(root: LayoutNode, mutated_root: LayoutNode) -> None:
    orig_bbox_mapping = get_bbox_mapping(root)
    mutated_bbox_mapping = get_bbox_mapping(mutated_root)
    assert are_bbox_mappings_equal(orig_bbox_mapping, mutated_bbox_mapping)


def merge_paths_by_id(root: LayoutNode, id_a: str, id_b: str) -> LayoutNode:
    root_copy = deepcopy(root)
    path_a = find_path_by_id(root, id_a, use_full_id=True)
    path_b = find_path_by_id(root, id_b, use_full_id=True)
    if path_a is None or path_b is None:
        raise ValueError("Node not found")
    assert path_a[:-1] != path_b[:-1], "Nodes are already siblings"
    mutated_root = merge_paths(root, path_a, path_b)
    assert are_nodes_equal(root, root_copy)  # verify no side effects
    return mutated_root


def assert_merge_paths_equal_layout(root: LayoutNode, id_a: str, id_b: str) -> None:
    mutated_root = merge_paths_by_id(root, id_a, id_b)
    assert are_siblings(mutated_root, id_a, id_b, use_full_id=True)
    assert_layout_equal(root, mutated_root)


def test_merge_paths_simple() -> None:
    left: LayoutNode = {"orient": "row", "children": ("1l", "2r"), "ratios": (70, 30)}
    right: LayoutNode = {"orient": "row", "children": ("3l", "4r"), "ratios": (50, 50)}
    root: LayoutNode = {"orient": "row", "children": (left, right), "ratios": (50, 50)}
    # connect 2r to 3l (from non-siblings to siblings)
    assert_merge_paths_equal_layout(root, "2r", "3l")
    assert_merge_paths_equal_layout(root, "3l", "2r")


def test_merge_paths_with_reorientation() -> None:
    left: LayoutNode = {"orient": "row", "children": ("1l", "2r"), "ratios": (70, 30)}
    right: LayoutNode = {"orient": "row", "children": ("3l", "4r"), "ratios": (50, 50)}
    left_parent: LayoutNode = {"orient": "column", "children": (left, "5"), "ratios": (80, 20)}
    right_parent: LayoutNode = {"orient": "column", "children": (right, "6"), "ratios": (80, 20)}
    root: LayoutNode = {
        "orient": "row",
        "children": (left_parent, right_parent),
        "ratios": (50, 50),
    }
    # connect 2r to 3l (from non-siblings to siblings)
    assert_merge_paths_equal_layout(root, "2r", "3l")
    assert_merge_paths_equal_layout(root, "3l", "2r")


def test_merge_paths_with_lca() -> None:
    left: LayoutNode = {"orient": "row", "children": ("1l", "2r"), "ratios": (70, 30)}
    right: LayoutNode = {"orient": "row", "children": ("3l", "4r"), "ratios": (50, 50)}
    left_parent: LayoutNode = {"orient": "column", "children": (left, "5"), "ratios": (80, 20)}
    right_parent: LayoutNode = {"orient": "column", "children": (right, "6"), "ratios": (80, 20)}
    lca: LayoutNode = {
        "orient": "row",
        "children": (left_parent, right_parent),
        "ratios": (50, 50),
    }
    root: LayoutNode = {
        "orient": "row",
        "children": (lca, "7"),
        "ratios": (50, 50),
    }
    # connect 2r to 3l (from non-siblings to siblings)
    assert_merge_paths_equal_layout(root, "2r", "3l")
    assert_merge_paths_equal_layout(root, "3l", "2r")


def test_merge_paths_partial_touch() -> None:
    left: LayoutNode = {"orient": "row", "children": ("1l", "2r"), "ratios": (70, 30)}
    right: LayoutNode = {"orient": "row", "children": ("3l", "4r"), "ratios": (50, 50)}
    left_parent: LayoutNode = {"orient": "column", "children": (left, "5"), "ratios": (79, 21)}
    right_parent: LayoutNode = {"orient": "column", "children": (right, "6"), "ratios": (80, 20)}
    root: LayoutNode = {
        "orient": "row",
        "children": (left_parent, right_parent),
        "ratios": (50, 50),
    }
    mutated_root = merge_paths_by_id(root, "2r", "3l")
    assert are_siblings(mutated_root, "2r", "3l", use_full_id=True)


def test_merge_paths_partial_touch_complex() -> None:
    root: LayoutNode = {
        "orient": "column",
        "children": (
            {
                "orient": "column",
                "children": (
                    "top_row",
                    {
                        "orient": "row",
                        "children": (
                            {
                                "orient": "row",
                                "children": ("center_row_left", "center_row_middle"),
                                "ratios": (56.182, 43.818),
                            },
                            "center_row_right",
                        ),
                        "ratios": (68.646, 31.354),
                    },
                ),
                "ratios": (46.64, 53.36),
            },
            {
                "orient": "row",
                "ratios": (67.737, 32.263),
                "children": ("bottom_row_left", "bottom_row_right"),
            },
        ),
        "ratios": (62.027, 37.973),
    }
    mutated_root = merge_paths_by_id(root, "center_row_right", "bottom_row_right")
    assert are_siblings(mutated_root, "center_row_right", "bottom_row_right", use_full_id=True)
