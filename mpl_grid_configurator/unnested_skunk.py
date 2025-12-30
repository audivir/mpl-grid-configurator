"""Adjusted from https://github.com/whitead/skunk."""

import copy
import warnings
from collections.abc import Mapping

import lxml.etree as ET  # noqa: N812
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle


def connect(ax: Axes, gid: str) -> None:
    """
    Add a rectangle to given matplotlib artist that can be replaced.

    Args:
        ax: matplotlib artist that has `add_artist`, like axes
        gid: string that is used for key to replace later

    """
    p = Rectangle((0, 0), 1, 1)
    ax.add_artist(p)
    p.set_gid(gid)


def _extract_loc(e: ET.Element) -> tuple[float, float, float, float]:
    path = e.attrib["d"]
    spath = path.split()
    x: list[float] = []
    y: list[float] = []
    a1, a2 = x, y
    for s in spath:
        try:
            a1.append(float(s))
            a1, a2 = a2, a1
        except ValueError:  # noqa: PERF203
            continue
    return min(x), min(y), max(x) - min(x), max(y) - min(y)


def insert(
    repl: Mapping[str, str],
    svg: str,
    asp: bool = True,
    center_h: bool = True,
    center_v: bool = True,
) -> str:
    """
    Replace elements by `id` in `svg`.

    Args:
        repl: Mapping where keys are ids from `connect` and values are SVGs to insert.
        svg: SVG text that will be modified.
        asp: If true, keep aspect ratio of inserted SVGs.
        center_h: If true, center inserted SVGs horizontally.
        center_v: If true, center inserted SVGs vertically.

    Returns:
        SVG as string

    """
    root, idmap = ET.XMLID(svg.encode())

    nsmap = root.nsmap.copy()
    nsmap[None] = nsmap.get(None, "http://www.w3.org/2000/svg")  # default namespace

    for rk, rv in repl.items():
        if rk not in idmap:
            warnings.warn(
                f"Could not find key {rk}. Available keys: {list(idmap.keys())}",
                UserWarning,
                stacklevel=2,
            )
            continue

        e = idmap[rk]

        # Determine allocated space
        if "width" in e.attrib:
            x, y = float(e.attrib.get("x", 0)), float(e.attrib.get("y", 0))
            dx, dy = float(e.attrib["width"]), float(e.attrib["height"])
            # clear element to reuse as container
            e.clear()
        else:
            # fallback: use first child for size
            c = next(iter(e))
            x, y, dx, dy = _extract_loc(c)
            e.clear()

        # Parse replacement SVG
        try:
            rr = ET.fromstring(rv)
        except ET.ParseError as e:
            raise ValueError("Replacement SVG is not valid XML.") from e

        # Get intrinsic width/height of replacement SVG
        rw = float(rr.attrib.get("width", dx))
        rh = float(rr.attrib.get("height", dy))

        if asp:
            scale_x = scale_y = min(dx / rw, dy / rh)
        else:
            scale_x = dx / rw
            scale_y = dy / rh

        # Compute centering offsets
        offset_x = (dx - rw * scale_x) / 2 if center_h else 0
        offset_y = (dy - rh * scale_y) / 2 if center_v else 0

        # Create a <g> wrapper for transform
        g = ET.SubElement(e, f"{{{nsmap[None]}}}g")
        g.attrib["transform"] = (
            f"translate({x + offset_x},{y + offset_y}) scale({scale_x},{scale_y})"
        )

        # Deep copy children to preserve namespaces
        for child in rr:
            g.append(copy.deepcopy(child))

    return ET.tostring(root, encoding="unicode", pretty_print=True)
