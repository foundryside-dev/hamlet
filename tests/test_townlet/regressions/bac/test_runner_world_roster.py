"""Real runner construction must preserve the authored run world declaration."""

import json
import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.config.world_roster import WorldRosterDeclaration
from townlet.demo.runner import DemoRunner


@pytest.fixture
def runner_inputs(tmp_path):
    root = Path(__file__).resolve().parents[4]
    pack = tmp_path / "pack"
    shutil.copytree(root / "configs/test/bac_remediation/feedforward", pack, ignore=shutil.ignore_patterns(".compiled"))
    training_path = pack / "levels/L0_0_minimal/training.yaml"
    doc = yaml.safe_load(training_path.read_text())
    doc["training"]["population"]["size"] = 2
    training_path.write_text(yaml.safe_dump(doc, sort_keys=False))
    return dict(
        config_dir=pack,
        db_path=tmp_path / "run.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=2,
        level_name="L0_0_minimal",
        world_roster=WorldRosterDeclaration(("declared-B", "declared-A")),
    )


def test_runner_persists_and_reuses_exact_authored_roster(runner_inputs, tmp_path):
    expected = runner_inputs["world_roster"]
    with DemoRunner(**runner_inputs) as runner:
        assert runner.world_roster is expected
        manifest = tmp_path / "run-world-roster.json"
        assert json.loads(manifest.read_bytes()) == expected.to_dict()
        original = manifest.read_bytes()
    with DemoRunner(**runner_inputs) as resumed:
        assert resumed.world_roster.to_dict() == expected.to_dict()
        assert manifest.read_bytes() == original


@pytest.mark.parametrize("damage", ["missing", "order", "extra", "schema"])
def test_runner_refuses_invalid_existing_manifest_before_rng_or_storage_mutation(runner_inputs, tmp_path, damage):
    with DemoRunner(**runner_inputs):
        pass
    manifest = tmp_path / "run-world-roster.json"
    payload = json.loads(manifest.read_bytes())
    if damage == "missing":
        manifest.unlink()
    else:
        if damage == "order":
            payload["world_ids"].reverse()
        elif damage == "extra":
            payload["invented"] = True
        else:
            payload["schema"] = "obsolete"
        manifest.write_text(json.dumps(payload))
    database = runner_inputs["db_path"].read_bytes()
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError, match="roster"):
        DemoRunner(**runner_inputs)
    assert torch.equal(before, torch.get_rng_state())
    assert runner_inputs["db_path"].read_bytes() == database


def test_runner_refuses_roster_cardinality_before_creating_run_files(runner_inputs, tmp_path):
    runner_inputs["world_roster"] = WorldRosterDeclaration(("only-world",))
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError, match="roster"):
        DemoRunner(**runner_inputs)
    assert torch.equal(before, torch.get_rng_state())
    assert not runner_inputs["db_path"].exists()
    assert not runner_inputs["checkpoint_dir"].exists()
    assert not (tmp_path / "run-world-roster.json").exists()
