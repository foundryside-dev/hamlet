"""Two-row/two-episode config witness for static observation and engine-only state."""

from pathlib import Path

import pytest
import torch

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

PACK = Path("configs/static_epistemic_access")
LEVEL = "L0_simple"


def _rows(env, observation):
    layout = env.token_spec.compact_layout().get_type("variable_element")
    assert layout is not None
    return observation[:, layout.start : layout.start + layout.capacity * layout.compact_row_width].reshape(
        env.num_agents, layout.capacity, layout.compact_row_width
    ), layout.dynamic_features.index("value_0")


@pytest.mark.parametrize("cached", [False, True])
def test_witness_public_observation_hidden_named_reward_and_immutable_state(tmp_path, cached):
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    if cached:
        artifact = tmp_path / "world.msgpack"
        universe.save_to_cache(artifact)
        universe = CompiledUniverse.load_from_cache(artifact)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    ids = universe.get_level(LEVEL).runtime_action_space.action_ids
    bindings = env.token_spec.get_type("variable_element").slot_bindings
    assert [binding.filler_ref for binding in bindings] == ["public_state"]
    assert universe.get_level(LEVEL).drive.extrinsic.variable_bonuses[0].variable == "hidden_score"
    for episode in range(2):
        observations = env.reset()
        rows, value_lane = _rows(env, observations)
        assert torch.all(rows[:, 0, 0] == 1)
        assert torch.all(rows[:, 0, value_lane] == 0)
        with pytest.raises(PermissionError, match="hidden_score"):
            env.vfs_registry.get_agent("hidden_score", reader="agent")
        assert torch.all(env.vfs_registry.get_agent("readable_unexposed", reader="agent") == 7)
        with pytest.raises(PermissionError, match="immutable_scale"):
            env.vfs_registry.set_engine_value("immutable_scale", torch.tensor(0.5))
        observation, rewards, dones, info = env.step(torch.tensor([ids["ADVANCE"], ids["WAIT"]]))
        assert not dones.any()
        assert torch.equal(env.vfs_registry.get("hidden_score", reader="engine"), torch.tensor([3.0, 2.0]))
        assert torch.equal(rewards, torch.tensor([1.5, 1.0]))
        assert torch.equal(info["reward_components"]["extrinsic"], rewards)
        rows, value_lane = _rows(env, observation)
        assert torch.equal(rows[:, 0, value_lane], torch.tensor([0.25, 0.0]))
        _, rewards, dones, _ = env.step(torch.tensor([ids["WAIT"], ids["ADVANCE"]]))
        assert not dones.any()
        assert torch.equal(rewards, torch.tensor([1.5, 1.5]))
        assert env.vfs_registry.get("immutable_scale", reader="engine").item() == 0.5
        assert torch.all(env.vfs_registry.get("readable_unexposed", reader="engine") == 7)


def test_exposure_contradiction_refuses_at_declared_source(tmp_path):
    import shutil
    import yaml

    pack = tmp_path / "invalid"
    shutil.copytree(PACK, pack)
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"][0]["readable_by"] = ["engine"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert any(str(path) in issue.location and "exposure requires read" in issue.message for issue in caught.value.issues)
