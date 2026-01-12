from __future__ import annotations

import msgspec
from typing_extensions import TypedDict

from mpl_grid_configurator.types import Ratios


def test_difficult_merge() -> None:
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
                                                "plot_a",
                                                {
                                                    "orient": "column",
                                                    "children": [
                                                        "plot_c",
                                                        {
                                                            "orient": "column",
                                                            "children": ["plot_d", "plot_f"],
                                                            "ratios": [51.356, 48.644],
                                                        },
                                                    ],
                                                    "ratios": [29.813, 70.187],
                                                },
                                            ],
                                            "ratios": [30.625932744775206, 69.37406725522479],
                                        },
                                        {
                                            "orient": "column",
                                            "children": ["plot_b", "plot_g"],
                                            "ratios": [41.634, 58.366],
                                        },
                                    ],
                                    "ratios": [38.69662802053879, 61.30337197946121],
                                },
                                {
                                    "orient": "row",
                                    "children": [
                                        "plot_h",
                                        {
                                            "orient": "row",
                                            "children": [
                                                "plot_i",
                                                {
                                                    "orient": "row",
                                                    "children": ["plot_j", "plot_j"],
                                                    "ratios": [50, 50],
                                                },
                                            ],
                                            "ratios": [43.172, 56.828],
                                        },
                                    ],
                                    "ratios": [34.16, 65.84],
                                },
                            ],
                            "ratios": [79.73425244848725, 20.265747551512746],
                        },
                        "plot_e",
                    ],
                    "ratios": [79.723, 20.277],
                },
                {"orient": "row", "children": ["plot_k", "plot_m"], "ratios": [49.429, 50.571]},
            ],
            "ratios": [82.936, 17.064],
        },
        "figsize": [14, 14],
    }

    from mpl_grid_configurator.types import Layout

    value = msgspec.convert(json, TypedDict[{"layout": Layout, "figsize": Ratios}])

    raise ValueError(value)
