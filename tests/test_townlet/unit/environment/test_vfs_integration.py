"""VFS integration tests for variable-meter universes.

These tests ensure that:
    - Compiled universes respect the configured meter count (4 / 12 meters).
    - Observation dimensions change when the meter vocabulary changes.
    - Environment meter tensors and name/index mappings stay aligned with
      the compiled universe metadata.
    - VFS misconfiguration (variables not matching bars) fails loudly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse


class TestVariableMeterVFSIntegration:
    """Integration tests for VFS + variable meter packs."""

    def test_4meter_universe_metadata_matches_env(
        self,
        compile_universe: callable,
        task001_config_4meter: Path,
        task001_env_4meter: VectorizedHamletEnv,
    ) -> None:
        """4-meter pack should compile with meter_count=4 and consistent env."""
        compiled: CompiledUniverse = compile_universe(task001_config_4meter)

        # Universe metadata
        assert compiled.metadata.meter_count == 4
        assert compiled.metadata.observation_dim > 0

        # Environment should agree with compiled universe
        assert task001_env_4meter.meters.shape[1] == 4
        assert len(task001_env_4meter.meter_name_to_index) == 4
        assert task001_env_4meter.observation_dim == compiled.metadata.observation_dim

        obs = task001_env_4meter.reset()
        assert obs.shape[1] == task001_env_4meter.observation_dim

    def test_12meter_universe_metadata_matches_env(
        self,
        compile_universe: callable,
        task001_config_12meter: Path,
        task001_env_12meter: VectorizedHamletEnv,
    ) -> None:
        """12-meter pack should compile with meter_count=12 and consistent env."""
        compiled: CompiledUniverse = compile_universe(task001_config_12meter)

        assert compiled.metadata.meter_count == 12
        assert compiled.metadata.observation_dim > 0

        assert task001_env_12meter.meters.shape[1] == 12
        assert len(task001_env_12meter.meter_name_to_index) == 12
        assert task001_env_12meter.observation_dim == compiled.metadata.observation_dim

        obs = task001_env_12meter.reset()
        assert obs.shape[1] == task001_env_12meter.observation_dim

    def test_obs_dim_increases_when_meter_count_increases(
        self,
        compile_universe: callable,
        task001_config_4meter: Path,
        task001_config_12meter: Path,
    ) -> None:
        """Compiled obs_dim should increase when we add meters."""
        compiled_4 = compile_universe(task001_config_4meter)
        compiled_12 = compile_universe(task001_config_12meter)

        assert compiled_4.metadata.meter_count == 4
        assert compiled_12.metadata.meter_count == 12
        assert compiled_12.metadata.observation_dim > compiled_4.metadata.observation_dim


def test_vfs_bars_mismatch_fails_fast(tmp_path: Path, compile_universe: callable, test_config_pack_path: Path) -> None:
    """Universe compiler should reject packs where VFS variables don't match bars.

    This creates a minimal broken pack by copying the canonical test config and
    changing bars.yaml to use a different number of meters than the variables
    declared in variables_reference.yaml.
    """
    broken_pack = tmp_path / "broken_vfs_pack"
    broken_pack.mkdir()

    # Copy the canonical v2.1 test config into broken_pack
    from shutil import copytree

    copytree(test_config_pack_path, broken_pack, dirs_exist_ok=True)

    # Overwrite the primary level's bars.yaml with a single-meter config
    import yaml

    from tests.test_townlet.helpers.config_builder import _get_primary_level_dir

    primary_level_dir = _get_primary_level_dir(broken_pack)
    bars_yaml = primary_level_dir / "bars.yaml"
    bars_data = {
        "version": "2.0",
        "description": "Broken 1-meter config (for VFS mismatch test)",
        "bars": [
            {
                "name": "energy",
                "index": 0,
                "tier": "pivotal",
                "range": [0.0, 1.0],
                "initial": 1.0,
                "base_depletion": 0.005,
                "base_move_depletion": 0.0,
                "base_interaction_cost": 0.0,
                "description": "Energy level",
            }
        ],
        "terminal_conditions": [],
    }
    with open(bars_yaml, "w") as handle:
        yaml.safe_dump({"bars": bars_data}, handle, sort_keys=False)

    # Leave variables_reference.yaml as-is, so it still reflects the original
    # meter vocabulary. The compiler should detect the mismatch and raise.
    with pytest.raises(Exception):
        compile_universe(broken_pack)
