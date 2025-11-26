"""Execution context for expression evaluation."""

from dataclasses import dataclass
from typing import Any

import torch

from townlet.world.expression.history import TemporalHistory


@dataclass
class ExecutionContext:
    """Runtime context for expression evaluation.

    Provides access to simulation state:
    - bars: Meter values (energy, health, etc.)
    - vfs: Variable & Feature System state
    - affordances: Affordance positions/states
    - temporal: Time-based values (tick count, day/night)
    """

    bars: dict[str, torch.Tensor]  # e.g., {"energy": tensor([batch])}
    vfs: dict[str, torch.Tensor]
    affordances: dict[str, Any]  # Affordance state
    temporal: dict[str, torch.Tensor]  # Time values
    affordance_positions: dict[str, torch.Tensor] | None = None
    agent_positions: torch.Tensor | None = None
    device: torch.device = torch.device("cpu")
    vfs_types: dict[str, str] | None = None  # Variable id → type (agent_ref/item_ref/etc.)
    num_agents: int | None = None
    self_indices: torch.Tensor | None = None
    target_indices: torch.Tensor | None = None
    item_vfs: torch.Tensor | None = None
    item_profile_map: dict[str, dict[str, int]] | None = None
    item_index_to_profile: dict[int, str] | None = None
    history: TemporalHistory | None = None
    step: int | None = None

    def get(self, path: str) -> torch.Tensor:
        """Resolve dotted path to tensor value.

        Args:
            path: Dotted path like "bar.energy" or "vfs.is_night", or bare variable name like "intensity"

        Returns:
            Tensor value from context

        Raises:
            KeyError: If path not found
        """
        segments = [seg for seg in path.split(".") if seg]
        segments = [seg for seg in segments if seg != "ref"]
        if not segments:
            raise KeyError(f"Path '{path}' not found in execution context")

        root, tail = segments[0], segments[1:]

        if root == "bar":
            return self._read_bar(tail, path)
        if root == "temporal":
            return self._read_temporal(tail, path)
        if root == "global":
            if not tail or tail[0] != "vfs":
                raise KeyError(f"Path '{path}' not found in execution context")
            return self._resolve_vfs_chain(tail[1:], base_indices=None, scope="global", original_path=path)
        if root in {"vfs", "self", "target"}:
            return self._resolve_entity_path(root=root, tail=tail, original_path=path)
        if len(segments) == 1 and path in self.vfs:
            return self.vfs[path]
        raise KeyError(f"Path '{path}' not found in execution context")

    def _resolve_entity_path(self, root: str, tail: list[str], original_path: str) -> torch.Tensor:
        if not tail:
            raise KeyError(f"Path '{original_path}' not found in execution context")

        if tail[0] == "bar":
            bar_name = tail[1] if len(tail) > 1 else None
            if bar_name is None:
                raise KeyError(f"Path '{original_path}' not found in execution context")
            indices = self._select_indices(root)
            bar_tensor = self._bar_tensor(bar_name, original_path)
            if indices is None or bar_tensor.dim() == 0:
                return bar_tensor
            return self._gather_by_index(bar_tensor, self._ensure_indices(indices, bar_tensor.device))

        vfs_tail = tail
        if vfs_tail and vfs_tail[0] == "vfs":
            vfs_tail = vfs_tail[1:]

        return self._resolve_vfs_chain(
            vfs_tail,
            base_indices=self._select_indices(root),
            scope="agent",
            original_path=original_path,
        )

    def _select_indices(self, root: str) -> torch.Tensor | None:
        if root == "self":
            if self.self_indices is not None:
                return self.self_indices
            return self._default_indices()
        if root == "target":
            if self.target_indices is not None:
                return self.target_indices
            if "target" in self.vfs and self._lookup_var_type("target") == "agent_ref":
                return self.vfs["target"].long()
            return None
        if root == "vfs":
            return self._default_indices()
        return None

    def _resolve_vfs_chain(
        self,
        segments: list[str],
        base_indices: torch.Tensor | None,
        scope: str,
        original_path: str,
    ) -> torch.Tensor:
        if not segments:
            raise KeyError(f"Path '{original_path}' not found in execution context")

        var_name, *rest = segments
        value = self._get_vfs_value(var_name, base_indices=base_indices, scope=scope, original_path=original_path)
        var_type = self._lookup_var_type(var_name)

        if not rest:
            return value

        if var_type is None:
            raise KeyError(f"Cannot traverse '{original_path}' without vfs_types for '{var_name}'")
        if var_type not in {"agent_ref", "item_ref"}:
            raise KeyError(f"Path '{original_path}' not found in execution context")

        hop, *tail = rest
        if var_type == "agent_ref":
            return self._resolve_agent_reference(hop, tail, value, original_path)
        return self._resolve_item_reference(hop, tail, value, original_path)

    def _resolve_agent_reference(self, hop: str, tail: list[str], ref_value: torch.Tensor, original_path: str) -> torch.Tensor:
        indices = ref_value.long()
        batch = self._infer_batch_size()
        self._validate_indices(indices, batch, label="agent reference")
        valid_mask = self._reference_valid_mask(indices, batch)
        safe_indices = torch.where(valid_mask, indices, torch.zeros_like(indices))

        if hop == "bar":
            if not tail:
                raise KeyError(f"Path '{original_path}' not found in execution context")
            bar_tensor = self._bar_tensor(tail[0], original_path)
            gathered = self._gather_by_index(bar_tensor, self._ensure_indices(safe_indices, bar_tensor.device))
            if len(tail) > 1:
                raise KeyError(f"Cannot traverse beyond bar values in '{original_path}'")
            return self._mask_reference_output(gathered, valid_mask)

        if hop != "vfs":
            raise KeyError(f"Invalid reference traversal segment '{hop}' in '{original_path}'")

        result = self._resolve_vfs_chain(
            tail,
            base_indices=self._ensure_indices(safe_indices, self.device),
            scope="agent",
            original_path=original_path,
        )
        if isinstance(result, torch.Tensor):
            return self._mask_reference_output(result, valid_mask)
        return result

    def _resolve_item_reference(self, hop: str, tail: list[str], ref_value: torch.Tensor, original_path: str) -> torch.Tensor:
        if hop != "vfs":
            raise KeyError(f"Item references only support '.vfs' traversal in '{original_path}'")
        if self.item_vfs is None or self.item_profile_map is None or self.item_index_to_profile is None:
            raise KeyError(f"Item reference in '{original_path}' requires item VFS metadata")
        if not tail:
            raise KeyError(f"Path '{original_path}' not found in execution context")
        if len(tail) > 1:
            raise KeyError(f"Cannot traverse beyond item variables in '{original_path}'")

        indices = self._ensure_indices(ref_value, self.item_vfs.device)
        self._validate_indices(indices, self.item_vfs.shape[0], label="item reference")
        valid_mask = self._reference_valid_mask(indices, self.item_vfs.shape[0])
        safe_indices = torch.where(valid_mask, indices, torch.zeros_like(indices))

        var_name = tail[0]
        result = torch.zeros_like(indices, dtype=self.item_vfs.dtype, device=self.item_vfs.device)

        for idx_val in safe_indices[valid_mask].unique():
            idx_int = int(idx_val.item())
            profile_name = self.item_index_to_profile.get(idx_int)
            if profile_name is None:
                raise KeyError(f"No item profile registered for index {idx_int}")
            var_map = self.item_profile_map.get(profile_name, {})
            if var_name not in var_map:
                raise KeyError(f"Variable '{var_name}' not found in item profile '{profile_name}'")
            column = var_map[var_name]
            mask = valid_mask & (safe_indices == idx_int)
            result[mask] = self.item_vfs[idx_int, column]

        return result

    def _read_bar(self, tail: list[str], original_path: str) -> torch.Tensor:
        if len(tail) != 1:
            raise KeyError(f"Path '{original_path}' not found in execution context")
        return self._bar_tensor(tail[0], original_path)

    def _read_temporal(self, tail: list[str], original_path: str) -> torch.Tensor:
        if len(tail) != 1 or tail[0] not in self.temporal:
            raise KeyError(f"Path '{original_path}' not found in execution context")
        return self.temporal[tail[0]]

    def _bar_tensor(self, name: str, original_path: str) -> torch.Tensor:
        if name not in self.bars:
            raise KeyError(f"Path '{original_path}' not found in execution context")
        return self.bars[name]

    def _get_vfs_value(self, name: str, base_indices: torch.Tensor | None, scope: str, original_path: str) -> torch.Tensor:
        if name not in self.vfs:
            raise KeyError(f"Path '{original_path}' not found in execution context")
        value = self.vfs[name]
        if scope == "global" or not isinstance(value, torch.Tensor):
            return value
        if base_indices is None or value.dim() == 0:
            return value
        return self._gather_by_index(value, self._ensure_indices(base_indices, value.device))

    def _lookup_var_type(self, var_name: str) -> str | None:
        if self.vfs_types and var_name in self.vfs_types:
            return self.vfs_types[var_name]
        return None

    def _infer_batch_size(self) -> int | None:
        if self.num_agents is not None:
            return self.num_agents
        for tensor in self.bars.values():
            if isinstance(tensor, torch.Tensor) and tensor.dim() > 0:
                return tensor.shape[0]
        for tensor in self.vfs.values():
            if isinstance(tensor, torch.Tensor) and tensor.dim() > 0:
                return tensor.shape[0]
        return None

    def _default_indices(self) -> torch.Tensor | None:
        batch = self._infer_batch_size()
        if batch is None:
            return None
        return torch.arange(batch, device=self.device)

    def _ensure_indices(self, indices: torch.Tensor, device: torch.device) -> torch.Tensor:
        if not isinstance(indices, torch.Tensor):
            indices = torch.tensor(indices, device=device)
        indices = indices.to(device=device, dtype=torch.long)
        if indices.dim() == 0:
            indices = indices.unsqueeze(0)
        return indices

    def _gather_by_index(self, tensor: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
        if tensor.dim() == 0:
            return tensor
        expanded = indices.view(indices.shape[0], *([1] * (tensor.dim() - 1))).expand(-1, *tensor.shape[1:])
        return torch.take_along_dim(tensor, expanded, dim=0)

    def _reference_valid_mask(self, indices: torch.Tensor, limit: int | None) -> torch.Tensor:
        mask = indices >= 0
        if limit is not None:
            mask = mask & (indices < limit)
        return mask

    def _mask_reference_output(self, result: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        mask = valid_mask.to(device=result.device, dtype=torch.bool)
        if result.dim() == 0:
            expanded_result = result.expand(mask.shape)
            return torch.where(mask, expanded_result, torch.zeros_like(expanded_result))
        while mask.dim() < result.dim():
            mask = mask.unsqueeze(-1)
        return torch.where(mask, result, torch.zeros_like(result))

    def _validate_indices(self, indices: torch.Tensor, limit: int | None, label: str) -> None:
        if (indices < -1).any():
            raise ValueError(f"Invalid {label} index in execution context")
        if limit is None:
            return
        if (indices >= limit).any():
            raise ValueError(f"Invalid {label} index in execution context")
