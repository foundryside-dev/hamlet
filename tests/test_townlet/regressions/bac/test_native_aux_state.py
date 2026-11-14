"""Native auxiliary state is staged data, never self-issued restore authority."""

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import compiled as compiled
from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import make_parent
from townlet.curriculum.static import StaticCurriculum
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.registry import VariableRegistry


def curriculum():
    owner = StaticCurriculum(
        commit_mode="completion", difficulty_level=0.25, reward_mode="shaped", active_meters=[], depletion_multiplier=1.0
    )
    owner.initialize_population(1)
    return owner


def test_curriculum_refuses_foreign_parent_without_mutation():
    owner = curriculum()
    before = owner.checkpoint_state()
    with pytest.raises(ValueError):
        owner.prepare_native_state(before, parent_plan=object())
    assert owner.checkpoint_state() == before


def test_curriculum_refuses_fabricated_install_without_mutation():
    owner = curriculum()
    before = owner.checkpoint_state()
    with pytest.raises(ValueError):
        owner.install_native_state(prepared=object(), parent_plan=object(), attempt=object(), restored=object())
    assert owner.checkpoint_state() == before


def test_registry_refuses_foreign_parent_without_mutation():
    owner = VariableRegistry(variables=[], num_agents=1, device=torch.device("cpu"))
    with pytest.raises(ValueError):
        owner.prepare_native_persistent_state({}, env=object(), parent_plan=object())
    assert owner.persistent_state() == {}


def test_registry_refuses_fabricated_install_without_mutation():
    owner = VariableRegistry(variables=[], num_agents=1, device=torch.device("cpu"))
    with pytest.raises(ValueError):
        owner.install_native_persistent_state(prepared=object(), env=object(), parent_plan=object(), attempt=object(), restored=object())
    assert owner.persistent_state() == {}


def native_pair(compiled):
    source, target = make_parent(compiled), make_parent(compiled)
    saved = source.population.get_checkpoint_state()
    target.bind()
    plan = target.population.prepare_native_checkpoint_data(saved, mode="initial")
    return source, target, plan


def test_real_curriculum_plan_stages_without_publication(compiled):
    source, target, plan = native_pair(compiled)
    owner = target.population.curriculum
    before = owner.checkpoint_state()
    prepared = owner.prepare_native_state(source.population.curriculum.checkpoint_state(), parent_plan=plan)
    assert prepared is not None
    assert owner.checkpoint_state() == before
    with pytest.raises(ValueError):
        owner.install_native_state(prepared=prepared, parent_plan=plan, attempt=object(), restored=object())
    assert owner.checkpoint_state() == before


def test_real_curriculum_plan_refuses_invalid_state_before_publication(compiled):
    source, target, plan = native_pair(compiled)
    owner = target.population.curriculum
    before = owner.checkpoint_state()
    malformed = source.population.curriculum.checkpoint_state()
    malformed["completion"]["generation"] = -1
    with pytest.raises(ValueError):
        owner.prepare_native_state(malformed, parent_plan=plan)
    assert owner.checkpoint_state() == before


def test_real_registry_plan_stages_without_publication(compiled):
    source, target, plan = native_pair(compiled)
    env = target.population.env
    owner = env.vfs_registry
    before = owner.persistent_state()
    prepared = owner.prepare_native_persistent_state(source.population.env.vfs_registry.persistent_state(), env=env, parent_plan=plan)
    assert prepared is not None
    after = owner.persistent_state()
    assert set(after) == set(before)
    assert all(torch.equal(after[key], before[key]) for key in before)

    with pytest.raises(ValueError):
        owner.install_native_persistent_state(prepared=prepared, env=env, parent_plan=plan, attempt=object(), restored=object())
    after = owner.persistent_state()
    assert all(torch.equal(after[key], before[key]) for key in before)


@pytest.fixture(scope="module")
def persistent_compiled(tmp_path_factory):
    source = Path(__file__).resolve().parents[4] / "configs/test/bac_remediation/feedforward"
    pack = tmp_path_factory.mktemp("native_aux_config") / "pack"
    shutil.copytree(source, pack, ignore=shutil.ignore_patterns(".compiled"))
    path = pack / "variables.yaml"
    declarations = yaml.safe_load(path.read_text())
    declarations["variables"]["declarations"].append(
        {
            "id": "native_persistent",
            "scope": "global",
            "type": "scalar",
            "lifetime": "persistent",
            "readable_by": ["engine", "agent"],
            "writable_by": ["engine"],
            "semantic_type": "custom",
            "exposed_to": [],
            "initial_value": 1.0,
        }
    )
    declarations["variables"]["declarations"].append(
        {
            "id": "native_persistent_flag",
            "scope": "global",
            "type": "bool",
            "lifetime": "persistent",
            "readable_by": ["engine", "agent"],
            "writable_by": ["engine"],
            "semantic_type": "custom",
            "exposed_to": [],
            "initial_value": False,
        }
    )
    path.write_text(yaml.safe_dump(declarations, sort_keys=False))
    return UniverseCompiler().compile(pack, primary_level="L0_0_minimal")


def test_native_persistent_stage_refuses_sparse_before_publication(persistent_compiled):
    _, target, plan = native_pair(persistent_compiled)
    env = target.population.env
    owner = env.vfs_registry
    before = owner.persistent_state()
    assert "native_persistent" in before
    payload = dict(before)
    payload["native_persistent"] = before["native_persistent"].to_sparse()
    with pytest.raises(ValueError, match="ordinary|layout|strided"):
        owner.prepare_native_persistent_state(payload, env=env, parent_plan=plan)
    assert torch.equal(owner.persistent_state()["native_persistent"], before["native_persistent"])


def test_native_persistent_stage_accepts_nonempty_ordinary_data_without_publication(persistent_compiled):
    _, target, plan = native_pair(persistent_compiled)
    env = target.population.env
    owner = env.vfs_registry
    before = owner.persistent_state()
    assert set(before) == {"native_persistent", "native_persistent_flag"}
    payload = {
        "native_persistent": torch.full_like(before["native_persistent"], 7.0),
        "native_persistent_flag": torch.ones_like(before["native_persistent_flag"]),
    }
    prepared = owner.prepare_native_persistent_state(payload, env=env, parent_plan=plan)
    assert prepared is not None
    after = owner.persistent_state()
    assert all(torch.equal(after[key], before[key]) for key in before)
    with pytest.raises(ValueError):
        owner.install_native_persistent_state(prepared=prepared, env=env, parent_plan=plan, attempt=object(), restored=object())
    after = owner.persistent_state()
    assert all(torch.equal(after[key], before[key]) for key in before)


def test_native_persistent_stage_rejects_key_overrides_without_callbacks(persistent_compiled):
    _, target, plan = native_pair(persistent_compiled)
    env = target.population.env
    owner = env.vfs_registry
    calls = []

    class Key(str):
        armed = False

        def __hash__(self):
            if self.armed:
                calls.append("hash")
                raise AssertionError("untrusted key hash executed")
            return str.__hash__(self)

        def __eq__(self, other):
            if self.armed:
                calls.append("eq")
                raise AssertionError("untrusted key equality executed")
            return str.__eq__(self, other)

    before = owner.persistent_state()
    payload = {Key(name): value for name, value in before.items()}
    calls.clear()
    Key.armed = True
    try:
        with pytest.raises(ValueError, match="ordinary|keys"):
            owner.prepare_native_persistent_state(payload, env=env, parent_plan=plan)
    finally:
        Key.armed = False
    assert calls == []
    assert torch.equal(owner.persistent_state()["native_persistent"], before["native_persistent"])
