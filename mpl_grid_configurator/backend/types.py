"""Types for the backend."""

# Pydantic: Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.12.
from typing_extensions import TypedDict

from mpl_grid_configurator.types import Change, FigureSize, Layout, LPath, Orient, Ratios

### Request types ###


class PathRequest(TypedDict):
    """Path."""

    path: LPath


class PathsRequest(TypedDict):
    """Two paths."""

    pathA: LPath
    pathB: LPath


class PathOrientRequest(PathRequest):
    """Path and orientation."""

    orient: Orient


class ResizeRequest(TypedDict):
    """Figsize."""

    figsize: FigureSize


class RestructureRequest(TypedDict):
    """Resize info for rows and columns."""

    rowRestructureInfo: tuple[LPath, Ratios] | None
    columnRestructureInfo: tuple[LPath, Ratios] | None


class ReplaceRequest(TypedDict):
    """Path and value."""

    path: LPath
    value: str


class InsertRequest(ReplaceRequest):
    """Path, orientation, ratios, and value."""

    orient: Orient
    ratios: Ratios


class UnmergeRequest(TypedDict):
    """Inverse of merge."""

    inverse: list[Change]


### Response types ###


class FullResponse(TypedDict):
    """Response containing layout, figsize, svg, and token."""

    token: str
    svg: str
    figsize: FigureSize
    layout: Layout


class MergeResponse(FullResponse):
    """Response containing layout, figsize, svg, token and inverse steps for merge."""

    inverse: list[Change]
