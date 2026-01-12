"""Merge two touching but not directly connected nodes."""

from __future__ import annotations

import logging
import uuid
from copy import deepcopy
from typing import TYPE_CHECKING

from mpl_grid_configurator.traverse import (
    adjust_node_id,
    almost_equal,
    find_path_by_id,
    get_lca,
    get_leaf,
    set_node,
)
from mpl_grid_configurator.types import BoundingBox, Edge, Layout, LayoutNode, LPath, Orient

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

MIN_TOUCH_RATIO = 0.9


class PartitioningError(ValueError):
    """Partitioning failed to create a node structure."""


class MergeError(ValueError):
    """Invalid leafs selected for merge."""


def get_edge(bbox: BoundingBox, orient: Orient) -> Edge:
    """Get the edge of a bounding box."""
    if orient == "row":
        return Edge(bbox.x_min, bbox.x_max)
    return Edge(bbox.y_min, bbox.y_max)


def get_bbox_mapping(
    node: Layout,
    bbox: BoundingBox | None = None,
    mapping: Mapping[str, BoundingBox] | None = None,
) -> dict[str, BoundingBox]:
    """Calculate bounding box (x_min, y_min, x_max, y_max) for a given path in the tree.

    Args:
        node: The tree node with added ids to calculate the bounding boxes for.
        bbox: The outer bounding box.
        mapping: The mapping of leaf ids to bounding boxes.

    Returns:
        A mapping of leaf ids (added by adjust_id) to bounding boxes.

    Raises:
        ValueError: If node ids are not unique
        ValueError: If edge length of bounding box is zero
    """
    if mapping is None:
        mapping = {}

    if not isinstance(mapping, dict):
        mapping = dict(mapping)

    if bbox is None:
        bbox = BoundingBox(0.0, 1.0, 0.0, 1.0)

    if isinstance(node, str):
        if node in mapping:
            raise ValueError(f"Node {node} already in mapping")
        mapping[node] = bbox
        return mapping

    orient = node["orient"]
    is_row = orient == "row"
    ratio1, ratio2 = node["ratios"]
    total = ratio1 + ratio2

    for child, start_ratio, end_ratio in zip(
        node["children"], (0, ratio1 / total), (ratio1 / total, 1), strict=True
    ):
        x_edge, y_edge = get_edge(bbox, "row"), get_edge(bbox, "column")
        edge, other = (x_edge, y_edge) if is_row else (y_edge, x_edge)
        new_edge = Edge(edge.min + edge.size * start_ratio, edge.min + edge.size * end_ratio)
        new_bbox = BoundingBox(*new_edge, *other) if is_row else BoundingBox(*other, *new_edge)
        get_bbox_mapping(child, new_bbox, mapping)

    if any(bbox.x_min == bbox.x_max or bbox.y_min == bbox.y_max for bbox in mapping.values()):
        raise ValueError("Invalid bounds, edge length is zero")
    return mapping


def are_bboxes_touching(bbox1: BoundingBox, bbox2: BoundingBox) -> Orient | None:
    """Evaluate if and how two bounding boxes touch.

    Returns:
        A Touch tuple if the bounding boxes touch, None otherwise.

    Raises:
        ValueError: If the bounding boxes touch in both directions
    """
    x_touch = almost_equal(bbox1.x_max, bbox2.x_min) or almost_equal(bbox2.x_max, bbox1.x_min)
    y_touch = almost_equal(bbox1.y_max, bbox2.y_min) or almost_equal(bbox2.y_max, bbox1.y_min)

    if not (x_touch or y_touch):
        logger.debug("Bounding boxes do not touch")
        return None

    if x_touch and y_touch:
        logger.debug("Bounding boxes share only a corner")
        return None

    children_orient: Orient = "row" if x_touch else "column"
    edge_orient: Orient = "column" if x_touch else "row"
    edge1, edge2 = get_edge(bbox1, edge_orient), get_edge(bbox2, edge_orient)
    overlap_min = max(edge1.min, edge2.min)
    overlap_max = min(edge1.max, edge2.max)
    overlap = max(0, overlap_max - overlap_min)
    min_size = min(edge1.size, edge2.size)

    if not overlap:
        logger.debug("Bounding boxes do not overlap")
        return None

    if overlap / min_size < MIN_TOUCH_RATIO:
        logger.debug("Bounding boxes do not overlap enough")
        return None
    return children_orient


def merge_bboxes(bbox1: BoundingBox, bbox2: BoundingBox) -> BoundingBox:
    """Merge two bounding boxes."""
    return BoundingBox(
        min(bbox1.x_min, bbox2.x_min),
        max(bbox1.x_max, bbox2.x_max),
        min(bbox1.y_min, bbox2.y_min),
        max(bbox1.y_max, bbox2.y_max),
    )


def get_bbox_size(bbox_mapping: Mapping[str, BoundingBox], orient: Orient) -> float:
    """Get the size of the given bounding boxes in the given orientation."""
    return max(r.x_max if orient == "row" else r.y_max for r in bbox_mapping.values()) - min(
        r.x_min if orient == "row" else r.y_min for r in bbox_mapping.values()
    )


def binary_space_partitioning(bbox_mapping: Mapping[str, BoundingBox]) -> LayoutNode | str:
    """Build a tree from the given bounding boxes.

    Raises:
        ValueError: If no bounding box is provided
        ValueError: If no guillotine split is possible
    """

    def build_node(
        orient: Orient,
        map1: Mapping[str, BoundingBox],
        map2: Mapping[str, BoundingBox],
    ) -> LayoutNode:
        """Build a node from the given bounding boxes."""
        size1 = get_bbox_size(map1, orient)
        size2 = get_bbox_size(map2, orient)
        total = size1 + size2
        return LayoutNode(
            orient=orient,
            children=(
                binary_space_partitioning(map1),
                binary_space_partitioning(map2),
            ),
            ratios=(100 * size1 / total, 100 * size2 / total),
        )

    if not bbox_mapping:
        raise ValueError("No bounding boxes to partition")

    if len(bbox_mapping) == 1:
        return next(iter(bbox_mapping))

    x_candidates = sorted({(r.x_max, key) for key, r in bbox_mapping.items()})[:-1]

    for x, key in x_candidates:
        left_side = {key: r for key, r in bbox_mapping.items() if r.x_max <= x}
        right_side = {key: r for key, r in bbox_mapping.items() if r.x_min >= x}

        if not left_side or not right_side:
            continue

        # A split is valid if all rectangles fall into one of the two sides
        if len(left_side) + len(right_side) == len(bbox_mapping):
            return build_node("row", left_side, right_side)

    y_candidates = sorted({(r.y_max, key) for key, r in bbox_mapping.items()})[:-1]

    for y, key in y_candidates:
        top_side = {key: r for key, r in bbox_mapping.items() if r.y_max <= y}
        bottom_side = {key: r for key, r in bbox_mapping.items() if r.y_min >= y}

        if not top_side or not bottom_side:
            continue

        if len(top_side) + len(bottom_side) == len(bbox_mapping):
            return build_node(
                "column",
                top_side,
                bottom_side,
            )

    raise PartitioningError(
        "Non-guillotine layout detected: No clear horizontal or vertical split possible."
    )


def rectify_bbox(
    to_rectify: BoundingBox,
    orient: Orient,
    bbox1: BoundingBox,
    bbox2: BoundingBox,
) -> BoundingBox:
    """Update bounding boxes along the non-touching axis.

    We take the union of A and B's extents along the non-touching axis
    (e.g., if touching side-to-side, we align their top and bottom edges)

    We must adjust ANY box that shares the old boundaries to the new target boundaries
    to maintain "guillotine" integrity (straight lines across the layout).
    """
    other_orient: Orient = "column" if orient == "row" else "row"

    edge1 = get_edge(bbox1, other_orient)
    edge2 = get_edge(bbox2, other_orient)

    target_min = min(edge1.min, edge2.min)
    target_max = max(edge1.max, edge2.max)

    curr_edge_other = get_edge(to_rectify, other_orient)
    curr_edge = get_edge(to_rectify, orient)

    # Check if this box's min or max was aligned with either node A or node B
    new_min, new_max = curr_edge_other.min, curr_edge_other.max

    if almost_equal(new_min, edge1.min) or almost_equal(new_min, edge2.min):
        new_min = target_min
    if almost_equal(new_min, edge1.max) or almost_equal(new_min, edge2.max):
        new_min = target_max
    if almost_equal(new_max, edge1.min) or almost_equal(new_max, edge2.min):
        new_max = target_min
    if almost_equal(new_max, edge1.max) or almost_equal(new_max, edge2.max):
        new_max = target_max

    new_rect_edge = Edge(new_min, new_max)

    # Reconstruct the BoundingBox
    final = (
        BoundingBox(*curr_edge, *new_rect_edge)
        if orient == "row"
        else BoundingBox(*new_rect_edge, *curr_edge)
    )

    if final.x_min == final.x_max or final.y_min == final.y_max:
        raise ValueError("Invalid bounds, edge length is zero")

    return final


def merge_paths(
    root: LayoutNode,
    path1: LPath,
    path2: LPath,
) -> tuple[LayoutNode, LPath]:
    """Merge two non-sibling, but fully touching leafs by their paths.

    Does not mutate the input node.

    Returns:
        The updated layout

    Raises:
        ValueError: If no merged bounding box can be built
    """
    # sanity checks
    if path1[:-1] == path2[:-1]:
        if path1[-1] == path2[-1]:
            raise MergeError("Paths are the same")
        raise MergeError("Paths are already siblings")

    root = deepcopy(root)
    root_with_id = adjust_node_id(root, mode="add")

    lca, lca_path, adj_path1, adj_path2 = get_lca(root_with_id, path1, path2)
    bbox_mapping = get_bbox_mapping(lca)

    leaf1 = get_leaf(lca, adj_path1)
    leaf2 = get_leaf(lca, adj_path2)

    bbox1 = bbox_mapping[leaf1]
    bbox2 = bbox_mapping[leaf2]

    orient = are_bboxes_touching(bbox1, bbox2)

    if orient is None:
        raise MergeError(
            f"Bounding boxes must touch and overlap at least {int(100 * MIN_TOUCH_RATIO)} %"
        )

    try:
        rectified_mapping: dict[str, BoundingBox] = {}
        for key, bbox in bbox_mapping.items():
            rectified_mapping[key] = rectify_bbox(bbox, orient, bbox1, bbox2)
    except ValueError as e:
        raise MergeError("Rectification failed") from e

    # Update the local copies of A and B from the rectified mapping
    rect_bbox1 = rectified_mapping[leaf1]
    rect_bbox2 = rectified_mapping[leaf2]
    merged_bbox = merge_bboxes(rect_bbox1, rect_bbox2)

    # Use the RECTIFIED mapping for the partitioner
    adj_bbox_map = dict(rectified_mapping)
    del adj_bbox_map[leaf1]
    del adj_bbox_map[leaf2]

    # Create a unique ID for the merged node placeholder
    node_id = str(uuid.uuid4())
    merged_key = f"{node_id}:::{node_id}"
    adj_bbox_map[merged_key] = merged_bbox

    try:
        partitioned_lca = binary_space_partitioning(adj_bbox_map)
    except PartitioningError as e:
        raise MergeError(*e.args) from e

    if isinstance(partitioned_lca, str):
        raise ValueError("Partitioning failed to create a node structure.")  # noqa: TRY004

    # Calculate ratios based on the rectified sizes
    edge1 = get_edge(rect_bbox1, orient)
    edge2 = get_edge(rect_bbox2, orient)
    total = edge1.size + edge2.size

    switch = edge1.min > edge2.min

    if switch:
        edge1, edge2 = edge2, edge1
        leaf1, leaf2 = leaf2, leaf1

    new_node: LayoutNode = {
        "orient": orient,
        "children": (leaf1, leaf2),
        "ratios": (100 * edge1.size / total, 100 * edge2.size / total),
    }

    new_node_path = find_path_by_id(partitioned_lca, node_id)
    if new_node_path is None:
        raise ValueError("Could not find path for new node")

    partitioned_lca = set_node(partitioned_lca, new_node_path, new_node)

    # reinsert the partitioned LCA into the original root
    new_root = set_node(root_with_id, lca_path, partitioned_lca)

    # remove the id suffixes
    new_root = adjust_node_id(new_root, mode="remove")

    return new_root, lca_path
