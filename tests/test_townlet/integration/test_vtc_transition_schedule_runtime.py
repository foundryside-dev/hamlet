"""Runtime checks for compiled VTC transition schedules."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.universe.compiler import UniverseCompiler

LEVEL_NAME = "L5_multi_agent"


def _copy_l5_pack(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(Path("configs") / LEVEL_NAME, target)
    return target


def _write_social_residue_rule(config_dir: Path, *, variable_id: str = "trust", delta: float = 0.1) -> None:
    payload = {
        "version": "1.0",
        "social_residue": [
            {
                "id": "constant_pair_delta",
                "phase": "apply_social_residue_effects",
                "kind": "social_residue",
                "reads": [variable_id],
                "condition": None,
                "writes": [
                    {
                        "variable_id": variable_id,
                        "effect": "pair_delta",
                        "expression": str(delta),
                        "composition": "additive_delta",
                        "condition": None,
                        "clamp": [0.0, 1.0],
                        "scope": "pair",
                    }
                ],
            }
        ],
    }
    (config_dir / "transition_rules.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))


def test_social_residue_rules_are_config_driven_runtime_transitions(tmp_path: Path) -> None:
    baseline_dir = _copy_l5_pack(tmp_path, "baseline")
    social_dir = _copy_l5_pack(tmp_path, "social")
    _write_social_residue_rule(social_dir, delta=0.1)

    compiler = UniverseCompiler()
    baseline = compiler.compile(baseline_dir, primary_level=LEVEL_NAME, use_cache=False)
    social = compiler.compile(social_dir, primary_level=LEVEL_NAME, use_cache=False)
    baseline_level = baseline.get_level(LEVEL_NAME)
    social_level = social.get_level(LEVEL_NAME)

    assert baseline_level.transition_graph_hash != social_level.transition_graph_hash
    assert baseline_level.vfs_hash != social_level.vfs_hash
    assert len(baseline_level.transition_schedule.social_residue_program.rules) == 0
    assert len(social_level.transition_schedule.social_residue_program.rules) == 1

    baseline_env = baseline.create_environment(num_agents=3, level_name=LEVEL_NAME, device="cpu")
    social_env = social.create_environment(num_agents=3, level_name=LEVEL_NAME, device="cpu")

    assert baseline_env.__class__ is social_env.__class__
    assert torch.allclose(baseline_env.vfs_registry.get("trust", reader="engine"), torch.full((3, 3), 0.5))
    assert torch.allclose(social_env.vfs_registry.get("trust", reader="engine"), torch.full((3, 3), 0.5))

    actions = torch.zeros(3, dtype=torch.long)
    baseline_env.step(actions)
    social_env.step(actions)

    assert torch.allclose(baseline_env.vfs_registry.get("trust", reader="engine"), torch.full((3, 3), 0.5))
    assert torch.allclose(social_env.vfs_registry.get("trust", reader="engine"), torch.full((3, 3), 0.6))


def test_transition_rules_typo_key_fails_at_load_not_silently(tmp_path: Path) -> None:
    """A typo'd write key must fail at config load; the raw-dict path used to
    silently drop it, turning a conditional rule unconditional."""
    config_dir = _copy_l5_pack(tmp_path, "typo-key")
    payload = {
        "version": "1.0",
        "social_residue": [
            {
                "id": "constant_pair_delta",
                "phase": "apply_social_residue_effects",
                "kind": "social_residue",
                "reads": ["trust"],
                "condition": None,
                "writes": [
                    {
                        "variable_id": "trust",
                        "effect": "pair_delta",
                        "expression": "0.1",
                        "composition": "additive_delta",
                        "clamp": [0.0, 1.0],
                        "scope": "pair",
                        "condtion": "trust > 0.5",
                    }
                ],
            }
        ],
    }
    (config_dir / "transition_rules.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))

    with pytest.raises(Exception, match="condtion"):
        UniverseCompiler().compile(config_dir, primary_level=LEVEL_NAME, use_cache=False)


def test_transition_rules_missing_version_fails_at_load(tmp_path: Path) -> None:
    config_dir = _copy_l5_pack(tmp_path, "missing-version")
    payload = {
        "social_residue": [],
    }
    (config_dir / "transition_rules.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))

    with pytest.raises(Exception, match="version"):
        UniverseCompiler().compile(config_dir, primary_level=LEVEL_NAME, use_cache=False)


def test_social_residue_rules_fail_loudly_for_unknown_targets(tmp_path: Path) -> None:
    config_dir = _copy_l5_pack(tmp_path, "missing-target")
    _write_social_residue_rule(config_dir, variable_id="missing_social_variable")

    with pytest.raises(ValueError, match="targets unknown VFS variable 'missing_social_variable'"):
        UniverseCompiler().compile(config_dir, primary_level=LEVEL_NAME, use_cache=False)


def test_environment_runtime_does_not_embed_social_residue_domain_semantics() -> None:
    source = Path("src/townlet/environment/vectorized_env.py").read_text()

    forbidden_tokens = (
        "social_residue",
        "trust",
        "obligation",
        "reputation",
        "norm_legitimacy",
        "faction",
        "institution",
    )
    for token in forbidden_tokens:
        assert token not in source
