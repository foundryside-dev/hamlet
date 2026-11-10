"""Native component reset proofs; BANK boundary and RNG custody are external gates."""

import random
from copy import deepcopy
from typing import Any

import numpy as np
import pytest
import torch

from tests.test_townlet.regressions.bac.test_pw_scope_conversion import compiled as compiled
from tests.test_townlet.regressions.bac.test_pw_scope_conversion import policy
from townlet.config.bac_options import BaCOptions, RNDOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, resolve_exploration_policy
from townlet.exploration import provider_factory
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.rnd import RNDExploration
from townlet.exploration.world_curiosity_state import ServiceClock

FAMILIES = ("rnd", "adaptive_rnd", "icm")
UNITS = ("vector_tick", "world_eligible_admission")


def assert_equal(left: Any, right: Any) -> None:
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert left.shape == right.shape
        assert left.dtype == right.dtype
        assert left.device == right.device
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert left.shape == right.shape
        assert left.dtype == right.dtype
        assert np.array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            assert_equal(a, b)
    else:
        assert left == right


def ambient_rng() -> tuple[Any, ...]:
    """Observe after real construction; native reset itself must consume no draws."""
    return torch.get_rng_state().clone(), random.getstate(), deepcopy(np.random.get_state())


def inner(backend: Any) -> Any:
    return backend.rnd if isinstance(backend, AdaptiveIntrinsicExploration) else backend


def native(state: dict[str, Any], family: str) -> dict[str, Any]:
    return state["rnd_state"] if family == "adaptive_rnd" else state


def ledger(state: dict[str, Any], family: str) -> dict[str, Any]:
    state = native(state, family)
    return state["counters"] if family == "icm" else state["predictor_service"]


def pending(state: dict[str, Any], family: str) -> Any:
    state = native(state, family)
    return state["pending"] if family == "icm" else state["predictor_service"]["pending_observations"]


def origin(state: dict[str, Any], family: str) -> int:
    state = native(state, family)
    return state["optimizer_epoch_origin"] if family == "icm" else state["predictor_service"]["optimizer_epoch_origin"]


def modules(backend: Any) -> tuple[Any, ...]:
    backend = inner(backend)
    if isinstance(backend, ICMExploration):
        return backend.encoder, backend.inverse_model, backend.forward_model
    return backend.fixed_network, backend.predictor_network


def parameters(backend: Any) -> list[Any]:
    return [parameter for module in modules(backend) for parameter in module.parameters() if parameter.requires_grad]


def gradients(backend: Any) -> list[Any]:
    return [None if p.grad is None else p.grad.detach().clone() for module in modules(backend) for p in module.parameters()]


def assert_pairing(backend: Any) -> None:
    actual = [p for group in inner(backend).optimizer.param_groups for p in group["params"]]
    assert [id(p) for p in actual] == [id(p) for p in parameters(backend)]


def adam_steps(backend: Any) -> set[int]:
    return {int(item["step"].item()) for item in inner(backend).optimizer.state.values()}


def construct(compiled: Any, family: str, unit: str, *, overflow: str = "drop_oldest") -> Any:
    scope = "shared" if unit == "vector_tick" else "per_world"
    selected = policy(compiled, family, scope, "paced_fifo")
    if family == "icm":
        # The public fixture authors drop_oldest; a different policy is never forged.
        assert overflow == "drop_oldest"
        return ICMExploration(
            selected,
            obs_dim=3,
            action_dim=2,
            feature_dim=4,
            hidden_dim=8,
            learning_rate=0.001,
            inverse_weight=0.8,
            forward_weight=0.2,
            training_batch_size=2,
            max_pending_transitions=4,
            device="cpu",
            rng=None,
            service_clock_unit=unit,
        )
    common = dict(obs_dim=3, embed_dim=4, epsilon_start=0.8, epsilon_min=0.1, epsilon_decay=0.9, device=torch.device("cpu"))
    if family == "rnd":
        backend = RNDExploration(**common, learning_rate=0.001, training_batch_size=2, rng=None, service_clock_unit=unit)
    else:
        backend = AdaptiveIntrinsicExploration(
            **common,
            rnd_learning_rate=0.001,
            rnd_training_batch_size=2,
            initial_intrinsic_weight=0.4,
            min_intrinsic_weight=0.0,
            variance_threshold=100.0,
            min_survival_fraction=0.1,
            max_episode_length=20,
            survival_window=20,
            decay_rate=0.9,
            rng=None,
            service_clock_unit=unit,
        )
    backend.configure_service(RNDOptions(service_mode="paced_fifo", max_updates_per_tick=1, max_pending_rows=4, overflow_policy=overflow))
    return backend


def rows(start: int, count: int) -> torch.Tensor:
    return torch.arange(start * 3, (start + count) * 3, dtype=torch.float32).reshape(count, 3) / 10 + 0.2


def service(backend: Any, *, start: int, count: int, position: int, tick: int) -> Any:
    observations = rows(start, count)
    clock = ServiceClock(backend.service_clock_unit, position)
    if isinstance(backend, ICMExploration):
        context = IntrinsicTransitionContext(
            predecessor=observations,
            actions=torch.arange(count, dtype=torch.long) % 2,
            successor=observations + 0.125,
            active_on_entry=torch.ones(count, dtype=torch.bool),
            vector_tick=tick,
        )
        return backend.admit_and_service_at(context, clock=clock)
    return backend.admit_and_service_at(observations, clock=clock)


def train_with_tail(backend: Any, family: str) -> None:
    service(backend, start=0, count=3, position=3 if backend.service_clock_unit == "world_eligible_admission" else 7, tick=7)
    state = backend.checkpoint_state()
    assert ledger(state, family)["optimizer_updates"] == 1
    assert len(pending(state, family)) == 1
    assert adam_steps(backend) == {1}
    assert any(value is not None for value in gradients(backend))
    inner(backend).decay_epsilon()
    if family != "icm":
        backend.compute_intrinsic_rewards(rows(10, 3), update_stats=True)
        assert inner(backend).reward_rms.count > 1e-4
    if family == "adaptive_rnd":
        for _ in range(10):
            backend.update_on_episode_end(10.0)
        assert backend.survival_history
        assert backend.current_intrinsic_weight < backend.initial_intrinsic_weight


def assert_service_preserved(before: dict[str, Any], after: dict[str, Any], family: str) -> None:
    old, new = ledger(before, family), ledger(after, family)
    for key in ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates"):
        assert_equal(old[key], new[key])
    assert_equal(pending(before, family), pending(after, family))
    if family == "icm":
        assert_equal(old["mandatory_service_updates"], new["mandatory_service_updates"])
    for key in ("service_clock_unit", "service_position", "ordinary_updates_at_position"):
        a = native(before, family) if family == "icm" else old
        b = native(after, family) if family == "icm" else new
        assert_equal(a[key], b[key])
    if family != "icm":
        for key in ("options", "training_batch_size", "step_counter"):
            assert_equal(old[key], new[key])
    for key in ("epsilon", "epsilon_min", "epsilon_decay"):
        assert_equal(native(before, family)[key], native(after, family)[key])


def install_reset(backend: Any, fresh: Any) -> None:
    rng_before = ambient_rng()
    prepared = backend.prepare_learning_reset(fresh=fresh)
    assert_equal(ambient_rng(), rng_before)
    backend.install_state(prepared)
    assert_equal(ambient_rng(), rng_before)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("unit", UNITS)
def test_reset_fresh_learning_retains_real_service_and_next_update(compiled: Any, family: str, unit: str) -> None:
    backend = construct(compiled, family, unit)
    train_with_tail(backend, family)
    before = backend.checkpoint_state()
    old_pending = list(backend._pending) if family == "icm" else list(inner(backend).obs_buffer)
    fresh = construct(compiled, family, unit)
    fresh_state = fresh.checkpoint_state()
    source_gradients = gradients(backend)
    rng_before = ambient_rng()
    # First intended causal RED: genuine learned native reaches the absent operation.
    prepared = backend.prepare_learning_reset(fresh=fresh)
    assert_equal(ambient_rng(), rng_before)
    assert_equal(backend.checkpoint_state(), before)
    assert_equal(gradients(backend), source_gradients)
    assert_equal(fresh.checkpoint_state(), fresh_state)
    # Candidate ownership must not alias the caller-owned factory learning.
    with torch.no_grad():
        for module in modules(fresh):
            for parameter in module.parameters():
                parameter.add_(3.0)
    backend.install_state(prepared)
    assert_equal(ambient_rng(), rng_before)
    after = backend.checkpoint_state()
    assert_service_preserved(before, after, family)
    new_pending = list(backend._pending) if family == "icm" else list(inner(backend).obs_buffer)
    for old_row, new_row in zip(old_pending, new_pending, strict=True):
        if family == "icm":
            assert old_row is not new_row
            for key in ("predecessor", "successor"):
                assert old_row[key].data_ptr() != new_row[key].data_ptr()
        else:
            assert old_row.data_ptr() != new_row.data_ptr()
    assert origin(after, family) == ledger(before, family)["optimizer_updates"] == 1
    assert inner(backend).optimizer.state == {}
    assert all(value is None for value in gradients(backend))
    assert_pairing(backend)
    model_keys = ("encoder", "inverse_model", "forward_model") if family == "icm" else ("fixed_network", "predictor_network")
    for key in model_keys:
        assert_equal(native(after, family)[key], native(fresh_state, family)[key])
    assert any(
        not torch.equal(native(before, family)[key][name], tensor)
        for key in model_keys
        for name, tensor in native(after, family)[key].items()
    )
    if family == "icm":
        assert after["last_loss"] == 0.0
    else:
        assert inner(backend).reward_rms.mean == 0.0
        assert inner(backend).reward_rms.var == 1.0
        assert inner(backend).reward_rms.count == 1e-4
        assert not any(p.requires_grad for p in inner(backend).fixed_network.parameters())
    if family == "adaptive_rnd":
        assert backend.survival_history == []
        assert backend.current_intrinsic_weight == backend.initial_intrinsic_weight == before["initial_intrinsic_weight"]
        for key in ("min_intrinsic_weight", "variance_threshold", "max_episode_length", "survival_window", "decay_rate"):
            assert_equal(before[key], after[key])
    model_before = [p.detach().clone() for p in parameters(backend)]
    receipt = service(backend, start=30, count=1, position=4 if unit == "world_eligible_admission" else 8, tick=8)
    assert receipt.optimizer_updates == 1
    continued = backend.checkpoint_state()
    assert ledger(continued, family)["optimizer_updates"] == 2
    assert ledger(continued, family)["consumed_rows"] == 4
    assert origin(continued, family) == 1
    assert adam_steps(backend) == {1}
    assert len(pending(continued, family)) == 0
    assert any(not torch.equal(old, actual) for old, actual in zip(model_before, parameters(backend), strict=True))
    assert_pairing(backend)
    backend.validate_state(continued)


@pytest.mark.parametrize("family", FAMILIES)
def test_shared_full_deferred_batch_keeps_spent_budget(compiled: Any, family: str) -> None:
    backend = construct(compiled, family, "vector_tick")
    train_with_tail(backend, family)
    service(backend, start=3, count=1, position=7, tick=7)
    before = backend.checkpoint_state()
    assert len(pending(before, family)) == 2
    install_reset(backend, construct(compiled, family, "vector_tick"))
    assert_service_preserved(before, backend.checkpoint_state(), family)
    same_tick = service(backend, start=4, count=1, position=7, tick=7)
    assert same_tick.optimizer_updates == 0
    assert adam_steps(backend) == set()
    next_tick = service(backend, start=5, count=1, position=8, tick=8)
    assert next_tick.optimizer_updates == 1
    assert adam_steps(backend) == {1}
    backend.validate_state(backend.checkpoint_state())


@pytest.mark.parametrize("family", FAMILIES)
def test_overflow_adjacent_fifo_preserved_before_real_drop(compiled: Any, family: str) -> None:
    backend = construct(compiled, family, "vector_tick")
    train_with_tail(backend, family)
    service(backend, start=3, count=3, position=7, tick=7)
    before = backend.checkpoint_state()
    assert len(pending(before, family)) == 4
    install_reset(backend, construct(compiled, family, "vector_tick"))
    assert_service_preserved(before, backend.checkpoint_state(), family)
    receipt = service(backend, start=6, count=1, position=7, tick=7)
    assert receipt.dropped_rows == 1
    assert receipt.optimizer_updates == 0
    after = backend.checkpoint_state()
    old_tail = pending(before, family)
    new_tail = pending(after, family)
    assert_equal(old_tail[1:] if family != "icm" else old_tail[1:], new_tail[:-1])
    assert ledger(after, family)["admitted_rows"] == ledger(before, family)["admitted_rows"] + 1
    assert ledger(after, family)["dropped_rows"] == ledger(before, family)["dropped_rows"] + 1
    backend.validate_state(after)


@pytest.mark.parametrize("family", ("rnd", "adaptive_rnd"))
def test_overflow_mandatory_real_update_after_reset(compiled: Any, family: str) -> None:
    backend = construct(compiled, family, "vector_tick", overflow="service_before_admit")
    train_with_tail(backend, family)
    service(backend, start=3, count=3, position=7, tick=7)
    before = backend.checkpoint_state()
    install_reset(backend, construct(compiled, family, "vector_tick", overflow="service_before_admit"))
    receipt = service(backend, start=6, count=1, position=7, tick=7)
    assert receipt.overflow_optimizer_updates == 1
    assert receipt.paced_optimizer_updates == 0
    assert ledger(backend.checkpoint_state(), family)["optimizer_updates"] == ledger(before, family)["optimizer_updates"] + 1
    assert adam_steps(backend) == {1}
    backend.validate_state(backend.checkpoint_state())


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("unit", UNITS)
def test_repeated_reset_and_exact_restore_continue_learning(compiled: Any, family: str, unit: str) -> None:
    backend = construct(compiled, family, unit)
    train_with_tail(backend, family)
    initial = backend.checkpoint_state()
    install_reset(backend, construct(compiled, family, unit))
    first = backend.checkpoint_state()
    install_reset(backend, construct(compiled, family, unit))
    second = backend.checkpoint_state()
    assert_service_preserved(initial, second, family)
    assert origin(first, family) == origin(second, family) == 1
    assert first.keys() == second.keys()
    assert native(first, family).keys() == native(second, family).keys()
    assert ledger(first, family).keys() == ledger(second, family).keys()
    assert inner(backend).optimizer.state == {}
    keys = ("encoder", "inverse_model", "forward_model") if family == "icm" else ("fixed_network", "predictor_network")
    assert any(
        not torch.equal(native(first, family)[key][name], tensor) for key in keys for name, tensor in native(second, family)[key].items()
    )
    restored = construct(compiled, family, unit)
    restored.load_state(second)
    assert_equal(restored.checkpoint_state(), second)
    assert_pairing(restored)
    for item in (backend, restored):
        service(item, start=30, count=1, position=4 if unit == "world_eligible_admission" else 8, tick=8)
    assert_equal(backend.checkpoint_state(), restored.checkpoint_state())
    assert_equal(gradients(backend), gradients(restored))
    backend.validate_state(backend.checkpoint_state())


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("defect", ("self", "learned", "configuration", "invalid_source"))
def test_refused_offside_reset_keeps_source_and_fresh(compiled: Any, family: str, defect: str) -> None:
    backend = construct(compiled, family, "vector_tick")
    train_with_tail(backend, family)
    fresh = construct(compiled, family, "vector_tick")
    if defect == "self":
        fresh = backend
    elif defect == "learned":
        train_with_tail(fresh, family)
    elif defect == "configuration":
        fresh = construct(compiled, family, "world_eligible_admission")
    else:
        if family == "icm":
            backend._counters["admitted_rows"] += 1
        else:
            inner(backend)._admitted_rows += 1
    before, candidate = backend.checkpoint_state(), fresh.checkpoint_state()
    before_gradients, candidate_gradients = gradients(backend), gradients(fresh)
    rng_before = ambient_rng()
    with pytest.raises(ValueError):
        backend.prepare_learning_reset(fresh=fresh)
    assert_equal(ambient_rng(), rng_before)
    assert_equal(backend.checkpoint_state(), before)
    assert_equal(fresh.checkpoint_state(), candidate)
    assert_equal(gradients(backend), before_gradients)
    assert_equal(gradients(fresh), candidate_gradients)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("bad_origin", (True, -1, 2, 0.5))
def test_reset_origin_corruption_rejected_without_install(compiled: Any, family: str, bad_origin: Any) -> None:
    backend = construct(compiled, family, "vector_tick")
    train_with_tail(backend, family)
    install_reset(backend, construct(compiled, family, "vector_tick"))
    before = backend.checkpoint_state()
    damaged = deepcopy(before)
    destination = native(damaged, family) if family == "icm" else ledger(damaged, family)
    destination["optimizer_epoch_origin"] = bad_origin
    with pytest.raises(ValueError):
        backend.prepare_state(damaged)
    assert_equal(backend.checkpoint_state(), before)


@pytest.mark.parametrize("family", FAMILIES)
def test_real_adam_history_mismatch_and_foreign_consumed_handles_refuse(compiled: Any, family: str) -> None:
    backend = construct(compiled, family, "vector_tick")
    train_with_tail(backend, family)
    install_reset(backend, construct(compiled, family, "vector_tick"))
    service(backend, start=30, count=1, position=8, tick=8)
    before = backend.checkpoint_state()
    damaged = deepcopy(before)
    adam = native(damaged, family)["optimizer"]["state"]
    assert adam
    next(iter(adam.values()))["step"].add_(1)
    with pytest.raises(ValueError):
        backend.prepare_state(damaged)
    assert_equal(backend.checkpoint_state(), before)
    other = construct(compiled, family, "vector_tick")
    prepared = backend.prepare_learning_reset(fresh=other)
    with pytest.raises(ValueError):
        other.install_state(prepared)
    backend.install_state(prepared)
    installed = backend.checkpoint_state()
    with pytest.raises(ValueError):
        backend.install_state(prepared)
    assert_equal(backend.checkpoint_state(), installed)


@pytest.mark.parametrize("family", ("rnd", "adaptive_rnd"))
def test_rnd_manual_adam_displacement_survives_restore_then_reset_clears_it(compiled: Any, family: str) -> None:
    backend = construct(compiled, family, "vector_tick")
    train_with_tail(backend, family)
    rnd = inner(backend)
    # An actual explicit public manual step changes Adam history, not recorded service.
    for parameter in rnd.predictor_network.parameters():
        parameter.grad = torch.ones_like(parameter) * 0.01
    rnd.optimizer.step()
    before = backend.checkpoint_state()
    assert ledger(before, family)["optimizer_updates"] == 1
    assert ledger(before, family)["optimizer_step_offset"] == 1
    assert adam_steps(backend) == {2}
    restored = construct(compiled, family, "vector_tick")
    restored.load_state(before)
    assert_equal(restored.checkpoint_state(), before)
    # A real managed update must preserve the nonzero displacement before reset.
    service(restored, start=30, count=1, position=8, tick=8)
    managed = restored.checkpoint_state()
    assert ledger(managed, family)["optimizer_updates"] == 2
    assert ledger(managed, family)["consumed_rows"] == 4
    assert ledger(managed, family)["admitted_rows"] == 4
    assert len(pending(managed, family)) == 0
    assert origin(managed, family) == 0
    assert ledger(managed, family)["optimizer_step_offset"] == 1
    assert adam_steps(restored) == {3}
    restored.validate_state(managed)
    old_optimizer = inner(restored).optimizer
    install_reset(restored, construct(compiled, family, "vector_tick"))
    reset = restored.checkpoint_state()
    assert_service_preserved(managed, reset, family)
    assert origin(reset, family) == 2
    assert ledger(reset, family)["optimizer_step_offset"] == 0
    assert old_optimizer is not inner(restored).optimizer
    assert adam_steps(restored) == set()
    service(restored, start=40, count=2, position=9, tick=9)
    assert adam_steps(restored) == {1}
    continued = restored.checkpoint_state()
    assert ledger(continued, family)["optimizer_updates"] == 3
    assert origin(continued, family) == 2
    assert ledger(continued, family)["optimizer_step_offset"] == 0
    restored.validate_state(continued)


@pytest.mark.parametrize("family", FAMILIES)
def test_actual_shared_factory_candidates_use_native_reset_contract(compiled: Any, family: str) -> None:
    selected = policy(compiled, family, "shared", "paced_fifo")

    def factory() -> Any:
        return provider_factory.make_backend(selected, world_id=None, obs_dim=3, action_dim=2, device="cpu", rng=None, descriptor=None)

    backend = factory()
    train_with_tail(backend, family)
    before = backend.checkpoint_state()
    install_reset(backend, factory())
    assert_service_preserved(before, backend.checkpoint_state(), family)
    assert origin(backend.checkpoint_state(), family) == 1
    assert inner(backend).optimizer.state == {}
    assert_pairing(backend)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("unit", UNITS)
def test_ordinary_factory_learning_epoch_zero_current_schema(compiled: Any, family: str, unit: str) -> None:
    backend = construct(compiled, family, unit)
    saved = backend.checkpoint_state()
    assert origin(saved, family) == 0
    assert native(saved, family)["schema"] == ("icm-state-v3" if family == "icm" else "rnd-state-v3")
    if family == "adaptive_rnd":
        assert saved["schema"] == "adaptive-intrinsic-state-v3"
    if family != "icm":
        assert ledger(saved, family)["version"] == 3
    backend.validate_state(saved)
    destination = construct(compiled, family, unit)
    destination.load_state(saved)
    assert_equal(destination.checkpoint_state(), saved)


@pytest.mark.parametrize("family", ("rnd", "adaptive_rnd"))
def test_negative_manual_displacement_is_distinct_from_learning_origin(compiled: Any, family: str) -> None:
    backend = construct(compiled, family, "vector_tick")
    train_with_tail(backend, family)
    rnd = inner(backend)
    # A genuinely new public optimizer has no moments, despite recorded service U=1.
    # This preserves the signed-offset native contract without fabricating Adam steps.
    rnd.optimizer = torch.optim.Adam(rnd.predictor_network.parameters(), lr=0.001)
    saved = backend.checkpoint_state()
    assert ledger(saved, family)["optimizer_updates"] == 1
    assert ledger(saved, family)["optimizer_step_offset"] == -1
    assert adam_steps(backend) == set()
    destination = construct(compiled, family, "vector_tick")
    destination.load_state(saved)
    assert_equal(destination.checkpoint_state(), saved)
    assert origin(destination.checkpoint_state(), family) == 0
    install_reset(destination, construct(compiled, family, "vector_tick"))
    reset = destination.checkpoint_state()
    assert origin(reset, family) == 1
    assert ledger(reset, family)["optimizer_step_offset"] == 0
    assert_service_preserved(saved, reset, family)
    destination.validate_state(reset)


def test_icm_real_mandatory_updates_survive_reset_and_continue(compiled: Any) -> None:
    template = policy(compiled, "icm", "shared", "paced_fifo").to_dict()
    options_data = template["authored_parameters"]["bac_options"]
    options_data["rnd"]["overflow_policy"] = "service_before_admit"
    options_data["providers"]["icm"]["training_batch_size"] = 2
    options_data["providers"]["icm"]["max_pending_transitions"] = 4
    selected = resolve_exploration_policy(
        drive_intrinsic=IntrinsicStrategyConfig.model_validate(template["authored_parameters"]["drive_intrinsic"]),
        training=compiled.get_level(compiled.metadata.primary_level).training,
        options=BaCOptions.model_validate(options_data),
    )
    assert selected.strategy == "icm"
    assert selected.overflow_policy == "service_before_admit"
    assert selected.service_mode == "paced_fifo"
    assert selected.max_updates_per_tick == 1

    def factory() -> Any:
        return provider_factory.make_backend(selected, world_id=None, obs_dim=3, action_dim=2, device="cpu", rng=None, descriptor=None)

    backend = factory()
    train_with_tail(backend, "icm")
    first_overflow = service(backend, start=3, count=4, position=7, tick=7)
    assert first_overflow.mandatory_service_updates == 1
    assert first_overflow.optimizer_updates == 1
    before = backend.checkpoint_state()
    assert before["counters"]["mandatory_service_updates"] == 1
    assert before["counters"]["optimizer_updates"] == 2
    assert before["ordinary_updates_at_position"] == 1
    assert len(before["pending"]) == 3
    assert adam_steps(backend) == {2}
    install_reset(backend, factory())
    reset = backend.checkpoint_state()
    assert_service_preserved(before, reset, "icm")
    assert origin(reset, "icm") == 2
    assert reset["last_loss"] == 0.0
    assert backend.optimizer.state == {}
    second_overflow = service(backend, start=7, count=2, position=7, tick=7)
    assert second_overflow.mandatory_service_updates == 1
    assert second_overflow.optimizer_updates == 1
    after = backend.checkpoint_state()
    assert after["counters"]["mandatory_service_updates"] == 2
    assert after["counters"]["optimizer_updates"] == 3
    assert after["counters"]["admitted_rows"] == 9
    assert after["counters"]["consumed_rows"] == 6
    assert len(after["pending"]) == 3
    assert after["ordinary_updates_at_position"] == 1
    assert after["service_position"] == 7
    assert origin(after, "icm") == 2
    assert adam_steps(backend) == {1}
    assert_pairing(backend)
    backend.validate_state(after)
