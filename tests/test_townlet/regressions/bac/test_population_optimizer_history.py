"""Component controls from real CPU Torch updates, not native POP install evidence."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
import torch

from townlet.population.vectorized import VectorizedPopulation

KINDS = ("adam", "adamw", "rmsprop", "sgd", "sgd_momentum")


def _history(kind: str, *, trained: bool):
    model = torch.nn.Module()
    for name in ("early", "late", "never"):
        model.register_parameter(name, torch.nn.Parameter(torch.tensor([1.0, 2.0])))
    # Intentionally unlike named_parameters order: history belongs to optimizer order.
    groups = [{"params": [model.late, model.never]}, {"params": [model.early]}]
    if kind == "adam":
        optimizer = torch.optim.Adam(groups, lr=0.01)
    elif kind == "adamw":
        optimizer = torch.optim.AdamW(groups, lr=0.01)
    elif kind == "rmsprop":
        optimizer = torch.optim.RMSprop(groups, lr=0.01)
    else:
        optimizer = torch.optim.SGD(groups, lr=0.01, momentum=0.9 if kind == "sgd_momentum" else 0.0)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
    initial_epoch = scheduler.last_epoch
    if trained:
        optimizer.zero_grad(set_to_none=True)
        model.early.square().sum().backward()
        assert model.late.grad is None and model.never.grad is None
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad(set_to_none=True)
        (model.early.sum() * 0.0 + model.late.square().sum()).backward()
        assert torch.equal(model.early.grad, torch.zeros_like(model.early))
        assert model.never.grad is None
        optimizer.step()
        scheduler.step()
    # Only real optimizer/scheduler plus independently captured constructor baseline.
    host = SimpleNamespace(optimizer=optimizer, scheduler=scheduler, initial_epoch=initial_epoch)
    checkpoint = {
        "training_step_counter": 2 if trained else 0,
        # Explicit oracle from the two losses above, not copied from production counters.
        "optimizer_parameter_updates": [1, 0, 2] if trained else [0, 0, 0],
        "optimizer": deepcopy(optimizer.state_dict()),
        "scheduler": deepcopy(scheduler.state_dict()),
    }
    return host, checkpoint


def _validate(host, checkpoint):
    learning_rates = VectorizedPopulation._validate_optimizer_checkpoint_state("optimizer", checkpoint["optimizer"], host.optimizer)
    VectorizedPopulation._validate_scheduler_checkpoint_state("scheduler", checkpoint["scheduler"], host.scheduler, learning_rates)
    VectorizedPopulation._validate_optimizer_update_history(
        checkpoint, optimizer=host.optimizer, scheduler_initial_epoch=host.initial_epoch
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("trained", (False, True), ids=("initial", "lazy_trained"))
def test_actual_optimizer_history_accepts_initial_and_lazy_parameters(kind, trained):
    host, checkpoint = _history(kind, trained=trained)
    state = checkpoint["optimizer"]["state"]
    groups = checkpoint["optimizer"]["param_groups"]
    late, never = groups[0]["params"]
    early = groups[1]["params"][0]
    if not trained or kind == "sgd":
        assert state == {}
    else:
        assert set(state) == {early, late}
        assert never not in state
        if kind == "sgd_momentum":
            assert all(set(value) == {"momentum_buffer"} for value in state.values())
        else:
            assert state[early]["step"].item() == 2
            assert state[late]["step"].item() == 1
    _validate(host, checkpoint)


def test_stateless_sgd_accepts_explicit_empty_parameter_mappings():
    host, checkpoint = _history("sgd", trained=True)
    checkpoint["optimizer"]["state"] = {
        parameter_id: {} for group in checkpoint["optimizer"]["param_groups"] for parameter_id in group["params"]
    }
    _validate(host, checkpoint)


@pytest.mark.parametrize(
    "counts",
    ([True, 0, 2], [1.0, 0, 2], [-1, 0, 2], [1, 0], [1, 0, 2, 0], (1, 0, 2), [1, 0, 3], [0, 0, 0], [2, 0, 1]),
    ids=("bool", "float", "negative", "short", "long", "tuple", "above_global", "no_participation", "wrong_parameter"),
)
def test_actual_adam_history_rejects_invalid_counts(counts):
    host, checkpoint = _history("adam", trained=True)
    checkpoint["optimizer_parameter_updates"] = counts
    with pytest.raises(ValueError):
        _validate(host, checkpoint)


@pytest.mark.parametrize("kind", ("adam", "adamw", "rmsprop", "sgd_momentum"))
@pytest.mark.parametrize("corruption", ("missing_participant", "populated_never"))
def test_lazy_state_must_agree_with_real_participation(kind, corruption):
    host, checkpoint = _history(kind, trained=True)
    state = checkpoint["optimizer"]["state"]
    late, never = checkpoint["optimizer"]["param_groups"][0]["params"]
    if corruption == "missing_participant":
        del state[late]
    else:
        state[never] = deepcopy(state[late])
    with pytest.raises(ValueError, match="lazy state"):
        _validate(host, checkpoint)


@pytest.mark.parametrize("kind", ("adam", "adamw", "rmsprop"))
@pytest.mark.parametrize("step", (0.0, 1.5, 3.0))
def test_actual_adaptive_optimizer_rejects_invalid_step(kind, step):
    host, checkpoint = _history(kind, trained=True)
    early = checkpoint["optimizer"]["param_groups"][1]["params"][0]
    checkpoint["optimizer"]["state"][early]["step"].fill_(step)
    with pytest.raises(ValueError):
        _validate(host, checkpoint)


def test_initial_history_cannot_claim_parameter_updates():
    host, checkpoint = _history("adam", trained=False)
    checkpoint["optimizer_parameter_updates"] = [1, 0, 0]
    with pytest.raises(ValueError, match="exceed"):
        _validate(host, checkpoint)


def test_scheduler_rewind_rejected_against_constructor_baseline():
    host, checkpoint = _history("adam", trained=True)
    assert checkpoint["scheduler"]["last_epoch"] == host.initial_epoch + 2
    checkpoint["scheduler"]["last_epoch"] -= 1
    checkpoint["scheduler"]["_step_count"] -= 1
    with pytest.raises(ValueError, match="epoch disagrees"):
        _validate(host, checkpoint)
