"""Native replay data is owned transport, never caller-created install authority."""

from __future__ import annotations

import copy

import pytest
import torch

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import compiled as compiled
from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import make_parent
from townlet.training import replay_contract
from townlet.training.replay_buffer import ReplayBuffer


def test_native_data_cannot_be_constructed_or_fabricated_for_install() -> None:
    replay = ReplayBuffer(capacity=8, device=torch.device("cpu"))
    before = replay.serialize()
    data_type = replay_contract.StagedReplayData
    with pytest.raises(TypeError):
        data_type()
    fabricated = object.__new__(data_type)
    with pytest.raises((ValueError, TypeError)):
        replay.install_native_restore(fabricated, parent_plan=object(), attempt=object(), restored=object(), lineage=None)
    assert replay.serialize() == before
    assert replay.retained_transitions == 0


def test_native_stage_refuses_unissued_parent_before_mutating_receiver() -> None:
    replay = ReplayBuffer(capacity=8, device=torch.device("cpu"))
    state = replay.serialize()
    before = copy.deepcopy(state)
    with pytest.raises(ValueError):
        replay.stage_native_restore(state, expected_obs_dim=3, parent_plan=object(), lineage=None)
    assert replay.serialize() == before
    assert state == before
    assert replay.retained_transitions == 0


def test_native_install_refuses_unissued_data_without_consuming_ordinary_restore() -> None:
    replay = ReplayBuffer(capacity=8, device=torch.device("cpu"))
    state = replay.serialize()
    ordinary = replay.prepare_serialized(state, expected_obs_dim=3, lineage=None)
    with pytest.raises(ValueError):
        replay.install_native_restore(ordinary, parent_plan=object(), attempt=object(), restored=object(), lineage=None)
    # Refusal must not reinterpret an ordinary capability as native data or
    # mutate the receiver. A new ordinary preparation remains lawful.
    current = replay.prepare_serialized(state, expected_obs_dim=3, lineage=None)
    replay.load_prepared(current, lineage=None)
    assert replay.retained_transitions == 0
    assert replay.serialize() == state


def test_native_stage_owns_data_without_publishing_or_ordinary_token(compiled) -> None:
    source, target = make_parent(compiled), make_parent(compiled)
    saved = source.population.get_checkpoint_state()
    target.bind()
    pop = target.population
    replay = pop.replay_buffer
    participant = replay.rng_participant
    before = replay.serialize()
    plan = pop.prepare_native_checkpoint_data(saved, mode="initial")
    transport = pop.native_replay_restore_state(plan=plan)
    data = replay.stage_native_restore(
        transport,
        expected_obs_dim=compiled.get_level(compiled.metadata.primary_level).token_spec.total_dims,
        parent_plan=plan,
        lineage=None,
    )
    assert isinstance(data, replay_contract.StagedReplayData)
    assert not isinstance(data, replay_contract.PreparedReplay)
    with pytest.raises(TypeError):
        copy.copy(data)
    assert replay is pop.replay_buffer and replay.rng_participant is participant
    assert replay.serialize() == before
    with pytest.raises(ValueError):
        replay.load_prepared(data, lineage=None)
    assert replay.serialize() == before


def test_native_stage_refuses_malformed_transport_before_live_mutation(compiled) -> None:
    source, target = make_parent(compiled), make_parent(compiled)
    saved = source.population.get_checkpoint_state()
    target.bind()
    pop = target.population
    replay = pop.replay_buffer
    before = replay.serialize()
    plan = pop.prepare_native_checkpoint_data(saved, mode="initial")
    transport = pop.native_replay_restore_state(plan=plan)
    transport["size"] = -1
    with pytest.raises(ValueError):
        replay.stage_native_restore(
            transport,
            expected_obs_dim=compiled.get_level(compiled.metadata.primary_level).token_spec.total_dims,
            parent_plan=plan,
            lineage=None,
        )
    assert replay.serialize() == before


@pytest.fixture
def native_data(compiled):
    source, target = make_parent(compiled), make_parent(compiled)
    target.bind()
    pop = target.population
    plan = pop.prepare_native_checkpoint_data(source.population.get_checkpoint_state(), mode="initial")
    data = pop.replay_buffer.stage_native_restore(
        pop.native_replay_restore_state(plan=plan),
        expected_obs_dim=compiled.get_level(compiled.metadata.primary_level).token_spec.total_dims,
        parent_plan=plan,
        lineage=None,
    )
    return target, plan, data


def test_native_data_requires_real_finalizer_even_with_genuine_parent(native_data) -> None:
    target, plan, data = native_data
    replay = target.population.replay_buffer
    before = replay.serialize()
    with pytest.raises(ValueError):
        replay.install_native_restore(data, parent_plan=plan, attempt=object(), restored=object(), lineage=None)
    assert replay.serialize() == before


def test_native_data_refuses_another_receiving_owner(native_data) -> None:
    _, plan, data = native_data
    foreign = ReplayBuffer(capacity=8, device=torch.device("cpu"))
    with pytest.raises(ValueError, match="foreign"):
        foreign.install_native_restore(data, parent_plan=plan, attempt=object(), restored=object(), lineage=None)
    assert foreign.retained_transitions == 0


def test_native_data_refuses_changed_receiver_revision(native_data) -> None:
    target, plan, data = native_data
    replay = target.population.replay_buffer
    ordinary = replay.prepare_serialized(replay.serialize(), expected_obs_dim=None, lineage=None)
    replay.load_prepared(ordinary, lineage=None)
    with pytest.raises(ValueError, match="changed"):
        replay.install_native_restore(data, parent_plan=plan, attempt=object(), restored=object(), lineage=None)
    assert replay.retained_transitions == 0


def test_native_data_refuses_another_thread_before_domain_work(native_data) -> None:
    from concurrent.futures import ThreadPoolExecutor

    target, plan, data = native_data
    replay = target.population.replay_buffer
    with ThreadPoolExecutor(max_workers=1) as pool:
        attempted = pool.submit(replay.install_native_restore, data, parent_plan=plan, attempt=object(), restored=object(), lineage=None)
        with pytest.raises(ValueError, match="thread"):
            attempted.result()
    assert replay.retained_transitions == 0
