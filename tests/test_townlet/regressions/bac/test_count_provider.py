"""COUNT owns finite novelty/LRU state; world-bank routing remains a later gate."""

from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config


def _policy(width: float, capacity: int, scope: str | None, weight: float) -> ResolvedExplorationPolicy:
    manifest = Path(__file__).resolve().parents[2] / "fixtures/bac_curiosity_pre_scope/manifest.json"
    effective = json.loads(manifest.read_text())["artifacts"][0]["effective_run"]
    training = copy.deepcopy(effective["training"])
    drive = copy.deepcopy(effective["exploration"]["authored_parameters"]["drive_intrinsic"])
    options = {"providers": {"count_based": {"quantization_width": width, "max_entries": capacity}}}
    if scope is not None:
        options["curiosity_scope"] = {"scope": scope}
    training["population"]["size"] = 3
    training["replay_buffer"].update(batch_size=2, min_size=2, capacity=64)
    training["exploration"].update(epsilon_start=0.4, epsilon_end=0.1, epsilon_decay=0.5)
    training["intrinsic"]["initial_weight"] = weight
    training["bac_options"] = options
    drive["strategy"] = "count_based"
    policy = resolve_exploration_policy(
        IntrinsicStrategyConfig.model_validate(drive), TrainingV2Config.model_validate(training), BaCOptions.model_validate(options)
    )
    assert policy.provider_parameters == {"quantization_width": width, "max_entries": capacity}
    assert policy.to_dict()["raw_provider_parameters"] == {
        key: drive[key] for key in ("rnd_config", "adaptive_config", "count_config", "icm_config")
    }
    assert policy.parameter_units["quantization_width"] == "observation_units/bin"
    assert policy.parameter_units["max_entries"] == "LRU_keys"
    assert policy.field_roles["provider_parameters.quantization_width"].origin == "bac_options.providers.count_based.quantization_width"
    return policy


def _provider(policy: ResolvedExplorationPolicy):
    assert importlib.util.find_spec("townlet.exploration.count_based") is not None, "T18b requires the bounded count novelty provider"
    provider_type = importlib.import_module("townlet.exploration.count_based").CountExploration
    return provider_type(
        policy,
        quantization_width=policy.provider_parameters["quantization_width"],
        max_entries=policy.provider_parameters["max_entries"],
        device=torch.device("cpu"),
    )


def _reward(provider, values: list[float], update_stats: bool) -> torch.Tensor:
    return provider.compute_intrinsic_rewards(torch.tensor(values, dtype=torch.float64).reshape(-1, 1), update_stats=update_stats)


def test_count_novelty_and_no_stat_query():
    provider = _provider(_policy(0.25, 4, None, 1.0))
    observations = torch.tensor([[10.0], [10.0], [float("nan")]], dtype=torch.float64)
    active = torch.tensor([True, True, False])
    rewards = torch.zeros(3, dtype=torch.float64)
    rewards[active] = provider.compute_intrinsic_rewards(observations[active], update_stats=True)
    torch.testing.assert_close(rewards, torch.tensor([1.0, 1 / math.sqrt(2), 0.0], dtype=torch.float64))
    snapshot = copy.deepcopy(provider.checkpoint_state())
    assert snapshot["counts"] == {(40,): 2}
    assert snapshot["lru"] == [(40,)]
    torch.testing.assert_close(_reward(provider, [10.0, 11.0], False), torch.tensor([1 / math.sqrt(3), 1.0], dtype=torch.float64))
    assert provider.checkpoint_state() == snapshot
    context = IntrinsicTransitionContext(
        predecessor=torch.tensor([[10.0], [11.0]], dtype=torch.float64),
        actions=torch.tensor([0, 1]),
        successor=torch.tensor([[10.0], [11.0]], dtype=torch.float64),
        active_on_entry=torch.tensor([True, False]),
        vector_tick=0,
    )
    receipt = provider.admit_and_service(context)
    assert receipt.provider == "count_based"
    assert (receipt.admitted_rows, receipt.consumed_rows, receipt.dropped_rows, receipt.pending_rows) == (0, 0, 0, 0)
    assert (receipt.optimizer_updates, receipt.mandatory_service_updates, receipt.last_loss) == (0, 0, 0.0)
    assert provider.checkpoint_state() == snapshot


def test_count_omitted_update_flag_preserves_observation_protocol():
    provider = _provider(_policy(0.25, 4, None, 1.0))
    observations = torch.tensor([[0.0], [0.0]], dtype=torch.float64)
    torch.testing.assert_close(
        provider.compute_intrinsic_rewards(observations, True), torch.tensor([1.0, 1 / math.sqrt(2)], dtype=torch.float64)
    )
    queries = torch.tensor([[0.0], [0.25]], dtype=torch.float64)
    expected = torch.tensor([1 / math.sqrt(3), 1.0], dtype=torch.float64)
    snapshot = copy.deepcopy(provider.checkpoint_state())
    torch.testing.assert_close(provider.compute_intrinsic_rewards(queries, False), expected)
    torch.testing.assert_close(provider.compute_intrinsic_rewards(queries, update_stats=False), expected)
    assert provider.checkpoint_state() == snapshot
    torch.testing.assert_close(provider.compute_intrinsic_rewards(queries), expected)
    assert provider.checkpoint_state() == snapshot
    torch.testing.assert_close(provider.compute_intrinsic_rewards(observations=queries), expected)
    assert provider.checkpoint_state() == snapshot
    for invalid_flag in (None, 0, 1, "False", []):
        with pytest.raises(ValueError):
            provider.compute_intrinsic_rewards(queries, invalid_flag)
        assert provider.checkpoint_state() == snapshot
    with pytest.raises(TypeError):
        provider.compute_intrinsic_rewards(queries, False, update_stats=False)
    with pytest.raises(TypeError):
        provider.compute_intrinsic_rewards(queries, False, False)
    with pytest.raises(TypeError):
        provider.compute_intrinsic_rewards(queries, unsupported=False)
    assert provider.checkpoint_state() == snapshot
    torch.testing.assert_close(provider.compute_intrinsic_rewards(observations=queries, update_stats=True), expected)
    assert provider.checkpoint_state()["counts"] == {(0,): 3, (1,): 1}


def test_count_exact_signed_bins_extremes_and_width_contrast():
    provider = _provider(_policy(0.25, 16, None, 1.0))
    rewards = _reward(provider, [-0.01, 0.0, 0.249, 0.25, -0.0, -0.25, -0.2501], True)
    torch.testing.assert_close(
        rewards, torch.tensor([1.0, 1.0, 1 / math.sqrt(2), 1.0, 1 / math.sqrt(3), 1 / math.sqrt(2), 1.0], dtype=torch.float64)
    )
    assert provider.checkpoint_state()["counts"] == {(-1,): 2, (0,): 3, (1,): 1, (-2,): 1}
    assert provider.checkpoint_state()["lru"] == [(1,), (0,), (-1,), (-2,)]
    huge = [2.0**1023, 2.0**1022, -(2.0**1023), -(2.0**1022)]
    torch.testing.assert_close(_reward(provider, huge, True), torch.ones(4, dtype=torch.float64))
    torch.testing.assert_close(_reward(provider, huge, True), torch.full((4,), 1 / math.sqrt(2), dtype=torch.float64))
    assert set(provider.checkpoint_state()["counts"]) >= {(2**1025,), (2**1024,), (-(2**1025),), (-(2**1024),)}
    exact = _provider(_policy(0.1, 8, None, 1.0))
    # Exact represented-float .5/.1 is below 5, although float division rounds to 5.
    torch.testing.assert_close(_reward(exact, [0.499, 0.5, 0.5001], True), torch.tensor([1.0, 1 / math.sqrt(2), 1.0], dtype=torch.float64))
    assert exact.checkpoint_state()["counts"] == {(4,): 2, (5,): 1}
    fine = _provider(_policy(0.25, 4, None, 1.0))
    coarse = _provider(_policy(1.0, 4, None, 1.0))
    torch.testing.assert_close(_reward(fine, [0.0, 0.25], True), torch.ones(2, dtype=torch.float64))
    torch.testing.assert_close(_reward(coarse, [0.0, 0.25], True), torch.tensor([1.0, 1 / math.sqrt(2)], dtype=torch.float64))


def test_count_capacity_and_restore():
    policy = _policy(0.25, 2, None, 1.0)
    provider = _provider(policy)
    _reward(provider, [0.0, 0.25], True)
    before_query = copy.deepcopy(provider.checkpoint_state())
    assert _reward(provider, [0.0], False).item() == pytest.approx(1 / math.sqrt(2))
    assert provider.checkpoint_state() == before_query
    assert _reward(provider, [0.5], True).item() == 1.0
    assert provider.eviction_count == 1
    assert provider.checkpoint_state()["counts"] == {(1,): 1, (2,): 1}
    assert provider.checkpoint_state()["lru"] == [(1,), (2,)]
    assert _reward(provider, [0.25], True).item() == pytest.approx(1 / math.sqrt(2))
    provider.decay_epsilon()
    saved = provider.checkpoint_state()
    assert saved["schema_version"] == "count-state-v1"
    assert saved["policy_identity"] == policy.policy_identity
    assert saved["policy"] == policy.to_dict()
    assert (saved["quantization_width"], saved["max_entries"], saved["eviction_count"]) == (0.25, 2, 1)
    assert (saved["epsilon"], saved["epsilon_decay"], saved["epsilon_min"]) == (0.2, 0.5, 0.1)
    restored = _provider(policy)
    restored.load_state(saved)
    assert restored.checkpoint_state() == saved
    assert _reward(restored, [0.5], True).item() == pytest.approx(1 / math.sqrt(2))
    assert restored.checkpoint_state()["lru"] == [(1,), (2,)]
    assert _reward(provider, [0.5], True).item() == pytest.approx(1 / math.sqrt(2))
    assert restored.checkpoint_state() == provider.checkpoint_state()
    assert _reward(restored, [0.0], True).item() == 1.0
    assert restored.eviction_count == 2
    assert restored.checkpoint_state()["lru"] == [(2,), (0,)]


@pytest.mark.parametrize(
    "corruption",
    [
        "zero_count",
        "negative_count",
        "bool_count",
        "float_count",
        "duplicate_lru",
        "missing_lru",
        "bad_bin",
        "policy",
        "identity",
        "width",
        "capacity",
        "epsilon",
        "evictions",
        "schema",
    ],
)
def test_count_corrupt_restore_is_atomic(corruption: str):
    provider = _provider(_policy(0.25, 2, None, 1.0))
    _reward(provider, [0.0, 0.25], True)
    before = copy.deepcopy(provider.checkpoint_state())
    broken = copy.deepcopy(before)
    if corruption in ("zero_count", "negative_count", "bool_count", "float_count"):
        broken["counts"][(0,)] = {"zero_count": 0, "negative_count": -1, "bool_count": True, "float_count": 1.5}[corruption]
    elif corruption == "duplicate_lru":
        broken["lru"] = [(0,), (0,)]
    elif corruption == "missing_lru":
        broken["lru"] = [(0,)]
    elif corruption == "bad_bin":
        broken["counts"] = {(False,): 1, (1,): 1}
    elif corruption == "policy":
        broken["policy"]["provider_parameters"]["quantization_width"] = 1.0
    else:
        field, value = {
            "identity": ("policy_identity", "0" * 64),
            "width": ("quantization_width", 0.5),
            "capacity": ("max_entries", 3),
            "epsilon": ("epsilon", float("nan")),
            "evictions": ("eviction_count", -1),
            "schema": ("schema_version", "unknown"),
        }[corruption]
        broken[field] = value
    with pytest.raises(ValueError):
        provider.load_state(broken)
    assert provider.checkpoint_state() == before
    assert _reward(provider, [0.0], True).item() == pytest.approx(1 / math.sqrt(2))


def test_count_instances_and_checkpoints_own_their_state():
    policy = _policy(0.25, 2, "per_world", 1.0)
    assert (policy.curiosity_scope, policy.seed_policy, policy.scope_guarantee) == (
        "per_world",
        "world_id_derived_v1",
        "world_id_owned_state",
    )
    first, second = _provider(policy), _provider(policy)
    _reward(first, [0.0], True)
    assert _reward(second, [0.0], True).item() == 1.0
    saved = first.checkpoint_state()
    second.load_state(saved)
    original = copy.deepcopy(second.checkpoint_state())
    saved["counts"][(0,)] = 100
    saved["lru"].append((99,))
    saved["policy"]["authored_parameters"]["bac_options"]["providers"]["count_based"]["max_entries"] = 99
    assert first.checkpoint_state() == original
    assert second.checkpoint_state() == original
    assert _reward(first, [0.0], True).item() == pytest.approx(1 / math.sqrt(2))
    assert _reward(second, [0.0], False).item() == pytest.approx(1 / math.sqrt(2))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_count_nonfinite_admission_refuses_before_mutation(value: float):
    provider = _provider(_policy(0.25, 2, None, 1.0))
    before = copy.deepcopy(provider.checkpoint_state())
    with pytest.raises(ValueError):
        _reward(provider, [0.0, value], True)
    assert provider.checkpoint_state() == before


@pytest.mark.parametrize(
    "width,capacity",
    [
        (0.0, 2),
        (-0.25, 2),
        (float("nan"), 2),
        (float("inf"), 2),
        (True, 2),
        (0.5, 2),
        (0.25, 0),
        (0.25, -1),
        (0.25, True),
        (0.25, 2.5),
        (0.25, 3),
    ],
)
def test_count_constructor_refuses_invalid_or_policy_divergent_configuration(width, capacity):
    policy = _policy(0.25, 2, None, 1.0)
    _provider(policy)
    provider_type = importlib.import_module("townlet.exploration.count_based").CountExploration
    with pytest.raises(ValueError):
        provider_type(policy, quantization_width=width, max_entries=capacity, device=torch.device("cpu"))


def test_count_legal_actions_epsilon_and_zero_weight_stay_finite():
    policy = _policy(0.25, 2, None, 0.0)
    assert (policy.curiosity_scope, policy.scope_origin, policy.seed_policy) == ("shared", "bac-options-v1", "legacy_shared_v1")
    provider = _provider(policy)
    actions = provider.select_actions(
        torch.tensor([[100.0, 1.0, 99.0], [100.0, 99.0, 1.0]]),
        SimpleNamespace(epsilons=torch.tensor([1.0, 0.0])),
        action_masks=torch.tensor([[False, True, False], [False, False, True]]),
    )
    assert actions.tolist() == [1, 2]
    for _ in range(4):
        provider.decay_epsilon()
    assert provider.epsilon == 0.1
    rewards = _reward(provider, [0.0, 0.0], True)
    assert torch.isfinite(rewards).all()
    torch.testing.assert_close(rewards, torch.tensor([1.0, 1 / math.sqrt(2)], dtype=torch.float64))
    torch.testing.assert_close(rewards * policy.initial_intrinsic_weight, torch.zeros_like(rewards))
