"""Decorator to register and the global registry of drawing functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mpl_grid_configurator.types import DrawFunc, DrawFuncT

logger = logging.getLogger(__name__)

DRAW_FUNCS: dict[str, DrawFunc] = {}


def register(func: DrawFuncT) -> DrawFuncT:
    """Register a drawing function. Can be used as a decorator.

    A drawing function can be:
    * Variant 1: a function that takes a Matplotlib figure, draws on it and returns any of its axes.
    * Variant 2: a function that takes a Matplotlib figure,
        draws on it, returns its SVG as a string and one of its axes.
    * Variant 3: a function that takes no parameters and returns its SVG as a string.

    If the function takes no parameters, Variant 3 is assumed, if the function returns a tuple,
    Variant 2 is assumed, otherwise Variant 1 is assumed.

    ```python
    from mpl_grid_configurator import register
    from matplotlib.figure import Figure, SubFigure
    from matplotlib.axes import Axes

    @register
    def draw_func(container: Figure | SubFigure) -> Axes:
        ...
    ```

    Args:
        func: The drawing function to register.

    Returns:
        The registered function.
    """
    if func in DRAW_FUNCS.values():
        logger.warning("Function %s is already registered.", func.__name__)
        return func

    # register with unique name
    name = func.__name__
    count = 1
    while name in DRAW_FUNCS:
        name = f"{func.__name__}_{count}"
        count += 1
    DRAW_FUNCS[name] = func

    return func
