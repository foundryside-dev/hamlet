"""Configuration-related pytest fixtures."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import prepare_config_dir
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

__all__ = [
    "mock_config_path",
    "test_config_pack_path",
    "temp_config_pack",
    "config_pack_factory",
    "mock_config",
    "compile_universe",
    "_apply_config_overrides",
]


def _apply_config_overrides(config_data: dict[str, Any], overrides: dict[str, Any] | None) -> None:
    """Merge section overrides into config_data in-place."""

    if not overrides:
        return

    for section, updates in overrides.items():
        if section in config_data:
            current = config_data.get(section) or {}
            current.update(updates)
            config_data[section] = current
            continue

        # Convenience: allow top-level overrides for training.* keys without nesting
        training = config_data.get("training")
        if isinstance(training, dict):
            current = training.get(section) or {}
            if isinstance(updates, dict):
                current.update(updates)
            else:
                current = updates
            training[section] = current
            config_data["training"] = training
            continue

        # Fallback: add new top-level section
        config_data[section] = updates


@pytest.fixture(scope="session")
def mock_config_path() -> Path:
    """Path to frozen mock configuration for exact-value assertions."""

    return Path(__file__).parent.parent / "fixtures" / "mock_config.yaml"


@pytest.fixture(scope="session")
def test_config_pack_path() -> Path:
    """Path to the canonical v2.1 test config pack.

    This points at configs/test/model_config, which is a stable,
    minimally-sized experiment pack kept in sync with the v2.1
    configuration schema for tests.
    """

    repo_root = Path(__file__).parent.parent.parent.parent
    return repo_root / "configs" / "test" / "model_config"


@pytest.fixture
def temp_config_pack(tmp_path: Path, test_config_pack_path: Path) -> Path:
    """Temporary writable copy of the test config pack."""

    target_pack = tmp_path / "config_pack"
    shutil.copytree(test_config_pack_path, target_pack)
    return target_pack


@pytest.fixture
def config_pack_factory(tmp_path: Path):
    """Factory for isolated config packs with optional overrides."""

    counter = 0

    def _build(*, name: str | None = None, modifier: Callable[[dict[str, Any]], None] | None = None) -> Path:
        nonlocal counter
        counter += 1
        pack_name = name or f"config_pack_{counter:04d}"
        return prepare_config_dir(tmp_path, modifier=modifier, name=pack_name)

    return _build


@pytest.fixture
def mock_config(mock_config_path: Path) -> dict[str, Any]:
    """Load the frozen mock configuration as a dictionary."""

    with open(mock_config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def compile_universe() -> Callable[[Path | str], CompiledUniverse]:
    """Compile config packs to CompiledUniverse objects with simple caching."""

    compiler = UniverseCompiler()
    cache: dict[Path, CompiledUniverse] = {}
    repo_configs = (Path(__file__).parent.parent.parent.parent / "configs").resolve()

    def _compile(config_dir: Path | str) -> CompiledUniverse:
        target_path = Path(config_dir).resolve()
        cache_key: Path | None = None
        try:
            target_path.relative_to(repo_configs)
            cache_key = target_path
        except ValueError:
            cache_key = None

        if cache_key is not None and cache_key in cache:
            return cache[cache_key]

        # Disable on-disk cache to ensure tests see the latest
        # compiler semantics; rely on this in-memory cache instead.
        compiled = compiler.compile(target_path, use_cache=False)
        if cache_key is not None:
            cache[cache_key] = compiled
        return compiled

    return _compile
