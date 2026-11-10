# Actual R1 candidate review

Base b954c812dc0e92044eb3cab503b371e3346b48a4; tree fc9be745ab293003ab8f69a8ad7dd52c23a48f2a. Scope4wholefiles/2729actual lines including RP/RNGreadonly. Allsource/index/trackeddocsfrozen.

```diff
diff --git a/src/townlet/exploration/world_curiosity_state.py b/src/townlet/exploration/world_curiosity_state.py
index d0f27d2d..e54acc27 100644
--- a/src/townlet/exploration/world_curiosity_state.py
+++ b/src/townlet/exploration/world_curiosity_state.py
@@ -59,6 +59,118 @@ def derive_world_seed(*, training_seed: int, world_id: str, provider_kind: str,
     return int(digest[:16], 16) & (2**63 - 1)
 
 
+@dataclass(frozen=True)
+class ServiceClock:
+    """Typed service position; live scheduling authority belongs to its owner."""
+
+    unit: Literal["vector_tick", "world_eligible_admission"]
+    position: int
+
+    def __post_init__(self) -> None:
+        if type(self.unit) is not str or self.unit not in ("vector_tick", "world_eligible_admission"):
+            raise ValueError("service clock unit must be an exact supported string")
+        _integer(self.position, "position", 0)
+
+
+@dataclass(frozen=True)
+class CuriosityEventId:
+    """Exact accepted-episode identity; eligible_seq zero marks no admission yet.
+
+    This value does not authenticate ENV acceptance or allocate live cursors.
+    An inactive row may retain the ID of its latest eligible admission.
+    """
+
+    curiosity_epoch: int
+    world_id: str
+    world_episode_seq: int
+    eligible_seq: int
+
+    def __post_init__(self) -> None:
+        _integer(self.curiosity_epoch, "curiosity_epoch", 0)
+        if type(self.world_id) is not str or not self.world_id:
+            raise ValueError("world_id must be an exact nonempty string")
+        _integer(self.world_episode_seq, "world_episode_seq", 1)
+        _integer(self.eligible_seq, "eligible_seq", 0)
+
+
+@dataclass(frozen=True, init=False, eq=False)
+class CuriosityStepStamp:
+    """Owned all-row identity snapshot, with identity equality and no hashing.
+
+    Tensor access returns detached independent copies. Acceptance, actual-context
+    correlation, phase ordering and retry receipts remain live-owner duties.
+    Inputs must be quiescent while this cooperative snapshot is constructed.
+    """
+
+    __hash__ = None
+
+    event_ids: tuple[CuriosityEventId, ...]
+    world_ids: tuple[str, ...]
+    _world_episode_seqs: torch.Tensor
+    _eligible_seqs: torch.Tensor
+    _eligible: torch.Tensor
+
+    def __init__(
+        self,
+        *,
+        event_ids: tuple[CuriosityEventId, ...],
+        world_ids: tuple[str, ...],
+        world_episode_seqs: torch.Tensor,
+        eligible_seqs: torch.Tensor,
+        eligible: torch.Tensor,
+    ) -> None:
+        if type(world_ids) is not tuple or not world_ids or any(type(item) is not str or not item for item in world_ids):
+            raise ValueError("stamp world_ids must be an exact nonempty tuple of exact nonempty strings")
+        if len(set(world_ids)) != len(world_ids):
+            raise ValueError("stamp world_ids must be unique")
+        rows = len(world_ids)
+        if type(event_ids) is not tuple or len(event_ids) != rows or any(type(item) is not CuriosityEventId for item in event_ids):
+            raise ValueError("stamp event_ids must be an exact tuple of CuriosityEventId values matching all rows")
+        if len({item.curiosity_epoch for item in event_ids}) != 1:
+            raise ValueError("stamp rows must share one curiosity epoch")
+        inputs = (world_episode_seqs, eligible_seqs, eligible)
+        for value, dtype in zip(inputs, (torch.int64, torch.int64, torch.bool), strict=True):
+            if (
+                not isinstance(value, torch.Tensor)
+                or value.layout != torch.strided
+                or value.device.type not in ("cpu", "cuda")
+                or value.shape != (rows,)
+                or value.dtype != dtype
+            ):
+                raise ValueError("stamp tensors require dense CPU/CUDA [N] vectors with int64/int64/bool dtypes")
+        if any(value.device != world_episode_seqs.device for value in inputs):
+            raise ValueError("stamp tensors must share exactly one device")
+        episodes_owned, sequences_owned, eligible_owned = (value.detach().clone() for value in inputs)
+        if bool((episodes_owned < 1).any()) or bool((sequences_owned < 0).any()) or bool((eligible_owned & (sequences_owned < 1)).any()):
+            raise ValueError("stamp episodes must be positive and eligible admissions require a positive local sequence")
+        episodes = episodes_owned.tolist()
+        sequences = sequences_owned.tolist()
+        for index, event_id in enumerate(event_ids):
+            if (
+                event_id.world_id != world_ids[index]
+                or event_id.world_episode_seq != episodes[index]
+                or event_id.eligible_seq != sequences[index]
+            ):
+                raise ValueError("stamp event IDs must match exact ordered world/episode/eligible content")
+        object.__setattr__(self, "event_ids", event_ids)
+        object.__setattr__(self, "world_ids", world_ids)
+        object.__setattr__(self, "_world_episode_seqs", episodes_owned)
+        object.__setattr__(self, "_eligible_seqs", sequences_owned)
+        object.__setattr__(self, "_eligible", eligible_owned)
+
+    @property
+    def world_episode_seqs(self) -> torch.Tensor:
+        return self._world_episode_seqs.detach().clone()
+
+    @property
+    def eligible_seqs(self) -> torch.Tensor:
+        return self._eligible_seqs.detach().clone()
+
+    @property
+    def eligible(self) -> torch.Tensor:
+        return self._eligible.detach().clone()
+
+
 @dataclass(frozen=True)
 class WorldCuriosityDescriptor:
     """Immutable declared geometry, ID binding and canonical ID-keyed streams.
diff --git a/tests/test_townlet/regressions/bac/test_pw_clock_stamp.py b/tests/test_townlet/regressions/bac/test_pw_clock_stamp.py
new file mode 100644
index 00000000..d5bae7c7
--- /dev/null
+++ b/tests/test_townlet/regressions/bac/test_pw_clock_stamp.py
@@ -0,0 +1,317 @@
+"""Public data primitives; accepted identity and live cursors remain owner duties."""
+
+import random
+from dataclasses import FrozenInstanceError
+
+import numpy as np
+import pytest
+import torch
+
+from townlet.exploration import world_curiosity_state as ws
+
+
+class StringAlias(str):
+    pass
+
+
+class TupleAlias(tuple):
+    pass
+
+
+def _api():
+    names = ("ServiceClock", "CuriosityEventId", "CuriosityStepStamp")
+    for name in names:
+        assert hasattr(ws, name), f"Missing promised public clock/stamp ABI: {name}"
+    return tuple(getattr(ws, name) for name in names)
+
+
+def _inputs():
+    _, event_id, _ = _api()
+    # Explicit accepted-episode values are fixture data, not acceptance authority.
+    return {
+        "event_ids": (event_id(0, "world-a", 1, 1), event_id(0, "world-b", 2, 0)),
+        "world_ids": ("world-a", "world-b"),
+        "world_episode_seqs": torch.tensor([1, 2], dtype=torch.int64),
+        "eligible_seqs": torch.tensor([1, 0], dtype=torch.int64),
+        "eligible": torch.tensor([True, False], dtype=torch.bool),
+    }
+
+
+def _stamp(values):
+    _, _, stamp = _api()
+    return stamp(**values)
+
+
+def _assert_values(stamp, expected):
+    assert stamp.event_ids == expected["event_ids"]
+    assert stamp.world_ids == expected["world_ids"]
+    for name in ("world_episode_seqs", "eligible_seqs", "eligible"):
+        actual = getattr(stamp, name)
+        assert actual.dtype == expected[name].dtype
+        assert actual.device == expected[name].device
+        assert torch.equal(actual, expected[name])
+
+
+def test_service_clock_strict_typed_units():
+    clock, _, _ = _api()
+    for unit in ("vector_tick", "world_eligible_admission"):
+        for position in (0, 3, 2**80):
+            value = clock(unit, position)
+            assert (value.unit, value.position) == (unit, position)
+            assert value == clock(unit, position)
+            assert hash(value) == hash(clock(unit, position))
+            with pytest.raises(FrozenInstanceError):
+                value.position = 9
+    assert clock("vector_tick", 3) != clock("world_eligible_admission", 3)
+    for position in (True, False, 0.0, 1.0, np.int64(1), -1, "1", None):
+        with pytest.raises(ValueError):
+            clock("vector_tick", position)
+    for unit in ("unknown", "", None, 0, StringAlias("vector_tick")):
+        with pytest.raises(ValueError):
+            clock(unit, 0)
+
+
+def test_event_id_initial_and_exact_identity():
+    _, event_id, _ = _api()
+    for world in ("world-a", " ", "é", "e\u0301"):
+        value = event_id(0, world, 1, 0)
+        assert value.world_id == world
+        assert (value.curiosity_epoch, value.world_episode_seq, value.eligible_seq) == (0, 1, 0)
+        assert value == event_id(0, world, 1, 0)
+        assert hash(value) == hash(event_id(0, world, 1, 0))
+        with pytest.raises(FrozenInstanceError):
+            value.world_id = "changed"
+    assert event_id(0, "é", 1, 0) != event_id(0, "e\u0301", 1, 0)
+    assert event_id(0, "world-a", 1, 0) != event_id(0, "world-a ", 1, 0)
+    assert event_id(2**80, "world-a", 2**80, 2**80).eligible_seq == 2**80
+    original = (0, "world-a", 1, 0)
+    for index, invalid in (
+        (0, (-1, True, False, 0.0, np.int64(0), None)),
+        (1, ("", None, 1, StringAlias("world-a"))),
+        (2, (0, -1, True, 1.0, np.int64(1), None)),
+        (3, (-1, True, False, 0.0, np.int64(0), None)),
+    ):
+        for bad in invalid:
+            values = list(original)
+            values[index] = bad
+            with pytest.raises(ValueError):
+                event_id(*values)
+
+
+def test_step_stamp_first_eligible_and_inactive():
+    _, event_id, _ = _api()
+    values = _inputs()
+    stamp = _stamp(values)
+    _assert_values(stamp, values)
+    # An inactive row may retain a positive cursor; equality is no admission.
+    values["event_ids"] = (event_id(0, "world-a", 1, 1), event_id(0, "world-b", 2, 7))
+    values["eligible_seqs"] = torch.tensor([1, 7])
+    values["eligible"] = torch.tensor([False, False])
+    inactive = _stamp(values)
+    assert inactive.event_ids[0] == stamp.event_ids[0]
+    assert not inactive.eligible.any()
+    values["eligible"] = torch.tensor([True, True])
+    _assert_values(_stamp(values), values)
+    # No bootstrap episode0 stamp is manufactured; inactive local0 remains valid.
+    single = {
+        "event_ids": (event_id(0, "world-a", 1, 0),),
+        "world_ids": ("world-a",),
+        "world_episode_seqs": torch.tensor([1]),
+        "eligible_seqs": torch.tensor([0]),
+        "eligible": torch.tensor([False]),
+    }
+    _assert_values(_stamp(single), single)
+    single["eligible"] = torch.tensor([True])
+    with pytest.raises(ValueError):
+        _stamp(single)
+
+
+@pytest.mark.parametrize("field", ["event_ids", "world_ids"])
+@pytest.mark.parametrize("kind", ["list", "tuple_alias", "empty", "short", "long"])
+def test_step_stamp_sequence_refusals(field, kind):
+    values = _inputs()
+    original = values[field]
+    replacements = {
+        "list": list(original),
+        "tuple_alias": TupleAlias(original),
+        "empty": (),
+        "short": original[:1],
+        "long": original + original[:1],
+    }
+    values[field] = replacements[kind]
+    with pytest.raises(ValueError):
+        _stamp(values)
+
+
+@pytest.mark.parametrize(
+    "case", ["duplicate", "empty_id", "alias_id", "not_id", "id_alias", "mixed_epoch", "world", "episode", "local", "overflow"]
+)
+def test_step_stamp_all_row_identity_refusals(case):
+    _, event_id, _ = _api()
+    values = _inputs()
+    first = values["event_ids"][0]
+    if case == "duplicate":
+        values["world_ids"] = ("world-a", "world-a")
+        values["event_ids"] = (first, event_id(0, "world-a", 2, 0))
+    elif case == "empty_id":
+        values["world_ids"] = ("world-a", "")
+    elif case == "alias_id":
+        values["world_ids"] = ("world-a", StringAlias("world-b"))
+    elif case == "not_id":
+        values["event_ids"] = (first, (0, "world-b", 2, 0))
+    elif case == "id_alias":
+        class EventAlias(event_id):
+            pass
+
+        values["event_ids"] = (first, EventAlias(0, "world-b", 2, 0))
+    else:
+        replacement = {
+            "mixed_epoch": (1, "world-b", 2, 0),
+            "world": (0, "world-c", 2, 0),
+            "episode": (0, "world-b", 3, 0),
+            "local": (0, "world-b", 2, 1),
+            "overflow": (0, "world-b", 2**80, 0),
+        }[case]
+        values["event_ids"] = (first, event_id(*replacement))
+    with pytest.raises(ValueError):
+        _stamp(values)
+
+
+def test_step_stamp_all_row_order_and_geometry():
+    values = _inputs()
+    reversed_values = {
+        "event_ids": tuple(reversed(values["event_ids"])),
+        "world_ids": tuple(reversed(values["world_ids"])),
+        **{name: values[name].flip(0) for name in ("world_episode_seqs", "eligible_seqs", "eligible")},
+    }
+    _assert_values(_stamp(reversed_values), reversed_values)
+    values["event_ids"] = tuple(reversed(values["event_ids"]))
+    with pytest.raises(ValueError):
+        _stamp(values)
+    values = _inputs()
+    values["world_ids"] = tuple(reversed(values["world_ids"]))
+    with pytest.raises(ValueError):
+        _stamp(values)
+    values = _inputs()
+    values.update(event_ids=(), world_ids=())
+    for name in ("world_episode_seqs", "eligible_seqs", "eligible"):
+        values[name] = values[name][:0]
+    with pytest.raises(ValueError):
+        _stamp(values)
+
+
+@pytest.mark.parametrize("field", ["world_episode_seqs", "eligible_seqs", "eligible"])
+@pytest.mark.parametrize(
+    "kind", ["rank0", "rank2", "short", "long", "list", "none", "float", "int32", "wrong_bool", "meta", "sparse"]
+)
+def test_step_stamp_tensor_shape_dtype_layout_device(field, kind):
+    values = _inputs()
+    source = values[field]
+    replacements = {
+        "rank0": source[0],
+        "rank2": source.unsqueeze(0),
+        "short": source[:1],
+        "long": torch.cat((source, source[:1])),
+        "list": source.tolist(),
+        "none": None,
+        "float": source.float(),
+        "int32": source.to(torch.int32),
+        "wrong_bool": source.long() if field == "eligible" else source.bool(),
+        "meta": torch.empty(2, dtype=source.dtype, device="meta"),
+        "sparse": source.to_sparse(),
+    }
+    values[field] = replacements[kind]
+    with pytest.raises(ValueError):
+        _stamp(values)
+
+
+@pytest.mark.parametrize("field,bad", [("world_episode_seqs", 0), ("world_episode_seqs", -1), ("eligible_seqs", -1)])
+def test_step_stamp_tensor_domains_include_last_row(field, bad):
+    values = _inputs()
+    values[field][-1] = bad
+    with pytest.raises(ValueError):
+        _stamp(values)
+
+
+def test_step_stamp_owns_inputs_and_outputs():
+    values = _inputs()
+    for name in ("world_episode_seqs", "eligible_seqs", "eligible"):
+        source = values[name]
+        storage = torch.empty(4, dtype=source.dtype)
+        storage[::2] = source
+        values[name] = storage[::2]
+        assert not values[name].is_contiguous()
+    expected = {**values, **{name: values[name].clone() for name in ("world_episode_seqs", "eligible_seqs", "eligible")}}
+    stamp = _stamp(values)
+    equal_content = _stamp(expected)
+    assert stamp == stamp
+    assert stamp != equal_content
+    with pytest.raises(TypeError):
+        hash(stamp)
+    with pytest.raises(FrozenInstanceError):
+        stamp.world_ids = ("changed",)
+    for name in ("world_episode_seqs", "eligible_seqs", "eligible"):
+        values[name].zero_()
+        output = getattr(stamp, name)
+        second = getattr(stamp, name)
+        assert output.data_ptr() != second.data_ptr()
+        assert not output.requires_grad and output.grad_fn is None
+        output.zero_()
+        _assert_values(stamp, expected)
+
+
+def test_primitive_refusal_has_no_external_effects():
+    _, event_id, _ = _api()
+    values = _inputs()
+    pristine = {**values, **{name: values[name].clone() for name in ("world_episode_seqs", "eligible_seqs", "eligible")}}
+    existing = _stamp(values)
+    torch_before = torch.get_rng_state().clone()
+    python_before = random.getstate()
+    numpy_before = np.random.get_state()
+    _stamp(values)
+    bad = {**values, "event_ids": (values["event_ids"][0], event_id(0, "world-b", 2, 1))}
+    with pytest.raises(ValueError):
+        _stamp(bad)
+    _assert_values(existing, pristine)
+    for name in ("world_episode_seqs", "eligible_seqs", "eligible"):
+        assert torch.equal(values[name], pristine[name])
+    assert torch.equal(torch_before, torch.get_rng_state())
+    assert python_before == random.getstate()
+    numpy_after = np.random.get_state()
+    assert numpy_before[0] == numpy_after[0]
+    assert np.array_equal(numpy_before[1], numpy_after[1])
+    assert numpy_before[2:] == numpy_after[2:]
+
+
+def test_cpu_stamp_never_probes_or_initializes_cuda(monkeypatch):
+    values = _inputs()
+
+    def forbidden(*args, **kwargs):
+        pytest.fail("CPU primitive touched CUDA runtime")
+
+    for name in ("is_available", "is_initialized", "device_count", "current_device", "init", "_lazy_init"):
+        monkeypatch.setattr(torch.cuda, name, forbidden)
+    _assert_values(_stamp(values), values)
+
+
+def test_step_stamp_cuda_ownership_when_available():
+    _api()
+    if not torch.cuda.is_available():
+        pytest.skip("CUDA stamp ownership unrun: no supported hardware")
+    values = _inputs()
+    cpu_values = _inputs()
+    for name in ("world_episode_seqs", "eligible_seqs", "eligible"):
+        values[name] = values[name].cuda()
+    expected = {**values, **{name: values[name].clone() for name in ("world_episode_seqs", "eligible_seqs", "eligible")}}
+    stamp = _stamp(values)
+    _assert_values(stamp, expected)
+    for name in ("world_episode_seqs", "eligible_seqs", "eligible"):
+        mixed = {**values, name: cpu_values[name]}
+        with pytest.raises(ValueError):
+            _stamp(mixed)
+        exposed = getattr(stamp, name)
+        assert exposed.device == values[name].device
+        exposed.zero_()
+        _assert_values(stamp, expected)
+        values[name].zero_()
+    _assert_values(stamp, expected)

```
