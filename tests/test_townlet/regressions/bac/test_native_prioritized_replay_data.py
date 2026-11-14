"""Real PER/POP native data staging; actual C installation remains integration-owned."""

from __future__ import annotations

import copy
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import make_parent
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_contract import StagedReplayData
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture(scope="module")
def per_compiled(tmp_path_factory: pytest.TempPathFactory) -> Any:
    root = Path(__file__).resolve().parents[4]
    config = tmp_path_factory.mktemp("native-per") / "config"
    shutil.copytree(root / "configs/test/bac_remediation/feedforward", config)
    brain_path = config / "brain.yaml"
    brain = yaml.safe_load(brain_path.read_text())
    brain["replay"].update(prioritized=True, priority_alpha=0.6, priority_beta=0.4, priority_beta_annealing=True)
    brain_path.write_text(yaml.safe_dump(brain))
    return UniverseCompiler().compile(config, primary_level="L0_0_minimal", use_cache=False)


def assert_equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for first, second in zip(left, right, strict=True):
            assert_equal(first, second)
    else:
        assert left == right


def prepared_parent(compiled: Any) -> tuple[Any, Any, dict[str, Any]]:
    source, target = make_parent(compiled), make_parent(compiled)
    assert isinstance(source.population.replay_buffer, PrioritizedReplayBuffer)
    assert isinstance(target.population.replay_buffer, PrioritizedReplayBuffer)
    saved = source.population.get_checkpoint_state()
    target.bind()
    plan = target.population.prepare_native_checkpoint_data(saved, mode="initial")
    state = target.population.native_replay_restore_state(plan=plan)
    return target, plan, state


def stage(target: Any, plan: Any, state: dict[str, Any]) -> StagedReplayData:
    return target.population.replay_buffer.stage_native_restore(
        state, expected_obs_dim=target.env.observation_dim, parent_plan=plan, lineage=None
    )


def refuse_without_finalizer(target: Any, plan: Any, data: Any) -> None:
    target.population.replay_buffer.install_native_restore(data, parent_plan=plan, attempt=object(), restored=object(), lineage=None)


def test_native_per_rejects_unissued_parent(per_compiled: Any) -> None:
    target = make_parent(per_compiled)
    replay = target.population.replay_buffer
    before = replay.serialize()
    with pytest.raises(ValueError):
        stage(target, object(), before)
    assert_equal(replay.serialize(), before)


def test_native_per_stages_real_parent_without_publication(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    replay = target.population.replay_buffer
    before = replay.serialize()
    data = stage(target, plan, state)
    assert type(data) is StagedReplayData
    assert target.population.replay_buffer is replay
    assert_equal(replay.serialize(), before)
    with pytest.raises(TypeError):
        copy.deepcopy(data)
    with pytest.raises((ValueError, RuntimeError)):
        refuse_without_finalizer(target, plan, data)
    assert_equal(replay.serialize(), before)


def test_native_per_rejects_fabricated_data(per_compiled: Any) -> None:
    target, plan, _ = prepared_parent(per_compiled)
    before = target.population.replay_buffer.serialize()
    with pytest.raises(ValueError, match="foreign|fabricated|consumed"):
        refuse_without_finalizer(target, plan, object.__new__(StagedReplayData))
    assert_equal(target.population.replay_buffer.serialize(), before)


def test_native_per_rejects_ordinary_prepared_replay(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    replay = target.population.replay_buffer
    prepared = replay.prepare_serialized(state, expected_obs_dim=target.env.observation_dim, lineage=None)
    with pytest.raises(ValueError, match="foreign|fabricated|consumed"):
        refuse_without_finalizer(target, plan, prepared)
    assert_equal(replay.serialize(), state)


def test_native_per_data_survives_later_prepare_currency(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    replay = target.population.replay_buffer
    first = stage(target, plan, state)
    second = stage(target, plan, state)
    assert first is not second
    # Read-only oracle: authentic data validity does not borrow an old RNG token.
    assert replay._native_replay_payload(first, parent_plan=plan) is not None
    with pytest.raises((ValueError, RuntimeError)):
        refuse_without_finalizer(target, plan, first)
    assert_equal(replay.serialize(), state)


def test_native_per_data_owns_priority_ids_and_sampler(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    replay = target.population.replay_buffer
    expected = copy.deepcopy(state)
    data = stage(target, plan, state)
    # The source-owned payload is inspected only as an assertion oracle.
    material = replay._native_replay_payload(data, parent_plan=plan).material
    assert not np.shares_memory(material.priorities, state["priorities"])
    assert not np.shares_memory(material.unit_ids, state["unit_ids"])
    state["priorities"].fill(777)
    state["unit_ids"].fill(777)
    state["sampling_rng"]["state"].clear()
    np.testing.assert_array_equal(material.priorities, expected["priorities"])
    np.testing.assert_array_equal(material.unit_ids, expected["unit_ids"])
    assert material.sampler.rng is not None
    assert_equal(material.sampler.rng.bit_generator.state, expected["sampling_rng"]["state"])
    assert_equal(replay.serialize(), expected)


def test_native_per_rejects_foreign_receiver(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    other, other_plan, other_state = prepared_parent(per_compiled)
    data = stage(target, plan, state)
    with pytest.raises(ValueError, match="foreign|fabricated|consumed"):
        refuse_without_finalizer(other, other_plan, data)
    assert_equal(other.population.replay_buffer.serialize(), other_state)


def test_native_per_rejects_wrong_parent_plan(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    data = stage(target, plan, state)
    _, other_plan, _ = prepared_parent(per_compiled)
    with pytest.raises(ValueError, match="another parent"):
        refuse_without_finalizer(target, other_plan, data)
    assert_equal(target.population.replay_buffer.serialize(), state)


def test_native_per_rejects_lawfully_changed_receiver(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    replay = target.population.replay_buffer
    data = stage(target, plan, state)
    replay.configure_sampling(sampling_mode=state["sampling_mode"], rng=np.random.default_rng(198), origin="authored")
    before = replay.serialize()
    with pytest.raises(ValueError, match="changed after staging"):
        refuse_without_finalizer(target, plan, data)
    assert_equal(replay.serialize(), before)


def test_native_per_rejects_foreign_thread(per_compiled: Any) -> None:
    target, plan, state = prepared_parent(per_compiled)
    data = stage(target, plan, state)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(refuse_without_finalizer, target, plan, data)
        with pytest.raises(ValueError, match="process or thread"):
            future.result()
    assert_equal(target.population.replay_buffer.serialize(), state)


@pytest.mark.parametrize("field", ["priorities", "unit_ids", "sampling_rng"])
def test_native_per_rejects_malformed_transport(per_compiled: Any, field: str) -> None:
    target, plan, state = prepared_parent(per_compiled)
    before = target.population.replay_buffer.serialize()
    if field == "priorities":
        state[field][0] = np.nan
    elif field == "unit_ids":
        state[field][0] = 0
    else:
        state[field]["state"] = {}
    with pytest.raises(ValueError):
        stage(target, plan, state)
    assert_equal(target.population.replay_buffer.serialize(), before)


@pytest.mark.parametrize("version", [4, 5])
def test_native_per_rejects_valid_historical_transport(per_compiled: Any, version: int) -> None:
    target, plan, state = prepared_parent(per_compiled)
    replay = target.population.replay_buffer
    before = replay.serialize()
    for field in (
        "unit_ids",
        "next_unit_id",
        "sampling_mode",
        "sampling_origin",
        "sampling_objective_unit",
        "sampling_weight_rule",
        "sampling_rng",
    ):
        del state[field]
    if version == 4:
        for field in (
            "action_dim",
            "legality_mode",
            "historical_archives",
            "next_action_masks",
            "legality_recorded",
            "rewards_extrinsic_present",
            "rewards_intrinsic_present",
            "rewards_shaping_present",
        ):
            del state[field]
    state["format_version"] = version
    # The generic historical route accepts this transport; native resume must not.
    replay.validate_serialized(state, expected_obs_dim=target.env.observation_dim)
    with pytest.raises(ValueError, match="current.*6|format.*6"):
        stage(target, plan, state)
    assert_equal(replay.serialize(), before)
