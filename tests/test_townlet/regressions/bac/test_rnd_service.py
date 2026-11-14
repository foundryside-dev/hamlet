"""Bounded FIFO service, real predictor updates and transactional continuation."""

import copy

import pytest
import torch

from townlet.config.bac_options import RNDOptions
from townlet.exploration.rnd import RNDExploration


def provider(batch, capacity, mode, overflow):
    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=batch)
    assert hasattr(rnd, "configure_service"), "bounded RND service interface missing"
    rnd.configure_service(RNDOptions(service_mode=mode, max_updates_per_tick=1, max_pending_rows=capacity, overflow_policy=overflow))
    return rnd


def rows(count):
    return torch.arange(count * 2, dtype=torch.float32).reshape(count, 2) / 10


def equal(left, right):
    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            equal(a, b)
    else:
        assert left == right


def test_occupancy512_consumes_four_batches():
    rnd = provider(128, 128, "occupancy_fifo", "service_before_admit")
    before = copy.deepcopy(rnd.predictor_network.state_dict())
    target = copy.deepcopy(rnd.fixed_network.state_dict())
    receipt = rnd.admit_and_service(rows(512), vector_tick=0)
    assert (receipt.admitted_rows, receipt.consumed_rows, receipt.pending_rows, receipt.optimizer_updates) == (512, 512, 0, 4)
    assert receipt.dropped_rows == 0
    assert receipt.last_loss > 0
    assert any(not torch.equal(before[key], value) for key, value in rnd.predictor_network.state_dict().items())
    equal(target, rnd.fixed_network.state_dict())
    assert all(not parameter.requires_grad for parameter in rnd.fixed_network.parameters())


def test_seven_rows_fifo_tail_and_normalizer_are_distinct():
    rnd = provider(3, 3, "occupancy_fifo", "service_before_admit")
    seen = []
    handle = rnd.predictor_network.register_forward_pre_hook(lambda _, args: seen.append(args[0].clone()))
    values = rows(7)
    receipt = rnd.admit_and_service(values, vector_tick=10)
    handle.remove()
    equal(torch.cat(seen), values[:6])
    equal(torch.stack(rnd.obs_buffer), values[6:])
    assert (receipt.admitted_rows, receipt.consumed_rows, receipt.pending_rows) == (7, 6, 1)
    assert rnd.reward_rms.count == 1e-4
    novelty = rnd.compute_intrinsic_rewards(values[:2], update_stats=True)
    assert rnd.reward_rms.count == 2.0001
    assert torch.count_nonzero(novelty * 0.0) == 0
    assert torch.all(novelty > 0)
    values.fill_(99)
    equal(torch.stack(rnd.obs_buffer), rows(7)[6:])


@pytest.mark.parametrize("policy", ["service_before_admit", "drop_oldest", "drop_newest"])
def test_paced_retention_is_bounded(policy):
    rnd = provider(128, 256, "paced_fifo", policy)
    for tick in range(3):
        result = rnd.admit_and_service(rows(512), vector_tick=tick)
        assert result.pending_rows <= 256
        assert result.paced_optimizer_updates <= 1
        assert result.optimizer_updates == result.paced_optimizer_updates + result.overflow_optimizer_updates
        if policy == "service_before_admit":
            assert result.dropped_rows == 0
            assert result.overflow_optimizer_updates > 0
        else:
            assert result.dropped_rows > 0
            assert result.overflow_optimizer_updates == 0
        state = rnd.checkpoint_state()["predictor_service"]
        assert state["admitted_rows"] == state["consumed_rows"] + state["dropped_rows"] + result.pending_rows


@pytest.mark.parametrize(
    "policy,expected,dropped", [("service_before_admit", [6], 0), ("drop_oldest", [4, 5, 6], 1), ("drop_newest", [3, 4, 5], 1)]
)
def test_oversized_fifo_policy_retains_exact_rows(policy, expected, dropped):
    rnd = provider(3, 3, "paced_fifo", policy)
    result = rnd.admit_and_service(rows(7), vector_tick=0)
    equal(torch.stack(rnd.obs_buffer), rows(7)[expected])
    assert result.dropped_rows == dropped
    assert result.admitted_rows == 7
    assert result.paced_optimizer_updates == 1


def test_same_tick_does_not_reset_paced_budget():
    rnd = provider(3, 9, "paced_fifo", "service_before_admit")
    assert rnd.admit_and_service(rows(3), vector_tick=4).optimizer_updates == 1
    assert rnd.admit_and_service(rows(3), vector_tick=4).optimizer_updates == 0
    assert rnd.admit_and_service(rows(0), vector_tick=5).optimizer_updates == 1
    before = rnd.checkpoint_state()
    with pytest.raises(ValueError):
        rnd.admit_and_service(rows(1), vector_tick=3)
    equal(before, rnd.checkpoint_state())


def test_two_of_three_tail_resume():
    uninterrupted = provider(3, 6, "paced_fifo", "service_before_admit")
    uninterrupted.compute_intrinsic_rewards(rows(2), update_stats=True)
    uninterrupted.admit_and_service(rows(2), vector_tick=2)
    state = uninterrupted.checkpoint_state()
    resumed = provider(3, 6, "paced_fifo", "service_before_admit")
    resumed.load_state(state)
    equal(state, resumed.checkpoint_state())
    a = uninterrupted.admit_and_service(rows(3)[2:], vector_tick=3)
    b = resumed.admit_and_service(rows(3)[2:], vector_tick=3)
    assert a == b
    assert a.optimizer_updates == 1
    equal(uninterrupted.checkpoint_state(), resumed.checkpoint_state())
    # Checkpoints own their tensors; a later optimizer step cannot rewrite a saved state.
    assert state["predictor_service"]["pending_observations"].shape == (2, 2)
    assert any(not torch.equal(state["predictor_network"][k], v) for k, v in resumed.predictor_network.state_dict().items())


@pytest.mark.parametrize("damage", ["tail_shape", "tail_nan", "capacity", "policy", "count", "clock", "normalizer", "network", "optimizer"])
def test_malformed_state_is_atomic(damage):
    rnd = provider(3, 6, "paced_fifo", "service_before_admit")
    rnd.admit_and_service(rows(5), vector_tick=2)
    before = rnd.checkpoint_state()
    bad = copy.deepcopy(before)
    service = bad["predictor_service"]
    if damage == "tail_shape":
        service["pending_observations"] = torch.ones(2, 3)
    elif damage == "tail_nan":
        service["pending_observations"][0, 0] = float("nan")
    elif damage == "capacity":
        service["options"]["max_pending_rows"] = 2
    elif damage == "policy":
        service["options"]["overflow_policy"] = "drop_oldest"
    elif damage == "count":
        service["admitted_rows"] += 1
    elif damage == "clock":
        service["ordinary_updates_at_position"] = 2
    elif damage == "normalizer":
        bad["reward_rms_var"] = -1
    elif damage == "network":
        next(iter(bad["predictor_network"].values())).fill_(float("inf"))
    else:
        next(iter(bad["optimizer"]["state"].values()))["exp_avg"] = torch.ones(1)
    with pytest.raises((ValueError, RuntimeError)):
        rnd.load_state(bad)
    equal(before, rnd.checkpoint_state())


def test_service_options_are_explicit_and_buffer_admission_validated():
    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
    assert hasattr(rnd, "configure_service"), "bounded RND service interface missing"
    with pytest.raises(ValueError):
        rnd.configure_service(RNDOptions(service_mode="paced_fifo"))
    with pytest.raises(ValueError):
        rnd.admit_and_service(rows(1), vector_tick=0)
    rnd = provider(3, 3, "paced_fifo", "drop_newest")
    for bad in (torch.ones(2, 3), torch.full((1, 2), float("nan")), torch.ones(1, 2, dtype=torch.int64)):
        before = rnd.checkpoint_state()
        with pytest.raises(ValueError):
            rnd.admit_and_service(bad, vector_tick=0)
        equal(before, rnd.checkpoint_state())


def test_direct_minibatch_and_current_native_state_refuse_diagnostic_import():
    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
    rnd.update({"observations": rows(7)})
    assert len(rnd.obs_buffer) == 4  # Preserve current one-minibatch direct update API.
    assert rnd.update_predictor() > 0
    assert len(rnd.obs_buffer) == 1
    assert hasattr(rnd, "available_state"), "explicit available-state export missing"
    diagnostic = rnd.available_state()
    assert "predictor_service" not in diagnostic
    restored = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
    assert not hasattr(restored, "load_available_state")
    for current in (rnd, restored):
        before = current.checkpoint_state()
        for operation in (current.validate_state, current.prepare_state, current.load_state):
            with pytest.raises(ValueError):
                operation(diagnostic)
            equal(before, current.checkpoint_state())
    native = rnd.checkpoint_state()
    assert native["schema"] == "rnd-state-v4"
    assert native["predictor_service"]["version"] == 3
    assert native["predictor_service"]["optimizer_epoch_origin"] == 0
    assert native["predictor_service"]["service_clock_unit"] == "vector_tick"
    restored.load_state(native)
    equal(native, restored.checkpoint_state())
    equal(diagnostic, restored.available_state())
    equal(torch.stack(restored.obs_buffer), rows(7)[6:])
    for current in (rnd, restored):
        current.update({"observations": rows(2)})
    equal(rnd.checkpoint_state(), restored.checkpoint_state())
    with pytest.raises(ValueError):
        restored.load_state({**native, "misspelled_service": {}})


def test_invalid_minibatch_refuses_before_allocation():
    for batch in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=batch)


@pytest.mark.parametrize("damage", ["negative_moment", "orphan_moment", "fractional_batch", "false_clock_count"])
def test_corrupt_optimizer_and_service_metadata_are_atomic(damage):
    rnd = provider(3, 6, "paced_fifo", "service_before_admit")
    rnd.admit_and_service(rows(5), vector_tick=2)
    before = rnd.checkpoint_state()
    bad = copy.deepcopy(before)
    if damage == "negative_moment":
        next(iter(bad["optimizer"]["state"].values()))["exp_avg_sq"].fill_(-1)
    elif damage == "orphan_moment":
        bad["optimizer"]["state"][999] = copy.deepcopy(next(iter(bad["optimizer"]["state"].values())))
    elif damage == "fractional_batch":
        bad["predictor_service"]["training_batch_size"] = 3.0
    else:
        bad["predictor_service"]["ordinary_updates_at_position"] = 1
        bad["predictor_service"]["optimizer_updates"] = 0
        bad["predictor_service"]["consumed_rows"] = 0
        bad["predictor_service"]["admitted_rows"] = 2
        bad["predictor_service"]["service_position"] = 2
    with pytest.raises(ValueError):
        rnd.load_state(bad)
    equal(before, rnd.checkpoint_state())


def test_paced_budget_survives_resume_and_service_instances_are_private():
    first = provider(3, 6, "paced_fifo", "service_before_admit")
    first.admit_and_service(rows(6), vector_tick=4)
    second = provider(3, 6, "paced_fifo", "service_before_admit")
    rng = torch.get_rng_state().clone()
    second.load_state(first.checkpoint_state())
    equal(rng, torch.get_rng_state())
    assert second.admit_and_service(rows(0), vector_tick=4).optimizer_updates == 0
    before = first.checkpoint_state()
    assert second.admit_and_service(rows(0), vector_tick=5).optimizer_updates == 1
    equal(before, first.checkpoint_state())


def test_checkpoint_validation_does_not_install_valid_foreign_state():
    source = provider(3, 6, "paced_fifo", "service_before_admit")
    source.admit_and_service(rows(5), vector_tick=2)
    destination = provider(3, 6, "paced_fifo", "service_before_admit")
    assert hasattr(destination, "validate_state"), "consumer checkpoint validation interface missing"
    before = destination.checkpoint_state()
    destination.validate_state(source.checkpoint_state())
    equal(before, destination.checkpoint_state())


def test_configured_direct_operation_is_one_batch_and_update_adapter_advances_clock():
    rnd = provider(3, 9, "paced_fifo", "service_before_admit")
    rnd.admit_and_service(rows(9), vector_tick=4)
    assert len(rnd.obs_buffer) == 6
    assert rnd.update_predictor() > 0
    assert len(rnd.obs_buffer) == 3
    rnd.update({"observations": rows(0)})
    assert len(rnd.obs_buffer) == 0


def test_native_runner_checkpoint_retains_tail_and_rejects_corruption(tmp_path):
    import hashlib
    import shutil
    from pathlib import Path

    import yaml

    from townlet.config.world_roster import WorldRosterDeclaration
    from townlet.demo.runner import DemoRunner
    from townlet.training.checkpoint_utils import safe_torch_load

    root = Path(__file__).resolve().parents[4]
    pack = tmp_path / "pack"
    shutil.copytree(root / "configs/test/bac_remediation/feedforward", pack, ignore=shutil.ignore_patterns(".compiled"))
    training_path = pack / "levels/L0_0_minimal/training.yaml"
    doc = yaml.safe_load(training_path.read_text())
    training = doc["training"]
    training["population"]["size"] = 2
    training["replay_buffer"].update(capacity=64, batch_size=5, min_size=5)
    training["training_loop"].update(max_episodes=2, max_steps_per_episode=3, train_frequency=1)
    training["training_loop"]["checkpointing"]["interval"] = 1
    training["bac_options"]["rnd"]["max_pending_rows"] = 6
    training_path.write_text(yaml.safe_dump(doc, sort_keys=False))
    world_roster = WorldRosterDeclaration(("native-world-A", "native-world-B"))
    with DemoRunner(
        config_dir=pack,
        db_path=tmp_path / "run.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=2,
        world_roster=world_roster,
        level_name="L0_0_minimal",
    ) as runner:
        runner.run()
        artifact = tmp_path / "checkpoints/checkpoint_ep00002.pt"
        digest = artifact.with_suffix(".pt.sha256")
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == digest.read_text().strip()
        payload = safe_torch_load(artifact, allow_unsafe_pickle=True)
        saved = payload["population_state"]
        state = saved["exploration_state"]["rnd_state"]
        service = state["predictor_service"]
        assert (service["admitted_rows"], service["consumed_rows"], service["optimizer_updates"]) == (12, 10, 2)
        assert service["pending_observations"].shape == (2, state["obs_dim"])
        population = runner.population
        assert population is not None
        before = copy.deepcopy(population.get_checkpoint_state())
        bad = copy.deepcopy(saved)
        next(iter(bad["q_network"].values())).fill_(99)
        bad["exploration_state"]["rnd_state"]["predictor_service"]["pending_observations"][0, 0] = float("nan")
        with pytest.raises(ValueError):
            population.load_checkpoint_state(bad)
        equal(before, population.get_checkpoint_state())
        for damage in ("missing", "empty", "reset_steps", "capturable"):
            bad = copy.deepcopy(saved)
            next(iter(bad["q_network"].values())).fill_(99)
            bad["total_steps"] += 10
            corrupt_optimizer(bad["exploration_state"]["rnd_state"], damage)
            for operation in (population.validate_checkpoint_state, population.load_checkpoint_state):
                with pytest.raises(ValueError):
                    operation(bad)
                equal(before, population.get_checkpoint_state())
        rnd = population.exploration.rnd
        next_rows = torch.linspace(0, 1, 3 * state["obs_dim"]).reshape(3, state["obs_dim"])
        rnd.update({"observations": next_rows})
        expected = rnd.checkpoint_state()
        assert runner.load_checkpoint() is not None
        rnd = population.exploration.rnd
        equal(state, rnd.checkpoint_state())
        rnd.update({"observations": next_rows})
        equal(expected, rnd.checkpoint_state())
    fresh_dir = tmp_path / "fresh-checkpoints"
    fresh_dir.mkdir()
    shutil.copy2(artifact, fresh_dir / artifact.name)
    shutil.copy2(digest, fresh_dir / digest.name)
    with DemoRunner(
        config_dir=pack,
        db_path=tmp_path / "fresh.db",
        checkpoint_dir=fresh_dir,
        max_episodes=payload["episode"],
        world_roster=world_roster,
        level_name="L0_0_minimal",
    ) as fresh:
        fresh.run()
        restored = fresh.population.exploration.rnd
        equal(state, restored.checkpoint_state())
        restored.update({"observations": next_rows})
        equal(expected, restored.checkpoint_state())


@pytest.mark.parametrize("mode,count", [("paced_fifo", 5), ("occupancy_fifo", 8)])
def test_configured_direct_buffer_api_retains_checkpointable_counters(mode, count):
    rnd = provider(3, 9, mode, "service_before_admit")
    rnd.obs_buffer.extend(rows(count).unbind())
    assert rnd.update_predictor() > 0
    assert len(rnd.obs_buffer) == count - 3
    saved = rnd.checkpoint_state()
    assert saved["predictor_service"]["admitted_rows"] == count
    restored = provider(3, 9, mode, "service_before_admit")
    restored.load_state(saved)
    equal(saved, restored.checkpoint_state())


def corrupt_optimizer(state, damage):
    optimizer = state["optimizer"]
    if damage == "missing":
        del optimizer["state"][next(iter(optimizer["state"]))]
    elif damage == "empty":
        optimizer["state"].clear()
    elif damage == "reset_steps":
        for moments in optimizer["state"].values():
            moments["step"].zero_()
    elif damage == "unknown_group_key":
        optimizer["param_groups"][0]["unknown_execution_flag"] = False
    elif damage == "wrong_flag_type":
        optimizer["param_groups"][0]["maximize"] = 1
    else:
        optimizer["param_groups"][0][damage] = True


@pytest.mark.parametrize("damage", ["missing", "empty", "reset_steps", "capturable", "unknown_group_key", "wrong_flag_type"])
def test_optimizer_continuation_refuses_corruption_before_install(damage):
    rnd = provider(3, 6, "occupancy_fifo", "service_before_admit")
    rnd.admit_and_service(rows(7), vector_tick=2)
    before = rnd.checkpoint_state()
    bad = copy.deepcopy(before)
    corrupt_optimizer(bad, damage)
    for operation in (rnd.validate_state, rnd.load_state):
        with pytest.raises(ValueError):
            operation(bad)
        equal(before, rnd.checkpoint_state())


@pytest.mark.parametrize("historical_updates", [0, 3])
def test_current_native_manual_optimizer_history_replaces_existing_service_counts(historical_updates):
    source = provider(3, 9, "occupancy_fifo", "service_before_admit")
    for _ in range(historical_updates):
        loss = (source.predictor_network(rows(3)) - source.fixed_network(rows(3))).square().mean()
        source.optimizer.zero_grad()
        loss.backward()
        source.optimizer.step()
    source.obs_buffer.extend(rows(2).unbind())
    assert source.update_predictor() == 0.0
    destination = provider(3, 9, "occupancy_fifo", "service_before_admit")
    destination.admit_and_service(rows(8), vector_tick=3)
    before = destination.checkpoint_state()
    for operation in (destination.validate_state, destination.prepare_state, destination.load_state):
        with pytest.raises(ValueError):
            operation(source.available_state())
        equal(before, destination.checkpoint_state())
    destination.load_state(source.checkpoint_state())
    state = destination.checkpoint_state()
    equal(source.checkpoint_state(), state)
    assert before["predictor_service"]["optimizer_updates"] == 2
    assert state["predictor_service"]["optimizer_updates"] == 0
    assert state["predictor_service"]["optimizer_step_offset"] == historical_updates
    restored = provider(3, 9, "occupancy_fifo", "service_before_admit")
    restored.load_state(state)
    equal(state, restored.checkpoint_state())
    for current in (destination, restored):
        current.obs_buffer.extend(rows(1).unbind())
        assert current.update_predictor() > 0
    equal(destination.checkpoint_state(), restored.checkpoint_state())
    assert {int(moment["step"].item()) for moment in destination.optimizer.state.values()} == {historical_updates + 1}


def test_supported_optimizer_execution_options_survive_restore():
    source = provider(3, 6, "paced_fifo", "service_before_admit")
    source.optimizer = torch.optim.Adam(source.predictor_network.parameters(), lr=0.0002, amsgrad=True, maximize=True, foreach=True)
    source.admit_and_service(rows(5), vector_tick=0)
    restored = provider(3, 6, "paced_fifo", "service_before_admit")
    restored.load_state(source.checkpoint_state())
    for current in (source, restored):
        current.admit_and_service(rows(1), vector_tick=1)
    equal(source.checkpoint_state(), restored.checkpoint_state())


@pytest.mark.parametrize("steps", [1, 5])
def test_public_manual_optimizer_steps_capture_their_live_clock(steps):
    source = provider(3, 6, "paced_fifo", "service_before_admit")
    for _ in range(steps):
        loss = (source.predictor_network(rows(3)) - source.fixed_network(rows(3))).square().mean()
        source.optimizer.zero_grad()
        loss.backward()
        source.optimizer.step()
    state = source.checkpoint_state()
    assert state["predictor_service"]["optimizer_updates"] == 0
    assert state["predictor_service"]["optimizer_step_offset"] == steps
    restored = provider(3, 6, "paced_fifo", "service_before_admit")
    restored.load_state(state)
    for current in (source, restored):
        current.admit_and_service(rows(3), vector_tick=0)
    equal(source.checkpoint_state(), restored.checkpoint_state())


def service_counter_values(snapshot):
    return (
        snapshot.admitted_rows,
        snapshot.consumed_rows,
        snapshot.dropped_rows,
        snapshot.pending_rows,
        snapshot.optimizer_updates,
    )


def test_public_predictor_counters_follow_genuine_legacy_optimizer_work():
    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
    before = copy.deepcopy(rnd.predictor_network.state_dict())
    steps = []
    handle = rnd.optimizer.register_step_post_hook(lambda *_: steps.append(1))
    try:
        rnd.update({"observations": rows(7)})
    finally:
        handle.remove()
    assert steps == [1]
    assert {int(moment["step"].item()) for moment in rnd.optimizer.state.values()} == {1}
    assert any(not torch.equal(before[key], value) for key, value in rnd.predictor_network.state_dict().items())
    # The first intended RED is here, after genuine existing one-minibatch work.
    assert callable(getattr(rnd, "predictor_service_counters", None)), "cheap public predictor accounting view missing"
    assert service_counter_values(rnd.predictor_service_counters()) == (7, 3, 0, 4, 1)


def test_public_predictor_counters_bracket_legacy_partial_and_full_direct_updates():
    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
    rnd.obs_buffer.extend(rows(2).unbind())
    assert rnd.update_predictor() == 0.0
    assert rnd.optimizer.state == {}
    before = rnd.predictor_service_counters()
    assert service_counter_values(before) == (2, 0, 0, 2, 0)
    rnd.obs_buffer.extend(rows(5).unbind())
    # An unserviced public-buffer append changes occupancy, not recorded admissions.
    unserviced = rnd.predictor_service_counters()
    assert service_counter_values(unserviced) == (2, 0, 0, 7, 0)
    loss = rnd.update_predictor()
    assert type(loss) is float
    after = rnd.predictor_service_counters()
    assert service_counter_values(after) == (7, 3, 0, 4, 1)
    assert after.admitted_rows - before.admitted_rows == 5
    assert after.consumed_rows - before.consumed_rows == 3
    assert after.optimizer_updates - before.optimizer_updates == 1
    assert type(rnd.update_predictor()) is float
    assert service_counter_values(rnd.predictor_service_counters()) == (7, 6, 0, 1, 2)
    assert rnd.update_predictor() == 0.0
    assert service_counter_values(rnd.predictor_service_counters()) == (7, 6, 0, 1, 2)
    assert {int(moment["step"].item()) for moment in rnd.optimizer.state.values()} == {2}
    assert service_counter_values(before) == (2, 0, 0, 2, 0)


@pytest.mark.parametrize("configured", [False, True])
def test_public_predictor_counters_count_real_zero_loss_steps(configured):
    rnd = (
        provider(3, 9, "paced_fifo", "service_before_admit")
        if configured
        else RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
    )
    rnd.predictor_network.load_state_dict(rnd.fixed_network.state_dict())
    steps = []
    handle = rnd.optimizer.register_step_post_hook(lambda *_: steps.append(1))
    try:
        if configured:
            receipt = rnd.admit_and_service(rows(7), vector_tick=0)
            assert receipt.last_loss == 0.0
            assert receipt.optimizer_updates == 1
        else:
            rnd.obs_buffer.extend(rows(7).unbind())
            assert rnd.update_predictor() == 0.0
        assert steps == [1]
        assert {int(moment["step"].item()) for moment in rnd.optimizer.state.values()} == {1}
        assert service_counter_values(rnd.predictor_service_counters()) == (7, 3, 0, 4, 1)
        assert rnd.update_predictor() == 0.0
        assert steps == [1, 1]
        assert {int(moment["step"].item()) for moment in rnd.optimizer.state.values()} == {2}
        assert service_counter_values(rnd.predictor_service_counters()) == (7, 6, 0, 1, 2)
        assert rnd.update_predictor() == 0.0
        assert steps == [1, 1]
    finally:
        handle.remove()


@pytest.mark.parametrize("mode", ["paced_fifo", "occupancy_fifo"])
@pytest.mark.parametrize("policy", ["service_before_admit", "drop_oldest", "drop_newest"])
def test_public_predictor_counters_agree_with_configured_receipts(mode, policy):
    rnd = provider(3, 3, mode, policy)
    steps = []
    handle = rnd.optimizer.register_step_post_hook(lambda *_: steps.append(1))
    totals = [0, 0, 0, 0]
    try:
        assert service_counter_values(rnd.predictor_service_counters()) == (0, 0, 0, 0, 0)
        for count, tick in ((7, 4), (2, 4), (0, 5), (4, 6)):
            receipt = rnd.admit_and_service(rows(count), vector_tick=tick)
            totals = [
                a + b
                for a, b in zip(
                    totals, (receipt.admitted_rows, receipt.consumed_rows, receipt.dropped_rows, receipt.optimizer_updates), strict=True
                )
            ]
            snapshot = rnd.predictor_service_counters()
            assert service_counter_values(snapshot) == (*totals[:3], receipt.pending_rows, totals[3])
            assert snapshot.admitted_rows == snapshot.consumed_rows + snapshot.dropped_rows + snapshot.pending_rows
            assert snapshot.optimizer_updates == len(steps)
            assert snapshot.consumed_rows == 3 * len(steps)
            assert {int(moment["step"].item()) for moment in rnd.optimizer.state.values()} == {len(steps)}
        assert len(steps) > 0
    finally:
        handle.remove()


@pytest.mark.parametrize("configured", [False, True])
def test_public_predictor_counters_are_frozen_owned_primitives_and_observationally_pure(monkeypatch, configured):
    import random
    from dataclasses import FrozenInstanceError, fields, is_dataclass

    import numpy as np

    rnd = (
        provider(3, 9, "paced_fifo", "service_before_admit")
        if configured
        else RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
    )
    rnd.update({"observations": rows(5)})
    before = rnd.checkpoint_state()  # One test oracle, never the per-step accounting path.
    queue = rnd.obs_buffer
    queued_rows = tuple(queue)
    networks = (rnd.fixed_network, rnd.predictor_network)
    optimizer = rnd.optimizer
    gradients = [None if parameter.grad is None else parameter.grad.clone() for parameter in rnd.predictor_network.parameters()]
    torch_rng = torch.get_rng_state().clone()
    numpy_rng = np.random.get_state()
    python_rng = random.getstate()

    def forbidden(*_args, **_kwargs):
        pytest.fail("counter observation performed clone/model/optimizer/admission/service work")

    with monkeypatch.context() as guarded:
        for name in ("checkpoint_state", "available_state", "update", "update_predictor", "admit_and_service", "configure_service"):
            guarded.setattr(rnd, name, forbidden)
        for network in networks:
            guarded.setattr(network, "forward", forbidden)
            guarded.setattr(network, "state_dict", forbidden)
        for name in ("step", "zero_grad", "state_dict"):
            guarded.setattr(optimizer, name, forbidden)
        guarded.setattr("townlet.exploration.rnd.deepcopy", forbidden)
        guarded.setattr(torch.Tensor, "clone", forbidden)
        guarded.setattr(torch, "stack", forbidden)
        snapshots = [rnd.predictor_service_counters() for _ in range(3)]

    snapshot = snapshots[0]
    assert type(snapshot).__name__ == "PredictorServiceCounters"
    assert is_dataclass(snapshot)
    assert tuple(field.name for field in fields(snapshot)) == (
        "admitted_rows",
        "consumed_rows",
        "dropped_rows",
        "pending_rows",
        "optimizer_updates",
    )
    assert all(type(value) is int for value in service_counter_values(snapshot))
    assert all(service_counter_values(item) == (5, 3, 0, 2, 1) for item in snapshots)
    for field in fields(snapshot):
        with pytest.raises(FrozenInstanceError):
            setattr(snapshot, field.name, 999)
    assert rnd.obs_buffer is queue
    assert len(queue) == len(queued_rows)
    assert all(current is original for current, original in zip(queue, queued_rows, strict=True))
    assert rnd.fixed_network is networks[0] and rnd.predictor_network is networks[1]
    assert rnd.optimizer is optimizer
    equal(before, rnd.checkpoint_state())
    for parameter, gradient in zip(rnd.predictor_network.parameters(), gradients, strict=True):
        if gradient is None:
            assert parameter.grad is None
        else:
            equal(gradient, parameter.grad)
    equal(torch_rng, torch.get_rng_state())
    current_numpy_rng = np.random.get_state()
    assert numpy_rng[0] == current_numpy_rng[0]
    assert np.array_equal(numpy_rng[1], current_numpy_rng[1])
    assert numpy_rng[2:] == current_numpy_rng[2:]
    assert python_rng == random.getstate()
    rnd.update({"observations": rows(1)})
    assert service_counter_values(rnd.predictor_service_counters()) == (6, 6, 0, 0, 2)
    assert service_counter_values(snapshot) == (5, 3, 0, 2, 1)
