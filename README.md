# Matplotlib Grid Configurator

# Prerequisites

- Python 3.9 or higher
- Node.js and npm

# Installation

- From PyPI

```bash
python -m pip install mpl-grid-configurator # or uv pip install mpl-grid-configurator
```

- From source

```bash
git clone https://github.com/timvdm/mpl-grid-configurator.git
cd mpl-grid-configurator
python -m pip install . # or uv pip install .
```

# Example Usage

```bash
python example.py
```

# Usage

```python
"""Example usage of mpl-grid-configurator."""

from __future__ import annotations
from mpl_grid_configurator import register, start_app
from typing import TYPE_CHECKING
from functools import lru_cache

if TYPE_CHECKING:
    from matplotlib.figure import Figure, SubFigure
    from matplotlib.axes import Axes
    from numpy import NDArray
    import numpy as np


# To speed up the process, cache the data collection
@lru_cache
def build_data() -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Build and cache data to plot."""
    rnd_gen = np.random.default_rng()
    return rnd_gen.random(100), rnd_gen.random(100)


def draw_scatter(container: Figure | SubFigure) -> Axes:
    """Draw a scatter plot."""
    ax = container.subplots()
    x, y = build_data()
    ax.scatter(x, y)
    return ax


def draw_plot(container: Figure | SubFigure) -> Axes:
    """Draw a plot."""
    ax = container.subplots()
    x, y = build_data()
    ax.plot(x, y)
    return ax


# Register the drawing functions
register(draw_scatter)
register(draw_plot)

# Start backend and frontend
start_app()
```

Adjust the imports and register your drawing functions, then call `start_app()`.

- Add required imports: `from mpl_grid_configurator import register, start_app`
- Register your drawing functions: `register(draw_scatter)` and `register(draw_plot)`
- Start the backend and frontend: `start_app()`

A webbrowser opens, adjust the grid, add panels, choose the drawing function,
to store the configuration for finalizing the layout or to continue the edit later, use `Copy Configuration` and import it later with `Import Configuration`.

To finalize the layout, adjust the code:

- Change import to `from mpl_grid_configurator import register, render_layout`
- Add configuration: `layout_data = ...`
- Replace `start_app()` with `fig = render_layout(layout_data)`

# TODO

- Place the icons for rotate in the center of the separator
- Put the other icons in a new line below the drop down menu if the size of the panel is too small
- Show a preview which panel gets expanded in case of a delete while hovering over the delete icon
- Show a spinner hovering spinner while loading (at the position of the change happening)
- Multiple overlay states, none/only separators/all
