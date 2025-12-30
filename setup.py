"""Build the React frontend."""

import shutil
import subprocess
from pathlib import Path

from setuptools import setup

PARENT = Path(__file__).parent
FRONTEND_DIR = PARENT / "frontend"


class MissingBinaryError(RuntimeError):
    """Binary not found."""


def build_frontend() -> None:
    """Build the frontend."""
    npm_bin = shutil.which("npm")
    if not npm_bin:
        raise MissingBinaryError("npm not found")

    subprocess.check_call([npm_bin, "install"], cwd=FRONTEND_DIR)  # noqa: S603
    subprocess.check_call([npm_bin, "run", "build"], cwd=FRONTEND_DIR)  # noqa: S603


build_frontend()
setup()
