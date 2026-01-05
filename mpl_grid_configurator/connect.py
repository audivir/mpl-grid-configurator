"""Connect two touching but not directly connected nodes."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Literal

from mpl_grid_configurator.traverse import get_lca, get_leaf, set_node
from mpl_grid_configurator.types import BoundingBox, Edge, LayoutNode, LayoutT, Orientation

if TYPE_CHECKING:
    from collections.abc import Mapping


EPSILON = 1e-9
MIN_TOUCH_RATIO = 1.0


def almost_equal(a: float, b: float) -> bool:
    """Check if two floats are almost equal."""
    return abs(a - b) < EPSILON


def less_than(a: float, b: float) -> bool:
    """Check if a is less than b by more than epsilon."""
    return a < b - EPSILON


def more_than(a: float, b: float) -> bool:
    """Check if a is greater than b by more than epsilon."""
    return a > b + EPSILON


def adjust_node_id(node: LayoutT, mode: Literal["add", "remove"] = "add") -> LayoutT:
    """Add or remove a unique id to every node.

    Returns:
        A copy of the node with adjusted ids.
    """
    if isinstance(node, str):
        if mode == "add":
            return f"{node}:::{uuid.uuid4()}"
        return node.rsplit(":::", 1)[0]
    children = node["children"]
    return {
        "orient": node["orient"],
        "children": (adjust_node_id(children[0], mode), adjust_node_id(children[1], mode)),  # type: ignore[type-var]
        "ratios": node["ratios"],
    }


def find_path_by_id(
    node: LayoutNode | str,
    id_to_find: str,
    path: tuple[int, ...] = (),
    *,
    use_full_id: bool = False,
) -> tuple[int, ...] | None:
    """Find the path to the node with the given id.

    Args:
        node: The node to search in.
        id_to_find: The id to search for.
        path: The current path.
        use_full_id: Whether to use the full id (function name + optional uuid)
            or just the uuid.

    Returns:
        The path to the node with the given id or None if no such node exists.
    """
    if isinstance(node, str):
        curr_id = node if use_full_id else node.rsplit(":::", 1)[1]
        return path if curr_id == id_to_find else None

    for ix, child in enumerate(node["children"]):
        result = find_path_by_id(child, id_to_find, (*path, ix), use_full_id=use_full_id)
        if result is not None:
            return result
    return None


def get_edge(bbox: BoundingBox, orient: Orientation) -> Edge:
    """Get the edge of a bounding box."""
    if orient == "row":
        return Edge(bbox.x_min, bbox.x_max)
    return Edge(bbox.y_min, bbox.y_max)


def get_bbox_mapping(
    node: LayoutNode | str,
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
    ratio_a, ratio_b = node["ratios"]
    total = ratio_a + ratio_b

    for child, start_ratio, end_ratio in zip(
        node["children"], (0, ratio_a / total), (ratio_a / total, 1), strict=True
    ):
        x_edge, y_edge = get_edge(bbox, "row"), get_edge(bbox, "column")
        edge, other = (x_edge, y_edge) if is_row else (y_edge, x_edge)
        new_edge = Edge(edge.min + edge.size * start_ratio, edge.min + edge.size * end_ratio)
        new_bbox = BoundingBox(*new_edge, *other) if is_row else BoundingBox(*other, *new_edge)
        get_bbox_mapping(child, new_bbox, mapping)

    if any(bbox.x_min == bbox.x_max or bbox.y_min == bbox.y_max for bbox in mapping.values()):
        raise ValueError("Invalid bounds, edge length is zero")
    return mapping


def are_bboxes_touching(bbox_a: BoundingBox, bbox_b: BoundingBox) -> Orientation | None:
    """Evaluate if and how two bounding boxes touch.

    Returns:
        A Touch tuple if the bounding boxes touch, None otherwise.

    Raises:
        ValueError: If the bounding boxes touch in both directions
    """
    x_touch = almost_equal(bbox_a.x_max, bbox_b.x_min) or almost_equal(bbox_b.x_max, bbox_a.x_min)
    y_touch = almost_equal(bbox_a.y_max, bbox_b.y_min) or almost_equal(bbox_b.y_max, bbox_a.y_min)

    if not (x_touch or y_touch):
        return None

    if x_touch and y_touch:
        raise ValueError("touches in both directions")

    children_orient: Orientation = "row" if x_touch else "column"
    edge_orient: Orientation = "column" if x_touch else "row"
    edge_a, edge_b = get_edge(bbox_a, edge_orient), get_edge(bbox_b, edge_orient)
    overlap_min = max(edge_a.min, edge_b.min)
    overlap_max = min(edge_a.max, edge_b.max)
    overlap = max(0, overlap_max - overlap_min)
    min_size = min(edge_a.size, edge_b.size)

    if overlap / min_size < MIN_TOUCH_RATIO:
        return None
    return children_orient


def connect_bboxes(bbox_a: BoundingBox, bbox_b: BoundingBox) -> BoundingBox:
    """Connect two bounding boxes."""
    return BoundingBox(
        min(bbox_a.x_min, bbox_b.x_min),
        max(bbox_a.x_max, bbox_b.x_max),
        min(bbox_a.y_min, bbox_b.y_min),
        max(bbox_a.y_max, bbox_b.y_max),
    )


def _get_size(bbox_mapping: Mapping[str, BoundingBox], orient: Orientation) -> float:
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
        orient: Orientation,
        map_a: Mapping[str, BoundingBox],
        map_b: Mapping[str, BoundingBox],
    ) -> LayoutNode:
        """Build a node from the given bounding boxes."""
        size_a = _get_size(map_a, orient)
        size_b = _get_size(map_b, orient)
        total = size_a + size_b
        return LayoutNode(
            orient=orient,
            children=(
                binary_space_partitioning(map_a),
                binary_space_partitioning(map_b),
            ),
            ratios=(100 * size_a / total, 100 * size_b / total),
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

    raise ValueError(
        "Non-guillotine layout detected: No clear horizontal or vertical split possible."
    )


def rectify_bbox(
    bbox_to_rectify: BoundingBox,
    orient: Orientation,
    bbox_a: BoundingBox,
    bbox_b: BoundingBox,
) -> BoundingBox:
    """Update bounding boxes along the non-touching axis.

    We take the union of A and B's extents along the non-touching axis
    (e.g., if touching side-to-side, we align their top and bottom edges)

    We must adjust ANY box that shares the old boundaries to the new target boundaries
    to maintain "guillotine" integrity (straight lines across the layout).
    """
    other_orient: Orientation = "column" if orient == "row" else "row"

    edge_a = get_edge(bbox_a, other_orient)
    edge_b = get_edge(bbox_b, other_orient)

    target_min = min(edge_a.min, edge_b.min)
    target_max = max(edge_a.max, edge_b.max)

    curr_edge_other = get_edge(bbox_to_rectify, other_orient)
    curr_edge = get_edge(bbox_to_rectify, orient)

    # Check if this box's min or max was aligned with either node A or node B
    new_min, new_max = curr_edge_other.min, curr_edge_other.max

    if almost_equal(new_min, edge_a.min) or almost_equal(new_min, edge_b.min):
        new_min = target_min
    if almost_equal(new_min, edge_a.max) or almost_equal(new_min, edge_b.max):
        new_min = target_max
    if almost_equal(new_max, edge_a.min) or almost_equal(new_max, edge_b.min):
        new_max = target_min
    if almost_equal(new_max, edge_a.max) or almost_equal(new_max, edge_b.max):
        new_max = target_max

    new_rect_edge = Edge(new_min, new_max)

    # Reconstruct the BoundingBox
    if orient == "row":
        return BoundingBox(*curr_edge, *new_rect_edge)
    return BoundingBox(*new_rect_edge, *curr_edge)


def connect_paths(
    root: LayoutNode,
    path_a: tuple[int, ...],
    path_b: tuple[int, ...],
) -> LayoutNode:
    """Connect two non-sibling, but fully touching leafs by their paths.

    Returns:
        The updated layout

    Raises:
        ValueError: If no connected bounding box can be built
    """
    # sanity checks
    if path_a[:-1] == path_b[:-1]:
        if path_a[-1] == path_b[-1]:
            raise ValueError("Paths are the same")
        raise ValueError("Paths are already siblings")

    root_with_id = adjust_node_id(root, mode="add")
    lca, lca_path, adj_path_a, adj_path_b = get_lca(root_with_id, path_a, path_b)
    bbox_mapping = get_bbox_mapping(lca)

    leaf_a = get_leaf(lca, adj_path_a)
    leaf_b = get_leaf(lca, adj_path_b)

    bbox_a = bbox_mapping[leaf_a]
    bbox_b = bbox_mapping[leaf_b]

    orient = are_bboxes_touching(bbox_a, bbox_b)

    if orient is None:
        raise ValueError("Bounding boxes do not touch")

    rectified_mapping: dict[str, BoundingBox] = {}
    for key, bbox in bbox_mapping.items():
        rectified_mapping[key] = rectify_bbox(bbox, orient, bbox_a, bbox_b)

    # Update the local copies of A and B from the rectified mapping
    rect_bbox_a = rectified_mapping[leaf_a]
    rect_bbox_b = rectified_mapping[leaf_b]
    connected_bbox = connect_bboxes(rect_bbox_a, rect_bbox_b)

    # Use the RECTIFIED mapping for the partitioner
    adj_bbox_map = dict(rectified_mapping)
    del adj_bbox_map[leaf_a]
    del adj_bbox_map[leaf_b]

    # Create a unique ID for the merged node placeholder
    node_id = str(uuid.uuid4())
    merged_key = f"{node_id}:::{node_id}"
    adj_bbox_map[merged_key] = connected_bbox

    partitioned_lca = binary_space_partitioning(adj_bbox_map)
    if isinstance(partitioned_lca, str):
        raise ValueError("Partitioning failed to create a node structure.")  # noqa: TRY004

    # Calculate ratios based on the rectified sizes
    edge_a = get_edge(rect_bbox_a, orient)
    edge_b = get_edge(rect_bbox_b, orient)
    total = edge_a.size + edge_b.size

    switch = edge_a.min > edge_b.min

    if switch:
        edge_a, edge_b = edge_b, edge_a
        leaf_a, leaf_b = leaf_b, leaf_a

    new_node: LayoutNode = {
        "orient": orient,
        "children": (leaf_a, leaf_b),
        "ratios": (100 * edge_a.size / total, 100 * edge_b.size / total),
    }

    new_node_path = find_path_by_id(partitioned_lca, node_id)
    if new_node_path is None:
        raise ValueError("Could not find path for new node")

    set_node(partitioned_lca, new_node_path, new_node)

    if not lca_path:
        return adjust_node_id(partitioned_lca, mode="remove")

    set_node(root_with_id, lca_path, partitioned_lca)
    return adjust_node_id(root_with_id, mode="remove")
