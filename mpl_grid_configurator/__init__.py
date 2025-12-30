"""Matplotlib grid configurator."""

from mpl_grid_configurator.backend import start_app
from mpl_grid_configurator.register import register
from mpl_grid_configurator.render import render_layout, render_recursive, split_figure

__version__ = "0.2.3"

__all__ = [
    "register",
    "render_layout",
    "render_recursive",
    "split_figure",
    "start_app",
]
