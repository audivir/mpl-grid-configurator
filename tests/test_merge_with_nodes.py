from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import json_comments
import msgspec
from utils import render_fig

from mpl_grid_configurator.merge_editor import merge
from mpl_grid_configurator.traverse import find_path_by_id
from mpl_grid_configurator.types import Config

if TYPE_CHECKING:
    from _typeshed import StrPath

    from mpl_grid_configurator.types import FigureSize, Layout, LPath

PARENT = Path(__file__).parent


def load_layout(file: StrPath) -> tuple[Layout, FigureSize]:
    path = PARENT / "layouts" / file
    json = msgspec.json.Decoder(Config).decode(json_comments.strip_json(path.read_text()))
    return json["layout"], json["figsize"]


def find_paths(layout: Layout, id1: str, id2: str) -> tuple[LPath, LPath]:
    path1 = find_path_by_id(layout, id1, use_full_id=True)
    path2 = find_path_by_id(layout, id2, use_full_id=True)
    if not path1 or not path2:
        raise ValueError("Could not find paths")
    return path1, path2


def test_merge_with_nodes(define_draw_funcs: None) -> None:
    del define_draw_funcs  # just for the side effect

    layout, figsize = load_layout("merge_with_nodes.jsonc")

    path1, path2 = find_paths(layout, "f4l", "f7l")

    root = render_fig(layout, figsize)

    layout, root, _, _ = merge(layout, root, path1, path2, {}, lambda svg: svg)

    root = render_fig(layout, figsize)
