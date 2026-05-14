"""Environment and substrate fixtures."""

from __future__ import annotations

import shutil
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from tests.test_townlet._fixtures.config import _apply_config_overrides
from tests.test_townlet.helpers.config_builder import _get_primary_level_dir, mutate_training_yaml
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse

# =============================================================================
# ENVIRONMENT FIXTURES
# =============================================================================


@pytest.fixture
def basic_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    test_config_pack_path: Path,
    device: torch.device,
) -> VectorizedHamletEnv:
    """Create a basic environment with default test config.

    Configuration:
        - 1 agent
        - 8×8 grid
        - Full observability
        - No temporal mechanics
        - Device: CUDA if available, else CPU

    Returns:
        VectorizedHamletEnv instance
    """
    universe = compile_universe(test_config_pack_path)
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name="L0_test",
        num_agents=1,
        device=device,
    )


@pytest.fixture
def pomdp_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    device: torch.device,
) -> VectorizedHamletEnv:
    """Create a POMDP environment with partial observability.

    Configuration:
        - 1 agent
        - 8×8 grid
        - Partial observability (5×5 vision)
        - No temporal mechanics
        - Device: CUDA if available, else CPU

    Returns:
        VectorizedHamletEnv instance with POMDP
    """
    universe = compile_universe(Path("configs/default_curriculum"))
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name="L2_partial_observability",
        num_agents=1,
        device=device,
    )


@pytest.fixture
def temporal_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    device: torch.device,
) -> VectorizedHamletEnv:
    """Create an environment with temporal mechanics enabled.

    Configuration:
        - 1 agent
        - 8×8 grid
        - Full observability
        - Temporal mechanics (24-hour cycle)
        - Device: CUDA if available, else CPU

    Returns:
        VectorizedHamletEnv instance with temporal mechanics
    """
    universe = compile_universe(Path("configs/default_curriculum"))
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name="L3_temporal_mechanics",
        num_agents=1,
        device=device,
    )


@pytest.fixture
def multi_agent_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    test_config_pack_path: Path,
    device: torch.device,
) -> VectorizedHamletEnv:
    """Create an environment with multiple agents.

    Configuration:
        - 4 agents (for batching tests)
        - 8×8 grid
        - Full observability
        - No temporal mechanics
        - Device: CUDA if available, else CPU

    Returns:
        VectorizedHamletEnv instance with 4 agents
    """
    universe = compile_universe(test_config_pack_path)
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name="L0_test",
        num_agents=4,
        device=device,
    )


@pytest.fixture
def env_factory(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    test_config_pack_path: Path,
    device: torch.device,
):
    """Return a helper for building environments from compiled universes.

    Most tests only need to vary the config pack or agent count.  This
    factory centralizes the compile → from_universe pipeline so individual
    tests do not reach for the legacy constructor.
    """

    def _build_env(
        *,
        config_dir: Path | str | None = None,
        universe: CompiledUniverse | None = None,
        num_agents: int = 1,
        device_override: torch.device | str | None = None,
        level_name: str | None = None,
    ) -> VectorizedHamletEnv:
        target_universe = universe
        if target_universe is None:
            pack_path = Path(config_dir) if config_dir is not None else test_config_pack_path
            target_universe = compile_universe(pack_path)

        target_device = device_override if device_override is not None else device
        target_level = level_name or (target_universe.available_levels[0] if target_universe.available_levels else None)

        return VectorizedHamletEnv.from_universe(
            target_universe,
            level_name=target_level,
            num_agents=num_agents,
            device=target_device,
        )

    return _build_env


@pytest.fixture
def cpu_env_factory(env_factory, cpu_device):
    """Convenience factory that always targets the CPU device."""

    def _build_env(**kwargs):
        return env_factory(device_override=cpu_device, **kwargs)

    return _build_env


@pytest.fixture
def custom_env_builder(
    tmp_path: Path,
    test_config_pack_path: Path,
    env_factory,
    cpu_device,
):
    """Factory to build environments with optional training overrides."""

    def _build_env(
        *,
        num_agents: int = 1,
        overrides: dict[str, Any] | None = None,
        source_pack: Path | str | None = None,
    ):
        source_path = Path(source_pack) if source_pack is not None else test_config_pack_path
        target_dir = tmp_path / f"config_pack_{uuid.uuid4().hex}"
        shutil.copytree(source_path, target_dir)

        if overrides:
            overrides = dict(overrides)

            # Allow enabling temporal mechanics via curriculum when requested.
            env_overrides = overrides.pop("environment", None) or {}
            if env_overrides.get("enable_temporal_mechanics"):
                level_dir = _get_primary_level_dir(target_dir)
                curriculum_yaml = level_dir / "curriculum.yaml"
                curriculum_data = yaml.safe_load(curriculum_yaml.read_text())
                curriculum_section = curriculum_data.get("curriculum", {}) or {}
                curriculum_section["active_temporal"] = True
                # Provide a sane default day_length if not specified by override
                curriculum_section["day_length"] = env_overrides.get("day_length", 24)
                curriculum_data["curriculum"] = curriculum_section
                curriculum_yaml.write_text(yaml.safe_dump(curriculum_data, sort_keys=False))

            # Training overrides (default path)
            mutate_training_yaml(target_dir, lambda data: _apply_config_overrides(data, overrides))

        return env_factory(
            config_dir=target_dir,
            num_agents=num_agents,
            device_override=cpu_device,
        )

    return _build_env


# =============================================================================
# TASK-002A: SUBSTRATE-PARAMETERIZED FIXTURES
# =============================================================================


@pytest.fixture
def grid2d_3x3_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    device: torch.device,
) -> VectorizedHamletEnv:
    """Small 3×3 Grid2D environment for fast tests.

    Configuration:
        - 1 agent
        - 3×3 grid
        - Full observability
        - No temporal mechanics
        - Device: CUDA if available, else CPU

    Use for: Fast unit tests that don't need full 8×8 grid

    Returns:
        VectorizedHamletEnv with 3×3 Grid2D substrate
    """
    universe = compile_universe(Path("configs/default_curriculum"))
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name="L0_0_minimal",
        num_agents=1,
        device=device,
    )


@pytest.fixture
def grid2d_8x8_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    test_config_pack_path: Path,
    device: torch.device,
) -> VectorizedHamletEnv:
    """Standard 8×8 Grid2D environment (same as basic_env, explicit name).

    Configuration:
        - 1 agent
        - 8×8 grid
        - Full observability
        - No temporal mechanics
        - Device: CUDA if available, else CPU

    Use for: Tests requiring standard grid size (legacy compatibility)

    Returns:
        VectorizedHamletEnv with 8×8 Grid2D substrate
    """
    universe = compile_universe(test_config_pack_path)
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name="L0_test",
        num_agents=1,
        device=device,
    )


@pytest.fixture
def aspatial_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    device: torch.device,
    tmp_path: Path,
    test_config_pack_path: Path,
) -> VectorizedHamletEnv:
    """Aspatial environment (no grid, meters only).

    Configuration:
        - 1 agent
        - No spatial substrate (aspatial)
        - 4 meters: energy, health, money, mood
        - 4 affordances: Bed, Hospital, HomeMeal, Job
        - Device: CUDA if available, else CPU

    Use for: Testing aspatial substrate behavior (no positions, no movement)

    Returns:
        VectorizedHamletEnv with Aspatial substrate
    """
    # Build a temporary aspatial pack from the canonical test pack.
    aspatial_config_path = tmp_path / "aspatial_pack"
    shutil.copytree(test_config_pack_path, aspatial_config_path)

    # Patch stratum to aspatial
    stratum_path = aspatial_config_path / "stratum.yaml"
    stratum_path.write_text("""stratum:
  version: "1.0"
  substrate:
    type: aspatial
    aspatial: {}
  vision_support: global
  temporal_support: disabled
""")

    # Patch bars for expected base/move/interaction costs used in movement mask tests.
    import yaml

    level_dir = aspatial_config_path / "levels" / "L0_test"
    bars_path = level_dir / "bars.yaml"
    bars_data = yaml.safe_load(bars_path.read_text())
    meters = bars_data.get("bars", {}).get("meters", []) or bars_data.get("meters", [])
    for meter in meters:
        name = meter.get("name")
        dep = meter.get("depletion", {})
        if name == "energy":
            dep.update({"passive": 0.005, "move": 0.005, "interact": 0.005})
        elif name == "hygiene":
            dep.update({"passive": 0.003, "move": 0.0, "interact": 0.0})
        elif name == "satiation":
            dep.update({"passive": 0.004, "move": 0.0, "interact": 0.0})
        meter["depletion"] = dep
    if "bars" in bars_data and isinstance(bars_data["bars"], dict):
        bars_data["bars"]["meters"] = meters
    else:
        bars_data["meters"] = meters
    bars_path.write_text(yaml.safe_dump(bars_data, sort_keys=False))

    universe = compile_universe(aspatial_config_path)
    target_level = getattr(universe, "primary_level", None) or (universe.available_levels[0] if universe.available_levels else None)
    return VectorizedHamletEnv.from_universe(
        universe,
        level_name=target_level,
        num_agents=1,
        device=device,
    )


@pytest.fixture
def continuous1d_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    device: torch.device,
    tmp_path: Path,
) -> VectorizedHamletEnv:
    """Continuous 1D environment for movement/action-mask tests."""

    import yaml

    source = Path("configs/test/action_space/continuous1d")
    config_dir = tmp_path / "continuous1d_pack"
    shutil.copytree(source, config_dir)

    # Patch bars for expected base/move/interaction depletions
    bars_path = config_dir / "levels" / "L0" / "bars.yaml"
    bars_data = yaml.safe_load(bars_path.read_text())
    meters = bars_data.get("bars", {}).get("meters", []) or bars_data.get("meters", [])
    for meter in meters:
        if meter.get("name") == "energy":
            meter["depletion"] = {"passive": 0.005, "move": 0.005, "interact": 0.005}
    if "bars" in bars_data and isinstance(bars_data["bars"], dict):
        bars_data["bars"]["meters"] = meters
    else:
        bars_data["meters"] = meters
    bars_path.write_text(yaml.safe_dump(bars_data, sort_keys=False))

    universe = compile_universe(config_dir)
    return VectorizedHamletEnv.from_universe(universe, level_name="L0", num_agents=1, device=device)


@pytest.fixture
def continuous3d_env(
    compile_universe: Callable[[Path | str], CompiledUniverse],
    device: torch.device,
    tmp_path: Path,
) -> VectorizedHamletEnv:
    """Continuous 3D environment for movement/action-mask tests."""

    import yaml

    source = Path("configs/test/action_space/continuous1d")
    config_dir = tmp_path / "continuous3d_pack"
    shutil.copytree(source, config_dir)

    # Patch stratum to 3D continuous
    stratum_path = config_dir / "stratum.yaml"
    stratum_path.write_text("""stratum:
  version: "1.0"
  substrate:
    type: continuous
    continuous:
      dimensions: 3
      bounds:
        - [0.0, 10.0]
        - [0.0, 10.0]
        - [0.0, 10.0]
      boundary: clamp
      movement_delta: 0.5
      interaction_radius: 1.0
      distance_metric: euclidean
      observation_encoding: relative
      action_discretization:
        num_directions: 8
        num_magnitudes: 3
  vision_support: global
  temporal_support: disabled
""")

    # Patch bars for expected base/move/interaction depletions
    bars_path = config_dir / "levels" / "L0" / "bars.yaml"
    bars_data = yaml.safe_load(bars_path.read_text())
    meters = bars_data.get("bars", {}).get("meters", []) or bars_data.get("meters", [])
    for meter in meters:
        if meter.get("name") == "energy":
            meter["depletion"] = {"passive": 0.005, "move": 0.005, "interact": 0.005}
    if "bars" in bars_data and isinstance(bars_data["bars"], dict):
        bars_data["bars"]["meters"] = meters
    else:
        bars_data["meters"] = meters
    bars_path.write_text(yaml.safe_dump(bars_data, sort_keys=False))

    # Update affordance positions to 3D points
    aff_path = config_dir / "levels" / "L0" / "affordances.yaml"
    aff_data = yaml.safe_load(aff_path.read_text())
    aff_list = aff_data["affordances"]["affordances"] if isinstance(aff_data["affordances"], dict) else aff_data["affordances"]
    for aff in aff_list:
        positions = aff.get("deployment", {}).get("positions", [])
        aff.setdefault("deployment", {})
        aff["deployment"]["positions"] = [[p[0], 0, 0] if isinstance(p, list) else [0, 0, 0] for p in positions] or [[0, 0, 0]]
    if isinstance(aff_data["affordances"], dict):
        aff_data["affordances"]["affordances"] = aff_list
    else:
        aff_data["affordances"] = aff_list
    aff_path.write_text(yaml.safe_dump(aff_data, sort_keys=False))

    universe = compile_universe(config_dir)
    return VectorizedHamletEnv.from_universe(universe, level_name="L0", num_agents=1, device=device)


# Parameterization helper for multi-substrate tests
SUBSTRATE_FIXTURES = ["grid2d_3x3_env", "grid2d_8x8_env", "aspatial_env"]
