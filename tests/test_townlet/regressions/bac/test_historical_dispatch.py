"""Approved Option A against pinned, complete native pre-capture artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import fields
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

from townlet.config.brain_config import BrainConfig, load_brain_config
from townlet.config.training_v2_config import TrainingV2Config
from townlet.curriculum.factory import build_curriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training import checkpoint_utils as checkpoint_io
from townlet.training import historical_checkpoint as hc
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.replay_contract import HistoricalLegalityUnavailable
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer
from townlet.universe.compiler import UniverseCompiler

DATA = Path(__file__).resolve().parents[2] / "fixtures" / "bac_historical"
APPROVAL = "BAC-HISTORY-A-2026-11-01"
ROW_KEYS = ("observations", "actions", "rewards", "next_observations", "dones", "rewards_extrinsic", "rewards_intrinsic", "rewards_shaping")


def assert_exact(actual, expected):
    assert type(actual) is type(expected) or isinstance(actual, Mapping) and isinstance(expected, Mapping)
    if isinstance(expected, torch.Tensor):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape
        assert torch.equal(
            actual.detach().cpu().contiguous().reshape(-1).view(torch.uint8),
            expected.detach().cpu().contiguous().reshape(-1).view(torch.uint8),
        )
    elif isinstance(expected, np.ndarray):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape and actual.tobytes() == expected.tobytes()
    elif isinstance(expected, Mapping):
        assert list(actual) == list(expected)
        for key in expected:
            assert_exact(actual[key], expected[key])
    elif isinstance(expected, (tuple, list)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            assert_exact(left, right)
    else:
        assert actual == expected


@pytest.fixture(params=("uniform", "per", "sequence-trained"))
def native(request):
    manifest = json.loads((DATA / "portable-manifest.json").read_text())
    record = next(item for item in manifest["canonical_artifacts"] if item["label"] == request.param)
    path = DATA / record["artifact"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    payload = checkpoint_io.safe_torch_load(path, map_location="cpu", allow_unsafe_pickle=True)
    population, replay = payload["population_state"], payload["population_state"]["replay_buffer"]
    assert list(payload) == record["outer_keys"] and list(population) == record["population_keys"]
    assert list(replay) == record["buffer_keys"]
    assert (payload["version"], population["version"], replay["format_version"]) == (9, 6, record["replay_version"])
    assert replay[record["count_key"]] == record["retained_transitions"]
    return payload, record, path


@lru_cache(maxsize=3)
def legacy_population(kind, level):
    label = {"standard": "uniform", "prioritized": "per", "sequential": "sequence-trained"}[kind]
    universe = UniverseCompiler().compile(DATA / f"{label}-pack", primary_level=level, use_cache=False)
    metadata = universe.get_level(level)
    t, obs_dim, device = metadata.training, metadata.token_spec.total_dims, torch.device("cpu")
    loop, intrinsic, epsilon = t.training_loop, t.intrinsic, t.exploration
    env = VectorizedHamletEnv.from_universe(universe, level_name=level, num_agents=t.population.size, device=device)
    curriculum = build_curriculum(t, max_steps_per_episode=loop.max_steps_per_episode, device=device)
    exploration = AdaptiveIntrinsicExploration(
        obs_dim=obs_dim,
        embed_dim=intrinsic.rnd.feature_dim,
        rnd_learning_rate=intrinsic.rnd.learning_rate,
        rnd_training_batch_size=t.replay_buffer.batch_size,
        initial_intrinsic_weight=intrinsic.initial_weight,
        min_intrinsic_weight=intrinsic.annealing.min_weight,
        variance_threshold=intrinsic.annealing.threshold,
        min_survival_fraction=intrinsic.min_survival_fraction,
        max_episode_length=loop.max_steps_per_episode,
        survival_window=intrinsic.survival_window,
        decay_rate=intrinsic.annealing.decay_rate,
        epsilon_start=epsilon.epsilon_start,
        epsilon_min=epsilon.epsilon_end,
        epsilon_decay=epsilon.epsilon_decay,
        device=device,
    )
    return universe, env, curriculum, exploration, obs_dim, load_brain_config(DATA / f"{label}-pack")


def legacy_validator(payload):
    """Execute existing exact old outer/runtime/replay validators, never a no-op."""
    checkpoint_io.validate_demo_checkpoint_payload(payload)
    checkpoint_io.validate_demo_checkpoint_runtime_fields(
        payload, position_dim=2, substrate_type="Grid2DSubstrate", num_agents=payload["training_config"]["population"]["size"]
    )
    replay = payload["population_state"]["replay_buffer"]
    universe, env, curriculum, exploration, obs_dim, pack_brain = legacy_population(replay["replay_kind"], payload["primary_level"])
    if replay["replay_kind"] == "prioritized":
        buffer = PrioritizedReplayBuffer(
            capacity=replay["capacity"],
            alpha=replay["alpha"],
            beta=replay["beta_initial"],
            beta_annealing=replay["beta_annealing"],
            device=torch.device("cpu"),
        )
    elif replay["replay_kind"] == "sequential":
        buffer = SequentialReplayBuffer(replay["capacity"], torch.device("cpu"))
    else:
        buffer = ReplayBuffer(replay["capacity"], torch.device("cpu"))
    buffer.validate_serialized(replay, expected_obs_dim=obs_dim)
    t = universe.get_level(payload["primary_level"]).training
    checkpoint_io.assert_checkpoint_pack_hashes(payload, universe)
    checkpoint_io.assert_checkpoint_vfs_hash(payload, universe, force_new_vfs=False)
    metadata = universe.get_level(payload["primary_level"])
    for key in (
        "drive_hash",
        "curriculum_hash",
        "bars_hash",
        "affordances_hash",
        "items_appearance_hash",
        "layout_hash",
        "token_type_schema_hash",
    ):
        if payload[key] != getattr(metadata, key):
            raise ValueError(f"legacy identity {key} mismatch")
    for key, digest in (
        ("brain_hash", hc.format9_brain_hash(universe.effective_run.effective_brain, training=None)),
        ("pack_brain_hash", hc.format9_brain_hash(pack_brain, training=None)),
        ("training_hash", hc.format9_training_hash(t)),
    ):
        if payload[key] != digest:
            raise ValueError(f"legacy identity {key} mismatch")
    population = VectorizedPopulation(
        env=env,
        curriculum=curriculum,
        exploration=exploration,
        agent_ids=list(payload["agent_ids"]),
        device=torch.device("cpu"),
        brain_config=universe.effective_run.effective_brain,
        obs_dim=obs_dim,
        train_frequency=t.training_loop.train_frequency,
        batch_size=t.replay_buffer.batch_size,
        sequence_length=t.training_loop.sequence_length,
        max_grad_norm=t.training_loop.max_grad_norm,
        action_dim=universe.get_level(payload["primary_level"]).action_metadata.total_actions,
        tb_logger=None,
        max_episodes=t.training_loop.max_episodes,
        max_steps_per_episode=t.training_loop.max_steps_per_episode,
    )
    population.validate_checkpoint_state(payload["population_state"])


def prepared(payload, *, requested_mode="auto"):
    calls = []

    def validate(candidate):
        calls.append(candidate)
        legacy_validator(candidate)

    envelope = hc.prepare_historical_envelope(payload, requested_mode=requested_mode, validate_legacy=validate)
    assert len(calls) == 1
    return envelope


def expected_rows(replay):
    if replay["replay_kind"] != "sequential":
        result = {key: replay[key] for key in ROW_KEYS}
        if "priorities" in replay:
            result["priorities"] = torch.from_numpy(replay["priorities"][: replay["size_current"]].copy())
        return result
    result = {key: torch.cat([episode[key] for episode in replay["episodes"]]) for key in ROW_KEYS}
    result["episode_ids"] = torch.cat(
        [torch.full((len(episode["actions"]),), i, dtype=torch.int64) for i, episode in enumerate(replay["episodes"])]
    )
    return result


def test_approved_import_preserves_archive_and_seeds_empty_replay(native, tmp_path):
    payload, record, path = native
    before = copy.deepcopy(payload)
    envelope = prepared(payload)
    policy = envelope.policy
    assert isinstance(envelope, hc.HistoricalPreparedEnvelope) and isinstance(policy, hc.HistoricalAccessPolicy)
    assert policy.requested_mode == "auto" and policy.effective_mode == "archived_history_fresh_episode"
    assert policy.approval_reference == APPROVAL and policy.archived_row_count == record["retained_transitions"]
    assert policy.active_retained_transitions == 0 and policy.legacy_identity_recipe
    for key in ("episode", "completed_live_agent_steps"):
        assert policy.restored_clocks[key] == payload[key]
    for key in ("total_steps", "training_step_counter"):
        assert policy.restored_clocks[key] == payload["population_state"][key]
    (archive,) = envelope.archives
    assert policy.source_formats == archive.source_formats
    assert [field.name for field in fields(archive)] == [
        "source_formats",
        "original_state",
        "source_digest",
        "archived_row_count",
        "reward_semantics",
        "approval_reference",
    ]
    replay = before["population_state"]["replay_buffer"]
    assert_exact(archive.original_state, replay)
    assert archive.source_digest.startswith("state-sha256:v1:") and len(archive.source_digest) == 80
    assert archive.reward_semantics == "historical_recorded_pre_fix" and archive.approval_reference == APPROVAL
    assert archive.archived_row_count == record["retained_transitions"]
    expected = expected_rows(replay)
    rows = archive.query_rows(offset=0, limit=archive.archived_row_count)
    for key, value in expected.items():
        assert_exact(rows[key], value)
        assert_exact(archive.query_rows(offset=1, limit=2)[key], value[1:3])
    assert not {"next_action_masks", "legality_recorded"} & rows.keys()
    for offset, limit in ((-1, 1), (0, -1), (True, 1)):
        with pytest.raises(ValueError, match="offset|limit|integer"):
            archive.query_rows(offset=offset, limit=limit)
    assert not any(hasattr(archive, name) for name in ("sample", "push", "add", "update_priorities"))
    learned = envelope.available_learned_state
    assert "replay_buffer" not in learned["population_state"]
    for key, value in before["population_state"].items():
        if key != "replay_buffer":
            assert_exact(learned["population_state"][key], value)
    destination = tmp_path / "additional-native-export.pt"
    receipt = archive.export(destination)
    assert receipt.destination == destination and receipt.source_digest == archive.source_digest
    assert receipt.row_count == archive.archived_row_count
    assert receipt.output_digest == "artifact-sha256:" + hashlib.sha256(destination.read_bytes()).hexdigest()
    assert_exact(checkpoint_io.safe_torch_load(destination, map_location="cpu", allow_unsafe_pickle=True), replay)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
    assert_exact(payload, before)
    rows["rewards"].zero_()
    archive.original_state["rewards"].zero_() if "rewards" in replay else archive.original_state["episodes"][0]["rewards"].zero_()
    assert_exact(archive.query_rows(offset=0, limit=archive.archived_row_count)["rewards"], expected["rewards"])
    producer_replay = payload["population_state"]["replay_buffer"]
    producer_rows = producer_replay["episodes"][0] if producer_replay["replay_kind"] == "sequential" else producer_replay
    producer_rows["rewards"].zero_()
    assert_exact(archive.query_rows(offset=0, limit=archive.archived_row_count)["rewards"], expected["rewards"])
    with pytest.raises((AttributeError, TypeError)):
        archive.archived_row_count = 0
    explicit = prepared(before, requested_mode="archived_history_fresh_episode")
    assert explicit.archives[0].source_digest == archive.source_digest
    assert hc.resolve_historical_access(before, requested_mode="inference").effective_mode == "inference"


def test_old_identity_recipe_ignores_only_new_absent_fields(native):
    payload, record, _ = native
    pack = DATA / record["config"]
    brain = load_brain_config(pack)
    training_document = yaml.safe_load((pack / "levels" / payload["primary_level"] / "training.yaml").read_text())
    training = TrainingV2Config.model_validate({**training_document["training"], "run_metadata": training_document["run_metadata"]})
    assert hc.format9_brain_hash(brain, training=None) == payload["pack_brain_hash"]
    assert hc.format9_brain_hash(brain, training=training) == payload["brain_hash"]
    assert hc.format9_training_hash(training) == payload["training_hash"]
    edited = brain.model_dump()
    edited["optimizer"]["learning_rate"] *= 2
    assert hc.format9_brain_hash(BrainConfig.model_validate(edited), training=None) != payload["pack_brain_hash"]
    changed_training = training.model_copy(update={"q_learning": training.q_learning.model_copy(update={"gamma": 0.7})})
    assert hc.format9_training_hash(changed_training) != payload["training_hash"]
    assert hc.format9_brain_hash(brain, training=changed_training) != payload["brain_hash"]
    for key, value in (("target_update_frequency", 333), ("use_double_dqn", False), ("learning_rate", 0.002)):
        override = training.model_copy(update={"q_learning": training.q_learning.model_copy(update={key: value})})
        assert hc.format9_brain_hash(brain, training=override) != payload["brain_hash"]
    override = training.model_copy(update={"replay_buffer": training.replay_buffer.model_copy(update={"capacity": 99})})
    assert hc.format9_brain_hash(brain, training=override) != payload["brain_hash"]
    with pytest.raises(ValueError, match="bac_options|option|format.?9"):
        hc.format9_training_hash({**training.model_dump(), "bac_options": {"replay_sampling": {"mode": "iid"}}})
    if brain.architecture.type == "recurrent":
        edited = brain.model_dump()
        edited["architecture"]["recurrent"]["token_encoder"] = {"type": "mlp", "hidden_dim": 8, "activation": "relu"}
        with pytest.raises(ValueError, match="token_encoder|encoder|format.?9"):
            hc.format9_brain_hash(edited, training=None)


def test_archive_failure_is_atomic(native, tmp_path, monkeypatch):
    payload, _, _ = native
    before = copy.deepcopy(payload)
    with pytest.raises(HistoricalLegalityUnavailable, match="mask|legality"):
        prepared(payload, requested_mode="recorded_full_resume")
    assert_exact(payload, before)
    malformed = copy.deepcopy(payload)
    malformed["population_state"]["replay_buffer"]["format_version"] = 999
    with pytest.raises(ValueError, match="replay|version|format"):
        prepared(malformed)
    incompatible = copy.deepcopy(payload)
    incompatible["brain_hash"] = "0" * 64
    with pytest.raises(ValueError, match="brain_hash"):
        prepared(incompatible)
    with pytest.raises(ValueError, match="key|missing|epsilon"):
        prepared({key: value for key, value in payload.items() if key != "epsilon"})
    deep = copy.deepcopy(payload)
    replay = deep["population_state"]["replay_buffer"]
    rows = replay["episodes"][0] if replay["replay_kind"] == "sequential" else replay
    rows["rewards"] = rows["rewards"][:-1]
    deep_before = copy.deepcopy(deep)
    with pytest.raises(ValueError, match="reward|rows|shape|length"):
        prepared(deep)
    assert_exact(deep, deep_before)
    archive = prepared(payload).archives[0]
    existing = tmp_path / "existing.pt"
    existing.write_bytes(b"existing artifact")
    with pytest.raises((ValueError, FileExistsError)):
        archive.export(existing)
    assert existing.read_bytes() == b"existing artifact"
    real_save = torch.save

    def corrupt_save(state, destination, *args, **kwargs):
        corrupted = copy.deepcopy(state)
        rows = corrupted["episodes"][0] if corrupted["replay_kind"] == "sequential" else corrupted
        rows["rewards"][0] += 1
        return real_save(corrupted, destination, *args, **kwargs)

    with monkeypatch.context() as serialization:
        serialization.setattr(torch, "save", corrupt_save)
        with pytest.raises(ValueError, match="digest|corrupt"):
            archive.export(tmp_path / "corrupt-export.pt")

    def fail(*args, **kwargs):
        raise OSError("injected publication failure")

    with monkeypatch.context() as publication:
        for name in ("link", "replace", "rename"):
            publication.setattr(os, name, fail)
        with pytest.raises(OSError, match="publication failure"):
            archive.export(tmp_path / "unpublished.pt")
    assert sorted(path.name for path in tmp_path.iterdir()) == ["existing.pt"]
    with monkeypatch.context() as preparation:
        preparation.setattr(hc, "HistoricalReplayArchive", fail)
        with pytest.raises(OSError, match="publication failure"):
            prepared(payload)
    assert_exact(payload, before)


def test_embedded_archive_is_standalone_and_detects_corruption(native, tmp_path, monkeypatch):
    payload, _, native_path = native
    envelope = prepared(payload)
    encoded = hc.encode_historical_envelope(envelope)
    target = tmp_path / "relocated-envelope.pt"
    torch.save(encoded, target)
    encoded = checkpoint_io.safe_torch_load(target, map_location="cpu", allow_unsafe_pickle=True)
    original_open = Path.open

    def isolated_open(path, *args, **kwargs):
        assert path != native_path, "embedded archive reopened its original source"
        return original_open(path, *args, **kwargs)

    with monkeypatch.context() as relocation:
        relocation.setattr(Path, "open", isolated_open)
        decoded = hc.decode_historical_envelope(encoded)
    assert decoded.archives[0].source_digest == envelope.archives[0].source_digest
    assert_exact(decoded.archives[0].original_state, envelope.archives[0].original_state)
    archive_state = encoded["archives"][0]
    assert not any(key in archive_state for key in ("artifact_digest", "source_path", "artifact_verified"))
    for location in ("schema", "state", "digest"):
        broken = copy.deepcopy(encoded)
        if location == "schema":
            broken["schema_version"] = 999
        elif location == "digest":
            broken["archives"][0]["source_digest"] = "state-sha256:v1:" + "0" * 64
        else:
            replay = broken["archives"][0]["original_state"]
            rows = replay["episodes"][0] if replay["replay_kind"] == "sequential" else replay
            rows["rewards"][0] += 1
        with pytest.raises(ValueError, match="schema|version|digest|corrupt"):
            hc.decode_historical_envelope(broken)


def test_state_digest_is_independent_of_native_serialization(native, tmp_path):
    payload, _, _ = native
    archive = prepared(payload).archives[0]
    first, second = tmp_path / "protocol2.pt", tmp_path / "protocol5.pt"
    torch.save(archive.original_state, first, pickle_protocol=2)
    torch.save(archive.original_state, second, pickle_protocol=5)
    assert hashlib.sha256(first.read_bytes()).digest() != hashlib.sha256(second.read_bytes()).digest()
    for path in (first, second):
        state = checkpoint_io.safe_torch_load(path, map_location="cpu", allow_unsafe_pickle=True)
        restored = hc.HistoricalReplayArchive(
            archive.source_formats, state, archive.source_digest, archive.archived_row_count, archive.reward_semantics, APPROVAL
        )
        assert restored.source_digest == archive.source_digest
        assert_exact(restored.original_state, archive.original_state)
    bad_digest = "state-sha256:v1:" + "0" * 64
    with pytest.raises(ValueError, match="digest"):
        hc.HistoricalReplayArchive(
            archive.source_formats, archive.original_state, bad_digest, archive.archived_row_count, archive.reward_semantics, APPROVAL
        )


@pytest.mark.parametrize("native", ("sequence-trained",), indirect=True)
def test_sequence_archive_queries_preserve_partial_reward_component_coverage(native, tmp_path):
    payload, _, source = native
    modified = copy.deepcopy(payload)
    replay = modified["population_state"]["replay_buffer"]
    episodes = replay["episodes"]
    assert len(episodes) >= 3 and all(len(episode["actions"]) == 2 for episode in episodes[:3])
    component = "rewards_intrinsic"
    episodes[1][component] = None
    episodes[1]["dones"][-1] = False
    before = copy.deepcopy(modified)
    archive = prepared(modified).archives[0]
    known = archive.query_rows(offset=0, limit=2)
    assert_exact(known[component], episodes[0][component])
    assert_exact(known[f"{component}_present"], torch.ones(2, dtype=torch.bool))
    crossing = archive.query_rows(offset=0, limit=6)
    presence = torch.tensor([True, True, False, False, True, True], dtype=torch.bool)
    assert_exact(crossing[f"{component}_present"], presence)
    assert_exact(crossing[component][presence], torch.cat((episodes[0][component], episodes[2][component])))
    later = archive.query_rows(offset=4, limit=2)
    assert_exact(later[component], episodes[2][component])
    assert_exact(later[f"{component}_present"], torch.ones(2, dtype=torch.bool))
    missing = archive.query_rows(offset=2, limit=2)
    assert_exact(missing[f"{component}_present"], torch.zeros(2, dtype=torch.bool))
    assert component not in missing, "an entirely unrecorded query must not present placeholder rewards as recorded values"
    for key in ("rewards", "rewards_extrinsic", "rewards_shaping"):
        assert_exact(crossing[key], torch.cat([episode[key] for episode in episodes[:3]]))
    for key in ("rewards_extrinsic", "rewards_shaping"):
        assert_exact(crossing[f"{key}_present"], torch.ones(6, dtype=torch.bool))
    assert_exact(modified, before)
    assert_exact(archive.original_state, before["population_state"]["replay_buffer"])
    export = tmp_path / "partial-component-native.pt"
    receipt = archive.export(export)
    assert receipt.source_digest == archive.source_digest
    assert_exact(checkpoint_io.safe_torch_load(export, map_location="cpu", allow_unsafe_pickle=True), replay)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == next(
        item["sha256"]
        for item in json.loads((DATA / "portable-manifest.json").read_text())["canonical_artifacts"]
        if item["label"] == "sequence-trained"
    )
