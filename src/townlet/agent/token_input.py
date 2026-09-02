"""Network-owned expansion of one compact token type at a time."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from townlet.universe.dto.token_spec import TokenSpec


@dataclass(frozen=True)
class _TypeAssembly:
    capacity: int
    compact_row_width: int
    fixed_row_width: int
    context_buffer: str
    dynamic_lane_buffer: str
    fixed_lane_buffer: str
    selector_lane: int | None


class TokenInputAssembler(nn.Module):
    """Expand ``[B, C, compact_row_width]`` at one type's fixed network boundary."""

    def __init__(self, token_spec: TokenSpec) -> None:
        super().__init__()
        compact_layout = token_spec.compact_layout()
        assemblies: dict[str, _TypeAssembly] = {}
        for type_index, schema in enumerate(token_spec.types):
            type_layout = compact_layout.get_type(schema.type_name)
            assert type_layout is not None
            context_name = f"_token_context_{type_index}"
            dynamic_lane_name = f"_dynamic_lanes_{type_index}"
            fixed_lane_name = f"_fixed_lanes_{type_index}"
            if schema.type_name == "effect":
                context_payloads = tuple(context.fixed_payload for context in schema.effect_catalog_contexts)
            else:
                context_payloads = schema.slot_context_payloads
            context_rows = torch.zeros((len(context_payloads), schema.fixed_row_width), dtype=torch.float32)
            if context_payloads:
                context_rows[:, 1:] = torch.tensor(context_payloads, dtype=torch.float32)
            dynamic_lanes = tuple(lane for lane, fixed_lane in enumerate(type_layout.fixed_scatter_indices) if fixed_lane is not None)
            fixed_lanes = tuple(fixed_lane for fixed_lane in type_layout.fixed_scatter_indices if fixed_lane is not None)
            self.register_buffer(context_name, context_rows, persistent=False)
            self.register_buffer(dynamic_lane_name, torch.tensor(dynamic_lanes, dtype=torch.long), persistent=False)
            self.register_buffer(fixed_lane_name, torch.tensor(fixed_lanes, dtype=torch.long), persistent=False)
            selector_lane = None
            if "context_index" in type_layout.dynamic_features:
                selector_lane = type_layout.dynamic_features.index("context_index")
            assemblies[schema.type_name] = _TypeAssembly(
                capacity=schema.capacity,
                compact_row_width=type_layout.compact_row_width,
                fixed_row_width=schema.fixed_row_width,
                context_buffer=context_name,
                dynamic_lane_buffer=dynamic_lane_name,
                fixed_lane_buffer=fixed_lane_name,
                selector_lane=selector_lane,
            )
        self._assemblies = assemblies

    def expand_type(self, type_name: str, dynamic_rows: torch.Tensor) -> torch.Tensor:
        """``[B, capacity, compact_row_width] -> [B, capacity, fixed_row_width]``."""
        assembly = self._assemblies.get(type_name)
        if assembly is None:
            raise ValueError(f"Unknown token type {type_name!r}")
        expected_tail = (assembly.capacity, assembly.compact_row_width)
        if dynamic_rows.dim() != 3 or tuple(dynamic_rows.shape[1:]) != expected_tail:
            raise ValueError(
                f"Token type {type_name!r} compact rows must have shape [batch, {assembly.capacity}, "
                f"{assembly.compact_row_width}], got {tuple(dynamic_rows.shape)}"
            )
        if not dynamic_rows.is_floating_point():
            raise ValueError(f"Token type {type_name!r} compact rows must use a floating dtype, got {dynamic_rows.dtype}")

        presence = dynamic_rows[:, :, 0] != 0
        context = getattr(self, assembly.context_buffer)
        if assembly.selector_lane is None:
            if context.shape[0] != assembly.capacity:
                raise ValueError(f"Token type {type_name!r} has {context.shape[0]} positional contexts for capacity {assembly.capacity}")
            fixed_rows = (
                context.to(device=dynamic_rows.device, dtype=dynamic_rows.dtype).unsqueeze(0).expand(dynamic_rows.shape[0], -1, -1).clone()
            )
        else:
            selectors = dynamic_rows[:, :, assembly.selector_lane]
            selected = selectors[presence]
            if selected.numel():
                if not bool(torch.isfinite(selected).all()):
                    raise ValueError("Present effect context_index must be finite before catalog gather")
                if not bool((selected == selected.trunc()).all()):
                    raise ValueError("Present effect context_index must be integral before catalog gather")
                if not bool((selected.to(dtype=torch.float32).to(dtype=selected.dtype) == selected).all()):
                    raise ValueError("Present effect context_index must be exactly representable in float32 before catalog gather")
                if context.shape[0] == 0:
                    raise ValueError("Present effect cannot select from an empty effect catalog")
                if not bool(((selected >= 0) & (selected < context.shape[0])).all()):
                    raise ValueError(f"Present effect context_index must be in range [0, {context.shape[0]}) before catalog gather")
            safe_selectors = torch.where(presence, selectors, torch.zeros_like(selectors)).to(dtype=torch.long)
            if context.shape[0] == 0:
                fixed_rows = torch.zeros(
                    (*dynamic_rows.shape[:2], assembly.fixed_row_width),
                    dtype=dynamic_rows.dtype,
                    device=dynamic_rows.device,
                )
            else:
                fixed_rows = (
                    context.to(device=dynamic_rows.device, dtype=dynamic_rows.dtype)
                    .index_select(0, safe_selectors.flatten())
                    .view(dynamic_rows.shape[0], assembly.capacity, assembly.fixed_row_width)
                )

        dynamic_lanes = getattr(self, assembly.dynamic_lane_buffer)
        fixed_lanes = getattr(self, assembly.fixed_lane_buffer)
        fixed_rows[:, :, fixed_lanes] = dynamic_rows[:, :, dynamic_lanes]
        return torch.where(presence.unsqueeze(-1), fixed_rows, torch.zeros_like(fixed_rows))
