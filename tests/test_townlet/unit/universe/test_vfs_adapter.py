"""Unit tests for vfs_to_observation_spec adapter."""

from townlet.universe.adapters.vfs_adapter import vfs_to_observation_spec
from townlet.vfs.schema import ObservationField as VFSObservationField


def make_field(**kwargs):
    base = {
        "id": "obs_energy",
        "source_variable": "energy",
        "exposed_to": ["agent"],
        "shape": [],
        "normalization": None,
    }
    base.update(kwargs)
    return VFSObservationField(**base)


def test_adapter_scalar_and_vector():
    fields = [
        make_field(id="obs_energy", shape=[]),
        make_field(id="obs_position", shape=[2]),
    ]

    spec = vfs_to_observation_spec(fields)

    assert spec.total_dims == 3
    assert spec.fields[0].name == "obs_energy"
    assert spec.fields[0].dims == 1
    assert spec.fields[1].name == "obs_position"
    assert spec.fields[1].dims == 2
    assert spec.fields[0].uuid != spec.fields[1].uuid


def test_adapter_grid_field():
    fields = [make_field(id="local_grid", shape=[5, 5], source_variable="grid_encoding")]

    spec = vfs_to_observation_spec(fields)

    assert spec.total_dims == 25
    assert spec.fields[0].start_index == 0
    assert spec.fields[0].end_index == 25
    assert spec.fields[0].uuid is not None


def test_adapter_respects_explicit_semantic_type():
    """Verify that explicit semantic_type overrides name heuristics.

    BUG-28: vfs_to_observation_spec was ignoring field.semantic_type and
    always using name heuristics via _semantic_from_name(field.id).

    This test verifies that:
    1. Explicit semantic_type (e.g., "bars") is respected even if name doesn't match pattern
    2. Name heuristics are used only for "custom" semantic_type
    3. Explicit semantic_type overrides name-based inference
    """
    fields = [
        # Field with explicit semantic_type="bars" but non-matching name
        make_field(
            id="weird_name_123",
            source_variable="energy",
            shape=[],
            semantic_type="bars",
        ),
        # Field with explicit semantic_type="spatial" but non-matching name
        make_field(
            id="agent_coords",
            source_variable="position",
            shape=[2],
            semantic_type="spatial",
        ),
        # Field with semantic_type="custom" should fall back to name heuristics
        make_field(
            id="energy_backup",
            source_variable="energy",
            shape=[],
            semantic_type="custom",
        ),
        # Field with semantic_type="custom" and non-matching name should get None
        make_field(
            id="custom_var",
            source_variable="custom",
            shape=[],
            semantic_type="custom",
        ),
    ]

    spec = vfs_to_observation_spec(fields)

    # Field 0: explicit "bars" should override name heuristics
    assert spec.fields[0].semantic_type == "bars"
    assert spec.fields[0].name == "weird_name_123"

    # Field 1: explicit "spatial" should override name heuristics
    assert spec.fields[1].semantic_type == "spatial"
    assert spec.fields[1].name == "agent_coords"

    # Field 2: semantic_type="custom" should trigger name heuristics
    # "energy_backup" contains "energy" so should infer "meter"
    assert spec.fields[2].semantic_type == "meter"
    assert spec.fields[2].name == "energy_backup"

    # Field 3: semantic_type="custom" with non-matching name should get None
    assert spec.fields[3].semantic_type is None
    assert spec.fields[3].name == "custom_var"
