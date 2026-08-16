"""Tests for VFS schema provenance hashes."""

import hashlib
from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.config.affordances_v2_config import ModulationParamConfig
from townlet.config.drive_as_code import (
    DriveAsCodeConfig,
    ExtrinsicStrategyConfig,
    IntrinsicStrategyConfig,
    VariableBonusConfig,
)
from townlet.environment.action_config import ActionConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto import RuntimeAction
from townlet.vfs import vtc
from townlet.vfs.schema import NormalizationSpec, ObservationField, VariableDef
from townlet.vfs.schema_hashes import (
    canonical_action_schema,
    canonical_observation_schema,
    canonical_transition_graph_schema,
    canonical_variable_schema,
    compute_action_schema_hash,
    compute_observation_schema_hash,
    compute_transition_graph_hash,
    compute_variable_schema_hash,
    compute_vfs_hash,
)
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.vfs.vtc import compile_vtc_action_writes_with_phase_graph, compile_vtc_threshold_cascades_with_phase_graph


def test_canonical_variable_schema_uses_sorted_contract_fields() -> None:
    """Variable schema hashes should be based on the explicit state ABI fields."""
    variable = VariableDef(
        id="energy",
        scope="agent",
        type="scalar",
        lifetime="tick",
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        default=1.0,
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
        description="Description is not part of the state ABI hash",
    )

    assert canonical_variable_schema((variable,)) == [
        {
            "id": "energy",
            "type": "scalar",
            "scope": "agent",
            "dims": None,
            "lifetime": "tick",
            "readable_by": ["agent", "engine"],
            "writable_by": ["engine"],
            "range": [0.0, 1.0],
        }
    ]


def test_variable_schema_hash_is_order_stable() -> None:
    """Variable order and permission ordering should not change the ABI hash."""
    energy = VariableDef(
        id="energy",
        scope="agent",
        type="scalar",
        lifetime="tick",
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        default=1.0,
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
    )
    position = VariableDef(
        id="position",
        scope="agent",
        type="vecNf",
        dims=2,
        lifetime="tick",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=[0.0, 0.0],
        normalization=NormalizationSpec(kind="minmax", min=[0.0, 0.0], max=[10.0, 10.0], clip=False),
    )
    energy_reordered_permissions = energy.model_copy(update={"readable_by": ["agent", "engine"]})

    left_hash = compute_variable_schema_hash((energy, position))
    right_hash = compute_variable_schema_hash((position, energy_reordered_permissions))

    assert left_hash == right_hash
    assert len(left_hash) == 64


def test_variable_schema_hash_changes_when_abi_field_changes() -> None:
    """Changing a hashed variable ABI field should produce a new digest."""
    variable = VariableDef(
        id="energy",
        scope="agent",
        type="scalar",
        lifetime="tick",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=1.0,
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
    )

    changed_range = variable.model_copy(update={"normalization": NormalizationSpec(kind="minmax", min=0.0, max=2.0, clip=False)})
    changed_permissions = variable.model_copy(update={"writable_by": ["engine", "vtc"]})

    assert compute_variable_schema_hash((variable,)) != compute_variable_schema_hash((changed_range,))
    assert compute_variable_schema_hash((variable,)) != compute_variable_schema_hash((changed_permissions,))


def test_compiler_surfaces_variable_schema_hash(tmp_path: Path) -> None:
    """UniverseCompiler should emit the variable schema hash on the compiled artifact."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    assert compiled.variable_schema_hash == compute_variable_schema_hash(compiled.vfs_variables)
    assert compiled.all_levels is not None
    assert compiled.all_levels[PRIMARY_LEVEL_NAME].variable_schema_hash == compiled.variable_schema_hash
    assert compiled.to_dict()["variable_schema_hash"] == compiled.variable_schema_hash


def test_canonical_observation_schema_uses_ordered_abi_fields() -> None:
    """Observation hashes should use the ordered field ABI, including normalization."""
    field = ObservationField(
        id="obs_energy",
        source_variable="energy",
        exposed_to=["engine", "agent"],
        shape=[1],
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
        semantic_type="bars",
        curriculum_active=True,
    )

    assert canonical_observation_schema((field,)) == [
        {
            "id": "obs_energy",
            "source_variable": "energy",
            "shape": [1],
            "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0, "clip": False},
            "exposed_to": ["agent", "engine"],
            "curriculum_active": True,
            "dtype": "float32",
            "semantic_type": "bars",
        }
    ]


def test_observation_schema_hash_changes_when_order_or_normalization_changes() -> None:
    """Observation field order and normalization are part of the checkpoint ABI."""
    energy = ObservationField(
        id="obs_energy",
        source_variable="energy",
        exposed_to=["agent"],
        shape=[1],
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
        semantic_type="bars",
    )
    position = ObservationField(
        id="obs_position",
        source_variable="position",
        exposed_to=["agent"],
        shape=[2],
        normalization=NormalizationSpec(kind="minmax", min=[0.0, 0.0], max=[10.0, 10.0], clip=False),
        semantic_type="spatial",
    )
    changed_normalization = energy.model_copy(update={"normalization": NormalizationSpec(kind="minmax", min=0.0, max=2.0, clip=False)})

    assert compute_observation_schema_hash((energy, position)) != compute_observation_schema_hash((position, energy))
    assert compute_observation_schema_hash((energy,)) != compute_observation_schema_hash((changed_normalization,))


def test_observation_schema_hash_is_stable_for_exposure_ordering() -> None:
    """Exposure lists represent an access set, so input ordering should not churn the hash."""
    field = ObservationField(
        id="obs_energy",
        source_variable="energy",
        exposed_to=["engine", "agent"],
        shape=[1],
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
        semantic_type="bars",
    )
    reordered = field.model_copy(update={"exposed_to": ["agent", "engine"]})

    assert compute_observation_schema_hash((field,)) == compute_observation_schema_hash((reordered,))


def test_compiler_surfaces_observation_schema_hash(tmp_path: Path) -> None:
    """UniverseCompiler should emit the observation schema hash on the compiled artifact."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    assert compiled.observation_schema_hash == compute_observation_schema_hash(compiled.vfs_observation_fields)
    assert compiled.all_levels is not None
    assert compiled.all_levels[PRIMARY_LEVEL_NAME].observation_schema_hash == compiled.observation_schema_hash
    assert compiled.to_dict()["observation_schema_hash"] == compiled.observation_schema_hash


def test_canonical_action_schema_uses_action_abi_fields() -> None:
    """Action hashes should use IDs, names, masks, movement shape, reads, and writes."""
    action = RuntimeAction(
        id=2,
        name="REST",
        type="passive",
        enabled=True,
        source="custom",
        costs={"energy": 0.1},
        effects={"mood": 0.2},
        delta=None,
        teleport_to=None,
        description="Descriptions are not part of the action ABI hash",
        icon=None,
        source_affordance=None,
        reads=("mood", "energy"),
        writes=(
            {
                "variable_id": "energy",
                "expression": "energy + 0.2",
                "condition": None,
                "composition": "additive_delta",
                "phase": "action_effects",
                "priority": 0,
                "clamp": [0.0, 1.0],
                "telemetry_label": "rest_energy_gain",
            },
        ),
    )

    assert canonical_action_schema((action,)) == [
        {
            "id": 2,
            "name": "REST",
            "type": "passive",
            "source": "custom",
            "enabled": True,
            "costs": {"energy": 0.1},
            "effects": {"mood": 0.2},
            "delta": None,
            "teleport_to": None,
            "source_affordance": None,
            "reads": ["energy", "mood"],
            "writes": [
                {
                    "variable_id": "energy",
                    "expression": "energy + 0.2",
                    "condition": None,
                    "composition": "additive_delta",
                    "phase": "action_effects",
                    "priority": 0,
                    "clamp": [0.0, 1.0],
                    "telemetry_label": "rest_energy_gain",
                }
            ],
        }
    ]


def test_action_schema_hash_sorts_by_action_id() -> None:
    """Action IDs define the policy ABI order, independent of tuple ordering."""
    wait = RuntimeAction(id=0, name="WAIT", type="passive", enabled=True, source="custom")
    rest = RuntimeAction(id=1, name="REST", type="passive", enabled=True, source="custom")

    assert compute_action_schema_hash((wait, rest)) == compute_action_schema_hash((rest, wait))


def test_action_schema_hash_changes_when_mask_or_reads_or_writes_change() -> None:
    """Enabled masks and declared dependencies are policy/action-space ABI fields."""
    base = RuntimeAction(id=0, name="REST", type="passive", enabled=True, source="custom", reads=("energy",))
    disabled = RuntimeAction(id=0, name="REST", type="passive", enabled=False, source="custom", reads=("energy",))
    changed_reads = RuntimeAction(id=0, name="REST", type="passive", enabled=True, source="custom", reads=("mood",))
    changed_writes = RuntimeAction(
        id=0,
        name="REST",
        type="passive",
        enabled=True,
        source="custom",
        reads=("energy",),
        writes=({"variable_id": "energy", "expression": "energy + 0.2"},),
    )

    assert compute_action_schema_hash((base,)) != compute_action_schema_hash((disabled,))
    assert compute_action_schema_hash((base,)) != compute_action_schema_hash((changed_reads,))
    assert compute_action_schema_hash((base,)) != compute_action_schema_hash((changed_writes,))


def test_compiler_surfaces_action_schema_hash(tmp_path: Path) -> None:
    """UniverseCompiler should emit the action schema hash on the compiled artifact."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    assert compiled.action_schema_hash == compute_action_schema_hash(compiled.runtime_action_space.actions)
    assert compiled.all_levels is not None
    assert compiled.all_levels[PRIMARY_LEVEL_NAME].action_schema_hash == compiled.action_schema_hash
    assert compiled.to_dict()["action_schema_hash"] == compiled.action_schema_hash


def test_transition_graph_hash_binds_phases_and_compiled_rule_fields() -> None:
    """Transition hashes should bind scheduler order and compiled action-write semantics."""
    phase_graph = TransitionPhaseGraph(("phase_a", "phase_b"))

    def make_action(*, expression: str, composition: str) -> ActionConfig:
        return ActionConfig(
            id=3,
            name="REST",
            type="passive",
            costs={},
            effects={},
            delta=None,
            teleport_to=None,
            enabled=True,
            description=None,
            icon=None,
            source="custom",
            source_affordance=None,
            reads=["energy"],
            writes=[
                {
                    "variable_id": "energy",
                    "expression": expression,
                    "condition": "energy < 0.8",
                    "composition": composition,
                    "phase": "phase_b",
                    "priority": 5,
                    "clamp": [0.0, 1.0],
                    "telemetry_label": "rest_energy_gain",
                }
            ],
        )

    action = make_action(expression="energy + 0.25", composition="additive_delta")
    program = compile_vtc_action_writes_with_phase_graph([action], phase_graph)

    assert canonical_transition_graph_schema(phase_graph, program) == {
        "phase_graph": {
            "phases": ["phase_a", "phase_b"],
            "edges": [{"before": "phase_a", "after": "phase_b"}],
        },
        "rules": [
            {
                "action_id": 3,
                "action_name": "REST",
                "variable_id": "energy",
                "expression": "energy + 0.25",
                "condition": "energy < 0.8",
                "composition": "additive_delta",
                "phase": "phase_b",
                "priority": 5,
                "clamp": [0.0, 1.0],
                "telemetry_label": "rest_energy_gain",
            }
        ],
    }

    baseline = compute_transition_graph_hash(phase_graph, program)
    reordered_graph = TransitionPhaseGraph(("phase_b", "phase_a"))
    changed_expression = make_action(expression="energy + 0.5", composition="additive_delta")
    changed_composition = make_action(expression="energy + 0.25", composition="overwrite")

    assert baseline != ""
    assert baseline != compute_transition_graph_hash(
        reordered_graph,
        compile_vtc_action_writes_with_phase_graph([action], reordered_graph),
    )
    assert baseline != compute_transition_graph_hash(
        phase_graph,
        compile_vtc_action_writes_with_phase_graph([changed_expression], phase_graph),
    )
    assert baseline != compute_transition_graph_hash(
        phase_graph, compile_vtc_action_writes_with_phase_graph([changed_composition], phase_graph)
    )


def test_transition_graph_hash_binds_modulation_rules() -> None:
    """Transition hashes should bind compiled affordance modulation semantics."""
    assert hasattr(vtc, "compile_vtc_modulations_with_phase_graph"), "VTC modulation compiler is required"

    phase_graph = TransitionPhaseGraph.default()
    action_program = compile_vtc_action_writes_with_phase_graph([], phase_graph)
    modulation = ModulationParamConfig(
        bar="energy",
        affordances=["WORK"],
        type="linear_multiplier",
        threshold=0.3,
        min_multiplier=0.5,
    )
    changed_modulation = modulation.model_copy(update={"min_multiplier": 0.25})

    modulation_program = vtc.compile_vtc_modulations_with_phase_graph([modulation], phase_graph)

    assert canonical_transition_graph_schema(phase_graph, action_program, modulation_program=modulation_program)["rules"] == [
        {
            "rule_id": "energy->WORK",
            "kind": "modulation",
            "source_variable_id": "energy",
            "target_affordance_id": "WORK",
            "variable_id": "affordance.WORK.multiplier",
            "expression": "where(bar.energy < 0.3, 0.5 + (1.0 - 0.5) * (bar.energy / 0.3), 1.0)",
            "condition": None,
            "composition": "multiplicative_modifier",
            "phase": "apply_modulations",
            "priority": 0,
            "clamp": [0.0, 1.0],
            "telemetry_label": "modulation:energy->WORK",
        }
    ]

    baseline = compute_transition_graph_hash(phase_graph, action_program, modulation_program=modulation_program)

    assert baseline != compute_transition_graph_hash(
        phase_graph,
        action_program,
        modulation_program=vtc.compile_vtc_modulations_with_phase_graph([changed_modulation], phase_graph),
    )


def test_transition_graph_hash_binds_passive_depletion_rules() -> None:
    """Transition hashes should bind compiled passive-depletion semantics."""
    assert hasattr(vtc, "compile_vtc_passive_depletions_with_phase_graph"), "VTC passive depletion compiler is required"

    phase_graph = TransitionPhaseGraph.default()
    action_program = compile_vtc_action_writes_with_phase_graph([], phase_graph)
    meter = {"name": "energy", "depletion": {"passive": 0.1}, "bounds": {"min": 0.0, "max": 1.0}}
    changed_meter = {"name": "energy", "depletion": {"passive": 0.2}, "bounds": {"min": 0.0, "max": 1.0}}

    passive_program = vtc.compile_vtc_passive_depletions_with_phase_graph([meter], phase_graph)

    assert canonical_transition_graph_schema(phase_graph, action_program, passive_depletion_program=passive_program)["rules"] == [
        {
            "rule_id": "passive:energy",
            "kind": "passive_depletion",
            "source_variable_id": "energy",
            "variable_id": "energy",
            "expression": "bar.energy - (0.1 * temporal.depletion_multiplier)",
            "condition": None,
            "composition": "overwrite",
            "phase": "apply_passive_depletion",
            "priority": 0,
            "clamp": [0.0, 1.0],
            "telemetry_label": "passive_depletion:energy",
        }
    ]

    baseline = compute_transition_graph_hash(phase_graph, action_program, passive_depletion_program=passive_program)

    assert baseline != compute_transition_graph_hash(
        phase_graph,
        action_program,
        passive_depletion_program=vtc.compile_vtc_passive_depletions_with_phase_graph([changed_meter], phase_graph),
    )


def test_transition_graph_hash_binds_interaction_progress_rules() -> None:
    """Transition hashes should bind VTC multi-tick progress and completion semantics."""
    phase_graph = TransitionPhaseGraph.default()
    action_program = compile_vtc_action_writes_with_phase_graph([], phase_graph)
    affordance = {"name": "SLEEP", "interaction_type": "multi_tick", "duration_ticks": 5}
    changed_affordance = {"name": "SLEEP", "interaction_type": "multi_tick", "duration_ticks": 6}

    interaction_program = vtc.compile_vtc_interaction_progress_with_phase_graph([affordance], phase_graph)

    assert canonical_transition_graph_schema(
        phase_graph,
        action_program,
        interaction_progress_program=interaction_program,
    )["rules"] == [
        {
            "rule_id": "sleep_advance_interaction_progress",
            "kind": "interaction_progress",
            "source_variable_id": "interaction_progress",
            "target_affordance_id": "SLEEP",
            "variable_id": "interaction_progress",
            "expression": "where(same_affordance and affordance_is_open and chosen_interact, interaction_progress + 1, 0)",
            "condition": None,
            "composition": "overwrite",
            "phase": "advance_interaction_progress",
            "priority": 0,
            "clamp": None,
            "telemetry_label": "interaction_progress:SLEEP",
            "duration_ticks": 5,
        },
        {
            "rule_id": "sleep_completion_bonus",
            "kind": "interaction_completion_bonus",
            "source_variable_id": "interaction_progress",
            "target_affordance_id": "SLEEP",
            "variable_id": "affordance.SLEEP.completed",
            "expression": "interaction_progress >= 5",
            "condition": None,
            "composition": "event",
            "phase": "apply_completion_bonuses",
            "priority": 0,
            "clamp": None,
            "telemetry_label": "interaction_completion_bonus:SLEEP",
            "duration_ticks": 5,
        },
    ]

    baseline = compute_transition_graph_hash(phase_graph, action_program, interaction_progress_program=interaction_program)

    assert baseline != compute_transition_graph_hash(
        phase_graph,
        action_program,
        interaction_progress_program=vtc.compile_vtc_interaction_progress_with_phase_graph([changed_affordance], phase_graph),
    )


def test_transition_graph_hash_binds_terminal_condition_rules() -> None:
    """Transition hashes should bind lethal meter terminal-condition semantics."""
    phase_graph = TransitionPhaseGraph.default()
    action_program = compile_vtc_action_writes_with_phase_graph([], phase_graph)
    meter = {"name": "energy", "bounds": {"min": 0.0, "max": 1.0, "lethal_min": True, "lethal_max": False}}
    changed_meter = {"name": "energy", "bounds": {"min": 0.25, "max": 1.0, "lethal_min": True, "lethal_max": False}}

    terminal_program = vtc.compile_vtc_terminal_conditions_with_phase_graph([meter], phase_graph)

    assert canonical_transition_graph_schema(phase_graph, action_program, terminal_condition_program=terminal_program)["rules"] == [
        {
            "rule_id": "terminal:energy:min",
            "kind": "terminal_condition",
            "source_variable_id": "energy",
            "variable_id": "done",
            "expression": "bar.energy <= 0.0",
            "condition": None,
            "composition": "event",
            "phase": "evaluate_terminal_conditions",
            "priority": 0,
            "clamp": None,
            "telemetry_label": "terminal_condition:energy:min",
            "operator": "<=",
            "threshold": 0.0,
        }
    ]

    baseline = compute_transition_graph_hash(phase_graph, action_program, terminal_condition_program=terminal_program)

    assert baseline != compute_transition_graph_hash(
        phase_graph,
        action_program,
        terminal_condition_program=vtc.compile_vtc_terminal_conditions_with_phase_graph([changed_meter], phase_graph),
    )


def test_transition_graph_hash_binds_reward_component_rules() -> None:
    """Transition hashes should bind compiled reward-component semantics."""
    assert hasattr(vtc, "compile_vtc_reward_components_with_phase_graph"), "VTC reward-component compiler is required"

    phase_graph = TransitionPhaseGraph.default()
    action_program = compile_vtc_action_writes_with_phase_graph([], phase_graph)

    def drive_config(*, weight: float) -> DriveAsCodeConfig:
        return DriveAsCodeConfig(
            version="1.0",
            extrinsic=ExtrinsicStrategyConfig(
                type="vfs_variable",
                variable_bonuses=[VariableBonusConfig(variable="custom_reward", weight=weight)],
            ),
            intrinsic=IntrinsicStrategyConfig(strategy="none", base_weight=0.0, apply_modifiers=[]),
            shaping=[],
        )

    reward_program = vtc.compile_vtc_reward_components_with_phase_graph(drive_config(weight=0.25), phase_graph)

    assert canonical_transition_graph_schema(
        phase_graph,
        action_program,
        reward_component_program=reward_program,
    )["rules"] == [
        {
            "rule_id": "reward:extrinsic:vfs_variable",
            "kind": "reward_component",
            "source_variable_id": "reward.extrinsic",
            "variable_id": "reward.extrinsic",
            "expression": "dac.extrinsic.vfs_variable",
            "condition": None,
            "composition": "overwrite",
            "phase": "compute_rewards",
            "priority": 0,
            "clamp": None,
            "telemetry_label": "reward_component:extrinsic",
            "reads": ["vfs.custom_reward"],
            "component": "extrinsic",
            "source_kind": "dac_extrinsic",
            "strategy": "vfs_variable",
            "shaping_type": None,
            "parameters": {
                "apply_modifiers": [],
                "bar_bonuses": [],
                "bars": [],
                "base": None,
                "base_reward": None,
                "type": "vfs_variable",
                "variable": None,
                "variable_bonuses": [{"variable": "custom_reward", "weight": 0.25}],
            },
        },
        {
            "rule_id": "reward:intrinsic:none",
            "kind": "reward_component",
            "source_variable_id": "intrinsic_raw",
            "variable_id": "reward.intrinsic",
            "expression": "intrinsic_raw * dac.intrinsic.weight",
            "condition": None,
            "composition": "overwrite",
            "phase": "compute_rewards",
            "priority": 1,
            "clamp": None,
            "telemetry_label": "reward_component:intrinsic",
            "reads": ["intrinsic_raw"],
            "component": "intrinsic",
            "source_kind": "dac_intrinsic",
            "strategy": "none",
            "shaping_type": None,
            "parameters": {
                "adaptive_config": None,
                "apply_modifiers": [],
                "base_weight": 0.0,
                "count_config": None,
                "icm_config": None,
                "rnd_config": None,
                "strategy": "none",
            },
        },
        {
            "rule_id": "reward:total",
            "kind": "reward_total",
            "source_variable_id": "reward.components",
            "variable_id": "reward.total",
            "expression": "reward.extrinsic + reward.intrinsic + reward.shaping",
            "condition": None,
            "composition": "sum",
            "phase": "compute_rewards",
            "priority": 2,
            "clamp": None,
            "telemetry_label": "reward_total",
            "reads": ["reward.extrinsic", "reward.intrinsic", "reward.shaping"],
            "component": "total",
            "source_kind": "reward_composition",
            "strategy": None,
            "shaping_type": None,
            "parameters": {"components": ["extrinsic", "intrinsic", "shaping"]},
        },
    ]

    baseline = compute_transition_graph_hash(phase_graph, action_program, reward_component_program=reward_program)

    assert baseline != compute_transition_graph_hash(
        phase_graph,
        action_program,
        reward_component_program=vtc.compile_vtc_reward_components_with_phase_graph(drive_config(weight=0.5), phase_graph),
    )


def test_transition_graph_hash_binds_social_residue_rules() -> None:
    """Transition hashes should bind compiled social-residue semantics."""
    assert hasattr(vtc, "compile_vtc_social_residue_rules_with_phase_graph"), "VTC social-residue compiler is required"

    phase_graph = TransitionPhaseGraph.default()
    action_program = compile_vtc_action_writes_with_phase_graph([], phase_graph)

    def social_program(*, delta: float) -> vtc.VTCSocialResidueProgram:
        return vtc.compile_vtc_social_residue_rules_with_phase_graph(
            [
                {
                    "id": "seen_stealing_damages_trust",
                    "phase": "apply_social_residue_effects",
                    "kind": "visibility_effect",
                    "reads": ["chosen_action", "observer_mask", "trust"],
                    "condition": "observer_mask and chosen_action == 7",
                    "writes": [
                        {
                            "variable_id": "trust",
                            "effect": "trust_delta",
                            "scope": "pair",
                            "target": "observer -> actor",
                            "expression": str(delta),
                            "composition": "additive_delta",
                            "clamp": [0.0, 1.0],
                        }
                    ],
                }
            ],
            phase_graph,
        )

    program = social_program(delta=-0.15)

    assert canonical_transition_graph_schema(
        phase_graph,
        action_program,
        social_residue_program=program,
    )["rules"] == [
        {
            "rule_id": "seen_stealing_damages_trust",
            "kind": "visibility_effect",
            "effect": "trust_delta",
            "variable_id": "trust",
            "expression": "-0.15",
            "condition": "observer_mask and chosen_action == 7",
            "composition": "additive_delta",
            "phase": "apply_social_residue_effects",
            "priority": 0,
            "clamp": [0.0, 1.0],
            "telemetry_label": "visibility_effect:seen_stealing_damages_trust:trust_delta",
            "reads": ["chosen_action", "observer_mask", "trust"],
            "scope": "pair",
            "target": "observer -> actor",
        }
    ]

    baseline = compute_transition_graph_hash(phase_graph, action_program, social_residue_program=program)
    assert baseline != compute_transition_graph_hash(
        phase_graph,
        action_program,
        social_residue_program=social_program(delta=-0.25),
    )


def test_vfs_hash_combines_component_hashes_and_transition_graph() -> None:
    """The VFS identity should bind all component hashes, including the transition graph."""
    variable_hash = "a" * 64
    observation_hash = "b" * 64
    action_hash = "c" * 64
    transition_hash = "d" * 64

    expected = hashlib.sha256((variable_hash + observation_hash + action_hash + transition_hash).encode("utf-8")).hexdigest()

    assert compute_vfs_hash(variable_hash, observation_hash, action_hash, transition_hash) == expected
    assert compute_vfs_hash("e" * 64, observation_hash, action_hash, transition_hash) != expected
    assert compute_vfs_hash(variable_hash, "e" * 64, action_hash, transition_hash) != expected
    assert compute_vfs_hash(variable_hash, observation_hash, "f" * 64, transition_hash) != expected
    assert compute_vfs_hash(variable_hash, observation_hash, action_hash, "g" * 64) != expected


def test_compiler_surfaces_vfs_hash(tmp_path: Path) -> None:
    """UniverseCompiler should emit the combined VFS hash on compiled artifacts."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    phase_graph = TransitionPhaseGraph.default()
    expected = compute_vfs_hash(
        compiled.variable_schema_hash,
        compiled.observation_schema_hash,
        compiled.action_schema_hash,
        compiled.transition_graph_hash,
    )

    assert compiled.transition_graph_hash != ""
    assert compiled.transition_graph_hash == compute_transition_graph_hash(
        phase_graph,
        compile_vtc_action_writes_with_phase_graph(compiled.runtime_action_space.actions, phase_graph),
        affordance_gate_program=vtc.compile_vtc_affordance_gates_with_phase_graph(
            compiled.get_level(PRIMARY_LEVEL_NAME).affordances.affordances,
            phase_graph,
        ),
        interaction_progress_program=vtc.compile_vtc_interaction_progress_with_phase_graph(
            compiled.get_level(PRIMARY_LEVEL_NAME).affordances.affordances,
            phase_graph,
        ),
        terminal_condition_program=vtc.compile_vtc_terminal_conditions_with_phase_graph(
            compiled.get_level(PRIMARY_LEVEL_NAME).bars.meters,
            phase_graph,
        ),
        threshold_cascade_program=compile_vtc_threshold_cascades_with_phase_graph(
            compiled.get_level(PRIMARY_LEVEL_NAME).bars.cascades,
            compiled.get_level(PRIMARY_LEVEL_NAME).bars.meters,
            phase_graph,
        ),
        modulation_program=vtc.compile_vtc_modulations_with_phase_graph(
            compiled.get_level(PRIMARY_LEVEL_NAME).affordances.modulations,
            phase_graph,
        ),
        passive_depletion_program=vtc.compile_vtc_passive_depletions_with_phase_graph(
            compiled.get_level(PRIMARY_LEVEL_NAME).bars.meters,
            phase_graph,
        ),
        reward_component_program=vtc.compile_vtc_reward_components_with_phase_graph(
            compiled.get_level(PRIMARY_LEVEL_NAME).drive,
            phase_graph,
        ),
    )
    assert compiled.vfs_hash == expected
    assert compiled.all_levels is not None
    assert compiled.all_levels[PRIMARY_LEVEL_NAME].transition_graph_hash == compiled.transition_graph_hash
    assert compiled.all_levels[PRIMARY_LEVEL_NAME].vfs_hash == compiled.vfs_hash
    assert compiled.to_dict()["transition_graph_hash"] == compiled.transition_graph_hash
    assert compiled.to_dict()["vfs_hash"] == compiled.vfs_hash
