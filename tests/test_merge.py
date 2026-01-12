from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Literal

import pytest

from mpl_grid_configurator.debug import are_bbox_mappings_equal, are_siblings
from mpl_grid_configurator.merge import (
    are_bboxes_touching,
    binary_space_partitioning,
    find_path_by_id,
    get_bbox_mapping,
    get_bbox_size,
    get_edge,
    merge_bboxes,
    merge_paths,
    rectify_bbox,
)
from mpl_grid_configurator.traverse import are_nodes_equal
from mpl_grid_configurator.types import BoundingBox, Edge

if TYPE_CHECKING:
    from mpl_grid_configurator.types import LayoutNode, LPath, Orient


def assert_layout_equal(root: LayoutNode, mutated_root: LayoutNode) -> None:
    """Assert that two layouts are equal by comparing their bounding box mappings."""
    orig_bbox_mapping = get_bbox_mapping(root)
    mutated_bbox_mapping = get_bbox_mapping(mutated_root)
    assert are_bbox_mappings_equal(orig_bbox_mapping, mutated_bbox_mapping)


def merge_paths_by_id(root: LayoutNode, id1: str, id2: str) -> tuple[LayoutNode, LPath]:
    """Merge two paths by their IDs."""
    root_copy = deepcopy(root)
    path1 = find_path_by_id(root, id1, use_full_id=True)
    path2 = find_path_by_id(root, id2, use_full_id=True)
    if path1 is None or path2 is None:
        raise ValueError("Node not found")
    mutated_root, lca_path = merge_paths(root, path1, path2)
    assert are_nodes_equal(root, root_copy)  # verify no side effects
    return mutated_root, lca_path


def assert_merge_paths_equal_layout(
    root: LayoutNode, id1: str, id2: str, expected_lca: LPath = ()
) -> None:
    """Assert that two paths merge and keep the same layout."""
    mutated_root, lca_path = merge_paths_by_id(root, id1, id2)
    assert are_siblings(mutated_root, id1, id2, use_full_id=True)
    assert_layout_equal(root, mutated_root)
    assert lca_path == expected_lca


@pytest.mark.parametrize(
    ("bbox", "orient", "expected"),
    [
        (BoundingBox(0.5, 1.5, 1.0, 2.0), "row", Edge(0.5, 1.5)),
        (BoundingBox(0.5, 1.5, 1.0, 2.0), "column", Edge(1.0, 2.0)),
    ],
)
def test_get_edge(bbox: BoundingBox, orient: Orient, expected: Edge) -> None:
    assert get_edge(bbox, orient) == expected


def test_get_bbox_mapping_leaf() -> None:
    assert get_bbox_mapping("hello") == {"hello": BoundingBox(0.0, 1.0, 0.0, 1.0)}


def test_get_bbox_mapping_left(simple_left: LayoutNode) -> None:
    assert get_bbox_mapping(simple_left) == {
        "f1l": BoundingBox(0.0, 1.0, 0.0, 0.3),
        "f2l": BoundingBox(0.0, 1.0, 0.3, 0.3 + 0.3 * 0.7),
        "f6l": BoundingBox(0.0, 1.0, 0.3 + 0.3 * 0.7, 1.0),
    }


def test_get_bbox_mapping_simple_root(simple_root: LayoutNode) -> None:
    assert get_bbox_mapping(simple_root) == {
        "f1l": BoundingBox(0.0, 0.7, 0.0, 0.3),
        "f2l": BoundingBox(0.0, 0.7, 0.3, 0.3 + 0.3 * 0.7),
        "f6l": BoundingBox(0.0, 0.7, 0.3 + 0.3 * 0.7, 1.0),
        "f3r": BoundingBox(0.7, 1.0, 0.0, 0.3),
        "f4r": BoundingBox(0.7, 1.0, 0.3, 0.3 + 0.5 * 0.7),
        "f5r": BoundingBox(0.7, 1.0, 0.3 + 0.5 * 0.7, 1.0),
    }


@pytest.mark.parametrize(
    ("id1", "id2", "expected"),
    [
        ("f1l", "f3r", "row"),
        ("f1l", "f2l", "column"),
        ("f3r", "f4r", "column"),
        ("f2l", "f4r", "row"),
        ("f2l", "f6l", "column"),
        ("f6l", "f5r", "row"),
        ("f1l", "f4r", "corner"),
        ("f3r", "f2l", "corner"),
        ("f1l", "f5r", "no_overlap"),
        ("f3r", "f6l", "no_overlap"),
        ("f6l", "f4r", "too_small_overlap"),
        ("f1l", "f7", None),
        ("f2l", "f7", None),
        ("f6l", "f7", None),
    ],
)
def test_are_bboxes_touching(
    id1: str,
    id2: str,
    expected: Orient | Literal["corner", "no_overlap", "too_small_overlap"] | None,
    lca_root: LayoutNode,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bbox_mapping = get_bbox_mapping(lca_root)
    bbox1, bbox2 = bbox_mapping[id1], bbox_mapping[id2]
    with caplog.at_level(logging.DEBUG):
        touch = are_bboxes_touching(bbox1, bbox2)
    if expected is None:
        assert "Bounding boxes do not touch" in caplog.text
    elif expected == "corner":
        assert "Bounding boxes share only a corner" in caplog.text
    elif expected == "no_overlap":
        assert "Bounding boxes do not overlap" in caplog.text
    elif expected == "too_small_overlap":
        assert "Bounding boxes do not overlap enough" in caplog.text
    else:
        assert caplog.text == ""
    expected = expected if expected in ("row", "column") else None
    assert touch == expected


@pytest.mark.parametrize(
    ("bbox1", "bbox2", "expected"),
    [
        (
            BoundingBox(0.0, 0.8, 0.1, 0.3),
            BoundingBox(0.2, 1.0, 0.2, 0.4),
            BoundingBox(0.0, 1.0, 0.1, 0.4),
        ),
    ],
)
def test_merge_bboxes(bbox1: BoundingBox, bbox2: BoundingBox, expected: BoundingBox) -> None:
    assert merge_bboxes(bbox1, bbox2) == expected


def test_get_bbox_size(lca_root: LayoutNode) -> None:
    bbox_mapping = get_bbox_mapping(lca_root)
    assert get_bbox_size(bbox_mapping, "row") == 1.0
    assert get_bbox_size(bbox_mapping, "column") == 1.0
    del bbox_mapping["f7"]
    assert get_bbox_size(bbox_mapping, "row") == 0.7  # noqa: PLR2004
    assert get_bbox_size(bbox_mapping, "column") == 1.0
    del bbox_mapping["f1l"], bbox_mapping["f3r"]
    assert get_bbox_size(bbox_mapping, "row") == 0.7  # noqa: PLR2004
    assert get_bbox_size(bbox_mapping, "column") == 0.7  # noqa: PLR2004


def test_binary_space_partitioning_left(simple_left: LayoutNode) -> None:
    assert are_nodes_equal(binary_space_partitioning(get_bbox_mapping(simple_left)), simple_left)


def test_binary_space_partitioning_right(simple_right: LayoutNode) -> None:
    assert are_nodes_equal(binary_space_partitioning(get_bbox_mapping(simple_right)), simple_right)


# TODO(tihoph): find fail cases for binary space partitioning

bbx = {
    "1": BoundingBox(0, 0.2, 0.0, 0.4),
    "2": BoundingBox(0, 0.2, 0.4, 1.0),
    "3": BoundingBox(0.2, 0.4, 0.0, 0.5),
    "4": BoundingBox(0.2, 0.4, 0.5, 1.0),
    "5": BoundingBox(0.4, 0.6, 0.0, 1.0),
    "6": BoundingBox(0.6, 0.8, 0.0, 0.5),
    "7": BoundingBox(0.8, 1.0, 0.0, 0.5),
    "8": BoundingBox(0.6, 0.9, 0.5, 1.0),
    "9": BoundingBox(0.9, 1.0, 0.5, 1.0),
}

bbx_expected = bbx.copy()
bbx_expected.update(
    {
        "1": BoundingBox(0, 0.2, 0.0, 0.5),  # resizing to the larger bbox
        "2": BoundingBox(0, 0.2, 0.5, 1.0),
        "3": BoundingBox(0.2, 0.4, 0.0, 0.5),
        "4": BoundingBox(0.2, 0.4, 0.5, 1.0),
    }
)


@pytest.mark.parametrize("to_rectify", bbx.values())
def test_rectify_bbox_no_rectify(to_rectify: BoundingBox) -> None:
    assert rectify_bbox(to_rectify, "column", bbx["1"], bbx["2"]) == to_rectify


@pytest.mark.parametrize(("key", "to_rectify"), bbx.items(), ids=lambda item: item[0])
def test_rectify_bbox_rectify(key: str, to_rectify: BoundingBox) -> None:
    # TODO(tihoph): this should not be like this
    # bboxes on the other side are unchanged as they are on the 0.5 line
    rectified = rectify_bbox(to_rectify, "row", bbx["1"], bbx["3"])
    assert rectified == bbx_expected[key]


@pytest.mark.parametrize(
    ("key", "to_rectify"),
    [(key, bbx[key]) for key in ("1", "2", "3", "4")],
    ids=lambda item: item[0],
)
def test_rectify_only_touching(key: str, to_rectify: BoundingBox) -> None:
    rectified = rectify_bbox(to_rectify, "row", bbx["1"], bbx["3"])
    assert rectified == bbx_expected[key]


@pytest.mark.xfail(reason="not yet implemented to look for touching")
@pytest.mark.parametrize(
    ("key", "to_rectify"),
    [(key, bbx[key]) for key in ("6", "7", "8", "9")],
    ids=lambda item: item[0],
)
def test_rectify_bbox_rectify_only_touching_fail(key: str, to_rectify: BoundingBox) -> None:
    expected = bbx[key]
    if key in ("6", "7"):
        to_rectify = to_rectify._replace(y_max=0.4)
        expected = expected._replace(y_max=0.4)
    if key in ("8", "9"):
        to_rectify = to_rectify._replace(y_min=0.4)
        expected = expected._replace(y_min=0.4)
    rectified = rectify_bbox(to_rectify, "row", bbx["1"], bbx["3"])
    assert rectified == expected


def test_merge_paths_fail(simple_root: LayoutNode) -> None:
    """Test merging to paths with the same previous orientation."""
    with pytest.raises(ValueError, match="Paths are the same"):
        merge_paths_by_id(simple_root, "f1l", "f1l")

    with pytest.raises(ValueError, match="Paths are already siblings"):
        merge_paths_by_id(simple_root, "f4r", "f5r")


# TODO(tihoph): define the exact expected layout


def test_merge_paths_right(simple_right: LayoutNode) -> None:
    """Test merging to paths with the same previous orientation."""
    assert_merge_paths_equal_layout(simple_right, "f3r", "f4r")
    assert_merge_paths_equal_layout(simple_right, "f4r", "f3r")


def test_merge_paths_with_reorientation(simple_root: LayoutNode) -> None:
    """Test merging to paths with different previous orientations."""
    assert_merge_paths_equal_layout(simple_root, "f1l", "f3r")
    assert_merge_paths_equal_layout(simple_root, "f3r", "f1l")


@pytest.mark.parametrize(
    ("id1", "id2", "expected_lca"), [("f3r", "f4r", (0, 1)), ("f1l", "f3r", (0,))]
)
def test_merge_paths_with_lca(
    lca_root: LayoutNode, id1: str, id2: str, expected_lca: LPath
) -> None:
    """Test merging paths if they have a common ancestor."""
    assert_merge_paths_equal_layout(lca_root, id1, id2, expected_lca)
    assert_merge_paths_equal_layout(lca_root, id2, id1, expected_lca)


def test_merge_paths_partial_touch(simple_root: LayoutNode) -> None:
    """Test merging paths if they dont fully overlap."""
    mutated_root, lca_path = merge_paths_by_id(simple_root, "f2l", "f4r")
    assert are_siblings(mutated_root, "f2l", "f4r", use_full_id=True)
    assert lca_path == ()
    mutated_root, lca_path = merge_paths_by_id(simple_root, "f4r", "f2l")
    assert are_siblings(mutated_root, "f4r", "f2l", use_full_id=True)
    assert lca_path == ()


def test_merge_paths_partial_touch_with_lca(lca_root: LayoutNode) -> None:
    """Test merging paths if they dont fully overlap."""
    mutated_root, lca_path = merge_paths_by_id(lca_root, "f2l", "f4r")
    assert are_siblings(mutated_root, "f2l", "f4r", use_full_id=True)
    assert lca_path == (0,)
    mutated_root, lca_path = merge_paths_by_id(lca_root, "f4r", "f2l")
    assert are_siblings(mutated_root, "f4r", "f2l", use_full_id=True)
    assert lca_path == (0,)


def test_merge_paths_non_touching(simple_root: LayoutNode) -> None:
    """Test merging paths if they dont touch."""
    with pytest.raises(ValueError, match="Bounding boxes must touch and overlap at least 90 %"):
        merge_paths_by_id(simple_root, "f1l", "f5r")


def test_merge_paths_errors(simple_root: LayoutNode) -> None:
    """Test merging paths if they are siblings."""
    with pytest.raises(ValueError, match="Paths are already siblings"):
        merge_paths_by_id(simple_root, "f4r", "f5r")
    with pytest.raises(ValueError, match="Paths are the same"):
        merge_paths_by_id(simple_root, "f4r", "f4r")


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
    mutated_root, _ = merge_paths_by_id(root, "center_row_right", "bottom_row_right")
    assert are_siblings(mutated_root, "center_row_right", "bottom_row_right", use_full_id=True)
