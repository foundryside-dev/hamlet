"""T14 HC classification and raw POP6 checkpoint transport with explicit replay attachment.

The real recurrent constructor remains non-PER. Synthetic captured episodes are
transport data, and greedy use is not a native inference-mode loader or T15 proof.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest
import torch

from townlet.config.bac_options import ReplayOptions
from townlet.curriculum.static import StaticCurriculum
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.historical_checkpoint import (
    APPROVAL_REFERENCE,
    HistoricalAccessPolicy,
    decode_historical_envelope,
    encode_historical_envelope,
    prepare_historical_envelope,
    resolve_historical_access,
)
from townlet.training.replay_contract import HistoricalLegalityUnavailable, ReplayRequest
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer

_DATA = Path(__file__).resolve().parents[2] / "fixtures" / "bac_sequence_current6"
_OPTIONS = {
    "sampling_mode": "successive_without_replacement",
    "uniform_sequence_adapter": "legacy_episode_length_with_replacement",
    "sequence_mode": "adaptive_prefix",
    "retention_mode": "transition_tail",
    "sequence_objective": "anchor_transition",
    "priority_reduction": "mean_abs",
}
_BASE_KEYS = {
    "replay_kind",
    "format_version",
    "capacity",
    "num_transitions",
    "episodes",
    "action_dim",
    "legality_mode",
    "replay_options",
    "next_episode_id",
    "next_transition_id",
    "historical_archives",
}


def _exact(actual, expected) -> None:
    """Compare owned checkpoint trees, including type/order and tensor value bits."""
    assert type(actual) is type(expected)
    if isinstance(expected, torch.Tensor):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape and actual.device == expected.device
        assert torch.equal(
            actual.detach().cpu().contiguous().reshape(-1).view(torch.uint8),
            expected.detach().cpu().contiguous().reshape(-1).view(torch.uint8),
        )
    elif isinstance(expected, np.ndarray):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape
        assert actual.tobytes() == expected.tobytes()
    elif isinstance(expected, Mapping):
        assert list(actual) == list(expected)
        for key in expected:
            _exact(actual[key], expected[key])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            _exact(left, right)
    else:
        assert actual == expected


def _captured6(with_archive: bool) -> dict:
    name, digest = (
        ("sequence6-captured-with-sequence5-archive.pt", "0a40c2dbba0d64f804f91f1a5600994385777a660d4a40c851e7aa3111fa239b")
        if with_archive
        else ("sequence6-captured.pt", "02e19371fc3131db51a9569fc6d5175de5a11416e2d6cea075d441ebd8bc8434")
    )
    path = _DATA / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    state = torch.load(path, map_location="cpu", weights_only=False)
    assert set(state) == _BASE_KEYS and state["format_version"] == 6
    assert state["num_transitions"] == 3 and state["capacity"] == 3 and state["action_dim"] == 12
    assert [episode["transition_ids"].tolist() for episode in state["episodes"]] == [[3], [4, 5]]
    assert [episode["dones"].tolist() for episode in state["episodes"]] == [[False], [False, True]]
    _exact(state["replay_options"], _OPTIONS)
    assert sum(archive["archived_row_count"] for archive in state["historical_archives"]) == (34 if with_archive else 0)
    return state


def _buffer(route: str, *, device, action_dim: int, tick: int):
    if route == "unconfigured":
        return SequentialReplayBuffer(capacity=3, device=device)
    options = ReplayOptions.model_validate(_OPTIONS)
    if route == "uniform":
        return SequentialReplayBuffer.for_replay(3, device, options=options, action_dim=action_dim, legality_mode="captured")
    assert route == "prioritized"
    return SequentialReplayBuffer.for_prioritized_replay(
        3,
        device,
        options=options,
        action_dim=action_dim,
        legality_mode="captured",
        alpha=0.6,
        beta=0.4,
        beta_annealing=True,
        beta_vector_tick_horizon=100,
        current_vector_tick=tick,
        rng=np.random.Generator(np.random.PCG64(9182)),
        origin="T14-explicit-transport-fixture",
    )


def _transport_rows(obs_dim: int, marker: int) -> dict:
    observations = torch.arange(3 * obs_dim, dtype=torch.float32).reshape(3, obs_dim) / 100 + marker
    return {
        "observations": observations,
        "actions": torch.tensor([0, 1, 0], dtype=torch.int64),
        "rewards": torch.tensor([1.0, 3.0, 7.0]) + marker,
        "next_observations": observations + 0.5,
        "dones": torch.tensor([False, False, True]),
        "rewards_extrinsic": torch.tensor([1.0, 2.0, 3.0]),
        "rewards_intrinsic": None,
        "rewards_shaping": torch.tensor([0.25, 0.5, 0.75]),
    }


def _legacy_rows(obs_dim: int, marker: int) -> dict:
    # The existing legacy ABI represents absent components by omitted entries.
    return {key: value for key, value in _transport_rows(obs_dim, marker).items() if value is not None}


def _native_captured6(*, device, obs_dim: int, action_dim: int, with_archive: bool) -> dict:
    """Produce genuine6 at native geometry; optional3-row history is newly authored transport."""
    replay = _buffer("uniform", device=device, action_dim=action_dim, tick=0)
    if with_archive:
        legacy = SequentialReplayBuffer(capacity=3, device=device)
        legacy.store_episode(_legacy_rows(obs_dim, 329))
        historical = legacy.serialize()
        assert historical["format_version"] == 5 and historical["num_transitions"] == 3
        replay.load_from_serialized(historical)
        assert replay.retained_transitions == 0
    first = _transport_rows(obs_dim, 17)
    first["dones"].zero_()  # Externally ended transport fragment, no invented terminal.
    second = {key: value[:2].clone() if value is not None else None for key, value in _transport_rows(obs_dim, 53).items()}
    second["dones"] = torch.tensor([False, True])
    second["rewards_extrinsic"], second["rewards_shaping"] = None, None
    second["rewards_intrinsic"] = torch.tensor([0.5, 1.5])
    for rows in (first, second):
        masks = torch.zeros((len(rows["dones"]), action_dim), dtype=torch.bool)
        masks[~rows["dones"], 1] = True
        replay.store_captured_episode(rows, next_action_masks=masks, legality_recorded=torch.ones_like(rows["dones"]))
    state = replay.serialize()
    assert state["format_version"] == 6 and state["num_transitions"] == 3 and state["action_dim"] == action_dim
    assert [episode["transition_ids"].tolist() for episode in state["episodes"]] == [[2], [3, 4]]
    assert all(episode["observations"].shape[1] == obs_dim for episode in state["episodes"])
    assert sum(record["archived_row_count"] for record in state["historical_archives"]) == (3 if with_archive else 0)
    return state


def _request() -> ReplayRequest:
    return ReplayRequest(
        batch_size=3,
        sequence_length=3,
        min_transitions=1,
        sampling_mode="successive_without_replacement",
        sequence_mode="adaptive_prefix",
        sequence_objective="anchor_transition",
    )


def _populate_prioritized(buffer, *, obs_dim: int, action_dim: int, marker: int, tick: int) -> None:
    masks = torch.zeros((3, action_dim), dtype=torch.bool)
    masks[0, 1], masks[1, 0] = True, True
    buffer.store_captured_episode(
        _transport_rows(obs_dim, marker), next_action_masks=masks, legality_recorded=torch.ones(3, dtype=torch.bool)
    )
    batch = buffer.sample_batch(_request())
    errors = torch.arange(1, 10, dtype=torch.float64).reshape(3, 3)
    buffer.update_priorities(batch.unit_ids, errors, loss_mask=batch.loss_mask)
    buffer.set_vector_tick(tick)


@pytest.fixture
def population_builder(env_factory, cpu_device, recurrent_brain_config):
    """Use receipt-supplied public fixtures; do not alter brain/use_per/validators."""

    def build(route: str, *, with_archive: bool, marker: int, tick: int):
        env = env_factory(num_agents=1, device_override=cpu_device)
        curriculum = StaticCurriculum(difficulty_level=0.5, reward_mode="shaped", active_meters=None, depletion_multiplier=1.0)
        curriculum.initialize_population(1)
        exploration = EpsilonGreedyExploration(epsilon=0.5, epsilon_decay=0.99, epsilon_min=0.1)
        population = VectorizedPopulation(
            env=env,
            curriculum=curriculum,
            exploration=exploration,
            agent_ids=["agent_0"],
            device=cpu_device,
            brain_config=recurrent_brain_config,
            obs_dim=env.observation_dim,
            action_dim=env.action_dim,
            train_frequency=10000,
            batch_size=2,
            sequence_length=3,
            max_grad_norm=10.0,
            tb_logger=None,
            max_episodes=1,
            max_steps_per_episode=100,
        )
        assert population.is_recurrent and population.use_per is False
        replay = _buffer(route, device=cpu_device, action_dim=env.action_dim, tick=tick)
        # Explicit public attachment is transport setup, not automatic authored recurrent-PER support.
        population.replay_buffer = replay
        if route == "uniform" or with_archive:
            assert route != "unconfigured"
            captured = _native_captured6(
                device=cpu_device, obs_dim=env.observation_dim, action_dim=env.action_dim, with_archive=with_archive
            )
            replay.load_from_serialized(captured)
        if route == "prioritized":
            _populate_prioritized(replay, obs_dim=env.observation_dim, action_dim=env.action_dim, marker=marker, tick=tick)
        elif route == "unconfigured":
            replay.store_episode(_legacy_rows(env.observation_dim, marker))
        # Distinct valid transport markers; these are not claimed optimizer/trajectory updates.
        with torch.no_grad():
            next(population.q_network.parameters()).add_(marker / 100)
            next(population.target_network.parameters()).sub_(marker / 100)
        population.total_steps, population.training_step_counter = marker, marker % 7
        population.exploration.epsilon = 0.25 if marker == 17 else 0.45
        return population

    return build


def _carrier(replay: dict, *, demo: int, population: int) -> dict:
    """HC classification carrier only; never a genuine native population checkpoint."""
    return {
        "version": demo,
        "action_dim": 12,
        "episode": 4,
        "completed_live_agent_steps": 9,
        "population_state": {"version": population, "total_steps": 17, "training_step_counter": 3, "replay_buffer": replay},
        "historical_archives": copy.deepcopy(replay.get("historical_archives", [])),
    }


def _policy(formats: dict, *, requested_mode: str) -> HistoricalAccessPolicy:
    legacy = formats["demo"] == 9
    effective = "inference" if requested_mode == "inference" else ("archived_history_fresh_episode" if legacy else "recorded_full_resume")
    return HistoricalAccessPolicy(
        source_formats=formats,
        requested_mode=requested_mode,
        effective_mode=effective,
        approval_reference=APPROVAL_REFERENCE if legacy else None,
        archived_row_count=0,
        active_retained_transitions=0,
        restored_clocks={"total_steps": 17},
        guarantees=(),
        legacy_identity_recipe="T14-policy-classification-only",
    )


@pytest.mark.parametrize(
    "demo,population,kind,replay",
    [
        (9, 6, "standard", 4),
        (9, 6, "prioritized", 4),
        (9, 6, "sequential", 5),
        (10, 7, "standard", 5),
        (10, 7, "prioritized", 5),
        (10, 7, "prioritized", 6),
        (10, 7, "sequential", 6),
        (10, 7, "sequential", 7),
    ],
)
@pytest.mark.parametrize("mode", ["auto", "inference"])
def test_hc_policy_preserves_exact_format_matrix(demo, population, kind, replay, mode):
    """Catches losing a preserved family or bypassing sequential7 at the policy gateway."""
    formats = {"demo": demo, "population": population, "replay": replay, "replay_kind": kind}
    before = copy.deepcopy(formats)
    policy = _policy(formats, requested_mode=mode)
    _exact(policy.source_formats, before)
    _exact(formats, before)
    formats["replay"] = 999
    _exact(policy.source_formats, before)


@pytest.mark.parametrize(
    "demo,population,kind,replay",
    [
        (10, 6, "sequential", 7),
        (9, 7, "sequential", 7),
        (9, 6, "sequential", 7),
        (10, 7, "sequential", 5),
        (10, 7, "sequential", 8),
        (10, 7, "unknown", 7),
        (10, 7, "standard", 7),
        (10, 7, "prioritized", 7),
        (10, 7, "sequential", True),
        (10, 7, "sequential", 7.0),
        (True, 7, "sequential", 7),
        (10, 7.0, "sequential", 7),
    ],
)
def test_hc_both_gateways_refuse_wrong_wrappers_and_versions(demo, population, kind, replay):
    """Catches relaxed exact-version types, kind mixing or rawPOP6 retag assumptions."""
    formats = {"demo": demo, "population": population, "replay": replay, "replay_kind": kind}
    carrier = _carrier(
        {"replay_kind": kind, "format_version": replay, "capacity": 3, "num_transitions": 0, "episodes": []},
        demo=demo,
        population=population,
    )
    before = copy.deepcopy(carrier)
    with pytest.raises(ValueError, match="format|version"):
        resolve_historical_access(carrier, requested_mode="auto")
    with pytest.raises(ValueError, match="format|version"):
        _policy(formats, requested_mode="auto")
    _exact(carrier, before)


@pytest.mark.parametrize("version", [6, 7])
@pytest.mark.parametrize("with_archive", [False, True])
@pytest.mark.parametrize("mode", ["auto", "recorded_full_resume", "inference"])
def test_hc_current_sequences_prepare_owned_complete_state(version, with_archive, mode):
    """Catches either HC gateway omitting new7, PER state, masks, clocks or archives."""
    replay = _captured6(with_archive)
    if version == 7:
        buffer = _buffer("prioritized", device=torch.device("cpu"), action_dim=12, tick=17)
        buffer.load_from_serialized(replay)
        _populate_prioritized(buffer, obs_dim=118, action_dim=12, marker=17, tick=17)
        replay = buffer.serialize()
        assert replay["format_version"] == 7 and set(replay) == _BASE_KEYS | {"priority_state"}
    payload = _carrier(replay, demo=10, population=7)
    before = copy.deepcopy(payload)

    def legacy_validator_must_not_run(_payload):
        raise AssertionError("HC current preparation invoked the legacy-only validator")

    policy = resolve_historical_access(payload, requested_mode=mode)
    envelope = prepare_historical_envelope(payload, requested_mode=mode, validate_legacy=legacy_validator_must_not_run)
    assert policy.effective_mode == ("inference" if mode == "inference" else "recorded_full_resume")
    assert policy.active_retained_transitions == 3 and policy.archived_row_count == (34 if with_archive else 0)
    _exact(policy.restored_clocks, {"episode": 4, "completed_live_agent_steps": 9, "total_steps": 17, "training_step_counter": 3})
    _exact(asdict(envelope.policy), asdict(policy))
    _exact(envelope.available_learned_state, before)
    encoded = encode_historical_envelope(envelope)
    decoded = decode_historical_envelope(encoded)
    _exact(encode_historical_envelope(decoded), encoded)
    # Decoder invokes the independently reachable policy gateway too.
    corrupt = copy.deepcopy(encoded)
    corrupt["policy"]["source_formats"]["replay"] = 8
    with pytest.raises(ValueError, match="format|version"):
        decode_historical_envelope(corrupt)
    with pytest.raises(ValueError, match="current|captured"):
        resolve_historical_access(payload, requested_mode="archived_history_fresh_episode")
    with pytest.raises(ValueError, match="current|captured"):
        _policy(policy.source_formats, requested_mode="archived_history_fresh_episode")
    exposed = envelope.available_learned_state
    exposed["population_state"]["replay_buffer"]["episodes"][0]["observations"].fill_(-999)
    _exact(envelope.available_learned_state, before)
    _exact(payload, before)


def _relocate(checkpoint: dict, directory: Path, label: str) -> dict:
    written, moved = directory / f"{label}-written", directory / f"{label}-relocated"
    written.mkdir()
    moved.mkdir()
    original = written / "population.pt"
    torch.save(checkpoint, original)
    destination = moved / "population.pt"
    original.rename(destination)
    assert not original.exists() and destination.is_file()
    return torch.load(destination, map_location="cpu", weights_only=False)


def _batch_tree(batch) -> dict:
    return asdict(batch)


@pytest.mark.parametrize("with_archive", [False, True])
def test_raw_population6_priority7_relocation_resave_and_bounded_greedy_use(population_builder, tmp_path, with_archive):
    """Catches missing POP opaque preparation, full priority transport or second-save custody."""
    source = population_builder("prioritized", with_archive=with_archive, marker=17, tick=17)
    before = copy.deepcopy(source.get_checkpoint_state())
    assert before["version"] == 6 and before["replay_buffer"]["format_version"] == 7
    assert set(before["replay_buffer"]) == _BASE_KEYS | {"priority_state"}
    priority = before["replay_buffer"]["priority_state"]
    assert priority["current_vector_tick"] == 17 and priority["beta"] == 0.4 + 0.6 * 0.17
    assert priority["domains"][0]["sequence_length"] == 3 and priority["domains"][0]["unit_ids"].numel() == 3
    assert priority["max_priority"] > 1.0
    assert sum(record["archived_row_count"] for record in before["replay_buffer"]["historical_archives"]) == (3 if with_archive else 0)
    incoming = _relocate(before, tmp_path, "first")
    _exact(incoming, before)
    target = population_builder("prioritized", with_archive=False, marker=73, tick=73)
    target_before = copy.deepcopy(target.get_checkpoint_state())
    target.validate_checkpoint_state(incoming)
    _exact(target.get_checkpoint_state(), target_before)
    _exact(source.get_checkpoint_state(), before)
    _exact(incoming, before)
    target.load_checkpoint_state(incoming)
    _exact(target.get_checkpoint_state(), before)
    second = _relocate(copy.deepcopy(target.get_checkpoint_state()), tmp_path, "second")
    again = population_builder("prioritized", with_archive=False, marker=91, tick=91)
    again.load_checkpoint_state(second)
    _exact(again.get_checkpoint_state(), before)
    # Two-argument storage adopts7 through the same real POP6 consumer, without retagging.
    adopting = population_builder("unconfigured", with_archive=False, marker=81, tick=81)
    adopting.load_checkpoint_state(second)
    _exact(adopting.get_checkpoint_state(), before)
    # Clone replay through public loaders to prove sampler continuation without moving source/restored states.
    left = SequentialReplayBuffer(capacity=3, device=torch.device("cpu"))
    right = SequentialReplayBuffer(capacity=3, device=torch.device("cpu"))
    left.load_from_serialized(source.replay_buffer.serialize())
    right.load_from_serialized(again.replay_buffer.serialize())
    for _ in range(3):
        _exact(_batch_tree(left.sample_batch(_request())), _batch_tree(right.sample_batch(_request())))
    _exact(left.serialize(), right.serialize())
    replay_before = copy.deepcopy(again.replay_buffer.serialize())
    again.reset()
    masks = again.env.get_action_masks().clone()
    actions = again.select_greedy_actions(again.env)
    assert actions.shape == (1,) and actions.dtype == torch.int64
    assert 0 <= actions.item() < again.action_dim and masks[0, actions.item()].item()
    assert again.last_selected_q_values.shape == (1, again.action_dim)
    assert torch.isfinite(again.last_selected_q_values).all()
    _exact(again.replay_buffer.serialize(), replay_before)
    _exact(source.get_checkpoint_state(), before)
    _exact(incoming, before)
    _exact(second, before)


def _corrupt(checkpoint: dict, defect: str) -> str:
    replay = checkpoint["replay_buffer"]
    priority = replay["priority_state"]
    domain = priority["domains"][0]
    if defect == "missing_priority_key":
        priority.pop("origin")
    elif defect == "extra_priority_key":
        priority["unknown"] = 1
    elif defect == "priority_version":
        priority["priority_state_version"] = True
    elif defect == "domain_cardinality":
        domain["priorities"] = domain["priorities"][:-1].clone()
    elif defect == "duplicate_handles":
        domain["unit_ids"][1] = domain["unit_ids"][0]
    elif defect == "wrong_context":
        domain["window_keys"][0, 2] += 99
    elif defect == "nonfinite_priority":
        domain["priorities"][0] = float("nan")
    elif defect == "epsilon_floor":
        domain["priorities"][0] = 0.0
    elif defect == "beta_tick":
        priority["beta"] = 0.99
    elif defect == "rng_codec":
        priority["rng"]["state"] = {}
    elif defect == "mask_geometry":
        replay["episodes"][0]["next_action_masks"] = replay["episodes"][0]["next_action_masks"][:, :-1].clone()
        return "mask|action|shape|geometry"
    elif defect == "row_geometry":
        replay["episodes"][0]["next_observations"] = replay["episodes"][0]["next_observations"][:, :-1].clone()
        return "observation|shape|dimension"
    elif defect == "whole_schema":
        checkpoint.pop("target_network")
        return "key|target_network"
    elif defect == "wrong_kind":
        replay["replay_kind"] = "prioritized"
        return "kind|replay|format"
    else:
        raise AssertionError(defect)
    return "priority|priorit|domain|window|unit|beta|rng|codec|origin"


@pytest.mark.parametrize(
    "defect",
    [
        "missing_priority_key",
        "extra_priority_key",
        "priority_version",
        "domain_cardinality",
        "duplicate_handles",
        "wrong_context",
        "nonfinite_priority",
        "epsilon_floor",
        "beta_tick",
        "rng_codec",
        "mask_geometry",
        "row_geometry",
        "whole_schema",
        "wrong_kind",
    ],
)
def test_raw_population_malformed_priority7_refuses_before_learned_mutation(population_builder, defect):
    """Catches new7 corruption reaching POP writes before complete replay preparation."""
    source = population_builder("prioritized", with_archive=True, marker=17, tick=17)
    source_before = copy.deepcopy(source.get_checkpoint_state())
    corrupt = copy.deepcopy(source_before)
    diagnostic = _corrupt(corrupt, defect)
    corrupt_before = copy.deepcopy(corrupt)
    target = population_builder("prioritized", with_archive=False, marker=73, tick=73)
    target_before = copy.deepcopy(target.get_checkpoint_state())
    for operation in (target.validate_checkpoint_state, target.load_checkpoint_state):
        with pytest.raises(ValueError, match=diagnostic):
            operation(corrupt)
        _exact(target.get_checkpoint_state(), target_before)
        _exact(corrupt, corrupt_before)
        _exact(source.get_checkpoint_state(), source_before)


@pytest.mark.parametrize("conflict", ["uniform", "alpha", "origin"])
def test_raw_population_configured_priority_incompatibility_is_early(population_builder, conflict):
    """Catches installer-only compatibility checks after POP has changed learned fields."""
    source = population_builder("prioritized", with_archive=True, marker=17, tick=17)
    incoming = copy.deepcopy(source.get_checkpoint_state())
    source_before = copy.deepcopy(incoming)
    target = population_builder("uniform" if conflict == "uniform" else "prioritized", with_archive=False, marker=73, tick=73)
    if conflict != "uniform":
        # This is a valid source artifact with a different immutable explicit PER configuration.
        incoming["replay_buffer"]["priority_state"][conflict] = 0.9 if conflict == "alpha" else "different-explicit-owner"
    incoming_before = copy.deepcopy(incoming)
    target_before = copy.deepcopy(target.get_checkpoint_state())
    for operation in (target.validate_checkpoint_state, target.load_checkpoint_state):
        with pytest.raises(ValueError, match="priorit|uniform|config|origin|alpha|compatib"):
            operation(incoming)
        _exact(target.get_checkpoint_state(), target_before)
        _exact(incoming, incoming_before)
        _exact(source.get_checkpoint_state(), source_before)


@pytest.mark.parametrize("with_archive", [False, True])
def test_raw_population_captured6_active_adapter_preserves_rows_and_derives_only_priority(population_builder, with_archive):
    """Catches captured6 accidentally archived/freshened, lost masks/options, or invented old PER state."""
    source = population_builder("uniform", with_archive=with_archive, marker=17, tick=17)
    before = copy.deepcopy(source.get_checkpoint_state())
    captured = copy.deepcopy(before["replay_buffer"])
    assert set(captured) == _BASE_KEYS and captured["format_version"] == 6 and captured["num_transitions"] == 3
    assert [episode["transition_ids"].tolist() for episode in captured["episodes"]] == [[2], [3, 4]]
    assert all(episode["observations"].shape[1] == source.env.observation_dim for episode in captured["episodes"])
    assert captured["episodes"][0]["rewards_intrinsic"] is None and captured["episodes"][1]["rewards_extrinsic"] is None
    assert sum(record["archived_row_count"] for record in captured["historical_archives"]) == (3 if with_archive else 0)
    # Tick17 is an explicit native-owner handoff, never inferred from replay occupancy.
    target = population_builder("prioritized", with_archive=False, marker=73, tick=17)
    target_before = copy.deepcopy(target.get_checkpoint_state())
    target.validate_checkpoint_state(before)
    _exact(target.get_checkpoint_state(), target_before)
    target.load_checkpoint_state(before)
    restored = copy.deepcopy(target.get_checkpoint_state())
    assert restored["version"] == 6 and restored["replay_buffer"]["format_version"] == 7
    replay = restored["replay_buffer"]
    assert set(replay) == _BASE_KEYS | {"priority_state"}
    for key in _BASE_KEYS - {"format_version"}:
        _exact(replay[key], captured[key])
    priority = replay["priority_state"]
    assert priority["initialization"] == {
        "kind": "captured6_active_adapter",
        "source_replay_kind": "sequential",
        "source_format_version": 6,
    }
    assert priority["domains"] == [] and priority["max_priority"] == 1.0
    assert priority["next_unit_id"] >= target_before["replay_buffer"]["priority_state"]["next_unit_id"]
    assert priority["current_vector_tick"] == 17 and priority["origin"] == "T14-explicit-transport-fixture"
    for key in before.keys() - {"replay_buffer"}:
        _exact(restored[key], before[key])
    uniform = population_builder("uniform", with_archive=False, marker=91, tick=91)
    uniform.load_checkpoint_state(before)
    _exact(uniform.get_checkpoint_state(), before)
    _exact(source.get_checkpoint_state(), before)


@pytest.mark.parametrize("new_legacy_rows", [False, True])
def test_raw_population_preserves_separate_inspection_transport_without_priority_downgrade(population_builder, tmp_path, new_legacy_rows):
    """Catches dispatching inspection as captured7 or losing its separately designated rows on resave."""
    source = population_builder("unconfigured", with_archive=False, marker=17, tick=17)
    captured = _native_captured6(device=source.device, obs_dim=source.env.observation_dim, action_dim=source.action_dim, with_archive=True)
    historical = copy.deepcopy(captured["historical_archives"][0]["original_state"])
    historical_before = copy.deepcopy(historical)
    assert historical["format_version"] == 5 and historical["num_transitions"] == 3
    replay = SequentialReplayBuffer(capacity=historical["capacity"], device=torch.device("cpu"))
    source.replay_buffer = replay
    replay.load_from_serialized(historical)
    if new_legacy_rows:
        replay.store_episode(_legacy_rows(source.env.observation_dim, 219))
    before = copy.deepcopy(source.get_checkpoint_state())
    inspection = before["replay_buffer"]
    assert set(inspection) == {"inspection_kind", "inspection_version", "legacy_transport", "historical_archives"}
    assert inspection["inspection_kind"] == "sequential_replay_inspection" and inspection["inspection_version"] == 1
    assert inspection["legacy_transport"]["format_version"] == 5
    assert inspection["legacy_transport"]["num_transitions"] == (3 if new_legacy_rows else 0)
    assert sum(record["archived_row_count"] for record in inspection["historical_archives"]) == 3
    _exact(inspection["historical_archives"], captured["historical_archives"])
    assert replay.retained_transitions == 0
    if new_legacy_rows:
        sampled = replay.sample_sequences(batch_size=1, seq_len=3)
        _exact(sampled["observations"][0], _transport_rows(source.env.observation_dim, 219)["observations"])
    for mapping in (historical, inspection):
        with pytest.raises(HistoricalLegalityUnavailable):
            replay.load_for_mode(mapping, requested_mode="recorded_full_resume")
        _exact(source.get_checkpoint_state(), before)
    for label in ("inspection-first", "inspection-second"):
        incoming = _relocate(copy.deepcopy(source.get_checkpoint_state()), tmp_path, label)
        target = population_builder("unconfigured", with_archive=False, marker=73, tick=73)
        target.replay_buffer = SequentialReplayBuffer(capacity=historical["capacity"], device=torch.device("cpu"))
        target.validate_checkpoint_state(incoming)
        target.load_checkpoint_state(incoming)
        _exact(target.get_checkpoint_state(), before)
        assert target.replay_buffer.retained_transitions == 0
        source = target
    qualified = population_builder("prioritized", with_archive=False, marker=91, tick=91)
    qualified_before = copy.deepcopy(qualified.get_checkpoint_state())
    for operation in (qualified.validate_checkpoint_state, qualified.load_checkpoint_state):
        with pytest.raises(ValueError, match="inspection|configured|downgrade|captured"):
            operation(before)
        _exact(qualified.get_checkpoint_state(), qualified_before)
    # This is a classification-only negative carrier, never a relabelled native artifact.
    with pytest.raises(ValueError, match="format|kind"):
        resolve_historical_access(_carrier(inspection, demo=10, population=7), requested_mode="auto")
    _exact(historical, historical_before)


@pytest.mark.parametrize("with_archive", [False, True])
def test_raw_population_refuses_incompatible_captured6_geometry_atomically(population_builder, with_archive):
    """The unchanged118-wide artifact is invalid for this native environment, not a valid resume fixture."""
    source = population_builder("uniform", with_archive=False, marker=17, tick=17)
    source_before = copy.deepcopy(source.get_checkpoint_state())
    target = population_builder("uniform", with_archive=False, marker=73, tick=73)
    target_before = copy.deepcopy(target.get_checkpoint_state())
    captured = _captured6(with_archive)
    captured_before = copy.deepcopy(captured)
    assert captured["episodes"][0]["observations"].shape[1] != target.env.observation_dim
    incoming = copy.deepcopy(source_before)
    incoming["replay_buffer"] = captured
    incoming_before = copy.deepcopy(incoming)
    for operation in (target.validate_checkpoint_state, target.load_checkpoint_state):
        with pytest.raises(ValueError, match="observation|obs_dim|dimension|shape|action|archive"):
            operation(incoming)
        _exact(target.get_checkpoint_state(), target_before)
        _exact(incoming, incoming_before)
        _exact(captured, captured_before)
        _exact(source.get_checkpoint_state(), source_before)
