"""Outer native RNG state must be owned and validated before publication.

These component controls do not replace the fresh DemoRunner continuation proof.
"""

import copy
import importlib
import random

import pytest
import torch

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import compiled as compiled
from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import make_parent
from townlet.exploration.rng_custody import process_rng_domain


def test_schema_validation_requires_no_domain_operation_or_rng_change():
    module = importlib.import_module("townlet.training.native_rng")
    payload = {"schema": "native-rng-v2", "python": random.getstate(), "torch_cpu": torch.get_rng_state().clone(), "torch_cuda": {}}
    domain = process_rng_domain()
    before = domain.status()
    state = torch.get_rng_state().clone()
    module.validate_native_rng_payload(payload, cuda_devices=())
    assert domain.status() == before
    assert torch.equal(torch.get_rng_state(), state)
    payload["torch_cpu"] = payload["torch_cpu"].long()
    with pytest.raises(ValueError):
        module.validate_native_rng_payload(payload, cuda_devices=())
    assert domain.status() == before


def native_owner():
    module = importlib.import_module("townlet.training.native_rng")
    return module.NativeRNGState(cuda_devices=())


def test_capture_preserves_ambient_stream_and_returns_owned_portable_state():
    owner = native_owner()
    before = torch.get_rng_state().clone()
    payload = owner.capture()
    assert torch.equal(torch.get_rng_state(), before)
    assert set(payload) == {"schema", "python", "torch_cpu", "torch_cuda"}
    assert payload["schema"] == "native-rng-v2"
    assert payload["torch_cuda"] == {}
    assert torch.equal(payload["torch_cpu"], before)
    payload["torch_cpu"].zero_()
    assert torch.equal(torch.get_rng_state(), before)
    assert torch.equal(owner.capture()["torch_cpu"], before)


def test_validation_owns_bytes_and_does_not_rewind_the_process():
    owner = native_owner()
    incoming = owner.capture()
    torch.rand(7)
    current = torch.get_rng_state().clone()
    validated = owner.validate_payload(incoming)
    assert torch.equal(torch.get_rng_state(), current)
    expected = incoming["torch_cpu"].clone()
    incoming["torch_cpu"].zero_()
    assert torch.equal(validated["torch_cpu"], expected)


@pytest.mark.parametrize("damage", ["schema", "extra", "dtype", "shape", "state", "devices", "bool_device"])
def test_bad_state_refuses_before_any_global_generator_changes(damage):
    owner = native_owner()
    incoming = owner.capture()
    if damage == "schema":
        incoming["schema"] = "unknown"
    elif damage == "extra":
        incoming["unexpected"] = 1
    elif damage == "dtype":
        incoming["torch_cpu"] = incoming["torch_cpu"].long()
    elif damage == "shape":
        incoming["torch_cpu"] = incoming["torch_cpu"].reshape(1, -1)
    elif damage == "state":
        incoming["torch_cpu"] = torch.zeros(3, dtype=torch.uint8)
    elif damage == "devices":
        incoming["torch_cuda"] = {0: incoming["torch_cpu"].clone()}
    else:
        incoming["torch_cuda"] = {False: incoming["torch_cpu"].clone()}
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        owner.validate_payload(incoming)
    assert torch.equal(torch.get_rng_state(), before)


def test_arbitrary_parent_cannot_turn_valid_bytes_into_restore_authority():
    owner = native_owner()
    payload = owner.capture()
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        owner.prepare(payload, parent=object(), parent_plan=object())
    assert torch.equal(torch.get_rng_state(), before)


@pytest.mark.parametrize("devices", [(True,), (-1,), (1, 0), (0, 0), [0]])
def test_device_inventory_is_exact_before_runtime_initialization(devices):
    module = importlib.import_module("townlet.training.native_rng")
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        module.NativeRNGState(cuda_devices=devices)
    assert torch.equal(torch.get_rng_state(), before)


def native_plan(compiled):
    source = make_parent(compiled)
    checkpoint = source.population.get_checkpoint_state()
    target = make_parent(compiled)
    target.bind()
    plan = target.population.prepare_native_checkpoint_data(checkpoint, mode="initial")
    return target, plan


def test_real_parent_can_stage_without_rewinding_but_cannot_install_outside_finalizer(compiled):
    owner = native_owner()
    payload = owner.capture()
    target, plan = native_plan(compiled)
    before = torch.get_rng_state().clone()
    prepared = owner.prepare(payload, parent=target.population, parent_plan=plan)
    assert torch.equal(torch.get_rng_state(), before)
    with pytest.raises((ValueError, RuntimeError)):
        owner.install(prepared=prepared, parent_plan=plan, attempt=object(), restored=object())
    assert torch.equal(torch.get_rng_state(), before)
    with pytest.raises(TypeError):
        copy.copy(prepared)


def test_staged_data_cannot_be_reassociated_with_another_real_parent_plan(compiled):
    owner = native_owner()
    target, plan = native_plan(compiled)
    prepared = owner.prepare(owner.capture(), parent=target.population, parent_plan=plan)
    other, other_plan = native_plan(compiled)
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        owner.install(prepared=prepared, parent_plan=other_plan, attempt=object(), restored=object())
    assert torch.equal(torch.get_rng_state(), before)
    assert other.population is not target.population


@pytest.mark.parametrize("method", ["clone", "is_contiguous"])
@pytest.mark.parametrize("route", ["schema", "owned"])
def test_plain_tensor_instance_override_is_refused_without_running_callback(method, route):
    module = importlib.import_module("townlet.training.native_rng")
    owner = native_owner()
    payload = owner.capture()
    tensor = payload["torch_cpu"]
    calls = []

    def overridden():
        calls.append(method)
        if method == "clone":
            return tensor
        return True

    setattr(tensor, method, overridden)
    assert type(tensor) is torch.Tensor
    before = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        if route == "schema":
            module.validate_native_rng_payload(payload, cuda_devices=())
        else:
            owner.validate_payload(payload)
    assert calls == []
    assert torch.equal(torch.get_rng_state(), before)
