"""Fixtures for variable-meter configurations used in tests.

These fixtures intentionally construct synthetic config packs that exercise
the variable-meter and VFS plumbing without claiming to be production packs.

Key design points:
    - Base packs are cloned from the canonical v2.1 test config
      (configs/test/model_config) via the shared test_config_pack_path fixture.
    - bars.yaml and cascades.yaml are rewritten to use 4 or 12 meters.
    - variables_reference.yaml is generated alongside bars.yaml and must match
      the meter vocabulary; this drives the VFS layer for TASK-001 scenarios.
    - training.yaml is patched with allow_unfeasible_universe=True to bypass
      Stage 4 feasibility checks: these fixtures focus on sizing behavior,
      not on full curriculum feasibility.

Use these fixtures ONLY in variable-meter tests. For production
curriculum behavior, prefer test_config_pack_path/basic_env and related
fixtures that compile the default_curriculum or model_config packs directly.
"""

from __future__ import annotations

import copy
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import _get_primary_level_dir
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

    cues_config = {
        "version": "1.0",
        "description": "4-meter cues for variable meter tests",
        "status": "TEST",
        "simple_cues": [
            {
                "cue_id": "looks_exhausted",
                "name": "Looks Exhausted",
                "category": "energy",
                "visibility": "public",
                "condition": {"meter": "energy", "operator": "<", "threshold": 0.25},
                "description": "Agent appears visibly tired",
            },
            {
                "cue_id": "looks_sickly",
                "name": "Looks Sickly",
                "category": "health",
                "visibility": "public",
                "condition": {"meter": "health", "operator": "<", "threshold": 0.4},
                "description": "Agent shows signs of illness",
            },
            {
                "cue_id": "looks_broke",
                "name": "Looks Broke",
                "category": "money",
                "visibility": "public",
                "condition": {"meter": "money", "operator": "<", "threshold": 0.2},
                "description": "Agent checks pockets frequently",
            },
            {
                "cue_id": "looks_sad",
                "name": "Looks Sad",
                "category": "mood",
                "visibility": "public",
                "condition": {"meter": "mood", "operator": "<", "threshold": 0.3},
                "description": "Agent moves listlessly",
            },
        ],
        "compound_cues": [],
    }

    with open(config_4m / "cues.yaml", "w") as f:
        yaml.safe_dump(cues_config, f, sort_keys=False)

    # Generate matching variables_reference.yaml for 4 meters
    # Must match bars_config meter count to avoid VFS/bars mismatch
    vfs_config = {
        "version": "1.0",
        "variables": [
            # Grid encoding (64 dims for 8×8 grid)
            {
                "id": "grid_encoding",
                "scope": "agent",
                "type": "vecNf",
                "dims": 64,
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": [0.0] * 64,
                "description": "8×8 grid encoding",
            },
            # Local window for POMDP (5×5 = 25 cells)
            {
                "id": "local_window",
                "scope": "agent",
                "type": "vecNf",
                "dims": 25,
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": [0.0] * 25,
                "description": "5×5 local window for POMDP",
            },
            # Position (2 dims)
            {
                "id": "position",
                "scope": "agent",
                "type": "vecNf",
                "dims": 2,
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": [0.0, 0.0],
                "description": "Normalized agent position (x, y)",
            },
            # 4 meters: energy, health, money, mood
            {
                "id": "energy",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "health",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "money",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 0.0,
            },
            {
                "id": "mood",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            # Affordance at position (15 dims)
            {
                "id": "affordance_at_position",
                "scope": "agent",
                "type": "vecNf",
                "dims": 15,
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": [0.0] * 14 + [1.0],
            },
            # Temporal features (4 scalars)
            {
                "id": "time_sin",
                "scope": "global",
                "type": "scalar",
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 0.0,
            },
            {
                "id": "time_cos",
                "scope": "global",
                "type": "scalar",
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 1.0,
            },
            {
                "id": "interaction_progress",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 0.0,
            },
            {
                "id": "lifetime_progress",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 0.0,
            },
        ],
        "exposed_observations": [
            {"id": "obs_grid_encoding", "source_variable": "grid_encoding", "exposed_to": ["agent"], "shape": [64], "normalization": None},
            {"id": "obs_local_window", "source_variable": "local_window", "exposed_to": ["agent"], "shape": [25], "normalization": None},
            {
                "id": "obs_position",
                "source_variable": "position",
                "exposed_to": ["agent"],
                "shape": [2],
                "normalization": {"kind": "minmax", "min": [0.0, 0.0], "max": [1.0, 1.0]},
            },
            {
                "id": "obs_energy",
                "source_variable": "energy",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_health",
                "source_variable": "health",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {"id": "obs_money", "source_variable": "money", "exposed_to": ["agent"], "shape": [], "normalization": None},
            {
                "id": "obs_mood",
                "source_variable": "mood",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_affordance_at_position",
                "source_variable": "affordance_at_position",
                "exposed_to": ["agent"],
                "shape": [15],
                "normalization": None,
            },
            {"id": "obs_time_sin", "source_variable": "time_sin", "exposed_to": ["agent"], "shape": [], "normalization": None},
            {"id": "obs_time_cos", "source_variable": "time_cos", "exposed_to": ["agent"], "shape": [], "normalization": None},
            {
                "id": "obs_interaction_progress",
                "source_variable": "interaction_progress",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_lifetime_progress",
                "source_variable": "lifetime_progress",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
        ],
    }

    with open(config_4m / "variables_reference.yaml", "w") as f:
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

    # Generate matching variables_reference.yaml for 12 meters
    # Must match bars_config meter count to avoid VFS/bars mismatch
    vfs_config = {
        "version": "1.0",
        "variables": [
            # Grid encoding (64 dims for 8×8 grid)
            {
                "id": "grid_encoding",
                "scope": "agent",
                "type": "vecNf",
                "dims": 64,
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": [0.0] * 64,
                "description": "8×8 grid encoding",
            },
            # Local window for POMDP (5×5 = 25 cells)
            {
                "id": "local_window",
                "scope": "agent",
                "type": "vecNf",
                "dims": 25,
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": [0.0] * 25,
                "description": "5×5 local window for POMDP",
            },
            # Position (2 dims)
            {
                "id": "position",
                "scope": "agent",
                "type": "vecNf",
                "dims": 2,
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": [0.0, 0.0],
                "description": "Normalized agent position (x, y)",
            },
            # 8 standard meters
            {
                "id": "energy",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "health",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "satiation",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "money",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 0.0,
            },
            {
                "id": "mood",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "social",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "fitness",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            {
                "id": "hygiene",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 1.0,
            },
            # 4 additional meters
            {
                "id": "reputation",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 0.5,
            },
            {
                "id": "skill",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 0.3,
            },
            {
                "id": "spirituality",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 0.6,
            },
            {
                "id": "community_trust",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine", "acs"],
                "writable_by": ["actions", "engine"],
                "default": 0.7,
            },
            # Affordance at position (15 dims)
            {
                "id": "affordance_at_position",
                "scope": "agent",
                "type": "vecNf",
                "dims": 15,
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": [0.0] * 14 + [1.0],
            },
            # Temporal features (4 scalars)
            {
                "id": "time_sin",
                "scope": "global",
                "type": "scalar",
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 0.0,
            },
            {
                "id": "time_cos",
                "scope": "global",
                "type": "scalar",
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 1.0,
            },
            {
                "id": "interaction_progress",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "tick",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 0.0,
            },
            {
                "id": "lifetime_progress",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "readable_by": ["agent", "engine"],
                "writable_by": ["engine"],
                "default": 0.0,
            },
        ],
        "exposed_observations": [
            {"id": "obs_grid_encoding", "source_variable": "grid_encoding", "exposed_to": ["agent"], "shape": [64], "normalization": None},
            {"id": "obs_local_window", "source_variable": "local_window", "exposed_to": ["agent"], "shape": [25], "normalization": None},
            {
                "id": "obs_position",
                "source_variable": "position",
                "exposed_to": ["agent"],
                "shape": [2],
                "normalization": {"kind": "minmax", "min": [0.0, 0.0], "max": [1.0, 1.0]},
            },
            # 8 standard meters
            {
                "id": "obs_energy",
                "source_variable": "energy",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_health",
                "source_variable": "health",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_satiation",
                "source_variable": "satiation",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {"id": "obs_money", "source_variable": "money", "exposed_to": ["agent"], "shape": [], "normalization": None},
            {
                "id": "obs_mood",
                "source_variable": "mood",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_social",
                "source_variable": "social",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_fitness",
                "source_variable": "fitness",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_hygiene",
                "source_variable": "hygiene",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            # 4 additional meters
            {
                "id": "obs_reputation",
                "source_variable": "reputation",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_skill",
                "source_variable": "skill",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_spirituality",
                "source_variable": "spirituality",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_community_trust",
                "source_variable": "community_trust",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            # Affordance and temporal
            {
                "id": "obs_affordance_at_position",
                "source_variable": "affordance_at_position",
                "exposed_to": ["agent"],
                "shape": [15],
                "normalization": None,
            },
            {"id": "obs_time_sin", "source_variable": "time_sin", "exposed_to": ["agent"], "shape": [], "normalization": None},
            {"id": "obs_time_cos", "source_variable": "time_cos", "exposed_to": ["agent"], "shape": [], "normalization": None},
            {
                "id": "obs_interaction_progress",
                "source_variable": "interaction_progress",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
            {
                "id": "obs_lifetime_progress",
                "source_variable": "lifetime_progress",
                "exposed_to": ["agent"],
                "shape": [],
                "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            },
        ],
    }

    with open(config_12m / "variables_reference.yaml", "w") as f:
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
    return VectorizedHamletEnv.from_universe(
        universe,
        num_agents=1,
        device=cpu_device,
    )


@pytest.fixture
def task001_env_4meter_pomdp(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    cpu_device: torch.device,
    task001_config_4meter: Path,
) -> VectorizedHamletEnv:
    """4-meter POMDP environment for TASK-001 recurrent network testing.

    Args:
        cpu_device: CPU device for deterministic behavior
        task001_config_4meter: Path to 4-meter config pack

    Returns:
        VectorizedHamletEnv instance with 4 meters and partial observability
    """
    pomdp_config = task001_config_4meter
    universe = compile_universe(pomdp_config)
    return VectorizedHamletEnv.from_universe(
        universe,
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
    return VectorizedHamletEnv.from_universe(
        universe,
        num_agents=1,
        device=cpu_device,
    )


@pytest.fixture
def task001_env_12meter_pomdp(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    cpu_device: torch.device,
    task001_config_12meter: Path,
) -> VectorizedHamletEnv:
    """12-meter POMDP environment for TASK-001 testing."""

    pomdp_config = task001_config_12meter
    universe = compile_universe(pomdp_config)
    return VectorizedHamletEnv.from_universe(
        universe,
        num_agents=1,
        device=cpu_device,
    )
