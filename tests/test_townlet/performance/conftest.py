"""Conftest for performance benchmarks.

Skips all benchmark tests if pytest-benchmark is not installed.
"""

import pytest

# Check if pytest-benchmark is available
try:
    import pytest_benchmark  # noqa: F401

    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False


def pytest_collection_modifyitems(config, items):
    """Skip benchmark tests if pytest-benchmark not installed."""
    if BENCHMARK_AVAILABLE:
        return

    skip_benchmark = pytest.mark.skip(reason="pytest-benchmark not installed (optional dependency)")
    for item in items:
        # Skip any test that uses the benchmark fixture
        if "benchmark" in item.fixturenames:
            item.add_marker(skip_benchmark)


# Only define stub fixture if pytest-benchmark is NOT available
if not BENCHMARK_AVAILABLE:

    @pytest.fixture
    def benchmark():
        """Stub fixture when pytest-benchmark is not installed.

        This prevents collection errors. Tests will be skipped via
        pytest_collection_modifyitems above.
        """
        pytest.skip("pytest-benchmark not installed")
