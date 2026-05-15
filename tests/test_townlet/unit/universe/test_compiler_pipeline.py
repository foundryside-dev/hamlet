"""Pipeline-level tests for UniverseCompiler staging."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest
import torch
import yaml

import townlet.universe.compiler as compiler_module
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.observation_builder import VFSObservationSpec


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_stage_markers_emit_in_order(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Compiler should emit the seven stage markers in order."""
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()

    caplog.set_level(logging.INFO, logger="townlet.universe.compiler")
    compiler.compile(config_dir, primary_level="L0_test", use_cache=False)

    markers = [
        record.message for record in caplog.records if record.name == "townlet.universe.compiler" and record.message.startswith("Stage ")
    ]

    assert markers == [
        "Stage 1: Parse v2.1 configs",
        "Stage 2: Build symbol table",
        "Stage 3: Resolve references",
        "Stage 4: Cross-validate semantics",
        "Stage 5: Enrich shared schemas and effects",
        "Stage 6: Compile levels and optimization data",
        "Stage 7: Emit compiled universe",
    ]


def test_stage3_resolves_invalid_affordance_reference(tmp_path: Path) -> None:
    """Unknown item references in level spawn rules should fail during Stage 3 resolution."""
    config_dir = _copy_experiment(tmp_path)
    items_path = config_dir / "levels" / "L0_test" / "items.yaml"
    items_payload = {
        "version": "1.0",
        "items": [
            {
                "item_type": "ghost_item",
                "spawn_count": 1,
            }
        ],
    }
    items_path.write_text(yaml.safe_dump(items_payload))

    compiler = UniverseCompiler()
    with pytest.raises(CompilationError) as excinfo:
        compiler.compile(config_dir, primary_level="L0_test", use_cache=False)

    assert "Stage 3: Reference Resolution" in str(excinfo.value)
    assert "ghost_item" in str(excinfo.value)


def test_compile_requires_explicit_primary_level(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    with pytest.raises(ValueError, match="requires an explicit primary_level"):
        UniverseCompiler().compile(config_dir, use_cache=False)


def test_compile_rejects_level_directory_input(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    level_dir = config_dir / "levels" / "L0_test"

    with pytest.raises(CompilationError, match="Cannot validate level directory directly"):
        UniverseCompiler().compile(level_dir, primary_level="L0_test", use_cache=False)


def test_obs_vfs_dims_come_from_compiled_vfs_observation_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = Path("configs/test/effects_smoke")
    forced_spec = VFSObservationSpec(global_vfs_dim=7, agent_vfs_dim=0, item_vfs_dim=0)

    monkeypatch.setattr(
        compiler_module.VFSObservationSpec,
        "from_compiled_profiles",
        classmethod(lambda cls, compiled_profiles, *, max_items_per_agent: forced_spec),
    )

    compiled = UniverseCompiler().compile(config_dir, primary_level="L0_effects", use_cache=False)
    obs_vfs = next(field for field in compiled.observation_spec.fields if field.name == "obs_vfs")

    assert compiled.vfs_observation_spec is forced_spec
    assert obs_vfs.dims == forced_spec.total_vfs_dim


@pytest.mark.parametrize(
    ("field_name", "patch_name"),
    [
        ("obs_grid_encoding", "_encode_full_grid"),
        ("obs_position", "_encode_position_observation"),
        ("obs_velocity", "_encode_velocity_observation"),
    ],
)
def test_runtime_observation_fields_fail_on_dimension_mismatch(
    tmp_path: Path,
    field_name: str,
    patch_name: str,
) -> None:
    config_dir = _copy_experiment(tmp_path)
    compiled = UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)
    env = compiled.create_environment(num_agents=2, level_name="L0_test", device=torch.device("cpu"))
    field = next(field for field in env.observation_spec.fields if field.name == field_name)

    wrong = torch.zeros((env.num_agents, max(field.dims - 1, 0)), device=env.device)
    if patch_name == "_encode_full_grid":
        setattr(env.substrate, patch_name, lambda positions, affordances: wrong)
    else:
        setattr(env, patch_name, lambda: wrong)

    with pytest.raises(ValueError, match=f"Observation field '{field_name}' produced"):
        env._get_observations()


def test_domain_compiler_modules_own_their_implementation() -> None:
    compiler_source = Path(compiler_module.__file__).read_text()
    forbidden_compiler_methods = [
        "_build_observation_spec",
        "_build_observation_activity",
        "_build_action_space_metadata",
        "_build_meter_metadata",
        "_build_affordance_metadata",
        "_build_optimization_data",
        "_compile_vfs_profiles",
        "_compile_effects_catalog",
    ]
    for method_name in forbidden_compiler_methods:
        assert f"def {method_name}" not in compiler_source

    compilers_dir = Path(compiler_module.__file__).parent / "compilers"
    for module_path in compilers_dir.glob("*.py"):
        source = module_path.read_text()
        assert "_delegate" not in source
