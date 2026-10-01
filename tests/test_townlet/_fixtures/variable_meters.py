"""Fixtures for variable-meter configurations used in tests.

These fixtures intentionally construct synthetic config packs that exercise
the variable-meter and VFS plumbing without claiming to be production packs.

Key design points:
    - Base packs are cloned from the canonical v2.1 test config
      (configs/test/model_config) via the shared test_config_pack_path fixture.
    - bars.yaml and cascades.yaml are rewritten to use 4 or 12 meters.
    - variables.yaml is generated alongside bars.yaml and must match
      the meter vocabulary; this drives the VFS layer for TASK-001 scenarios.
    - The cloned canonical variable roster is explicitly replaced for sizing tests;
      no retired observation overlay or feasibility bypass is emitted.

Use these fixtures ONLY in variable-meter tests. For production
curriculum behavior, prefer test_config_pack_path/basic_env and related
fixtures that compile the default_curriculum or model_config packs directly.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse

# =============================================================================
# Variable meter config fixtures
# =============================================================================


@pytest.fixture
def task001_config_4meter(tmp_path: Path, test_config_pack_path: Path) -> Path:
    """Create temporary 4-meter config pack for TASK-001 testing.

    Meters: energy, health, money, mood
    Use ONLY for: TASK-001 variable meter tests
    Do NOT use for: L0 curriculum (use separate curriculum fixtures)

    Args:
        tmp_path: pytest's temporary directory
        test_config_pack_path: Path to source config pack

    Returns:
        Path to temporary 4-meter config pack directory
    """
    config_4m = tmp_path / "config_4m"
    # Use dedicated 4-meter model pack as source of truth
    repo_root = Path(__file__).parent.parent.parent.parent
    source_pack = repo_root / "configs" / "test" / "model_config_4meter"
    shutil.copytree(source_pack, config_4m)

    # Create 4-meter bars.yaml in v2.1 BarsV2Config shape
    bars_v21 = {
        "version": "1.0",
        "meters": [
            {
                "name": "energy",
                "initial": 1.0,
                "depletion": {
                    "passive": 0.005,
                    "move": 0.0,
                    "interact": 0.0,
                },
                "recovery": {"natural": 0.0},
                "bounds": {
                    "min": 0.0,
                    "max": 1.0,
                    "lethal_min": True,
                    "lethal_max": False,
                },
            },
            {
                "name": "health",
                "initial": 1.0,
                "depletion": {
                    "passive": 0.0,
                    "move": 0.0,
                    "interact": 0.0,
                },
                "recovery": {"natural": 0.001},
                "bounds": {
                    "min": 0.0,
                    "max": 1.0,
                    "lethal_min": True,
                    "lethal_max": False,
                },
            },
            {
                "name": "money",
                "initial": 0.5,
                "depletion": {
                    "passive": 0.0,
                    "move": 0.0,
                    "interact": 0.0,
                },
                "recovery": {"natural": 0.0},
                "bounds": {
                    "min": 0.0,
                    "max": 1.0,
                    "lethal_min": False,
                    "lethal_max": False,
                },
            },
            {
                "name": "mood",
                "initial": 0.7,
                "depletion": {
                    "passive": 0.001,
                    "move": 0.0,
                    "interact": 0.0,
                },
                "recovery": {"natural": 0.0},
                "bounds": {
                    "min": 0.0,
                    "max": 1.0,
                    "lethal_min": False,
                    "lethal_max": False,
                },
            },
        ],
        "cascades": [
            {
                "source": "mood",
                "target": "energy",
                "threshold": 0.2,
                "strength": 0.01,
            }
        ],
    }

    # Write v2.1 bars.yaml for all curriculum levels in the pack
    levels_dir = config_4m / "levels"
    for level_dir in levels_dir.iterdir():
        if not level_dir.is_dir():
            continue
        with open(level_dir / "bars.yaml", "w") as f:
            yaml.safe_dump({"bars": bars_v21}, f, sort_keys=False)

    # Update environment.yaml in the cloned pack to use a 4-meter vocabulary
    env_yaml = config_4m / "environment.yaml"
    env_data = yaml.safe_load(env_yaml.read_text()) or {}
    env_root = env_data.get("environment", {})

    # Restrict meters to energy, health, money, mood
    keep_meters = {"energy", "health", "money", "mood"}
    meters = env_root.get("meters", []) or []
    env_root["meters"] = [m for m in meters if m.get("name") in keep_meters]

    # Minimal cascade graph consistent with BarsV2 cascades
    env_root["cascade_graph"] = [
        {
            "source": "mood",
            "target": "energy",
            "description": "Low mood drains energy",
        }
    ]

    env_data["environment"] = env_root
    env_yaml.write_text(yaml.safe_dump(env_data, sort_keys=False))

    # NOTE: 4-meter pack now uses dedicated v2.1 model_config_4meter affordances.yaml;
    # we no longer override per-level affordances here.

    # Generate matching variables.yaml for 4 meters
    # Must match bars_config meter count to avoid VFS/bars mismatch
    vfs_config = {
        "variables": {
            "version": "1.0",
            "evaluation_mode": "mark_and_sweep",
            "debug_logging": False,
            "extents": {},
            "item_profiles": ["default_item"],
            "declarations": [
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "grid_encoding",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 64,
                    "lifetime": "tick",
                    "description": "8×8 grid encoding",
                    "initial_value": [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "local_window",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 25,
                    "lifetime": "tick",
                    "description": "5×5 local window for POMDP",
                    "initial_value": [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "position",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 2,
                    "lifetime": "episode",
                    "description": "Normalized agent position (x, y)",
                    "initial_value": [0.0, 0.0],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "energy",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "health",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "money",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "mood",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "affordance_at_position",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 15,
                    "lifetime": "tick",
                    "initial_value": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "time_sin",
                    "scope": "global",
                    "type": "scalar",
                    "lifetime": "tick",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "time_cos",
                    "scope": "global",
                    "type": "scalar",
                    "lifetime": "tick",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "interaction_progress",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "tick",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "lifetime_progress",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
            ],
        }
    }

    with open(config_4m / "variables.yaml", "w") as f:
        yaml.safe_dump(vfs_config, f, sort_keys=False)

    # NOTE: v2.1 TrainingV2Config forbids extra fields, so we no longer
    # patch allow_unfeasible_universe into training.yaml here. Feasibility
    # checks should be satisfied by the constructed packs.

    return config_4m


@pytest.fixture
def task001_config_12meter(tmp_path: Path, test_config_pack_path: Path) -> Path:
    """Create temporary 12-meter config pack for TASK-001 testing.

    Meters: 8 standard + reputation, skill, spirituality, community_trust
    Use ONLY for: TASK-001 variable meter scaling tests
    Do NOT use for: L2 curriculum (use separate curriculum fixtures)

    Args:
        tmp_path: pytest's temporary directory
        test_config_pack_path: Path to source config pack

    Returns:
        Path to temporary 12-meter config pack directory
    """
    config_12m = tmp_path / "config_12m"
    # Use dedicated 12-meter model pack as source of truth
    repo_root = Path(__file__).parent.parent.parent.parent
    source_pack = repo_root / "configs" / "test" / "model_config_12meter"
    shutil.copytree(source_pack, config_12m)

    # Generate matching variables.yaml for 12 meters
    # Must match bars_config meter count to avoid VFS/bars mismatch
    vfs_config = {
        "variables": {
            "version": "1.0",
            "evaluation_mode": "mark_and_sweep",
            "debug_logging": False,
            "extents": {},
            "item_profiles": ["default_item"],
            "declarations": [
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "grid_encoding",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 64,
                    "lifetime": "tick",
                    "description": "8×8 grid encoding",
                    "initial_value": [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "local_window",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 25,
                    "lifetime": "tick",
                    "description": "5×5 local window for POMDP",
                    "initial_value": [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "position",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 2,
                    "lifetime": "episode",
                    "description": "Normalized agent position (x, y)",
                    "initial_value": [0.0, 0.0],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "energy",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "health",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "satiation",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "money",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "mood",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "social",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "fitness",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "hygiene",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "reputation",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.5,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "skill",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.3,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "spirituality",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.6,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "community_trust",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.7,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "affordance_at_position",
                    "scope": "agent",
                    "type": "vecNf",
                    "dims": 15,
                    "lifetime": "tick",
                    "initial_value": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "time_sin",
                    "scope": "global",
                    "type": "scalar",
                    "lifetime": "tick",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "time_cos",
                    "scope": "global",
                    "type": "scalar",
                    "lifetime": "tick",
                    "initial_value": 1.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "interaction_progress",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "tick",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
                {
                    "readable_by": ["engine", "agent"],
                    "writable_by": ["engine"],
                    "id": "lifetime_progress",
                    "scope": "agent",
                    "type": "scalar",
                    "lifetime": "episode",
                    "initial_value": 0.0,
                    "semantic_type": "custom",
                    "exposed_to": [],
                },
            ],
        }
    }

    with open(config_12m / "variables.yaml", "w") as f:
        yaml.safe_dump(vfs_config, f, sort_keys=False)

    # NOTE: v2.1 TrainingV2Config forbids extra fields, so we no longer
    # patch allow_unfeasible_universe into training.yaml here.

    return config_12m


@pytest.fixture
def task001_env_4meter(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    cpu_device: torch.device,
    task001_config_4meter: Path,
) -> VectorizedHamletEnv:
    """4-meter environment for TASK-001 testing.

    Args:
        cpu_device: CPU device for deterministic behavior
        task001_config_4meter: Path to 4-meter config pack

    Returns:
        VectorizedHamletEnv instance with 4 meters
    """
    universe = compile_universe(task001_config_4meter)
    target_level = getattr(universe, "primary_level", None) or (universe.available_levels[0] if universe.available_levels else None)
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name=target_level,
        num_agents=1,
        device=cpu_device,
    )


@pytest.fixture
def task001_env_12meter(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    cpu_device: torch.device,
    task001_config_12meter: Path,
) -> VectorizedHamletEnv:
    """12-meter environment for TASK-001 testing.

    Args:
        cpu_device: CPU device for deterministic behavior
        task001_config_12meter: Path to 12-meter config pack

    Returns:
        VectorizedHamletEnv instance with 12 meters
    """
    universe = compile_universe(task001_config_12meter)
    target_level = getattr(universe, "primary_level", None) or (universe.available_levels[0] if universe.available_levels else None)
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name=target_level,
        num_agents=1,
        device=cpu_device,
    )
