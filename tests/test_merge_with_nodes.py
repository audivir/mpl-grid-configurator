from __future__ import annotations

from utils import render_fig

from mpl_grid_configurator.merge_editor import merge
from mpl_grid_configurator.traverse import find_path_by_id


def test_merge_with_nodes(define_draw_funcs: None) -> None:
    del define_draw_funcs  # just for the side effect

    json = {
        "layout": {
            "orient": "column",
            "children": [
                {
                    "orient": "row",
                    "children": [
                        {
                            "orient": "column",
                            "children": [
                                {
                                    "orient": "row",
                                    "children": [
                                        {
                                            "orient": "column",
                                            "children": [
                                                "f1l",
                                                {
                                                    "orient": "column",
                                                    "children": [
                                                        "f2l",
                                                        {
                                                            "orient": "column",
                                                            "children": ["f3l", "f4l"],
                                                            "ratios": [51.356, 48.644],
                                                        },
                                                    ],
                                                    "ratios": [29.701, 70.299],
                                                },
                                            ],
                                            "ratios": [30.625932744775206, 69.37406725522479],
                                        },
                                        {
                                            "orient": "column",
                                            "children": ["f5l", "f6l"],
                                            "ratios": [44.834, 55.166],
                                        },
                                    ],
                                    "ratios": [38.69662802053879, 61.30337197946121],
                                },
                                {
                                    "orient": "row",
                                    "children": [
                                        "f7l",
                                        {
                                            "orient": "row",
                                            "children": [
                                                "f8l",
                                                {
                                                    "orient": "row",
                                                    "children": ["f9l", "f1r"],
                                                    "ratios": [50, 50],
                                                },
                                            ],
                                            "ratios": [28.371, 71.629],
                                        },
                                    ],
                                    "ratios": [36.95, 63.05],
                                },
                            ],
                            "ratios": [79.73425244848725, 20.265747551512746],
                        },
                        "f2r",
                    ],
                    "ratios": [77.626, 22.374],
                },
                {"orient": "row", "children": ["f3r", "f4r"], "ratios": [49.429, 50.571]},
            ],
            "ratios": [82.936, 17.064],
        },
        "figsize": [14, 14],
    }

    layout, figsize = json["layout"], json["figsize"]

    path1 = find_path_by_id(layout, "f4l", use_full_id=True)
    path2 = find_path_by_id(layout, "f7l", use_full_id=True)
    if not path1 or not path2:
        raise ValueError("Could not find paths")

    root = render_fig(layout, figsize)

    layout, root, _, _ = merge(layout, root, path1, path2, {}, lambda svg: svg)

    root = render_fig(layout, figsize)
