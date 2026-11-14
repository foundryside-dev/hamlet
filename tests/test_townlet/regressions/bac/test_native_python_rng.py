"""Native capture must retain Python replay draws without changing live streams."""

import random
from typing import Any

import pytest
import torch

from townlet.training.native_rng import NativeRNGState, validate_native_rng_payload


class HostileTuple(tuple):
    def __iter__(self) -> Any:
        raise AssertionError("Untrusted tuple behavior invoked")

    def __len__(self) -> int:
        raise AssertionError("Untrusted tuple behavior invoked")


def test_capture_and_validation_preserve_python_and_torch_and_own_payload() -> None:
    owner = NativeRNGState(cuda_devices=())
    python_before = random.getstate()
    torch_before = torch.get_rng_state().clone()
    payload = owner.capture()
    assert payload["python"] == python_before
    owned = owner.validate_payload(payload)
    assert random.getstate() == python_before
    assert torch.equal(torch.get_rng_state(), torch_before)
    expected = random.Random(0)
    expected.setstate(python_before)
    detached = random.Random(0)
    detached.setstate(owned["python"])
    assert [detached.random() for _ in range(12)] == [expected.random() for _ in range(12)]
    payload["python"] = random.Random(712).getstate()
    payload["torch_cpu"].zero_()
    assert owned["python"] == python_before
    assert torch.equal(owned["torch_cpu"], torch_before)
    assert random.getstate() == python_before
    assert torch.equal(torch.get_rng_state(), torch_before)


@pytest.mark.parametrize(
    "bad_state",
    [
        None,
        [],
        HostileTuple((3, (), None)),
        (True, (0,) * 624 + (624,), None),
        (2, (0,) * 624 + (624,), None),
        (3, HostileTuple((0,) * 624 + (624,)), None),
        (3, [0] * 625, None),
        (3, (0,) * 624, None),
        (3, (True,) + (0,) * 623 + (624,), None),
        (3, (-1,) + (0,) * 623 + (624,), None),
        (3, (2**32,) + (0,) * 623 + (624,), None),
        (3, (0,) * 624 + (-1,), None),
        (3, (0,) * 624 + (625,), None),
        (3, (0,) * 624 + (True,), None),
        (3, (0,) * 624 + (624,), True),
        (3, (0,) * 624 + (624,), 1),
        (3, (0,) * 624 + (624,), float("nan")),
        (3, (0,) * 624 + (624,), float("inf")),
    ],
)
def test_malformed_python_state_refused_without_live_mutation(bad_state: Any) -> None:
    owner = NativeRNGState(cuda_devices=())
    payload = owner.capture()
    python_before = random.getstate()
    torch_before = torch.get_rng_state().clone()
    payload["python"] = bad_state
    with pytest.raises(ValueError):
        validate_native_rng_payload(payload, cuda_devices=())
    with pytest.raises(ValueError):
        owner.validate_payload(payload)
    assert random.getstate() == python_before
    assert torch.equal(torch.get_rng_state(), torch_before)


def test_python_gaussian_cache_is_preserved_by_detached_validation() -> None:
    source = random.Random(72)
    source.gauss(0, 1)
    owner = NativeRNGState(cuda_devices=())
    payload = owner.capture()
    python_before = random.getstate()
    torch_before = torch.get_rng_state().clone()
    payload["python"] = source.getstate()
    owned = owner.validate_payload(payload)
    detached = random.Random(0)
    detached.setstate(owned["python"])
    assert detached.gauss(0, 1) == source.gauss(0, 1)
    assert random.getstate() == python_before
    assert torch.equal(torch.get_rng_state(), torch_before)


def test_python_state_is_required_without_old_schema_fallback() -> None:
    owner = NativeRNGState(cuda_devices=())
    payload = owner.capture()
    del payload["python"]
    with pytest.raises(ValueError):
        owner.validate_payload(payload)
    payload["schema"] = "native-rng-v1"
    with pytest.raises(ValueError):
        owner.validate_payload(payload)
