"""Compile ActionConfig writes into masked tensor updates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import torch

from townlet.environment.action_config import ActionConfig
from townlet.world.expression import ASTNode, ExpressionParser
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator


@dataclass(frozen=True)
class CompiledActionWrite:
    """A parsed action write with the metadata needed for masked execution."""

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
class CompiledActionWriteProgram:
    """Executable collection of compiled action writes."""

    writes: tuple[CompiledActionWrite, ...]

    def apply(
        self,
        *,
        actions: torch.Tensor,
        vfs_state: Mapping[str, torch.Tensor],
        active_mask: torch.Tensor,
        device: torch.device,
    ) -> dict[str, torch.Tensor]:
        """Apply compiled writes to a VFS state snapshot using action and active-agent masks."""
        if actions.shape != active_mask.shape:
            raise ValueError(f"actions shape {tuple(actions.shape)} must match active_mask shape {tuple(active_mask.shape)}")

        updated = {name: value.to(device=device).clone() for name, value in vfs_state.items()}
        actions_on_device = actions.to(device=device)
        active_mask_on_device = active_mask.to(device=device)

        for phase_writes in self._iter_phase_groups():
            phase_snapshot = dict(updated)
            phase_values = dict(updated)
            priority_state: dict[str, torch.Tensor] = {}

            for write in phase_writes:
                if write.variable_id not in phase_values:
                    raise KeyError(f"Action write targets unknown VFS variable '{write.variable_id}'")

                context = ExecutionContext(
                    bars={},
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

    def _iter_phase_groups(self) -> list[tuple[CompiledActionWrite, ...]]:
        phase_groups: list[tuple[CompiledActionWrite, ...]] = []
        current_phase: str | None = None
        current_group: list[CompiledActionWrite] = []

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
        write: CompiledActionWrite,
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

    def _compose_candidate(self, write: CompiledActionWrite, phase_value: torch.Tensor, expression_value: torch.Tensor) -> torch.Tensor:
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
            f"Action write composition '{write.composition}' is not implemented yet; "
            "claim/capacity/event compositions are tracked outside this action-write composition step."
        )

    @staticmethod
    def _apply_optional_clamp(write: CompiledActionWrite, value: torch.Tensor) -> torch.Tensor:
        if write.clamp is None:
            return value
        low, high = write.clamp
        return torch.clamp(value, min=low, max=high)

    def _apply_priority_write(
        self,
        write: CompiledActionWrite,
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
        write: CompiledActionWrite,
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
    def _evaluate_tensor(evaluator: Evaluator, ast: ASTNode, kind: str, write: CompiledActionWrite) -> torch.Tensor:
        value: Any = evaluator.evaluate(ast)
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"Action write {write.telemetry_label} {kind} resolved to non-tensor value")
        return value

    @staticmethod
    def _coerce_condition_mask(condition: torch.Tensor, actions: torch.Tensor, write: CompiledActionWrite) -> torch.Tensor:
        if condition.dim() == 0:
            return torch.full(actions.shape, bool(condition.item()), dtype=torch.bool, device=actions.device)
        if condition.shape != actions.shape:
            raise ValueError(
                f"Condition for action write '{write.telemetry_label}' produced shape {tuple(condition.shape)}, "
                f"expected {tuple(actions.shape)}"
            )
        return condition.to(device=actions.device, dtype=torch.bool)

    @staticmethod
    def _broadcast_agent_mask(mask: torch.Tensor, target: torch.Tensor, write: CompiledActionWrite) -> torch.Tensor:
        if target.dim() == 0:
            raise ValueError(f"Action write '{write.telemetry_label}' cannot apply a per-agent action mask to scalar variable")
        if target.shape[0] != mask.shape[0]:
            raise ValueError(
                f"Action write '{write.telemetry_label}' target leading dimension {target.shape[0]} "
                f"does not match action batch {mask.shape[0]}"
            )
        broadcast_mask = mask
        while broadcast_mask.dim() < target.dim():
            broadcast_mask = broadcast_mask.unsqueeze(-1)
        return broadcast_mask


def compile_action_writes(actions: Sequence[ActionConfig]) -> CompiledActionWriteProgram:
    """Compile ActionConfig writes into parsed records sorted by phase, priority, and action id."""
    parser = ExpressionParser()
    compiled_writes: list[CompiledActionWrite] = []

    for action in actions:
        for write in action.writes:
            compiled_writes.append(
                CompiledActionWrite(
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

    return CompiledActionWriteProgram(
        writes=tuple(sorted(compiled_writes, key=lambda item: (item.phase, item.priority, item.action_id, item.telemetry_label)))
    )
