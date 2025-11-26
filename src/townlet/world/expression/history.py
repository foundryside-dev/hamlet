"""Temporal history buffers for expression evaluation.

Manages per-key ring buffers, warm-length tracking, and EMA/edge caches
for temporal operators (lag, delta, moving_average, ema, rate_of_change,
rising_edge, falling_edge). Keys are string identifiers such as
"bar.energy" or "vfs.energy_deficit"; window sizes are defined per-key
via a history spec produced at compile time.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

MAX_WINDOW_SIZE = 256


@dataclass
class TemporalHistory:
    """Ring buffers and caches for temporal operators."""

    history_spec: dict[str, int]
    device: torch.device

    def __post_init__(self) -> None:
        self._buffers: dict[str, torch.Tensor] = {}
        self._write_index: dict[str, torch.Tensor] = {}
        self._warm_length: dict[str, torch.Tensor] = {}
        self._ema_state: dict[str, torch.Tensor] = {}
        self._edge_cache: dict[str, torch.Tensor] = {}

    def _ensure_allocated(self, key: str, value: torch.Tensor) -> None:
        window = self.history_spec.get(key)
        if window is None:
            return
        if window <= 0:
            raise ValueError(f"History window must be > 0 for key '{key}', got {window}")
        if window > MAX_WINDOW_SIZE:
            raise ValueError(f"History window for '{key}' exceeds MAX_WINDOW_SIZE={MAX_WINDOW_SIZE}")

        if key in self._buffers:
            return

        batch = value.shape[0]
        buffer_shape = (batch, window, *value.shape[1:])
        self._buffers[key] = torch.zeros(buffer_shape, device=self.device, dtype=value.dtype)
        self._write_index[key] = torch.zeros((batch,), device=self.device, dtype=torch.long)
        self._warm_length[key] = torch.zeros((batch,), device=self.device, dtype=torch.long)
        if value.dtype == torch.bool:
            self._edge_cache[key] = torch.zeros(value.shape, device=self.device, dtype=torch.bool)

    def push(self, key: str, value: torch.Tensor) -> None:
        """Push current value into ring buffer (once per timestep)."""

        window = self.history_spec.get(key)
        if window is None:
            return
        self._ensure_allocated(key, value)
        buffer = self._buffers[key]
        idx = self._write_index[key]
        warm = self._warm_length[key]

        batch_indices = torch.arange(value.shape[0], device=self.device)
        target = idx % window
        buffer[batch_indices, target, ...] = value

        self._write_index[key] = (idx + 1) % window
        self._warm_length[key] = torch.clamp(warm + 1, max=window)

        if value.dtype == torch.bool:
            self._edge_cache[key] = value

    def lag(self, key: str, n: int, fallback: torch.Tensor) -> torch.Tensor:
        window = self.history_spec.get(key)
        if window is None:
            return fallback
        if n < 0:
            raise ValueError(f"lag requires non-negative n, got {n}")
        if key not in self._buffers:
            return torch.zeros_like(fallback)

        buffer = self._buffers[key]
        idx = self._write_index[key]
        warm = self._warm_length[key]
        batch = buffer.shape[0]
        batch_indices = torch.arange(batch, device=self.device)

        target = (idx - n) % window
        values = buffer[batch_indices, target, ...]

        valid = warm >= n
        while valid.dim() < values.dim():
            valid = valid.unsqueeze(-1)
        return torch.where(valid, values, torch.zeros_like(values))

    def moving_average(self, key: str, window: int, current: torch.Tensor) -> torch.Tensor:
        if window <= 0:
            raise ValueError("moving_average window must be > 0")
        spec_window = self.history_spec.get(key)
        if spec_window is None:
            return current
        if window > spec_window:
            raise ValueError(f"moving_average window {window} exceeds spec window {spec_window} for key '{key}'")

        self._ensure_allocated(key, current)
        buffer = self._buffers[key]
        idx = self._write_index[key]
        warm = self._warm_length[key]
        batch = buffer.shape[0]

        # Include current sample + up to window-1 historical samples
        past_window = min(max(window - 1, 0), spec_window)
        if past_window == 0:
            return current

        batch_indices = torch.arange(batch, device=self.device)
        offsets = torch.arange(past_window, device=self.device)
        target = (idx.unsqueeze(1) - 1 - offsets.unsqueeze(0)) % spec_window
        selected = buffer[batch_indices.unsqueeze(1), target, ...]

        warm_past = torch.clamp(warm, max=past_window)
        mask = offsets.unsqueeze(0) < warm_past.unsqueeze(1)
        while mask.dim() < selected.dim():
            mask = mask.unsqueeze(-1)
        masked_past = torch.where(mask, selected, torch.zeros_like(selected))

        sum_values = current + masked_past.sum(dim=1)
        warm_total = torch.clamp(warm_past + 1, min=1).to(buffer.dtype)
        while warm_total.dim() < sum_values.dim():
            warm_total = warm_total.unsqueeze(-1)
        return sum_values / warm_total

    def ema(self, key: str, alpha: float, current: torch.Tensor) -> torch.Tensor:
        if alpha <= 0 or alpha > 1:
            raise ValueError(f"ema alpha must be in (0,1], got {alpha}")

        self._ensure_allocated(key, current)
        state = self._ema_state.get(key)
        if state is None:
            state = current
        else:
            state = alpha * current + (1 - alpha) * state

        self._ema_state[key] = state
        return state

    def rate_of_change(self, key: str, window: int, current: torch.Tensor) -> torch.Tensor:
        if window <= 0:
            raise ValueError("rate_of_change window must be > 0")
        lagged = self.lag(key, window, fallback=torch.zeros_like(current))
        return (current.to(dtype=torch.float32) - lagged.to(dtype=torch.float32)) / float(window)

    def edge(self, key: str, current: torch.Tensor, rising: bool) -> torch.Tensor:
        if key not in self._edge_cache:
            # Ensure allocation for bool tensors
            self._ensure_allocated(key, current)
            if key not in self._edge_cache:
                self._edge_cache[key] = torch.zeros_like(current, dtype=torch.bool)

        prev = self._edge_cache[key]
        if rising:
            result = torch.logical_and(torch.logical_not(prev), current)
        else:
            result = torch.logical_and(prev, torch.logical_not(current))
        return result

    def reset(self) -> None:
        self._buffers.clear()
        self._write_index.clear()
        self._warm_length.clear()
        self._ema_state.clear()
        self._edge_cache.clear()

    def to(self, device: torch.device) -> None:
        """Move all buffers to a new device while preserving history."""

        self.device = device
        for key, buf in list(self._buffers.items()):
            self._buffers[key] = buf.to(device)
        for key, idx in list(self._write_index.items()):
            self._write_index[key] = idx.to(device)
        for key, warm in list(self._warm_length.items()):
            self._warm_length[key] = warm.to(device)
        for key, ema in list(self._ema_state.items()):
            self._ema_state[key] = ema.to(device)
        for key, edge in list(self._edge_cache.items()):
            self._edge_cache[key] = edge.to(device)

    def has_history(self, key: str, n: int) -> torch.Tensor | None:
        warm = self._warm_length.get(key)
        if warm is None:
            return None
        return warm >= n
