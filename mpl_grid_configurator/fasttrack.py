"""Change an already rendered figure."""
# ruff: noqa: SLF001

from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib.figure import Figure, SubFigure

if TYPE_CHECKING:
    from collections.abc import Callable
    from matplotlib.axes import Axes
    from mpl_grid_configurator.types import Figure_, Orientation, SubFigure_


def fast_resize(
    parent: Figure_ | SubFigure_, orient: Orientation, new_ratios: tuple[float, float]
) -> None:
    """Resize the two subfigures of a parent."""
    subfig, _ = parent.subfigs  # fails if not 2 subfigs
    if orient == "row":
        subfig._subplotspec.get_gridspec().set_width_ratios(new_ratios)
    else:
        subfig._subplotspec.get_gridspec().set_height_ratios(new_ratios)


def fast_swap(parent: Figure_ | SubFigure_) -> None:
    """Swap two subfigures of a parent."""
    subfig_a, subfig_b = parent.subfigs  # fails if not 2 subfigs
    subfig_a._subplotspec.num1, subfig_b._subplotspec.num1 = (
        subfig_b._subplotspec.num1,
        subfig_a._subplotspec.num1,
    )
    subfig_a._subplotspec._num2, subfig_b._subplotspec._num2 = (
        subfig_b._subplotspec._num2,
        subfig_a._subplotspec._num2,
    )


def cross_swap(sf1: SubFigure_, sf2: SubFigure_) -> None:
    """Swap two subfigures even if they have different parents."""
    p1, p2 = sf1._parent, sf2._parent

    # 1. Swap the SubplotSpecs (this changes their position in the grid)
    sf1._subplotspec, sf2._subplotspec = sf2._subplotspec, sf1._subplotspec

    # 2. Update the parent references in the subfigures
    sf1.parent, sf2.parent = p2, p1

    # 3. Swap the references in the parents' subfigs lists
    ix1 = p1.subfigs.index(sf1)
    ix2 = p2.subfigs.index(sf2)
    p1.subfigs[ix1], p2.subfigs[ix2] = sf2, sf1


def replace_content(
    sf: SubFigure_, plot_or_sf_fn: Callable[[Figure | SubFigure_], Axes]
) -> SubFigure_:
    """...

    Ejects 'sf' from the figure tree to save it, and replaces its
    position with new content.
    """
    parent = sf._parent
    idx = parent.subfigs.index(sf)

    # 1. Create the replacement
    if callable(plot_or_sf_fn):
        # Create a fresh SubFigure in the same relative position
        # We use the existing subplotspec to ensure it fits the same grid slot
        new_sf: SubFigure_ = SubFigure(parent, sf._subplotspec)
        plot_or_sf_fn(new_sf)
    else:
        # If we are passing in a previously 'saved' SubFigure
        new_sf = plot_or_sf_fn
        new_sf.parent = parent
        new_sf._subplotspec = sf._subplotspec

    # 2. Swap the references in the parent
    parent.subfigs[idx] = new_sf

    # 3. Return the original, UNTOUCHED subfigure
    return sf


def resize_fig(fig: Figure, new_size: tuple[float, float]) -> Figure:
    """Resize the root figure."""
    fig.set_size_inches(new_size)
    return fig
