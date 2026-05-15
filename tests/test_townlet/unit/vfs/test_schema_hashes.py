"""Tests for VFS schema provenance hashes."""

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.schema import NormalizationSpec, ObservationField, VariableDef
from townlet.vfs.schema_hashes import (
    canonical_observation_schema,
    canonical_variable_schema,
    compute_observation_schema_hash,
    compute_variable_schema_hash,
)


def test_canonical_variable_schema_uses_sorted_contract_fields() -> None:
    """Variable schema hashes should be based on the explicit state ABI fields."""
    variable = VariableDef(
        id="energy",
        scope="agent",
        type="scalar",
        lifetime="tick",
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        default=1.0,
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
        description="Description is not part of the state ABI hash",
    )

    assert canonical_variable_schema((variable,)) == [
        {
            "id": "energy",
            "type": "scalar",
            "scope": "agent",
            "dims": None,
            "lifetime": "tick",
            "readable_by": ["agent", "engine"],
            "writable_by": ["engine"],
            "range": [0.0, 1.0],
        }
    ]


def test_variable_schema_hash_is_order_stable() -> None:
    """Variable order and permission ordering should not change the ABI hash."""
    energy = VariableDef(
        id="energy",
        scope="agent",
        type="scalar",
        lifetime="tick",
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        default=1.0,
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
    )
    position = VariableDef(
        id="position",
        scope="agent",
        type="vecNf",
        dims=2,
        lifetime="tick",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=[0.0, 0.0],
        normalization=NormalizationSpec(kind="minmax", min=[0.0, 0.0], max=[10.0, 10.0]),
    )
    energy_reordered_permissions = energy.model_copy(update={"readable_by": ["agent", "engine"]})

    left_hash = compute_variable_schema_hash((energy, position))
    right_hash = compute_variable_schema_hash((position, energy_reordered_permissions))

    assert left_hash == right_hash
    assert len(left_hash) == 64


def test_variable_schema_hash_changes_when_abi_field_changes() -> None:
    """Changing a hashed variable ABI field should produce a new digest."""
    variable = VariableDef(
        id="energy",
        scope="agent",
        type="scalar",
        lifetime="tick",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=1.0,
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
    )

    changed_range = variable.model_copy(update={"normalization": NormalizationSpec(kind="minmax", min=0.0, max=2.0)})
    changed_permissions = variable.model_copy(update={"writable_by": ["engine", "vtc"]})

    assert compute_variable_schema_hash((variable,)) != compute_variable_schema_hash((changed_range,))
    assert compute_variable_schema_hash((variable,)) != compute_variable_schema_hash((changed_permissions,))


def test_compiler_surfaces_variable_schema_hash(tmp_path: Path) -> None:
    """UniverseCompiler should emit the variable schema hash on the compiled artifact."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    assert compiled.variable_schema_hash == compute_variable_schema_hash(compiled.vfs_variables)
    assert compiled.all_levels is not None
    assert compiled.all_levels[PRIMARY_LEVEL_NAME].variable_schema_hash == compiled.variable_schema_hash
    assert compiled.to_dict()["variable_schema_hash"] == compiled.variable_schema_hash


def test_canonical_observation_schema_uses_ordered_abi_fields() -> None:
    """Observation hashes should use the ordered field ABI, including normalization."""
    field = ObservationField(
        id="obs_energy",
        source_variable="energy",
        exposed_to=["engine", "agent"],
        shape=[1],
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
        semantic_type="bars",
        curriculum_active=True,
    )

    assert canonical_observation_schema((field,)) == [
        {
            "id": "obs_energy",
            "source_variable": "energy",
            "shape": [1],
            "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0},
            "exposed_to": ["agent", "engine"],
            "curriculum_active": True,
            "dtype": "float32",
            "semantic_type": "bars",
        }
    ]


def test_observation_schema_hash_changes_when_order_or_normalization_changes() -> None:
    """Observation field order and normalization are part of the checkpoint ABI."""
    energy = ObservationField(
        id="obs_energy",
        source_variable="energy",
        exposed_to=["agent"],
        shape=[1],
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
    )
    position = ObservationField(
        id="obs_position",
        source_variable="position",
        exposed_to=["agent"],
        shape=[2],
        normalization=NormalizationSpec(kind="minmax", min=[0.0, 0.0], max=[10.0, 10.0]),
        semantic_type="spatial",
    )
    changed_normalization = energy.model_copy(update={"normalization": NormalizationSpec(kind="minmax", min=0.0, max=2.0)})

    assert compute_observation_schema_hash((energy, position)) != compute_observation_schema_hash((position, energy))
    assert compute_observation_schema_hash((energy,)) != compute_observation_schema_hash((changed_normalization,))


def test_observation_schema_hash_is_stable_for_exposure_ordering() -> None:
    """Exposure lists represent an access set, so input ordering should not churn the hash."""
    field = ObservationField(
        id="obs_energy",
        source_variable="energy",
        exposed_to=["engine", "agent"],
        shape=[1],
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0),
    )
    reordered = field.model_copy(update={"exposed_to": ["agent", "engine"]})

    assert compute_observation_schema_hash((field,)) == compute_observation_schema_hash((reordered,))


def test_compiler_surfaces_observation_schema_hash(tmp_path: Path) -> None:
    """UniverseCompiler should emit the observation schema hash on the compiled artifact."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    assert compiled.observation_schema_hash == compute_observation_schema_hash(compiled.vfs_observation_fields)
    assert compiled.all_levels is not None
    assert compiled.all_levels[PRIMARY_LEVEL_NAME].observation_schema_hash == compiled.observation_schema_hash
    assert compiled.to_dict()["observation_schema_hash"] == compiled.observation_schema_hash
