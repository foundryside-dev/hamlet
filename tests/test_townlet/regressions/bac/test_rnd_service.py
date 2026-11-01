"""Bounded FIFO service, real predictor updates and transactional continuation."""

import copy

import pytest
import torch

from townlet.config.bac_options import RNDOptions
from townlet.exploration.rnd import RNDExploration


def provider(batch, capacity, mode, overflow):
    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=batch)
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
        service["paced_updates_this_tick"] = 2
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
    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
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


def test_direct_minibatch_and_explicit_legacy_available_state():
    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
    rnd.update({"observations": rows(7)})
    assert len(rnd.obs_buffer) == 4  # Preserve working legacy one-minibatch update API.
    assert rnd.update_predictor() > 0
    assert len(rnd.obs_buffer) == 1
    assert hasattr(rnd, "available_state"), "explicit available-state export missing"
    legacy = rnd.available_state()
    assert "predictor_service" not in legacy
    restored = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
    restored.load_available_state(legacy)
    equal(legacy, restored.available_state())
    assert restored.obs_buffer == []
    restored.load_state(legacy)  # Exact historical schema remains a supported public API.
    equal(legacy, restored.available_state())
    rnd.load_state(legacy)
    equal(torch.stack(rnd.obs_buffer), rows(7)[6:])  # Historical import never invents or discards destination tails.
    with pytest.raises(ValueError):
        restored.load_state({**legacy, "misspelled_service": {}})


def test_invalid_minibatch_refuses_before_allocation():
    for batch in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=batch)


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
        bad["predictor_service"]["paced_updates_this_tick"] = 1
        bad["predictor_service"]["optimizer_updates"] = 0
        bad["predictor_service"]["consumed_rows"] = 0
        bad["predictor_service"]["admitted_rows"] = 2
        bad["predictor_service"]["vector_tick"] = 2
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
    with DemoRunner(
        config_dir=pack, db_path=tmp_path / "run.db", checkpoint_dir=tmp_path / "checkpoints", max_episodes=2, level_name="L0_0_minimal"
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
        config_dir=pack, db_path=tmp_path / "fresh.db", checkpoint_dir=fresh_dir, max_episodes=payload["episode"], level_name="L0_0_minimal"
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
def test_historical_optimizer_history_aligns_with_existing_service_counts(historical_updates):
    source = provider(3, 9, "occupancy_fifo", "service_before_admit")
    for tick in range(historical_updates):
        source.admit_and_service(rows(3), vector_tick=tick)
    destination = provider(3, 9, "occupancy_fifo", "service_before_admit")
    destination.admit_and_service(rows(8), vector_tick=3)
    destination.load_state(source.available_state())
    state = destination.checkpoint_state()
    assert state["predictor_service"]["optimizer_updates"] == 2
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
