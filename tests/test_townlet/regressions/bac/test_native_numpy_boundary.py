"""Native replay arrays retain strict type and ownership at receipt boundaries."""

import numpy as np
import pytest

from townlet.config.world_roster import WorldRecord, frozen_value, owned_value, same_value


def test_nested_numpy_receipt_owns_inputs_and_each_public_read() -> None:
    priorities = np.array([0.25, 0.5], dtype=np.float32)
    unit_ids = np.array([3, 4], dtype=np.int64)
    source = {"transport": [{"priorities": priorities}, (unit_ids,)]}
    record = WorldRecord("native-replay", object(), 0, frozen_value(source))
    priorities[:] = 9
    unit_ids[:] = -1
    source["transport"].clear()
    expected = {"transport": [{"priorities": np.array([0.25, 0.5], dtype=np.float32)}, (np.array([3, 4], dtype=np.int64),)]}
    assert same_value(record.payload, expected) is True
    payload = record.payload
    attribute = record.transport
    assert isinstance(payload["transport"], list)
    assert isinstance(payload["transport"][1], tuple)
    assert not np.shares_memory(payload["transport"][0]["priorities"], attribute[0]["priorities"])
    payload["transport"][0]["priorities"][:] = 22
    payload["transport"][1][0][:] = 23
    attribute[0]["priorities"][:] = 24
    attribute[1][0][:] = 25
    assert same_value(record.payload, expected) is True
    assert same_value(record.transport, expected["transport"]) is True


@pytest.mark.parametrize("dtype", [np.bool_, np.int64, np.uint64, np.float32, np.complex128])
@pytest.mark.parametrize("shape", ["strided", "scalar", "empty"])
def test_plain_numeric_array_copy_preserves_dtype_shape_and_values(dtype: type, shape: str) -> None:
    if shape == "strided":
        source = np.array([[0, 1], [1, 0], [0, 1]], dtype=dtype)[::2, ::-1]
    elif shape == "scalar":
        source = np.array(1, dtype=dtype)
    else:
        source = np.empty((0, 2), dtype=dtype)
    source.flags.writeable = False
    copied = owned_value(source)
    assert type(copied) is np.ndarray
    assert copied is not source
    assert copied.dtype == source.dtype
    assert copied.shape == source.shape
    assert not np.shares_memory(copied, source)
    assert copied.flags.writeable
    assert same_value(copied, source) is True


@pytest.mark.parametrize(
    "other",
    [
        np.array([1, 2], dtype=np.float32),
        np.array([[1, 2]], dtype=np.int64),
        np.array([1, 3], dtype=np.int64),
        np.array([1, 2], dtype=">i8"),
        [1, 2],
        1,
        None,
    ],
)
def test_numpy_equality_rejects_dtype_shape_content_and_type_mismatches(other: object) -> None:
    source = np.array([1, 2], dtype="<i8")
    assert same_value(source, other) is False
    assert same_value(other, source) is False


@pytest.mark.parametrize(
    "value",
    [
        np.array([object()], dtype=object),
        np.array(["text"]),
        np.array([b"text"]),
        np.array([("2026-11-14",)], dtype=[("date", "datetime64[D]")]),
        np.array([1], dtype="timedelta64[D]"),
        np.array([1], dtype=np.dtype(np.int64, metadata={"mutable": []})),
    ],
)
def test_non_numeric_or_metadata_arrays_are_refused(value: np.ndarray) -> None:
    for copy_value in (owned_value, frozen_value):
        with pytest.raises(ValueError, match="plain numeric ndarrays"):
            copy_value({"nested": [value]})
    assert same_value(value, value) is False
    assert same_value(value, np.array([1])) is False
    assert same_value(np.array([1]), value) is False


def test_numpy_subclasses_are_refused_without_custom_hooks() -> None:
    class HookedArray(np.ndarray):
        def copy(self, *args: object, **kwargs: object) -> np.ndarray:
            pytest.fail("subclass copy hook must not run")

        def __array_function__(self, *args: object, **kwargs: object) -> object:
            pytest.fail("subclass NumPy hook must not run")

        def __eq__(self, other: object) -> object:
            pytest.fail("subclass equality hook must not run")

    value = np.array([1, 2], dtype=np.int64).view(HookedArray)
    for copy_value in (owned_value, frozen_value):
        with pytest.raises(ValueError, match="plain numeric ndarrays"):
            copy_value(value)
    plain = np.array([1, 2], dtype=np.int64)
    assert same_value(value, plain) is False
    assert same_value(plain, value) is False
    assert same_value(value, value) is False
