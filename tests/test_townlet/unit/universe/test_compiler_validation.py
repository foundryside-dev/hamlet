"""Tests for UniverseCompiler validation methods."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError, CompilationErrorCollector

# --- _validate_config_dir tests ---


def test_validate_config_dir_rejects_nonexistent_path(tmp_path: Path) -> None:
    """_validate_config_dir raises for nonexistent path."""
    compiler = UniverseCompiler()
    fake_path = tmp_path / "does_not_exist"

    with pytest.raises(CompilationError, match="does not exist"):
        compiler._validate_config_dir(fake_path)


def test_validate_config_dir_rejects_file_path(tmp_path: Path) -> None:
    """_validate_config_dir raises when path is a file not directory."""
    compiler = UniverseCompiler()
    file_path = tmp_path / "some_file.txt"
    file_path.touch()

    with pytest.raises(CompilationError, match="not a directory"):
        compiler._validate_config_dir(file_path)


def test_validate_config_dir_accepts_valid_directory(tmp_path: Path) -> None:
    """_validate_config_dir passes for valid directory."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Should not raise
    compiler._validate_config_dir(config_dir)


def test_validate_config_dir_warns_on_traversal_patterns(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """_validate_config_dir warns about .. patterns."""
    import logging

    compiler = UniverseCompiler()
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create path with .. that resolves to valid directory
    suspicious_path = tmp_path / "config" / ".." / "config"

    caplog.set_level(logging.WARNING)
    compiler._validate_config_dir(suspicious_path)

    # Should log a warning
    assert any(".." in record.message for record in caplog.records)


# --- _phase_0_validate_yaml_syntax tests ---


def test_phase_0_yaml_syntax_rejects_missing_required_files(tmp_path: Path) -> None:
    """_phase_0_validate_yaml_syntax raises when required files missing."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    with pytest.raises(CompilationError) as excinfo:
        compiler._phase_0_validate_yaml_syntax(config_dir)

    assert "YAML Syntax Validation" in str(excinfo.value)
    assert "experiment.yaml" in str(excinfo.value) or "MISSING_FILE" in str(excinfo.value)


def test_phase_0_yaml_syntax_rejects_invalid_yaml(tmp_path: Path) -> None:
    """_phase_0_validate_yaml_syntax raises on malformed YAML."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create required files
    for f in ["experiment.yaml", "stratum.yaml", "environment.yaml", "actions.yaml", "brain.yaml"]:
        (config_dir / f).write_text("valid: yaml\n")

    # Create levels directory with malformed YAML
    levels_dir = config_dir / "levels" / "L0_test"
    levels_dir.mkdir(parents=True)
    (levels_dir / "curriculum.yaml").write_text("invalid: [yaml: syntax")  # Malformed

    for f in ["bars.yaml", "affordances.yaml", "training.yaml", "drive.yaml"]:
        (levels_dir / f).write_text("valid: yaml\n")

    with pytest.raises(CompilationError) as excinfo:
        compiler._phase_0_validate_yaml_syntax(config_dir)

    assert "YAML" in str(excinfo.value)


def test_phase_0_yaml_syntax_accepts_valid_yaml(tmp_path: Path) -> None:
    """_phase_0_validate_yaml_syntax passes with valid YAML files."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create required shared files
    for f in ["experiment.yaml", "stratum.yaml", "environment.yaml", "actions.yaml", "brain.yaml"]:
        (config_dir / f).write_text("valid: yaml\n")

    # Create levels directory with valid files
    levels_dir = config_dir / "levels" / "L0_test"
    levels_dir.mkdir(parents=True)
    for f in ["curriculum.yaml", "bars.yaml", "affordances.yaml", "training.yaml", "drive.yaml"]:
        (levels_dir / f).write_text("valid: yaml\n")

    # Should not raise
    compiler._phase_0_validate_yaml_syntax(config_dir)


def test_phase_0_yaml_syntax_allows_optional_items_yaml_missing(tmp_path: Path) -> None:
    """items.yaml is optional for phase 0 validation."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create required shared files (no items.yaml)
    for f in ["experiment.yaml", "stratum.yaml", "environment.yaml", "actions.yaml", "brain.yaml"]:
        (config_dir / f).write_text("valid: yaml\n")

    levels_dir = config_dir / "levels" / "L0_test"
    levels_dir.mkdir(parents=True)
    for f in ["curriculum.yaml", "bars.yaml", "affordances.yaml", "training.yaml", "drive.yaml"]:
        (levels_dir / f).write_text("valid: yaml\n")

    # Should not raise even though items.yaml is missing
    compiler._phase_0_validate_yaml_syntax(config_dir)


# --- _validate_spatial_feasibility tests ---


def test_validate_spatial_feasibility_detects_overcrowding() -> None:
    """_validate_spatial_feasibility fails when grid can't fit affordances + agents."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    # Mock raw_configs with small grid but many affordances
    raw_configs = MagicMock()
    raw_configs.substrate.type = "grid"
    raw_configs.substrate.grid.topology = "square"
    raw_configs.substrate.grid.width = 2
    raw_configs.substrate.grid.height = 2  # 4 cells total
    raw_configs.environment.enabled_affordances = ["a1", "a2", "a3", "a4", "a5"]  # 5 affordances
    raw_configs.population.num_agents = 2  # Need 7 cells total (5 + 2)

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_spatial_feasibility(raw_configs, errors, formatter)

    assert len(errors.errors) == 1
    assert "Spatial impossibility" in errors.errors[0]


def test_validate_spatial_feasibility_passes_when_space_sufficient() -> None:
    """_validate_spatial_feasibility passes when grid has enough space."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    raw_configs.substrate.type = "grid"
    raw_configs.substrate.grid.topology = "square"
    raw_configs.substrate.grid.width = 10
    raw_configs.substrate.grid.height = 10  # 100 cells
    raw_configs.environment.enabled_affordances = ["a1", "a2"]  # 2 affordances
    raw_configs.population.num_agents = 4  # Need 6 cells total

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_spatial_feasibility(raw_configs, errors, formatter)

    assert len(errors.errors) == 0


def test_validate_spatial_feasibility_skips_continuous_substrates() -> None:
    """_validate_spatial_feasibility skips continuous substrates."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    raw_configs.substrate.type = "continuous"
    raw_configs.substrate.grid = None

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    # Should return early without errors
    compiler._validate_spatial_feasibility(raw_configs, errors, formatter)

    assert len(errors.errors) == 0


def test_validate_spatial_feasibility_handles_3d_grid() -> None:
    """_validate_spatial_feasibility calculates 3D grid cells correctly."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    raw_configs.substrate.type = "grid"
    raw_configs.substrate.grid.topology = "cubic"
    raw_configs.substrate.grid.width = 3
    raw_configs.substrate.grid.height = 3
    raw_configs.substrate.grid.depth = 3  # 27 cells
    raw_configs.environment.enabled_affordances = ["a1"] * 30  # Too many!
    raw_configs.population.num_agents = 1

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_spatial_feasibility(raw_configs, errors, formatter)

    assert len(errors.errors) == 1
    assert "27 cells" in errors.errors[0]


def test_validate_spatial_feasibility_handles_gridnd() -> None:
    """_validate_spatial_feasibility calculates GridND cells correctly."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    raw_configs.substrate.type = "gridnd"
    raw_configs.substrate.grid = None
    raw_configs.substrate.gridnd.dimension_sizes = [2, 2, 2, 2]  # 16 cells (2^4)
    raw_configs.environment.enabled_affordances = ["a1"] * 20  # Too many!
    raw_configs.population.num_agents = 1

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_spatial_feasibility(raw_configs, errors, formatter)

    assert len(errors.errors) == 1
    assert "16 cells" in errors.errors[0]


# --- _enforce_security_limits tests ---


def test_enforce_security_limits_rejects_too_many_meters() -> None:
    """_enforce_security_limits fails when too many meters defined."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    # Create mock with excessive meters
    raw_configs = MagicMock()
    raw_configs.bars = ["meter"] * 1000  # Way too many
    raw_configs.affordances = []
    raw_configs.cascades = []
    raw_configs.global_actions.actions = []
    raw_configs.variables_reference = []
    raw_configs.item_types = []
    raw_configs.compiled_vfs_profiles = []

    compiler._enforce_security_limits(raw_configs, errors)

    assert len(errors.errors) >= 1
    assert any("meters" in e for e in errors.errors)


def test_enforce_security_limits_passes_within_limits() -> None:
    """_enforce_security_limits passes when counts are within limits."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    raw_configs.bars = ["meter1", "meter2"]
    raw_configs.affordances = ["aff1"]
    raw_configs.cascades = []
    raw_configs.global_actions.actions = ["action1"]
    raw_configs.variables_reference = []
    raw_configs.item_types = None
    raw_configs.compiled_vfs_profiles = None

    compiler._enforce_security_limits(raw_configs, errors)

    assert len(errors.errors) == 0


# --- _validate_operating_hours tests ---


def test_validate_operating_hours_rejects_invalid_open_hour() -> None:
    """_validate_operating_hours rejects open_hour outside 0-23."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    affordance = MagicMock()
    affordance.id = "test_aff"
    affordance.operating_hours = [25, 8]  # Invalid open_hour
    raw_configs.affordances = [affordance]

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_operating_hours(raw_configs, errors, formatter)

    assert len(errors.errors) == 1
    assert "open_hour" in errors.errors[0]


def test_validate_operating_hours_rejects_invalid_close_hour() -> None:
    """_validate_operating_hours rejects close_hour outside 1-28."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    affordance = MagicMock()
    affordance.id = "test_aff"
    affordance.operating_hours = [6, 30]  # Invalid close_hour
    raw_configs.affordances = [affordance]

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_operating_hours(raw_configs, errors, formatter)

    assert len(errors.errors) == 1
    assert "close_hour" in errors.errors[0]


def test_validate_operating_hours_rejects_wrong_tuple_length() -> None:
    """_validate_operating_hours rejects operating_hours with wrong length."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    affordance = MagicMock()
    affordance.id = "test_aff"
    affordance.operating_hours = [6]  # Only one element
    raw_configs.affordances = [affordance]

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_operating_hours(raw_configs, errors, formatter)

    assert len(errors.errors) == 1
    assert "exactly two" in errors.errors[0]


def test_validate_operating_hours_accepts_valid_hours() -> None:
    """_validate_operating_hours passes with valid operating hours."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    affordance = MagicMock()
    affordance.id = "test_aff"
    affordance.operating_hours = [6, 18]  # Valid 6am-6pm
    raw_configs.affordances = [affordance]

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_operating_hours(raw_configs, errors, formatter)

    assert len(errors.errors) == 0


def test_validate_operating_hours_allows_overnight() -> None:
    """_validate_operating_hours allows overnight hours (close > 24)."""
    compiler = UniverseCompiler()
    errors = CompilationErrorCollector(stage="Test")

    raw_configs = MagicMock()
    affordance = MagicMock()
    affordance.id = "nightclub"
    affordance.operating_hours = [22, 26]  # 10pm-2am (overnight)
    raw_configs.affordances = [affordance]

    def formatter(code, message, location):
        return f"[{code}] {message} @ {location}"

    compiler._validate_operating_hours(raw_configs, errors, formatter)

    assert len(errors.errors) == 0


# --- _position_in_bounds tests ---


def test_position_in_bounds_detects_out_of_bounds() -> None:
    """_position_in_bounds returns False for out of bounds position."""
    compiler = UniverseCompiler()

    substrate = MagicMock()
    substrate.type = "grid"
    substrate.grid.width = 5
    substrate.grid.height = 5
    substrate.grid.depth = None

    # Position outside grid - should be a list [x, y]
    position = [10, 2]

    in_bounds, message = compiler._position_in_bounds(position, substrate)

    assert not in_bounds
    assert "10" in message or "outside" in message.lower()


def test_position_in_bounds_accepts_valid_position() -> None:
    """_position_in_bounds returns True for valid position."""
    compiler = UniverseCompiler()

    substrate = MagicMock()
    substrate.type = "grid"
    substrate.grid.width = 5
    substrate.grid.height = 5
    substrate.grid.depth = None

    # Valid position as list
    position = [2, 3]

    in_bounds, message = compiler._position_in_bounds(position, substrate)

    assert in_bounds
    assert message == ""


# --- _compute_pydantic_hash tests ---


def test_compute_pydantic_hash_stable() -> None:
    """_compute_pydantic_hash produces stable hash for same input."""
    compiler = UniverseCompiler()

    config = MagicMock()
    config.model_dump_json.return_value = '{"key": "value"}'

    hash1 = compiler._compute_pydantic_hash(config)
    hash2 = compiler._compute_pydantic_hash(config)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length


def test_compute_pydantic_hash_different_for_different_input() -> None:
    """_compute_pydantic_hash produces different hash for different input."""
    compiler = UniverseCompiler()

    config1 = MagicMock()
    config1.model_dump_json.return_value = '{"key": "value1"}'

    config2 = MagicMock()
    config2.model_dump_json.return_value = '{"key": "value2"}'

    hash1 = compiler._compute_pydantic_hash(config1)
    hash2 = compiler._compute_pydantic_hash(config2)

    assert hash1 != hash2


# --- _build_cache_fingerprint tests ---


def test_build_cache_fingerprint_returns_tuple(tmp_path: Path) -> None:
    """_build_cache_fingerprint returns tuple of (config_hash, version)."""
    compiler = UniverseCompiler()
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    fingerprint = compiler._build_cache_fingerprint(config_dir)

    assert len(fingerprint) == 2
    config_hash, version = fingerprint
    assert isinstance(config_hash, str)
    assert isinstance(version, str)
    # Version string should be non-empty
    assert len(version) > 0
