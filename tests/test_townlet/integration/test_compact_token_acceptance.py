"""Engineering acceptance for the compact token observation ABI."""

from __future__ import annotations

import copy
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, assert_never

import numpy as np
import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

from tests.test_townlet.helpers.token_widths import fixed_width_for
from townlet.agent.network_factory import NetworkFactory
from townlet.agent.token_input import TokenInputAssembler
from townlet.config.bac_options import ReplayOptions
from townlet.config.brain_config import (
    DuelingConfig,
    DuelingStreamConfig,
    FeedforwardConfig,
    LSTMConfig,
    RecurrentConfig,
    SetAggregatorConfig,
    TokenSetConfig,
    apply_training_overrides,
)
from townlet.curriculum.factory import build_curriculum
from townlet.demo.runner import DemoRunner
from townlet.environment.token_publishers import EffectSlotBatch, EffectTokenPublisher, TokenPublishContext
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.exploration.rnd import RNDExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.checkpoint_utils import CHECKPOINT_FORMAT_VERSION, persist_checkpoint_digest
from townlet.training.prioritized_replay_buffer import (
    PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION,
    PrioritizedReplayBuffer,
)
from townlet.training.replay_buffer import REPLAY_BUFFER_FORMAT_VERSION, HistoricalLegalityUnavailable, ReplayBuffer
from townlet.training.replay_contract import ReplayRequest
from townlet.training.sequential_replay_buffer import (
    SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION,
    SequentialReplayBuffer,
)
from townlet.training.state import RewardTensor
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.token_spec import (
    EFFECT_STATIC_FEATURES,
    PAYLOAD_SCHEMAS,
    TOKEN_TRANSPORT_VERSION,
    EffectDeclaration,
    SlotBinding,
    TokenContext,
    TokenSpec,
    build_token_type,
    effect_static_payload,
)

CPU = torch.device("cpu")
BATCH_SIZE = 256
SEQUENCE_LENGTH = 4
ArchitectureCase = Literal["feedforward", "dueling", "token_mean", "token_attention", "rnd"]
ReplayKind = Literal["standard", "prioritized", "sequential"]


@dataclass(frozen=True)
class _SubstrateCase:
    key: str
    config_path: Path
    level_name: str
    position_rank: int
    compact_width: int
    #: The fixed width is not pinned here: it derives from the census and the per-type payload
    #: schemas (tests/test_townlet/helpers/token_widths.py), pinned once in test_token_emission.
    deployed_affordances: int


SUBSTRATE_CASES = (
    _SubstrateCase("grid2d", Path("configs/default_curriculum"), "L1_full_observability", 2, 118, 14),
    _SubstrateCase("grid3d", Path("configs/differential/div003_cubic_partial"), "L2_partial_observability", 3, 152, 14),
    _SubstrateCase("aspatial", Path("configs/aspatial_test"), "L0", 0, 19, 1),
)


@pytest.fixture(scope="module")
def substrate_universes() -> dict[str, CompiledUniverse]:
    compiler = UniverseCompiler()
    return {case.key: compiler.compile(case.config_path, primary_level=case.level_name, use_cache=False) for case in SUBSTRATE_CASES}


def _expected_fixed_rows(spec: TokenSpec, type_name: str, dynamic_rows: torch.Tensor) -> torch.Tensor:
    """Independent compact-to-fixed parity oracle for one token type."""
    schema = spec.get_type(type_name)
    layout = spec.compact_layout().get_type(type_name)
    assert schema is not None and layout is not None
    expected = torch.zeros(
        (dynamic_rows.shape[0], schema.capacity, schema.fixed_row_width),
        dtype=dynamic_rows.dtype,
        device=dynamic_rows.device,
    )
    if schema.capacity == 0:
        return expected

    if type_name == "effect":
        contexts = torch.tensor(
            [context.fixed_payload for context in schema.effect_catalog_contexts],
            dtype=dynamic_rows.dtype,
            device=dynamic_rows.device,
        )
        selectors = dynamic_rows[:, :, layout.dynamic_features.index("context_index")].to(dtype=torch.long)
        present = dynamic_rows[:, :, 0] != 0
        safe_selectors = torch.where(present, selectors, torch.zeros_like(selectors))
        if contexts.shape[0] > 0:
            expected[:, :, 1:] = contexts.index_select(0, safe_selectors.flatten()).view(
                dynamic_rows.shape[0], schema.capacity, len(schema.payload_features)
            )
    else:
        contexts = torch.tensor(schema.slot_context_payloads, dtype=dynamic_rows.dtype, device=dynamic_rows.device)
        expected[:, :, 1:] = contexts.unsqueeze(0)

    for compact_lane, fixed_lane in enumerate(layout.fixed_scatter_indices):
        if fixed_lane is not None:
            expected[:, :, fixed_lane] = dynamic_rows[:, :, compact_lane]
    return expected * (dynamic_rows[:, :, :1] != 0).to(dtype=dynamic_rows.dtype)


def _assert_per_type_assembly_parity(spec: TokenSpec, compact: torch.Tensor) -> None:
    assembler = TokenInputAssembler(spec)
    for layout in spec.compact_layout().types:
        dynamic_rows = compact[:, layout.start : layout.end].view(compact.shape[0], layout.capacity, layout.compact_row_width)
        actual = assembler.expand_type(layout.type_name, dynamic_rows)
        expected = _expected_fixed_rows(spec, layout.type_name, dynamic_rows)
        torch.testing.assert_close(actual, expected, rtol=0.0, atol=0.0)


def _attach_checkpoint_runtime(runner: DemoRunner, *, num_agents: int) -> None:
    training = runner.training_config
    loop = training.training_loop
    env = VectorizedHamletEnv.from_universe(runner.compiled, level_name=runner.level_name, num_agents=num_agents, device=CPU)
    curriculum = build_curriculum(training, max_steps_per_episode=loop.max_steps_per_episode, device=CPU)
    curriculum.initialize_population(num_agents)
    exploration = EpsilonGreedyExploration(epsilon=0.5, epsilon_decay=0.99, epsilon_min=0.1)
    population = VectorizedPopulation(
        env=env,
        curriculum=curriculum,
        exploration=exploration,
        agent_ids=[f"agent_{index}" for index in range(num_agents)],
        device=CPU,
        obs_dim=env.observation_dim,
        brain_config=apply_training_overrides(runner.brain_config, training),
        train_frequency=loop.train_frequency,
        batch_size=training.replay_buffer.batch_size,
        sequence_length=loop.sequence_length,
        max_grad_norm=loop.max_grad_norm,
        action_dim=env.action_dim,
        max_episodes=1,
        max_steps_per_episode=loop.max_steps_per_episode,
    )
    runner.env = env
    runner.curriculum = curriculum
    runner.exploration = exploration
    runner.population = population


def _assert_outer_checkpoint_roundtrip(case: _SubstrateCase, tmp_path: Path) -> None:
    copied_pack = tmp_path / f"{case.key}-pack"
    shutil.copytree(case.config_path, copied_pack)
    checkpoint_dir = tmp_path / f"{case.key}-checkpoints"
    with DemoRunner(
        config_dir=copied_pack,
        db_path=tmp_path / f"{case.key}.db",
        checkpoint_dir=checkpoint_dir,
        max_episodes=1,
        level_name=case.level_name,
    ) as runner:
        _attach_checkpoint_runtime(runner, num_agents=2)
        runner.current_episode = 7
        runner.save_checkpoint()
        assert runner.load_checkpoint() == 7

        current_path = checkpoint_dir / "checkpoint_ep00007.pt"
        previous_payload = torch.load(current_path, map_location=CPU, weights_only=False)
        previous_payload["version"] = CHECKPOINT_FORMAT_VERSION - 1
        previous_path = checkpoint_dir / "checkpoint_ep99999.pt"
        torch.save(previous_payload, previous_path)
        persist_checkpoint_digest(previous_path)
        with pytest.raises(ValueError, match=rf"Expected version {CHECKPOINT_FORMAT_VERSION}"):
            runner.load_checkpoint()


@pytest.mark.parametrize("case", SUBSTRATE_CASES, ids=lambda case: case.key)
def test_substrate_matrix(
    case: _SubstrateCase,
    substrate_universes: dict[str, CompiledUniverse],
    tmp_path: Path,
) -> None:
    """Artifact, runtime, projection, and checkpoint contracts hold on all substrates."""
    universe = substrate_universes[case.key]
    artifact_path = tmp_path / f"{case.key}.msgpack"
    universe.save_to_cache(artifact_path)
    restored = CompiledUniverse.load_from_cache(artifact_path)
    level = restored.get_level(case.level_name)
    original_level = universe.get_level(case.level_name)
    assert level.token_spec == original_level.token_spec
    assert level.token_type_schema_hash == original_level.token_type_schema_hash
    assert level.layout_hash == original_level.layout_hash
    assert level.observation_schema_hash == original_level.observation_schema_hash

    env = VectorizedHamletEnv(universe=restored, level_name=case.level_name, num_agents=2, device=CPU)
    observations = env.reset()
    wait_actions = torch.full((2,), env.action_ids["WAIT"], dtype=torch.long)
    next_observations, rewards, dones, _ = env.step(wait_actions)
    spec = env.token_spec

    assert spec.position_rank == case.position_rank
    assert spec.total_dims == env.observation_dim == case.compact_width
    assert spec.fixed_total_dims == fixed_width_for(spec.census)
    assert observations.shape == next_observations.shape == (2, case.compact_width)
    assert observations.dtype is next_observations.dtype is torch.float32
    assert rewards.shape == dones.shape == (2,)
    assert torch.isfinite(observations).all() and torch.isfinite(next_observations).all()

    for layout in spec.compact_layout().types:
        rows = observations[:, layout.start : layout.end].view(2, layout.capacity, layout.compact_row_width)
        presence = rows[:, :, 0]
        assert torch.all((presence == 0) | (presence == 1))
        assert torch.count_nonzero(rows * (presence == 0).unsqueeze(-1)) == 0
    affordance_layout = spec.compact_layout().get_type("affordance")
    assert affordance_layout is not None
    affordance_rows = observations[:, affordance_layout.start : affordance_layout.end].view(
        2, affordance_layout.capacity, affordance_layout.compact_row_width
    )
    affordance_positions, affordance_deployed = env._affordance_layout()
    assert int(affordance_deployed.sum()) == case.deployed_affordances
    expected_presence = env.substrate.visible(
        env.positions,
        affordance_positions,
        env.vision_range if env.partial_observability else None,
    ) & affordance_deployed.unsqueeze(0)
    torch.testing.assert_close(affordance_rows[:, :, 0].to(dtype=torch.bool), expected_presence)
    _assert_per_type_assembly_parity(spec, observations)
    _assert_per_type_assembly_parity(spec, next_observations)
    _assert_outer_checkpoint_roundtrip(case, tmp_path)


def test_substrate_hash_boundary(substrate_universes: dict[str, CompiledUniverse]) -> None:
    levels = [substrate_universes[case.key].get_level(case.level_name) for case in SUBSTRATE_CASES]
    assert len({level.token_type_schema_hash for level in levels}) == 1
    assert len({level.layout_hash for level in levels}) == len(SUBSTRATE_CASES)
    assert [level.token_spec.position_rank for level in levels] == [2, 3, 0]


@pytest.fixture(scope="module")
def l1_runtime(substrate_universes: dict[str, CompiledUniverse]) -> tuple[TokenSpec, int, torch.Tensor]:
    universe = substrate_universes["grid2d"]
    env = VectorizedHamletEnv(universe=universe, level_name="L1_full_observability", num_agents=4, device=CPU)
    return env.token_spec, env.action_dim, env.reset()


def _batch_256_observations(observations: torch.Tensor) -> torch.Tensor:
    assert observations.shape[0] == 4
    return observations.repeat(BATCH_SIZE // observations.shape[0], 1)


def _changed_parameter(before: dict[str, torch.Tensor], module: nn.Module) -> bool:
    return any(not torch.equal(before[name], parameter.detach()) for name, parameter in module.named_parameters())


def _train_network_once(network: nn.Module, observations: torch.Tensor, action_dim: int) -> None:
    optimizer = torch.optim.Adam(network.parameters(), lr=1e-3)
    before = {name: parameter.detach().clone() for name, parameter in network.named_parameters()}
    q_values = network(observations)
    assert q_values.shape == (BATCH_SIZE, action_dim)
    targets = torch.linspace(-0.5, 0.5, action_dim).expand_as(q_values)
    loss = F.mse_loss(q_values, targets)
    assert loss.ndim == 0 and torch.isfinite(loss)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    assert _changed_parameter(before, network)


@pytest.mark.parametrize("architecture", ["feedforward", "dueling", "token_mean", "token_attention", "rnd"])
def test_batch_256_architecture_matrix(
    architecture: ArchitectureCase,
    l1_runtime: tuple[TokenSpec, int, torch.Tensor],
) -> None:
    spec, action_dim, observations = l1_runtime
    batch = _batch_256_observations(observations)
    if architecture == "feedforward":
        network = NetworkFactory.build_feedforward(
            FeedforwardConfig(hidden_layers=[32], activation="relu", dropout=0.0, layer_norm=False),
            obs_dim=spec.total_dims,
            action_dim=action_dim,
        )
        _train_network_once(network, batch, action_dim)
    elif architecture == "dueling":
        network = NetworkFactory.build_dueling(
            DuelingConfig(
                shared_layers=[32],
                value_stream=DuelingStreamConfig(hidden_layers=[16], activation="relu"),
                advantage_stream=DuelingStreamConfig(hidden_layers=[16], activation="relu"),
                activation="relu",
                dropout=0.0,
                layer_norm=False,
            ),
            obs_dim=spec.total_dims,
            action_dim=action_dim,
        )
        _train_network_once(network, batch, action_dim)
    elif architecture in {"token_mean", "token_attention"}:
        aggregator_type = "mean" if architecture == "token_mean" else "attention"
        network = NetworkFactory.build_token_set(
            TokenSetConfig(
                token_embed_dim=16,
                q_head_hidden_dim=16,
                aggregator=SetAggregatorConfig(
                    type=aggregator_type,
                    num_heads=None if aggregator_type == "mean" else 4,
                ),
            ),
            action_dim=action_dim,
            token_spec=spec,
        )
        _train_network_once(network, batch, action_dim)
    elif architecture == "rnd":
        rnd = RNDExploration(
            obs_dim=spec.total_dims,
            embed_dim=16,
            learning_rate=1e-3,
            training_batch_size=BATCH_SIZE,
            epsilon_start=1.0,
            epsilon_min=0.1,
            epsilon_decay=0.99,
            device=CPU,
        )
        before = {name: parameter.detach().clone() for name, parameter in rnd.predictor_network.named_parameters()}
        target = rnd.fixed_network(batch).detach()
        predicted = rnd.predictor_network(batch)
        assert target.shape == predicted.shape == (BATCH_SIZE, 16)
        loss = F.mse_loss(predicted, target)
        assert loss.ndim == 0 and torch.isfinite(loss)
        rnd.optimizer.zero_grad()
        loss.backward()
        rnd.optimizer.step()
        assert _changed_parameter(before, rnd.predictor_network)
    else:
        assert_never(architecture)


def _recurrent_config() -> RecurrentConfig:
    return RecurrentConfig(
        token_embed_dim=16,
        aggregator=SetAggregatorConfig(type="mean"),
        lstm=LSTMConfig(hidden_size=32, num_layers=1, dropout=0.0),
        q_head_hidden_dim=16,
    )


def test_batch_256_recurrent_bptt(l1_runtime: tuple[TokenSpec, int, torch.Tensor]) -> None:
    spec, action_dim, observations = l1_runtime
    batch = _batch_256_observations(observations)
    sequences = torch.stack([batch, batch * 0.99, batch * 0.98, batch * 0.97], dim=1)
    next_observations = torch.stack([batch * 0.99, batch * 0.98, batch * 0.97, batch * 0.96], dim=1)
    assert sequences.shape == next_observations.shape == (BATCH_SIZE, SEQUENCE_LENGTH, spec.total_dims)

    validity = torch.ones((BATCH_SIZE, SEQUENCE_LENGTH), dtype=torch.bool)
    validity[-32:, -1] = False
    terminals = torch.zeros_like(validity)
    terminals[:128, 1] = True
    terminals[128:160, -1] = True

    network = NetworkFactory.build_recurrent(_recurrent_config(), action_dim=action_dim, token_spec=spec)
    optimizer = torch.optim.Adam(network.parameters(), lr=1e-3)
    lstm_before = {name: parameter.detach().clone() for name, parameter in network.lstm.named_parameters()}
    hidden = network.initial_hidden(BATCH_SIZE, CPU)
    q_values, hidden = network(sequences, hidden)
    losses = [q_values[:, step, :].square().mean(dim=1)[validity[:, step]].mean() for step in range(SEQUENCE_LENGTH)]

    with torch.no_grad():
        bootstrap_q, _ = network(next_observations[:, -1:, :], hidden)
        bootstrap = bootstrap_q[:, 0, :].max(dim=1).values
        bootstrap = torch.where(terminals[:, -1], torch.zeros_like(bootstrap), bootstrap)
    boundary_mask = validity[:, -1]
    boundary_loss = F.mse_loss(q_values[boundary_mask, -1, 0], bootstrap[boundary_mask])
    loss = torch.stack(losses).mean() + boundary_loss
    assert loss.ndim == 0 and torch.isfinite(loss)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    assert _changed_parameter(lstm_before, network.lstm)
    assert torch.count_nonzero(terminals) > 0
    assert torch.count_nonzero(~validity) > 0


def _transition_batch(obs_dim: int, batch_size: int = 8) -> tuple[torch.Tensor, torch.Tensor, RewardTensor, torch.Tensor, torch.Tensor]:
    observations = torch.linspace(-1.0, 1.0, batch_size * obs_dim, dtype=torch.float32).view(batch_size, obs_dim)
    next_observations = observations.roll(1, dims=0)
    actions = torch.arange(batch_size, dtype=torch.long) % 3
    total = torch.linspace(-0.25, 0.25, batch_size, dtype=torch.float32)
    rewards = RewardTensor.from_dac(total, extrinsic=total.clone(), intrinsic=torch.zeros_like(total), shaping=torch.zeros_like(total))
    dones = torch.zeros(batch_size, dtype=torch.bool)
    dones[-1] = True
    return observations, actions, rewards, next_observations, dones


def _assert_exact_state(expected: Any, actual: Any) -> None:
    assert type(actual) is type(expected)
    if isinstance(expected, torch.Tensor):
        assert actual.shape == expected.shape
        assert actual.dtype is expected.dtype
        assert torch.equal(actual, expected)
    elif isinstance(expected, np.ndarray):
        assert actual.shape == expected.shape
        assert actual.dtype == expected.dtype
        assert np.array_equal(actual, expected)
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            _assert_exact_state(expected[key], actual[key])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for expected_item, actual_item in zip(expected, actual, strict=True):
            _assert_exact_state(expected_item, actual_item)
    else:
        assert actual == expected


def _qualified_sequence(action_dim: int) -> SequentialReplayBuffer:
    return SequentialReplayBuffer.for_replay(
        16,
        CPU,
        options=ReplayOptions(
            sampling_mode="successive_without_replacement",
            uniform_sequence_adapter="legacy_episode_length_with_replacement",
            sequence_mode="fixed_full",
            retention_mode="whole_episode",
            sequence_objective="window_mean",
            priority_reduction="max_abs",
        ),
        action_dim=action_dim,
        legality_mode="unconstrained",  # Explicit invariant for newly authored synthetic rows only.
    )


@pytest.mark.parametrize("replay_kind", ["standard", "prioritized", "sequential"])
def test_replay_matrix(replay_kind: ReplayKind, l1_runtime: tuple[TokenSpec, int, torch.Tensor]) -> None:
    spec, action_dim, _ = l1_runtime
    observations, actions, rewards, next_observations, dones = _transition_batch(spec.total_dims)
    if replay_kind == "standard":
        replay: Any = ReplayBuffer(capacity=16, device=CPU)
        replay.push(observations, actions, rewards, next_observations, dones)
        sample = replay.sample(batch_size=4)
        current_version = REPLAY_BUFFER_FORMAT_VERSION
        restored: Any = ReplayBuffer(capacity=16, device=CPU)
    elif replay_kind == "prioritized":
        replay = PrioritizedReplayBuffer(capacity=16, alpha=0.6, beta=0.4, beta_annealing=True, device=CPU)
        replay.push(observations, actions, rewards, next_observations, dones)
        sample = replay.sample(batch_size=4)
        current_version = PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION
        restored = PrioritizedReplayBuffer(capacity=16, alpha=0.6, beta=0.4, beta_annealing=True, device=CPU)
    elif replay_kind == "sequential":
        episode = {
            "observations": observations,
            "actions": actions,
            "rewards": rewards.total,
            "rewards_extrinsic": rewards.extrinsic,
            "rewards_intrinsic": rewards.intrinsic,
            "rewards_shaping": rewards.shaping,
            "next_observations": next_observations,
            "dones": dones,
        }
        legacy_transport = SequentialReplayBuffer(capacity=16, device=CPU)
        legacy_transport.store_episode(episode)
        sample = legacy_transport.sample_sequences(batch_size=2, seq_len=4)
        assert legacy_transport.serialize()["format_version"] == 5
        replay = _qualified_sequence(action_dim)
        replay.store_episode(episode)
        request = ReplayRequest(
            batch_size=2,
            sequence_length=4,
            min_transitions=1,
            sampling_mode="successive_without_replacement",
            sequence_mode="fixed_full",
            sequence_objective="window_mean",
        )
        qualified = replay.sample_batch(request)
        assert qualified.observations.shape == qualified.next_observations.shape == (2, 4, spec.total_dims)
        assert qualified.observations.dtype is qualified.next_observations.dtype is torch.float32
        assert qualified.actions.dtype is torch.int64 and qualified.dones.dtype is torch.bool
        assert qualified.rewards.dtype is torch.float32
        assert torch.equal(qualified.lengths, torch.full((2,), 4, dtype=torch.int64))
        assert qualified.loss_mask.dtype is torch.bool and qualified.loss_mask.all()
        assert qualified.legality_recorded.dtype is torch.bool and qualified.legality_recorded.all()
        assert qualified.next_action_masks.shape == (2, 4, action_dim)
        assert qualified.next_action_masks.dtype is torch.bool and qualified.next_action_masks.all()
        assert qualified.sampling.mode == "legacy_episode_length_with_replacement"
        assert qualified.sampling.objective_unit == "window" and qualified.sampling.weight_rule == "uniform"
        assert qualified.sampling.population_size == 5
        assert np.array_equal(qualified.sampling.conditional_draw_probabilities, np.full(2, 1 / 5, dtype=np.float64))
        assert torch.equal(qualified.weights, torch.ones(2, dtype=torch.float64))
        for row, endpoint in enumerate(qualified.unit_ids.tolist()):
            assert 3 <= endpoint < 8
            selection = slice(endpoint - 3, endpoint + 1)
            for name, values in episode.items():
                _assert_exact_state(values[selection], getattr(qualified, name)[row])
            for name in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
                presence = getattr(qualified, f"{name}_present")
                assert presence.dtype is torch.bool and presence.all()
        current_version = SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION
        restored = _qualified_sequence(action_dim)
    else:
        assert_never(replay_kind)

    assert sample["observations"].shape[-1] == spec.total_dims
    assert sample["observations"].dtype is torch.float32
    assert sample["next_observations"].shape == sample["observations"].shape
    assert sample["next_observations"].dtype is torch.float32
    assert sample["actions"].dtype is torch.int64
    assert sample["rewards"].dtype is torch.float32
    assert sample["dones"].dtype is torch.bool
    if "mask" in sample:
        assert sample["mask"].dtype is torch.bool
    else:
        assert replay_kind == "prioritized"
    if replay_kind == "prioritized":
        assert sample["weights"].dtype is torch.float32
        assert sample["indices"].dtype == np.dtype(np.int64)
    state = replay.serialize()
    assert state["format_version"] == current_version
    if replay_kind == "sequential":
        assert state["action_dim"] == action_dim and state["legality_mode"] == "unconstrained"
        assert state["num_transitions"] == 8 and state["next_episode_id"] == 1 and state["next_transition_id"] == 8
        assert state["historical_archives"] == []
        assert state["replay_options"] == {
            "sampling_mode": "successive_without_replacement",
            "uniform_sequence_adapter": "legacy_episode_length_with_replacement",
            "sequence_mode": "fixed_full",
            "retention_mode": "whole_episode",
            "sequence_objective": "window_mean",
            "priority_reduction": "max_abs",
        }
        assert len(state["episodes"]) == 1
        record = state["episodes"][0]
        assert record["episode_id"] == record["start_offset"] == 0 and record["original_length"] == 8
        _assert_exact_state(torch.arange(8, dtype=torch.int64), record["transition_ids"])
        _assert_exact_state(torch.ones((8, action_dim), dtype=torch.bool), record["next_action_masks"])
        _assert_exact_state(torch.ones(8, dtype=torch.bool), record["legality_recorded"])
        for name, values in episode.items():
            _assert_exact_state(values, record[name])
    restored.load_from_serialized(state)
    restored_state = restored.serialize()
    _assert_exact_state(state, restored_state)

    previous = copy.deepcopy(state)
    previous["format_version"] = current_version - 1
    before_input = copy.deepcopy(previous)
    before_live = copy.deepcopy(restored.serialize())
    if replay_kind == "standard":
        # Current keys with an old tag are a mixed schema, not a genuine v4 artifact.
        previous["format_version"] = 4
        before_input = copy.deepcopy(previous)
        with pytest.raises(ValueError, match="Replay checkpoint key set mismatch"):
            restored.load_from_serialized(previous)
    elif replay_kind == "prioritized":
        # PER6 keys with old5 or old4 tags are mixed schemas, not captured history.
        assert state["format_version"] == 6
        assert previous["format_version"] == 5
        for old_version in (5, 4):
            previous["format_version"] = old_version
            before_input = copy.deepcopy(previous)
            with pytest.raises(ValueError, match="PER checkpoint key set mismatch"):
                restored.load_from_serialized(previous)
            _assert_exact_state(before_input, previous)
            _assert_exact_state(before_live, restored.serialize())
    else:
        # Captured6 with an old5 tag is mixed schema, never an honest old artifact.
        assert state["format_version"] == 6 and previous["format_version"] == 5
        with pytest.raises(ValueError, match="Sequential checkpoint key set mismatch"):
            restored.load_from_serialized(previous)
    _assert_exact_state(before_input, previous)
    _assert_exact_state(before_live, restored.serialize())

    if replay_kind == "standard":
        # Authored historical shape: no current legality/presence/archive fields.
        legacy = {
            "replay_kind": "standard",
            "format_version": 4,
            "capacity": 16,
            "size": 8,
            "position": 8,
            "observations": observations.clone(),
            "actions": actions.clone(),
            "rewards": rewards.total.clone(),
            "rewards_extrinsic": rewards.extrinsic.clone(),
            "rewards_intrinsic": rewards.intrinsic.clone(),
            "rewards_shaping": rewards.shaping.clone(),
            "next_observations": next_observations.clone(),
            "dones": dones.clone(),
        }
        before_legacy = copy.deepcopy(legacy)
        restored.validate_serialized(legacy, expected_obs_dim=spec.total_dims)
        _assert_exact_state(before_legacy, legacy)
        _assert_exact_state(before_live, restored.serialize())
        with pytest.raises(HistoricalLegalityUnavailable, match="missing historical successor masks"):
            restored.load_for_mode(legacy, requested_mode="recorded_full_resume")
        _assert_exact_state(before_legacy, legacy)
        _assert_exact_state(before_live, restored.serialize())

        archived = ReplayBuffer(capacity=16, device=CPU)
        archived.load_from_serialized(legacy)
        assert archived.retained_transitions == len(archived) == archived.position == 0
        assert len(archived.historical_archives) == 1
        with pytest.raises(ValueError, match="Buffer size"):
            archived.sample(batch_size=1)
        _assert_exact_state(before_legacy, legacy)
        archived_state = archived.serialize()
        assert archived_state["format_version"] == current_version
        archive_restored = ReplayBuffer(capacity=16, device=CPU)
        archive_restored.load_from_serialized(archived_state)
        _assert_exact_state(archived_state, archive_restored.serialize())

        unsupported = copy.deepcopy(legacy)
        unsupported["format_version"] = 3
        before_unsupported = copy.deepcopy(unsupported)
        with pytest.raises(ValueError, match="Cannot load replay buffer checkpoint with format_version"):
            restored.load_from_serialized(unsupported)
        _assert_exact_state(before_unsupported, unsupported)
        _assert_exact_state(before_live, restored.serialize())
    elif replay_kind == "prioritized":
        # Independent historical PER4 wire shape, including annealed beta and physical priorities.
        legacy_priorities = np.zeros(16, dtype=np.float32)
        legacy_priorities[:8] = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], dtype=np.float32)
        legacy = {
            "replay_kind": "prioritized",
            "format_version": 4,
            "capacity": 16,
            "alpha": 0.6,
            "beta": 1.0,
            "beta_initial": 0.4,
            "beta_annealing": True,
            "observations": observations.clone(),
            "actions": actions.clone(),
            "rewards": rewards.total.clone(),
            "rewards_extrinsic": rewards.extrinsic.clone(),
            "rewards_intrinsic": rewards.intrinsic.clone(),
            "rewards_shaping": rewards.shaping.clone(),
            "next_observations": next_observations.clone(),
            "dones": dones.clone(),
            "priorities": legacy_priorities,
            "max_priority": 4.0,
            "position": 8,
            "size_current": 8,
        }
        before_legacy = copy.deepcopy(legacy)
        restored.validate_serialized(legacy, expected_obs_dim=spec.total_dims)
        _assert_exact_state(before_legacy, legacy)
        _assert_exact_state(before_live, restored.serialize())
        with pytest.raises(HistoricalLegalityUnavailable, match="missing historical successor masks"):
            restored.load_for_mode(legacy, requested_mode="recorded_full_resume")
        _assert_exact_state(before_legacy, legacy)
        _assert_exact_state(before_live, restored.serialize())

        archived = PrioritizedReplayBuffer(capacity=16, alpha=0.6, beta=0.4, beta_annealing=True, device=CPU)
        archived.load_from_serialized(legacy)
        assert archived.retained_transitions == len(archived) == archived.size_current == archived.position == 0
        assert np.array_equal(archived.priorities, np.zeros(16, dtype=np.float32))
        assert archived.max_priority == 1.0
        assert archived.beta_initial == 0.4
        assert archived.beta == 1.0
        archives = archived.historical_archives
        assert len(archives) == 1
        archive = archives[0]
        assert archive.source_formats == {"scope": "standalone_replay", "replay": 4, "replay_kind": "prioritized"}
        assert archive.archived_row_count == 8
        _assert_exact_state(before_legacy, archive.original_state)
        archived_rows = archive.query_rows(offset=0, limit=8)
        for field in (
            "observations",
            "actions",
            "rewards",
            "rewards_extrinsic",
            "rewards_intrinsic",
            "rewards_shaping",
            "next_observations",
            "dones",
        ):
            _assert_exact_state(before_legacy[field], archived_rows[field])
        assert torch.equal(archived_rows["priorities"], torch.from_numpy(legacy_priorities[:8]))
        with pytest.raises(ValueError, match="Buffer size"):
            archived.sample(batch_size=1)
        _assert_exact_state(before_legacy, legacy)

        archived_state = archived.serialize()
        assert archived_state["format_version"] == 6
        before_archived_state = copy.deepcopy(archived_state)
        archive_restored = PrioritizedReplayBuffer(capacity=16, alpha=0.6, beta=0.4, beta_annealing=True, device=CPU)
        archive_restored.load_from_serialized(archived_state)
        _assert_exact_state(before_archived_state, archived_state)
        _assert_exact_state(before_archived_state, archive_restored.serialize())

        unsupported = copy.deepcopy(legacy)
        unsupported["format_version"] = 3
        before_unsupported = copy.deepcopy(unsupported)
        with pytest.raises(ValueError, match="Cannot load PER checkpoint with format_version 3"):
            restored.load_from_serialized(unsupported)
        _assert_exact_state(before_unsupported, unsupported)
        _assert_exact_state(before_live, restored.serialize())

    elif replay_kind == "sequential":
        # Independent exact old5 wire shape: never relabel captured6 rows/history.
        legacy = {
            "replay_kind": "sequential",
            "format_version": 5,
            "capacity": 16,
            "num_transitions": 8,
            "episodes": [
                {
                    "observations": observations.clone(),
                    "actions": actions.clone(),
                    "rewards": rewards.total.clone(),
                    "rewards_extrinsic": rewards.extrinsic.clone(),
                    "rewards_intrinsic": rewards.intrinsic.clone(),
                    "rewards_shaping": rewards.shaping.clone(),
                    "next_observations": next_observations.clone(),
                    "dones": dones.clone(),
                }
            ],
        }
        before_legacy = copy.deepcopy(legacy)
        restored.validate_serialized(legacy, expected_obs_dim=spec.total_dims)
        _assert_exact_state(before_legacy, legacy)
        _assert_exact_state(before_live, restored.serialize())
        with pytest.raises(HistoricalLegalityUnavailable, match="missing historical successor masks"):
            restored.load_for_mode(legacy, requested_mode="recorded_full_resume")
        _assert_exact_state(before_legacy, legacy)
        _assert_exact_state(before_live, restored.serialize())

        archived = _qualified_sequence(action_dim)
        archived.load_from_serialized(legacy)
        assert archived.retained_transitions == archived.num_transitions == len(archived) == 0
        assert archived.readiness(request).reason == "warmup"
        with pytest.raises(ValueError, match="buffer is empty"):
            archived.sample_sequences(batch_size=1, seq_len=1)
        with pytest.raises(ValueError, match="warmup"):
            archived.sample_batch(request)
        archives = archived.historical_archives
        assert len(archives) == 1
        archive = archives[0]
        assert archive.source_formats == {"scope": "standalone_replay", "replay": 5, "replay_kind": "sequential"}
        assert archive.archived_row_count == 8
        _assert_exact_state(before_legacy, archive.original_state)
        rows = archive.query_rows(offset=0, limit=8)
        for field, values in legacy["episodes"][0].items():
            _assert_exact_state(values, rows[field])
        for field in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
            assert rows[f"{field}_present"].all()
        assert torch.equal(rows["episode_ids"], torch.zeros(8, dtype=torch.int64))
        _assert_exact_state(before_legacy, legacy)

        archived_state = archived.serialize()
        assert archived_state["format_version"] == 6
        archive_restored = _qualified_sequence(action_dim)
        archive_restored.load_from_serialized(archived_state)
        _assert_exact_state(archived_state, archive_restored.serialize())
        # Fresh qualified data stays active while the old artifact stays archive-only.
        archive_restored.store_episode(episode)
        combined = archive_restored.serialize()
        assert combined["num_transitions"] == 8
        assert combined["next_episode_id"] == 1 and combined["next_transition_id"] == 8
        _assert_exact_state(archived_state["historical_archives"], combined["historical_archives"])
        combined_restored = _qualified_sequence(action_dim)
        combined_restored.load_for_mode(combined, requested_mode="recorded_full_resume")
        _assert_exact_state(combined, combined_restored.serialize())

        for unsupported_version in (4, 7):
            unsupported = copy.deepcopy(legacy)
            unsupported["format_version"] = unsupported_version
            before_unsupported = copy.deepcopy(unsupported)
            with pytest.raises(ValueError, match="supported format_version values are 5 and 6"):
                restored.load_from_serialized(unsupported)
            _assert_exact_state(before_unsupported, unsupported)
            _assert_exact_state(before_live, restored.serialize())


def _effect_spec() -> TokenSpec:
    declarations = (
        EffectDeclaration(id="regen", scope="agent", duration=10, reapply_policy="renew"),
        EffectDeclaration(id="poison", scope="global", duration=5, reapply_policy="stack"),
    )
    contexts: list[TokenContext] = []
    for declaration in declarations:
        payload = [0.0] * len(PAYLOAD_SCHEMAS["effect"])
        payload[: len(EFFECT_STATIC_FEATURES)] = effect_static_payload(declaration)
        contexts.append(TokenContext(context_ref=f"effect:{declaration.id}", fixed_payload=tuple(payload)))
    schema = build_token_type(
        "effect",
        (SlotBinding(slot_index=0, filler_kind="dynamic", filler_ref="effect:0", scope=None),),
        slot_context_payloads=(),
        effect_catalog_contexts=tuple(contexts),
    )
    return TokenSpec(types=(schema,), position_rank=2, transport_version=TOKEN_TRANSPORT_VERSION)


def test_multiworld_effect_context() -> None:
    spec = _effect_spec()
    schema = spec.get_type("effect")
    layout = spec.compact_layout().get_type("effect")
    assert schema is not None and layout is not None
    rows = torch.zeros((2, 1, layout.compact_row_width), dtype=torch.float32)
    EffectTokenPublisher(schema, layout, owner_slot_capacity=2).publish(
        rows,
        TokenPublishContext(
            effect_slots=EffectSlotBatch(
                slot_indices=torch.tensor([0]),
                effect_indices=torch.tensor([[0], [1]]),
                remaining_fraction=torch.tensor([[0.5], [0.25]]),
                intensity=torch.tensor([[1.0], [2.0]]),
                owner_slot=torch.tensor([0]),
                active=torch.tensor([[True], [True]]),
            )
        ),
    )
    assembler = TokenInputAssembler(spec)
    expanded = assembler.expand_type("effect", rows)
    static_end = 1 + len(EFFECT_STATIC_FEATURES)
    assert not torch.equal(expanded[0, 0, 1:static_end], expanded[1, 0, 1:static_end])
    torch.testing.assert_close(expanded, _expected_fixed_rows(spec, "effect", rows), rtol=0.0, atol=0.0)

    selector_lane = layout.dynamic_features.index("context_index")
    invalid_selectors = (-1.0, 2.0, 0.5, float("nan"), float("inf"), float("-inf"), 16_777_217.0)
    for selector in invalid_selectors:
        present = torch.zeros((1, 1, layout.compact_row_width), dtype=torch.float64)
        present[:, :, 0] = 1.0
        present[:, :, selector_lane] = selector
        with pytest.raises(ValueError, match="context_index"):
            assembler.expand_type("effect", present)

        absent = present.clone()
        absent[:, :, 0] = 0.0
        assert torch.count_nonzero(assembler.expand_type("effect", absent)) == 0

    mixed = torch.zeros((2, 1, layout.compact_row_width), dtype=torch.float64)
    mixed[0, 0, 0] = 1.0
    mixed[0, 0, selector_lane] = 1.0
    mixed[1, 0, selector_lane] = float("nan")
    mixed_expanded = assembler.expand_type("effect", mixed)
    assert torch.count_nonzero(mixed_expanded[0]) > 0
    assert torch.count_nonzero(mixed_expanded[1]) == 0
