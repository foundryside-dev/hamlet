"""Native SEQ data controls; actual C publication/next learning remain runner evidence."""

from __future__ import annotations

import copy
import random
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import equal, make_parent
from townlet.training.replay_contract import ReplayRequest, StagedReplayData
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture(params=(False, True), ids=("uniform", "prioritized"))
def recurrent_compiled(request: Any, tmp_path: Path) -> Any:
    source = Path("configs/test/bac_remediation/recurrent")
    selected = source
    if request.param:
        selected = tmp_path / "recurrent"
        shutil.copytree(source, selected)
        path = selected / "brain.yaml"
        brain = yaml.safe_load(path.read_text())
        brain["replay"].update(prioritized=True, priority_alpha=0.6, priority_beta=0.4, priority_beta_annealing=True)
        path.write_text(yaml.safe_dump(brain))
    return UniverseCompiler().compile(selected, primary_level="L0_0_minimal", use_cache=False)


def native_pair(compiled: Any, *, populated: bool = False) -> tuple[Any, Any, Any, dict[str, Any]]:
    source, target = make_parent(compiled), make_parent(compiled)
    assert isinstance(source.population.replay_buffer, SequentialReplayBuffer)
    assert isinstance(target.population.replay_buffer, SequentialReplayBuffer)
    mode = "initial"
    if populated:
        source.enter()
        for _ in range(3):
            source.population.step_population(source.env)
        source.complete()
        mode = "completed_boundary"
    saved = source.population.get_checkpoint_state()
    target.bind()
    plan = target.population.prepare_native_checkpoint_data(saved, mode=mode)
    state = target.population.native_replay_restore_state(plan=plan)
    return source, target, plan, state


def stage(target: Any, plan: Any, state: dict[str, Any]) -> StagedReplayData:
    return target.population.replay_buffer.stage_native_restore(
        state, expected_obs_dim=target.env.observation_dim, parent_plan=plan, lineage=None
    )


def request_for(replay: SequentialReplayBuffer) -> ReplayRequest:
    options = replay.replay_options
    assert options is not None
    return ReplayRequest(2, 8, 2, options.sampling_mode, options.sequence_mode, options.sequence_objective)


def ambient() -> tuple[Any, Any, torch.Tensor]:
    return random.getstate(), copy.deepcopy(np.random.get_state()), torch.get_rng_state().clone()


def assert_ambient(before: tuple[Any, Any, torch.Tensor]) -> None:
    assert random.getstate() == before[0]
    actual = np.random.get_state()
    assert actual[0] == before[1][0] and actual[2:] == before[1][2:]
    np.testing.assert_array_equal(actual[1], before[1][1])
    assert torch.equal(torch.get_rng_state(), before[2])


def test_genuine_initial_sequence_data_stages_without_publication(recurrent_compiled: Any) -> None:
    _, target, plan, state = native_pair(recurrent_compiled)
    replay = target.population.replay_buffer
    before, ready, rng = replay.serialize(), replay.readiness(request_for(replay)), ambient()
    data = stage(target, plan, state)
    assert type(data) is StagedReplayData
    assert target.population.replay_buffer is replay
    equal(replay.serialize(), before)
    assert replay.readiness(request_for(replay)) == ready
    assert_ambient(rng)
    with pytest.raises(TypeError):
        copy.copy(data)
    with pytest.raises(TypeError):
        StagedReplayData()


def test_nonempty_real_sequence_stage_preserves_source_and_receiver(recurrent_compiled: Any) -> None:
    source, target, plan, state = native_pair(recurrent_compiled, populated=True)
    source_replay, target_replay = source.population.replay_buffer, target.population.replay_buffer
    request = request_for(source_replay)
    assert source_replay.readiness(request).ready
    assert state["num_transitions"] > 0 and state["episodes"]
    for episode in state["episodes"]:
        assert not bool(episode["dones"][:-1].any())
        assert bool(episode["legality_recorded"].all())
        assert episode["next_action_masks"].shape[-1] == source.population.action_dim
        assert episode["transition_ids"].numel() == episode["actions"].numel()
    before_source, before_target = source_replay.serialize(), target_replay.serialize()
    ready, rng = target_replay.readiness(request_for(target_replay)), ambient()
    data = stage(target, plan, state)
    assert type(data) is StagedReplayData
    equal(source_replay.serialize(), before_source)
    equal(target_replay.serialize(), before_target)
    assert target_replay.readiness(request_for(target_replay)) == ready
    assert_ambient(rng)
    # Includes priority generator/domain transport when the genuine constructor selects PER.
    equal(state, before_source)
    assert state["historical_archives"] == before_source["historical_archives"]


def test_sequence_native_stage_refuses_unissued_parent(recurrent_compiled: Any) -> None:
    _, target, _, state = native_pair(recurrent_compiled)
    before, rng = target.population.replay_buffer.serialize(), ambient()
    with pytest.raises((ValueError, RuntimeError)):
        stage(target, object(), state)
    equal(target.population.replay_buffer.serialize(), before)
    assert_ambient(rng)


@pytest.mark.parametrize("kind", ("fabricated", "ordinary", "genuine"))
def test_sequence_install_requires_native_data_and_actual_finalizer(recurrent_compiled: Any, kind: str) -> None:
    _, target, plan, state = native_pair(recurrent_compiled)
    replay = target.population.replay_buffer
    if kind == "fabricated":
        data = object.__new__(StagedReplayData)
    elif kind == "ordinary":
        data = replay.prepare_serialized(state, expected_obs_dim=target.env.observation_dim, lineage=None)
    else:
        data = stage(target, plan, state)
    before, rng = replay.serialize(), ambient()
    with pytest.raises((ValueError, RuntimeError)):
        replay.install_native_restore(data, parent_plan=plan, attempt=object(), restored=object(), lineage=None)
    equal(replay.serialize(), before)
    assert_ambient(rng)


@pytest.mark.parametrize("corruption", ("mask", "boundary", "identity"))
def test_malformed_nonempty_sequence_refuses_before_staging(recurrent_compiled: Any, corruption: str) -> None:
    _, target, plan, state = native_pair(recurrent_compiled, populated=True)
    record = state["episodes"][0]
    if corruption == "mask":
        record["legality_recorded"].fill_(False)
    elif corruption == "boundary":
        record["start_offset"] = record["original_length"] + 1
    else:
        record["transition_ids"].fill_(-1)
    replay = target.population.replay_buffer
    before, rng = replay.serialize(), ambient()
    with pytest.raises((ValueError, RuntimeError)):
        stage(target, plan, state)
    equal(replay.serialize(), before)
    assert_ambient(rng)


@pytest.mark.parametrize("change", ("owner", "parent", "revision", "thread"))
def test_genuine_sequence_data_refuses_changed_custody(recurrent_compiled: Any, change: str) -> None:
    _, target, plan, state = native_pair(recurrent_compiled)
    replay = target.population.replay_buffer
    data = stage(target, plan, state)
    if change in ("owner", "parent"):
        _, other, other_plan, _ = native_pair(recurrent_compiled)
        if change == "owner":
            replay = other.population.replay_buffer
        else:
            plan = other_plan
    elif change == "revision":
        replay.clear()
    before, rng = replay.serialize(), ambient()

    def install() -> None:
        replay.install_native_restore(data, parent_plan=plan, attempt=object(), restored=object(), lineage=None)

    reason = {"owner": "foreign", "parent": "another parent", "revision": "owner changed", "thread": "another process or thread"}[change]
    with pytest.raises((ValueError, RuntimeError), match=reason):
        if change == "thread":
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(install).result()
        else:
            install()
    equal(replay.serialize(), before)
    assert_ambient(rng)
