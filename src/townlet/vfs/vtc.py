"""VFS Transition Compiler support for ActionConfig writes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import torch

from townlet.vfs.schema import WriteSpec
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.world.expression import ASTNode, ExpressionParser
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator


class VTCActionWriteSource(Protocol):
    """Minimal action shape needed by the VTC action-write compiler."""

    @property
    def id(self) -> int: ...

    @property
    def name(self) -> str: ...

    @property
    def writes(self) -> Sequence[WriteSpec | Mapping[str, Any]]: ...


class VTCThresholdCascadeSource(Protocol):
    """Minimal cascade shape needed by the VTC threshold-cascade compiler."""

    @property
    def source(self) -> str: ...

    @property
    def target(self) -> str: ...

    @property
    def threshold(self) -> float: ...

    @property
    def strength(self) -> float: ...


@dataclass(frozen=True)
class CompiledVTCActionWrite:
    """A parsed VTC action write with the metadata needed for masked execution."""

    action_id: int
    action_name: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str


@dataclass(frozen=True)
class CompiledVTCThresholdCascade:
    """A parsed VTC threshold-delta relationship rule."""

    rule_id: str
    kind: str
    source_variable_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode
    condition: str
    condition_ast: ASTNode
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str


@dataclass(frozen=True)
class VTCActionWriteProgram:
    """Executable collection of compiled VTC action writes."""

    writes: tuple[CompiledVTCActionWrite, ...]

    def apply(
        self,
        *,
        actions: torch.Tensor,
        vfs_state: Mapping[str, torch.Tensor],
        bars_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> dict[str, torch.Tensor]:
        """Apply compiled VTC writes to a VFS state snapshot using action and active-agent masks."""
        if actions.shape != active_mask.shape:
            raise ValueError(f"actions shape {tuple(actions.shape)} must match active_mask shape {tuple(active_mask.shape)}")

        updated = {name: value.to(device=device).clone() for name, value in vfs_state.items()}
        for bar_name, value in bars_state.items():
            if bar_name in updated:
                raise ValueError(f"VTC action write state has ambiguous bar/VFS variable '{bar_name}'")
            updated[bar_name] = value.to(device=device).clone()
        bar_names = set(bars_state)
        actions_on_device = actions.to(device=device)
        active_mask_on_device = active_mask.to(device=device)

        for phase_writes in self._iter_phase_groups():
            phase_snapshot = dict(updated)
            phase_values = dict(updated)
            priority_state: dict[str, torch.Tensor] = {}

            for write in phase_writes:
                if write.variable_id not in phase_values:
                    raise KeyError(f"VTC action write targets unknown VFS variable '{write.variable_id}'")

                context = ExecutionContext(
                    bars={name: phase_snapshot[name] for name in bar_names},
                    vfs=dict(phase_snapshot),
                    affordances={},
                    temporal={},
                    device=device,
                )
                evaluator = Evaluator(context)
                phase_value = phase_values[write.variable_id]
                write_mask = self._build_write_mask(write, actions_on_device, active_mask_on_device, evaluator)
                expression_value = self._evaluate_tensor(evaluator, write.expression_ast, "expression", write)
                phase_values[write.variable_id] = self._apply_composed_write(
                    write=write,
                    phase_value=phase_value,
                    expression_value=expression_value,
                    write_mask=write_mask,
                    priority_state=priority_state,
                )

            updated = phase_values

        return updated

    def _iter_phase_groups(self) -> list[tuple[CompiledVTCActionWrite, ...]]:
        phase_groups: list[tuple[CompiledVTCActionWrite, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCActionWrite] = []

        for write in self.writes:
            if current_phase is None:
                current_phase = write.phase
            if write.phase != current_phase:
                phase_groups.append(tuple(current_group))
                current_group = []
                current_phase = write.phase
            current_group.append(write)

        if current_group:
            phase_groups.append(tuple(current_group))
        return phase_groups

    def _apply_composed_write(
        self,
        *,
        write: CompiledVTCActionWrite,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
        priority_state: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        candidate = self._compose_candidate(write, phase_value, expression_value)
        candidate = self._apply_optional_clamp(write, candidate)

        if write.composition == "priority_write":
            return self._apply_priority_write(write, phase_value, candidate, write_mask, priority_state)

        broadcast_mask = self._broadcast_agent_mask(write_mask, phase_value, write)
        return torch.where(
            broadcast_mask,
            candidate.to(device=phase_value.device, dtype=phase_value.dtype),
            phase_value,
        )

    def _compose_candidate(self, write: CompiledVTCActionWrite, phase_value: torch.Tensor, expression_value: torch.Tensor) -> torch.Tensor:
        expression = expression_value.to(device=phase_value.device, dtype=phase_value.dtype)
        if write.composition in {"overwrite", "last_write_wins", "priority_write", "clamp"}:
            return expression
        if write.composition == "additive_delta":
            return phase_value + expression
        if write.composition == "multiplicative_modifier":
            return phase_value * expression
        if write.composition == "min":
            return torch.minimum(phase_value, expression)
        if write.composition == "max":
            return torch.maximum(phase_value, expression)
        raise NotImplementedError(
            f"VTC action write composition '{write.composition}' is not implemented yet; "
            "claim/capacity/event compositions are tracked outside this VTC action-write composition step."
        )

    @staticmethod
    def _apply_optional_clamp(write: CompiledVTCActionWrite, value: torch.Tensor) -> torch.Tensor:
        if write.clamp is None:
            return value
        low, high = write.clamp
        return torch.clamp(value, min=low, max=high)

    def _apply_priority_write(
        self,
        write: CompiledVTCActionWrite,
        phase_value: torch.Tensor,
        candidate: torch.Tensor,
        write_mask: torch.Tensor,
        priority_state: dict[str, torch.Tensor],
    ) -> torch.Tensor:
        current_priority = priority_state.get(write.variable_id)
        if current_priority is None:
            current_priority = torch.full(write_mask.shape, -1, device=write_mask.device, dtype=torch.long)

        write_priority = torch.full(write_mask.shape, write.priority, device=write_mask.device, dtype=torch.long)
        winning_mask = write_mask & (write_priority >= current_priority)
        priority_state[write.variable_id] = torch.where(winning_mask, write_priority, current_priority)
        broadcast_mask = self._broadcast_agent_mask(winning_mask, phase_value, write)
        return torch.where(
            broadcast_mask,
            candidate.to(device=phase_value.device, dtype=phase_value.dtype),
            phase_value,
        )

    def _build_write_mask(
        self,
        write: CompiledVTCActionWrite,
        actions: torch.Tensor,
        active_mask: torch.Tensor,
        evaluator: Evaluator,
    ) -> torch.Tensor:
        action_mask = actions == write.action_id
        write_mask = action_mask & active_mask.bool()
        if write.condition_ast is None:
            return write_mask

        condition = self._evaluate_tensor(evaluator, write.condition_ast, "condition", write).bool()
        condition_mask = self._coerce_condition_mask(condition, actions, write)
        return write_mask & condition_mask

    @staticmethod
    def _evaluate_tensor(evaluator: Evaluator, ast: ASTNode, kind: str, write: CompiledVTCActionWrite) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC action write {write.telemetry_label} {kind} resolved to non-tensor value")
        return value

    @staticmethod
    def _coerce_condition_mask(condition: torch.Tensor, actions: torch.Tensor, write: CompiledVTCActionWrite) -> torch.Tensor:
        if condition.dim() == 0:
            return torch.full(actions.shape, bool(condition.item()), dtype=torch.bool, device=actions.device)
        if condition.shape != actions.shape:
            raise ValueError(
                f"Condition for VTC action write '{write.telemetry_label}' produced shape {tuple(condition.shape)}, "
                f"expected {tuple(actions.shape)}"
            )
        return condition.to(device=actions.device, dtype=torch.bool)

    @staticmethod
    def _broadcast_agent_mask(mask: torch.Tensor, target: torch.Tensor, write: CompiledVTCActionWrite) -> torch.Tensor:
        if target.dim() == 0:
            raise ValueError(f"VTC action write '{write.telemetry_label}' cannot apply a per-agent action mask to scalar variable")
        if target.shape[0] != mask.shape[0]:
            raise ValueError(
                f"VTC action write '{write.telemetry_label}' target leading dimension {target.shape[0]} "
                f"does not match action batch {mask.shape[0]}"
            )
        broadcast_mask = mask
        while broadcast_mask.dim() < target.dim():
            broadcast_mask = broadcast_mask.unsqueeze(-1)
        return broadcast_mask


@dataclass(frozen=True)
class VTCThresholdCascadeProgram:
    """Executable collection of compiled VTC threshold-delta cascade rules."""

    rules: tuple[CompiledVTCThresholdCascade, ...]

    def apply(
        self,
        *,
        bars_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
        strength_multiplier: float = 1.0,
    ) -> dict[str, torch.Tensor]:
        """Apply compiled threshold cascades to a bar state snapshot."""
        if strength_multiplier <= 0:
            raise ValueError("threshold cascade strength_multiplier must be positive")
        if active_mask.dim() != 1:
            raise ValueError(f"active_mask must be rank-1, got shape {tuple(active_mask.shape)}")

        updated = {name: value.to(device=device).clone() for name, value in bars_state.items()}
        active_mask_on_device = active_mask.to(device=device, dtype=torch.bool)

        for phase_rules in self._iter_phase_groups(self.rules):
            phase_snapshot = dict(updated)
            phase_values = dict(updated)

            for rule in phase_rules:
                if rule.variable_id not in phase_values:
                    raise KeyError(f"VTC threshold cascade targets unknown bar '{rule.variable_id}'")

                context = ExecutionContext(
                    bars=phase_snapshot,
                    vfs=dict(phase_snapshot),
                    affordances={},
                    temporal={},
                    device=device,
                )
                evaluator = Evaluator(context)
                target_value = phase_values[rule.variable_id]
                write_mask = self._build_rule_mask(rule, active_mask_on_device, evaluator)
                expression_value = self._evaluate_tensor(evaluator, rule.expression_ast, "expression", rule)
                if strength_multiplier != 1.0:
                    expression_value = expression_value * strength_multiplier
                phase_values[rule.variable_id] = self._apply_composed_rule(
                    rule=rule,
                    phase_value=target_value,
                    expression_value=expression_value,
                    write_mask=write_mask,
                )

            updated = phase_values

        return updated

    def apply_named(
        self,
        cascade_id: str,
        bars_state: Mapping[str, torch.Tensor],
        *,
        active_mask: torch.Tensor,
        device: torch.device,
        strength: float,
    ) -> dict[str, torch.Tensor]:
        """Apply one named cascade rule through the same threshold-delta executor."""
        matching_rules = tuple(rule for rule in self.rules if rule.rule_id == cascade_id)
        if not matching_rules:
            raise ValueError(f"Unknown cascade_id '{cascade_id}' for trigger_cascade")
        return VTCThresholdCascadeProgram(matching_rules).apply(
            bars_state=bars_state,
            active_mask=active_mask,
            device=device,
            strength_multiplier=strength,
        )

    @staticmethod
    def _iter_phase_groups(rules: Sequence[CompiledVTCThresholdCascade]) -> list[tuple[CompiledVTCThresholdCascade, ...]]:
        phase_groups: list[tuple[CompiledVTCThresholdCascade, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCThresholdCascade] = []

        for rule in rules:
            if current_phase is None:
                current_phase = rule.phase
            if rule.phase != current_phase:
                phase_groups.append(tuple(current_group))
                current_group = []
                current_phase = rule.phase
            current_group.append(rule)

        if current_group:
            phase_groups.append(tuple(current_group))
        return phase_groups

    def _build_rule_mask(
        self,
        rule: CompiledVTCThresholdCascade,
        active_mask: torch.Tensor,
        evaluator: Evaluator,
    ) -> torch.Tensor:
        condition = self._evaluate_tensor(evaluator, rule.condition_ast, "condition", rule).bool()
        condition_mask = self._coerce_condition_mask(condition, active_mask, rule)
        return active_mask & condition_mask

    def _apply_composed_rule(
        self,
        *,
        rule: CompiledVTCThresholdCascade,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
    ) -> torch.Tensor:
        expression = expression_value.to(device=phase_value.device, dtype=phase_value.dtype)
        if rule.composition == "additive_delta":
            candidate = phase_value + expression
        elif rule.composition in {"overwrite", "last_write_wins", "clamp"}:
            candidate = expression
        else:
            raise NotImplementedError(f"VTC threshold cascade composition '{rule.composition}' is not implemented")

        if rule.clamp is not None:
            low, high = rule.clamp
            candidate = torch.clamp(candidate, min=low, max=high)

        broadcast_mask = self._broadcast_agent_mask(write_mask, phase_value, rule)
        return torch.where(
            broadcast_mask,
            candidate.to(device=phase_value.device, dtype=phase_value.dtype),
            phase_value,
        )

    @staticmethod
    def _evaluate_tensor(
        evaluator: Evaluator,
        ast: ASTNode,
        kind: str,
        rule: CompiledVTCThresholdCascade,
    ) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC threshold cascade {rule.telemetry_label} {kind} resolved to non-tensor value")
        return value

    @staticmethod
    def _coerce_condition_mask(
        condition: torch.Tensor,
        active_mask: torch.Tensor,
        rule: CompiledVTCThresholdCascade,
    ) -> torch.Tensor:
        if condition.dim() == 0:
            return torch.full(active_mask.shape, bool(condition.item()), dtype=torch.bool, device=active_mask.device)
        if condition.shape != active_mask.shape:
            raise ValueError(
                f"Condition for VTC threshold cascade '{rule.telemetry_label}' produced shape {tuple(condition.shape)}, "
                f"expected {tuple(active_mask.shape)}"
            )
        return condition.to(device=active_mask.device, dtype=torch.bool)

    @staticmethod
    def _broadcast_agent_mask(mask: torch.Tensor, target: torch.Tensor, rule: CompiledVTCThresholdCascade) -> torch.Tensor:
        if target.dim() == 0:
            raise ValueError(f"VTC threshold cascade '{rule.telemetry_label}' cannot apply a per-agent mask to scalar bar")
        if target.shape[0] != mask.shape[0]:
            raise ValueError(
                f"VTC threshold cascade '{rule.telemetry_label}' target leading dimension {target.shape[0]} "
                f"does not match active mask batch {mask.shape[0]}"
            )
        broadcast_mask = mask
        while broadcast_mask.dim() < target.dim():
            broadcast_mask = broadcast_mask.unsqueeze(-1)
        return broadcast_mask


def compile_vtc_action_writes(actions: Sequence[VTCActionWriteSource]) -> VTCActionWriteProgram:
    """Compile ActionConfig writes into VTC records sorted by phase, priority, and action id."""
    return compile_vtc_action_writes_with_phase_graph(actions, TransitionPhaseGraph.default())


def compile_vtc_action_writes_with_phase_graph(
    actions: Sequence[VTCActionWriteSource],
    phase_graph: TransitionPhaseGraph,
) -> VTCActionWriteProgram:
    """Compile ActionConfig writes using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_writes: list[CompiledVTCActionWrite] = []

    for action in actions:
        for raw_write in action.writes:
            write = _coerce_write_spec(raw_write, action.name)
            compiled_writes.append(
                CompiledVTCActionWrite(
                    action_id=action.id,
                    action_name=action.name,
                    variable_id=write.variable_id,
                    expression=write.expression,
                    expression_ast=parser.parse(write.expression),
                    condition=write.condition,
                    condition_ast=parser.parse(write.condition) if write.condition is not None else None,
                    composition=write.composition,
                    phase=write.phase,
                    priority=write.priority,
                    clamp=write.clamp,
                    telemetry_label=write.telemetry_label,
                )
            )

    return VTCActionWriteProgram(
        writes=tuple(
            sorted(
                compiled_writes,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.action_id, item.telemetry_label),
            )
        )
    )


def _coerce_write_spec(write: WriteSpec | Mapping[str, Any], action_name: str) -> WriteSpec:
    if isinstance(write, WriteSpec):
        return write
    if isinstance(write, Mapping):
        return WriteSpec.model_validate(dict(write))
    raise TypeError(f"Action '{action_name}' write entry must be a WriteSpec or mapping")


def compile_vtc_threshold_cascades(cascades: Sequence[VTCThresholdCascadeSource | Mapping[str, Any]]) -> VTCThresholdCascadeProgram:
    """Compile bars.yaml cascades into VTC threshold-delta transition rules."""
    return compile_vtc_threshold_cascades_with_phase_graph(cascades, TransitionPhaseGraph.default())


def compile_vtc_threshold_cascades_with_phase_graph(
    cascades: Sequence[VTCThresholdCascadeSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCThresholdCascadeProgram:
    """Compile bars.yaml cascades using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCThresholdCascade] = []

    for priority, raw_cascade in enumerate(cascades):
        cascade = _coerce_threshold_cascade(raw_cascade)
        threshold_literal = _format_rule_float(cascade["threshold"])
        strength_literal = _format_rule_float(-cascade["strength"])
        condition = f"bar.{cascade['source']} < {threshold_literal}"
        expression = (
            "0.0"
            if cascade["threshold"] == 0.0
            else f"{strength_literal} * (({threshold_literal} - bar.{cascade['source']}) / {threshold_literal})"
        )
        rule_id = cascade["rule_id"]
        compiled_rules.append(
            CompiledVTCThresholdCascade(
                rule_id=rule_id,
                kind="threshold_delta",
                source_variable_id=cascade["source"],
                variable_id=cascade["target"],
                expression=expression,
                expression_ast=parser.parse(expression),
                condition=condition,
                condition_ast=parser.parse(condition),
                composition="additive_delta",
                phase="apply_threshold_cascades",
                priority=priority,
                clamp=(0.0, 1.0),
                telemetry_label=f"threshold_delta:{rule_id}",
            )
        )

    return VTCThresholdCascadeProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_threshold_cascade(cascade: VTCThresholdCascadeSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(cascade, Mapping):
        source = str(cascade["source"])
        target = str(cascade["target"])
        threshold = float(cascade["threshold"])
        strength = float(cascade["strength"])
        rule_id = str(cascade.get("id") or cascade.get("rule_id") or f"{source}->{target}")
    else:
        source = cascade.source
        target = cascade.target
        threshold = float(cascade.threshold)
        strength = float(cascade.strength)
        rule_id = str(getattr(cascade, "id", None) or f"{source}->{target}")

    return {
        "rule_id": rule_id,
        "source": source,
        "target": target,
        "threshold": threshold,
        "strength": strength,
    }


def _format_rule_float(value: float) -> str:
    return repr(float(value))
