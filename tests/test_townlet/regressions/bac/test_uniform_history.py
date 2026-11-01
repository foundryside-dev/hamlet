"""Uniform replay keeps recorded successor legality and archives unknown history."""

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import fields, replace
from pathlib import Path

import numpy as np
import pytest
import torch

from townlet.training import historical_checkpoint as history
from townlet.training.historical_checkpoint import (
    APPROVAL_REFERENCE,
    decode_historical_envelope,
    encode_historical_envelope,
    prepare_historical_envelope,
    resolve_historical_access,
)
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.replay_contract import HistoricalLegalityUnavailable, ReplayRequest
from townlet.training.state import RewardTensor

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "bac_historical"
NATIVE_SHA256 = "44a77c9e6edf183eaa5cb5761bad4999f0947175d51e8b308b7c2d3fcaf99d6d"
MANIFEST_SHA256 = "d1582c8a3b84eff4dca06c7fdf17e12c7b1adfcbf65f8c7b1c1979f1f87bbfe1"


def _equal(actual, expected):
    assert type(actual) is type(expected)
    if isinstance(actual, torch.Tensor):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape and actual.device == expected.device
        assert torch.equal(actual.contiguous().reshape(-1).view(torch.uint8), expected.contiguous().reshape(-1).view(torch.uint8))
    elif isinstance(actual, np.ndarray):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape and actual.tobytes() == expected.tobytes()
    elif isinstance(actual, Mapping):
        assert list(actual) == list(expected)
        for key in actual:
            _equal(actual[key], expected[key])
    elif isinstance(actual, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            _equal(left, right)
    else:
        assert actual == expected


@pytest.fixture
def native_uniform():
    manifest_path, native_path = FIXTURES / "portable-manifest.json", FIXTURES / "uniform.pt"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == MANIFEST_SHA256
    manifest = json.loads(manifest_path.read_text())
    entry = next(item for item in manifest["canonical_artifacts"] if item["label"] == "uniform")
    assert entry["sha256"] == NATIVE_SHA256
    assert hashlib.sha256(native_path.read_bytes()).hexdigest() == NATIVE_SHA256
    assert native_path.stat().st_size == entry["bytes"] == 1340853
    for relative, digest in entry["config_files"].items():
        assert hashlib.sha256((FIXTURES / relative).read_bytes()).hexdigest() == digest
    payload = torch.load(native_path, map_location="cpu", weights_only=False)
    assert (payload["version"], payload["population_state"]["version"]) == (9, 6)
    replay = payload["population_state"]["replay_buffer"]
    assert (replay["format_version"], replay["replay_kind"], replay["capacity"], replay["size"]) == (4, "standard", 8, 4)
    assert replay["observations"].shape == (4, 118) and payload["action_dim"] == 15
    return payload


def _validate_old(payload):
    replay = payload["population_state"]["replay_buffer"]
    buffer = ReplayBuffer(replay["capacity"], torch.device("cpu"))
    before = copy.deepcopy(buffer.serialize())
    buffer.validate_serialized(replay, expected_obs_dim=118)
    _equal(buffer.serialize(), before)


def _request(batch_size, minimum):
    return ReplayRequest(batch_size, 1, minimum, "uniform_without_replacement", "feedforward", "transition")


def _rows():
    ids = torch.arange(6, dtype=torch.float32)
    return {
        "observations": torch.stack((ids, ids + 0.25), dim=1),
        "actions": torch.arange(6, dtype=torch.int64) % 4,
        "rewards": ids + 10,
        "rewards_extrinsic": ids + 20,
        "rewards_intrinsic": ids + 30,
        "rewards_shaping": ids + 40,
        "next_observations": torch.stack((ids + 100, ids + 100.25), dim=1),
        "dones": torch.tensor([False, False, False, False, False, True]),
        "next_action_masks": torch.tensor(
            [
                [True, False, False, False],
                [False, True, False, False],
                [False, False, True, False],
                [False, False, False, True],
                [True, False, True, False],
                [False, False, False, False],
            ]
        ),
    }


def _push_recorded(buffer, rows, selection):
    rewards = RewardTensor(
        total=rows["rewards"][selection],
        extrinsic=rows["rewards_extrinsic"][selection],
        intrinsic=rows["rewards_intrinsic"][selection],
        shaping=rows["rewards_shaping"][selection],
    )
    buffer.push_recorded(
        rows["observations"][selection],
        rows["actions"][selection],
        rewards,
        rows["next_observations"][selection],
        rows["dones"][selection],
        rows["next_action_masks"][selection],
    )


def _check_batch(buffer, rows):
    batch = buffer.sample_batch(_request(4, 4))
    ids = batch.observations[:, 0].to(torch.int64)
    assert sorted(ids.tolist()) == [2, 3, 4, 5]
    for key in (
        "observations",
        "actions",
        "rewards",
        "rewards_extrinsic",
        "rewards_intrinsic",
        "rewards_shaping",
        "next_observations",
        "dones",
        "next_action_masks",
    ):
        _equal(getattr(batch, key), rows[key][ids])
    assert batch.legality_recorded.all() and batch.loss_mask.all() and batch.lengths.tolist() == [1] * 4
    receipt = batch.sampling
    assert receipt.population_size == 4 and len(set(receipt.indices.tolist())) == 4
    np.testing.assert_array_equal(receipt.weights, np.ones(4, dtype=np.float64))
    np.testing.assert_array_equal(receipt.conditional_draw_probabilities, np.array([1 / 4, 1 / 3, 1 / 2, 1], dtype=np.float64))
    _equal(batch.observations, buffer.observations[torch.from_numpy(receipt.indices.copy())])
    assert batch.unit_ids.tolist() == receipt.indices.tolist()
    _equal(batch.weights, torch.ones(4, dtype=torch.float64))
    return batch


def test_uniform_mask_wrap_sample_restore_atomic(native_uniform):
    """An approved old import preserves history without activating unknown-mask rows."""
    old = native_uniform["population_state"]["replay_buffer"]
    buffer = ReplayBuffer(old["capacity"], torch.device("cpu"))
    _validate_old(native_uniform)
    original = copy.deepcopy(old)
    buffer.load_from_serialized(old)
    assert len(buffer) == 0, "pre-capture rows must be archived, never installed as active replay"
    assert buffer.retained_transitions == 0 and type(buffer.historical_archives) is tuple
    assert len(buffer.historical_archives) == 1 and buffer.historical_archives[0].archived_row_count == 4
    archive = buffer.historical_archives[0]
    assert isinstance(archive, history.HistoricalReplayArchive)
    assert archive.source_formats == {"scope": "standalone_replay", "replay": 4, "replay_kind": "standard"}
    _equal(archive.original_state, original)
    _equal(archive.query_rows(offset=0, limit=4)["next_observations"], original["next_observations"])
    assert archive.source_digest == history.archive_standalone_replay(old).source_digest
    _equal(old, original)
    before = copy.deepcopy(buffer.serialize())
    with pytest.raises(HistoricalLegalityUnavailable):
        buffer.load_for_mode(old, requested_mode="recorded_full_resume")
    _equal(buffer.serialize(), before)
    archived_restore = ReplayBuffer(8, torch.device("cpu"))
    archived_restore.load_from_serialized(buffer.serialize())
    archived_restore.clear()
    assert archived_restore.retained_transitions == 0 and len(archived_restore.historical_archives) == 1
    _equal(archived_restore.historical_archives[0].original_state, original)
    bad_old = copy.deepcopy(old)
    bad_old["rewards_shaping"][-1] = float("nan")
    with pytest.raises(ValueError):
        buffer.load_from_serialized(bad_old)
    _equal(buffer.serialize(), before)
    rows = _rows()
    expected = copy.deepcopy(rows)
    buffer = ReplayBuffer(4, torch.device("cpu"))
    empty = buffer.readiness(_request(1, 1))
    assert not empty.ready and empty.retained_transitions == empty.sampleable_units == 0 and empty.reason == "warmup"
    _push_recorded(buffer, rows, slice(0, 3))
    warmup = buffer.readiness(_request(2, 4))
    assert not warmup.ready and warmup.retained_transitions == warmup.sampleable_units == 3 and warmup.reason == "warmup"
    _push_recorded(buffer, rows, slice(3, 6))
    assert len(buffer) == buffer.retained_transitions == buffer.stats()["size"] == 4
    assert buffer.readiness(_request(4, 4)).ready
    unavailable = buffer.readiness(_request(5, 0))
    assert not unavailable.ready and unavailable.reason == "batch_unavailable" and unavailable.sampleable_units == 4
    for value in buffer.stats().values():
        if isinstance(value, (int, float)):
            assert math.isfinite(value)
    for tensor in rows.values():
        tensor.zero_()
    batch = _check_batch(buffer, expected)
    state = buffer.serialize()
    assert state["format_version"] == 5 and state["next_action_masks"].shape == (4, 4)
    for key in ("observations", "next_observations", "rewards", "rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
        _equal(state[key], expected[key][2:])
    _equal(state["next_action_masks"], expected["next_action_masks"][2:])
    assert state["legality_recorded"].all()
    assert buffer.stats()["memory_bytes"] == sum(
        value.numel() * value.element_size() for value in state.values() if isinstance(value, torch.Tensor)
    )
    restored = ReplayBuffer(4, torch.device("cpu"))
    restored.load_prepared(restored.prepare_serialized(state, expected_obs_dim=2))
    frozen = copy.deepcopy(restored.serialize())
    for value in state.values():
        if isinstance(value, torch.Tensor):
            value.zero_()
    _check_batch(restored, expected)
    batch.next_action_masks.zero_()
    batch.observations.zero_()
    _equal(restored.serialize(), frozen)
    _equal(buffer.serialize(), frozen)
    restored.clear()
    assert len(restored) == restored.retained_transitions == restored.stats()["size"] == restored.stats()["memory_bytes"] == 0
    assert restored.stats()["occupancy_ratio"] == 0.0
    assert restored.readiness(_request(1, 0)).reason == "batch_unavailable"
    with pytest.raises(ValueError):
        restored.sample_batch(_request(1, 0))


def test_uniform_current_bad_masks_and_deep_restore_refuse_atomically():
    buffer, rows = ReplayBuffer(4, torch.device("cpu")), _rows()
    _push_recorded(buffer, rows, slice(0, 3))
    _push_recorded(buffer, rows, slice(3, 6))
    before = copy.deepcopy(buffer.serialize())
    for defect in ("missing", "unknown", "version", "width", "empty_live", "unrecorded", "deep"):
        bad = copy.deepcopy(before)
        if defect == "missing":
            del bad["next_action_masks"]
        elif defect == "unknown":
            bad["unknown"] = True
        elif defect == "version":
            bad["format_version"] = True
        elif defect == "width":
            bad["next_action_masks"] = bad["next_action_masks"][:, :-1]
        elif defect == "empty_live":
            bad["next_action_masks"][0].zero_()
        elif defect == "unrecorded":
            bad["legality_recorded"][0] = False
        else:
            bad["rewards_shaping"][-1] = float("nan")
        with pytest.raises(ValueError):
            buffer.load_from_serialized(bad)
        _equal(buffer.serialize(), before)
    for masks in (torch.zeros((1, 4), dtype=torch.bool), torch.ones((1, 3), dtype=torch.bool)):
        bad_rows = _rows()
        bad_rows["next_action_masks"] = masks
        with pytest.raises(ValueError):
            _push_recorded(buffer, bad_rows, slice(0, 1))
        _equal(buffer.serialize(), before)


def test_uniform_unconstrained_public_push_sample_adapter():
    buffer, rows = ReplayBuffer(4, torch.device("cpu")), _rows()
    rewards = RewardTensor(total=rows["rewards"][:3], extrinsic=None, intrinsic=None, shaping=None)
    buffer.push(rows["observations"][:3], rows["actions"][:3], rewards, rows["next_observations"][:3], rows["dones"][:3])
    sampled = buffer.sample(3)
    ids = sampled["observations"][:, 0].to(torch.int64)
    assert sorted(ids.tolist()) == [0, 1, 2] and sampled["mask"].all()
    _equal(sampled["rewards"], rows["rewards"][ids])
    declared = copy.deepcopy(rows)
    declared["next_action_masks"] = torch.ones((6, 4), dtype=torch.bool)
    qualified = ReplayBuffer(4, torch.device("cpu"))
    _push_recorded(qualified, declared, slice(0, 3))
    assert qualified.sample_batch(_request(3, 0)).next_action_masks.all()
    optional = ReplayBuffer(4, torch.device("cpu"))
    optional.push_recorded(
        rows["observations"][:3],
        rows["actions"][:3],
        rewards,
        rows["next_observations"][:3],
        rows["dones"][:3],
        rows["next_action_masks"][:3],
    )
    sample = optional.sample_batch(_request(3, 0))
    assert sample.rewards_extrinsic is sample.rewards_intrinsic is sample.rewards_shaping is None
    restored = ReplayBuffer(4, torch.device("cpu"))
    restored.load_from_serialized(optional.serialize())
    sample = restored.sample_batch(_request(3, 0))
    assert sample.rewards_extrinsic is sample.rewards_intrinsic is sample.rewards_shaping is None


def test_uniform_history_approved_archive_codec_export(native_uniform, tmp_path):
    original = copy.deepcopy(native_uniform)
    envelope = prepare_historical_envelope(native_uniform, requested_mode="auto", validate_legacy=_validate_old)
    policy, archive = envelope.policy, envelope.archives[0]
    assert policy.effective_mode == "archived_history_fresh_episode" and policy.approval_reference == APPROVAL_REFERENCE
    assert policy.archived_row_count == archive.archived_row_count == 4 and policy.active_retained_transitions == 0
    assert policy.restored_clocks == {"episode": 2, "completed_live_agent_steps": 4, "total_steps": 4, "training_step_counter": 3}
    expected_learned = copy.deepcopy(original)
    old = expected_learned["population_state"].pop("replay_buffer")
    _equal(envelope.available_learned_state, expected_learned)
    _equal(archive.original_state, old)
    standalone = history.archive_standalone_replay(old)
    installed = ReplayBuffer(8, torch.device("cpu"))
    installed.install_historical_archive(archive)
    installed.install_historical_archive(archive)
    assert len(installed.historical_archives) == 1
    installed.install_historical_archive(standalone)
    assert len(installed.historical_archives) == 2 and standalone.source_digest != archive.source_digest
    saved = copy.deepcopy(installed.serialize())
    corrupt = copy.deepcopy(archive)
    object.__setattr__(corrupt, "source_digest", "state-sha256:v1:" + "0" * 64)
    with pytest.raises(ValueError):
        installed.install_historical_archive(corrupt)
    _equal(installed.serialize(), saved)
    malformed = copy.deepcopy(archive)
    bad_rows = malformed.original_state
    bad_rows["next_observations"] = bad_rows["next_observations"][:, :-1]
    object.__setattr__(malformed, "original_state", bad_rows)
    with pytest.raises(ValueError):
        installed.install_historical_archive(malformed)
    _equal(installed.serialize(), saved)
    malformed = copy.deepcopy(archive)
    object.__setattr__(malformed, "source_formats", {"scope": "standalone_replay", "replay": 4, "replay_kind": "standard", "demo": 9})
    with pytest.raises(ValueError):
        installed.install_historical_archive(malformed)
    _equal(installed.serialize(), saved)
    installed.load_from_serialized(saved)
    installed.clear()
    assert installed.retained_transitions == 0 and len(installed.historical_archives) == 2
    for imported in installed.historical_archives:
        _equal(imported.original_state, old)
    fresh = ReplayBuffer(8, torch.device("cpu"))
    readiness = fresh.readiness(_request(1, 1))
    assert not readiness.ready and readiness.retained_transitions == readiness.sampleable_units == 0
    with pytest.raises(ValueError):
        fresh.sample_batch(_request(1, 0))
    fresh.clear()
    assert fresh.stats()["size"] == fresh.stats()["memory_bytes"] == 0
    _equal(archive.original_state, old)
    assert archive.source_digest.startswith("state-sha256:v1:")
    query = archive.query_rows(offset=0, limit=4)
    for key in ("observations", "actions", "rewards", "next_observations", "dones"):
        _equal(query[key], old[key])
    for key in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
        _equal(query[key], old[key])
        assert query[f"{key}_present"].all()
    query["observations"].fill_(777)
    archive.original_state["rewards"].fill_(888)
    _equal(archive.original_state, old)
    assert archive.query_rows(offset=4, limit=1)["rewards"].numel() == 0
    codec = encode_historical_envelope(envelope)
    assert "archives" in codec and "historical_archives" not in codec
    restored = decode_historical_envelope(codec)
    _equal(restored.archives[0].original_state, old)
    _equal(restored.available_learned_state, expected_learned)
    codec["archives"][0]["original_state"]["observations"].zero_()
    _equal(restored.archives[0].original_state, old)
    current = copy.deepcopy(expected_learned)
    current["version"], current["population_state"]["version"] = 10, 7
    captured, qualified = _rows(), ReplayBuffer(8, torch.device("cpu"))
    for key in ("observations", "next_observations"):
        captured[key] = torch.nn.functional.pad(captured[key], (0, 116))
    captured["next_action_masks"] = torch.nn.functional.pad(captured["next_action_masks"], (0, 11))
    _push_recorded(qualified, captured, slice(0, 4))
    current["population_state"]["replay_buffer"] = qualified.serialize()
    current["historical_archives"] = encode_historical_envelope(envelope)["archives"]
    current["historical_archives"].append({field.name: getattr(standalone, field.name) for field in fields(standalone)})
    native_policy = resolve_historical_access(current, requested_mode="recorded_full_resume")
    assert native_policy.archived_row_count == 8 and native_policy.active_retained_transitions == 4
    embedded = prepare_historical_envelope(current, requested_mode="recorded_full_resume", validate_legacy=_validate_old)
    _equal(embedded.archives[0].original_state, old)
    decoded = decode_historical_envelope(encode_historical_envelope(embedded))
    assert decoded.archives[1].source_formats == standalone.source_formats
    _equal(decoded.archives[1].original_state, old)
    receipt = archive.export(tmp_path / "uniform-history.pt")
    assert receipt.row_count == 4 and receipt.source_digest == archive.source_digest
    assert receipt.output_digest == "artifact-sha256:" + hashlib.sha256(receipt.destination.read_bytes()).hexdigest()
    _equal(torch.load(receipt.destination, map_location="cpu", weights_only=False), old)
    with pytest.raises(FileExistsError):
        archive.export(receipt.destination)
    with pytest.raises(HistoricalLegalityUnavailable):
        prepare_historical_envelope(native_uniform, requested_mode="recorded_full_resume", validate_legacy=_validate_old)
    _equal(native_uniform, original)
    assert hashlib.sha256((FIXTURES / "uniform.pt").read_bytes()).hexdigest() == NATIVE_SHA256


def test_uniform_malformed_old_components_and_native_domains_refuse(native_uniform):
    payload = copy.deepcopy(native_uniform)
    replay = payload["population_state"]["replay_buffer"]
    for key in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
        replay[key] = None
    with pytest.raises(ValueError):
        prepare_historical_envelope(payload, requested_mode="auto", validate_legacy=_validate_old)
    payload = copy.deepcopy(native_uniform)
    payload["population_state"]["version"] = 7
    with pytest.raises(ValueError):
        resolve_historical_access(payload, requested_mode="auto")
    replay = copy.deepcopy(native_uniform["population_state"]["replay_buffer"])
    replay["format_version"] = 999
    with pytest.raises(ValueError):
        history.archive_standalone_replay(replay)


def test_uniform_mixed_component_presence_survives_overwrite_restore_and_aliasing():
    buffer, rows = ReplayBuffer(4, torch.device("cpu")), _rows()
    _push_recorded(buffer, rows, slice(0, 3))
    rewards = RewardTensor(total=rows["rewards"][3:], extrinsic=None, intrinsic=rows["rewards_intrinsic"][3:], shaping=None)
    buffer.push_recorded(
        rows["observations"][3:],
        rows["actions"][3:],
        rewards,
        rows["next_observations"][3:],
        rows["dones"][3:],
        rows["next_action_masks"][3:],
    )
    rows["rewards_intrinsic"].fill_(777)
    snapshot = copy.deepcopy(buffer.serialize())
    restored = ReplayBuffer(4, torch.device("cpu"))
    restored.load_from_serialized(snapshot)
    for candidate in (buffer, restored):
        batch = candidate.sample_batch(_request(4, 0))
        ids = batch.observations[:, 0]
        present = ids == 2
        _equal(batch.rewards_extrinsic_present, present)
        _equal(batch.rewards_shaping_present, present)
        assert batch.rewards_intrinsic_present.all()
        _equal(batch.rewards, ids + 10)
        _equal(batch.rewards_intrinsic, ids + 30)
        _equal(batch.rewards_extrinsic, torch.where(present, ids + 20, torch.zeros_like(ids)))
        _equal(batch.rewards_shaping, torch.where(present, ids + 40, torch.zeros_like(ids)))
        with pytest.raises(ValueError):
            replace(batch, rewards_extrinsic_present=torch.ones(4, dtype=torch.float32))
        batch.rewards_extrinsic_present.zero_()
        batch.rewards_extrinsic.fill_(555)
        _equal(candidate.serialize(), snapshot)


def _native_current(native_uniform, case):
    source = prepare_historical_envelope(native_uniform, requested_mode="auto", validate_legacy=_validate_old)
    payload = source.available_learned_state
    payload["version"], payload["population_state"]["version"] = 10, 7
    buffer = ReplayBuffer(8, torch.device("cpu"))
    if case == "archived":
        buffer.load_from_serialized(native_uniform["population_state"]["replay_buffer"])
    elif case != "fresh":
        rows = _rows()
        for key in ("observations", "next_observations"):
            rows[key] = torch.nn.functional.pad(rows[key], (0, 116))
        rows["next_action_masks"] = torch.nn.functional.pad(rows["next_action_masks"], (0, 11))
        _push_recorded(buffer, rows, slice(0, 1))
        if case == "cleared":
            buffer.clear()
    payload["population_state"]["replay_buffer"] = buffer.serialize()
    payload["historical_archives"] = [
        {field.name: getattr(archive, field.name) for field in fields(archive)} for archive in buffer.historical_archives
    ]
    return payload


@pytest.mark.parametrize("operation", ("resolve", "prepare"))
@pytest.mark.parametrize("requested_mode", ("recorded_full_resume", "inference"))
@pytest.mark.parametrize("case", ("fresh", "cleared", "archived", "captured"))
def test_uniform_native_current_modes_accept_consistent_rows(native_uniform, case, requested_mode, operation):
    payload = _native_current(native_uniform, case)
    before = copy.deepcopy(payload)
    if operation == "resolve":
        policy = resolve_historical_access(payload, requested_mode=requested_mode)
    else:
        prepared = prepare_historical_envelope(payload, requested_mode=requested_mode, validate_legacy=_validate_old)
        policy = prepared.policy
        if case == "archived":
            assert len(prepared.archives) == 1
            _equal(prepared.archives[0].original_state, native_uniform["population_state"]["replay_buffer"])
    assert policy.effective_mode == requested_mode
    assert policy.active_retained_transitions == int(case == "captured")
    assert policy.archived_row_count == 4 * int(case == "archived")
    if case == "archived":
        assert policy.approval_reference == APPROVAL_REFERENCE
    _equal(payload, before)


@pytest.mark.parametrize("operation", ("resolve", "prepare"))
@pytest.mark.parametrize("requested_mode", ("recorded_full_resume", "inference"))
@pytest.mark.parametrize(
    "defect",
    (
        "zero_count_real_rows",
        "positive_count_mismatch",
        "positive_count_null",
        "unknown_version",
        "unrecorded",
        "missing_masks",
        "empty_observation",
        "empty_position",
        "empty_unknown_key",
        "empty_profile",
    ),
)
def test_uniform_native_current_modes_refuse_inconsistent_rows(native_uniform, defect, requested_mode, operation):
    payload = _native_current(native_uniform, "captured")
    replay = payload["population_state"]["replay_buffer"]
    observations = replay["observations"].clone()
    if defect.startswith("empty_") or defect == "positive_count_null":
        payload = _native_current(native_uniform, "fresh")
        replay = payload["population_state"]["replay_buffer"]
    if defect == "zero_count_real_rows":
        replay["size"] = replay["position"] = 0
    elif defect == "positive_count_mismatch":
        replay["size"] = replay["position"] = 2
    elif defect == "positive_count_null":
        replay["size"] = replay["position"] = 1
    elif defect == "unknown_version":
        replay["format_version"] = 999
    elif defect == "unrecorded":
        replay["legality_recorded"][0] = False
    elif defect == "missing_masks":
        replay["next_action_masks"] = None
    elif defect == "empty_observation":
        replay["observations"] = observations
    elif defect == "empty_position":
        replay["position"] = 1
    elif defect == "empty_unknown_key":
        replay["unknown"] = True
    else:
        replay["legality_mode"], replay["action_dim"] = "recorded", 15
    before = copy.deepcopy(payload)
    with pytest.raises(ValueError):
        if operation == "resolve":
            resolve_historical_access(payload, requested_mode=requested_mode)
        else:
            prepare_historical_envelope(payload, requested_mode=requested_mode, validate_legacy=_validate_old)
    _equal(payload, before)


def test_uniform_sample_insufficient_size_keeps_original_diagnostic():
    buffer, rows = ReplayBuffer(4, torch.device("cpu")), _rows()
    _push_recorded(buffer, rows, slice(0, 3))
    with pytest.raises(ValueError, match=r"Buffer size.*<.*batch_size"):
        buffer.sample(4)
