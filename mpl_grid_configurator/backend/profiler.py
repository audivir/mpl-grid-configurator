"""Optional profiler for the API endpoints."""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
# Configuration via Environment Variable
PROFILING_ENABLED = bool(os.getenv("MPL_PROFILE"))
perf_logger = logging.getLogger(__name__)


class SessionProfiler:
    """Profile API endpoints during a session."""

    def __init__(self, operation_name: str) -> None:
        """Initialize the profiler."""
        self.operation = operation_name
        self.timings: dict[str, float] = {}
        self.start_total = time.perf_counter()

    @contextmanager
    def track(self, label: str) -> Generator[None]:
        """Track a function."""
        if not PROFILING_ENABLED:
            yield
            return
        start = time.perf_counter()
        yield
        self.timings[label] = time.perf_counter() - start

    def finalize(self) -> None:
        """Finalize profiling."""
        if not PROFILING_ENABLED:
            return
        total = time.perf_counter() - self.start_total
        # Format: OpName | Total | Segment1 | Segment2 ...
        breakdown = " | ".join([f"{k}: {v:.4f}s" for k, v in self.timings.items()])
        perf_logger.info("[%s] Total: %.4fs | %s", self.operation, total, breakdown)


# Set up a dedicated file handler for performance if enabled
if PROFILING_ENABLED:
    handler = logging.FileHandler("api_performance.log")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    perf_logger.addHandler(handler)
    perf_logger.setLevel(logging.INFO)
