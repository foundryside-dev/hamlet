"""Pytest configuration for Hamlet project test suite."""

from __future__ import annotations

from pathlib import Path

import torch
from hypothesis import settings

# Wall-clock deadlines fail on a loaded runner (parallel workers, shared CI) and say
# nothing about correctness; property tests assert behaviour, not speed.
settings.register_profile("townlet", deadline=None)
settings.load_profile("townlet")


def pytest_configure(config):  # pragma: no cover - test infrastructure
    """One torch thread per xdist worker.

    Each process sizes its thread pool to every visible core, so N workers oversubscribe
    the machine N-fold; on these small tensors that contention cost 5x wall-clock.
    """
    if hasattr(config, "workerinput"):
        torch.set_num_threads(1)


def pytest_sessionstart(session):  # pragma: no cover - test infrastructure
    """Ensure legacy coverage artefacts do not break branch coverage runs.

    pytest-cov uses coverage.py's branch mode by default in this project.
    Older `.coverage` files produced without branch data cause coverage.py to
    raise `DataError: Can't combine branch coverage data with statement data`
    when reports are aggregated.  Proactively delete any stale coverage data
    before the run so each invocation starts clean.

    Under xdist only the controller cleans: a worker would race the others'
    data files.
    """

    if hasattr(session.config, "workerinput"):
        return
    coverage_root = Path(".")
    for data_file in coverage_root.glob(".coverage*"):
        # Avoid touching directories or freshly-created files mid-run.
        if data_file.is_file():
            try:
                data_file.unlink()
            except OSError:
                # If deletion fails we fall back to letting coverage.py handle it.
                pass
