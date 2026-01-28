from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from matplotlib.artist import Artist
from matplotlib.figure import Figure, SubFigure
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from collections.abc import Generator

    from matplotlib.backend_bases import RendererBase

    from mpl_grid_configurator.types import LPath

logger = logging.getLogger(__name__)

# 0: Disabled | 1: Logic Breakdown | 2: SubFigure Tree | 3: Full cProfile (Tuna)
PROFILE_LEVEL = int(os.getenv("MPL_PROFILE", "0"))
PROFILE_DIR = Path("profiles")


class DrawContext(TypedDict):
    """Context for draw calls."""

    paths: dict[SubFigure, LPath]
    times: dict[LPath, float]
    names: dict[LPath, str | None]


class SessionProfiler:
    """Handles timing breakdown for API endpoints."""

    def __init__(self, operation_name: str) -> None:
        """Initialize the profiler."""
        self.operation = operation_name
        self.timings: dict[str, float] = {}
        self.start_total = time.perf_counter()

    @contextmanager
    def track(self, label: str) -> Generator[None, None, None]:
        """Track a logical step."""
        if PROFILE_LEVEL < 1:
            yield
            return
        start = time.perf_counter()
        yield
        self.timings[label] = time.perf_counter() - start

    def finalize(self) -> None:
        """Finalize profiling."""
        total = time.perf_counter() - self.start_total
        if PROFILE_LEVEL < 1:
            logger.info("[%s] Total: %.4fs", self.operation, total)
            return
        breakdown = " | ".join([f"{k}: {v:.4f}s" for k, v in self.timings.items()])
        logger.info("[%s] Total: %.4fs | %s", self.operation, total, breakdown)


def setup_profiling() -> None:  # noqa: C901
    """Apply monkey-patches based on PROFILE_LEVEL."""
    if PROFILE_LEVEL < 2:  # noqa: PLR2004
        return

    # store context during the draw recursive call
    draw_context: DrawContext = {"paths": {}, "times": {}, "names": {}}
    orig_draw = SubFigure.draw

    first_draw_time = time.perf_counter()

    artist_draw = Artist.draw

    def draw(self: Artist, renderer: RendererBase) -> None:
        print(
            f"(ARTIST, {type(self)}) time since first draw:", time.perf_counter() - first_draw_time
        )
        artist_draw(self, renderer)

    Artist.draw = draw  # type: ignore[method-assign]

    def tracking_draw(self: SubFigure, renderer: RendererBase) -> None:
        print(
            f"(SUBFIGURE, {type(self)}) time since first draw:",
            time.perf_counter() - first_draw_time,
        )
        path = draw_context["paths"][self]
        start = time.perf_counter()
        res = orig_draw(self, renderer)
        draw_context["times"][path] = time.perf_counter() - start
        draw_context["names"][path] = getattr(self, "_name", None)
        return res

    SubFigure.draw = tracking_draw  # type: ignore[assignment]

    orig_savefig = Figure.savefig

    def profiled_savefig(self: Figure, fname: Any, **kwargs: Any) -> None:
        # Clear previous run data
        draw_context["paths"].clear()
        draw_context["times"].clear()

        # Build path map for the tree
        def map_tree(curr: Any, path: LPath) -> None:
            draw_context["paths"][curr] = path
            for i, sf in enumerate(getattr(curr, "subfigs", [])):
                map_tree(sf, (*path, i))

        if self.subfigs:
            map_tree(self.subfigs[0], ())

        # Execution
        if PROFILE_LEVEL >= 3:  # noqa: PLR2004
            try:
                import yappi  # type: ignore[import-untyped]
            except ImportError:
                logger.warning("yappi not found, skipping detailed profiling")
                orig_savefig(self, fname, **kwargs)
                return
            yappi.start()
            try:
                orig_savefig(self, fname, **kwargs)
            finally:
                yappi.stop()

                PROFILE_DIR.mkdir(exist_ok=True)
                stats_path = PROFILE_DIR / f"savefig_{int(time.time() * 1000)}.prof"
                stats = yappi.get_func_stats()
                stats.save(stats_path)

                logger.info("Detailed profile saved to %s", stats_path)
                yappi.clear_stats()
        else:
            nonlocal first_draw_time
            first_draw_time = time.perf_counter()
            orig_savefig(self, fname, **kwargs)

        # Print the subfigure tree
        if PROFILE_LEVEL >= 2:  # noqa: PLR2004
            for path in sorted(draw_context["times"]):
                # build the indentation prefix
                indent = ""
                for depth in range(len(path)):
                    if depth == len(path) - 1:
                        # we are at the leaf-end of the indent: use ├ or └
                        is_last_child = path[depth] == 1
                        indent += "└── " if is_last_child else "├── "
                    else:
                        # we are in the 'trunk'
                        is_ancestor_last = path[depth] == 1
                        indent += "    " if is_ancestor_last else "│   "

                # format the name and duration
                duration = draw_context["times"][path]
                name = draw_context["names"].get(path)
                name_str = f"({name})" if name else ""

                logger.info("%s%s: %.4fs", indent, name_str or "node", duration)

    Figure.savefig = profiled_savefig  # type: ignore[method-assign]

    called = False
    draw_ = Figure.draw

    def only_once(self: Figure, renderer: RendererBase) -> None:
        # log the function stack
        import traceback

        logger.warning("Function stack: %s", "\n".join(traceback.format_stack()))
        nonlocal called
        if called:
            5  # raise RuntimeError("Figure.draw should only be called once")
        called = True
        start = time.perf_counter()
        draw_(self, renderer)
        logger.error("Figure.draw took %.4fs", time.perf_counter() - start)

    Figure.draw = only_once  # type: ignore[assignment]


# Run the setup once on import
if PROFILE_LEVEL > 0:
    setup_profiling()
else:
    logger.debug("Profiling disabled (MPL_PROFILE=0)")
