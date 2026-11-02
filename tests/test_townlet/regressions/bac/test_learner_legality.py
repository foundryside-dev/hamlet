"""T15 consumer regressions: real authored learning plus labelled numerical controls.

The real-family matrix and X04 witnesses retain factory-built networks/optimizers.
The PrefixNetwork and controlled ReplayBatch isolate recurrent consumer arithmetic;
they are not evidence of natural provider, native-checkpoint, or factory selection.
"""

from __future__ import annotations

import copy
import hashlib
import random
import shutil
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as F  # noqa: N812
import yaml
from torch import nn

from townlet.config.bac_options import ReplayOptions, resolve_bac_options
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import resolve_exploration_policy
from townlet.curriculum.static import StaticCurriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.count_based import CountExploration
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.rnd import RNDExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.checkpoint_utils import safe_torch_load
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.replay_contract import ReplayBatch, ReplayRequest, SamplingReceipt
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer
from townlet.training.state import RewardTensor
from townlet.universe.compiler import UniverseCompiler

ROOT = Path(__file__).resolve().parents[4]
LEVEL = "L1_full_observability"
CPU = torch.device("cpu")
FAMILIES = ("feedforward", "dueling", "token_set", "recurrent")
LAWS = ("successive_without_replacement", "independent_with_replacement")


def _yaml_edit(path, mutate):
    data = yaml.safe_load(path.read_text())
    mutate(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _options(mode=LAWS[0], sequence_mode="adaptive_prefix", objective="window_mean", retention="transition_tail", reducer="max_abs"):
    return ReplayOptions(
        sampling_mode=mode,
        uniform_sequence_adapter="uniform_windows_with_replacement",
        sequence_mode=sequence_mode,
        retention_mode=retention,
        sequence_objective=objective,
        priority_reduction=reducer,
    )


def _make(
    tmp_path,
    family="feedforward",
    *,
    per=False,
    explicit=False,
    n=2,
    batch=2,
    minimum=2,
    capacity=32,
    length=3,
    frequency=1,
    reward=1.0,
    gamma=0.5,
    double=False,
    alpha=1.0,
    beta=1.0,
    annealing=False,
    options=None,
    template=None,
    global_illegal=True,
    preserve_brain=False,
    initial_tick=0,
    limits=(20, 100),
):
    """Author YAML data, then use the actual compiler/environment/population seam."""
    options = _options() if options is None else options
    pack = tmp_path / "pack"
    shutil.copytree(ROOT / "configs/test/bac_remediation" / family if template is None else template, pack)

    def brain_edit(data):
        data["q_learning"].update(gamma=gamma, use_double_dqn=double, target_update_frequency=1000)
        data["loss"] = {"type": "huber", "huber_delta": 0.25}
        data["replay"] = {"capacity": capacity, "prioritized": per}
        if per:
            data["replay"].update(priority_alpha=alpha, priority_beta=beta, priority_beta_annealing=annealing)
        if family == "feedforward":
            data["architecture"]["feedforward"]["hidden_layers"] = [16]

    def training_edit(data):
        t = data["training"]
        t["seed"] = 42
        t["population"]["size"] = n
        t["randomize_affordances"] = False
        t["q_learning"].update(gamma=gamma, use_double_dqn=double, target_update_frequency=1000)
        t["replay_buffer"].update(capacity=capacity, batch_size=batch, min_size=minimum)
        t["training_loop"].update(max_episodes=20, max_steps_per_episode=100, train_frequency=frequency, sequence_length=length)
        t["exploration"].update(epsilon_start=0.0, epsilon_end=0.0, epsilon_decay=0.99)
        t["enabled_actions"]["custom"] = ["WAIT"] if global_illegal else ["WAIT", "REST", "MEDITATE"]
        t["bac_options"] = {"replay": options.model_dump()}

    def drive_edit(data):
        d = data["drive"]
        d["extrinsic"] = dict(
            type="constant_base_with_shaped_bonus", base_reward=reward, bar_bonuses=[], variable_bonuses=[], apply_modifiers=[]
        )
        d["intrinsic"] = dict(strategy="none", base_weight=0.0, apply_modifiers=[])
        d["shaping"] = []
        d["composition"].update(normalize=False, clip=None)

    if not preserve_brain:
        _yaml_edit(pack / "brain.yaml", brain_edit)
    _yaml_edit(pack / "levels" / LEVEL / "training.yaml", training_edit)
    _yaml_edit(pack / "levels" / LEVEL / "drive.yaml", drive_edit)
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=n, device=CPU)

    def corner(num_agents, device, *, generator):
        return torch.zeros((num_agents, 2), dtype=torch.long, device=device)

    # Labelled deterministic public-initializer fixture; real reset publishes observations.
    env.substrate.initialize_positions = corner
    curriculum = StaticCurriculum(difficulty_level=0.5, reward_mode="shaped", active_meters=None, depletion_multiplier=1.0)
    curriculum.initialize_population(n)
    exploration = EpsilonGreedyExploration(epsilon=0.0, epsilon_decay=1.0, epsilon_min=0.0)
    kwargs = dict(
        env=env,
        curriculum=curriculum,
        exploration=exploration,
        agent_ids=[f"agent_{i}" for i in range(n)],
        device=CPU,
        brain_config=universe.brain,
        obs_dim=env.observation_dim,
        action_dim=env.action_dim,
        train_frequency=frequency,
        batch_size=batch,
        sequence_length=length,
        max_grad_norm=10.0,
        tb_logger=None,
        max_episodes=limits[0],
        max_steps_per_episode=limits[1],
    )
    if explicit:
        pop = VectorizedPopulation.for_training(
            **kwargs,
            replay_options=options,
            min_transitions=minimum,
            replay_rng=np.random.Generator(np.random.PCG64(42)),
            replay_origin="authored",
            beta_vector_tick_horizon=2000,
            beta_horizon_origin="max_episodes(20,authored)*max_steps_per_episode(100,authored)",
            current_vector_tick=initial_tick,
        )
    else:
        pop = VectorizedPopulation(**kwargs)
    assert pop.brain_config.model_dump() == universe.brain.model_dump()
    pop.reset()
    return pop


def _id(pop, name):
    return next(a.id for a in pop.env.level.runtime_action_space.actions if a.name == name)


def _constant(pop, illegal=None):
    """Keep real family forwards/parameters; add a known constant at their output."""
    values = torch.zeros(pop.action_dim)
    values[_id(pop, "WAIT")] = 4.0
    if illegal is not None:
        values[illegal] = 100.0

    def offset(_module, _args, output):
        if isinstance(output, tuple):
            return output[0] + values.to(output[0]), output[1]
        return output + values.to(output)

    with torch.no_grad():
        for network in (pop.q_network, pop.target_network):
            for parameter in network.parameters():
                parameter.zero_()
            network.register_forward_hook(offset)


def _loss_spy(monkeypatch):
    calls = []

    def wrap(original):
        def observe(prediction, target, *args, **kwargs):
            calls.append((prediction.detach().clone(), target.detach().clone()))
            return original(prediction, target, *args, **kwargs)

        return observe

    for name in ("huber_loss", "smooth_l1_loss"):
        monkeypatch.setattr(F, name, wrap(getattr(F, name)))
    return calls


def _finish(pop):
    for i in range(pop.num_agents):
        if not bool(pop.episode_completed[i]):
            pop.flush_episode(i, reason="cap")
    pop.reset()


def _until_update(pop, count=1, limit=24):
    wanted = pop.training_step_counter + count
    for _ in range(limit):
        pop.step_population(pop.env)
        if pop.training_step_counter == wanted:
            return
        _finish(pop)
    pytest.fail(f"No {count} successful updates after {limit} real opportunities")


def _owned(pop):
    return copy.deepcopy(pop.get_checkpoint_state())


def _same(left, right):
    if isinstance(left, torch.Tensor):
        assert left.dtype == right.dtype and left.shape == right.shape and torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            _same(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert type(left) is type(right) and len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _same(a, b)
    else:
        assert left == right


def _tensor_leaves(value):
    if isinstance(value, torch.Tensor):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _tensor_leaves(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from _tensor_leaves(child)


def _assert_disjoint_optimizer_storage(first, second):
    def addresses(state):
        return {(str(t.device), t.untyped_storage().data_ptr()) for t in _tensor_leaves(state) if t.numel()}

    own, other = addresses(first), addresses(second)
    assert own and other and own.isdisjoint(other), "raw population load must own optimizer tensor storage"


def _request(pop, *, minimum=0):
    options = resolve_bac_options(pop.env.level.training.bac_options, training=pop.env.level.training).options.replay
    return ReplayRequest(
        pop.batch_size,
        pop.sequence_length if pop.is_recurrent else 1,
        minimum,
        options.sampling_mode if pop.use_per or pop.is_recurrent else "uniform_without_replacement",
        options.sequence_mode if pop.is_recurrent else "feedforward",
        options.sequence_objective if pop.is_recurrent else "transition",
    )


def _episode(pop, rows, *, reward=1.0, terminal=False):
    obs = torch.zeros(rows, pop.env.observation_dim)
    obs[:, 0] = torch.arange(1, rows + 1)
    done = torch.zeros(rows, dtype=torch.bool)
    done[-1] = terminal
    masks = torch.zeros(rows, pop.action_dim, dtype=torch.bool)
    masks[:, _id(pop, "WAIT")] = True
    masks[done] = False
    return (
        dict(
            observations=obs,
            actions=torch.full((rows,), _id(pop, "WAIT"), dtype=torch.long),
            rewards=torch.full((rows,), reward),
            next_observations=obs + 0.25,
            dones=done,
        ),
        masks,
    )


def _store(pop, rows, **kwargs):
    episode, masks = _episode(pop, rows, **kwargs)
    pop.replay_buffer.store_captured_episode(episode, next_action_masks=masks, legality_recorded=torch.ones(rows, dtype=torch.bool))


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("double", (False, True))
@pytest.mark.parametrize("global_illegal", (False, True), ids=("state-mask", "global-mask"))
@pytest.mark.parametrize("per", (False, True), ids=("uniform", "per"))
def test_authored_target_matrix_and_direction(tmp_path, monkeypatch, family, double, global_illegal, per):
    # A real flat constructor reaches today's wrong target, independently of the new factory.
    pop = _make(tmp_path, family, per=per, explicit=family == "recurrent", double=double, length=1, global_illegal=global_illegal)
    masks = pop.env.get_action_masks()
    if global_illegal:
        illegal = _id(pop, "REST")
    else:
        illegal = next(
            a.id
            for a in pop.env.level.runtime_action_space.actions
            if a.type == "movement" and a.delta is not None and not bool(masks[:, a.id].any())
        )
    assert not bool(masks[:, illegal].any())
    _constant(pop, illegal)
    calls = _loss_spy(monkeypatch)
    before = [p.detach().clone() for p in pop.q_network.parameters()]
    _until_update(pop)
    prediction, target = calls[0]
    torch.testing.assert_close(target, torch.full_like(target, 3.0), rtol=0, atol=1e-6)
    assert all(torch.isfinite(p).all() for p in pop.q_network.parameters())
    assert any(not torch.equal(a, b) for a, b in zip(before, pop.q_network.parameters(), strict=True))
    assert prediction.reshape(-1)[0].item() == pytest.approx(4.0)
    with torch.no_grad():
        out = (
            pop.q_network(pop.current_obs.unsqueeze(1), pop.q_network.initial_hidden(pop.num_agents, CPU))[0][:, 0]
            if pop.is_recurrent
            else pop.q_network(pop.current_obs)
        )
    assert bool((out[:, _id(pop, "WAIT")] < 4.0).all())
    sampled = pop.replay_buffer.sample_batch(_request(pop))
    assert sampled.legality_recorded.all() and not sampled.next_action_masks[..., illegal].any()


@pytest.mark.parametrize("family", ("feedforward", "recurrent"))
@pytest.mark.parametrize("per", (False, True))
def test_terminal_and_truncation_controls(tmp_path, monkeypatch, family, per):
    pop = _make(tmp_path, family, per=per, explicit=family == "recurrent", length=1, reward=0.0)
    _constant(pop, _id(pop, "REST"))
    calls = _loss_spy(monkeypatch)
    health = pop.env.bars_config.meter_names.index("health")
    for _ in range(4):
        # Actual lethal meter state; ENV computes the terminal and its all-false mask.
        pop.env.meters[:, health] = 0.0
        state = pop.step_population(pop.env)
        assert bool(state.dones.all()) and bool((state.rewards == 0).all())
        assert not bool(state.info["successor_action_masks"].any())
        if pop.training_step_counter:
            break
        _finish(pop)
    assert pop.training_step_counter == 1
    assert calls and all(bool((target == 0).all()) for _, target in calls)
    cap = _make(tmp_path / "cap", family, per=per, explicit=family == "recurrent", length=1)
    _constant(cap, _id(cap, "REST"))
    calls.clear()
    cap.step_population(cap.env)
    assert not bool(cap.env.dones.any())
    _finish(cap)
    _until_update(cap)
    torch.testing.assert_close(calls[-1][1], torch.full_like(calls[-1][1], 3.0))


@pytest.mark.parametrize("per,alpha", ((False, 0.0), (True, 0.0), (True, 1.0)))
@pytest.mark.parametrize("reward", (1.0, 2e38), ids=("modest", "large-finite"))
def test_large_finite_td_mean_is_truthful(tmp_path, monkeypatch, per, alpha, reward):
    # No network injection or buffer/priority writes: the admitted authored X04 witness.
    pop = _make(tmp_path, per=per, alpha=alpha, reward=reward, gamma=0.0, capacity=2, length=1)
    calls = _loss_spy(monkeypatch)
    for expected_step in (1, 2):
        before = [p.detach().clone() for p in pop.q_network.parameters()]
        pop.step_population(pop.env)
        assert pop.training_step_counter == expected_step
        prediction, target = calls[-1]
        oracle = (target.to(torch.float64) - prediction.to(torch.float64)).abs().mean().item()
        assert np.isfinite(oracle) and pop.get_training_metrics()["td_error"] == pytest.approx(oracle, rel=2e-6)
        assert np.isfinite(pop.last_loss)
        assert any(not torch.equal(a, b) for a, b in zip(before, pop.q_network.parameters(), strict=True))
        assert all(torch.isfinite(p).all() for p in pop.q_network.parameters())
        for state in pop.optimizer.state.values():
            assert all(not isinstance(v, torch.Tensor) or torch.isfinite(v).all() for v in state.values())
        if reward > 1e38:
            assert bool((target > 1.9e38).all()) and bool((target < 2.1e38).all())


def test_declared_warmup_blocks_existing_constructor(tmp_path):
    pop = _make(tmp_path, minimum=12)
    before = _owned(pop)
    pop.step_population(pop.env)
    assert pop.training_step_counter == 0, "batch occupancy cannot replace the authored retained-transition minimum"
    _same(before["optimizer"], pop.optimizer.state_dict())
    _same(before["target_network"], pop.target_network.state_dict())


@pytest.mark.parametrize("per", (False, True))
@pytest.mark.parametrize("frequency", (1, 2))
def test_ready_skip_preserves_update_clocks(tmp_path, per, frequency):
    pop = _make(tmp_path, per=per, minimum=6, frequency=frequency, beta=0.4, annealing=True)
    pop.scheduler = torch.optim.lr_scheduler.StepLR(pop.optimizer, step_size=1, gamma=0.5)
    initial = _owned(pop)
    for tick in (1, 2):
        rng_before = copy.deepcopy(np.random.get_state())
        pop.step_population(pop.env)
        assert pop.total_steps == tick and pop.training_step_counter == 0
        _same(initial["optimizer"], pop.optimizer.state_dict())
        _same(initial["scheduler"], pop.scheduler.state_dict())
        _same(initial["target_network"], pop.target_network.state_dict())
        _same(rng_before, np.random.get_state())
        if per:
            assert pop.replay_buffer.beta == pytest.approx(0.4 + 0.6 * tick / 2000)
    pop.q_network.eval()
    pop.target_network.train()
    _until_update(pop)
    assert pop.scheduler.last_epoch == 1 and pop.q_network.training and not pop.target_network.training
    assert pop.training_step_counter == 1
    assert pop.total_steps == (3 if frequency == 1 else 4)


@pytest.mark.parametrize(
    "rows,capacity,length,mode,reason",
    (
        (2, 64, 3, "fixed_full", "window_unavailable"),
        (2, 15, 3, "fixed_full", "window_unavailable"),
        (1, 1, 8, "fixed_full", "capacity_window_impossible"),
    ),
)
def test_real_sequence_readiness_skips_legacy_episode_gate(tmp_path, monkeypatch, caplog, rows, capacity, length, mode, reason):
    caplog.set_level("INFO", logger="townlet.population.vectorized")
    options = _options(sequence_mode=mode)
    pop = _make(tmp_path, "recurrent", minimum=1, capacity=capacity, length=length, options=options)
    # Explicit storage attachment isolates the existing consumer gate, not natural factory proof.
    pop.replay_buffer = SequentialReplayBuffer.for_replay(
        capacity, CPU, options=options, action_dim=pop.action_dim, legality_mode="captured"
    )
    for _ in range(16):
        _store(pop, rows)
    readiness = pop.replay_buffer.readiness(_request(pop))
    assert not readiness.ready and readiness.reason == reason
    assert readiness.retained_transitions <= capacity and readiness.sampleable_units == 0
    before = _owned(pop)

    def forbidden(*args, **kwargs):
        pytest.fail("unready captured replay must not enter the legacy sampler")

    monkeypatch.setattr(pop.replay_buffer, "sample_sequences", forbidden)
    monkeypatch.setattr(pop.replay_buffer, "sample_batch", forbidden)
    pop.step_population(pop.env)
    pop.step_population(pop.env)
    assert pop.training_step_counter == 0
    _same(before["optimizer"], pop.optimizer.state_dict())
    _same(before["target_network"], pop.target_network.state_dict())
    assert pop.rollout_hidden is not None and bool(pop.rollout_hidden[0].abs().any())
    assert sum(reason in record.getMessage() for record in caplog.records) == 1, "unchanged readiness diagnostics must not repeat"


@pytest.mark.parametrize("per", (False, True))
def test_adaptive_capacity_one_uses_one_real_row(tmp_path, monkeypatch, per):
    pop = _make(tmp_path, "recurrent", per=per, explicit=True, capacity=1, batch=1, minimum=1, length=8)
    _constant(pop, _id(pop, "REST"))
    calls = _loss_spy(monkeypatch)
    _until_update(pop)
    batch = pop.replay_buffer.sample_batch(_request(pop, minimum=1))
    assert batch.lengths.tolist() == [1] and int(batch.loss_mask.sum()) == 1
    assert calls[0][0].numel() == 1 and calls[0][1].reshape(-1).item() == pytest.approx(3.0)


@pytest.mark.parametrize("mode,expected", ((LAWS[0], 0), (LAWS[1], 1)))
def test_successive_and_replacement_have_different_batch_readiness(tmp_path, mode, expected):
    pop = _make(tmp_path, per=True, explicit=True, n=1, capacity=4, batch=3, minimum=1, options=_options(mode))
    pop.step_population(pop.env)
    assert pop.training_step_counter == expected


@pytest.mark.parametrize("mode,expected_updates", ((LAWS[0], 0), (LAWS[1], 1)))
def test_recurrent_one_window_readiness_distinguishes_laws(tmp_path, monkeypatch, mode, expected_updates):
    pop = _make(
        tmp_path,
        "recurrent",
        per=True,
        explicit=True,
        n=1,
        capacity=16,
        batch=2,
        minimum=1,
        length=3,
        beta=0.4,
        annealing=True,
        options=_options(mode, sequence_mode="fixed_full"),
    )
    _constant(pop, _id(pop, "REST"))
    pop.scheduler = torch.optim.lr_scheduler.StepLR(pop.optimizer, step_size=1, gamma=0.5)
    _store(pop, 3)  # Three retained transitions form exactly ONE L3 window.
    readiness = pop.replay_buffer.readiness(_request(pop, minimum=1))
    assert readiness.retained_transitions == 3 >= pop.batch_size and readiness.sampleable_units == 1
    assert readiness.ready == bool(expected_updates)
    if not expected_updates:
        assert readiness.reason == "batch_unavailable"
    before = _owned(pop)
    draws = []
    sample = pop.replay_buffer.sample_batch

    def sample_observed(request):
        batch = sample(request)
        draws.append(batch)
        return batch

    monkeypatch.setattr(pop.replay_buffer, "sample_batch", sample_observed)
    pop.step_population(pop.env)
    state = pop.replay_buffer.serialize()
    assert pop.total_steps == 1 and pop.training_step_counter == pop.scheduler.last_epoch == expected_updates
    assert state["priority_state"]["current_vector_tick"] == 1
    assert state["priority_state"]["beta"] == pytest.approx(0.4 + 0.6 / 2000)
    assert pop.replay_buffer.retained_transitions == 3, "pending rollout rows do not create retained windows"
    assert len(draws) == expected_updates
    if not expected_updates:
        _same(before["optimizer"], pop.optimizer.state_dict())
        _same(before["scheduler"], pop.scheduler.state_dict())
        _same(before["target_network"], pop.target_network.state_dict())
        _same(before["replay_buffer"]["priority_state"]["rng"], state["priority_state"]["rng"])
    else:
        assert draws[0].lengths.tolist() == [3, 3] and draws[0].unit_ids.unique().numel() == 1
        assert any(not torch.equal(before["q_network"][name], value) for name, value in pop.q_network.state_dict().items())
        assert all(torch.isfinite(p).all() for p in pop.q_network.parameters())


@pytest.mark.parametrize("family", ("feedforward", "recurrent"))
def test_batch_one_and_update_modes(tmp_path, monkeypatch, family):
    pop = _make(tmp_path, family, explicit=family == "recurrent", n=1, batch=1, minimum=1, length=1)
    _constant(pop)
    calls = _loss_spy(monkeypatch)
    pop.q_network.eval()
    pop.target_network.train()
    _until_update(pop)
    assert calls[0][0].shape == calls[0][1].shape and calls[0][0].numel() == 1
    if family == "feedforward":
        assert calls[0][0].shape == (1,)
    assert pop.q_network.training and not pop.target_network.training


class PrefixNetwork(nn.Module):
    """Analytic history-sensitive numerical fixture; parameters really optimize."""

    def __init__(self, width, wait, alternative, coefficient):
        super().__init__()
        self.coefficient = nn.Parameter(torch.tensor(float(coefficient)))
        self.width, self.wait, self.alternative = width, wait, alternative
        self.calls = []

    def initial_hidden(self, batch_size, device):
        return torch.zeros(1, batch_size, 1, device=device), torch.zeros(1, batch_size, 1, device=device)

    def forward(self, observations, hidden):
        assert torch.isfinite(observations).all(), "padding reached the recurrent network"
        value = hidden[0][0, :, 0]
        outputs = []
        for t in range(observations.shape[1]):
            x = observations[:, t, 0]
            value = value + self.coefficient * x
            if value.requires_grad:
                value.retain_grad()
            self.calls.append((x.detach().clone(), value, self.training, torch.is_grad_enabled()))
            q = value[:, None].expand(-1, self.width).clone() * 0
            q[:, self.wait] = value
            q[:, self.alternative] = 20 - value
            outputs.append(q)
        final = value.reshape(1, -1, 1)
        return torch.stack(outputs, dim=1), (final, final.clone())


def _numerical_batch(pop, objective, poison, weights=(2.0, 0.5), reward=1.0):
    """Select genuine unit handles, then supply an explicit controlled DTO oracle."""
    alternative = _id(pop, "REST")
    for observations, successors in (([1.0, 2.0, 3.0], [7.0, 2.0, 1.0]), ([5.0], [9.0])):
        episode, masks = _episode(pop, len(observations), reward=reward)
        episode["observations"][:, 0] = torch.tensor(observations)
        episode["next_observations"][:, 0] = torch.tensor(successors)
        masks[:, alternative] = True
        pop.replay_buffer.store_captured_episode(
            episode, next_action_masks=masks, legality_recorded=torch.ones(len(observations), dtype=torch.bool)
        )
    if pop.use_per:
        # Admit another L-domain first: real stable IDs then differ from sampler positions.
        pop.replay_buffer.sample_batch(replace(_request(pop), sequence_length=1, batch_size=1))
    request = replace(_request(pop), batch_size=4 if pop.use_per and request_mode(pop) == LAWS[0] else 64)
    pool = pop.replay_buffer.sample_batch(request)
    first = torch.nonzero(pool.lengths == 3).flatten()[0].item()
    second = torch.nonzero((pool.lengths == 1) & (pool.observations[:, 0, 0] == 5)).flatten()[0].item()
    selected = torch.tensor([first, second])
    obs = pool.observations[selected].clone()
    nxt = pool.next_observations[selected].clone()
    actions = pool.actions[selected].clone()
    rewards = pool.rewards[selected].clone()
    masks = pool.next_action_masks[selected].clone()
    done = pool.dones[selected].clone()
    recorded = pool.legality_recorded[selected].clone()
    loss_mask = pool.loss_mask[selected].clone()
    if poison:
        obs[1, 1:] = float("nan")
        nxt[1, 1:] = float("inf")
        actions[1, 1:] = -999
        rewards[1, 1:] = float("nan")
        masks[1, 1:] = False
        recorded[1, 1:] = False
    receipt = SamplingReceipt(
        indices=pool.sampling.indices[selected.numpy()],
        weights=np.array(weights, dtype=np.float64),
        population_size=4,
        conditional_draw_probabilities=np.array([0.25, 0.25]),
        mode=pool.sampling.mode,
        objective_unit=pool.sampling.objective_unit,
        weight_rule=pool.sampling.weight_rule,
    )
    assert loss_mask.tolist() == (
        [[False, False, True], [True, False, False]] if objective == "anchor_transition" else [[True, True, True], [True, False, False]]
    )
    return ReplayBatch(
        observations=obs,
        next_observations=nxt,
        actions=actions,
        rewards=rewards,
        rewards_extrinsic=None,
        rewards_intrinsic=None,
        rewards_shaping=None,
        dones=done,
        next_action_masks=masks,
        legality_recorded=recorded,
        loss_mask=loss_mask,
        lengths=pool.lengths[selected],
        unit_ids=pool.unit_ids[selected],
        weights=torch.tensor(weights, dtype=torch.float64),
        sampling=receipt,
    )


def request_mode(pop):
    return pop.env.level.training.bac_options.replay.sampling_mode


@pytest.mark.parametrize("mode", LAWS)
@pytest.mark.parametrize("per", (False, True))
@pytest.mark.parametrize("objective", ("window_mean", "anchor_transition"))
@pytest.mark.parametrize("reducer", ("max_abs", "mean_abs"))
@pytest.mark.parametrize("poison", (False, True))
def test_exact_prefix_bptt_objective_stable_feedback_and_unweighted_td(tmp_path, monkeypatch, mode, per, objective, reducer, poison):
    options = _options(mode, objective=objective, reducer=reducer)
    if not per:
        options = ReplayOptions.model_validate(
            {**options.model_dump(), "uniform_sequence_adapter": "legacy_episode_length_with_replacement"}
        )
    pop = _make(tmp_path, "recurrent", per=per, explicit=True, global_illegal=False, double=True, options=options)
    batch = _numerical_batch(pop, objective, poison)
    online = PrefixNetwork(pop.action_dim, _id(pop, "WAIT"), _id(pop, "REST"), 1)
    target = PrefixNetwork(pop.action_dim, _id(pop, "WAIT"), _id(pop, "REST"), 2)
    pop.q_network, pop.target_network = online, target
    pop.optimizer = torch.optim.Adam(online.parameters(), lr=0.001)
    pop.scheduler = None
    pop.rollout_hidden = online.initial_hidden(pop.num_agents, CPU)
    online.eval()
    target.train()
    calls = _loss_spy(monkeypatch)
    feedback = []
    update = pop.replay_buffer.update_priorities

    def update_observed(ids, errors, *, loss_mask):
        feedback.append((ids.detach().clone(), errors.detach().clone(), loss_mask.detach().clone()))
        return update(ids, errors, loss_mask=loss_mask)

    monkeypatch.setattr(pop.replay_buffer, "sample_batch", lambda request: batch)
    monkeypatch.setattr(pop.replay_buffer, "update_priorities", update_observed)
    pop.step_population(pop.env)
    targets = torch.cat([t.reshape(-1) for _, t in calls])
    # Independent arithmetic: prefix sums1,3,6/5; own target coefficient2;
    # Double selects REST at online successor sums8,5,7, WAIT at14.
    assert set(targets.tolist()) <= {3.0, 4.0, 6.0, 15.0} and {4.0, 15.0} <= set(targets.tolist())
    if objective == "window_mean":
        assert sorted(targets.tolist()) == [3.0, 4.0, 6.0, 15.0]
    per_unit = (0.25 * (2 + 3 + 2) / 3 - 0.25**2 / 2) if objective == "window_mean" else (0.25 * 2 - 0.25**2 / 2)
    expected = (2 * per_unit + 0.5 * (0.25 * 10 - 0.25**2 / 2)) / 2
    assert pop.last_loss == pytest.approx(expected)
    assert pop.last_td_error == pytest.approx(4.25), "all real rows, without IS or anchor weighting"
    assert pop.training_step_counter == 1 and online.coefficient.item() != 1.0
    if per:
        ids, errors, mask = feedback[0]
        torch.testing.assert_close(ids, batch.unit_ids)
        torch.testing.assert_close(mask, batch.loss_mask)
        torch.testing.assert_close(errors[0, mask[0]].abs(), torch.tensor([2.0, 3.0, 2.0], dtype=torch.float64)[mask[0]])
        assert errors[1, 0].abs().item() == pytest.approx(10)
    else:
        assert not feedback
    assert all(training for _, _, training, grad in online.calls if grad)
    assert all(not training and not grad for _, _, training, grad in target.calls)
    early = [value for x, value, _, grad in online.calls if grad and x.tolist() == [1.0]]
    assert early and any(
        value.grad is not None and bool(value.grad.abs().any()) for value in early
    ), "anchor loss must backpropagate through earlier real context"


def _subset(batch, indices, weights):
    indices = torch.tensor(indices)
    values = {
        name: (getattr(batch, name)[indices] if isinstance(getattr(batch, name), torch.Tensor) else getattr(batch, name))
        for name in batch.__dataclass_fields__
    }
    values["weights"] = torch.tensor(weights, dtype=torch.float64)
    values["sampling"] = replace(
        batch.sampling,
        indices=batch.sampling.indices[indices.numpy()],
        weights=np.array(weights, dtype=np.float64),
        conditional_draw_probabilities=batch.sampling.conditional_draw_probabilities[indices.numpy()],
    )
    return ReplayBatch(**values)


@pytest.mark.parametrize("per", (False, True))
@pytest.mark.parametrize("single", (False, True), ids=("unequal-lengths", "batch-one"))
def test_recurrent_large_finite_mean_excludes_padding_and_weights(tmp_path, monkeypatch, per, single):
    pop = _make(tmp_path, "recurrent", per=per, explicit=True, batch=1 if single else 2, gamma=0.0, global_illegal=False)
    batch = _numerical_batch(pop, "window_mean", True, reward=2e38)
    if single:
        batch = _subset(batch, [0], [2.0])
    calls = _loss_spy(monkeypatch)
    monkeypatch.setattr(pop.replay_buffer, "sample_batch", lambda request: batch)
    pop.step_population(pop.env)
    real = torch.arange(batch.observations.shape[1])[None, :] < batch.lengths[:, None]
    # Every real residual differs from2e38 by only ordinary finite network Q.
    expected = batch.rewards[real].double().mean().item()
    assert pop.training_step_counter == 1 and np.isfinite(pop.last_loss)
    assert pop.last_td_error == pytest.approx(expected, rel=2e-6)
    assert all(torch.isfinite(prediction).all() and torch.isfinite(target).all() for prediction, target in calls)
    assert all(torch.isfinite(p).all() for p in pop.q_network.parameters())


def test_recurrent_repeated_ids_use_canonical_mask(tmp_path, monkeypatch):
    pop = _make(
        tmp_path,
        "recurrent",
        per=True,
        explicit=True,
        global_illegal=False,
        options=_options(LAWS[1], objective="anchor_transition", reducer="mean_abs"),
    )
    batch = _subset(_numerical_batch(pop, "anchor_transition", True), [0, 0], [2.0, 0.5])
    assert batch.unit_ids[0] == batch.unit_ids[1]
    calls = []
    update = pop.replay_buffer.update_priorities

    def feedback(ids, errors, *, loss_mask):
        calls.append((ids.clone(), loss_mask.clone()))
        return update(ids, errors, loss_mask=loss_mask)

    monkeypatch.setattr(pop.replay_buffer, "sample_batch", lambda request: batch)
    monkeypatch.setattr(pop.replay_buffer, "update_priorities", feedback)
    pop.step_population(pop.env)
    assert pop.training_step_counter == 1 and len(calls) == 1
    torch.testing.assert_close(calls[0][0], batch.unit_ids)
    torch.testing.assert_close(calls[0][1], batch.loss_mask)


@pytest.mark.parametrize("mode", LAWS)
def test_flat_feedback_uses_owned_stable_ids_after_overwrite(tmp_path, monkeypatch, mode):
    pop = _make(tmp_path, per=True, capacity=2, options=_options(mode))
    _until_update(pop, count=2)
    sampled, feedback = [], []
    sample = pop.replay_buffer.sample_batch
    update = pop.replay_buffer.update_unit_priorities

    def sampling(request):
        batch = sample(request)
        sampled.append(batch)
        return batch

    def updating(ids, errors):
        assert ids.dtype == np.int64 and ids.flags.owndata
        assert not np.shares_memory(ids, sampled[-1].unit_ids.numpy())
        feedback.append((ids.copy(), errors.detach().clone()))
        return update(ids, errors)

    monkeypatch.setattr(pop.replay_buffer, "sample_batch", sampling)
    monkeypatch.setattr(pop.replay_buffer, "update_unit_priorities", updating)
    pop.step_population(pop.env)
    assert len(sampled) == len(feedback) == 1
    np.testing.assert_array_equal(feedback[0][0], sampled[0].unit_ids.numpy())
    assert not np.array_equal(feedback[0][0], sampled[0].sampling.indices)
    assert feedback[0][1].shape == (pop.batch_size,) and torch.isfinite(feedback[0][1]).all()


def _adaptive_snapshot_provider(pop, snapshot):
    rnd = snapshot["rnd_state"]
    return AdaptiveIntrinsicExploration(
        obs_dim=rnd["obs_dim"],
        embed_dim=rnd["embed_dim"],
        rnd_learning_rate=rnd["optimizer"]["param_groups"][0]["lr"],
        rnd_training_batch_size=pop.batch_size,
        initial_intrinsic_weight=snapshot["current_intrinsic_weight"],
        min_intrinsic_weight=snapshot["min_intrinsic_weight"],
        variance_threshold=snapshot["variance_threshold"],
        min_survival_fraction=snapshot["min_survival_fraction"],
        max_episode_length=snapshot["max_episode_length"],
        survival_window=snapshot["survival_window"],
        decay_rate=snapshot["decay_rate"],
        epsilon_start=rnd["epsilon"],
        epsilon_min=rnd["epsilon_min"],
        epsilon_decay=rnd["epsilon_decay"],
        device=CPU,
    )


@pytest.mark.parametrize("kind", ("uniform", "per", "sequence-trained"))
def test_archived_rows_cannot_drive_learning(tmp_path, monkeypatch, kind):
    artifact = ROOT / "tests/test_townlet/fixtures/bac_historical" / f"{kind}.pt"
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    payload = safe_torch_load(artifact, map_location="cpu", allow_unsafe_pickle=True)["population_state"]
    old = payload["replay_buffer"]
    family = "recurrent" if kind == "sequence-trained" else "feedforward"
    pop = _make(
        tmp_path,
        family,
        per=kind == "per",
        minimum=6,
        capacity=old["capacity"],
        length=1,
        alpha=old.get("alpha", 1.0),
        beta=old.get("beta_initial", 1.0),
        annealing=old.get("beta_annealing", False),
        template=artifact.parent / f"{kind}-pack",
        preserve_brain=True,
    )
    pop.exploration = _adaptive_snapshot_provider(pop, payload["exploration_state"])
    pop.env.set_exploration_module(pop.exploration)
    pop.load_checkpoint_state(payload)
    # This is actual rawPOP6/old-storage admission, not complete native10/7 orchestration.
    restored = _owned(pop)
    for key in ("q_network", "target_network", "optimizer", "scheduler", "total_steps", "training_step_counter"):
        _same(payload[key], restored[key])
    assert pop.replay_buffer.retained_transitions == 0
    archives = pop.replay_buffer.historical_archives
    assert len(archives) == 1
    _same(old, archives[0].original_state)
    queried = archives[0].query_rows(offset=0, limit=100)
    assert queried["rewards"].numel() == archives[0].archived_row_count
    export = tmp_path / "archive.pt"
    receipt = archives[0].export(export)
    assert export.is_file() and receipt.source_digest == archives[0].source_digest
    # After proving restored learned-state preservation, arrange an explicit known-Q control.
    _constant(pop, _id(pop, "REST"))
    pop.gamma = 0.5  # Labelled numerical control after exact genuine-brain restoration.
    calls = _loss_spy(monkeypatch)
    initial_counter, initial_steps = pop.training_step_counter, pop.total_steps
    initial_optimizer = copy.deepcopy(pop.optimizer.state_dict())
    for _ in range(2):
        pop.step_population(pop.env)
        _finish(pop)
        assert pop.training_step_counter == initial_counter and pop.replay_buffer.retained_transitions <= 4
        _same(initial_optimizer, pop.optimizer.state_dict())
    assert pop.total_steps == initial_steps + 2
    _until_update(pop)
    assert pop.training_step_counter == initial_counter + 1
    assert calls and all(torch.allclose(target, torch.full_like(target, 3.0)) for _, target in calls)
    assert pop.replay_buffer.sample_batch(_request(pop, minimum=6)).legality_recorded.all()
    _same(old, pop.replay_buffer.historical_archives[0].original_state)
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == digest


def _archive(kind):
    name = "sequence-trained" if kind == "recurrent" else kind
    state = safe_torch_load(
        ROOT / "tests/test_townlet/fixtures/bac_historical" / f"{name}.pt", map_location="cpu", allow_unsafe_pickle=True
    )["population_state"]["replay_buffer"]
    if kind == "recurrent":
        buffer = SequentialReplayBuffer(state["capacity"], CPU)
    elif kind == "per":
        buffer = PrioritizedReplayBuffer(state["capacity"], state["alpha"], state["beta_initial"], state["beta_annealing"], CPU)
    else:
        buffer = ReplayBuffer(state["capacity"], CPU)
    buffer.load_from_serialized(state)
    return buffer.historical_archives[0]


@pytest.mark.parametrize("family,per", (("feedforward", False), ("feedforward", True), ("recurrent", False), ("recurrent", True)))
@pytest.mark.parametrize("empty", (False, True), ids=("active-current", "owned-empty-current"))
@pytest.mark.parametrize("install", ("load", "attach"))
def test_load_before_first_step_adopts_current_replay_and_clocks(tmp_path, monkeypatch, family, per, empty, install):
    settings = dict(per=per, minimum=6, beta=0.4, annealing=True, length=1)
    archive_kind = "sequence-trained" if family == "recurrent" else ("per" if per else "uniform")
    settings["template"] = ROOT / "tests/test_townlet/fixtures/bac_historical" / f"{archive_kind}-pack"
    source = _make(tmp_path / "source", family, explicit=True, **settings)
    archive = _archive("recurrent" if family == "recurrent" else ("per" if per else "uniform"))
    if family == "recurrent":
        source.replay_buffer.load_prepared(
            source.replay_buffer.prepare_archived_import((archive,), expected_obs_dim=source.env.observation_dim)
        )
    else:
        source.replay_buffer.install_historical_archive(archive)
    _until_update(source, count=2)
    _finish(source)
    if empty:
        source.replay_buffer.clear()
    saved = _owned(source)
    saved_before = copy.deepcopy(saved)
    assert bool(source.replay_buffer.retained_transitions) != empty
    targets = [_make(tmp_path / label, family, explicit=explicit, **settings) for label, explicit in (("lazy", False), ("eager", True))]
    for target in targets:
        before = _owned(target)
        target.validate_checkpoint_state(saved)
        _same(before, _owned(target))
        if install == "attach" and target is targets[0]:
            # Explicit externally owned attachment control, separate from natural construction.
            if family == "recurrent":
                buffer = SequentialReplayBuffer(32, CPU)
            elif per:
                buffer = PrioritizedReplayBuffer(32, 1.0, 0.4, True, CPU)
            else:
                buffer = ReplayBuffer(32, CPU)
            buffer.load_from_serialized(saved["replay_buffer"])
            target.replay_buffer = buffer
            target.q_network.load_state_dict(saved["q_network"])
            target.target_network.load_state_dict(saved["target_network"])
            target.optimizer.load_state_dict(copy.deepcopy(saved["optimizer"]))
            target.total_steps = saved["total_steps"]
            target.training_step_counter = saved["training_step_counter"]
        else:
            target.load_checkpoint_state(saved)
        _same(saved, _owned(target))
        _same(saved_before, saved)
        _assert_disjoint_optimizer_storage(target.optimizer.state_dict(), saved["optimizer"])
    _assert_disjoint_optimizer_storage(targets[0].optimizer.state_dict(), targets[1].optimizer.state_dict())
    torch.testing.assert_close(targets[0].current_obs, targets[1].current_obs, rtol=0, atol=0)
    assert targets[0].q_network.training == targets[1].q_network.training
    assert targets[0].target_network.training == targets[1].target_network.training
    eager_before = copy.deepcopy(targets[1].optimizer.state_dict())
    sampled = [[], []]

    def spy(index, original):
        def sample(request):
            batch = original(request)
            sampled[index].append(asdict(batch))
            return batch

        return sample

    for index, target in enumerate(targets):
        monkeypatch.setattr(target.replay_buffer, "sample_batch", spy(index, target.replay_buffer.sample_batch))
    rng = torch.get_rng_state().clone(), copy.deepcopy(np.random.get_state()), random.getstate()
    targets[0].step_population(targets[0].env)
    _same(saved_before, saved)
    _same(eager_before, targets[1].optimizer.state_dict())
    after_lazy_rng = torch.get_rng_state().clone(), copy.deepcopy(np.random.get_state()), random.getstate()
    torch.set_rng_state(rng[0])
    np.random.set_state(rng[1])
    random.setstate(rng[2])
    targets[1].step_population(targets[1].env)
    _same(after_lazy_rng, (torch.get_rng_state(), np.random.get_state(), random.getstate()))
    assert len(sampled[0]) == len(sampled[1]) == (0 if empty else 1)
    _same(sampled[0], sampled[1])  # Actual sampled observations/actions/rewards/masks/IDs/receipts.
    _same(saved_before, saved)
    _same(_owned(targets[0]), _owned(targets[1]))
    assert targets[0].total_steps == source.total_steps + 1
    assert targets[0].training_step_counter == source.training_step_counter + (0 if empty else 1)
    assert len(targets[0].replay_buffer.historical_archives) == 1
    # A fallible restore must not move a live clock or discard the adopted sampler.
    bad = copy.deepcopy(saved)
    bad["total_steps"] += 11
    bad["replay_buffer"]["format_version"] = 999
    before = _owned(targets[0])
    with pytest.raises(ValueError):
        targets[0].load_checkpoint_state(bad)
    _same(before, _owned(targets[0]))
    if per and family == "recurrent":
        buffer = targets[0].replay_buffer
        before = copy.deepcopy(buffer.serialize())
        buffer.set_vector_tick(targets[0].total_steps)
        _same(before, buffer.serialize())
        with pytest.raises(ValueError):
            buffer.set_vector_tick(targets[0].total_steps - 1)


def _provider(pop, kind):
    if kind == "none":
        return EpsilonGreedyExploration(epsilon=0.0, epsilon_decay=1.0, epsilon_min=0.0)
    if kind == "rnd":
        return RNDExploration(
            obs_dim=pop.env.observation_dim,
            embed_dim=8,
            learning_rate=0.0001,
            training_batch_size=2,
            epsilon_start=0.0,
            epsilon_min=0.0,
            epsilon_decay=1.0,
            device=CPU,
        )
    if kind == "adaptive_rnd":
        return AdaptiveIntrinsicExploration(
            obs_dim=pop.env.observation_dim,
            embed_dim=8,
            rnd_learning_rate=0.0001,
            rnd_training_batch_size=2,
            initial_intrinsic_weight=1.0,
            min_intrinsic_weight=0.0,
            variance_threshold=100.0,
            min_survival_fraction=0.4,
            max_episode_length=100,
            survival_window=100,
            decay_rate=0.99,
            epsilon_start=0.0,
            epsilon_min=0.0,
            epsilon_decay=1.0,
            device=CPU,
        )
    training = pop.env.level.training
    drive = IntrinsicStrategyConfig.model_validate(dict(strategy=kind, base_weight=0.0, apply_modifiers=[]))
    policy = resolve_exploration_policy(drive, training, training.bac_options)
    if kind == "count_based":
        return CountExploration(policy, **dict(policy.provider_parameters), device=CPU)
    return ICMExploration(
        policy, obs_dim=pop.env.observation_dim, action_dim=pop.action_dim, **dict(policy.provider_parameters), device=CPU
    )


@pytest.mark.parametrize("kind", ("none", "rnd", "adaptive_rnd", "count_based", "icm"))
def test_all_providers_select_only_true_eligible_rows(tmp_path, monkeypatch, kind):
    pop = _make(tmp_path, minimum=16, frequency=1000)
    provider = _provider(pop, kind)
    if kind != "icm":
        pop.exploration = provider
        pop.env.set_exploration_module(provider)
        pop.sync_exploration_metrics()
    pop.env.meters[0, pop.env.bars_config.meter_names.index("health")] = 0.0
    first = pop.step_population(pop.env)
    assert first.dones.tolist() == [True, False]
    if kind == "icm":
        # Establish lifecycle through epsilon, then test actual ICM selection only.
        pop.exploration = provider
        pop.env.set_exploration_module(provider)
        pop.sync_exploration_metrics()
    pop.current_epsilons = torch.tensor([0.91, 0.23])
    expected_obs = pop.current_obs[1:].clone()
    calls = []
    selector_rng = []
    after_attachment = torch.get_rng_state().clone()
    original = provider.select_actions

    def observe(q_values, state, masks=None):
        assert q_values.shape == (1, pop.action_dim), "inactive provider slots must not draw random actions/coins"
        assert state.dones.tolist() == [False] and state.epsilons.tolist() == pytest.approx([0.23])
        torch.testing.assert_close(state.observations, expected_obs)
        assert all(getattr(state, name).shape[0] == 1 for name in ("actions", "rewards", "intrinsic_rewards", "survival_times"))
        before = torch.get_rng_state().clone()
        if kind == "icm":
            torch.testing.assert_close(before, after_attachment)
        result = original(q_values, state, masks)
        after = torch.get_rng_state().clone()
        torch.set_rng_state(before)
        torch.testing.assert_close(original(q_values, state, masks), result)
        torch.testing.assert_close(torch.get_rng_state(), after)
        calls.append(result.clone())
        selector_rng.append(after)
        return result

    monkeypatch.setattr(provider, "select_actions", observe)
    if kind == "icm":

        class SelectionBoundaryError(Exception):
            pass

        scattered = []

        def stop_before_reward(actions, depletion_multiplier):
            scattered.append(actions.detach().clone())
            raise SelectionBoundaryError

        monkeypatch.setattr(pop.env, "step", stop_before_reward)
        with pytest.raises(SelectionBoundaryError):
            pop.step_population(pop.env)
        assert len(calls) == len(scattered) == 1 and scattered[0].shape == (pop.num_agents,)
        assert scattered[0][1].item() == calls[0][0].item()
        assert scattered[0][0].item() == pop.last_selected_q_values[0].argmax().item()
        torch.testing.assert_close(torch.get_rng_state(), selector_rng[0])
        assert not torch.equal(after_attachment, selector_rng[0])
        assert pop.replay_buffer.retained_transitions == 2  # Only the first physical step.
        return  # Full ICM reward/learning remains required under T18e/T18f.
    result = pop.step_population(pop.env)
    assert len(calls) == 1 and result.actions[1].item() == calls[0][0].item()
    assert result.info["active_on_entry"].tolist() == [False, True]
    assert pop.replay_buffer.retained_transitions == 3
    if kind == "adaptive_rnd":
        assert provider.survival_history == [1]
        pop.flush_episode(1, reason="cap")
        pop.flush_episode(1, reason="cap")
        assert provider.survival_history == [1, 2]


def test_eligible_empty_mask_refuses_before_provider_rng(tmp_path, monkeypatch):
    pop = _make(tmp_path, frequency=1000)
    before = torch.get_rng_state().clone()
    monkeypatch.setattr(pop.env, "get_action_masks", lambda: torch.zeros(pop.num_agents, pop.action_dim, dtype=torch.bool))
    with pytest.raises(ValueError, match="eligible|legal"):
        pop.step_population(pop.env)
    torch.testing.assert_close(torch.get_rng_state(), before)


@pytest.mark.parametrize("mode", LAWS)
def test_flat_unequal_td_mean_is_unweighted_and_loss_weights_apply_once(tmp_path, monkeypatch, mode):
    pop = _make(tmp_path, per=True, explicit=True, frequency=2, options=_options(mode))
    _constant(pop, _id(pop, "REST"))
    pop.step_population(pop.env)
    batch = pop.replay_buffer.sample_batch(_request(pop))
    # Deliberately unequal canonical totals/components distinguish recomposition and weighting.
    batch = replace(
        batch,
        rewards=torch.tensor([1.0, 5.0]),
        weights=torch.tensor([2.0, 0.5], dtype=torch.float64),
        sampling=replace(batch.sampling, weights=np.array([2.0, 0.5], dtype=np.float64)),
    )
    monkeypatch.setattr(pop.replay_buffer, "sample_batch", lambda request: batch)
    pop.step_population(pop.env)
    assert pop.training_step_counter == 1
    assert pop.last_td_error == pytest.approx(2.0)
    assert pop.last_loss == pytest.approx((2 * (0.25 - 0.25**2 / 2) + 0.5 * (0.75 - 0.25**2 / 2)) / 2)


@pytest.mark.parametrize("family", ("feedforward", "recurrent"))
def test_learning_never_queries_later_live_legality(tmp_path, monkeypatch, family):
    pop = _make(tmp_path, family, explicit=family == "recurrent", length=1)
    _constant(pop, _id(pop, "REST"))
    original = pop.env.step
    mask_getter = pop.env.get_action_masks

    def committed_step(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(pop.env, "get_action_masks", lambda: pytest.fail("learner queried later live legality"))
        return result

    monkeypatch.setattr(pop.env, "step", committed_step)
    for _ in range(4):
        monkeypatch.setattr(pop.env, "get_action_masks", mask_getter)
        pop.step_population(pop.env)
        if pop.training_step_counter:
            break
        monkeypatch.setattr(pop.env, "get_action_masks", mask_getter)
        _finish(pop)
    assert pop.training_step_counter == 1 and pop.last_td_error == pytest.approx(1.0)


def test_captured_six_adapts_offside_at_restored_tick_for_selected_recurrent_per(tmp_path, monkeypatch):
    source = _make(tmp_path / "uniform", "recurrent", explicit=True, length=1)
    _until_update(source, count=2)
    _finish(source)
    saved = _owned(source)
    assert saved["replay_buffer"]["format_version"] == 6 and source.total_steps > 0
    target = _make(
        tmp_path / "per", "recurrent", per=True, explicit=True, length=1, beta=0.4, annealing=True, initial_tick=source.total_steps
    )
    target.load_checkpoint_state(saved)
    assert target.replay_buffer.retained_transitions == source.replay_buffer.retained_transitions > 0
    assert not target.replay_buffer.historical_archives
    assert target.total_steps == source.total_steps and target.training_step_counter == source.training_step_counter
    _same(saved, _owned(source))
    _constant(target, _id(target, "REST"))
    calls = _loss_spy(monkeypatch)
    _until_update(target)
    assert calls and all(torch.allclose(q_target, torch.full_like(q_target, 3.0)) for _, q_target in calls)
    assert target.replay_buffer.serialize()["priority_state"]["beta"] == pytest.approx(0.4 + 0.6 * target.total_steps / 2000)


def test_flat_population_refuses_ordinary_beta_clock_rewind(tmp_path):
    pop = _make(tmp_path, per=True, explicit=True, minimum=20, frequency=1000, beta=0.4, annealing=True)
    for _ in range(3):
        pop.step_population(pop.env)
    beta = pop.replay_buffer.beta
    pop.total_steps = 0  # Labelled invalid caller clock, not an imported historical tick.
    with pytest.raises(ValueError, match="tick|clock|rewind|monoton"):
        pop.step_population(pop.env)
    assert pop.replay_buffer.beta == beta and pop.training_step_counter == 0


def test_constructor_inspection_preserves_nullable_limits_and_global_per_role(tmp_path):
    pop = _make(tmp_path, per=True, limits=(None, None))
    assert pop.max_episodes is None and pop.max_steps_per_episode is None
    assert pop.select_greedy_actions(pop.env).shape == (pop.num_agents,)
    # Explicit unconstrained inspection adapter, never presented as constrained capture.
    rewards = RewardTensor.from_dac(total=torch.ones(2), extrinsic=torch.ones(2), intrinsic=torch.zeros(2), shaping=torch.zeros(2))
    pop.replay_buffer.push(pop.current_obs, torch.full((2,), _id(pop, "WAIT")), rewards, pop.current_obs, torch.zeros(2, dtype=torch.bool))
    pop.replay_buffer.declare_unconstrained_action_dim(action_dim=pop.action_dim)
    before = copy.deepcopy(np.random.get_state())
    batch = pop.replay_buffer.sample_batch(replace(_request(pop), batch_size=1))
    after = np.random.get_state()
    assert before[2] != after[2] or not np.array_equal(before[1], after[1]), "constructor inspection keeps the external-global sampler"
    assert batch.observations.shape[0] == 1 and pop.training_step_counter == pop.total_steps == 0
