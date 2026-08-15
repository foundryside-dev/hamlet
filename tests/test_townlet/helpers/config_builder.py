"""Shared helpers for building temporary config packs in tests."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import yaml

from tests.test_townlet.unit.config.fixtures import CONFIGS_DIR

# Experiment/root-level files for the v2.1 test pack skeleton.
TOP_LEVEL_FILES = [
    "experiment.yaml",
    "stratum.yaml",
    "environment.yaml",
    "actions.yaml",
    "brain.yaml",
    "effects.yaml",
    "vfs_profiles.yaml",
    "items.yaml",
]

# Level-local files (curriculum-level configs).
LEVEL_FILES = [
    "bars.yaml",
    "affordances.yaml",
    "curriculum.yaml",
    "drive.yaml",
]

# Source skeletons: v2.1 test experiment + level template.
EXPERIMENT_SRC = CONFIGS_DIR / "test" / "model_config"
LEVEL_TEMPLATE_SRC = CONFIGS_DIR / "default_curriculum" / "levels" / "L0_0_minimal"

# Single-level test packs use this level name (matches experiment.yaml in the skeleton).
PRIMARY_LEVEL_NAME = "L0_test"


def _copy_top_level_files(dest_dir: Path) -> None:
    """Copy experiment-level YAMLs into the destination config directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for filename in TOP_LEVEL_FILES:
        src = EXPERIMENT_SRC / filename
        if not src.exists():
            raise FileNotFoundError(f"Required test config file '{filename}' missing in {EXPERIMENT_SRC}")
        shutil.copy(src, dest_dir / filename)


def _copy_level_support_files(level_dir: Path) -> None:
    """Copy curriculum-level support YAMLs (excluding training.yaml)."""
    level_dir.mkdir(parents=True, exist_ok=True)
    for filename in LEVEL_FILES:
        src = LEVEL_TEMPLATE_SRC / filename
        if not src.exists():
            raise FileNotFoundError(f"Required level file '{filename}' missing in {LEVEL_TEMPLATE_SRC}")
        shutil.copy(src, level_dir / filename)


def _load_training_template() -> dict:
    """Load the training.yaml template from the level source."""
    training_path = LEVEL_TEMPLATE_SRC / "training.yaml"
    if not training_path.exists():
        raise FileNotFoundError(f"training.yaml missing in {LEVEL_TEMPLATE_SRC}")
    return yaml.safe_load(training_path.read_text())


def _write_training_yaml(level_dir: Path, config_data: dict) -> None:
    """Write training.yaml for the level."""
    level_dir.mkdir(parents=True, exist_ok=True)
    with open(level_dir / "training.yaml", "w") as handle:
        yaml.safe_dump(config_data, handle, sort_keys=False)


def _get_primary_level_dir(config_dir: Path) -> Path:
    """Resolve the primary level directory from experiment.yaml."""
    experiment_yaml = config_dir / "experiment.yaml"
    if not experiment_yaml.exists():
        raise FileNotFoundError(f"experiment.yaml not found in {config_dir}")
    experiment_data = yaml.safe_load(experiment_yaml.read_text())
    levels = experiment_data.get("experiment", {}).get("curriculum_levels") or []
    if not levels:
        raise ValueError(f"No curriculum_levels defined in {experiment_yaml}")
    level_name = levels[0]
    return config_dir / "levels" / level_name


def prepare_config_dir(tmp_path: Path, modifier: Callable[[dict], None] | None = None, name: str = "config") -> Path:
    """Prepare a v2.1 config pack in tmp_path with optional training modifier."""
    config_dir = tmp_path / name
    config_dir.mkdir()

    _copy_top_level_files(config_dir)

    level_dir = config_dir / "levels" / PRIMARY_LEVEL_NAME
    _copy_level_support_files(level_dir)

    config_data = _load_training_template()
    if modifier is not None:
        modifier(config_data)
    _write_training_yaml(level_dir, config_data)

    return config_dir


def mutate_training_yaml(config_dir: Path, mutator: Callable[[dict], None]) -> None:
    """Load training.yaml, apply mutator, and write back."""
    level_dir = _get_primary_level_dir(config_dir)
    training_yaml = level_dir / "training.yaml"
    data = yaml.safe_load(training_yaml.read_text())
    mutator(data)
    _write_training_yaml(level_dir, data)


def mutate_brain_yaml(config_dir: Path, mutator: Callable[[dict], None]) -> None:
    """Load brain.yaml, apply mutator, and write back."""
    brain_yaml = config_dir / "brain.yaml"
    data = yaml.safe_load(brain_yaml.read_text())
    mutator(data)
    with open(brain_yaml, "w") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def mutate_stratum_yaml(config_dir: Path, mutator: Callable[[dict], None]) -> None:
    """Load stratum.yaml, apply mutator, and write back."""
    stratum_yaml = config_dir / "stratum.yaml"
    data = yaml.safe_load(stratum_yaml.read_text())
    mutator(data)
    with open(stratum_yaml, "w") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def mutate_curriculum_yaml(config_dir: Path, mutator: Callable[[dict], None]) -> None:
    """Load the primary level's curriculum.yaml, apply mutator, and write back."""
    level_dir = _get_primary_level_dir(config_dir)
    curriculum_yaml = level_dir / "curriculum.yaml"
    data = yaml.safe_load(curriculum_yaml.read_text())
    mutator(data)
    with open(curriculum_yaml, "w") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def mutate_drive_yaml(config_dir: Path, mutator: Callable[[dict], None]) -> None:
    """Load the primary level's drive.yaml, apply mutator, and write back."""
    level_dir = _get_primary_level_dir(config_dir)
    drive_yaml = level_dir / "drive.yaml"
    data = yaml.safe_load(drive_yaml.read_text())
    mutator(data)
    with open(drive_yaml, "w") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def copy_config_pack(src_dir: Path, tmp_path: Path, name: str = "pack") -> Path:
    """Copy a whole shipped config pack into tmp_path so a test can mutate it.

    The other helpers here build a synthetic single-level pack from the
    `configs/test/model_config` skeleton. Some behaviour is only reachable in a
    real multi-level pack (temporal mechanics live in L3), so those tests copy
    the shipped pack and re-parameterize it rather than reconstructing one.
    """
    dest = tmp_path / name
    shutil.copytree(src_dir, dest)
    return dest


def mutate_affordances_yaml(
    config_dir: Path,
    mutator: Callable[[dict], None],
    *,
    level_name: str | None = None,
) -> None:
    """Load a level's affordances.yaml, apply mutator, and write back.

    `level_name` selects the level in a multi-level pack; it defaults to the
    primary level, matching the other mutators. Note that the affordance
    *vocabulary* is cross-validated against environment.yaml — the compiler
    rejects an added or renamed affordance with AFFORDANCE_VOCAB_MISMATCH — so
    a mutator may change an affordance's parameters but must not change the set
    of names.
    """
    level_dir = (config_dir / "levels" / level_name) if level_name else _get_primary_level_dir(config_dir)
    affordances_yaml = level_dir / "affordances.yaml"
    if not affordances_yaml.exists():
        raise FileNotFoundError(f"affordances.yaml not found in {level_dir}")
    data = yaml.safe_load(affordances_yaml.read_text())
    mutator(data)
    with open(affordances_yaml, "w") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)
