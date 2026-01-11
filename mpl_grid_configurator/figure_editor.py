"""Edit an already rendered figure."""
# ruff: noqa: SLF001

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from matplotlib.figure import Figure, SubFigure

from mpl_grid_configurator.register import DRAW_FUNCS
from mpl_grid_configurator.render import run_draw_func
from mpl_grid_configurator.traverse import get_subfig

if TYPE_CHECKING:
    from collections.abc import Callable

    from mpl_grid_configurator.types import DrawFunc, Orientation, SubFigure_

logger = logging.getLogger(__name__)


class FigureEditor:
    """Figure editor. Mutates the figure."""

    @staticmethod
    def delete(root: SubFigure_, path: tuple[int, ...]) -> tuple[SubFigure_, SubFigure_]:
        """Remove a subfigure from the figure tree."""
        if not path:
            raise ValueError("Root figure cannot be deleted")
        parent_path = path[:-1]
        parent = get_subfig(root, parent_path) if parent_path else root
        sf = get_subfig(parent, path[-1:])

        delete_ix = parent.subfigs.index(sf)
        keep_ix = 1 - delete_ix
        keep_sf = parent.subfigs[keep_ix]

        grandpa = parent._parent
        parent_ix = grandpa.subfigs.index(parent)

        keep_sf._parent = grandpa
        keep_sf._subplotspec = parent._subplotspec
        grandpa.subfigs[parent_ix] = keep_sf

        if not parent_path:
            return keep_sf, sf

        return root, sf

    @classmethod
    def insert(  # noqa: PLR0913
        cls,
        root: SubFigure_,
        path: tuple[int, ...],
        orient: Orientation,
        ratios: tuple[float, float],
        value: str,
        drawer: DrawFunc | SubFigure_,
    ) -> tuple[SubFigure_, SubFigure_, Callable[[str], str]]:
        """Prepare the layout and figure for an insert."""
        if not path:
            raise ValueError("Cannot insert as root")

        parent_path = path[:-1]
        curr_ix = path[-1]

        root = cls.split(root, parent_path, orient)
        cls.restructure(root, parent_path, ratios)

        if curr_ix == 0:
            cls.swap(root, (*parent_path, 0), (*parent_path, 1))  # type: ignore[has-type]

        return cls.replace(root, path, value, drawer)

    @staticmethod
    def replace(
        root: SubFigure_,
        path: tuple[int, ...],
        value: str,
        drawer: DrawFunc | SubFigure_,
    ) -> tuple[SubFigure_, SubFigure_, Callable[[str], str]]:
        """Replace a subfigure with new content."""
        if not path:
            parent = root._parent
            sf = root
        else:
            parent_path = path[:-1]
            parent = get_subfig(root, parent_path) if parent_path else root
            sf = get_subfig(parent, path[-1:])

        ix = parent.subfigs.index(sf)

        # create the replacement
        if callable(drawer):
            logger.warning("Draw func needs to be run: %s", drawer.__name__)
            # creating fresh SubFigure in the same relative position
            # using existing subplotspec ensures it fits the same grid slot
            new_sf: SubFigure_ = SubFigure(parent, sf._subplotspec)  # type: ignore[assignment]
            new_sf.patch.set_visible(False)
            svg_callback = run_draw_func(value, drawer, new_sf)
        else:

            def svg_callback(_: str) -> str:
                return _

            # passing a cached SubFigure
            new_sf = drawer
            new_sf._parent = parent
            new_sf._subplotspec = sf._subplotspec

        # swap the references in the parent
        parent.subfigs[ix] = new_sf

        if path:
            return root, sf, svg_callback

        return new_sf, sf, svg_callback

    @staticmethod
    def resize(root: SubFigure_, new_size: tuple[float, float]) -> None:
        """Resize the root figure."""
        parent = root._parent
        if not isinstance(parent, Figure):
            raise ValueError("Cannot resize non-root figure")  # noqa: TRY004
        parent.set_size_inches(new_size)

    @staticmethod
    def restructure(
        root: SubFigure_,
        path: tuple[int, ...],
        ratios: tuple[float, float],
    ) -> None:
        """Restructure the two subfigures of a parent."""
        parent = get_subfig(root, path) if path else root

        try:
            subfig, _ = parent.subfigs
        except ValueError as e:
            raise ValueError("Unsplitted root figure provided") from e
        gs = subfig._subplotspec.get_gridspec()
        if gs._ncols > 1:  # type: ignore[attr-defined]
            gs.set_width_ratios(ratios)
        else:
            gs.set_height_ratios(ratios)

    @staticmethod
    def rotate(root: SubFigure_, path: tuple[int, ...]) -> None:
        """Rotate the two subfigures of a parent."""
        parent = get_subfig(root, path) if path else root

        try:
            subfig, _ = parent.subfigs
        except ValueError as e:
            raise ValueError("Unsplitted root figure provided") from e
        gs = subfig._subplotspec.get_gridspec()
        gs._nrows, gs._ncols = gs._ncols, gs._nrows  # type: ignore[attr-defined]
        gs._row_height_ratios, gs._col_width_ratios = gs._col_width_ratios, gs._row_height_ratios  # type: ignore[attr-defined]

    @staticmethod
    def split(root: SubFigure_, path: tuple[int, ...], orient: Orientation) -> SubFigure_:
        """Split a subfigure into two subfigures. Returns the root subfigure."""
        if not path:
            sf = root
            logger.warning("Splitting root figure, root figure reference will change")
        else:
            sf = get_subfig(root, path)

        nrows, ncols = (1, 2) if orient == "row" else (2, 1)

        parent = sf._parent
        orig_gs = sf._subplotspec
        curr_ix = parent.subfigs.index(sf)

        wrapper_sf: SubFigure_ = SubFigure(parent, orig_gs)  # type: ignore[assignment]
        wrapper_sf.patch.set_visible(False)
        parent.subfigs[curr_ix] = wrapper_sf

        gs = wrapper_sf.add_gridspec(nrows, ncols)
        gs.set_width_ratios([50, 50]) if orient == "row" else gs.set_height_ratios([50, 50])

        sf._parent = wrapper_sf
        sf._subplotspec = gs[0]  # type: ignore[assignment]

        new_sf: SubFigure_ = wrapper_sf.add_subfigure(gs[1])  # type: ignore[assignment]
        DRAW_FUNCS["draw_empty"](new_sf)  # type: ignore[call-arg]
        wrapper_sf.subfigs = [sf, new_sf]

        if not path:
            return wrapper_sf
        return root

    @staticmethod
    def swap(root: SubFigure_, path1: tuple[int, ...], path2: tuple[int, ...]) -> None:
        """Swap two subfigures even if they have different parents."""
        if not path1 or not path2:
            raise ValueError("Cannot swap root figure")

        sf1 = get_subfig(root, path1)
        sf2 = get_subfig(root, path2)

        if sf1 is sf2:
            logger.warning("Subfigures are the same, nothing to do")
            return

        p1, p2 = sf1._parent, sf2._parent

        # swap the SubplotSpecs
        sf1._subplotspec, sf2._subplotspec = sf2._subplotspec, sf1._subplotspec

        # update the parent references in the subfigures
        sf1._parent, sf2._parent = p2, p1

        # swap the references in the parents' subfigs lists
        ix1 = p1.subfigs.index(sf1)
        ix2 = p2.subfigs.index(sf2)
        p1.subfigs[ix1], p2.subfigs[ix2] = sf2, sf1
