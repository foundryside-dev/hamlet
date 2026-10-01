"""Transition commit preflights selected writes without rewriting read-only snapshots."""

from types import SimpleNamespace

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef
from townlet.vfs.transition_schedule import VTCTransitionState


def _environment():
    registry = VariableRegistry(
        variables=[
            VariableDef(
                id=identifier, scope="agent", type="scalar", lifetime="episode", default=3.0, readable_by=["engine"], writable_by=writers
            )
            for identifier, writers in (("allowed", ["engine"]), ("literal", []))
        ],
        num_agents=2,
        device=torch.device("cpu"),
    )
    bars = {"energy": torch.tensor([1.0, 1.0])}
    return (
        SimpleNamespace(
            vfs_registry=registry, dones=torch.tensor([False, False]), _set_vtc_bar_value=lambda key, value: bars.__setitem__(key, value)
        ),
        bars,
    )


def test_denied_transition_target_prevents_all_bar_vfs_done_mutation():
    env, bars = _environment()
    state = VTCTransitionState(
        vfs_state={"allowed": torch.tensor([8.0, 8.0]), "literal": torch.tensor([3.0, 3.0])},
        bars_state={"energy": torch.tensor([0.0, 0.0])},
        dones=torch.tensor([True, True]),
        attempted_vfs_targets=frozenset({"allowed", "literal"}),
    )
    with pytest.raises(PermissionError, match="literal"):
        VectorizedHamletEnv._commit_vtc_transition_state(env, state)
    assert torch.equal(bars["energy"], torch.tensor([1.0, 1.0]))
    assert not env.dones.any()
    assert torch.equal(env.vfs_registry.get("allowed", reader="engine"), torch.tensor([3.0, 3.0]))


def test_unused_immutable_snapshot_is_not_written():
    env, bars = _environment()
    state = VTCTransitionState(
        vfs_state={"allowed": torch.tensor([8.0, 8.0]), "literal": torch.tensor([3.0, 3.0])},
        bars_state={"energy": torch.tensor([0.0, 0.0])},
        dones=torch.tensor([True, True]),
        attempted_vfs_targets=frozenset({"allowed"}),
    )
    VectorizedHamletEnv._commit_vtc_transition_state(env, state)
    assert torch.equal(env.vfs_registry.get("allowed", reader="engine"), torch.tensor([8.0, 8.0]))
    assert torch.equal(env.vfs_registry.get("literal", reader="engine"), torch.tensor([3.0, 3.0]))
    assert env.dones.all()


def test_immutable_global_agent_literals_survive_wait_and_reset_lifecycle(tmp_path):
    import shutil

    import yaml

    from townlet.universe.compiler import UniverseCompiler

    pack = tmp_path / "pack"
    shutil.copytree("configs/simple", pack)
    payload = yaml.safe_load((pack / "variables.yaml").read_text())
    literals = [
        dict(
            id=f"literal_{scope}_{lifetime}",
            scope=scope,
            lifetime=lifetime,
            type="scalar",
            semantic_type="custom",
            initial_value=3.0,
            readable_by=["engine"],
            writable_by=[],
            exposed_to=[],
        )
        for scope in ("global", "agent")
        for lifetime in ("tick", "episode", "persistent")
    ]
    payload["variables"]["declarations"].extend(literals)
    (pack / "variables.yaml").write_text(yaml.safe_dump(payload))
    compiled = UniverseCompiler().compile(pack, primary_level="L0_simple", use_cache=False)
    env = compiled.create_environment(num_agents=2, level_name="L0_simple", device="cpu")
    wait = next(action.id for action in env.action_space.actions if action.name == "WAIT")
    for _ in range(2):
        env.reset()
        env.step(torch.full((2,), wait))
        for declaration in literals:
            assert torch.all(env.vfs_registry.get(declaration["id"], reader="engine") == 3.0)
