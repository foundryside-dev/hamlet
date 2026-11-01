"""Additive BAC authoring: refusal, resolution and real compiled transport."""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import torch
import yaml
from pydantic import ValidationError

import townlet
from townlet.config.brain_config import BrainConfig
from townlet.config.training_v2_config import load_training_v2_config
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

ROOT = Path(__file__).resolve().parents[4]
PACK = ROOT / "configs/default_curriculum"
LEVEL = "L0_0_minimal"


@pytest.fixture(scope="session", autouse=True)
def identity():
    assert Path(townlet.__file__).resolve() == ROOT / "src/townlet/__init__.py"
    if "BAC_EXPECT_HEAD" in os.environ:
        assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == os.environ["BAC_EXPECT_HEAD"]
    diff = subprocess.check_output(["git", "diff", "HEAD", "--", "src/townlet"], cwd=ROOT)
    if "BAC_EXPECT_DIFF" in os.environ:
        assert hashlib.sha256(diff).hexdigest() == os.environ["BAC_EXPECT_DIFF"]
    torch.set_num_threads(1)


def api():
    # An assertion on the missing feature gives a useful red before importing it.
    import townlet.config.training_v2_config as tc

    assert "bac_options" in tc.TrainingV2Config.model_fields, "additive bac_options interface missing"
    from townlet.config.bac_options import BaCOptions, resolve_bac_options

    return BaCOptions, resolve_bac_options


def training():
    return load_training_v2_config(PACK / "levels" / LEVEL)


def test_old_options_remain_accepted():
    options, resolve = api()
    t = training()
    resolved = resolve(t.bac_options, training=t)
    assert resolved.options.replay.sampling_mode == "successive_without_replacement"
    assert resolved.options.replay.uniform_sequence_adapter == "legacy_episode_length_with_replacement"
    assert resolved.options.rnd.max_pending_rows == 32
    assert resolved.options.providers.icm.hidden_dim == 256
    assert resolved.options.providers.count_based.max_entries == 100000
    assert resolved.options.evaluation.episode_cap == 1000
    assert resolved.options.evaluation.seed == 42
    assert resolved.options.checkpoint.save_initial is False
    assert resolved.options.checkpoint.save_final is True
    assert all(entry.origin.startswith("bac-options-v1") for entry in resolved.provenance)
    explicit = resolve(options.model_validate({"rnd": {"max_updates_per_tick": 3}}), training=t)
    assert explicit.options.rnd.max_updates_per_tick == 3
    assert explicit.options.rnd.max_pending_rows == 32
    assert next(p for p in explicit.provenance if p.field == "rnd.max_updates_per_tick").origin == "authored"
    assert options.model_validate_json(resolved.options.model_dump_json()) == resolved.options
    with pytest.raises(ValidationError):
        resolved.options.rnd.max_updates_per_tick = 4


@pytest.mark.parametrize("family", ["feedforward", "dueling", "token_set", "recurrent"])
def test_all_modes_round_trip(family, tmp_path):
    _, resolve = api()
    source = ROOT / "configs/test/bac_remediation" / family
    target = tmp_path / "pack"
    shutil.copytree(source, target)
    compiled = UniverseCompiler().compile(target, primary_level=LEVEL, use_cache=False)
    selected = compiled.get_level(LEVEL).training
    resolved = resolve(selected.bac_options, training=selected)
    expected = yaml.safe_load((source / "levels" / LEVEL / "training.yaml").read_text())["training"]["bac_options"]
    for block, values in expected.items():
        if isinstance(values, dict):
            for name, value in values.items():
                assert resolved.options.model_dump()[block][name] == value
        else:
            assert resolved.options.model_dump()[block] == values
    assert compiled.brain.architecture.type == family
    restored = CompiledUniverse.from_dict(compiled.to_dict())
    assert restored.get_level(LEVEL).training.bac_options == selected.bac_options
    cache = tmp_path / "compiled.msgpack"
    compiled.save_to_cache(cache)
    assert CompiledUniverse.load_from_cache(cache).get_level(LEVEL).training.bac_options == selected.bac_options
    (target / "brain.yaml").rename(target / "renamed-brain.yaml")
    train_path = target / "levels" / LEVEL / "training.yaml"
    train_path.rename(train_path.with_name("renamed-training.yaml"))
    renamed = UniverseCompiler().compile(target, primary_level=LEVEL, use_cache=False)
    renamed_t = renamed.get_level(LEVEL).training
    assert resolve(renamed_t.bac_options, training=renamed_t) == resolved


def test_unqualified_options_are_retained():
    api()
    t = training().model_dump()
    t["recording"] = {"enabled": True, "criteria": {"novel_episodes": {"threshold": 0.3}}}
    from townlet.config.training_v2_config import TrainingV2Config

    checked = TrainingV2Config.model_validate(t)
    assert checked.recording.criteria == t["recording"]["criteria"]
    assert checked.curriculum.adversarial.adaptation_rate == 0.1
    brain = yaml.safe_load((PACK / "brain.yaml").read_text())
    brain["architecture"]["token_set"] = {"token_embed_dim": 8, "q_head_hidden_dim": 8, "aggregator": {"type": "mean"}}
    assert BrainConfig.model_validate(brain).architecture.token_set is not None


@pytest.mark.parametrize(
    "payload",
    [
        {"bogus": 1},
        {"replay": {"sampling_mode": "unknown"}},
        {"obs_dim": 3},
        {"rnd": {"max_updates_per_tick": 0}},
        {"rnd": {"max_pending_rows": -1}},
        {"providers": {"count_based": {"quantization_width": float("inf")}}},
        {"providers": {"icm": {"learning_rate": float("nan")}}},
        {"evaluation": {"epsilon": float("inf")}},
        {"checkpoint": {"save_initial": "false"}},
    ],
)
def test_invalid_options_refuse(payload):
    options, _ = api()
    with pytest.raises(ValidationError):
        options.model_validate(payload)


@pytest.mark.parametrize(
    "kind,width,valid",
    [
        ("linear", None, True),
        ("linear", 4, False),
        ("interaction_mlp", 4, True),
        ("interaction_mlp", None, False),
        ("interaction_mlp", 0, False),
    ],
)
@pytest.mark.parametrize("family", ["token_set", "recurrent"])
def test_token_encoder_contract(kind, width, valid, family):
    api()
    brain = yaml.safe_load((PACK / "brain.yaml").read_text())
    block = {
        "token_embed_dim": 8,
        "q_head_hidden_dim": 8,
        "aggregator": {"type": "mean"},
        "token_encoder": {"mode": kind, "hidden_width": width},
    }
    if family == "recurrent":
        block["lstm"] = {"hidden_size": 8, "num_layers": 1, "dropout": 0.0}
    brain["architecture"] = {"type": family, family: block}
    if valid:
        parsed = BrainConfig.model_validate(brain)
        assert getattr(parsed.architecture, family).token_encoder.mode == kind
        assert BrainConfig.model_validate_json(parsed.model_dump_json()) == parsed
    else:
        with pytest.raises(ValidationError):
            BrainConfig.model_validate(brain)


def test_service_capacity_and_provider_presets():
    options, resolve = api()
    t = training()
    with pytest.raises(ValueError, match="max_pending_rows"):
        resolve(options.model_validate({"rnd": {"max_pending_rows": 1}}), training=t)
    with pytest.raises(ValueError, match="max_pending_transitions"):
        resolve(options.model_validate({"providers": {"icm": {"max_pending_transitions": 1}}}), training=t)
    result = resolve(
        options.model_validate(
            {"provider_parameter_source": "drive", "providers": {"count_based": {"quantization_width": 0.25}, "icm": {"feature_dim": 7}}}
        ),
        training=t,
    )
    assert result.options.provider_parameter_source == "drive"
    assert result.options.providers.icm.hidden_dim == 14
    assert result.options.providers.count_based.quantization_width == 0.25


def test_encoder_omission_has_recorded_linear_semantics():
    from townlet.config.brain_config import resolve_token_encoder

    selected, origin = resolve_token_encoder(None)
    assert selected.mode == "linear"
    assert selected.hidden_width is None
    assert origin.startswith("bac-options-v1")
    assert resolve_token_encoder(selected) == (selected, "authored")


def test_option_documents_are_portable():
    options, resolve = api()
    for path in sorted((ROOT / "configs/test/bac_remediation/options").glob("*.yaml")):
        parsed = options.model_validate(yaml.safe_load(path.read_text()))
        receipt = resolve(parsed, training=training())
        assert type(receipt).model_validate_json(receipt.model_dump_json()) == receipt


@pytest.mark.parametrize("key", ["obs_dim", "action_dim", "token_types", "capacity", "hidden_dim", "type"])
def test_encoder_geometry_remains_compiler_owned(key):
    from townlet.config.brain_config import TokenEncoderOptions

    with pytest.raises(ValidationError):
        TokenEncoderOptions.model_validate({"mode": "linear", key: 4})


def test_encoder_schema_is_portable_option_interface():
    import townlet.config.bac_options as op

    assert hasattr(op, "TokenEncoderOptions"), "P4 requires TokenEncoderOptions in portable options module"
    selected = op.TokenEncoderOptions.model_validate({"mode": "interaction_mlp", "hidden_width": 12})
    assert selected.mode == "interaction_mlp"
    assert selected.hidden_width == 12
