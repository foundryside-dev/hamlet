"""Inspect native sampler mass and the producer-owned eligibility boundary."""

import pytest
import torch

from townlet.exploration import action_selection as selection


@pytest.mark.parametrize("strict", [False, True])
def test_disabled_mass_exact_zero(monkeypatch, strict):
    weights = []
    native = torch.multinomial

    def capture(probs, num_samples):
        weights.append(probs.clone())
        return native(probs, num_samples)

    monkeypatch.setattr(torch, "multinomial", capture)
    q = torch.tensor([[100.0, 1.0]])
    masks = torch.tensor([[False, True]])
    for epsilon in (1.0, 0.0):
        if strict:
            actions = selection.epsilon_greedy_action_selection_eligible(q, torch.tensor([epsilon]), masks, eligible=torch.tensor([True]))
        else:
            actions = selection.epsilon_greedy_action_selection(q, torch.tensor([epsilon]), masks)
        assert actions.tolist() == [1]
    assert weights
    for probs in weights:
        assert torch.equal(probs, torch.tensor([[0.0, 1.0]]))


def test_live_empty_mask_diagnoses(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("live-empty rows must fail before sampling")

    monkeypatch.setattr(torch, "multinomial", forbidden)
    for epsilon in (0.0, 1.0):
        with pytest.raises(ValueError, match="eligible.*no legal actions"):
            selection.epsilon_greedy_action_selection_eligible(
                torch.tensor([[100.0, 1.0]]), torch.tensor([epsilon]), torch.zeros(1, 2, dtype=torch.bool), eligible=torch.tensor([True])
            )


@pytest.mark.parametrize("strict", [False, True])
def test_mixed_epsilons_dead_transport_and_native_mass(monkeypatch, strict):
    weights = []
    native = torch.multinomial

    def capture(probs, num_samples):
        weights.append(probs.clone())
        return native(probs, num_samples)

    monkeypatch.setattr(torch, "multinomial", capture)
    q = torch.tensor([[100.0, 1.0, 2.0], [3.0, 100.0, 2.0], [100.0, 1.0, 2.0], [1.0, 2.0, 100.0]])
    masks = torch.tensor([[False, True, True], [True, False, True], [False, True, True], [False, False, False]])
    eps = torch.tensor([0.0, 0.5, 1.0, 1.0])
    if strict:
        actions = selection.epsilon_greedy_action_selection_eligible(q, eps, masks, eligible=torch.tensor([True, True, True, False]))
    else:
        actions = selection.epsilon_greedy_action_selection(q, eps, masks)
    assert actions[0] == 2
    assert masks[:3].gather(1, actions[:3, None]).all()
    assert actions[3] == 2
    assert len(weights) == 1
    assert torch.equal(weights[0], masks[:3].float() / 2)


@pytest.mark.parametrize("unmasked", [False, True])
def test_explicit_inactive_rows_never_sample(monkeypatch, unmasked):
    def forbidden(*args, **kwargs):
        pytest.fail("inactive rows must not sample")

    monkeypatch.setattr(torch, "multinomial", forbidden)
    monkeypatch.setattr(torch, "randint", forbidden)
    q = torch.tensor([[1.0, 5.0]])
    masks = None if unmasked else torch.ones(1, 2, dtype=torch.bool)
    actions = selection.epsilon_greedy_action_selection_eligible(q, torch.ones(1), masks, eligible=torch.tensor([False]))
    assert actions.tolist() == [1]


def test_explicit_unmasked_selection():
    q = torch.tensor([[1.0, 5.0], [5.0, 1.0]])
    actions = selection.epsilon_greedy_action_selection_eligible(q, torch.zeros(2), None, eligible=torch.ones(2, dtype=torch.bool))
    assert actions.tolist() == [1, 0]


@pytest.mark.parametrize("eligible", [torch.tensor([1]), torch.tensor([[True]]), torch.tensor([True, False])])
def test_eligibility_shape_and_dtype(eligible):
    with pytest.raises(ValueError, match="eligible"):
        selection.epsilon_greedy_action_selection_eligible(torch.ones(1, 2), torch.ones(1), None, eligible=eligible)
