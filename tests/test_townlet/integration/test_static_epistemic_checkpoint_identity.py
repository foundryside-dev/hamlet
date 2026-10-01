"""Policy-only edits must refuse exact resume and serving before weights change."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.integration.test_live_inference_checkpoint_identity import (
    LEVEL,
    SOURCE_PACK,
    _make_server,
    _q_state_snapshot,
    _write_checkpoint,
)
from townlet.demo.runner import DemoRunner
from townlet.universe.compiled import CompiledUniverse

TOKEN_BRAIN = SOURCE_PACK.parents[1] / "benchmarks/l2_token_regression/brain_templates/token_feedforward_mean.yaml"


def _policy_pack(tmp_path: Path, name: str, architecture: str) -> Path:
    pack = tmp_path / name
    shutil.copytree(SOURCE_PACK, pack, ignore=shutil.ignore_patterns(".compiled", "*.msgpack"))
    variables = yaml.safe_load((pack / "variables.yaml").read_text())
    variables["variables"]["item_profiles"] = ["policy_item"]
    variables["variables"]["declarations"].append(
        {
            "id": "policy_charge",
            "profile": "policy_item",
            "scope": "item",
            "type": "scalar",
            "lifetime": "episode",
            "semantic_type": "custom",
            "initial_value": 2.0,
            "exposed_to": [],
            "readable_by": ["engine", "agent"],
            "writable_by": ["engine"],
        }
    )
    variables["variables"]["declarations"].append(
        {
            "id": "public_charge",
            "profile": "policy_item",
            "scope": "item",
            "type": "scalar",
            "lifetime": "episode",
            "semantic_type": "custom",
            "initial_value": 3.0,
            "exposed_to": ["agent"],
            "readable_by": ["engine", "agent"],
            "writable_by": ["engine"],
            "normalization": {"kind": "minmax", "min": 0.0, "max": 20.0, "clip": True},
        }
    )
    items_path = pack / "items.yaml"
    items = yaml.safe_load(items_path.read_text())
    items["items"]["max_items_in_world"] = 2
    items["items"]["max_items_per_agent"] = 1
    items["items"]["item_types"] = [
        {
            "id": "policy_cell",
            "name": "Policy cell",
            "icon": "P",
            "tags": ["policy"],
            "exclusive": True,
            "vfs_profile": "policy_item",
            "description": "Permission identity fixture",
            "duration": None,
            "cooldown": None,
            "interactions": {"on_pickup": [], "on_use": [], "on_drop": [], "local_commands": [], "inventory_commands": []},
        }
    ]
    items_path.write_text(yaml.safe_dump(items, sort_keys=False))
    (pack / "variables.yaml").write_text(yaml.safe_dump(variables, sort_keys=False))
    if architecture == "token_set":
        shutil.copyfile(TOKEN_BRAIN, pack / "brain.yaml")
    return pack


def _policy_edit(pack: Path, target: str, permission: str) -> None:
    path = pack / "variables.yaml"
    variables = yaml.safe_load(path.read_text())
    name = {"public": "deficit_energy", "hidden": "position", "item": "policy_charge", "public_item": "public_charge"}[target]
    declaration = next(v for v in variables["variables"]["declarations"] if v["id"] == name)
    if permission == "writer":
        declaration["writable_by"] = []
    else:
        declaration["readable_by"] = ["engine"]
    path.write_text(yaml.safe_dump(variables, sort_keys=False))


@pytest.mark.asyncio
@pytest.mark.parametrize("architecture", ["feedforward", "token_set"])
@pytest.mark.parametrize(
    "target,permission",
    [("public", "writer"), ("hidden", "reader"), ("hidden", "writer"), ("item", "reader"), ("item", "writer"), ("public_item", "writer")],
)
async def test_policy_only_change_refuses_serving_and_resume_before_weight_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    architecture: str,
    target: str,
    permission: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    base_pack = _policy_pack(tmp_path, "base", architecture)
    changed_pack = _policy_pack(tmp_path, "changed", architecture)
    _policy_edit(changed_pack, target, permission)
    checkpoint_dir = tmp_path / "checkpoints"
    base = _make_server(base_pack, checkpoint_dir)
    _write_checkpoint(checkpoint_dir, base)
    changed = _make_server(changed_pack, checkpoint_dir)
    before = _q_state_snapshot(changed)
    old_level = base.compiled_universe.get_level(LEVEL)
    new_level = changed.compiled_universe.get_level(LEVEL)
    assert old_level.variable_schema_hash != new_level.variable_schema_hash
    assert old_level.vfs_hash != new_level.vfs_hash
    assert old_level.token_type_schema_hash == new_level.token_type_schema_hash
    assert old_level.layout_hash == new_level.layout_hash
    assert old_level.token_spec.total_dims == new_level.token_spec.total_dims

    with pytest.raises(ValueError, match="vfs_hash mismatch"):
        await changed._check_and_load_checkpoint()
    assert all(torch.equal(before[k], changed.population.q_network.state_dict()[k]) for k in before)
    assert changed.current_checkpoint_path is None

    # Use real initialized server components as the runner's required runtime
    # dependencies; exercise the production resume consumer without training.
    with DemoRunner(changed_pack, tmp_path / "resume.db", checkpoint_dir, level_name=LEVEL) as runner:
        runner.env, runner.population, runner.curriculum = changed.env, changed.population, changed.curriculum
        with pytest.raises(ValueError, match="vfs_hash mismatch"):
            runner.load_checkpoint()
        assert all(torch.equal(before[k], runner.population.q_network.state_dict()[k]) for k in before)
        assert runner.current_episode == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("architecture", ["feedforward", "token_set"])
async def test_equivalent_role_order_reloads_and_serves_the_same_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    architecture: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    base_pack = _policy_pack(tmp_path, "base", architecture)
    reordered_pack = _policy_pack(tmp_path, "reordered", architecture)
    path = reordered_pack / "variables.yaml"
    data = yaml.safe_load(path.read_text())
    for declaration in data["variables"]["declarations"]:
        declaration["readable_by"].reverse()
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    checkpoint_dir = tmp_path / "checkpoints"
    base = _make_server(base_pack, checkpoint_dir)
    _write_checkpoint(checkpoint_dir, base)
    reordered = _make_server(reordered_pack, checkpoint_dir)
    assert base.compiled_universe.get_level(LEVEL).variable_schema_hash == reordered.compiled_universe.get_level(LEVEL).variable_schema_hash
    # Coherence accepts an exact MessagePack-style reconstruction as well.
    artifact = tmp_path / "reordered.msgpack"
    reordered.compiled_universe.save_to_cache(artifact)
    rebuilt = CompiledUniverse.load_from_cache(artifact)
    assert rebuilt.get_level(LEVEL).vfs_hash == base.compiled_universe.get_level(LEVEL).vfs_hash
    before = _q_state_snapshot(reordered)
    assert await reordered._check_and_load_checkpoint()
    assert any(not torch.equal(before[k], reordered.population.q_network.state_dict()[k]) for k in before)
