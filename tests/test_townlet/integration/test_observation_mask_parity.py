"""Integration tests to ensure observation masks follow metadata/curriculum flags."""

from __future__ import annotations

from tests.test_townlet.helpers.config_builder import mutate_curriculum_yaml, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _compile(tmp_path, name: str, curriculum_mutator=None):
    """Build a test config pack and compile it."""
    config_dir = prepare_config_dir(tmp_path, name=name)
    if curriculum_mutator is not None:
        mutate_curriculum_yaml(config_dir, curriculum_mutator)

    compiler = UniverseCompiler()
    return compiler.compile(config_dir, use_cache=False)


def _get_field(spec, name: str):
    return next(f for f in spec.fields if f.name == name)


def _get_vfs_field(compiled, name: str):
    return next(f for f in compiled.vfs_observation_fields if f.id == name)


def test_global_grid_masked_when_partial_vision(tmp_path):
    """Global grid encoding should be masked when curriculum requests partial vision."""
    compiled = _compile(
        tmp_path,
        name="mask_partial",
        curriculum_mutator=lambda data: data["curriculum"].update({"active_vision": "partial"}),
    )

    grid_field = _get_field(compiled.observation_spec, "obs_grid_encoding")
    mask_slice = compiled.observation_activity.active_mask[grid_field.start_index : grid_field.end_index]
    assert all(mask is False for mask in mask_slice), "Global grid dims should be masked under partial vision"

    vfs_field = _get_vfs_field(compiled, "obs_grid_encoding")
    assert vfs_field.curriculum_active is False, "VFS field should reflect masked curriculum state"


def test_global_grid_active_when_global_vision(tmp_path):
    """Global grid encoding remains active when curriculum requests global vision."""
    compiled = _compile(tmp_path, name="mask_global")  # default curriculum uses global vision

    grid_field = _get_field(compiled.observation_spec, "obs_grid_encoding")
    mask_slice = compiled.observation_activity.active_mask[grid_field.start_index : grid_field.end_index]
    assert all(mask is True for mask in mask_slice), "Global grid dims should be active under global vision"

    vfs_field = _get_vfs_field(compiled, "obs_grid_encoding")
    assert vfs_field.curriculum_active is True, "VFS field should be active when observation is active"
