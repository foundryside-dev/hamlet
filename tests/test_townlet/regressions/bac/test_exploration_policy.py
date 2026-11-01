"""Authored exploration boundary: real DTOs, ownership, identity and transport."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import torch
import yaml

from townlet.config.bac_options import BaCOptions, resolve_bac_options
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.training_v2_config import TrainingV2Config, load_training_v2_config

ROOT = Path(__file__).resolve().parents[4]
PACK = ROOT / "configs/default_curriculum"


def boundary():
    assert importlib.util.find_spec("townlet.config.exploration_policy"), "authored exploration resolver interface missing"
    return importlib.import_module("townlet.config.exploration_policy")


def authored(strategy="adaptive_rnd", **changes):
    training = load_training_v2_config(PACK / "levels/L0_0_minimal")
    drive = yaml.safe_load((PACK / "levels/L0_0_minimal/drive.yaml").read_text())["drive"]["intrinsic"]
    drive["strategy"] = strategy
    drive.update(changes)
    return IntrinsicStrategyConfig.model_validate(drive), training


def resolve(strategy="adaptive_rnd", options=None, **changes):
    drive, training = authored(strategy, **changes)
    return boundary().resolve_exploration_policy(drive, training, BaCOptions.model_validate(options or {}))


@pytest.mark.parametrize("strategy", ["none", "rnd", "adaptive_rnd", "count_based", "icm"])
def test_drive_selects_five_strategies(strategy):
    drive, training = authored(strategy)
    policy = boundary().resolve_exploration_policy(drive, training, BaCOptions())
    assert policy.strategy == strategy
    assert policy.epsilon_start == training.exploration.epsilon_start
    assert policy.initial_intrinsic_weight == training.intrinsic.initial_weight
    assert policy.drive_base_weight == drive.base_weight
    assert policy.modifier_names == tuple(drive.apply_modifiers)
    assert policy.reward_observation_phase == "successor_postphysics"
    assert policy.predictor_observation_phase == "eligible_predecessor"
    assert policy.predictor_input_kind == ("transition" if strategy == "icm" else "observation")
    assert not hasattr(policy, "enabled")
    if strategy == "none":
        assert policy.provider_parameters == {}
    if strategy == "count_based":
        assert dict(policy.provider_parameters) == {"quantization_width": 1 / 16, "max_entries": training.replay_buffer.capacity}
    if strategy == "icm":
        assert policy.provider_parameters["hidden_dim"] == 2 * training.intrinsic.rnd.feature_dim
        assert policy.provider_parameters["max_pending_transitions"] == max(2 * training.population.size, training.replay_buffer.batch_size)


def test_training_drive_override_roles():
    drive, training = authored(
        "adaptive_rnd",
        rnd_config={"feature_dim": 17, "learning_rate": 0.002, "future": {"a": [1, 2]}},
        count_config={"quantization_width": 0.7},
    )
    api = boundary()
    policy = api.resolve_exploration_policy(drive, training, BaCOptions())
    assert policy.rnd_feature_dim == training.intrinsic.rnd.feature_dim
    assert policy.variance_threshold == training.intrinsic.annealing.threshold
    assert policy.field_roles["drive.intrinsic.rnd_config.feature_dim"].status == "inactive_preset"
    assert policy.field_roles["drive.intrinsic.rnd_config.future.a"].status == "inactive_preset"
    assert policy.raw_provider_parameters["rnd_config"]["future"]["a"] == (1, 2)
    selected = api.resolve_exploration_policy(drive, training, BaCOptions(provider_parameter_source="drive"))
    assert selected.rnd_feature_dim == 17
    assert selected.rnd_learning_rate == 0.002
    assert selected.min_intrinsic_weight == 0.01
    assert selected.field_roles["drive.intrinsic.adaptive_config.min_weight"].status == "active"
    assert selected.field_roles["training.intrinsic.rnd.feature_dim"].status == "inactive_preset"
    assert selected.field_roles["training.intrinsic.annealing.min_weight"].status == "inactive_preset"
    assert selected.field_roles["provider_parameters.feature_dim"].origin == "drive.intrinsic.rnd_config.feature_dim"
    assert selected.epsilon_start == training.exploration.epsilon_start
    assert selected.initial_intrinsic_weight == training.intrinsic.initial_weight
    count = resolve(
        "count_based",
        options={"providers": {"count_based": {"quantization_width": 0.25}}},
        count_config={"quantization_width": 0.5, "max_entries": 19, "custom": ["retained"]},
    )
    assert dict(count.provider_parameters) == {"quantization_width": 0.25, "max_entries": 19}
    assert count.field_roles["drive.intrinsic.count_config.quantization_width"].status == "inactive_preset"
    assert count.field_roles["bac_options.providers.count_based.quantization_width"].status == "active"
    assert count.field_roles["training.intrinsic.annealing.threshold"].status == "inactive_preset"
    assert count.field_roles["drive.intrinsic.count_config.custom"].status == "inactive_preset"


@pytest.mark.parametrize(
    "options,raw,expected",
    [
        ({}, {"feature_dim": 7, "training_batch_size": 40}, {"feature_dim": 7, "hidden_dim": 14, "max_pending_transitions": 40}),
        (
            {"providers": {"icm": {"feature_dim": 9, "training_batch_size": 50}}},
            {"feature_dim": 7},
            {"feature_dim": 9, "hidden_dim": 18, "max_pending_transitions": 50},
        ),
    ],
)
def test_icm_dependent_derivations_follow_selected_values(options, raw, expected):
    policy = resolve("icm", options=options, icm_config=raw)
    for key, value in expected.items():
        assert policy.provider_parameters[key] == value
    assert policy.field_roles["provider_parameters.hidden_dim"].status == "derived"


@pytest.mark.parametrize(
    "strategy,raw",
    [
        ("rnd", {"rnd_config": {"learning_rate": float("nan")}}),
        ("adaptive_rnd", {"adaptive_config": {"threshold": float("inf")}}),
        ("count_based", {"count_config": {"quantization_width": float("inf")}}),
        ("icm", {"icm_config": {"inverse_weight": float("nan")}}),
    ],
)
def test_nonfinite_active_parameters_are_located(strategy, raw):
    drive, training = authored(strategy, **raw)
    with pytest.raises(ValueError, match=r"drive\.intrinsic\..*finite"):
        boundary().resolve_exploration_policy(drive, training, BaCOptions(provider_parameter_source="drive"))


def test_equal_precedence_conflict_is_located_and_presets_do_not_conflict():
    drive, training = authored("adaptive_rnd", rnd_config={"feature_dim": 7}, adaptive_config={"rnd_feature_dim": 8})
    api = boundary()
    assert api.resolve_exploration_policy(drive, training, BaCOptions()).rnd_feature_dim == 128
    with pytest.raises(ValueError, match=r"drive\.intrinsic\.rnd_config\.feature_dim.*drive\.intrinsic\.adaptive_config\.rnd_feature_dim"):
        api.resolve_exploration_policy(drive, training, BaCOptions(provider_parameter_source="drive"))


def test_zero_initial_scale_and_none_are_distinct():
    drive, training = authored("adaptive_rnd")
    payload = training.model_dump()
    payload["intrinsic"]["initial_weight"] = 0.0
    zero = TrainingV2Config.model_validate(payload)
    policy = boundary().resolve_exploration_policy(drive, zero, BaCOptions())
    assert policy.initial_intrinsic_weight == 0
    assert policy.strategy == "adaptive_rnd"
    assert policy.field_roles["initial_intrinsic_weight"].status == "active"
    assert policy.policy_identity != resolve("none").policy_identity


@pytest.mark.parametrize(
    "strategy,section,key,value",
    [
        ("rnd", "exploration", "epsilon_start", 0.9),
        ("rnd", "exploration", "epsilon_end", 0.02),
        ("rnd", "exploration", "epsilon_decay", 0.9),
        ("rnd", "intrinsic", "initial_weight", 0.0),
        ("adaptive_rnd", "intrinsic", "min_survival_fraction", 0.5),
        ("adaptive_rnd", "intrinsic", "survival_window", 12),
        ("adaptive_rnd", "training_loop", "max_steps_per_episode", 99),
    ],
)
def test_active_training_knobs_change_identity(strategy, section, key, value):
    drive, training = authored(strategy)
    api = boundary()
    before = api.resolve_exploration_policy(drive, training, BaCOptions())
    payload = training.model_dump()
    payload[section][key] = value
    after = api.resolve_exploration_policy(drive, TrainingV2Config.model_validate(payload), BaCOptions())
    assert before.policy_identity != after.policy_identity


@pytest.mark.parametrize(
    "strategy,block,values",
    [
        ("rnd", "rnd_config", {"feature_dim": 9, "learning_rate": 0.002, "predictor_batch_size": 8}),
        ("adaptive_rnd", "adaptive_config", {"threshold": 5.0, "decay_rate": 0.9, "min_weight": 0.1}),
        ("count_based", "count_config", {"quantization_width": 0.2, "max_entries": 4}),
        (
            "icm",
            "icm_config",
            {
                "feature_dim": 7,
                "hidden_dim": 9,
                "learning_rate": 0.002,
                "inverse_weight": 0.3,
                "forward_weight": 0.7,
                "training_batch_size": 8,
                "max_pending_transitions": 40,
            },
        ),
    ],
)
def test_each_selected_provider_parameter_changes_identity(strategy, block, values):
    baseline = resolve(strategy, options={"provider_parameter_source": "drive"})
    for key, value in values.items():
        changed = resolve(strategy, options={"provider_parameter_source": "drive"}, **{block: {key: value}})
        assert baseline.policy_identity != changed.policy_identity, key


def test_presets_change_only_authored_identity_and_own_immutable_copies():
    drive, training = authored("rnd", rnd_config={"feature_dim": 17, "nested": {"values": [1, 2]}})
    api = boundary()
    first = api.resolve_exploration_policy(drive, training, BaCOptions())
    drive.rnd_config["nested"]["values"].append(3)
    second = api.resolve_exploration_policy(drive, training, BaCOptions())
    assert first.policy_identity == second.policy_identity
    assert first.authored_identity != second.authored_identity
    assert first.raw_provider_parameters["rnd_config"]["nested"]["values"] == (1, 2)
    with pytest.raises(TypeError):
        first.provider_parameters["feature_dim"] = 4
    with pytest.raises(FrozenInstanceError):
        first.strategy = "none"
    portable = first.to_dict()
    portable["raw_provider_parameters"]["rnd_config"]["nested"]["values"].append(9)
    assert first.raw_provider_parameters["rnd_config"]["nested"]["values"] == (1, 2)
    clone = api.ResolvedExplorationPolicy.from_dict(yaml.safe_load(yaml.safe_dump(first.to_dict())))
    assert clone.policy_identity == first.policy_identity
    assert clone.to_dict() == first.to_dict()


def test_service_options_identity_roles_and_capacity():
    before = resolve("rnd")
    assert before.service_mode == "paced_fifo"
    for key, value in {
        "service_mode": "occupancy_fifo",
        "max_updates_per_tick": 2,
        "max_pending_rows": 100,
        "overflow_policy": "drop_newest",
    }.items():
        assert resolve("rnd", options={"rnd": {key: value}}).policy_identity != before.policy_identity
        assert resolve("none", options={"rnd": {key: value}}).policy_identity == resolve("none").policy_identity
    with pytest.raises(ValueError, match="max_pending"):
        resolve("icm", icm_config={"training_batch_size": 40, "max_pending_transitions": 39})
    with pytest.raises(ValueError, match="max_pending"):
        resolve(
            "rnd", options={"provider_parameter_source": "drive", "rnd": {"max_pending_rows": 32}}, rnd_config={"predictor_batch_size": 40}
        )


def test_transition_context_owns_tensor_copies_and_receipt_schema():
    api = boundary()
    predecessor, successor = torch.zeros(2, 3), torch.ones(2, 3)
    actions, active = torch.tensor([0, 1]), torch.tensor([True, False])
    context = api.IntrinsicTransitionContext(
        predecessor=predecessor, actions=actions, successor=successor, active_on_entry=active, vector_tick=3
    )
    predecessor.add_(7)
    assert context.predecessor.equal(torch.zeros(2, 3))
    context.predecessor.add_(9)
    assert context.predecessor.equal(torch.zeros(2, 3))
    assert context.successor.equal(successor) and context.vector_tick == 3
    with pytest.raises(ValueError, match="shape"):
        api.IntrinsicTransitionContext(
            predecessor=predecessor, actions=actions[:1], successor=successor, active_on_entry=active, vector_tick=3
        )
    receipt = api.ExplorationServiceReceipt(
        provider="none",
        admitted_rows=0,
        consumed_rows=0,
        dropped_rows=0,
        pending_rows=0,
        optimizer_updates=0,
        mandatory_service_updates=0,
        last_loss=0.0,
    )
    assert receipt.provider == "none" and receipt.optimizer_updates == 0


def test_compiler_transport_preserves_authored_resolution(tmp_path):
    import shutil

    from townlet.universe.compiler import UniverseCompiler

    api = boundary()
    pack = tmp_path / "pack"
    shutil.copytree(PACK, pack, ignore=shutil.ignore_patterns(".compiled"))
    path = pack / "levels/L0_0_minimal/training.yaml"
    raw = yaml.safe_load(path.read_text())
    raw["training"]["bac_options"] = {"providers": {"icm": {"feature_dim": 7}}}
    path.write_text(yaml.safe_dump(raw))
    drive_path = pack / "levels/L0_0_minimal/drive.yaml"
    drive_document = yaml.safe_load(drive_path.read_text())
    drive_document["drive"]["intrinsic"].update(strategy="icm", icm_config={"hidden_dim": 11, "future": [1]})
    drive_path.write_text(yaml.safe_dump(drive_document))
    compiled = UniverseCompiler().compile(pack, primary_level="L0_0_minimal", use_cache=False)
    loaded = type(compiled).from_dict(compiled.to_dict())
    training = loaded.all_levels["L0_0_minimal"].training
    drive = loaded.all_levels["L0_0_minimal"].drive.intrinsic
    options = training.bac_options
    assert options.providers.icm.feature_dim == 7
    policy = api.resolve_exploration_policy(drive, training, options)
    assert policy.provider_parameters["feature_dim"] == 7 and policy.provider_parameters["hidden_dim"] == 11
    assert policy.raw_provider_parameters["icm_config"]["future"] == (1,)
    assert policy.execution_identity() == api.ResolvedExplorationPolicy.from_dict(policy.to_dict()).policy_identity
    changed = drive.model_copy(deep=True)
    changed.icm_config["future"].append(2)
    preset = api.resolve_exploration_policy(changed, training, options)
    assert preset.authored_identity != policy.authored_identity and preset.policy_identity == policy.policy_identity
    resolved_options = resolve_bac_options(options, training=training)
    assert resolved_options.schema_version == "bac-options-v1"


def test_training_derivation_roles_are_truthful():
    icm = resolve("icm")
    assert icm.field_roles["provider_parameters.feature_dim"].origin == "training.intrinsic.rnd.feature_dim"
    assert icm.field_roles["training.intrinsic.rnd.feature_dim"].status == "derived"
    assert icm.field_roles["rnd_feature_dim"].status == "inactive_preset"
    count = resolve("count_based")
    assert count.field_roles["provider_parameters.max_entries"].origin == "training.replay_buffer.capacity"
    drive_batch = resolve("rnd", options={"provider_parameter_source": "drive"}, rnd_config={"predictor_batch_size": 40})
    assert drive_batch.max_pending_rows == 40
    assert "resolved predictor_batch_size" in drive_batch.field_roles["max_pending_rows"].reason


def test_portable_policy_rejects_corrupt_active_scalar():
    api = boundary()
    payload = resolve("rnd").to_dict()
    payload["rnd_learning_rate"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        api.ResolvedExplorationPolicy.from_dict(payload)


def test_drive_weight_modifiers_and_nonselected_options_identity():
    for strategy in ("none", "rnd", "adaptive_rnd", "count_based", "icm"):
        before = resolve(strategy)
        for edit in ({"base_weight": 0.3}, {"apply_modifiers": ["other_modifier"]}):
            changed = resolve(strategy, **edit)
            assert (before.policy_identity != changed.policy_identity) == (strategy != "none")
        preset = resolve(strategy, options={"providers": {"count_based": {"max_entries": 13}}})
        assert (before.policy_identity != preset.policy_identity) == (strategy == "count_based")
        assert before.authored_identity != preset.authored_identity


@pytest.mark.parametrize("strategy", ["rnd", "adaptive_rnd", "icm"])
@pytest.mark.parametrize("capacity", [8, 7, None])
def test_capacity_uses_final_selected_batch(strategy, capacity):
    raw_key, batch_key = "rnd_config", "predictor_batch_size"
    options = {"provider_parameter_source": "drive"}
    if strategy == "icm":
        raw_key, batch_key = "icm_config", "training_batch_size"
        if capacity is not None:
            options["providers"] = {"icm": {"max_pending_transitions": capacity}}
    elif capacity is not None:
        options["rnd"] = {"max_pending_rows": capacity}
    if capacity == 7:
        with pytest.raises(ValueError, match="max_pending"):
            resolve(strategy, options=options, **{raw_key: {batch_key: 8}})
    else:
        policy = resolve(strategy, options=options, **{raw_key: {batch_key: 8}})
        assert policy.predictor_batch_size == 8
        expected = 16 if capacity is None else capacity
        assert policy.max_pending_rows == expected
        if capacity is not None:
            path = "max_pending_rows"
            if strategy == "icm":
                path = "provider_parameters.max_pending_transitions"
            assert policy.field_roles[path].status == "active"


def test_typed_icm_batch_beats_raw_before_capacity_validation():
    policy = resolve(
        "icm",
        options={"providers": {"icm": {"training_batch_size": 4, "max_pending_transitions": 4}}},
        icm_config={"training_batch_size": 8},
    )
    assert policy.predictor_batch_size == policy.max_pending_rows == 4


def test_standalone_options_still_validate_training_owned_capacity():
    _, training = authored()
    for payload in ({"rnd": {"max_pending_rows": 8}}, {"providers": {"icm": {"max_pending_transitions": 8}}}):
        with pytest.raises(ValueError, match="max_pending"):
            resolve_bac_options(BaCOptions.model_validate(payload), training=training)


def reconstruct(payload, method):
    api = boundary()
    if method == "portable":
        return api.ResolvedExplorationPolicy.from_dict(payload)
    direct = dict(payload)
    direct["field_roles"] = {path: api.FieldRole(**role) for path, role in direct["field_roles"].items()}
    return api.ResolvedExplorationPolicy(**direct)


@pytest.mark.parametrize("method", ["portable", "constructor"])
@pytest.mark.parametrize(
    "strategy,key,value",
    [
        ("rnd", "feature_dim", 7),
        ("rnd", "learning_rate", 0.2),
        ("rnd", "predictor_batch_size", 8),
        ("adaptive_rnd", "variance_threshold", 2.0),
        ("icm", "training_batch_size", 8),
        ("icm", "max_pending_transitions", 99),
    ],
)
def test_policy_rejects_contradictory_selected_values(method, strategy, key, value):
    payload = resolve(strategy).to_dict()
    payload["provider_parameters"][key] = value
    with pytest.raises(ValueError, match=rf"provider_parameters\.{key}"):
        reconstruct(payload, method)


@pytest.mark.parametrize("method", ["portable", "constructor"])
@pytest.mark.parametrize("strategy", ["none", "rnd", "adaptive_rnd", "count_based", "icm"])
def test_policy_requires_exact_selected_provider_schema(method, strategy):
    payload = resolve(strategy).to_dict()
    payload["provider_parameters"]["not_a_selected_parameter"] = 1.0
    with pytest.raises(ValueError, match="provider_parameters"):
        reconstruct(payload, method)
    if strategy != "none":
        payload["provider_parameters"] = {}
        with pytest.raises(ValueError, match="provider_parameters"):
            reconstruct(payload, method)


@pytest.mark.parametrize("method", ["portable", "constructor"])
@pytest.mark.parametrize(
    "strategy,scalar",
    [("rnd", "rnd_feature_dim"), ("rnd", "rnd_learning_rate"), ("adaptive_rnd", "variance_threshold"), ("icm", "predictor_batch_size")],
)
def test_transported_roles_cannot_hide_active_scalar_nan(method, strategy, scalar):
    payload = resolve(strategy).to_dict()
    payload[scalar] = float("nan")
    payload["field_roles"][scalar]["status"] = "inactive_preset"
    with pytest.raises(ValueError, match=rf"{scalar}.*finite"):
        reconstruct(payload, method)


@pytest.mark.parametrize("method", ["portable", "constructor"])
def test_roles_cannot_remove_valid_active_scalar_from_identity(method):
    payload = resolve("rnd").to_dict()
    payload["field_roles"]["rnd_feature_dim"]["status"] = "inactive_preset"
    with pytest.raises(ValueError, match=r"field_roles\.rnd_feature_dim"):
        reconstruct(payload, method)


@pytest.mark.parametrize("method", ["portable", "constructor"])
@pytest.mark.parametrize("strategy", ["none", "rnd", "adaptive_rnd", "count_based", "icm"])
def test_all_selected_policies_roundtrip_with_inactive_presets(method, strategy):
    policy = resolve(strategy, rnd_config={"future": {"retained": [1, 2]}})
    payload = policy.to_dict()
    rebuilt = reconstruct(payload, method)
    assert rebuilt.to_dict() == payload
    assert rebuilt.policy_identity == policy.policy_identity
    if strategy in ("none", "count_based", "icm"):
        payload["rnd_feature_dim"] = 7
        inactive = reconstruct(payload, method)
        assert inactive.rnd_feature_dim == 7 and inactive.policy_identity == policy.policy_identity
