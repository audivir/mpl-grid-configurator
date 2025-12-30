"""Example usage of mpl-grid-configurator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure, SubFigure


def add_svg() -> str:
    """Add a svg logo."""
    return (Path(__file__).parent / "example.svg").read_text()


def draw_sine(container: Figure | SubFigure) -> Axes:
    """Draw a sine wave."""
    ax = container.subplots()

    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x), color="#007bff")
    ax.set_title("Sine Wave")

    return ax


def draw_scatter(container: Figure | SubFigure) -> Axes:
    """Draw a scatter plot."""
    ax = container.subplots()

    rnd_gen = np.random.default_rng()

    ax.scatter(rnd_gen.random(20), rnd_gen.random(20), color="#ff7f0e")
    ax.set_title("Random Distribution")

    return ax


if __name__ == "__main__":
    from mpl_grid_configurator import register, start_app

    # Register the drawing functions
    register(add_svg)
    register(draw_sine)
    register(draw_scatter)

    # Start the backend and frontend
    start_app()
