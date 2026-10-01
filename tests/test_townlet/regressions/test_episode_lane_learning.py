"""Observe eligible rows and actual optimizer loss targets through real learners."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import torch
import torch.nn as nn
import torch.nn.functional as functional

from tests.test_townlet.regressions.fixtures.episode_lanes import controlled_action_schedule
from tests.test_townlet.regressions.test_episode_lane_population import make_lane_population, schedule_for
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer


def row_digest(row: torch.Tensor) -> str:
    return hashlib.sha256(row.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def assert_admitted_rows(expected: list[tuple[tuple[int, int, int], str]], observed: list[torch.Tensor]) -> None:
    assert Counter(row_digest(row) for row in observed) == Counter(digest for _, digest in expected)


class AdmissionWitness:
    """Bind actual normalization and buffer/predictor calls to independent entry rows."""

    def __init__(self, population):
        self.population = population
        self.rnd = population.exploration.rnd
        self.current = []
        self.pending = []
        self.normalized = []
        self.admitted = []
        self.trained = []
        self.original_update = self.rnd.update_predictor
        self.initial_rms = (float(self.rnd.reward_rms.mean), float(self.rnd.reward_rms.var), float(self.rnd.reward_rms.count))
        self.raw_errors = []
        self.current_normalized = {}

    def enter_step(self, episode: int, tick: int, active: torch.Tensor, observations: torch.Tensor) -> None:
        self.current = [
            ((episode, tick, agent), observations[agent].detach().clone())
            for agent in torch.nonzero(active, as_tuple=False).flatten().tolist()
        ]

    def normalize(self, observations: torch.Tensor) -> None:
        assert len(observations) == len(self.current), "normalization admitted an ineligible coordinate or dropped a terminal"
        self.normalized.extend((coordinate, row_digest(row)) for (coordinate, _), row in zip(self.current, observations, strict=True))

    def reconcile_normalization(self, observations: torch.Tensor, result: torch.Tensor) -> None:
        # Independently pool scalar moments from all eligible errors, including
        # the initial pseudo-sample. Do not call RunningMeanStd.update here.
        with torch.no_grad():
            errors = ((self.rnd.fixed_network(observations) - self.rnd.predictor_network(observations)) ** 2).mean(dim=1)
        self.raw_errors.extend(float(value) for value in errors)
        initial_mean, initial_variance, initial_count = self.initial_rms
        count = initial_count + len(self.raw_errors)
        mean = (initial_count * initial_mean + math.fsum(self.raw_errors)) / count
        variance = (
            initial_count * (initial_variance + (initial_mean - mean) ** 2) + math.fsum((value - mean) ** 2 for value in self.raw_errors)
        ) / count
        assert self.rnd.reward_rms.count == pytest.approx(count)
        assert self.rnd.reward_rms.mean == pytest.approx(mean, rel=1e-5, abs=1e-8)
        assert self.rnd.reward_rms.var == pytest.approx(variance, rel=1e-5, abs=1e-8)
        expected = errors / (math.sqrt(variance) + 1e-8)
        assert torch.allclose(result, expected, rtol=1e-5, atol=1e-6), "eligible RND normalization differs from independent pooled moments"
        self.current_normalized = {coordinate: float(value) for (coordinate, _), value in zip(self.current, expected, strict=True)}

    def reconcile_reward(self, state) -> None:
        env = self.population.env
        drive = env.dac_engine.dac_config
        assert drive.intrinsic.base_weight == 0.1
        assert drive.intrinsic.apply_modifiers == ["energy_crisis"]
        assert drive.extrinsic.type == "constant_base_with_shaped_bonus"
        assert drive.extrinsic.base_reward == 0.01
        assert not drive.composition.normalize and drive.composition.clip is None
        components = state.info["reward_components"]
        active_agents = set()
        for coordinate, _ in self.current:
            agent = coordinate[2]
            active_agents.add(agent)
            energy = float(env.meters[agent, env.meter_name_to_index["energy"]])
            health = float(env.meters[agent, env.meter_name_to_index["health"]])
            retired = bool(state.info["newly_retired"][agent])
            authored_terminal = bool(state.info["newly_terminal"][agent]) and not retired
            raw_weighted = self.current_normalized[coordinate] * 0.1
            modifier = 0.0 if 0.0 <= energy < 0.2 else 1.0
            intrinsic = 0.0 if authored_terminal else raw_weighted * modifier
            extrinsic = 0.0 if authored_terminal else math.fsum((0.01, 0.5 * energy, 0.5 * health))
            extrinsic += float(retired)
            distance = math.dist(env.positions[agent].tolist(), env.affordances["EAT"].tolist())
            shaping = 0.0 if authored_terminal else max(0.0, min(0.01, 0.01 * (1.0 - distance / 5.0)))
            for name, expected in (
                ("extrinsic", extrinsic),
                ("intrinsic", intrinsic),
                ("intrinsic_raw", raw_weighted),
                ("shaping", shaping),
            ):
                assert float(components[name][agent]) == pytest.approx(expected, rel=1e-5, abs=1e-6), (coordinate, name)
            assert float(state.info["intrinsic_weight"][agent]) == modifier
            assert float(state.rewards[agent]) == pytest.approx(math.fsum((extrinsic, intrinsic, shaping)), rel=1e-5, abs=1e-6)
        for agent in set(range(env.num_agents)) - active_agents:
            assert state.rewards[agent] == 0.0
            assert state.info["intrinsic_weight"][agent] == 0.0
            assert all(component[agent] == 0.0 for component in components.values())

    def predictor(self, observations: torch.Tensor) -> None:
        expected = self.pending[: len(observations)]
        assert len(expected) == len(observations)
        for (coordinate, predecessor), row in zip(expected, observations, strict=True):
            assert torch.equal(predecessor, row), "predictor row does not match its actual queued coordinate"
            self.trained.append((coordinate, row_digest(row)))

    def update_predictor(self) -> float:
        self.pending.extend(self.current)
        assert len(self.rnd.obs_buffer) == len(self.pending), "predictor ingestion admitted an ineligible coordinate or dropped a terminal"
        for (_, predecessor), actual in zip(self.pending, self.rnd.obs_buffer, strict=True):
            assert torch.equal(predecessor, actual), "actual predictor ingestion changed coordinate order or predecessor bytes"
        if self.current:
            self.admitted.extend(
                (coordinate, row_digest(actual))
                for (coordinate, _), actual in zip(self.current, self.rnd.obs_buffer[-len(self.current) :], strict=True)
            )
        trained_before = len(self.trained)
        result = self.original_update()
        consumed = len(self.trained) - trained_before
        self.pending = self.pending[consumed:]
        assert len(self.pending) == len(self.rnd.obs_buffer)
        return result


@pytest.mark.parametrize("mode", ["standard", "per", "recurrent"])
def test_one_episode_ingests_seven_owned_predecessors_and_normalizes_seven_successors(tmp_path: Path, mode: str) -> None:
    population = make_lane_population(
        tmp_path / "pack",
        mode=mode,
        num_agents=2,
        lifespan=20,
        batch_size=128,
        sequence_length=1,
        rnd_batch_size=7,
        double_dqn=False,
    )
    rnd = population.exploration.rnd
    admission = AdmissionWitness(population)
    predictor_inputs = []
    normalized_inputs = []
    expected_predecessors = []
    expected_successors = []
    phantom_successors = []
    predictor_before = [parameter.detach().clone() for parameter in rnd.predictor_network.parameters()]
    rms_before = rnd.reward_rms.count
    original_compute = population.exploration.compute_intrinsic_rewards

    def compute(observations, update_stats=False):
        if update_stats:
            admission.normalize(observations)
            normalized_inputs.extend(row.detach().clone() for row in observations)
        result = original_compute(observations, update_stats=update_stats)
        if update_stats:
            admission.reconcile_normalization(observations, result)
        return result

    def predictor_hook(module, args):
        if torch.is_grad_enabled():
            admission.predictor(args[0])
            predictor_inputs.extend(row.detach().clone() for row in args[0])

    hook = rnd.predictor_network.register_forward_pre_hook(predictor_hook)
    try:
        with (
            patch.object(population.exploration, "compute_intrinsic_rewards", side_effect=compute),
            patch.object(rnd, "update_predictor", side_effect=admission.update_predictor),
        ):
            with patch.object(rnd.optimizer, "step", wraps=rnd.optimizer.step) as predictor_steps:
                with controlled_action_schedule(population.exploration, population.env, schedule_for((2, 5))):
                    for tick in range(1, 6):
                        active = ~population.env.dones.clone()
                        predecessor = population.current_obs.clone()
                        admission.enter_step(0, tick, active, predecessor)
                        state = population.step_population(population.env)
                        admission.reconcile_reward(state)
                        for agent in range(2):
                            identity = (0, tick, agent)
                            if bool(active[agent]):
                                expected_predecessors.append((identity, row_digest(predecessor[agent])))
                                expected_successors.append((identity, row_digest(state.observations[agent])))
                            else:
                                phantom_successors.append(row_digest(state.observations[agent]))
                assert predictor_steps.call_count > 0
    finally:
        hook.remove()
    assert len(expected_predecessors) == 7
    assert len(predictor_inputs) == 7
    assert_admitted_rows(expected_predecessors, predictor_inputs)
    assert admission.admitted == expected_predecessors
    assert admission.trained == expected_predecessors
    assert admission.normalized == expected_successors
    assert len(normalized_inputs) == 7
    assert_admitted_rows(expected_successors, normalized_inputs)
    assert rnd.reward_rms.count - rms_before == pytest.approx(7)
    assert len(rnd.obs_buffer) == 0
    assert any(not torch.equal(before, after) for before, after in zip(predictor_before, rnd.predictor_network.parameters(), strict=True))
    # Frozen terminal successors can equal later dead successors. Role overlap is
    # explicitly ambiguous; counts and coordinate-bound ledgers qualify admission.
    eligible = {digest for _, digest in expected_successors}
    qualify_hash_exclusion(eligible, set(phantom_successors))
    # Corrupt a retained role witness with a real eligible digest: a hash-only
    # exclusion claim must then refuse rather than subtract the shared digest.
    corrupted_phantoms = set(phantom_successors) | {next(iter(eligible))}
    with pytest.raises(ValueError, match="ambiguous"):
        qualify_hash_exclusion(eligible, corrupted_phantoms)


def qualify_hash_exclusion(eligible: set[str], phantom: set[str]) -> None:
    if eligible & phantom:
        raise ValueError("Hash-only eligibility proof is ambiguous across ledger coordinates")


@pytest.mark.parametrize("mode,sequence_length", [("standard", 1), ("per", 1), ("recurrent", 1), ("recurrent", 2)])
@pytest.mark.parametrize("double_dqn", [False, True])
@pytest.mark.parametrize("ending", ["terminal", "cap"])
def test_real_learners_keep_terminal_and_truncation_targets(
    tmp_path: Path, mode: str, sequence_length: int, double_dqn: bool, ending: str
) -> None:
    qualify_real_learner(
        tmp_path, mode=mode, sequence_length=sequence_length, double_dqn=double_dqn, ending=ending, corrupt_truncation=False
    )


def qualify_real_learner(
    tmp_path: Path, *, mode: str, sequence_length: int, double_dqn: bool, ending: str, corrupt_truncation: bool
) -> None:
    torch.manual_seed(98)
    population = make_lane_population(
        tmp_path / "pack",
        mode=mode,
        num_agents=2,
        lifespan=20,
        batch_size=2,
        sequence_length=sequence_length,
        rnd_batch_size=7,
        double_dqn=double_dqn,
    )
    rnd = population.exploration.rnd
    admission = AdmissionWitness(population)
    online_before = [parameter.detach().clone() for parameter in population.q_network.parameters()]
    predictor_before = [parameter.detach().clone() for parameter in rnd.predictor_network.parameters()]
    with torch.no_grad():
        for parameter in population.target_network.parameters():
            parameter.zero_()
        output = [module for module in population.target_network.modules() if isinstance(module, nn.Linear)][-1]
        output.bias.fill_(3.0)
    batches = []
    targets = []
    target_inputs = []
    predictor_inputs = []
    normalized_inputs = []
    predecessor_ledger = []
    successor_ledger = []
    cut_rows = set()
    rms_before = rnd.reward_rms.count
    sampler_calls = 0
    original_compute = population.exploration.compute_intrinsic_rewards

    def compute(observations, update_stats=False):
        if update_stats:
            admission.normalize(observations)
            normalized_inputs.extend(row.detach().clone() for row in observations)
        result = original_compute(observations, update_stats=update_stats)
        if update_stats:
            admission.reconcile_normalization(observations, result)
        return result

    def predictor_hook(module, args):
        if torch.is_grad_enabled():
            admission.predictor(args[0])
            predictor_inputs.extend(row.detach().clone() for row in args[0])

    def target_hook(module, args):
        target_inputs.append(args[0].detach().clone())

    def capture_target(target):
        assert len(batches) == len(targets) + 1
        targets.append(target.detach().clone())

    def loss_hook(module, args):
        capture_target(args[1])

    original_loss = functional.smooth_l1_loss

    def functional_loss(prediction, target, **kwargs):
        capture_target(target)
        return original_loss(prediction, target, **kwargs)

    replay = population.replay_buffer
    sampler_name = "sample_sequences" if mode == "recurrent" else "sample"
    original_sample = getattr(replay, sampler_name)

    def sample(**kwargs):
        nonlocal sampler_calls
        sampler_calls += 1
        with ExitStack() as sampling:
            if isinstance(replay, SequentialReplayBuffer):

                def select_episode(episodes, **selection_kwargs):
                    selected = max(episodes, key=lambda episode: len(episode["actions"]))
                    return [selected]

                sampling.enter_context(patch("townlet.training.sequential_replay_buffer.random.choices", side_effect=select_episode))
                starts = iter((0, 1))

                def choose_start(low, high):
                    return high if next(starts) else low

                sampling.enter_context(patch("townlet.training.sequential_replay_buffer.random.randint", side_effect=choose_start))
            else:
                size = len(replay)
                boundary = []
                ordinary = []
                for index in range(size):
                    if bool(replay.dones[index]) or row_digest(replay.observations[index]) in cut_rows:
                        boundary.append(index)
                    else:
                        ordinary.append(index)
                indices = ([boundary[-1]] if boundary else []) + ([ordinary[0]] if ordinary else [])
                indices += [index for index in range(size) if index not in indices]
                if mode == "per":
                    sampling.enter_context(
                        patch("townlet.training.prioritized_replay_buffer.np.random.choice", return_value=np.array(indices[:2]))
                    )
                else:
                    sampling.enter_context(patch("townlet.training.replay_buffer.torch.randperm", return_value=torch.tensor(indices)))
            batch = original_sample(**kwargs)
        batches.append({key: value.detach().clone() for key, value in batch.items() if isinstance(value, torch.Tensor)})
        return batch

    hooks = [
        rnd.predictor_network.register_forward_pre_hook(predictor_hook),
        population.target_network.register_forward_pre_hook(target_hook),
    ]
    try:
        with ExitStack() as stack:
            if mode == "standard":
                hooks.append(population.loss_fn.register_forward_pre_hook(loss_hook))
            else:
                stack.enter_context(patch("townlet.population.vectorized.F.smooth_l1_loss", side_effect=functional_loss))
            stack.enter_context(patch.object(replay, sampler_name, side_effect=sample))
            stack.enter_context(patch.object(population.exploration, "compute_intrinsic_rewards", side_effect=compute))
            stack.enter_context(patch.object(rnd, "update_predictor", side_effect=admission.update_predictor))
            q_steps = stack.enter_context(patch.object(population.optimizer, "step", wraps=population.optimizer.step))
            rnd_steps = stack.enter_context(patch.object(rnd.optimizer, "step", wraps=rnd.optimizer.step))
            for episode in range(9):
                if episode:
                    population.reset()
                schedule = schedule_for((2, 5))
                if ending == "cap":
                    schedule[-1] = ("WAIT", "WAIT")
                with controlled_action_schedule(population.exploration, population.env, schedule):
                    for tick in range(1, 6):
                        active = ~population.env.dones.clone()
                        predecessor = population.current_obs.clone()
                        admission.enter_step(episode, tick, active, predecessor)
                        state = population.step_population(population.env)
                        admission.reconcile_reward(state)
                        for agent in range(2):
                            if bool(active[agent]):
                                identity = (episode, tick, agent)
                                predecessor_ledger.append((identity, row_digest(predecessor[agent])))
                                successor_ledger.append((identity, row_digest(state.observations[agent])))
                                if ending == "cap" and agent == 1 and tick == 5:
                                    cut_rows.add(row_digest(predecessor[agent]))
                if ending == "cap":
                    population.flush_episode(1, reason="cap")
                    if corrupt_truncation:
                        if isinstance(replay, SequentialReplayBuffer):
                            replay.episodes[-1]["dones"][-1] = True
                        else:
                            replay.dones[len(replay) - 1] = True
            assert q_steps.call_count > 0
            assert rnd_steps.call_count > 0
    finally:
        for hook in hooks:
            hook.remove()
    assert len(predecessor_ledger) == 63
    assert len(successor_ledger) == 63
    assert len(predictor_inputs) == 63
    assert_admitted_rows(predecessor_ledger, predictor_inputs)
    assert_admitted_rows(successor_ledger, normalized_inputs)
    assert admission.admitted == predecessor_ledger
    assert admission.trained == predecessor_ledger
    assert admission.normalized == successor_ledger
    assert rnd.reward_rms.count - rms_before == pytest.approx(63)
    assert sampler_calls > 0 and len(batches) == len(targets)
    assert any(not torch.equal(before, after) for before, after in zip(online_before, population.q_network.parameters(), strict=True))
    assert any(not torch.equal(before, after) for before, after in zip(predictor_before, rnd.predictor_network.parameters(), strict=True))
    terminal_rows = 0
    truncated_rows = 0
    ordinary_rows = 0
    for batch, actual in zip(batches, targets, strict=True):
        expected = batch["rewards"] + population.gamma * 3.0 * (~batch["dones"]).float()
        assert torch.allclose(actual, expected, atol=1e-6)
        observations = batch["observations"].reshape(-1, population.env.observation_dim)
        assert all(row_digest(row) in {digest for _, digest in predecessor_ledger} for row in observations)
        terminal_rows += int(batch["dones"].sum())
        truncated_mask = torch.tensor([row_digest(row) in cut_rows for row in observations])
        truncated_rows += int(truncated_mask.sum())
        if truncated_mask.any():
            assert torch.allclose(
                actual.flatten()[truncated_mask], batch["rewards"].flatten()[truncated_mask] + population.gamma * 3.0, atol=1e-6
            ), "truncation target lost the final-successor bootstrap"
        ordinary_rows += sum(
            not bool(done) and row_digest(row) not in cut_rows for row, done in zip(observations, batch["dones"].flatten(), strict=True)
        )
        successor = batch["next_observations"][:, -1:, :] if mode == "recurrent" else batch["next_observations"]
        assert any(torch.equal(successor, observed) for observed in target_inputs)
        if mode == "recurrent":
            assert batch["mask"][:, -1].all()
    assert ordinary_rows > 0
    if ending == "terminal":
        assert terminal_rows > 0
    else:
        assert truncated_rows > 0
        assert any(
            not bool(done) and row_digest(row) in cut_rows
            for batch in batches
            for row, done in zip(batch["observations"].reshape(-1, population.env.observation_dim), batch["dones"].flatten(), strict=True)
        )


@pytest.mark.parametrize("corruption", ["post_step_eligibility", "ghost_admission", "repeated_completion"])
def test_real_population_negative_controls_fail_independent_conformance(tmp_path: Path, corruption: str) -> None:
    population = make_lane_population(
        tmp_path / "pack",
        mode="standard",
        num_agents=2,
        lifespan=20,
        batch_size=128,
        sequence_length=1,
        rnd_batch_size=128,
        double_dqn=False,
    )
    env = population.env
    original_step = env.step
    original_finalize = population._finalize_episode

    def step(actions, depletion_multiplier=1.0):
        observation, rewards, dones, info = original_step(actions, depletion_multiplier)
        if corruption == "post_step_eligibility":
            info["active_on_entry"] = ~dones.clone()
        elif corruption == "ghost_admission":
            info["active_on_entry"] = torch.ones_like(dones)
        elif corruption == "repeated_completion":
            info["newly_terminal"] = dones.clone()
        return observation, rewards, dones, info

    def finalize(agent_idx, reason):
        if corruption == "repeated_completion":
            population.episode_completed[agent_idx] = False
        return original_finalize(agent_idx, reason)

    ledger = torch.zeros(2, dtype=torch.long)
    with patch.object(env, "step", side_effect=step), patch.object(population, "_finalize_episode", side_effect=finalize):
        with controlled_action_schedule(population.exploration, env, schedule_for((2, 5))):
            for _ in range(5):
                active = ~env.dones.clone()
                population.step_population(env)
                ledger += active.long()
    assert ledger.tolist() == [2, 5]
    if corruption == "repeated_completion":
        with pytest.raises(AssertionError, match="completion history"):
            assert population.exploration.survival_history == [2, 5], "completion history repeated a sticky terminal"
    else:
        with pytest.raises(AssertionError, match="eligible replay"):
            assert len(population.replay_buffer) == int(ledger.sum()), "eligible replay lost a terminal or admitted a ghost"


def test_real_truncation_done_corruption_fails_actual_loss_target(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="truncation target"):
        qualify_real_learner(tmp_path, mode="standard", sequence_length=1, double_dqn=True, ending="cap", corrupt_truncation=True)
