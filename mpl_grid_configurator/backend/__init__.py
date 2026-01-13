"""FastAPI backend for mpl-grid-configurator."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TypeVar

import colorlog
import dotenv
from fastapi import FastAPI

from mpl_grid_configurator.backend.api import EditApi, MainApi

R = TypeVar("R")

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(message)s"))
root_logger.addHandler(handler)

PARENT = Path(__file__).parent
FRONTEND_DIR = PARENT / ".." / "frontend"


def start_app(port: int = 8000) -> None:
    """Start the backend and the frontend."""
    import threading
    import time

    import uvicorn
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

    MainApi.add_endpoints(backend_app)
    EditApi.add_endpoints(backend_app)

    # start the backend in a thread
    backend = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": backend_app, "port": 8765},
        daemon=True,
    )
    backend.start()

    frontend_app = ServeStaticASGI(None, root=FRONTEND_DIR, index_file="index.html")

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

    # allow ctrl-c to stop the servers
    while True:
        time.sleep(0.1)

    # wait for the backend thread and the frontend process to finish
    backend.join()
    frontend.join()
