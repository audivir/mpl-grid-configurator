"""FastAPI backend for mpl-grid-configurator."""

import io
import logging
from pathlib import Path

from mpl_grid_configurator.register import DRAW_FUNCS, register
from mpl_grid_configurator.render import draw_empty, render_layout
from mpl_grid_configurator.types import LayoutData, SVGResponse

logger = logging.getLogger(__name__)

PARENT = Path(__file__).parent
FRONTEND_DIR = PARENT / "frontend"


async def get_functions() -> list[str]:
    """Get a list of available functions."""
    return list(DRAW_FUNCS.keys())


async def render_api(layout_data: LayoutData) -> SVGResponse:
    """Render a layout."""
    import matplotlib.pyplot as plt
    from fastapi import HTTPException

    try:
        fig, svg_callback = render_layout(layout_data["layout"], layout_data["figsize"], DRAW_FUNCS)
        buf = io.BytesIO()
        fig.savefig(buf, format="svg")
        plt.close(fig)
        final_svg = buf.getvalue().decode("utf-8")
        fixed_svg = svg_callback(final_svg)
    except Exception as e:
        logger.exception("Error during rendering")
        raise HTTPException(status_code=400, detail=str(e)) from e
    else:
        return {"svg": fixed_svg}


def start_app(port: int = 8000) -> None:
    """Start the backend and the frontend."""
    import threading
    import time

    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from servestatic import ServeStaticASGI  # type: ignore[import-untyped]

    backend_app = FastAPI()

    # Enable CORS for React development
    backend_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    backend_app.get("/functions")(get_functions)
    backend_app.post("/render")(render_api)

    if draw_empty not in DRAW_FUNCS.values():
        register(draw_empty)

    # start the backend in a thread
    backend = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": backend_app, "port": 8765},
        daemon=True,
    )
    backend.start()

    frontend_app = ServeStaticASGI(None, root=FRONTEND_DIR)

    frontend = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": frontend_app, "port": port},
        daemon=True,
    )
    frontend.start()

    time.sleep(0.5)  # give the servers time to start
    print(  # noqa: T201
        f"To configure your grid, open http://localhost:{port}/index.html in your browser."
    )

    # wait for the backend thread and the frontend process to finish
    backend.join()
    frontend.join()
