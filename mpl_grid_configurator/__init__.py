"""Matplotlib grid configurator."""

from mpl_grid_configurator.backend import start_app
from mpl_grid_configurator.register import register
from mpl_grid_configurator.render import render_layout, render_recursive, split_figure
from mpl_grid_configurator.types import Layout, LayoutNode

__version__ = "0.3.0"

__all__ = [
    "Layout",
    "LayoutNode",
    "register",
    "render_layout",
    "render_recursive",
    "split_figure",
    "start_app",
]
