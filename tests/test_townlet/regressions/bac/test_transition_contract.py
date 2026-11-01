"""Historical legality and finite Bellman targets; no live-world reconstruction."""

import importlib
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch


def api():
    """Missing proposed interfaces are the intentional baseline failure."""
    for name in ("replay_contract", "q_targets"):
        assert importlib.util.find_spec(f"townlet.training.{name}") is not None, f"T08 missing interface: {name}"
    modules = tuple(importlib.import_module(f"townlet.training.{name}") for name in ("replay_contract", "q_targets"))
    root = Path(__file__).resolve().parents[4]
    for module in modules:
        assert Path(module.__file__).resolve().parent == root / "src/townlet/training"
    return modules


def receipt():
    rc, _ = api()
    return rc.SamplingReceipt(
        indices=np.array([0], dtype=np.int64),
        weights=np.array([1.0], dtype=np.float64),
        population_size=1,
        conditional_draw_probabilities=np.array([1.0], dtype=np.float64),
        mode="uniform_without_replacement",
        objective_unit="transition",
        weight_rule="unit",
    )


def batch(recurrent: bool):
    rc, _ = api()
    shape = (1, 3) if recurrent else (1,)
    observations = torch.zeros((*shape, 2))
    return rc.ReplayBatch(
        legality_recorded=torch.ones(shape, dtype=torch.bool),
        observations=observations,
        actions=torch.zeros(shape, dtype=torch.int64),
        rewards=torch.ones(shape),
        rewards_extrinsic=None,
        rewards_intrinsic=torch.full(shape, 17.0),
        rewards_shaping=None,
        next_observations=observations + 1,
        dones=torch.zeros(shape, dtype=torch.bool),
        next_action_masks=torch.tensor([True, False]).expand(*shape, 2).clone(),
        loss_mask=torch.tensor([[False, False, True]]) if recurrent else torch.ones(shape, dtype=torch.bool),
        lengths=torch.tensor([3 if recurrent else 1]),
        unit_ids=torch.tensor([23]),
        weights=torch.ones(1, dtype=torch.float64),
        sampling=receipt(),
    )


@pytest.mark.parametrize("poison", [float("-inf"), float("nan"), 1e30])
def test_terminal_empty_mask_is_finite(poison):
    _, qt = api()
    values = torch.full((1, 2), poison, requires_grad=True)
    masks = torch.zeros((1, 2), dtype=torch.bool)
    done = torch.ones(1, dtype=torch.bool)
    for double in (False, True):
        out = qt.legal_bootstrap(values, values, masks, ~done, double_dqn=double)
        assert out.shape == (1,) and out.item() == 0 and not out.requires_grad
        target = qt.legal_td_target(torch.tensor([7.0]), done, values, values, masks, gamma=1.0, double_dqn=double)
        assert target.item() == 7 and torch.isfinite(target).all()


def test_nonterminal_empty_mask_refuses():
    rc, qt = api()
    masks = torch.zeros((1, 2), dtype=torch.bool)
    done = torch.zeros(1, dtype=torch.bool)
    for validate in (rc.validate_successor_masks, qt.validate_successor_masks):
        with pytest.raises(ValueError, match="nonterminal"):
            validate(masks, done, action_dim=2)
    with pytest.raises(ValueError, match="nonterminal"):
        qt.legal_bootstrap(None, torch.zeros(1, 2), masks, ~done, double_dqn=False)


def test_double_uses_online_legal_choice():
    _, qt = api()
    online = torch.tensor([[8.0, 2.0, 1000.0]], requires_grad=True)
    target = torch.tensor([[4.0, 10.0, float("nan")]], requires_grad=True)
    legal = torch.tensor([[True, True, False]])
    done = torch.tensor([False])
    double = qt.legal_td_target(torch.tensor([1.0]), done, online, target, legal, gamma=0.5, double_dqn=True)
    standard = qt.legal_td_target(torch.tensor([1.0]), done, None, target, legal, gamma=0.5, double_dqn=False)
    assert double.item() == 3.0 and standard.item() == 6.0
    assert not double.requires_grad and not standard.requires_grad
    assert online.grad is None and target.grad is None


def test_historical_mask_changes_wrong_direction_update():
    _, qt = api()
    target_q = torch.tensor([[4.0, 100.0]], requires_grad=True)
    historical_legal = torch.tensor([[True, False]])
    target = qt.legal_td_target(torch.tensor([1.0]), torch.tensor([False]), None, target_q, historical_legal, gamma=0.5, double_dqn=False)
    prediction = torch.tensor([[10.0, 40.0]], requires_grad=True)
    selected = prediction.gather(1, torch.tensor([[0]])).squeeze(1)
    ((selected - target) ** 2).mean().backward()
    assert target.item() == 3.0  # Unmasked target51 would push10 upwards.
    assert prediction.grad.tolist() == [[14.0, 0.0]]
    assert target_q.grad is None


@pytest.mark.parametrize("double", [False, True])
def test_recurrent_real_bootstrap_and_gamma_zero(double):
    _, qt = api()
    q = torch.tensor([[[4.0, float("nan")], [float("nan"), float("-inf")], [float("nan"), float("nan")]]])
    legal = torch.tensor([[[True, False], [False, False], [False, False]]])
    bootstrap = torch.tensor([[True, False, False]])
    result = qt.legal_bootstrap(q, q, legal, bootstrap, double_dqn=double)
    assert result.tolist() == [[4.0, 0.0, 0.0]]
    poisoned = torch.full((1, 2), float("nan"))
    out = qt.legal_td_target(
        torch.tensor([2.0]), torch.tensor([False]), poisoned, poisoned, torch.tensor([[True, False]]), gamma=0, double_dqn=double
    )
    assert out.item() == 2.0


@pytest.mark.parametrize("gamma", [-0.1, 1.1, float("nan"), float("inf"), True])
def test_gamma_domain(gamma):
    _, qt = api()
    with pytest.raises((TypeError, ValueError), match="gamma"):
        qt.legal_td_target(
            torch.tensor([1.0]),
            torch.tensor([False]),
            None,
            torch.ones(1, 2),
            torch.ones(1, 2, dtype=torch.bool),
            gamma=gamma,
            double_dqn=False,
        )


def test_target_validation_and_no_input_mutation():
    _, qt = api()
    q = torch.tensor([[4.0, 100.0]])
    legal = torch.tensor([[True, False]])
    active = torch.tensor([True])
    before = q.clone()
    with pytest.raises(ValueError, match="q_online"):
        qt.legal_bootstrap(None, q, legal, active, double_dqn=True)
    with pytest.raises((TypeError, ValueError), match="legal"):
        qt.legal_bootstrap(None, q, legal.float(), active, double_dqn=False)
    with pytest.raises(ValueError, match="shape"):
        qt.legal_bootstrap(None, q, legal, torch.ones(1, 1, dtype=torch.bool), double_dqn=False)
    with pytest.raises(ValueError, match="finite"):
        qt.legal_bootstrap(None, torch.tensor([[float("nan"), 1.0]]), legal, active, double_dqn=False)
    assert torch.equal(q, before) and legal.tolist() == [[True, False]]


@pytest.mark.parametrize("recurrent", [False, True])
def test_batch_owns_historical_values_without_recomposing_rewards(recurrent):
    original = batch(recurrent)
    copied = replace(original)
    original.observations.fill_(99)
    original.next_action_masks.fill_(False)
    original.rewards.fill_(-4)
    assert copied.observations.sum() == 0
    assert copied.next_action_masks[..., 0].all()
    assert copied.rewards.eq(1).all() and copied.rewards_intrinsic.eq(17).all()
    assert copied.rewards_extrinsic is None and copied.rewards_shaping is None
    assert copied.unit_ids.tolist() == [23]


def test_legality_provenance_covers_real_non_loss_rows():
    rc, _ = api()
    original = batch(True)
    provenance = original.legality_recorded.clone()
    provenance[0, 0] = False  # Real history despite anchor-only loss.
    with pytest.raises(rc.HistoricalLegalityUnavailable, match="archiv"):
        replace(original, legality_recorded=provenance)
    with pytest.raises((TypeError, ValueError), match="next_action_masks"):
        replace(original, next_action_masks=None)
    masks = original.next_action_masks.clone()
    masks[0, 0] = False
    with pytest.raises(ValueError, match="nonterminal"):
        replace(original, next_action_masks=masks)


def test_padding_is_transport_not_experience():
    original = batch(True)
    provenance = torch.tensor([[True, False, False]])
    masks = torch.tensor([[[True, False], [False, False], [False, False]]])
    padded = replace(
        original,
        lengths=torch.tensor([1]),
        loss_mask=torch.tensor([[True, False, False]]),
        legality_recorded=provenance,
        next_action_masks=masks,
    )
    assert padded.lengths.tolist() == [1]
    with pytest.raises(ValueError, match="loss_mask"):
        replace(padded, loss_mask=torch.tensor([[True, True, False]]))
    with pytest.raises(ValueError, match="lengths"):
        replace(padded, lengths=torch.tensor([0]))
    with pytest.raises(ValueError, match="actions"):
        replace(padded, actions=torch.ones(1, 3))


def test_batch_and_receipt_reject_corruption_without_mutation():
    original = batch(False)
    with pytest.raises(ValueError, match="rewards"):
        replace(original, rewards=torch.tensor([float("nan")]))
    with pytest.raises(ValueError, match="actions"):
        replace(original, actions=torch.tensor([2]))
    with pytest.raises(ValueError, match="shape"):
        replace(original, next_observations=torch.zeros(1, 3))
    sampled = receipt()
    weights = np.array([1.0], dtype=np.float64)
    owned = replace(sampled, weights=weights)
    weights[0] = 8
    assert owned.weights.tolist() == [1.0]
    with pytest.raises(ValueError, match="indices"):
        replace(sampled, indices=np.array([0], dtype=np.int32))
    with pytest.raises(ValueError, match="weights"):
        replace(sampled, weights=np.array([1.0], dtype=np.float32))
    with pytest.raises(ValueError, match="probabilities"):
        replace(sampled, conditional_draw_probabilities=np.array([0.0], dtype=np.float64))
    assert sampled.indices.tolist() == [0] and original.rewards.tolist() == [1.0]


def test_request_readiness_diagnostics_are_typed():
    rc, _ = api()
    request = rc.ReplayRequest(1, 8, 0, "uniform_without_replacement", "adaptive_prefix", "anchor_transition")
    assert request.sequence_length == 8
    ready = rc.ReplayReadiness(False, 1, 0, "capacity_window_impossible")
    assert ready.retained_transitions == 1 and ready.sampleable_units == 0
    with pytest.raises(ValueError, match="batch_size"):
        replace(request, batch_size=True)
    with pytest.raises(ValueError, match="ready"):
        replace(ready, ready=True)


def test_invalid_target_geometry_is_diagnostic():
    _, qt = api()
    with pytest.raises(ValueError, match="q_target"):
        qt.legal_td_target(
            torch.ones(1),
            torch.zeros(1, dtype=torch.bool),
            None,
            torch.tensor(4.0),
            torch.ones(1, 1, dtype=torch.bool),
            gamma=0.5,
            double_dqn=False,
        )


def test_batch_owns_receipt_and_refuses_post_terminal_experience():
    original = batch(True)
    producer = receipt()
    owned = replace(original, sampling=producer)
    producer.indices.setflags(write=True)
    producer.indices[0] = 5
    assert owned.sampling.indices.tolist() == [0]


def test_refuses_post_terminal_experience():
    original = batch(True)
    with pytest.raises(ValueError, match="terminal"):
        replace(original, dones=torch.tensor([[True, False, False]]))


@pytest.mark.parametrize("field", ["observations", "rewards", "rewards_intrinsic", "weights"])
def test_batch_preserves_storage_and_estimator_dtypes(field):
    original = batch(False)
    wrong = getattr(original, field).double()
    if field == "weights":
        wrong = wrong.float()
    changes = {field: wrong}
    if field == "observations":
        changes["next_observations"] = original.next_observations.double()
    with pytest.raises(ValueError, match=field):
        replace(original, **changes)


def test_batch_weights_are_exact_receipt_weights():
    original = batch(False)
    with pytest.raises(ValueError, match="weights"):
        replace(original, weights=torch.tensor([1.000000001], dtype=torch.float64))
