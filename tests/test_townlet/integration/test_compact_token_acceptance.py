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

from townlet.agent.network_factory import NetworkFactory
from townlet.agent.token_input import TokenInputAssembler
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
from townlet.training.replay_buffer import REPLAY_BUFFER_FORMAT_VERSION, ReplayBuffer
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
    fixed_width: int
    deployed_affordances: int


SUBSTRATE_CASES = (
    _SubstrateCase("grid2d", Path("configs/default_curriculum"), "L1_full_observability", 2, 118, 4142, 14),
    _SubstrateCase("grid3d", Path("configs/differential/div003_cubic_partial"), "L2_partial_observability", 3, 152, 4142, 14),
    _SubstrateCase("aspatial", Path("configs/aspatial_test"), "L0", 0, 19, 394, 1),
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
    assert spec.fixed_total_dims == case.fixed_width
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


@pytest.mark.parametrize("replay_kind", ["standard", "prioritized", "sequential"])
def test_replay_matrix(replay_kind: ReplayKind, l1_runtime: tuple[TokenSpec, int, torch.Tensor]) -> None:
    spec, _, _ = l1_runtime
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
        replay = SequentialReplayBuffer(capacity=16, device=CPU)
        replay.store_episode(
            {
                "observations": observations,
                "actions": actions,
                "rewards": rewards.total,
                "rewards_extrinsic": rewards.extrinsic,
                "rewards_intrinsic": rewards.intrinsic,
                "rewards_shaping": rewards.shaping,
                "next_observations": next_observations,
                "dones": dones,
            }
        )
        sample = replay.sample_sequences(batch_size=2, seq_len=4)
        current_version = SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION
        restored = SequentialReplayBuffer(capacity=16, device=CPU)
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
        assert sample["weights"].dtype is torch.float32
        assert sample["indices"].dtype == np.dtype(np.int64)
    state = replay.serialize()
    assert state["format_version"] == current_version
    restored.load_from_serialized(state)
    restored_state = restored.serialize()
    _assert_exact_state(state, restored_state)

    previous = copy.deepcopy(state)
    previous["format_version"] = current_version - 1
    with pytest.raises(ValueError, match=rf"exact current format_version is {current_version}"):
        restored.load_from_serialized(previous)


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
        (SlotBinding(slot_index=0, filler_kind="dynamic", filler_ref="effect:0"),),
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
