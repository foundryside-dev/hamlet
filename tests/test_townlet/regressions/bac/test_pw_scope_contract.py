"""PW01 scope/identity/seed contract; this does not certify private training updates."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from townlet.config.bac_options import BaCOptions, resolve_bac_options
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.effective_run import EffectiveRunConfig
from townlet.config.exploration_policy import ResolvedExplorationPolicy, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

ROOT = Path(__file__).resolve().parents[4]
PACK = ROOT / "configs/test/token_set_smoke"
PROFILES = ROOT / "configs/test/bac_remediation/options"
NATIVE = ROOT / "tests/test_townlet/fixtures/bac_curiosity_pre_scope"
PRODUCER = "1c99510967c132fce04548564f4cb317e2ecddaf"
NATIVE_DIGESTS = {
    "scope-omitted": "89e60038cdc532ce812634fbe06620ec5bf45b3e8639e44e444eddb2d745333a",
    "options-authored": "46e155bb01b376e206847dd70da4c1de6c316a4c23eace1e06a2cae5b6b2e315",
}
STREAMS = ("model_init", "target", "predictor", "service")


def _profile(scope: str) -> dict:
    return yaml.safe_load((PROFILES / f"curiosity-{scope.replace('_', '-')}.yaml").read_text())


def _authoring(options: dict | None, population: int, batch: int) -> tuple[TrainingV2Config, IntrinsicStrategyConfig]:
    level = PACK / "levels/L0_test"
    training = yaml.safe_load((level / "training.yaml").read_text())["training"]
    training["population"]["size"] = population
    training["replay_buffer"]["batch_size"] = batch
    if options is not None:
        training["bac_options"] = deepcopy(options)
    drive = yaml.safe_load((level / "drive.yaml").read_text())["drive"]["intrinsic"]
    return TrainingV2Config.model_validate(training), IntrinsicStrategyConfig.model_validate(drive)


def _policy(options: dict | None, strategy: str, population: int, batch: int) -> ResolvedExplorationPolicy:
    training, drive = _authoring(options, population, batch)
    selected = drive.model_dump()
    selected["strategy"] = strategy
    authored = BaCOptions() if options is None else BaCOptions.model_validate(options)
    return resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(selected), training, authored)


def _legacy_policy_identity(payload: dict) -> str:
    """Frozen pre-scope v1 recipe, checked against genuine 1.41 DATA controls."""
    active = set(
        "strategy epsilon_start epsilon_end epsilon_decay provider_parameters reward_observation_phase "
        "predictor_observation_phase predictor_input_kind".split()
    )
    if payload["strategy"] != "none":
        active.update(("initial_intrinsic_weight", "drive_base_weight", "modifier_names"))
    if payload["strategy"] in ("rnd", "adaptive_rnd"):
        active.update(("provider_parameter_source", "rnd_feature_dim", "rnd_learning_rate", "predictor_batch_size"))
    if payload["strategy"] == "adaptive_rnd":
        active.update("min_intrinsic_weight variance_threshold min_survival_fraction max_episode_length survival_window decay_rate".split())
    if payload["strategy"] in ("rnd", "adaptive_rnd", "icm"):
        active.update(("service_mode", "max_updates_per_tick", "max_pending_rows", "overflow_policy"))
    if payload["strategy"] == "icm":
        active.add("predictor_batch_size")
    record = {"schema": "exploration-policy-v1", **{name: payload[name] for name in active}}
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _assert_scope(policy: ResolvedExplorationPolicy, scope: str, origin: str) -> None:
    payload = policy.to_dict()
    assert payload.get("curiosity_scope") == scope, "PW01 must publish explicit resolved curiosity ownership"
    assert payload["seed_policy"] == ("legacy_shared_v1" if scope == "shared" else "world_id_derived_v1")
    assert payload["service_clock_unit"] == ("vector_tick" if scope == "shared" else "world_eligible_admission")
    assert payload["scope_origin"] == origin
    assert payload["scope_guarantee"] == ("shared_population_state" if scope == "shared" else "world_id_owned_state")
    for name in ("curiosity_scope", "seed_policy", "service_clock_unit", "scope_origin", "scope_guarantee"):
        assert policy.field_roles[name].status in ("active", "derived")
        assert policy.field_roles[name].origin
        assert policy.parameter_units[name]
    assert ResolvedExplorationPolicy.from_dict(payload).to_dict() == payload
    partial = deepcopy(payload)
    partial.pop("curiosity_scope")
    with pytest.raises(ValueError):
        ResolvedExplorationPolicy.from_dict(partial)
    stripped = deepcopy(payload)
    for name in ("curiosity_scope", "seed_policy", "service_clock_unit", "scope_origin", "scope_guarantee"):
        stripped.pop(name)
    with pytest.raises(ValueError):
        ResolvedExplorationPolicy.from_dict(stripped)


def test_scope_defaults_and_identity_roundtrip(tmp_path: Path) -> None:
    manifest = json.loads((NATIVE / "manifest.json").read_text())
    assert manifest["producer_sha"] == PRODUCER
    assert {item["label"] for item in manifest["artifacts"]} == set(NATIVE_DIGESTS)
    for item in manifest["artifacts"]:
        artifact = NATIVE / item["artifact"]
        assert item["producer_sha"] == PRODUCER and item["schema_version"] == "1.41"
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == item["sha256"] == NATIVE_DIGESTS[item["label"]]
        legacy = CompiledUniverse.load_from_cache(artifact)
        assert legacy is not None
        view = legacy.effective_run
        assert view is not None
        assert legacy.execution_hash == view.execution_hash == item["execution_hash"]
        assert legacy.brain_hash == item["brain_hash"] and legacy.pack_brain_hash == item["pack_brain_hash"]
        assert view.training_hash == item["training_hash"]
        assert view.authored_identity == item["effective_run"]["authored_identity"]
        assert view.exploration.policy_identity == _legacy_policy_identity(item["effective_run"]["exploration"])
        view.validate_payload(item["effective_run"])
        reconstructed = EffectiveRunConfig.from_dict(item["effective_run"])
        assert reconstructed.execution_hash == view.execution_hash
        assert reconstructed.training_hash == view.training_hash
        for field in ("rnd_feature_dim", "rnd_learning_rate", "predictor_batch_size", "max_pending_rows", "max_updates_per_tick"):
            assert getattr(view.exploration, field) == item["effective_run"]["exploration"][field]
        if item["label"] == "options-authored":
            assert view.authored_options.serving.policy_mode == "mc_dropout"
            assert view.authored_options.replay.sampling_mode == "independent_with_replacement"
            assert view.authored_options.checkpoint.save_initial is True
        recached = tmp_path / f"{item['label']}.msgpack"
        legacy.save_to_cache(recached)
        for restored in (CompiledUniverse.from_dict(legacy.to_dict()), CompiledUniverse.load_from_cache(recached)):
            assert restored is not None and restored.execution_hash == item["execution_hash"]
            assert restored.effective_run.training_hash == item["training_hash"]
            assert restored.effective_run.authored_identity == item["effective_run"]["authored_identity"]
            _assert_scope(restored.effective_run.exploration, "shared", "bac-options-v1")

    training, _ = _authoring(None, 17, 3)
    defaults = resolve_bac_options(None, training=training)
    scope = getattr(defaults.options, "curiosity_scope", None)
    assert scope is not None, "PW01 must resolve omitted scope to the recorded shared policy"
    assert scope.scope == "shared" and scope.seed_policy == "legacy_shared_v1"
    assert defaults.options.rnd.max_pending_rows == 34
    derived = BaCOptions.model_validate({"curiosity_scope": {"scope": "per_world"}})
    assert resolve_bac_options(derived, training=training).options.curiosity_scope.seed_policy == "world_id_derived_v1"
    for invalid in (
        {"scope": "per_world", "seed_policy": "legacy_shared_v1"},
        {"scope": "shared", "seed_policy": "world_id_derived_v1"},
        {"scope": "unknown"},
    ):
        with pytest.raises(ValueError):
            BaCOptions.model_validate({"curiosity_scope": invalid})

    for strategy in ("none", "rnd", "adaptive_rnd", "count_based", "icm"):
        omitted = _policy(None, strategy, 17, 3)
        shared = _policy(_profile("shared"), strategy, 17, 3)
        private = _policy(_profile("per_world"), strategy, 17, 3)
        _assert_scope(omitted, "shared", "bac-options-v1")
        _assert_scope(shared, "shared", "authored")
        _assert_scope(private, "per_world", "authored")
        assert omitted.policy_identity == shared.policy_identity == _legacy_policy_identity(omitted.to_dict())
        assert private.policy_identity != shared.policy_identity
        assert omitted.max_pending_rows == shared.max_pending_rows == 34
        assert private.max_pending_rows == 3
        assert private.parameter_units["max_updates_per_tick"] == "predictor_minibatches/world_eligible_admission"
        if strategy == "icm":
            assert private.provider_parameters["max_pending_transitions"] == 3
        explicit = _profile("per_world") | {"rnd": {"max_pending_rows": 101}}
        if strategy == "icm":
            explicit["providers"] = {"icm": {"max_pending_transitions": 103}}
        selected = _policy(explicit, strategy, 17, 3)
        assert selected.max_pending_rows == (103 if strategy == "icm" else 101)

    compiled = {}
    for label, options in (("omitted", None), ("shared", _profile("shared")), ("per_world", _profile("per_world"))):
        authored_pack = tmp_path / label
        shutil.copytree(PACK, authored_pack, ignore=shutil.ignore_patterns(".compiled"))
        training_path = authored_pack / "levels/L0_test/training.yaml"
        authored = yaml.safe_load(training_path.read_text())
        authored["training"]["population"]["size"] = 17
        authored["training"]["replay_buffer"]["batch_size"] = 3
        if options is not None:
            authored["training"]["bac_options"] = options
        training_path.write_text(yaml.safe_dump(authored, sort_keys=False))
        universe = UniverseCompiler().compile(authored_pack, primary_level="L0_test", use_cache=False)
        compiled[label] = universe
        expected = universe.effective_run.to_dict()
        assert EffectiveRunConfig.from_dict(expected).to_dict() == expected
        corrupted = deepcopy(expected)
        corrupted["exploration"].pop("curiosity_scope")
        with pytest.raises(ValueError):
            EffectiveRunConfig.from_dict(corrupted)
        cache = tmp_path / f"{label}-new.msgpack"
        universe.save_to_cache(cache)
        for restored in (CompiledUniverse.from_dict(universe.to_dict()), CompiledUniverse.load_from_cache(cache)):
            assert restored is not None
            assert restored.effective_run.to_dict() == expected
            assert restored.execution_hash == universe.execution_hash
            assert restored.get_level("L0_test").training.bac_options == universe.get_level("L0_test").training.bac_options
    assert compiled["omitted"].execution_hash == compiled["shared"].execution_hash
    assert compiled["per_world"].execution_hash != compiled["shared"].execution_hash


def test_world_seed_is_stable_under_lane_reorder() -> None:
    module_name = "townlet.exploration.world_curiosity_state"
    assert importlib.util.find_spec(module_name) is not None, "PW01 must provide the world identity/seed contract primitive"
    primitive = importlib.import_module(module_name)
    descriptor_type = getattr(primitive, "WorldCuriosityDescriptor", None)
    derive_seed = getattr(primitive, "derive_world_seed", None)
    assert descriptor_type is not None and callable(derive_seed)
    ids = ("a.b", "a/b", "世界", "é", "e\u0301", "A.B")
    policy = _policy(_profile("per_world"), "rnd", len(ids), 3)

    def describe(world_ids: tuple[str, ...], selected: ResolvedExplorationPolicy):
        return descriptor_type.from_policy(selected, world_ids=world_ids, observation_dim=7, action_dim=4, training_seed=42)

    original = describe(ids, policy)
    reordered = describe(tuple(reversed(ids)), policy)
    spectator = describe(("spectator", *reversed(ids)), _policy(_profile("per_world"), "rnd", len(ids) + 1, 3))
    assert original.world_ids == ids
    assert original.canonical_world_ids == tuple(sorted(ids))
    assert original.world_binding_hash != reordered.world_binding_hash != spectator.world_binding_hash
    assert policy.policy_identity == _policy(_profile("per_world"), "rnd", 97, 3).policy_identity
    portable = original.to_dict()
    assert portable["schema_version"] == 1 and portable["scope"] == "per_world"
    assert portable["seed_policy"] == "world_id_derived_v1"
    assert portable["service_clock_unit"] == "world_eligible_admission"
    assert portable["provider_kind"] == "rnd" and portable["provider_parameter_hash"]
    assert portable["origin"] and portable["guarantee"]
    assert set(portable["seeds"]) == set(ids)
    assert descriptor_type.from_dict(portable).to_dict() == portable
    local_seeds = set()
    for world_id in ids:
        assert set(portable["seeds"][world_id]) == set(STREAMS)
        for component in STREAMS:
            seed = original.seed_for(world_id, component)
            assert type(seed) is int and 0 <= seed < 2**63
            assert seed == reordered.seed_for(world_id, component) == spectator.seed_for(world_id, component)
            assert seed == derive_seed(training_seed=42, world_id=world_id, provider_kind="rnd", component=component)
            assert seed == portable["seeds"][world_id][component]
            local_seeds.add(seed)
            assert seed != derive_seed(training_seed=43, world_id=world_id, provider_kind="rnd", component=component)
            assert seed != derive_seed(training_seed=42, world_id=world_id, provider_kind="icm", component=component)
    assert len(local_seeds) == len(ids) * len(STREAMS)
    # Model/queue geometry and active provider parameters cannot leak into the KDF.
    altered = describe(ids, _policy(_profile("per_world"), "rnd", len(ids), 11))
    for world_id in ids:
        assert altered.seed_for(world_id, "predictor") == original.seed_for(world_id, "predictor")
    for invalid in (("a.b", "a.b"), ("",), ("ok", "")):
        with pytest.raises(ValueError, match="world|World|duplicate|nonempty"):
            describe(invalid, policy)
    for bad_seed in (-1, True, 1.5):
        with pytest.raises(ValueError):
            derive_seed(training_seed=bad_seed, world_id="a.b", provider_kind="rnd", component="predictor")
    for bad_id in ("", None):
        with pytest.raises(ValueError):
            derive_seed(training_seed=42, world_id=bad_id, provider_kind="rnd", component="predictor")
    owned = original.to_dict()
    owned["seeds"]["a.b"]["predictor"] += 1
    assert original.to_dict() == portable
    with pytest.raises(ValueError):
        descriptor_type.from_dict(owned)
