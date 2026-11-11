"""Public binding preflight must compose with real owned construction without draws."""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from collections.abc import Mapping
from copy import copy, deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import ResolvedExplorationPolicy, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.exploration import rng_custody
from townlet.exploration import world_curiosity_state as world_state
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.exploration.world_curiosity_state import (
    WORLD_SEED_COMPONENTS,
    OwnedWorldBackend,
    WorldCuriosityDescriptor,
    WorldRNGState,
    derive_world_seed,
)


def _policy() -> ResolvedExplorationPolicy:
    root = Path(__file__).resolve().parents[4]
    directory = root / "configs/test/token_set_smoke/levels/L0_test"
    training = yaml.safe_load((directory / "training.yaml").read_text())["training"]
    drive = yaml.safe_load((directory / "drive.yaml").read_text())["drive"]["intrinsic"]
    drive["strategy"] = "none"
    options = BaCOptions.model_validate({"curiosity_scope": {"scope": "per_world", "seed_policy": "world_id_derived_v1"}})
    return resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(drive), TrainingV2Config.model_validate(training), options)


def _descriptor(policy: ResolvedExplorationPolicy, ids: tuple[str, ...]) -> WorldCuriosityDescriptor:
    return WorldCuriosityDescriptor.from_policy(policy, world_ids=ids, observation_dim=3, action_dim=2, training_seed=173)


def _backend(policy: ResolvedExplorationPolicy) -> EpsilonGreedyExploration:
    return EpsilonGreedyExploration(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)


def _same(left: Any, right: Any) -> None:
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert left.device == right.device and left.dtype == right.dtype
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert left.dtype == right.dtype
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, Mapping):
        assert left.keys() == right.keys()
        for key in left:
            _same(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _same(a, b)
    else:
        assert left == right


def _ambient(devices: tuple[int, ...]) -> dict[str, Any]:
    return {
        "torch": torch.get_rng_state().clone(),
        "python": random.getstate(),
        "numpy": deepcopy(np.random.get_state()),
        "cuda": {index: torch.cuda.get_rng_state(index).clone() for index in devices},
    }


def _validate(rng: WorldRNGState, descriptor: Any, world_id: Any, devices: Any) -> None:
    method = getattr(rng, "validate_binding", None)
    assert callable(method), "WorldRNGState lacks public activation-safe validate_binding"
    assert method(descriptor=descriptor, world_id=world_id, cuda_devices=devices) is None


@pytest.fixture
def binding() -> tuple[ResolvedExplorationPolicy, WorldCuriosityDescriptor, WorldRNGState]:
    policy = _policy()
    descriptor = _descriptor(policy, ("world-A", "world-B"))
    rng = WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=())
    return policy, descriptor, rng


def test_binding_fixture_prerequisite(binding: tuple[Any, ...]) -> None:
    """All real fixtures and lifecycle succeed independently of the new method."""
    policy, descriptor, rng = binding
    assert policy.strategy == "none" and policy.curiosity_scope == "per_world"
    assert WorldCuriosityDescriptor.from_dict(descriptor.to_dict()) == descriptor
    before = rng.snapshot()
    ambient = _ambient(())
    candidates = []

    def factory(candidate: WorldRNGState) -> EpsilonGreedyExploration:
        assert candidate is not rng
        candidates.append(candidate)
        with pytest.raises(RuntimeError, match="^Unrelated same-thread RNG reentry is forbidden$"):
            candidate.snapshot()
        with pytest.raises(RuntimeError, match="^RNG membership requires exclusive idle custody$"):
            WorldRNGState.from_snapshot(before, descriptor=descriptor, world_id="world-A", cuda_devices=())
        return _backend(policy)

    owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
    assert len(candidates) == 1
    _same(owner.snapshot(lineage=None)["rng"], before)
    _same(rng.snapshot(), before)
    _same(_ambient(()), ambient)


def test_binding_inside_actual_owned_constructor(binding: tuple[Any, ...]) -> None:
    policy, descriptor, rng = binding
    before = rng.snapshot()
    ambient = _ambient(())
    candidates = []

    def factory(candidate: WorldRNGState) -> EpsilonGreedyExploration:
        assert candidate is not rng
        candidates.append(candidate)
        installed = _ambient(())
        _validate(candidate, descriptor, "world-A", ())
        _same(_ambient(()), installed)
        return _backend(policy)

    owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
    assert len(candidates) == 1
    _same(owner.snapshot(lineage=None)["rng"], before)
    _same(rng.snapshot(), before)
    _same(_ambient(()), ambient)


@pytest.mark.parametrize("component", WORLD_SEED_COMPONENTS)
def test_binding_read_preserves_every_stream(binding: tuple[Any, ...], component: str) -> None:
    _, descriptor, rng = binding
    before = rng.snapshot()
    ambient = _ambient(())
    _validate(rng, descriptor, "world-A", ())
    with rng.activate(component) as sources:
        installed = _ambient(())
        pcg = deepcopy(sources.numpy.bit_generator.state)
        _validate(rng, descriptor, "world-A", ())
        _same(sources.numpy.bit_generator.state, pcg)
        _same(_ambient(()), installed)
        with pytest.raises(RuntimeError, match="^Unrelated same-thread RNG reentry is forbidden$"):
            rng.snapshot()
    _same(rng.snapshot(), before)
    _same(_ambient(()), ambient)


def test_binding_preserves_actual_candidate_domain_draws(binding: tuple[Any, ...]) -> None:
    policy, descriptor, rng = binding
    before = rng.snapshot()
    ambient = _ambient(())
    seen = []

    def factory(candidate: WorldRNGState) -> EpsilonGreedyExploration:
        seen.append(candidate)
        _validate(candidate, descriptor, "world-A", ())
        for component in WORLD_SEED_COMPONENTS:
            with candidate.activate(component) as sources:
                _validate(candidate, descriptor, "world-A", ())
                torch.rand(2)
                sources.python.random()
                sources.numpy.random()
                np.random.random()
        return _backend(policy)

    owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
    after = owner.snapshot(lineage=None)["rng"]
    _same(after, seen[0].snapshot())
    for component in WORLD_SEED_COMPONENTS:
        assert not torch.equal(after["components"][component]["torch_cpu"], before["components"][component]["torch_cpu"])
    _same(rng.snapshot(), before)
    _same(_ambient(()), ambient)


@pytest.mark.parametrize("ids", [("world-B", "world-A"), ("spectator", "world-A"), ("world-A",)])
def test_binding_ignores_spectator_roster_and_order(binding: tuple[Any, ...], ids: tuple[str, ...]) -> None:
    policy, _, rng = binding
    descriptor = _descriptor(policy, ids)
    before = rng.snapshot()
    _validate(rng, descriptor, "world-A", ())
    with rng.activate("model_init"):
        _validate(rng, descriptor, "world-A", ())
    _same(rng.snapshot(), before)


def test_binding_rejects_other_owner_inside_activation(binding: tuple[Any, ...]) -> None:
    _, descriptor, rng = binding
    other = WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=())
    before = other.snapshot()
    with rng.activate("model_init"):
        _validate(rng, descriptor, "world-A", ())
        installed = _ambient(())
        with pytest.raises(RuntimeError, match="^Unrelated same-thread RNG reentry is forbidden$"):
            _validate(other, descriptor, "world-A", ())
        with pytest.raises(RuntimeError, match="^Unrelated same-thread RNG reentry is forbidden$"):
            with other.activate("service"):
                pytest.fail("different owner was activated")
        _same(_ambient(()), installed)
    _same(other.snapshot(), before)


@pytest.mark.parametrize(
    "probe",
    [
        "id",
        "empty-id",
        "typed-id",
        "missing-id",
        "provider",
        "config",
        "observation",
        "action",
        "seed",
        "scope",
        "malformed-descriptor",
        "malformed-seeds",
        "malformed-clock",
        "device-list",
        "device-bool",
        "device-negative",
        "device-duplicate",
        "device-order",
    ],
)
@pytest.mark.parametrize("active", [False, True])
def test_binding_refuses_mismatch_before_draws(binding: tuple[Any, ...], probe: str, active: bool) -> None:
    policy, descriptor, rng = binding
    expected: Any = descriptor
    world_id: Any = "world-A"
    devices: Any = ()
    if probe == "id":
        world_id = "world-B"
    elif probe == "empty-id":
        world_id = ""
    elif probe == "typed-id":
        world_id = 1
    elif probe == "missing-id":
        expected = _descriptor(policy, ("world-B",))
    elif probe in ("provider", "seed"):
        payload = policy.to_dict()
        if probe == "provider":
            # Valid same-schema descriptor with a different current provider.
            expected = replace(
                descriptor,
                provider_kind="rnd",
                seeds={
                    wid: {
                        component: derive_world_seed(
                            training_seed=descriptor.training_seed, world_id=wid, provider_kind="rnd", component=component
                        )
                        for component in WORLD_SEED_COMPONENTS
                    }
                    for wid in descriptor.world_ids
                },
            )
        else:
            expected = WorldCuriosityDescriptor.from_policy(
                ResolvedExplorationPolicy.from_dict(payload),
                world_ids=descriptor.world_ids,
                observation_dim=3,
                action_dim=2,
                training_seed=174,
            )
    elif probe == "config":
        expected = replace(descriptor, provider_parameter_hash="0" * 64)
    elif probe == "observation":
        expected = replace(descriptor, observation_dim=4)
    elif probe == "action":
        expected = replace(descriptor, action_dim=3)
    elif probe == "scope":
        expected = replace(
            descriptor,
            scope="shared",
            seed_policy="legacy_shared_v1",
            service_clock_unit="vector_tick",
            guarantee="shared_population_state",
            seeds={},
        )
    elif probe == "malformed-descriptor":
        expected = descriptor.to_dict()
    elif probe in ("malformed-seeds", "malformed-clock"):
        expected = copy(descriptor)
        # Adversarial frozen-dataclass bypass must still be refused by preflight.
        object.__setattr__(
            expected, "seeds" if probe == "malformed-seeds" else "service_clock_unit", {} if probe == "malformed-seeds" else "vector_tick"
        )
    else:
        devices = {"device-list": [], "device-bool": (True,), "device-negative": (-1,), "device-duplicate": (0, 0), "device-order": (1, 0)}[
            probe
        ]
    before = rng.snapshot()
    ambient = _ambient(())

    def refuse() -> None:
        installed = _ambient(())
        with pytest.raises(ValueError):
            _validate(rng, expected, world_id, devices)
        _same(_ambient(()), installed)

    if active:
        with rng.activate("model_init"):
            refuse()
    else:
        refuse()
    _same(rng.snapshot(), before)
    _same(_ambient(()), ambient)


def test_binding_refuses_broken_owner(binding: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch) -> None:
    _, descriptor, rng = binding
    _validate(rng, descriptor, "world-A", ())
    ambient = _ambient(())

    def fail_capture() -> Any:
        raise RuntimeError("injected capture failure")

    with monkeypatch.context() as patch:
        patch.setattr(torch, "get_rng_state", fail_capture)
        with pytest.raises(RuntimeError, match="injected capture failure"):
            with rng.activate("model_init"):
                pytest.fail("capture unexpectedly succeeded")
    with pytest.raises(RuntimeError, match="^Private RNG state is unusable after failed capture$"):
        _validate(rng, descriptor, "world-A", ())
    _same(_ambient(()), ambient)


def test_binding_cpu_never_queries_cuda(binding: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch) -> None:
    _, descriptor, rng = binding

    def forbidden() -> Any:
        pytest.fail("CPU binding queried CUDA")

    monkeypatch.setattr(torch.cuda, "is_initialized", forbidden)
    monkeypatch.setattr(torch.cuda, "device_count", forbidden)
    _validate(rng, descriptor, "world-A", ())


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA binding requires available hardware")
def test_binding_cuda_domain(binding: tuple[Any, ...]) -> None:
    policy, descriptor, cpu = binding
    torch.cuda.init()
    devices = (0,)
    rng = WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=devices)
    before = rng.snapshot()
    ambient = _ambient(devices)
    _validate(rng, descriptor, "world-A", devices)
    with rng.activate("model_init"):
        _validate(rng, descriptor, "world-A", devices)
        with pytest.raises(ValueError):
            _validate(rng, descriptor, "world-A", ())
    with pytest.raises(ValueError):
        _validate(cpu, descriptor, "world-A", devices)
    with pytest.raises(ValueError):
        _validate(rng, descriptor, "world-A", (torch.cuda.device_count(),))
    owner = OwnedWorldBackend.construct(
        rng=rng, factory=lambda candidate: (_validate(candidate, descriptor, "world-A", devices), _backend(policy))[1]
    )
    _same(owner.snapshot(lineage=None)["rng"], before)
    _same(rng.snapshot(), before)
    _same(_ambient(devices), ambient)


def test_binding_validates_actual_owned_descriptor(binding: tuple[Any, ...]) -> None:
    _, descriptor, rng = binding
    malformed = copy(descriptor)
    object.__setattr__(malformed, "seeds", {})
    state = rng.snapshot()
    # The existing public constructor can receive an unvalidated descriptor.
    owner = WorldRNGState(malformed, "world-A", (), state["components"])
    before = owner.snapshot()
    ambient = _ambient(())
    with pytest.raises(ValueError):
        _validate(owner, descriptor, "world-A", ())
    _same(owner.snapshot(), before)
    _same(_ambient(()), ambient)


def test_binding_refuses_quarantined_coordinator(binding: tuple[Any, ...]) -> None:
    _, descriptor, rng = binding
    _validate(rng, descriptor, "world-A", ())
    parent_before, ambient = rng.snapshot(), _ambient(())
    root = Path(world_state.__file__).resolve().parents[3]
    source_hashes = {
        str(Path(module.__file__).resolve()): hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
        for module in (world_state, rng_custody)
    }
    expected_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    profile = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
    }
    script = r"""
import hashlib
import json
import os
import random
import subprocess
import sys
import types
from pathlib import Path
import numpy as np
import torch

root, expected_head, encoded_hashes, encoded_profile, encoded_descriptor = sys.argv[1:]
expected_hashes, expected_profile = json.loads(encoded_hashes), json.loads(encoded_profile)
qualification_names = ("BAC_QUAL_MANIFEST", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_ROOT", "BAC_QUAL_OUTPUT")
qualified = any(name in os.environ for name in qualification_names)
if qualified:
    assert all(os.environ.get(name) for name in qualification_names), "incomplete qualification environment"
    import bac_source_identity
    bac_source_identity.pytest_configure(types.SimpleNamespace(workerinput={"workerid": "binding_poison"}))
else:
    torch.set_num_threads(expected_profile["torch_threads"])
actual_profile = {
    "python_executable": sys.executable, "python_version": sys.version,
    "torch_version": torch.__version__, "torch_threads": torch.get_num_threads(),
    "torch_interop_threads": torch.get_num_interop_threads(),
}
assert actual_profile == expected_profile, (actual_profile, expected_profile)
sys.path.insert(0, str(Path(root) / "src"))
from townlet.exploration import rng_custody, rnd, world_curiosity_state as ws
imports = {"world_curiosity_state": str(Path(ws.__file__).resolve()),
           "rng_custody": str(Path(rng_custody.__file__).resolve()), "rnd": str(Path(rnd.__file__).resolve())}
def custody():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == expected_head
    for filename, expected in expected_hashes.items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
    assert imports["world_curiosity_state"] in expected_hashes and imports["rng_custody"] in expected_hashes
    if qualified:
        assert Path(os.environ["BAC_QUAL_ROOT"]).resolve() == Path(root).resolve()
        manifest_bytes = Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()
        manifest = json.loads(manifest_bytes)
        assert expected_head == os.environ["BAC_QUAL_SHA"] == manifest["base_commit"]
        for name, module in list(sys.modules.items()):
            if name == "townlet" or name.startswith("townlet."):
                filename = getattr(module, "__file__", None)
                if filename is not None:
                    path = Path(filename).resolve()
                    relative = str(path.relative_to(root))
                    assert relative in manifest["source_files"], (name, relative)
                    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["source_files"][relative]
    return {"pid": os.getpid(), **actual_profile, "imports": imports}
initial = custody()
if qualified:
    output = Path(os.environ["BAC_QUAL_OUTPUT"])
    receipt = output / "identity-binding_poison.json"
    identity = json.loads(receipt.read_text())
    identity.update(pid=os.getpid(), manifest_sha256=hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
                    debug=__debug__, interop_threads=torch.get_num_interop_threads(), imports=imports)
    receipt.write_text(json.dumps(identity, sort_keys=True, indent=2))
    destination = output / "spawn-identity-binding_poison.json"
    assert not destination.exists(), destination
    receipt.rename(destination)
descriptor = ws.WorldCuriosityDescriptor.from_dict(json.loads(encoded_descriptor))
first = ws.WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=())
other = ws.WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=())
first.validate_binding(descriptor=descriptor, world_id="world-A", cuda_devices=())
other.validate_binding(descriptor=descriptor, world_id="world-A", cuda_devices=())
random.seed(41)
random.gauss(0, 1)
np.random.seed(43)
np.random.normal()
saved_torch, saved_python, saved_numpy = torch.get_rng_state().clone(), random.getstate(), np.random.get_state()
real_torch, real_python, real_numpy = torch.set_rng_state, random.setstate, np.random.set_state
swaps, drawn = [], []
def torch_setter(state):
    swaps.append("torch")
    if drawn and torch.equal(state, saved_torch):
        raise RuntimeError("injected restoration failure")
    real_torch(state)
def python_setter(state):
    swaps.append("python")
    real_python(state)
def numpy_setter(state):
    swaps.append("numpy")
    real_numpy(state)
def retains_failure(error):
    return "injected restoration failure" in str(error) or any(
        retains_failure(item) for item in getattr(error, "exceptions", ())) or (
        error.__cause__ is not None and retains_failure(error.__cause__))
torch.set_rng_state, random.setstate, np.random.set_state = torch_setter, python_setter, numpy_setter
try:
    with first.activate("model_init") as sources:
        torch.rand(3)
        random.gauss(0, 1)
        sources.python.random()
        np.random.normal(size=3)
        sources.numpy.normal(size=3)
        drawn.append(True)
except BaseException as error:
    assert retains_failure(error), repr(error)
else:
    raise AssertionError("restoration failure was swallowed")
assert drawn and swaps[-3:] == ["torch", "python", "numpy"]
assert random.getstate() == saved_python
actual_numpy = np.random.get_state()
assert actual_numpy[0] == saved_numpy[0] and np.array_equal(actual_numpy[1], saved_numpy[1])
assert actual_numpy[2:] == saved_numpy[2:]
installed = (torch.get_rng_state().clone(), random.getstate(), np.random.get_state())
before_refusal = list(swaps)
try:
    other.validate_binding(descriptor=descriptor, world_id="world-A", cuda_devices=())
except RuntimeError as error:
    assert str(error) == "Ambient RNG domain is poisoned after failed restoration", str(error)
else:
    raise AssertionError("poisoned domain permitted unrelated binding")
assert swaps == before_refusal, "refused binding still swapped global streams"
assert torch.equal(installed[0], torch.get_rng_state()) and installed[1] == random.getstate()
now_numpy = np.random.get_state()
assert installed[2][0] == now_numpy[0] and np.array_equal(installed[2][1], now_numpy[1])
assert installed[2][2:] == now_numpy[2:]
assert custody() == initial
print("BAC_CHILD_RESULT " + json.dumps({"pid": os.getpid(), "message": "binding poison fail closed"}))
"""
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(root),
            expected_head,
            json.dumps(source_hashes),
            json.dumps(profile),
            json.dumps(descriptor.to_dict()),
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        try:
            stdout, stderr = child.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            child.terminate()
            try:
                child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.communicate(timeout=5)
            raise
    finally:
        assert child.stdout is not None and child.stderr is not None
        child.stdout.close()
        child.stderr.close()
    assert child.returncode == 0, stdout + stderr
    messages = [json.loads(line.removeprefix("BAC_CHILD_RESULT ")) for line in stdout.splitlines() if line.startswith("BAC_CHILD_RESULT ")]
    assert len(messages) == 1 and messages[0] == {"pid": child.pid, "message": "binding poison fail closed"}
    qualification_names = ("BAC_QUAL_MANIFEST", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_ROOT", "BAC_QUAL_OUTPUT")
    if any(name in os.environ for name in qualification_names):
        assert all(os.environ.get(name) for name in qualification_names)
        observation = {
            "process_pid": child.pid,
            "queued_pid": messages[0]["pid"],
            "exitcode": child.returncode,
            "qualified": True,
            "message": messages[0]["message"],
            "manifest_sha256": hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
        }
        with (Path(os.environ["BAC_QUAL_OUTPUT"]) / "spawn-observation-binding_poison.json").open("x") as stream:
            json.dump(observation, stream, sort_keys=True, indent=2)
    _same(rng.snapshot(), parent_before)
    _same(_ambient(()), ambient)
