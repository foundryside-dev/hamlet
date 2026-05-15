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

        for write in self.writes:
            if write.variable_id not in updated:
                raise KeyError(f"Action write targets unknown VFS variable '{write.variable_id}'")

            context = ExecutionContext(
                bars={},
                vfs=dict(updated),
                affordances={},
                temporal={},
                device=device,
            )
            evaluator = Evaluator(context)
            current_value = updated[write.variable_id]
            write_mask = self._build_write_mask(write, actions.to(device=device), active_mask.to(device=device), evaluator)
            expression_value = self._evaluate_tensor(evaluator, write.expression_ast, "expression", write)
            composed_value = self._compose_value(write, current_value, expression_value)
            if write.clamp is not None:
                low, high = write.clamp
                composed_value = torch.clamp(composed_value, min=low, max=high)

            broadcast_mask = self._broadcast_agent_mask(write_mask, current_value, write)
            updated[write.variable_id] = torch.where(
                broadcast_mask,
                composed_value.to(device=device, dtype=current_value.dtype),
                current_value,
            )

        return updated

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
    def _compose_value(write: CompiledActionWrite, current_value: torch.Tensor, expression_value: torch.Tensor) -> torch.Tensor:
        if write.composition == "overwrite":
            return expression_value
        raise NotImplementedError(
            f"Action write composition '{write.composition}' is not implemented yet; "
            "the current compiler step supports masked overwrite writes only."
        )

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
