"""VFS Transition Compiler support for declarative transition rules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

import torch

from townlet.vfs import vtc_kernels
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


class VTCPassiveDepletionSource(Protocol):
    """Minimal meter shape needed by the VTC passive-depletion compiler."""

    @property
    def name(self) -> str: ...

    @property
    def depletion(self) -> Any: ...


class VTCModulationSource(Protocol):
    """Minimal modulation shape needed by the VTC modulation compiler."""

    @property
    def bar(self) -> str: ...

    @property
    def affordances(self) -> Sequence[str]: ...

    @property
    def type(self) -> str: ...

    @property
    def threshold(self) -> float: ...

    @property
    def min_multiplier(self) -> float: ...


class VTCAffordanceGateSource(Protocol):
    """Minimal affordance shape needed by the VTC operating-hour gate compiler."""

    @property
    def name(self) -> str: ...

    @property
    def opening_hours(self) -> Any: ...


class VTCInteractionProgressSource(Protocol):
    """Minimal affordance shape needed by the VTC interaction-progress compiler."""

    @property
    def name(self) -> str: ...

    @property
    def interaction_type(self) -> str | None: ...

    @property
    def duration_ticks(self) -> int | None: ...


class VTCTerminalConditionSource(Protocol):
    """Minimal meter shape needed by the VTC terminal-condition compiler."""

    @property
    def name(self) -> str: ...

    @property
    def bounds(self) -> Any: ...


class VTCRewardConfigSource(Protocol):
    """Minimal drive shape needed by the VTC reward-component compiler."""

    @property
    def modifiers(self) -> Mapping[str, Any]: ...

    @property
    def extrinsic(self) -> Any: ...

    @property
    def intrinsic(self) -> Any: ...

    @property
    def shaping(self) -> Sequence[Any]: ...


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
    cascade_threshold: float
    cascade_strength: float


@dataclass(frozen=True)
class CompiledVTCPassiveDepletion:
    """A parsed VTC passive-depletion rule."""

    rule_id: str
    kind: str
    source_variable_id: str
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
    passive_rate: float


@dataclass(frozen=True)
class CompiledVTCModulation:
    """A parsed VTC affordance modulation rule."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
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
    modulation_threshold: float
    min_multiplier: float


@dataclass(frozen=True)
class CompiledVTCAffordanceGate:
    """A parsed VTC operating-hour gate for one affordance."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
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
class CompiledVTCInteractionProgress:
    """A parsed VTC progress-advance rule for one multi-tick affordance."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
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
    duration_ticks: int


@dataclass(frozen=True)
class CompiledVTCInteractionCompletionBonus:
    """A parsed VTC completion event rule for one multi-tick affordance."""

    rule_id: str
    kind: str
    source_variable_id: str
    target_affordance_id: str
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
    duration_ticks: int


@dataclass(frozen=True)
class CompiledVTCTerminalCondition:
    """A parsed VTC terminal-condition rule for one lethal meter bound."""

    rule_id: str
    kind: str
    source_variable_id: str
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
    operator: str
    threshold: float


@dataclass(frozen=True)
class CompiledVTCRewardComponent:
    """A declarative VTC reward-phase component rule backed by DAC execution."""

    rule_id: str
    kind: str
    source_variable_id: str
    variable_id: str
    expression: str
    expression_ast: ASTNode | None
    condition: str | None
    condition_ast: ASTNode | None
    composition: str
    phase: str
    priority: int
    clamp: tuple[float, float] | None
    telemetry_label: str
    reads: tuple[str, ...]
    component: str
    source_kind: str
    strategy: str | None
    shaping_type: str | None
    parameters: dict[str, Any]


@dataclass(frozen=True)
class _VTCActionWriteEffect:
    """Computed action-write candidate for one atomic VTC phase commit."""

    write: CompiledVTCActionWrite
    expression_value: torch.Tensor
    write_mask: torch.Tensor


@dataclass(frozen=True)
class VTCInteractionProgressResult:
    """Result of one VTC interaction-progress transition step."""

    interaction_progress: torch.Tensor
    ticks_done: torch.Tensor
    completion_mask: torch.Tensor
    completion_affordances: list[str | None]
    last_affordances: list[str | None]
    last_positions: torch.Tensor


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
            phase_effects = self._compute_phase_effects(
                phase_writes=phase_writes,
                phase_snapshot=phase_snapshot,
                bar_names=bar_names,
                actions=actions_on_device,
                active_mask=active_mask_on_device,
                device=device,
            )
            updated = self._commit_phase_effects(phase_snapshot, phase_effects)

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

    def _compute_phase_effects(
        self,
        *,
        phase_writes: Sequence[CompiledVTCActionWrite],
        phase_snapshot: Mapping[str, torch.Tensor],
        bar_names: set[str],
        actions: torch.Tensor,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> tuple[_VTCActionWriteEffect, ...]:
        phase_effects: list[_VTCActionWriteEffect] = []
        context = ExecutionContext(
            bars={name: phase_snapshot[name] for name in bar_names},
            vfs=dict(phase_snapshot),
            affordances={},
            temporal={},
            device=device,
        )
        evaluator = Evaluator(context)

        for write in phase_writes:
            if write.variable_id not in phase_snapshot:
                raise KeyError(f"VTC action write targets unknown VFS variable '{write.variable_id}'")

            target_snapshot = phase_snapshot[write.variable_id]
            write_mask = self._build_write_mask(write, actions, active_mask, evaluator)
            expression_value = self._evaluate_tensor(evaluator, write.expression_ast, "expression", write)
            phase_effects.append(
                _VTCActionWriteEffect(
                    write=write,
                    expression_value=self._coerce_expression_tensor(expression_value, target_snapshot, write),
                    write_mask=write_mask,
                )
            )

        return tuple(phase_effects)

    def _commit_phase_effects(
        self,
        phase_snapshot: Mapping[str, torch.Tensor],
        phase_effects: Sequence[_VTCActionWriteEffect],
    ) -> dict[str, torch.Tensor]:
        phase_values = dict(phase_snapshot)
        priority_state: dict[str, torch.Tensor] = {}

        for effect in phase_effects:
            phase_value = phase_values[effect.write.variable_id]
            phase_values[effect.write.variable_id] = self._apply_composed_write(
                write=effect.write,
                phase_value=phase_value,
                expression_value=effect.expression_value,
                write_mask=effect.write_mask,
                priority_state=priority_state,
            )

        return phase_values

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
        return cast(
            torch.Tensor,
            vtc_kernels.apply_masked_candidate(
                phase_value,
                candidate.to(device=phase_value.device, dtype=phase_value.dtype),
                broadcast_mask,
            ),
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
        return cast(
            torch.Tensor,
            vtc_kernels.apply_masked_candidate(
                phase_value,
                candidate.to(device=phase_value.device, dtype=phase_value.dtype),
                broadcast_mask,
            ),
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
    def _coerce_expression_tensor(
        value: torch.Tensor,
        target: torch.Tensor,
        write: CompiledVTCActionWrite,
    ) -> torch.Tensor:
        if value.dim() == 0:
            return value.to(device=target.device, dtype=target.dtype).expand_as(target)
        if value.shape != target.shape:
            raise ValueError(
                f"Expression for VTC action write '{write.telemetry_label}' produced shape {tuple(value.shape)}, "
                f"expected {tuple(target.shape)}"
            )
        return value.to(device=target.device, dtype=target.dtype)

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
                if rule.source_variable_id not in phase_snapshot:
                    raise KeyError(f"VTC threshold cascade reads unknown bar '{rule.source_variable_id}'")
                if rule.composition != "additive_delta":
                    raise NotImplementedError(f"VTC threshold cascade composition '{rule.composition}' is not scriptable")
                clamp_low, clamp_high = _required_clamp(rule.clamp, rule.telemetry_label)

                target_value = phase_values[rule.variable_id]
                source_value = phase_snapshot[rule.source_variable_id].to(device=device, dtype=target_value.dtype)
                phase_values[rule.variable_id] = vtc_kernels.apply_threshold_cascade(
                    source_value,
                    target_value,
                    active_mask_on_device,
                    rule.cascade_threshold,
                    rule.cascade_strength,
                    strength_multiplier,
                    clamp_low,
                    clamp_high,
                )

            updated = phase_values

        return updated

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


@dataclass(frozen=True)
class VTCPassiveDepletionProgram:
    """Executable collection of compiled VTC passive-depletion rules."""

    rules: tuple[CompiledVTCPassiveDepletion, ...]

    def passive_rate_for(self, variable_id: str) -> float:
        """Return the configured passive depletion rate for a meter bar."""
        for rule in self.rules:
            if rule.variable_id == variable_id:
                return rule.passive_rate
        raise KeyError(f"Meter '{variable_id}' has no VTC passive-depletion rule.")

    def apply(
        self,
        *,
        bars_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
        depletion_multiplier: float = 1.0,
    ) -> dict[str, torch.Tensor]:
        """Apply passive depletion to meter bars using a VTC phase snapshot."""
        if depletion_multiplier < 0:
            raise ValueError("passive depletion multiplier must be non-negative")
        if active_mask.dim() != 1:
            raise ValueError(f"active_mask must be rank-1, got shape {tuple(active_mask.shape)}")

        updated = {name: value.to(device=device).clone() for name, value in bars_state.items()}
        active_mask_on_device = active_mask.to(device=device, dtype=torch.bool)

        for phase_rules in self._iter_phase_groups(self.rules):
            phase_values = dict(updated)

            for rule in phase_rules:
                if rule.variable_id not in phase_values:
                    raise KeyError(f"VTC passive depletion targets unknown bar '{rule.variable_id}'")
                if rule.condition_ast is not None:
                    raise NotImplementedError(f"VTC passive depletion condition '{rule.telemetry_label}' is not scriptable")
                if rule.composition != "overwrite":
                    raise NotImplementedError(f"VTC passive depletion composition '{rule.composition}' is not scriptable")
                clamp_low, clamp_high = _required_clamp(rule.clamp, rule.telemetry_label)

                phase_value = phase_values[rule.variable_id]
                phase_values[rule.variable_id] = vtc_kernels.apply_passive_depletion(
                    phase_value,
                    active_mask_on_device,
                    rule.passive_rate,
                    float(depletion_multiplier),
                    clamp_low,
                    clamp_high,
                )

            updated = phase_values

        return updated

    @staticmethod
    def _iter_phase_groups(rules: Sequence[CompiledVTCPassiveDepletion]) -> list[tuple[CompiledVTCPassiveDepletion, ...]]:
        phase_groups: list[tuple[CompiledVTCPassiveDepletion, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCPassiveDepletion] = []

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
        rule: CompiledVTCPassiveDepletion,
        active_mask: torch.Tensor,
        evaluator: Evaluator,
    ) -> torch.Tensor:
        if rule.condition_ast is None:
            return active_mask

        condition = self._evaluate_tensor(evaluator, rule.condition_ast, "condition", rule).bool()
        condition_mask = self._coerce_rule_tensor(condition, active_mask, rule, "condition").bool()
        return active_mask & condition_mask

    def _apply_composed_rule(
        self,
        *,
        rule: CompiledVTCPassiveDepletion,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
    ) -> torch.Tensor:
        expression = self._coerce_rule_tensor(expression_value, phase_value, rule, "expression")
        if rule.composition == "overwrite":
            candidate = expression
        else:
            raise NotImplementedError(f"VTC passive depletion composition '{rule.composition}' is not implemented")

        if rule.clamp is not None:
            low, high = rule.clamp
            candidate = torch.clamp(candidate, min=low, max=high)

        return torch.where(write_mask, candidate.to(device=phase_value.device, dtype=phase_value.dtype), phase_value)

    @staticmethod
    def _evaluate_tensor(
        evaluator: Evaluator,
        ast: ASTNode,
        kind: str,
        rule: CompiledVTCPassiveDepletion,
    ) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC passive depletion {rule.telemetry_label} {kind} resolved to non-tensor value")
        return value

    @staticmethod
    def _coerce_rule_tensor(
        value: torch.Tensor,
        target: torch.Tensor,
        rule: CompiledVTCPassiveDepletion,
        kind: str,
    ) -> torch.Tensor:
        if value.dim() == 0:
            return value.to(device=target.device, dtype=target.dtype).expand_as(target)
        if value.shape != target.shape:
            raise ValueError(
                f"{kind.capitalize()} for VTC passive depletion '{rule.telemetry_label}' produced shape {tuple(value.shape)}, "
                f"expected {tuple(target.shape)}"
            )
        return value.to(device=target.device, dtype=target.dtype)


@dataclass(frozen=True)
class VTCModulationProgram:
    """Executable collection of compiled VTC affordance modulation rules."""

    rules: tuple[CompiledVTCModulation, ...]

    def compute_affordance_multiplier(
        self,
        affordance_name: str,
        bars_state: Mapping[str, torch.Tensor],
        *,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> torch.Tensor:
        """Compute the composed multiplier for an affordance from compiled modulation rules."""
        if active_mask.dim() != 1:
            raise ValueError(f"active_mask must be rank-1, got shape {tuple(active_mask.shape)}")

        bars_on_device = {name: value.to(device=device) for name, value in bars_state.items()}
        dtype = self._infer_dtype(bars_on_device)
        active_mask_on_device = active_mask.to(device=device, dtype=torch.bool)
        multiplier = torch.ones(active_mask_on_device.shape, device=device, dtype=dtype)
        matching_rules = tuple(rule for rule in self.rules if rule.target_affordance_id == affordance_name)

        for phase_rules in self._iter_phase_groups(matching_rules):
            phase_value = multiplier
            phase_snapshot = dict(bars_on_device)

            for rule in phase_rules:
                if rule.source_variable_id not in phase_snapshot:
                    raise KeyError(f"VTC modulation reads unknown bar '{rule.source_variable_id}'")
                if rule.condition_ast is not None:
                    raise NotImplementedError(f"VTC modulation condition '{rule.telemetry_label}' is not scriptable")
                if rule.composition != "multiplicative_modifier":
                    raise NotImplementedError(f"VTC modulation composition '{rule.composition}' is not scriptable")
                clamp_low, clamp_high = _required_clamp(rule.clamp, rule.telemetry_label)

                source_value = phase_snapshot[rule.source_variable_id].to(device=device, dtype=phase_value.dtype)
                phase_value = vtc_kernels.apply_modulation_multiplier(
                    phase_value,
                    source_value,
                    active_mask_on_device,
                    rule.modulation_threshold,
                    rule.min_multiplier,
                    clamp_low,
                    clamp_high,
                )

            multiplier = phase_value

        return torch.where(active_mask_on_device, multiplier, torch.zeros_like(multiplier))

    @staticmethod
    def _infer_dtype(bars_state: Mapping[str, torch.Tensor]) -> torch.dtype:
        if not bars_state:
            return torch.float32
        first_bar = next(iter(bars_state.values()))
        return first_bar.dtype if first_bar.is_floating_point() else torch.float32

    @staticmethod
    def _iter_phase_groups(rules: Sequence[CompiledVTCModulation]) -> list[tuple[CompiledVTCModulation, ...]]:
        phase_groups: list[tuple[CompiledVTCModulation, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledVTCModulation] = []

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
        rule: CompiledVTCModulation,
        active_mask: torch.Tensor,
        evaluator: Evaluator,
    ) -> torch.Tensor:
        if rule.condition_ast is None:
            return active_mask

        condition = self._evaluate_tensor(evaluator, rule.condition_ast, "condition", rule).bool()
        condition_mask = self._coerce_rule_tensor(condition, active_mask, rule, "condition").bool()
        return active_mask & condition_mask

    def _apply_composed_rule(
        self,
        *,
        rule: CompiledVTCModulation,
        phase_value: torch.Tensor,
        expression_value: torch.Tensor,
        write_mask: torch.Tensor,
    ) -> torch.Tensor:
        expression = self._coerce_rule_tensor(expression_value, phase_value, rule, "expression")
        if rule.composition == "multiplicative_modifier":
            candidate = phase_value * expression
        else:
            raise NotImplementedError(f"VTC modulation composition '{rule.composition}' is not implemented")

        if rule.clamp is not None:
            low, high = rule.clamp
            candidate = torch.clamp(candidate, min=low, max=high)

        return torch.where(write_mask, candidate.to(device=phase_value.device, dtype=phase_value.dtype), phase_value)

    @staticmethod
    def _evaluate_tensor(
        evaluator: Evaluator,
        ast: ASTNode,
        kind: str,
        rule: CompiledVTCModulation,
    ) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC modulation {rule.telemetry_label} {kind} resolved to non-tensor value")
        return value

    @staticmethod
    def _coerce_rule_tensor(
        value: torch.Tensor,
        target: torch.Tensor,
        rule: CompiledVTCModulation,
        kind: str,
    ) -> torch.Tensor:
        if value.dim() == 0:
            return value.to(device=target.device, dtype=target.dtype).expand_as(target)
        if value.shape != target.shape:
            raise ValueError(
                f"{kind.capitalize()} for VTC modulation '{rule.telemetry_label}' produced shape {tuple(value.shape)}, "
                f"expected {tuple(target.shape)}"
            )
        return value.to(device=target.device, dtype=target.dtype)


@dataclass(frozen=True)
class VTCAffordanceGateProgram:
    """Executable collection of compiled VTC operating-hour gates."""

    rules: tuple[CompiledVTCAffordanceGate, ...]

    def is_affordance_open(self, affordance_name: str, *, time_of_day: int | float | torch.Tensor, device: torch.device) -> bool:
        """Return whether one affordance is open for the current temporal state."""
        values = self.compute(time_of_day=time_of_day, device=device)
        try:
            value = values[affordance_name]
        except KeyError as exc:
            raise KeyError(f"VTC affordance gates have no rule for affordance '{affordance_name}'") from exc
        if value.numel() != 1:
            raise ValueError(f"VTC affordance gate for '{affordance_name}' produced non-scalar shape {tuple(value.shape)}")
        return bool(value.item())

    def compute(self, *, time_of_day: int | float | torch.Tensor, device: torch.device) -> dict[str, torch.Tensor]:
        """Evaluate all operating-hour gates from the VTC temporal snapshot."""
        time_tensor = self._time_tensor(time_of_day, device=device)
        context = ExecutionContext(
            bars={},
            vfs={},
            affordances={},
            temporal={"time_of_day": time_tensor},
            device=device,
        )
        evaluator = Evaluator(context)
        values: dict[str, torch.Tensor] = {}
        for rule in self.rules:
            value = self._evaluate_tensor(evaluator, rule.expression_ast, "expression", rule).to(device=device, dtype=torch.bool)
            if value.numel() != 1:
                raise ValueError(f"VTC affordance gate '{rule.telemetry_label}' produced non-scalar shape {tuple(value.shape)}")
            values[rule.target_affordance_id] = value.reshape(())
        return values

    @staticmethod
    def _time_tensor(time_of_day: int | float | torch.Tensor, *, device: torch.device) -> torch.Tensor:
        if isinstance(time_of_day, torch.Tensor):
            if time_of_day.numel() != 1:
                raise ValueError(f"time_of_day must be scalar, got shape {tuple(time_of_day.shape)}")
            return time_of_day.to(device=device, dtype=torch.float32).reshape(())
        return torch.tensor(float(time_of_day), device=device, dtype=torch.float32)

    @staticmethod
    def _evaluate_tensor(
        evaluator: Evaluator,
        ast: ASTNode,
        kind: str,
        rule: CompiledVTCAffordanceGate,
    ) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC affordance gate {rule.telemetry_label} {kind} resolved to non-tensor value")
        return value


@dataclass(frozen=True)
class VTCInteractionProgressProgram:
    """Executable collection of compiled VTC multi-tick progress and completion rules."""

    progress_rules: tuple[CompiledVTCInteractionProgress, ...]
    completion_bonus_rules: tuple[CompiledVTCInteractionCompletionBonus, ...]

    def apply(
        self,
        *,
        interaction_affordances: Mapping[int, str],
        positions: torch.Tensor,
        interaction_progress: torch.Tensor,
        last_affordances: Sequence[str | None],
        last_positions: torch.Tensor,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> VTCInteractionProgressResult:
        """Advance multi-tick interaction progress using compiled VTC duration rules."""
        self._validate_apply_inputs(
            positions=positions,
            interaction_progress=interaction_progress,
            last_affordances=last_affordances,
            last_positions=last_positions,
            active_mask=active_mask,
        )

        positions_on_device = positions.to(device=device)
        last_positions_on_device = last_positions.to(device=device)
        previous_progress = interaction_progress.to(device=device, dtype=torch.long)
        active = active_mask.to(device=device, dtype=torch.bool)

        next_progress = torch.zeros_like(previous_progress)
        ticks_done = torch.zeros_like(previous_progress)
        completion_mask = torch.zeros(previous_progress.shape, device=device, dtype=torch.bool)
        completion_affordances: list[str | None] = [None] * previous_progress.shape[0]
        next_last_affordances: list[str | None] = [None] * previous_progress.shape[0]
        next_last_positions = last_positions_on_device.clone()

        normalized_interactions = self._normalize_interaction_affordances(interaction_affordances, previous_progress.shape[0])
        for agent_idx in range(previous_progress.shape[0]):
            if not bool(active[agent_idx].item()):
                next_progress[agent_idx] = previous_progress[agent_idx]
                next_last_affordances[agent_idx] = last_affordances[agent_idx]
                next_last_positions[agent_idx] = last_positions_on_device[agent_idx]
                continue

            affordance_name = normalized_interactions.get(agent_idx)
            if affordance_name is None:
                next_last_positions[agent_idx] = positions_on_device[agent_idx]
                continue

            rule = self._rule_for_affordance(affordance_name)
            same_affordance = last_affordances[agent_idx] == affordance_name
            same_position = torch.equal(last_positions_on_device[agent_idx], positions_on_device[agent_idx])
            candidate_ticks = (
                previous_progress[agent_idx] + 1
                if same_affordance and same_position
                else torch.tensor(
                    1,
                    device=device,
                    dtype=torch.long,
                )
            )
            ticks_done[agent_idx] = candidate_ticks

            if int(candidate_ticks.item()) >= rule.duration_ticks:
                completion_mask[agent_idx] = True
                completion_affordances[agent_idx] = affordance_name
                next_last_affordances[agent_idx] = None
            else:
                next_progress[agent_idx] = candidate_ticks
                next_last_affordances[agent_idx] = affordance_name

            next_last_positions[agent_idx] = positions_on_device[agent_idx]

        return VTCInteractionProgressResult(
            interaction_progress=next_progress,
            ticks_done=ticks_done,
            completion_mask=completion_mask,
            completion_affordances=completion_affordances,
            last_affordances=next_last_affordances,
            last_positions=next_last_positions,
        )

    def duration_for(self, affordance_name: str) -> int:
        """Return the configured VTC duration for a multi-tick affordance."""
        return self._rule_for_affordance(affordance_name).duration_ticks

    def has_multi_tick_affordances(self) -> bool:
        """Return whether this program contains any multi-tick affordance rules."""
        return bool(self.progress_rules)

    def contains_affordance(self, affordance_name: str) -> bool:
        """Return whether an affordance has VTC multi-tick progress semantics."""
        return any(rule.target_affordance_id == affordance_name for rule in self.progress_rules)

    @staticmethod
    def _validate_apply_inputs(
        *,
        positions: torch.Tensor,
        interaction_progress: torch.Tensor,
        last_affordances: Sequence[str | None],
        last_positions: torch.Tensor,
        active_mask: torch.Tensor,
    ) -> None:
        if interaction_progress.dim() != 1:
            raise ValueError(f"interaction_progress must be rank-1, got shape {tuple(interaction_progress.shape)}")
        if active_mask.shape != interaction_progress.shape:
            raise ValueError(
                f"active_mask shape {tuple(active_mask.shape)} must match interaction_progress shape "
                f"{tuple(interaction_progress.shape)}"
            )
        if positions.shape[0] != interaction_progress.shape[0]:
            raise ValueError(
                f"positions leading dimension {positions.shape[0]} must match interaction batch {interaction_progress.shape[0]}"
            )
        if last_positions.shape != positions.shape:
            raise ValueError(f"last_positions shape {tuple(last_positions.shape)} must match positions shape {tuple(positions.shape)}")
        if len(last_affordances) != interaction_progress.shape[0]:
            raise ValueError(
                f"last_affordances length {len(last_affordances)} must match interaction batch {interaction_progress.shape[0]}"
            )

    @staticmethod
    def _normalize_interaction_affordances(interaction_affordances: Mapping[int, str], batch_size: int) -> dict[int, str]:
        normalized: dict[int, str] = {}
        for raw_idx, affordance_name in interaction_affordances.items():
            agent_idx = int(raw_idx)
            if agent_idx < 0 or agent_idx >= batch_size:
                raise ValueError(f"Interaction agent index {agent_idx} is outside batch size {batch_size}")
            normalized[agent_idx] = affordance_name
        return normalized

    def _rule_for_affordance(self, affordance_name: str) -> CompiledVTCInteractionProgress:
        for rule in self.progress_rules:
            if rule.target_affordance_id == affordance_name:
                return rule
        raise KeyError(f"VTC interaction progress has no rule for affordance '{affordance_name}'")


@dataclass(frozen=True)
class VTCTerminalConditionProgram:
    """Executable collection of compiled VTC terminal-condition rules."""

    rules: tuple[CompiledVTCTerminalCondition, ...]

    def apply(
        self,
        *,
        bars_state: Mapping[str, torch.Tensor],
        dones: torch.Tensor,
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> torch.Tensor:
        """Evaluate terminal conditions and OR triggered terminals into existing done flags."""
        self._validate_apply_inputs(bars_state=bars_state, dones=dones, active_mask=active_mask)

        updated_dones = dones.to(device=device, dtype=torch.bool).clone()
        active = active_mask.to(device=device, dtype=torch.bool)
        bars_on_device = {name: value.to(device=device) for name, value in bars_state.items()}
        if len(self.rules) == 0:
            return updated_dones

        missing_bars = sorted({rule.source_variable_id for rule in self.rules if rule.source_variable_id not in bars_on_device})
        if missing_bars:
            raise KeyError(f"VTC terminal conditions reference unknown bars: {missing_bars}")

        for rule in self.rules:
            if rule.condition_ast is not None:
                raise NotImplementedError(f"VTC terminal condition '{rule.telemetry_label}' condition is not scriptable")
            if rule.composition != "event":
                raise NotImplementedError(f"VTC terminal condition composition '{rule.composition}' is not scriptable")
            source_value = bars_on_device[rule.source_variable_id]
            if source_value.shape != updated_dones.shape:
                raise ValueError(
                    f"VTC terminal condition {rule.telemetry_label} reads shape {tuple(source_value.shape)}; "
                    f"expected {tuple(updated_dones.shape)}"
                )
            updated_dones = vtc_kernels.apply_terminal_condition(
                source_value,
                updated_dones,
                active,
                rule.threshold,
                rule.operator == "<=",
            )

        return updated_dones

    @staticmethod
    def _validate_apply_inputs(
        *,
        bars_state: Mapping[str, torch.Tensor],
        dones: torch.Tensor,
        active_mask: torch.Tensor,
    ) -> None:
        if dones.dim() != 1:
            raise ValueError(f"dones must be rank-1, got shape {tuple(dones.shape)}")
        if active_mask.shape != dones.shape:
            raise ValueError(f"active_mask shape {tuple(active_mask.shape)} must match dones shape {tuple(dones.shape)}")
        for bar_name, value in bars_state.items():
            if value.shape != dones.shape:
                raise ValueError(f"bar '{bar_name}' shape {tuple(value.shape)} must match dones shape {tuple(dones.shape)}")

    @staticmethod
    def _evaluate_bool_tensor(
        evaluator: Evaluator,
        ast: ASTNode,
        rule: CompiledVTCTerminalCondition,
    ) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC terminal condition {rule.telemetry_label} resolved to non-tensor value")
        if value.dtype != torch.bool:
            raise TypeError(f"VTC terminal condition {rule.telemetry_label} resolved to {value.dtype}, expected bool")
        return value


@dataclass(frozen=True)
class VTCRewardProgram:
    """Executable VTC reward-phase contract that delegates math to a DAC backend."""

    rules: tuple[CompiledVTCRewardComponent, ...]
    expected_components: tuple[str, ...] = ("extrinsic", "intrinsic", "intrinsic_raw", "shaping")

    def apply(
        self,
        *,
        reward_backend: Any,
        step_counts: torch.Tensor,
        dones: torch.Tensor,
        meters: torch.Tensor,
        intrinsic_raw: torch.Tensor,
        reward_context: Mapping[str, Any],
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        """Run the reward phase through the DAC backend and validate declared component outputs."""
        total_rewards, intrinsic_weights, components = reward_backend.calculate_rewards(
            step_counts=step_counts,
            dones=dones,
            meters=meters,
            intrinsic_raw=intrinsic_raw,
            **dict(reward_context),
        )
        self._validate_tensor("total_rewards", total_rewards, dones)
        self._validate_tensor("intrinsic_weights", intrinsic_weights, dones)
        self._validate_components(components, dones)
        return total_rewards, intrinsic_weights, components

    @staticmethod
    def _validate_tensor(name: str, value: Any, dones: torch.Tensor) -> None:
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"VTC reward program expected {name} to be a tensor")
        if value.shape != dones.shape:
            raise ValueError(f"VTC reward program expected {name} shape {tuple(dones.shape)}, got {tuple(value.shape)}")

    def _validate_components(self, components: Any, dones: torch.Tensor) -> None:
        if not isinstance(components, dict):
            raise TypeError("VTC reward program expected components to be a dict")

        missing = sorted(component for component in self.expected_components if component not in components)
        if missing:
            raise KeyError(f"VTC reward program missing declared reward components: {missing}")

        for name, value in components.items():
            if not isinstance(value, torch.Tensor):
                raise TypeError(f"VTC reward component '{name}' resolved to non-tensor value")
            if value.shape != dones.shape:
                raise ValueError(
                    f"VTC reward component '{name}' shape {tuple(value.shape)} does not match dones shape {tuple(dones.shape)}"
                )


def compile_vtc_reward_components(drive_config: VTCRewardConfigSource | Mapping[str, Any]) -> VTCRewardProgram:
    """Compile a drive reward configuration into VTC compute-reward component rules."""
    return compile_vtc_reward_components_with_phase_graph(drive_config, TransitionPhaseGraph.default())


def compile_vtc_reward_components_with_phase_graph(
    drive_config: VTCRewardConfigSource | Mapping[str, Any],
    phase_graph: TransitionPhaseGraph,
) -> VTCRewardProgram:
    """Compile reward components using an explicit VTC transition phase graph."""
    drive = _coerce_reward_drive(drive_config)
    compiled_rules: list[CompiledVTCRewardComponent] = []

    for modifier_name in sorted(drive["modifiers"]):
        modifier = drive["modifiers"][modifier_name]
        source_kind, source_variable_id, reads = _reward_modifier_source(modifier)
        compiled_rules.append(
            CompiledVTCRewardComponent(
                rule_id=f"reward:modifier:{modifier_name}",
                kind="reward_modifier",
                source_variable_id=source_variable_id,
                variable_id=f"reward.modifier.{modifier_name}",
                expression=f"dac.modifier.{modifier_name}",
                expression_ast=None,
                condition=None,
                condition_ast=None,
                composition="overwrite",
                phase="compute_rewards",
                priority=len(compiled_rules),
                clamp=None,
                telemetry_label=f"reward_modifier:{modifier_name}",
                reads=reads,
                component="modifier",
                source_kind=source_kind,
                strategy=None,
                shaping_type=None,
                parameters=_reward_payload(modifier),
            )
        )

    extrinsic = drive["extrinsic"]
    extrinsic_strategy = str(getattr(extrinsic, "type", _mapping_get(extrinsic, "type", "unknown")))
    compiled_rules.append(
        CompiledVTCRewardComponent(
            rule_id=f"reward:extrinsic:{extrinsic_strategy}",
            kind="reward_component",
            source_variable_id="reward.extrinsic",
            variable_id="reward.extrinsic",
            expression=f"dac.extrinsic.{extrinsic_strategy}",
            expression_ast=None,
            condition=None,
            condition_ast=None,
            composition="overwrite",
            phase="compute_rewards",
            priority=len(compiled_rules),
            clamp=None,
            telemetry_label="reward_component:extrinsic",
            reads=_extrinsic_reward_reads(extrinsic),
            component="extrinsic",
            source_kind="dac_extrinsic",
            strategy=extrinsic_strategy,
            shaping_type=None,
            parameters=_reward_payload(extrinsic),
        )
    )

    intrinsic = drive["intrinsic"]
    intrinsic_strategy = str(getattr(intrinsic, "strategy", _mapping_get(intrinsic, "strategy", "unknown")))
    compiled_rules.append(
        CompiledVTCRewardComponent(
            rule_id=f"reward:intrinsic:{intrinsic_strategy}",
            kind="reward_component",
            source_variable_id="intrinsic_raw",
            variable_id="reward.intrinsic",
            expression="intrinsic_raw * dac.intrinsic.weight",
            expression_ast=None,
            condition=None,
            condition_ast=None,
            composition="overwrite",
            phase="compute_rewards",
            priority=len(compiled_rules),
            clamp=None,
            telemetry_label="reward_component:intrinsic",
            reads=_intrinsic_reward_reads(intrinsic),
            component="intrinsic",
            source_kind="dac_intrinsic",
            strategy=intrinsic_strategy,
            shaping_type=None,
            parameters=_reward_payload(intrinsic),
        )
    )

    for index, shaping in enumerate(drive["shaping"]):
        shaping_type = str(getattr(shaping, "type", _mapping_get(shaping, "type", "unknown")))
        compiled_rules.append(
            CompiledVTCRewardComponent(
                rule_id=f"reward:shaping:{index}:{shaping_type}",
                kind="reward_component",
                source_variable_id=f"reward.shaping.{index}",
                variable_id="reward.shaping",
                expression=f"dac.shaping.{shaping_type}",
                expression_ast=None,
                condition=None,
                condition_ast=None,
                composition="additive_delta",
                phase="compute_rewards",
                priority=len(compiled_rules),
                clamp=None,
                telemetry_label=f"reward_component:shaping:{index}",
                reads=_shaping_reward_reads(shaping),
                component="shaping",
                source_kind="dac_shaping",
                strategy=None,
                shaping_type=shaping_type,
                parameters=_reward_payload(shaping),
            )
        )

    compiled_rules.append(
        CompiledVTCRewardComponent(
            rule_id="reward:total",
            kind="reward_total",
            source_variable_id="reward.components",
            variable_id="reward.total",
            expression="reward.extrinsic + reward.intrinsic + reward.shaping",
            expression_ast=None,
            condition=None,
            condition_ast=None,
            composition="sum",
            phase="compute_rewards",
            priority=len(compiled_rules),
            clamp=None,
            telemetry_label="reward_total",
            reads=("reward.extrinsic", "reward.intrinsic", "reward.shaping"),
            component="total",
            source_kind="reward_composition",
            strategy=None,
            shaping_type=None,
            parameters={"components": ["extrinsic", "intrinsic", "shaping"]},
        )
    )

    return VTCRewardProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


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
                cascade_threshold=cascade["threshold"],
                cascade_strength=cascade["strength"],
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


def compile_vtc_passive_depletions(meters: Sequence[VTCPassiveDepletionSource | Mapping[str, Any]]) -> VTCPassiveDepletionProgram:
    """Compile meter passive depletion rates into VTC overwrite rules."""
    return compile_vtc_passive_depletions_with_phase_graph(meters, TransitionPhaseGraph.default())


def compile_vtc_passive_depletions_with_phase_graph(
    meters: Sequence[VTCPassiveDepletionSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCPassiveDepletionProgram:
    """Compile meter passive depletion rates using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCPassiveDepletion] = []

    for priority, raw_meter in enumerate(meters):
        meter = _coerce_passive_depletion(raw_meter)
        depletion_literal = _format_rule_float(meter["passive"])
        expression = f"bar.{meter['name']} - ({depletion_literal} * temporal.depletion_multiplier)"
        compiled_rules.append(
            CompiledVTCPassiveDepletion(
                rule_id=f"passive:{meter['name']}",
                kind="passive_depletion",
                source_variable_id=meter["name"],
                variable_id=meter["name"],
                expression=expression,
                expression_ast=parser.parse(expression),
                condition=None,
                condition_ast=None,
                composition="overwrite",
                phase="apply_passive_depletion",
                priority=priority,
                clamp=(0.0, 1.0),
                telemetry_label=f"passive_depletion:{meter['name']}",
                passive_rate=meter["passive"],
            )
        )

    return VTCPassiveDepletionProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_passive_depletion(meter: VTCPassiveDepletionSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(meter, Mapping):
        name = str(meter["name"])
        depletion = meter["depletion"]
        passive = float(depletion["passive"] if isinstance(depletion, Mapping) else getattr(depletion, "passive"))
    else:
        name = meter.name
        passive = float(meter.depletion.passive)

    return {
        "name": name,
        "passive": passive,
    }


def compile_vtc_modulations(modulations: Sequence[VTCModulationSource | Mapping[str, Any]]) -> VTCModulationProgram:
    """Compile affordance modulation parameters into VTC multiplier rules."""
    return compile_vtc_modulations_with_phase_graph(modulations, TransitionPhaseGraph.default())


def compile_vtc_modulations_with_phase_graph(
    modulations: Sequence[VTCModulationSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCModulationProgram:
    """Compile affordance modulation parameters using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCModulation] = []

    for raw_modulation in modulations:
        modulation = _coerce_modulation(raw_modulation)
        for affordance in modulation["affordances"]:
            threshold_literal = _format_rule_float(modulation["threshold"])
            min_multiplier_literal = _format_rule_float(modulation["min_multiplier"])
            if modulation["threshold"] == 0.0:
                expression = "1.0"
            else:
                expression = (
                    f"where(bar.{modulation['bar']} < {threshold_literal}, "
                    f"{min_multiplier_literal} + (1.0 - {min_multiplier_literal}) * "
                    f"(bar.{modulation['bar']} / {threshold_literal}), 1.0)"
                )
            rule_id = f"{modulation['bar']}->{affordance}"
            compiled_rules.append(
                CompiledVTCModulation(
                    rule_id=rule_id,
                    kind="modulation",
                    source_variable_id=modulation["bar"],
                    target_affordance_id=affordance,
                    variable_id=f"affordance.{affordance}.multiplier",
                    expression=expression,
                    expression_ast=parser.parse(expression),
                    condition=None,
                    condition_ast=None,
                    composition="multiplicative_modifier",
                    phase="apply_modulations",
                    priority=len(compiled_rules),
                    clamp=(0.0, 1.0),
                    telemetry_label=f"modulation:{rule_id}",
                    modulation_threshold=modulation["threshold"],
                    min_multiplier=modulation["min_multiplier"],
                )
            )

    return VTCModulationProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_modulation(modulation: VTCModulationSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(modulation, Mapping):
        bar = str(modulation["bar"])
        affordances = [str(affordance) for affordance in modulation["affordances"]]
        modulation_type = str(modulation["type"])
        threshold = float(modulation["threshold"])
        min_multiplier = float(modulation["min_multiplier"])
    else:
        bar = modulation.bar
        affordances = [str(affordance) for affordance in modulation.affordances]
        modulation_type = str(modulation.type)
        threshold = float(modulation.threshold)
        min_multiplier = float(modulation.min_multiplier)

    if modulation_type != "linear_multiplier":
        raise ValueError(f"Unsupported VTC modulation type '{modulation_type}' for bar '{bar}'")

    return {
        "bar": bar,
        "affordances": affordances,
        "threshold": threshold,
        "min_multiplier": min_multiplier,
    }


def compile_vtc_interaction_progress(
    affordances: Sequence[VTCInteractionProgressSource | Mapping[str, Any]],
) -> VTCInteractionProgressProgram:
    """Compile multi-tick affordance durations into VTC progress and completion rules."""
    return compile_vtc_interaction_progress_with_phase_graph(affordances, TransitionPhaseGraph.default())


def compile_vtc_interaction_progress_with_phase_graph(
    affordances: Sequence[VTCInteractionProgressSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCInteractionProgressProgram:
    """Compile multi-tick affordance durations using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    progress_rules: list[CompiledVTCInteractionProgress] = []
    completion_bonus_rules: list[CompiledVTCInteractionCompletionBonus] = []
    progress_expression = "where(same_affordance and affordance_is_open and chosen_interact, interaction_progress + 1, 0)"

    for raw_affordance in affordances:
        affordance = _coerce_interaction_progress_affordance(raw_affordance)
        if affordance["interaction_type"] not in {"multi_tick", "dual"}:
            continue

        name = affordance["name"]
        duration_ticks = affordance["duration_ticks"]
        priority = len(progress_rules)
        slug = _rule_slug(name)
        progress_rules.append(
            CompiledVTCInteractionProgress(
                rule_id=f"{slug}_advance_interaction_progress",
                kind="interaction_progress",
                source_variable_id="interaction_progress",
                target_affordance_id=name,
                variable_id="interaction_progress",
                expression=progress_expression,
                expression_ast=parser.parse(progress_expression),
                condition=None,
                condition_ast=None,
                composition="overwrite",
                phase="advance_interaction_progress",
                priority=priority,
                clamp=None,
                telemetry_label=f"interaction_progress:{name}",
                duration_ticks=duration_ticks,
            )
        )

        completion_expression = f"interaction_progress >= {duration_ticks}"
        completion_bonus_rules.append(
            CompiledVTCInteractionCompletionBonus(
                rule_id=f"{slug}_completion_bonus",
                kind="interaction_completion_bonus",
                source_variable_id="interaction_progress",
                target_affordance_id=name,
                variable_id=f"affordance.{name}.completed",
                expression=completion_expression,
                expression_ast=parser.parse(completion_expression),
                condition=None,
                condition_ast=None,
                composition="event",
                phase="apply_completion_bonuses",
                priority=priority,
                clamp=None,
                telemetry_label=f"interaction_completion_bonus:{name}",
                duration_ticks=duration_ticks,
            )
        )

    return VTCInteractionProgressProgram(
        progress_rules=tuple(
            sorted(
                progress_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        ),
        completion_bonus_rules=tuple(
            sorted(
                completion_bonus_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        ),
    )


def _coerce_interaction_progress_affordance(
    affordance: VTCInteractionProgressSource | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(affordance, Mapping):
        name = str(affordance["name"])
        interaction_type = str(affordance.get("interaction_type") or "instant")
        duration_ticks = affordance.get("duration_ticks")
    else:
        name = affordance.name
        interaction_type = str(affordance.interaction_type or "instant")
        duration_ticks = affordance.duration_ticks

    if interaction_type not in {"instant", "multi_tick", "dual"}:
        raise ValueError(f"Unsupported VTC interaction_type '{interaction_type}' for affordance '{name}'")
    if interaction_type in {"multi_tick", "dual"}:
        if duration_ticks is None:
            raise ValueError(f"Affordance '{name}' interaction_type='{interaction_type}' requires duration_ticks")
        duration = int(duration_ticks)
        if duration <= 0:
            raise ValueError(f"Affordance '{name}' duration_ticks must be positive, got {duration}")
    else:
        duration = None

    return {
        "name": name,
        "interaction_type": interaction_type,
        "duration_ticks": duration,
    }


def compile_vtc_terminal_conditions(
    meters: Sequence[VTCTerminalConditionSource | Mapping[str, Any]],
) -> VTCTerminalConditionProgram:
    """Compile lethal meter bounds into VTC terminal-condition rules."""
    return compile_vtc_terminal_conditions_with_phase_graph(meters, TransitionPhaseGraph.default())


def compile_vtc_terminal_conditions_with_phase_graph(
    meters: Sequence[VTCTerminalConditionSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCTerminalConditionProgram:
    """Compile lethal meter bounds using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCTerminalCondition] = []

    for raw_meter in meters:
        meter = _coerce_terminal_condition_meter(raw_meter)
        if meter["lethal_min"]:
            threshold = meter["min"]
            operator = "<="
            name = meter["name"]
            expression = f"bar.{name} {operator} {_format_rule_float(threshold)}"
            compiled_rules.append(
                CompiledVTCTerminalCondition(
                    rule_id=f"terminal:{name}:min",
                    kind="terminal_condition",
                    source_variable_id=name,
                    variable_id="done",
                    expression=expression,
                    expression_ast=parser.parse(expression),
                    condition=None,
                    condition_ast=None,
                    composition="event",
                    phase="evaluate_terminal_conditions",
                    priority=len(compiled_rules),
                    clamp=None,
                    telemetry_label=f"terminal_condition:{name}:min",
                    operator=operator,
                    threshold=threshold,
                )
            )
        if meter["lethal_max"]:
            threshold = meter["max"]
            operator = ">="
            name = meter["name"]
            expression = f"bar.{name} {operator} {_format_rule_float(threshold)}"
            compiled_rules.append(
                CompiledVTCTerminalCondition(
                    rule_id=f"terminal:{name}:max",
                    kind="terminal_condition",
                    source_variable_id=name,
                    variable_id="done",
                    expression=expression,
                    expression_ast=parser.parse(expression),
                    condition=None,
                    condition_ast=None,
                    composition="event",
                    phase="evaluate_terminal_conditions",
                    priority=len(compiled_rules),
                    clamp=None,
                    telemetry_label=f"terminal_condition:{name}:max",
                    operator=operator,
                    threshold=threshold,
                )
            )

    return VTCTerminalConditionProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_terminal_condition_meter(meter: VTCTerminalConditionSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(meter, Mapping):
        name = str(meter["name"])
        bounds = meter["bounds"]
    else:
        name = meter.name
        bounds = meter.bounds

    if isinstance(bounds, Mapping):
        min_value = float(bounds["min"])
        max_value = float(bounds["max"])
        lethal_min = bool(bounds["lethal_min"])
        lethal_max = bool(bounds["lethal_max"])
    else:
        min_value = float(bounds.min)
        max_value = float(bounds.max)
        lethal_min = bool(bounds.lethal_min)
        lethal_max = bool(bounds.lethal_max)

    return {
        "name": name,
        "min": min_value,
        "max": max_value,
        "lethal_min": lethal_min,
        "lethal_max": lethal_max,
    }


def compile_vtc_affordance_gates(affordances: Sequence[VTCAffordanceGateSource | Mapping[str, Any]]) -> VTCAffordanceGateProgram:
    """Compile affordance opening hours into VTC action-legality gate rules."""
    return compile_vtc_affordance_gates_with_phase_graph(affordances, TransitionPhaseGraph.default())


def compile_vtc_affordance_gates_with_phase_graph(
    affordances: Sequence[VTCAffordanceGateSource | Mapping[str, Any]],
    phase_graph: TransitionPhaseGraph,
) -> VTCAffordanceGateProgram:
    """Compile affordance opening hours using an explicit VTC transition phase graph."""
    parser = ExpressionParser()
    compiled_rules: list[CompiledVTCAffordanceGate] = []

    for priority, raw_affordance in enumerate(affordances):
        affordance = _coerce_affordance_gate(raw_affordance)
        expression = _opening_hours_expression(affordance["windows"])
        name = affordance["name"]
        compiled_rules.append(
            CompiledVTCAffordanceGate(
                rule_id=f"{_rule_slug(name)}_open_window",
                kind="affordance_gate",
                source_variable_id="time_of_day",
                target_affordance_id=name,
                variable_id=f"affordance.{name}.available",
                expression=expression,
                expression_ast=parser.parse(expression),
                condition=None,
                condition_ast=None,
                composition="overwrite",
                phase="compute_action_legality_masks",
                priority=priority,
                clamp=None,
                telemetry_label=f"affordance_gate:{name}",
            )
        )

    return VTCAffordanceGateProgram(
        rules=tuple(
            sorted(
                compiled_rules,
                key=lambda item: (phase_graph.sort_key(item.phase), item.priority, item.rule_id),
            )
        )
    )


def _coerce_affordance_gate(affordance: VTCAffordanceGateSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(affordance, Mapping):
        name = str(affordance["name"])
        opening_hours = affordance["opening_hours"]
    else:
        name = affordance.name
        opening_hours = affordance.opening_hours

    enabled = _opening_hours_enabled(opening_hours)
    if not enabled:
        return {"name": name, "windows": [(0.0, 24.0)]}

    windows = _opening_hours_windows(opening_hours)
    if not windows:
        raise ValueError(f"Affordance '{name}' opening_hours.enabled=true requires at least one VTC gate window")
    return {"name": name, "windows": windows}


def _opening_hours_enabled(opening_hours: Any) -> bool:
    if isinstance(opening_hours, Mapping):
        return bool(opening_hours["enabled"])
    return bool(opening_hours.enabled)


def _opening_hours_windows(opening_hours: Any) -> list[tuple[float, float]]:
    schedule = opening_hours["schedule"] if isinstance(opening_hours, Mapping) else opening_hours.schedule
    windows: list[tuple[float, float]] = []
    for window in schedule:
        if isinstance(window, Mapping):
            start = window["start"]
            end = window["end"]
        else:
            start = window.start
            end = window.end
        windows.append((float(start), float(end)))
    return windows


def _opening_hours_expression(windows: Sequence[tuple[float, float]]) -> str:
    expressions = [
        f"time_in_window(temporal.time_of_day, {_format_rule_float(start)}, {_format_rule_float(end)})" for start, end in windows
    ]
    return " || ".join(expressions)


def _coerce_reward_drive(drive_config: VTCRewardConfigSource | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(drive_config, Mapping):
        modifiers = drive_config.get("modifiers", {})
        extrinsic = drive_config["extrinsic"]
        intrinsic = drive_config["intrinsic"]
        shaping = drive_config.get("shaping", [])
    else:
        modifiers = drive_config.modifiers
        extrinsic = drive_config.extrinsic
        intrinsic = drive_config.intrinsic
        shaping = drive_config.shaping

    return {
        "modifiers": dict(modifiers),
        "extrinsic": extrinsic,
        "intrinsic": intrinsic,
        "shaping": list(shaping),
    }


def _reward_modifier_source(modifier: Any) -> tuple[str, str, tuple[str, ...]]:
    bar = _config_field(modifier, "bar", None)
    if bar is not None:
        bar_id = str(bar)
        return "bar", f"bar.{bar_id}", (f"bar.{bar_id}",)

    variable = _config_field(modifier, "variable", None)
    if variable is not None:
        variable_id = str(variable)
        return "vfs_variable", f"vfs.{variable_id}", (f"vfs.{variable_id}",)

    source = _config_field(modifier, "source", None)
    if source is not None:
        source_id = str(source)
        return "bar", f"bar.{source_id}", (f"bar.{source_id}",)

    raise ValueError("VTC reward modifier must declare bar, variable, or source")


def _extrinsic_reward_reads(strategy: Any) -> tuple[str, ...]:
    reads: list[str] = []
    reads.extend(_bar_read(bar) for bar in _iter_config_strings(_config_field(strategy, "bars", [])))

    for bonus in _iter_config_items(_config_field(strategy, "bar_bonuses", [])):
        reads.append(_bar_read(str(_config_field(bonus, "bar"))))

    for bonus in _iter_config_items(_config_field(strategy, "bonuses", [])):
        reads.append(_bar_read(str(_config_field(bonus, "bar"))))

    variable = _config_field(strategy, "variable", None)
    if variable is not None:
        reads.append(_vfs_read(str(variable)))

    for bonus in _iter_config_items(_config_field(strategy, "variable_bonuses", [])):
        reads.append(_vfs_read(str(_config_field(bonus, "variable"))))

    reads.extend(_modifier_read(name) for name in _iter_config_strings(_config_field(strategy, "apply_modifiers", [])))
    return _dedupe(reads)


def _intrinsic_reward_reads(strategy: Any) -> tuple[str, ...]:
    reads = ["intrinsic_raw"]
    reads.extend(_modifier_read(name) for name in _iter_config_strings(_config_field(strategy, "apply_modifiers", [])))
    return _dedupe(reads)


def _shaping_reward_reads(shaping: Any) -> tuple[str, ...]:
    shaping_type = str(_config_field(shaping, "type", "unknown"))
    reads: list[str] = []

    if shaping_type == "approach_reward":
        target = _config_field(shaping, "target_affordance", None) or _config_field(shaping, "target", None)
        reads.append("position.agent")
        if target is not None:
            reads.append(f"affordance.{target}.position")
    elif shaping_type == "completion_bonus":
        reads.append("last_action_affordance")
        affordance = _config_field(shaping, "affordance", None)
        if affordance is not None:
            reads.append(f"affordance.{affordance}.completed")
    elif shaping_type == "efficiency_bonus":
        reads.append(_bar_read(str(_config_field(shaping, "bar"))))
    elif shaping_type == "state_achievement":
        for condition in _iter_config_items(_config_field(shaping, "conditions", [])):
            reads.append(_bar_read(str(_config_field(condition, "bar"))))
    elif shaping_type == "vfs_variable":
        reads.append(_vfs_read(str(_config_field(shaping, "variable"))))
    elif shaping_type == "streak_bonus":
        affordance = str(_config_field(shaping, "affordance"))
        reads.append(f"affordance.{affordance}.streak")
    elif shaping_type == "diversity_bonus":
        reads.append("affordance.unique_used")
    elif shaping_type == "timing_bonus":
        reads.extend(("temporal.current_hour", "last_action_affordance"))
        for time_range in _iter_config_items(_config_field(shaping, "time_ranges", [])):
            reads.append(f"affordance.{_config_field(time_range, 'affordance')}.used")
    elif shaping_type == "economic_efficiency":
        reads.append(_bar_read(str(_config_field(shaping, "money_bar"))))
    elif shaping_type == "balance_bonus":
        reads.extend(_bar_read(bar) for bar in _iter_config_strings(_config_field(shaping, "bars", [])))
    elif shaping_type == "crisis_avoidance":
        reads.append(_bar_read(str(_config_field(shaping, "bar"))))

    return _dedupe(reads)


def _config_field(config: Any, field: str, default: Any = None) -> Any:
    if isinstance(config, Mapping):
        return config.get(field, default)
    return getattr(config, field, default)


def _mapping_get(config: Any, field: str, default: Any = None) -> Any:
    if isinstance(config, Mapping):
        return config.get(field, default)
    return default


def _iter_config_items(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value)


def _iter_config_strings(value: Any) -> list[str]:
    return [str(item) for item in _iter_config_items(value)]


def _bar_read(bar_id: str) -> str:
    return f"bar.{bar_id}"


def _vfs_read(variable_id: str) -> str:
    return f"vfs.{variable_id}"


def _modifier_read(modifier_name: str) -> str:
    return f"reward.modifier.{modifier_name}"


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return tuple(deduped)


def _reward_payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        payload = value.model_dump(mode="json")
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        payload = dict(vars(value))
    plain_payload = _plain_reward_payload(payload)
    if not isinstance(plain_payload, dict):
        raise TypeError("VTC reward component parameters must resolve to a mapping payload")
    return plain_payload


def _plain_reward_payload(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _plain_reward_payload(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        return {str(key): _plain_reward_payload(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain_reward_payload(item) for item in value]
    return value


def _rule_slug(name: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in name).strip("_") or "affordance"


def _required_clamp(clamp: tuple[float, float] | None, telemetry_label: str) -> tuple[float, float]:
    if clamp is None:
        raise ValueError(f"Generated VTC rule '{telemetry_label}' requires explicit clamp bounds for scripted execution")
    return clamp


def _format_rule_float(value: float) -> str:
    return repr(float(value))
