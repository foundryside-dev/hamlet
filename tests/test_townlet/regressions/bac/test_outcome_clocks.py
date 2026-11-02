"""C07 owned envelopes: real authored lanes, explicit identity, event-owned clocks."""

import copy
import importlib
import importlib.util
from dataclasses import FrozenInstanceError, replace

import pytest
import torch
import yaml

from tests.test_townlet.regressions.fixtures.episode_lanes import (
    UNEQUAL_ENDINGS,
    build_authored_population,
    controlled_action_schedule,
    copy_authored_config,
    observe_environment_steps,
)
from townlet.config.bac_options import RNDOptions
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.training.replay_contract import ReplayRequest

CLOCKS = (
    "vector_ticks",
    "eligible_transitions",
    "optimizer_updates",
    "completed_batch_episodes",
    "predictor_admitted_rows",
    "predictor_consumed_minibatches",
    "predictor_dropped_rows",
)
WORLDS = ("world-cedar", "world-elm")  # Explicit caller-owned world-instance names.


def _population(tmp_path, *, learning=False):
    config = copy_authored_config(tmp_path / "pack", lifespan=10, num_agents=2)
    if learning:
        path = config / "levels/L0_test/training.yaml"
        data = yaml.safe_load(path.read_text())
        training = data["training"]
        training["replay_buffer"].update(batch_size=2, min_size=10)
        training["training_loop"]["train_frequency"] = 2
        training["q_learning"]["target_update_frequency"] = 2
        path.write_text(yaml.safe_dump(data, sort_keys=False))
    pop = build_authored_population(config, num_agents=2, exploration=EpsilonGreedyExploration(0.0, 1.0, 0.0))
    # Run real fixture/physics/replay prerequisites BEFORE any missing-feature assertion.
    with controlled_action_schedule(pop.exploration, pop.env, UNEQUAL_ENDINGS):
        states = [pop.step_population(pop.env) for _ in UNEQUAL_ENDINGS]
    assert pop.episode_step_counts.tolist() == [2, 5]
    assert sum(len(state.info["episode_completions"]) for state in states) == 2
    assert [item.reason for item in pop.episode_completions] == ["authored_terminal"] * 2
    assert pop.replay_buffer.retained_transitions == 7
    return pop


def _owned_api(pop):
    episode = importlib.import_module("townlet.training.episode")
    assert hasattr(episode, "LaneOutcome"), "C07 owned LaneOutcome interface missing"
    assert importlib.util.find_spec("townlet.training.clock_ledger") is not None, "C07 ClockLedger module missing"
    ledger = importlib.import_module("townlet.training.clock_ledger")
    assert hasattr(ledger, "ClockLedger"), "C07 ClockLedger type missing"
    for name in ("bind_episode_worlds", "begin_batch_episode", "commit_episode_outcomes"):
        assert callable(getattr(pop, name, None)), f"C07 population {name} interface missing"
    assert isinstance(getattr(pop, "clock_ledger", None), ledger.ClockLedger), "C07 population-owned ledger missing"
    assert isinstance(getattr(pop, "completed_outcomes", None), tuple), "C07 immutable outcome tuple missing"
    return episode.LaneOutcome


def _clocks(pop):
    return tuple(getattr(pop.clock_ledger, name) for name in CLOCKS)


def _begin(pop, *, batch, worlds, sequences):
    pop.bind_episode_worlds(world_ids=worlds, world_episode_seqs=sequences)
    pop.begin_batch_episode(index=batch, planned_horizon=10)
    pop.reset()  # The helper's initial empty reset is outside the measured episodes.


def _entropy(values):
    probabilities = torch.softmax(values, dim=-1)
    return -(probabilities * torch.log(probabilities + 1e-10)).sum(dim=-1) / torch.log(
        torch.tensor(values.shape[-1], dtype=torch.float32, device=values.device)
    )


def _snapshot(event):
    return (
        event.world_id,
        event.world_episode_seq,
        event.batch_episode,
        event.planned_horizon,
        event.reward_total,
        event.reward_extrinsic,
        event.reward_intrinsic,
        event.reward_shaping,
        event.policy_entropy,
        event.outcome.agent_idx,
        event.outcome.reason,
        event.outcome.survival_time,
        event.outcome.final_observation.clone(),
        event.outcome.final_meters.clone(),
    )


def _unchanged(event, expected):
    actual = _snapshot(event)
    assert actual[:-2] == expected[:-2]
    assert torch.equal(actual[-2], expected[-2])
    assert torch.equal(actual[-1], expected[-1])


@pytest.mark.parametrize("reverse", [False, True])
def test_lengths2_5_owned_events_and_clock_units(tmp_path, reverse):
    pop = _population(tmp_path)
    outcome_type = _owned_api(pop)
    schedule = tuple(tuple(reversed(row)) if reverse else row for row in UNEQUAL_ENDINGS)
    worlds = tuple(reversed(WORLDS)) if reverse else WORLDS
    retained = []
    for batch, declared in ((9, {WORLDS[0]: 17, WORLDS[1]: 83}), (42, {WORLDS[0]: 18, WORLDS[1]: 84})):
        before = _clocks(pop)
        _begin(pop, batch=batch, worlds=worlds, sequences=tuple(declared[world] for world in worlds))
        for event, frozen in retained:
            _unchanged(event, frozen)
        totals = torch.zeros((2, 4), dtype=torch.float64)
        last_entropy = torch.empty(2)
        published = []
        with observe_environment_steps(pop.env) as ticks, controlled_action_schedule(pop.exploration, pop.env, schedule):
            for row in schedule:
                state = pop.step_population(pop.env)
                tick = ticks[-1]
                active = tick.active_before
                parts = tick.info["reward_components"]
                values = torch.stack((tick.rewards, parts["extrinsic"], parts["intrinsic"], parts["shaping"]), dim=1)
                totals[active] += values[active].double()
                last_entropy[active] = _entropy(pop.last_selected_q_values)[active].cpu()
                events = pop.completed_outcomes
                assert len(events) == len(published) + len(state.info["episode_completions"])
                for event in events[len(published) :]:
                    assert isinstance(event, outcome_type)
                    lane = event.outcome.agent_idx
                    assert (event.world_id, event.world_episode_seq) == (worlds[lane], declared[worlds[lane]])
                    assert (event.batch_episode, event.planned_horizon) == (batch, 10)
                    assert event.outcome.reason == "authored_terminal"
                    assert event.outcome.survival_time == (2 if event.world_id == WORLDS[0] else 5)
                    assert (event.reward_total, event.reward_extrinsic, event.reward_intrinsic, event.reward_shaping) == pytest.approx(
                        totals[lane].tolist()
                    )
                    assert event.policy_entropy == pytest.approx(last_entropy[lane].item())
                    assert torch.equal(event.outcome.final_observation, state.observations[lane].cpu())
                    assert torch.equal(event.outcome.final_meters, pop.env.meters[lane].cpu())
                    assert event.outcome.final_observation.data_ptr() != pop.current_obs[lane].data_ptr()
                    retained.append((event, _snapshot(event)))
                    published.append(event)
                for event, frozen in retained:
                    _unchanged(event, frozen)
        assert len(published) == 2
        assert pop.total_steps == pop.clock_ledger.vector_ticks
        assert tuple(now - old for now, old in zip(_clocks(pop), before)) == (5, 7, 0, 0, 0, 0, 0)
        pop.commit_episode_outcomes(tuple(published))
        committed = _clocks(pop)
        assert committed[3] == before[3] + 1  # Batch commitment is distinct from two lane events.
        pop.commit_episode_outcomes(tuple(reversed(published)))
        assert _clocks(pop) == committed
        assert all(pop.flush_episode(lane, "checkpoint") is None for lane in range(2))
        with pytest.raises(FrozenInstanceError):
            published[0].reward_total = -999.0
        with pytest.raises(FrozenInstanceError):
            published[0].outcome.reason = "shutdown"


@pytest.mark.parametrize("reason", ["cap", "budget", "shutdown", "checkpoint"])
def test_external_cuts_keep_owned_reason_and_nonterminal_successor(tmp_path, reason):
    pop = _population(tmp_path)
    _owned_api(pop)
    _begin(pop, batch=31, worlds=WORLDS, sequences=(107, 204))
    with controlled_action_schedule(pop.exploration, pop.env, (("WAIT", "WAIT"),) * 2):
        pop.step_population(pop.env)
        state = pop.step_population(pop.env)
    assert not state.dones.any()
    assert state.info["successor_action_masks"].any(dim=1).all()
    for lane in range(2):
        completion = pop.flush_episode(lane, reason)
        assert completion.reason == reason
        assert completion.survival_time == 2
        assert pop.flush_episode(lane, reason) is None
    assert len(pop.completed_outcomes) == 2
    assert all(event.outcome.reason == reason for event in pop.completed_outcomes)
    # Sampling all real rows independently checks that flush did not forge done=True.
    batch = pop.replay_buffer.sample_batch(
        ReplayRequest(pop.replay_buffer.retained_transitions, 1, 0, "uniform_without_replacement", "feedforward", "transition")
    )
    assert batch.dones.sum().item() == 2  # Only the two prerequisite authored deaths.
    for lane in range(2):
        matching = (batch.next_observations == state.observations[lane]).all(dim=-1) & ~batch.dones
        assert matching.any()
        assert (batch.next_action_masks[matching] == state.info["successor_action_masks"][lane]).all()
    frozen = [(event, _snapshot(event)) for event in pop.completed_outcomes]
    pop.commit_episode_outcomes(pop.completed_outcomes)
    _begin(pop, batch=91, worlds=WORLDS, sequences=(108, 205))
    for event, expected in frozen:
        _unchanged(event, expected)


def test_owned_binding_requires_concrete_fresh_caller_identity(tmp_path):
    pop = _population(tmp_path)
    outcome_type = _owned_api(pop)
    before = _clocks(pop)
    with pytest.raises((ValueError, RuntimeError)):
        pop.begin_batch_episode(index=3, planned_horizon=10)
    for ids, sequences in (
        (WORLDS, (None, 8)),
        ((None, WORLDS[1]), (7, 8)),
        (("", WORLDS[1]), (7, 8)),
        ((WORLDS[0], WORLDS[0]), (7, 8)),
        (WORLDS, (True, 8)),
        (WORLDS, (-1, 8)),
        (WORLDS[:1], (7,)),
    ):
        with pytest.raises((TypeError, ValueError)):
            pop.bind_episode_worlds(world_ids=ids, world_episode_seqs=sequences)
        assert _clocks(pop) == before
    _begin(pop, batch=3, worlds=WORLDS, sequences=(7, 80))
    with controlled_action_schedule(pop.exploration, pop.env, (("WAIT", "WAIT"),)):
        pop.step_population(pop.env)
    for lane in range(2):
        pop.flush_episode(lane, "cap")
    event = pop.completed_outcomes[0]
    assert isinstance(event, outcome_type)
    for changes in ({"world_id": None}, {"world_id": ""}, {"world_episode_seq": None}, {"world_episode_seq": True}):
        with pytest.raises((TypeError, ValueError)):
            replace(event, **changes)
    pop.commit_episode_outcomes(pop.completed_outcomes)
    with pytest.raises((ValueError, RuntimeError)):
        pop.begin_batch_episode(index=4, planned_horizon=10)  # No implicit world sequence from batch/tick/row.


@pytest.mark.parametrize("overflow", ["service_before_admit", "drop_newest"])
def test_receipts_and_unequal_train_target_lr_clocks(tmp_path, monkeypatch, overflow):
    pop = _population(tmp_path, learning=True)
    _owned_api(pop)
    adaptive = AdaptiveIntrinsicExploration(
        obs_dim=pop.env.observation_dim, rnd_training_batch_size=1, rnd_learning_rate=1e-3, device=pop.device
    )
    rnd = adaptive.rnd
    rnd.configure_service(RNDOptions(service_mode="paced_fifo", max_updates_per_tick=1, max_pending_rows=1, overflow_policy=overflow))
    pop.exploration = adaptive
    pop.env.set_exploration_module(adaptive)
    pop.sync_exploration_metrics()
    pop.scheduler = torch.optim.lr_scheduler.StepLR(pop.optimizer, step_size=1, gamma=0.5)
    initial_lr = pop.optimizer.param_groups[0]["lr"]
    initial_predictor = copy.deepcopy(rnd.predictor_network.state_dict())
    receipts, attempts, updates, targets, completions = [], [], [], [], []
    service, learn = rnd.admit_and_service, pop._learn
    optimizer_step, target_load = pop.optimizer.step, pop.target_network.load_state_dict
    adaptive_end = adaptive.update_on_episode_end

    def service_spy(observations, *, vector_tick):
        receipt = service(observations, vector_tick=vector_tick)
        receipts.append((observations.detach().clone(), vector_tick, receipt))
        return receipt

    def learn_spy():
        attempts.append(pop.total_steps)
        return learn()

    def optimizer_spy(*args, **kwargs):
        result = optimizer_step(*args, **kwargs)
        updates.append(pop.total_steps)
        return result

    def target_spy(*args, **kwargs):
        result = target_load(*args, **kwargs)
        targets.append(pop.total_steps)
        return result

    def completion_spy(*, survival_time):
        completions.append(survival_time)
        return adaptive_end(survival_time=survival_time)

    monkeypatch.setattr(rnd, "admit_and_service", service_spy)
    monkeypatch.setattr(pop, "_learn", learn_spy)
    monkeypatch.setattr(pop.optimizer, "step", optimizer_spy)
    monkeypatch.setattr(pop.target_network, "load_state_dict", target_spy)
    monkeypatch.setattr(adaptive, "update_on_episode_end", completion_spy)
    before = _clocks(pop)
    _begin(pop, batch=57, worlds=WORLDS, sequences=(300, 701))
    predecessors = []
    with controlled_action_schedule(adaptive, pop.env, UNEQUAL_ENDINGS):
        for row in UNEQUAL_ENDINGS:
            predecessors.append(pop.current_obs[~pop.env.dones].clone())
            pop.step_population(pop.env)
    assert len(receipts) == 5, "POP must consume the real configured row-service receipt on each vector tick"
    assert all(torch.equal(rows, expected) for (rows, _, _), expected in zip(receipts, predecessors))
    assert [tick for _, tick, _ in receipts] == list(range(6, 11))  # Accepted step's vector tick.
    actual = [receipt for _, _, receipt in receipts]
    delta = tuple(now - old for now, old in zip(_clocks(pop), before))
    assert delta[:4] == (5, 7, 2, 0)
    assert delta[4:] == (
        sum(r.admitted_rows for r in actual),
        sum(r.optimizer_updates for r in actual),
        sum(r.dropped_rows for r in actual),
    )
    assert delta[4] == 7
    assert sum(r.consumed_rows for r in actual) + delta[6] + actual[-1].pending_rows == 7
    if overflow == "service_before_admit":
        assert sum(r.overflow_optimizer_updates for r in actual) > 0
    else:
        assert delta[6] > 0
    assert any(not torch.equal(value, initial_predictor[key]) for key, value in rnd.predictor_network.state_dict().items())
    assert attempts == [6, 8, 10] and updates == [8, 10] and targets == [10]
    assert pop.training_step_counter == 2
    assert pop.scheduler.last_epoch == 2
    assert pop.optimizer.param_groups[0]["lr"] == pytest.approx(initial_lr * 0.25)
    assert completions == [2, 5]
    pop.commit_episode_outcomes(pop.completed_outcomes)
    pop.commit_episode_outcomes(pop.completed_outcomes)
    assert pop.clock_ledger.completed_batch_episodes == before[3] + 1
    assert completions == [2, 5] and adaptive.survival_history == [2, 5]


def test_legacy_direct_predictor_still_services_one_minibatch(tmp_path):
    pop = _population(tmp_path)
    adaptive = AdaptiveIntrinsicExploration(obs_dim=pop.env.observation_dim, rnd_training_batch_size=1, device=pop.device)
    rnd = adaptive.rnd
    rnd.obs_buffer.extend(row.detach().cpu().clone() for row in pop.current_obs)
    rnd.update_predictor()
    assert len(rnd.obs_buffer) == 1
    assert torch.equal(rnd.obs_buffer[0], pop.current_obs[1].cpu())


def _cut_owned(pop, *, batch=71):
    _begin(pop, batch=batch, worlds=WORLDS, sequences=(501, 907))
    with controlled_action_schedule(pop.exploration, pop.env, (("WAIT", "WAIT"),) * 2):
        pop.step_population(pop.env)
        pop.step_population(pop.env)
    for lane in range(2):
        assert pop.flush_episode(lane, "checkpoint") is not None
    assert len(pop.completed_outcomes) == 2
    return pop.completed_outcomes


@pytest.mark.parametrize("field", ["final_observation", "final_meters", "reward_total"])
@pytest.mark.parametrize("already_committed", [False, True])
def test_exposed_event_mutation_cannot_rewrite_publication_authority(tmp_path, field, already_committed):
    pop = _population(tmp_path)
    _owned_api(pop)
    returned = _cut_owned(pop)
    originals = tuple(replace(event) for event in returned)
    expected = _snapshot(originals[0])
    before = _clocks(pop)
    if already_committed:
        pop.commit_episode_outcomes(originals)
    committed = _clocks(pop)
    if field == "reward_total":
        changed = replace(returned[0], reward_total=returned[0].reward_total + 0.25)
    else:
        getattr(returned[0].outcome, field).add_(0.25)
        changed = returned[0]
    _unchanged(pop.completed_outcomes[0], expected)  # Another sink must see publication-time bytes.
    _unchanged(originals[0], expected)
    with pytest.raises(ValueError, match="content"):
        pop.commit_episode_outcomes((changed,))
    assert _clocks(pop) == committed
    pop.commit_episode_outcomes(originals)
    pop.commit_episode_outcomes(tuple(reversed(originals)))
    assert pop.clock_ledger.completed_batch_episodes == before[3] + 1
    _unchanged(pop.completed_outcomes[0], expected)


@pytest.mark.parametrize("partial", [False, True])
def test_delayed_partial_commit_survives_reset_and_reordered_replay(tmp_path, partial):
    pop = _population(tmp_path)
    _owned_api(pop)
    adaptive = AdaptiveIntrinsicExploration(obs_dim=pop.env.observation_dim, rnd_training_batch_size=128, device=pop.device)
    pop.exploration = adaptive
    pop.env.set_exploration_module(adaptive)
    pop.sync_exploration_metrics()
    originals = tuple(replace(event) for event in _cut_owned(pop))
    before = _clocks(pop)
    if partial:
        pop.commit_episode_outcomes(originals[:1])
    assert pop.clock_ledger.completed_batch_episodes == before[3]
    assert adaptive.survival_history == [2, 2]
    _begin(pop, batch=82, worlds=tuple(reversed(WORLDS)), sequences=(908, 502))
    assert pop.completed_outcomes == ()
    pop.commit_episode_outcomes(originals[1:] if partial else originals)
    pop.commit_episode_outcomes(tuple(reversed(originals)))
    assert pop.clock_ledger.completed_batch_episodes == before[3] + 1
    assert adaptive.survival_history == [2, 2]  # Commitment/reset never replays adaptive death.
    changed_old = replace(originals[0], reward_total=originals[0].reward_total + 1.0)
    unchanged = _clocks(pop)
    with pytest.raises(ValueError, match="content"):
        pop.commit_episode_outcomes((changed_old,))
    assert _clocks(pop) == unchanged
    with controlled_action_schedule(adaptive, pop.env, (("WAIT", "WAIT"),)):
        pop.step_population(pop.env)
    for lane in range(2):
        pop.flush_episode(lane, "cap")
    pop.commit_episode_outcomes(pop.completed_outcomes)
    assert pop.clock_ledger.completed_batch_episodes == before[3] + 2
    assert adaptive.survival_history == [2, 2, 1, 1]


def test_duplicate_begin_ordinary_reset_and_historical_ledger_accessor(tmp_path):
    pop = _population(tmp_path)
    _owned_api(pop)
    originals = tuple(replace(event) for event in _cut_owned(pop))
    pop.commit_episode_outcomes(originals)
    old_reading = pop.clock_ledger
    pop.reset()  # Accepted ordinary reset must retain the legacy DTO-only API.
    with controlled_action_schedule(pop.exploration, pop.env, (("WAIT", "WAIT"),)):
        pop.step_population(pop.env)
    for lane in range(2):
        assert pop.flush_episode(lane, "cap").survival_time == 1
    assert pop.completed_outcomes == ()
    assert pop.clock_ledger.vector_ticks == old_reading.vector_ticks + 1
    assert old_reading.vector_ticks == 7  # Held immutable reading did not advance.
    pop.bind_episode_worlds(world_ids=WORLDS, world_episode_seqs=(502, 908))
    before = _clocks(pop)
    with pytest.raises(ValueError, match="reused"):
        pop.begin_batch_episode(index=71, planned_horizon=10)
    assert _clocks(pop) == before
    pop.commit_episode_outcomes(tuple(reversed(originals)))
    checkpoint = pop.get_checkpoint_state()
    pop.load_checkpoint_state(checkpoint)
    with pytest.raises(RuntimeError, match="ledger"):
        _ = pop.clock_ledger  # Historical payload has no complete ledger; unknown units are not zeros.


def test_population_unconfigured_predictor_counts_short_tail_and_real_updates(tmp_path, monkeypatch):
    pop = _population(tmp_path)
    _owned_api(pop)
    adaptive = AdaptiveIntrinsicExploration(obs_dim=pop.env.observation_dim, rnd_training_batch_size=3, device=pop.device)
    rnd = adaptive.rnd
    pop.exploration = adaptive
    pop.env.set_exploration_module(adaptive)
    pop.sync_exploration_metrics()
    readings = []
    counters = rnd.predictor_service_counters
    initial = copy.deepcopy(rnd.predictor_network.state_dict())

    def read_counters():
        reading = counters()
        readings.append(reading)
        return reading

    def bounded_service(*args, **kwargs):
        pytest.fail("The unconfigured POP path must retain its direct one-minibatch service")

    monkeypatch.setattr(rnd, "predictor_service_counters", read_counters)
    monkeypatch.setattr(rnd, "admit_and_service", bounded_service)
    _begin(pop, batch=63, worlds=WORLDS, sequences=(601, 1009))
    before = _clocks(pop)
    expected = ((1, 2, 0, 0, 2, 0, 0), (2, 4, 0, 0, 4, 1, 0), (3, 6, 0, 0, 6, 2, 0))
    with controlled_action_schedule(adaptive, pop.env, (("WAIT", "WAIT"),) * 3):
        for tick in range(3):
            pop.step_population(pop.env)
            assert tuple(now - old for now, old in zip(_clocks(pop), before)) == expected[tick]
    assert len(readings) == 6  # Pure before/after view brackets append plus actual direct service.
    assert [reading.optimizer_updates for reading in readings] == [0, 0, 0, 1, 1, 2]
    assert [reading.pending_rows for reading in readings] == [0, 2, 2, 1, 1, 0]
    assert any(not torch.equal(value, initial[key]) for key, value in rnd.predictor_network.state_dict().items())
    for lane in range(2):
        pop.flush_episode(lane, "cap")
    assert adaptive.survival_history == [3, 3]


def _singleton_population(tmp_path):
    # Supplier-authored candidate DATA; actual compilation/geometry is a prerequisite, never an entropy RED.
    config = copy_authored_config(tmp_path / "singleton", lifespan=10, num_agents=1)
    (config / "actions.yaml").write_text(
        "actions:\n"
        "  version: '1.0'\n"
        "  substrate_actions:\n"
        "    inherit: false\n"
        "  custom_actions:\n"
        "  - name: WAIT\n"
        "    description: Do nothing (pass turn)\n"
        "    enabled_by_default: true\n"
        "  labels:\n"
        "    preset: gaming\n"
    )
    path = config / "levels/L0_test/training.yaml"
    data = yaml.safe_load(path.read_text())
    data["training"]["enabled_actions"]["custom"] = []
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    pop = build_authored_population(config, num_agents=1, exploration=EpsilonGreedyExploration(0.0, 1.0, 0.0))
    assert pop.action_dim == pop.env.action_dim == 1, "Singleton fixture prerequisite: actual emitted action width must be1"
    assert set(pop.env.action_ids) == {"WAIT"}, "Singleton fixture prerequisite: actual vocabulary must contain only WAIT"
    masks = pop.env.get_action_masks()
    assert masks.shape == (1, 1) and masks.all(), "Singleton fixture prerequisite: actual WAIT successor geometry must be legal"
    _owned_api(pop)
    _begin(pop, batch=29, worlds=("world-singleton-orchid",), sequences=(1501,))
    return pop


def test_actual_singleton_tick_and_owned_entropy_are_finite_zero(tmp_path):
    pop = _singleton_population(tmp_path)
    before = _clocks(pop)
    with observe_environment_steps(pop.env) as ticks, controlled_action_schedule(pop.exploration, pop.env, (("WAIT",),)):
        state = pop.step_population(pop.env)
    assert len(ticks) == 1
    assert pop.last_selected_q_values.shape == (1, 1)
    assert torch.isfinite(pop.last_selected_q_values).all()
    assert pop.episode_step_counts.tolist() == [1]
    assert not state.dones.any()
    assert state.info["successor_action_masks"].shape == (1, 1)
    pop.flush_episode(0, "checkpoint")
    assert len(pop.completed_outcomes) == 1
    event = pop.completed_outcomes[0]
    assert torch.isfinite(torch.tensor(event.policy_entropy))
    assert event.policy_entropy == 0.0
    assert tuple(now - old for now, old in zip(_clocks(pop), before))[:4] == (1, 1, 0, 0)


@pytest.mark.parametrize("invalid_q", [float("nan"), float("inf"), -float("inf")])
def test_singleton_nonfinite_q_refuses_before_physics(tmp_path, monkeypatch, invalid_q):
    pop = _singleton_population(tmp_path)
    before = _clocks(pop)
    called = []
    step = pop.env.step

    def physics_spy(*args, **kwargs):
        called.append(True)
        return step(*args, **kwargs)

    def invalid_rollout(eligible):
        return torch.full((pop.num_agents, pop.action_dim), invalid_q, device=pop.device)

    monkeypatch.setattr(pop.env, "step", physics_spy)
    monkeypatch.setattr(pop, "_rollout_q", invalid_rollout)
    with pytest.raises(ValueError, match="finite"):
        pop.step_population(pop.env)
    assert called == []
    assert _clocks(pop) == before
    assert pop.episode_step_counts.tolist() == [0]
    assert pop.completed_outcomes == ()
