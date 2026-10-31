"""Constructible authored numerics, through compilation and real factories."""

import shutil
from pathlib import Path

import pytest
import torch
import yaml
from pydantic import ValidationError

import townlet
from townlet.agent.network_factory import NetworkFactory
from townlet.agent.optimizer_factory import OptimizerFactory
from townlet.config.brain_config import BrainConfig, apply_training_overrides, compute_brain_hash
from townlet.config.training_v2_config import load_training_v2_config
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

ROOT = Path(__file__).resolve().parents[4]
LEVEL = "L0_0_minimal"


def _read(path):
    return yaml.safe_load(path.read_text())


def _write(path, data):
    path.write_text(yaml.safe_dump(data))


def _set(data, path, value):
    for key in path[:-1]:
        data = data[key]
    data[path[-1]] = value


@pytest.fixture(scope="module", autouse=True)
def source_and_fixture_preflight(tmp_path_factory):
    assert Path(townlet.__file__).resolve().is_relative_to(ROOT / "src")
    torch.set_num_threads(1)
    original = ROOT / "configs/default_curriculum"
    assert _read(original / "brain.yaml")["architecture"]["type"] == "feedforward"
    assert "training" in _read(original / "levels" / LEVEL / "training.yaml")
    pack = tmp_path_factory.mktemp("numerics-preflight") / "pack"
    shutil.copytree(original, pack)
    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert compiled.brain.architecture.type == "feedforward"
    load_training_v2_config(pack / "levels" / LEVEL)


@pytest.fixture
def pack(tmp_path):
    destination = tmp_path / "pack"
    shutil.copytree(ROOT / "configs/default_curriculum", destination)
    return destination


def _compile(pack):
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _training(pack):
    return load_training_v2_config(pack / "levels" / LEVEL)


def _dueling():
    return {
        "shared_layers": [8],
        "value_stream": {"hidden_layers": [8], "activation": "relu"},
        "advantage_stream": {"hidden_layers": [8], "activation": "relu"},
        "activation": "relu",
        "dropout": 0.0,
        "layer_norm": False,
    }


@pytest.mark.parametrize(
    "family,width_path",
    [
        ("feedforward", ("hidden_layers",)),
        ("dueling", ("shared_layers",)),
        ("dueling", ("value_stream", "hidden_layers")),
        ("dueling", ("advantage_stream", "hidden_layers")),
    ],
)
def test_negative_width_is_located(pack, family, width_path):
    path = pack / "brain.yaml"
    data = _read(path)
    if family == "dueling":
        data["architecture"] = {"type": family, family: _dueling()}
    _set(data["architecture"][family], width_path, [8, -1])
    _write(path, data)
    with pytest.raises(CompilationError) as error:
        _compile(pack)
    message = str(error.value)
    assert "brain" in message
    assert family in message and width_path[-1] in message
    assert f"{width_path[-1]}[1]" in message  # the negative element is located


@pytest.mark.parametrize("momentum,nesterov,valid", [(0.0, True, False), (0.9, True, True), (0.0, False, True)])
def test_nesterov_requires_positive_momentum(pack, momentum, nesterov, valid):
    path = pack / "brain.yaml"
    data = _read(path)
    data["optimizer"].update(type="sgd", sgd_momentum=momentum, sgd_nesterov=nesterov)
    _write(path, data)
    if not valid:
        with pytest.raises(CompilationError, match="(?i)nesterov.*momentum"):
            _compile(pack)
        return
    brain = apply_training_overrides(_compile(pack).brain, _training(pack))
    _finite_update(brain)


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")], ids=["inf", "minus-inf", "nan"])
@pytest.mark.parametrize("location", ["training_lr", "brain_lr", "inactive_schedule_eta"])
def test_infinite_override_refused(pack, value, location):
    if location == "training_lr":
        path = pack / "levels" / LEVEL / "training.yaml"
        data = _read(path)
        data["training"]["q_learning"]["learning_rate"] = value
        field = "learning_rate"
    else:
        path = pack / "brain.yaml"
        data = _read(path)
        if location == "brain_lr":
            data["optimizer"]["learning_rate"] = value
            field = "learning_rate"
        else:
            data["optimizer"]["schedule"]["eta_min"] = value
            field = "eta_min"
    _write(path, data)
    with pytest.raises(CompilationError, match=field):
        _compile(pack)


@pytest.mark.parametrize(
    "section,field_path",
    [
        ("brain", ("optimizer", "adam_eps")),
        ("brain", ("optimizer", "rmsprop_eps")),
        ("brain", ("optimizer", "weight_decay")),
        ("brain", ("loss", "huber_delta")),
        ("training", ("intrinsic", "rnd", "learning_rate")),
        ("training", ("intrinsic", "annealing", "threshold")),
        ("training", ("intrinsic", "initial_weight")),
        ("training", ("training_loop", "max_grad_norm")),
    ],
)
@pytest.mark.parametrize("value", [float("inf"), float("nan")], ids=["inf", "nan"])
def test_other_unbounded_behavioral_floats_are_finite(pack, section, field_path, value):
    if section == "brain":
        data = _read(pack / "brain.yaml")
        if field_path[0] == "loss":
            data["loss"] = {"type": "huber", "huber_delta": 1.0}
        _set(data, field_path, value)
        with pytest.raises(ValidationError, match=field_path[-1]):
            BrainConfig.model_validate(data)
    else:
        path = pack / "levels" / LEVEL / "training.yaml"
        data = _read(path)
        _set(data["training"], field_path, value)
        _write(path, data)
        with pytest.raises(ValueError, match=field_path[-1]):
            _training(pack)


def _finite_update(brain):
    parameter = torch.nn.Parameter(torch.tensor([1.0]))
    optimizer, _ = OptimizerFactory.build(brain.optimizer, iter([parameter]))
    parameter.square().sum().backward()
    optimizer.step()
    assert torch.isfinite(parameter).all()
    assert parameter.item() != 1.0
    return optimizer


@pytest.mark.parametrize("family", ["feedforward", "dueling"])
def test_zero_gamma_and_constant_policy_work(pack, family):
    path = pack / "brain.yaml"
    data = _read(path)
    if family == "dueling":
        dueling = _dueling()
        dueling["shared_layers"] = [0]
        dueling["value_stream"]["hidden_layers"] = [0]
        dueling["advantage_stream"]["hidden_layers"] = [0]
        data["architecture"] = {"type": family, family: dueling}
    else:
        data["architecture"][family]["hidden_layers"] = [0]
    _write(path, data)
    training_path = pack / "levels" / LEVEL / "training.yaml"
    training_data = _read(training_path)
    training_data["training"]["q_learning"].update(gamma=0.0, target_update_frequency=7, use_double_dqn=True, learning_rate=0.123)
    training_data["training"]["replay_buffer"].update(capacity=17, min_size=8, batch_size=4)
    _write(training_path, training_data)
    base = _compile(pack).brain
    snapshot = base.model_dump()
    brain = apply_training_overrides(base, _training(pack))
    assert brain.q_learning.gamma == 0
    assert brain.q_learning.target_update_frequency == 7
    assert brain.q_learning.use_double_dqn is True
    assert brain.optimizer.learning_rate == 0.123
    assert brain.replay.capacity == 17
    assert base.model_dump() == snapshot
    assert compute_brain_hash(base) != compute_brain_hash(brain)
    builder = getattr(NetworkFactory, f"build_{family}")
    network = builder(getattr(brain.architecture, family), obs_dim=3, action_dim=2)
    observations = torch.tensor([[1.0, 2.0, 3.0], [-9.0, 8.0, -7.0]])
    q = network(observations)
    assert q.shape == (2, 2) and torch.isfinite(q).all()
    assert torch.equal(q[0], q[1])
    assert any(name.endswith("bias") and p.numel() > 0 for name, p in network.named_parameters())
    assert sum(p.numel() for p in network.parameters()) == (2 if family == "feedforward" else 3)
    _finite_update(brain)


@pytest.mark.parametrize("optimizer_type", ["adam", "adamw", "sgd", "rmsprop"])
def test_selected_optimizer_and_finite_presets_work(pack, optimizer_type):
    path = pack / "brain.yaml"
    data = _read(path)
    data["optimizer"].update(type=optimizer_type, sgd_momentum=0.0, sgd_nesterov=True, rmsprop_alpha=0.9, rmsprop_eps=1e-8)
    if optimizer_type == "sgd":
        data["optimizer"]["sgd_momentum"] = 0.9
    data["optimizer"]["schedule"].update(step_size=7, gamma=0.5, t_max=5, eta_min=0.0)
    data["architecture"]["token_set"] = {"token_embed_dim": 17, "q_head_hidden_dim": 19, "aggregator": {"type": "mean"}}
    _write(path, data)
    base = _compile(pack).brain
    brain = apply_training_overrides(base, _training(pack))
    assert brain.architecture.type == "feedforward"
    assert brain.architecture.token_set.token_embed_dim == 17
    optimizer = _finite_update(brain)
    assert type(optimizer).__name__.lower() == optimizer_type
    assert brain.optimizer.schedule.type == "constant"


def test_level_brain_remains_complete_replacement(pack):
    data = _read(pack / "brain.yaml")
    data["architecture"] = {"type": "dueling", "dueling": _dueling()}
    data["description"] = "complete level replacement"
    _write(pack / "levels" / LEVEL / "brain.yaml", data)
    brain = _compile(pack).brain
    assert brain.description == "complete level replacement"
    assert brain.architecture.type == "dueling"
    assert brain.architecture.feedforward is None
    assert brain.architecture.dueling.shared_layers == [8]


def test_invalid_inactive_architecture_width_is_located(pack):
    path = pack / "brain.yaml"
    data = _read(path)
    data["architecture"]["dueling"] = _dueling()
    data["architecture"]["dueling"]["value_stream"]["hidden_layers"] = [-1]
    _write(path, data)
    with pytest.raises(CompilationError, match=r"architecture\.dueling\.value_stream\.hidden_layers\[0\]"):
        _compile(pack)
