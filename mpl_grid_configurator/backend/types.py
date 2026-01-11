"""Types for the backend."""

from typing import TypedDict

from mpl_grid_configurator.types import Change, Layout, Orientation

### Request types ###


class LayoutRequest(TypedDict):
    """Layout and figure size."""

    figsize: tuple[float, float]
    layout: Layout


class PathRequest(TypedDict):
    """Path."""

    path: tuple[int, ...]


class PathsRequest(TypedDict):
    """Two paths."""

    pathA: tuple[int, ...]
    pathB: tuple[int, ...]


class PathOrientRequest(PathRequest):
    """Path and orientation."""

    orient: Orientation


class ResizeRequest(TypedDict):
    """Figsize."""

    figsize: tuple[float, float]


class RestructureRequest(TypedDict):
    """Resize info for rows and columns."""

    rowRestructureInfo: tuple[tuple[int, ...], tuple[float, float]] | None
    columnRestructureInfo: tuple[tuple[int, ...], tuple[float, float]] | None


class ReplaceRequest(TypedDict):
    """Path and value."""

    path: tuple[int, ...]
    value: str


class InsertRequest(ReplaceRequest):
    """Path, orientation, ratios, and value."""

    orient: Orientation
    ratios: tuple[float, float]


class UnmergeRequest(TypedDict):
    """Inverse of merge."""

    inverse: list[Change]


### Response types ###


class TokenResponse(TypedDict):
    """Token response."""

    token: str


class SVGResponse(TokenResponse):
    """SVG and token."""

    svg: str


class LayoutResponse(TokenResponse):
    """Layout and token."""

    layout: Layout


class FullResponse(TokenResponse):
    """Response containing layout, figsize, svg, and token."""

    svg: str
    figsize: tuple[float, float]
    layout: Layout


class MergeResponse(FullResponse):
    """Response containing layout, figsize, svg, token and inverse steps for merge."""

    inverse: list[Change]
