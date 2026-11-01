"""Effective execution contracts without changing the historical brain identity."""

import hashlib
import json
import math
import shutil
from copy import deepcopy
from pathlib import Path

import msgpack
import pytest
import torch
import yaml

from townlet.config.brain_config import compute_brain_hash
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

ROOT = Path(__file__).resolve().parents[4]
HISTORY = ROOT / "tests/test_townlet/fixtures/bac_historical"


@pytest.fixture
def pack(tmp_path):
    destination = tmp_path / "pack"
    shutil.copytree(ROOT / "configs/test/token_set_smoke", destination, ignore=shutil.ignore_patterns(".compiled"))
    return destination


def edit(path, update):
    payload = yaml.safe_load(path.read_text())
    update(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def compile_pack(pack, *, cache=False):
    return UniverseCompiler().compile(pack, primary_level="L0_test", use_cache=cache)


def test_preset_edit_changes_authored_not_execution(pack):
    first = compile_pack(pack)
    assert hasattr(first, "effective_run"), "compiler must expose the effective run view"
    preset = {"hidden_layers": [17, 0], "activation": "tanh", "dropout": 0.2, "layer_norm": False}
    edit(pack / "brain.yaml", lambda p: p["architecture"].update(feedforward=preset))
    second = compile_pack(pack)
    assert first.authored_brain_hash != second.authored_brain_hash
    assert first.execution_hash == second.execution_hash
    assert first.metadata.config_hash != second.metadata.config_hash
    assert second.brain.architecture.feedforward.hidden_layers == [17, 0]
    role = second.effective_run.field_roles["brain.architecture.feedforward.hidden_layers"]
    assert role.status == "inactive_preset" and role.origin
    from townlet.agent.network_factory import NetworkFactory

    weights = []
    for universe in (first, second):
        brain = universe.effective_run.effective_brain.architecture.token_set
        torch.manual_seed(31)
        network = NetworkFactory.build_token_set(brain, universe.metadata.action_count, universe.get_level("L0_test").token_spec)
        weights.append(network.state_dict())
    assert weights[0].keys() == weights[1].keys()
    assert all(torch.equal(weights[0][key], weights[1][key]) for key in weights[0])


def test_five_overrides_have_one_runtime_view(pack):
    selected = yaml.safe_load((pack / "brain.yaml").read_text())
    selected["architecture"] = {
        "type": "feedforward",
        "feedforward": {"hidden_layers": [0], "activation": "tanh", "dropout": 0.0, "layer_norm": False},
    }
    (pack / "levels/L0_test/brain.yaml").write_text(yaml.safe_dump(selected))
    before = deepcopy(selected)

    def overrides(p):
        p["training"]["q_learning"].update(gamma=0.73, target_update_frequency=13, use_double_dqn=True, learning_rate=0.0007)
        p["training"]["replay_buffer"]["capacity"] = 2048

    edit(pack / "levels/L0_test/training.yaml", overrides)
    universe = compile_pack(pack)
    assert hasattr(universe, "effective_run"), "five overrides require one effective runtime view"
    run = universe.effective_run
    assert universe.brain.model_dump(exclude_none=True) == before
    assert run.base_brain == universe.brain
    effective = run.effective_brain
    assert effective.q_learning.gamma == 0.73
    assert effective.q_learning.target_update_frequency == 13
    assert effective.q_learning.use_double_dqn is True
    assert effective.optimizer.learning_rate == 0.0007
    assert effective.replay.capacity == 2048
    assert effective.architecture.type == "feedforward" and effective.architecture.token_set is None
    assert universe.brain_hash == compute_brain_hash(effective)
    assert universe.pack_brain_hash != universe.brain_hash
    assert run.field_roles["brain.q_learning.gamma"].status == "inactive_preset"
    assert run.training_hash == universe.get_level("L0_test").training_hash


def test_effective_cache_roundtrip(pack, tmp_path):
    first = compile_pack(pack, cache=True)
    assert hasattr(first, "effective_run"), "effective run must survive cache transport"
    for other in (CompiledUniverse.from_dict(first.to_dict()), compile_pack(pack, cache=True), first.clone()):
        assert other.to_dict() == first.to_dict()
        assert other.execution_hash == first.execution_hash
        assert other.authored_brain_hash == first.authored_brain_hash
    path = tmp_path / "new.msgpack"
    first.save_to_cache(path)
    other = CompiledUniverse.load_from_cache(path)
    assert other.effective_run.to_dict() == first.effective_run.to_dict()
    before = first.to_dict()
    corrupted = first.to_dict()
    corrupted["effective_run"]["execution_hash"] = "0" * 64
    with pytest.raises(ValueError, match="effective_run|execution_hash"):
        CompiledUniverse.from_dict(corrupted)
    for corruption in ("outer_brain", "role", "phase", "provider", "missing_view"):
        corrupted = deepcopy(before)
        if corruption == "outer_brain":
            corrupted["brain"]["architecture"]["token_set"]["token_embed_dim"] = 24
        elif corruption == "role":
            corrupted["effective_run"]["field_roles"]["brain.architecture.type"]["status"] = "inactive_preset"
        elif corruption == "phase":
            corrupted["effective_run"]["exploration"]["predictor_observation_phase"] = "successor_postphysics"
        elif corruption == "provider":
            corrupted["effective_run"]["exploration"]["provider_parameters"]["unrecognized"] = 4
        else:
            corrupted.pop("effective_run")
        with pytest.raises(ValueError):
            CompiledUniverse.from_dict(corrupted)
        assert first.to_dict() == before
    run = first.effective_run
    exported = run.to_dict()
    exported["base_brain"]["description"] = "mutated exported DTO"
    run.base_brain.description = "mutated returned model"
    run.training.replay_buffer.batch_size = 99
    assert run.to_dict() == before["effective_run"]
    with pytest.raises(TypeError):
        run.field_roles["fake"] = run.field_roles["brain.architecture.type"]


def test_inactive_raw_nan_presets_survive_real_msgpack(pack, tmp_path):
    edit(
        pack / "levels/L0_test/drive.yaml",
        lambda p: p["drive"]["intrinsic"].update(strategy="none", rnd_config={"future": {"value": float("nan")}}),
    )
    original = compile_pack(pack)
    path = tmp_path / "inactive-nan.msgpack"
    original.save_to_cache(path)
    before = path.read_bytes()
    for restored in (CompiledUniverse.load_from_cache(path), original.clone(), CompiledUniverse.from_dict(original.to_dict())):
        assert math.isnan(restored.effective_run.exploration.raw_provider_parameters["rnd_config"]["future"]["value"])
        assert restored.authored_identity == original.authored_identity
        assert restored.execution_hash == original.execution_hash
    assert path.read_bytes() == before
    for replacement in ("NaN", None):
        corrupted = original.to_dict()
        corrupted["effective_run"]["exploration"]["raw_provider_parameters"]["rnd_config"]["future"]["value"] = replacement
        with pytest.raises(ValueError, match="effective_run"):
            CompiledUniverse.from_dict(corrupted)
    corrupted = original.to_dict()
    corrupted["effective_run"]["exploration"]["epsilon_start"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        CompiledUniverse.from_dict(corrupted)
    edit(pack / "levels/L0_test/drive.yaml", lambda p: p["drive"]["intrinsic"]["rnd_config"]["future"].update(value="NaN"))
    edited = compile_pack(pack)
    assert edited.authored_identity != original.authored_identity
    assert edited.execution_hash == original.execution_hash


def test_selected_provider_capacity_materializes_after_rp(pack):
    edit(pack / "levels/L0_test/drive.yaml", lambda p: p["drive"]["intrinsic"].update(strategy="rnd", rnd_config={"batch_size": 8}))
    edit(
        pack / "levels/L0_test/training.yaml",
        lambda p: p["training"].update(bac_options={"provider_parameter_source": "drive", "rnd": {"max_pending_rows": 8}}),
    )
    universe = compile_pack(pack, cache=True)
    assert hasattr(universe, "effective_run"), "resolve authored selected batch before option capacities"
    run = universe.effective_run
    assert run.training.replay_buffer.batch_size == 32
    assert run.exploration.predictor_batch_size == 8
    assert run.options.rnd.max_pending_rows == 8
    assert compile_pack(pack, cache=True).execution_hash == universe.execution_hash
    edit(pack / "levels/L0_test/training.yaml", lambda p: p["training"]["bac_options"]["rnd"].update(max_pending_rows=7))
    with pytest.raises(ValueError, match="max_pending_rows|predictor_batch_size"):
        compile_pack(pack)


def test_materialized_provider_defaults_are_not_authored_overrides(pack):
    edit(
        pack / "levels/L0_test/drive.yaml",
        lambda p: p["drive"]["intrinsic"].update(
            strategy="icm", icm_config={"training_batch_size": 8, "feature_dim": 7, "future": {"x": [1, 2]}}
        ),
    )
    edit(
        pack / "levels/L0_test/training.yaml",
        lambda p: p["training"].update(bac_options={"providers": {"icm": {"training_batch_size": 4}}}),
    )
    universe = compile_pack(pack, cache=True)
    assert hasattr(universe, "effective_run"), "materialized defaults must never become authored overrides"
    run = universe.effective_run
    assert run.training.replay_buffer.batch_size == 32
    assert run.exploration.provider_parameters["training_batch_size"] == 4
    assert run.options.providers.icm.feature_dim == 7
    assert run.options.providers.icm.hidden_dim == 14
    assert run.options.providers.icm.training_batch_size == 4
    assert run.exploration.predictor_input_kind == "transition"
    assert run.authored_options.model_dump(exclude_none=True) == {"providers": {"icm": {"training_batch_size": 4}}}
    assert run.exploration.raw_provider_parameters["icm_config"]["future"]["x"] == (1, 2)
    assert CompiledUniverse.from_dict(universe.to_dict()).effective_run.to_dict() == run.to_dict()


def test_known_v1_40_compiled_cache_derives_current_effective_view_without_rehashing(pack):
    current = compile_pack(pack)
    payload = current.to_dict()
    payload["compiled_schema_version"] = "1.40"
    payload.pop("effective_run", None)
    original = deepcopy(payload)
    loaded = CompiledUniverse.from_dict(payload)
    assert hasattr(loaded, "effective_run"), "known 1.40 caches need a truthful derived current view"
    assert payload == original
    assert loaded.brain_hash == original["brain_hash"]
    assert loaded.pack_brain_hash == original["pack_brain_hash"]
    assert loaded.execution_hash == current.execution_hash
    assert "1.40" in loaded.effective_run.derivations["capture_origin"]
    payload["compiled_schema_version"] = "1.39"
    with pytest.raises(ValueError, match="schema mismatch"):
        CompiledUniverse.from_dict(payload)


def test_original_historical_compiled_caches_stay_readable():
    manifest = json.loads((HISTORY / "portable-manifest.json").read_text())
    checked = 0
    for artifact in manifest["canonical_artifacts"]:
        if artifact["label"] not in ("uniform", "per", "sequence-trained"):
            continue
        for relative, expected in artifact["config_files"].items():
            if "/.compiled/" not in relative:
                continue
            path = HISTORY / relative
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
            payload = msgpack.unpackb(path.read_bytes(), raw=False, strict_map_key=False)
            assert payload["compiled_schema_version"] == "1.40"
            loaded = CompiledUniverse.load_from_cache(path)
            assert hasattr(loaded, "effective_run"), "original historic cache must remain readable"
            assert loaded.brain_hash == payload["brain_hash"]
            assert loaded.pack_brain_hash == payload["pack_brain_hash"]
            assert "1.40" in loaded.effective_run.derivations["capture_origin"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
            checked += 1
    assert checked == 15
    # The original pre-optimizer sequential capture is separately retained.
    path = HISTORY / "sequence-pack/.compiled/universe-L1_full_observability.msgpack"
    before = path.read_bytes()
    assert hashlib.sha256(before).hexdigest() == "5a654e72b714e771f7f9326b93647d71d804e48ff5fffd48d0f76d6d360c415a"
    loaded = CompiledUniverse.load_from_cache(path)
    assert loaded.effective_run.effective_brain.architecture.type == "recurrent"
    assert path.read_bytes() == before


@pytest.mark.parametrize("change", ["active", "inactive", "unqualified"])
def test_field_roles_drive_execution_identity(pack, change):
    first = compile_pack(pack)
    assert hasattr(first, "effective_run"), "finite field roles must govern execution identity"
    if change == "active":
        edit(pack / "brain.yaml", lambda p: p["architecture"]["token_set"].update(token_embed_dim=24))
    elif change == "inactive":
        edit(pack / "brain.yaml", lambda p: p["optimizer"].update(sgd_momentum=0.5, sgd_nesterov=True))
    else:
        edit(pack / "brain.yaml", lambda p: p.update(description="new authoring description"))
    second = compile_pack(pack)
    assert first.authored_brain_hash != second.authored_brain_hash
    assert (first.execution_hash != second.execution_hash) == (change == "active")


def test_shadowed_base_fields_remain_authored_presets(pack):
    from townlet.config.effective_run import resolve_effective_run

    universe = compile_pack(pack)
    run = universe.effective_run
    base = run.base_brain
    base.q_learning.gamma = 0.4
    base.q_learning.target_update_frequency = 77
    base.q_learning.use_double_dqn = False
    base.optimizer.learning_rate = 0.003
    base.replay.capacity = 12345
    changed = resolve_effective_run(
        base,
        run.training,
        primary_level=run.primary_level,
        origins=run.origins,
        drive_intrinsic=universe.get_level("L0_test").drive.intrinsic,
    )
    assert changed.authored_brain_hash != run.authored_brain_hash
    assert changed.authored_identity != run.authored_identity
    assert changed.execution_hash == run.execution_hash
    assert compute_brain_hash(changed.effective_brain) == universe.brain_hash


@pytest.mark.parametrize("strategy", ["none", "rnd", "adaptive_rnd", "icm", "count_based"])
def test_selected_provider_activity_is_schema_owned(pack, strategy):
    from townlet.config.effective_run import EffectiveRunConfig, resolve_effective_run

    edit(pack / "levels/L0_test/drive.yaml", lambda p: p["drive"]["intrinsic"].update(strategy=strategy))
    universe = compile_pack(pack)
    run = universe.effective_run
    training = run.training
    training.intrinsic.rnd.feature_dim = 96
    changed = resolve_effective_run(
        run.base_brain,
        training,
        primary_level=run.primary_level,
        origins=run.origins,
        drive_intrinsic=universe.get_level("L0_test").drive.intrinsic,
    )
    assert changed.authored_identity != run.authored_identity
    assert (changed.execution_hash != run.execution_hash) == (strategy in ("rnd", "adaptive_rnd", "icm"))
    assert EffectiveRunConfig.from_dict(changed.to_dict()).to_dict() == changed.to_dict()
    if strategy == "none":
        training = run.training
        from townlet.config.bac_options import BaCOptions

        training.bac_options = BaCOptions.model_validate({"providers": {"icm": {"training_batch_size": 100, "max_pending_transitions": 1}}})
        preset = resolve_effective_run(
            run.base_brain,
            training,
            primary_level=run.primary_level,
            origins=run.origins,
            drive_intrinsic=universe.get_level("L0_test").drive.intrinsic,
        )
        assert preset.authored_identity != run.authored_identity
        assert preset.execution_hash == run.execution_hash
        assert preset.options.providers.icm.max_pending_transitions == 1
        assert preset.field_roles["bac_options.providers.icm.training_batch_size"].status == "inactive_preset"
