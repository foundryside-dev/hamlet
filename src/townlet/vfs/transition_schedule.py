"""Compiled VTC transition schedule and generic runtime executor."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import torch

from townlet.vfs.schema import VariableDef
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.vfs.vtc import (
    VTCActionWriteProgram,
    VTCAffordanceGateProgram,
    VTCBoundsClampProgram,
    VTCInteractionProgressProgram,
    VTCModulationProgram,
    VTCPassiveDepletionProgram,
    VTCRewardProgram,
    VTCSocialResidueProgram,
    VTCTerminalConditionProgram,
    VTCThresholdCascadeProgram,
    compile_vtc_affordance_gates_with_phase_graph,
    compile_vtc_affordance_occupancy_with_phase_graph,
    compile_vtc_bounds_clamps_with_phase_graph,
    compile_vtc_interaction_progress_with_phase_graph,
    compile_vtc_modulations_with_phase_graph,
    compile_vtc_passive_depletions_with_phase_graph,
    compile_vtc_reward_components_with_phase_graph,
    compile_vtc_social_residue_rules_with_phase_graph,
    compile_vtc_terminal_conditions_with_phase_graph,
    compile_vtc_threshold_cascades_with_phase_graph,
)


@dataclass(frozen=True)
class VTCTransitionSchedule:
    """Runtime-ready VTC programs bound to a transition phase graph."""

    phase_graph: TransitionPhaseGraph
    action_write_program: VTCActionWriteProgram
    affordance_gate_program: VTCAffordanceGateProgram
    interaction_progress_program: VTCInteractionProgressProgram
    terminal_condition_program: VTCTerminalConditionProgram
    passive_depletion_program: VTCPassiveDepletionProgram
    modulation_program: VTCModulationProgram
    threshold_cascade_program: VTCThresholdCascadeProgram
    social_residue_program: VTCSocialResidueProgram
    reward_component_program: VTCRewardProgram
    bounds_clamp_program: VTCBoundsClampProgram


@dataclass(frozen=True)
class VTCTransitionContext:
    """Snapshot supplied to one or more generic transition phases."""

    vfs_state: Mapping[str, torch.Tensor]
    bars_state: Mapping[str, torch.Tensor]
    active_mask: torch.Tensor
    device: torch.device
    actions: torch.Tensor | None = None
    dones: torch.Tensor | None = None
    depletion_multiplier: float = 1.0


@dataclass(frozen=True)
class VTCTransitionState:
    """Updated state returned by the generic transition runner."""

    vfs_state: dict[str, torch.Tensor]
    bars_state: dict[str, torch.Tensor]
    dones: torch.Tensor | None


class VTCTransitionRunner:
    """Execute compiled transition programs by configured phase name."""

    def __init__(self, schedule: VTCTransitionSchedule) -> None:
        self.schedule = schedule

    def phases_through(self, phase: str) -> tuple[str, ...]:
        """Return all configured phases through the named phase, inclusive."""
        index = self.schedule.phase_graph.sort_key(phase)
        return self.schedule.phase_graph.ordered_phases[: index + 1]

    def phases_between(self, after_phase: str, before_phase: str) -> tuple[str, ...]:
        """Return configured phases after one boundary and before another."""
        after_index = self.schedule.phase_graph.sort_key(after_phase)
        before_index = self.schedule.phase_graph.sort_key(before_phase)
        if after_index >= before_index:
            raise ValueError(f"Phase '{after_phase}' must precede phase '{before_phase}'")
        return self.schedule.phase_graph.ordered_phases[after_index + 1 : before_index]

    def run_phase(self, phase: str, context: VTCTransitionContext) -> VTCTransitionState:
        """Run all compiled transition programs scheduled for one phase."""
        return self.run_phases((phase,), context)

    def run_phases(self, phases: Sequence[str], context: VTCTransitionContext) -> VTCTransitionState:
        """Run compiled transition programs for the supplied phases in order."""
        vfs_state = {name: value.to(device=context.device).clone() for name, value in context.vfs_state.items()}
        bars_state = {name: value.to(device=context.device).clone() for name, value in context.bars_state.items()}
        dones = None if context.dones is None else context.dones.to(device=context.device, dtype=torch.bool).clone()

        for phase in phases:
            self.schedule.phase_graph.sort_key(phase)
            vfs_state, bars_state = self._run_action_writes(phase, context, vfs_state, bars_state)
            bars_state = self._run_passive_depletions(phase, context, bars_state)
            bars_state = self._run_threshold_cascades(phase, context, bars_state)
            vfs_state = self._run_state_residue(phase, context, vfs_state, bars_state)
            bars_state = self._run_bounds_clamps(phase, context, bars_state)
            dones = self._run_terminal_conditions(phase, context, bars_state, dones)

        return VTCTransitionState(vfs_state=vfs_state, bars_state=bars_state, dones=dones)

    def _run_action_writes(
        self,
        phase: str,
        context: VTCTransitionContext,
        vfs_state: dict[str, torch.Tensor],
        bars_state: dict[str, torch.Tensor],
    ) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
        writes = tuple(write for write in self.schedule.action_write_program.writes if write.phase == phase)
        if not writes:
            return vfs_state, bars_state
        if context.actions is None:
            raise ValueError(f"Transition phase '{phase}' requires actions for VTC action writes")

        updated = VTCActionWriteProgram(writes).apply(
            actions=context.actions,
            vfs_state=vfs_state,
            bars_state=bars_state,
            active_mask=context.active_mask,
            device=context.device,
        )
        return _split_vfs_and_bars(updated, vfs_state.keys(), bars_state.keys())

    def _run_passive_depletions(
        self,
        phase: str,
        context: VTCTransitionContext,
        bars_state: dict[str, torch.Tensor],
    ) -> dict[str, torch.Tensor]:
        rules = tuple(rule for rule in self.schedule.passive_depletion_program.rules if rule.phase == phase)
        if not rules:
            return bars_state
        return VTCPassiveDepletionProgram(rules).apply(
            bars_state=bars_state,
            active_mask=context.active_mask,
            device=context.device,
            depletion_multiplier=context.depletion_multiplier,
        )

    def _run_threshold_cascades(
        self,
        phase: str,
        context: VTCTransitionContext,
        bars_state: dict[str, torch.Tensor],
    ) -> dict[str, torch.Tensor]:
        rules = tuple(rule for rule in self.schedule.threshold_cascade_program.rules if rule.phase == phase)
        if not rules:
            return bars_state
        return VTCThresholdCascadeProgram(rules).apply(
            bars_state=bars_state,
            active_mask=context.active_mask,
            device=context.device,
        )

    def _run_state_residue(
        self,
        phase: str,
        context: VTCTransitionContext,
        vfs_state: dict[str, torch.Tensor],
        bars_state: dict[str, torch.Tensor],
    ) -> dict[str, torch.Tensor]:
        rules = tuple(rule for rule in self.schedule.social_residue_program.rules if rule.phase == phase)
        if not rules:
            return vfs_state
        return VTCSocialResidueProgram(rules).apply(
            vfs_state=vfs_state,
            active_mask=context.active_mask,
            device=context.device,
            bars_state=bars_state,
        )

    def _run_bounds_clamps(
        self,
        phase: str,
        context: VTCTransitionContext,
        bars_state: dict[str, torch.Tensor],
    ) -> dict[str, torch.Tensor]:
        rules = tuple(rule for rule in self.schedule.bounds_clamp_program.rules if rule.phase == phase)
        if not rules:
            return bars_state
        return VTCBoundsClampProgram(rules).apply(
            bars_state=bars_state,
            device=context.device,
        )

    def _run_terminal_conditions(
        self,
        phase: str,
        context: VTCTransitionContext,
        bars_state: dict[str, torch.Tensor],
        dones: torch.Tensor | None,
    ) -> torch.Tensor | None:
        rules = tuple(rule for rule in self.schedule.terminal_condition_program.rules if rule.phase == phase)
        if not rules:
            return dones
        if dones is None:
            raise ValueError(f"Transition phase '{phase}' requires dones for VTC terminal conditions")
        return VTCTerminalConditionProgram(rules).apply(
            bars_state=bars_state,
            dones=dones,
            active_mask=context.active_mask,
            device=context.device,
        )


def build_vtc_transition_schedule(
    *,
    runtime_action_space: Any,
    level: Any,
    social_residue_rules: Sequence[Mapping[str, Any]],
    vfs_variables: Sequence[VariableDef],
) -> VTCTransitionSchedule:
    """Compile all VTC rule families into one runtime transition schedule."""
    phase_graph = TransitionPhaseGraph.default()
    # The occupancy-aware compiler is a superset of the plain action-writes
    # compiler: actions without a source_affordance compile identically, and
    # actions WITH one get their claim writes bound to the affordance's registry
    # row. The id order below is the registry's affordance-scope row order
    # (build_affordance_metadata enumerates the same sequence).
    affordance_ids = tuple(aff.name for aff in level.affordances.affordances)
    action_writes = compile_vtc_affordance_occupancy_with_phase_graph(runtime_action_space.actions, affordance_ids, phase_graph)
    _validate_action_write_targets(
        action_writes,
        vfs_variable_ids=(variable.id for variable in vfs_variables),
        meter_names=(meter.name for meter in level.bars.meters),
    )
    affordance_gates = compile_vtc_affordance_gates_with_phase_graph(level.affordances.affordances, phase_graph)
    interaction_progress = compile_vtc_interaction_progress_with_phase_graph(level.affordances.affordances, phase_graph)
    terminal_conditions = compile_vtc_terminal_conditions_with_phase_graph(level.bars.meters, phase_graph)
    passive_depletions = compile_vtc_passive_depletions_with_phase_graph(level.bars.meters, phase_graph)
    modulations = compile_vtc_modulations_with_phase_graph(level.affordances.modulations, phase_graph)
    threshold_cascades = compile_vtc_threshold_cascades_with_phase_graph(level.bars.cascades, level.bars.meters, phase_graph)
    social_program = compile_vtc_social_residue_rules_with_phase_graph(social_residue_rules, phase_graph)
    _validate_state_residue_targets(social_program, (variable.id for variable in vfs_variables))
    rewards = compile_vtc_reward_components_with_phase_graph(level.drive, phase_graph)
    bounds_clamps = compile_vtc_bounds_clamps_with_phase_graph(level.bars.meters, phase_graph)
    return VTCTransitionSchedule(
        phase_graph=phase_graph,
        action_write_program=action_writes,
        affordance_gate_program=affordance_gates,
        interaction_progress_program=interaction_progress,
        terminal_condition_program=terminal_conditions,
        passive_depletion_program=passive_depletions,
        modulation_program=modulations,
        threshold_cascade_program=threshold_cascades,
        social_residue_program=social_program,
        reward_component_program=rewards,
        bounds_clamp_program=bounds_clamps,
    )


def serialize_vtc_transition_schedule(schedule: VTCTransitionSchedule) -> dict[str, Any]:
    """Serialize the persisted transition runtime payload."""
    return {
        "phase_graph": list(schedule.phase_graph.ordered_phases),
        "social_residue_rules": [_social_rule_to_source(rule) for rule in schedule.social_residue_program.rules],
        # Only experiment-level rule families need source round-tripping here today.
        # The other programs are rebuilt from their existing compiled-universe inputs;
        # these counts are diagnostic metadata, not the load-bearing program payload.
        "program_counts": {
            "action_writes": len(schedule.action_write_program.writes),
            "affordance_gates": len(schedule.affordance_gate_program.rules),
            "interaction_progress": len(schedule.interaction_progress_program.progress_rules),
            "terminal_conditions": len(schedule.terminal_condition_program.rules),
            "passive_depletions": len(schedule.passive_depletion_program.rules),
            "modulations": len(schedule.modulation_program.rules),
            "threshold_cascades": len(schedule.threshold_cascade_program.rules),
            "social_residue": len(schedule.social_residue_program.rules),
            "reward_components": len(schedule.reward_component_program.rules),
            "bounds_clamps": len(schedule.bounds_clamp_program.rules),
        },
    }


def social_rules_from_transition_payload(payload: Mapping[str, Any], *, field_name: str) -> tuple[Mapping[str, Any], ...]:
    """Return persisted social-state rules from a serialized transition schedule."""
    if "phase_graph" not in payload:
        raise ValueError(f"Compiled universe cache field '{field_name}.phase_graph' is required; recompile the config pack.")
    if "social_residue_rules" not in payload:
        raise ValueError(f"Compiled universe cache field '{field_name}.social_residue_rules' is required; recompile the config pack.")
    return tuple(_ensure_mapping(rule, f"{field_name}.social_residue_rules") for rule in payload["social_residue_rules"])


def _split_vfs_and_bars(
    updated: Mapping[str, torch.Tensor],
    vfs_names: Iterable[str],
    bar_names: Iterable[str],
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    vfs_name_set = set(vfs_names)
    bar_name_set = set(bar_names)
    vfs_state: dict[str, torch.Tensor] = {}
    bars_state: dict[str, torch.Tensor] = {}
    for name, value in updated.items():
        if name in bar_name_set:
            bars_state[name] = value
        elif name in vfs_name_set:
            vfs_state[name] = value
        else:
            raise KeyError(f"VTC transition produced unknown state variable '{name}'")
    return vfs_state, bars_state


def _validate_action_write_targets(
    program: VTCActionWriteProgram,
    *,
    vfs_variable_ids: Iterable[str],
    meter_names: Iterable[str],
) -> None:
    """Every action write must target a declared VFS variable or meter bar —
    an unknown target would otherwise surface as a KeyError mid-step."""
    known = set(vfs_variable_ids) | set(meter_names)
    for write in program.writes:
        if write.variable_id not in known:
            raise ValueError(
                f"Action '{write.action_name}' write '{write.telemetry_label}' targets unknown "
                f"state variable '{write.variable_id}'. Declare it as a VFS variable or meter bar."
            )


def _validate_state_residue_targets(program: VTCSocialResidueProgram, variable_ids: Iterable[str]) -> None:
    known = set(variable_ids)
    for rule in program.rules:
        if rule.variable_id not in known:
            raise ValueError(f"VTC state residue rule '{rule.rule_id}' targets unknown VFS variable '{rule.variable_id}'")


def _social_rule_to_source(rule: Any) -> dict[str, Any]:
    return {
        "id": rule.rule_id,
        "phase": rule.phase,
        "kind": rule.kind,
        "reads": list(rule.reads),
        "condition": rule.condition,
        "priority": rule.priority,
        "writes": [
            {
                "variable_id": rule.variable_id,
                "effect": rule.effect,
                "expression": rule.expression,
                "composition": rule.composition,
                "phase": rule.phase,
                "priority": rule.priority,
                "clamp": None if rule.clamp is None else list(rule.clamp),
                "telemetry_label": rule.telemetry_label,
                "scope": rule.scope,
                "target": rule.target,
            }
        ],
    }


def _ensure_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Compiled universe cache field '{field_name}' entries must be mappings; recompile the config pack.")
    return value
