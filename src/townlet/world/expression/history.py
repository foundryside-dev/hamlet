"""Temporal history for expression evaluation: one ring buffer per history key.

A history key names the value a temporal operator reads the past of: ``bar.<meter>``
for a meter, ``vfs.<id>`` for a registry variable (the engine clock is ``vfs.tick``).
The compiled history spec maps each key to its ring depth, the deepest ``lag`` any
operator needs.

The contract, which every temporal operator is defined through:

- **One sample per instant.** The engine evaluates every expression once per instant
  (reset's instant 0, then each step). After all of them evaluate, it ``commit``\\ s the
  committed value of every key; ``lag(x, n)`` at instant ``t`` is that value at
  instant ``t - n``. A ``lag`` read therefore never reads the in-evaluation value, which
  is why it is not a dependency edge and why ``x: f(lag(x, 1))`` is well defined.
- **The pre-history is the episode-start value.** At the first instant of an episode
  ``seed`` fills every slot of a key's ring with the value the key held before that
  instant's evaluation: a meter's initial value, a variable's declared initial value
  (tick and episode lifetime) or carried value (persistent lifetime). So ``lag(x, n)``
  before ``n`` instants exist returns that value — never an undocumented zero.
- **History is episode-scoped for every lifetime.** ``reset`` drops every ring; the
  next ``seed`` refills it. For a persistent variable the seed is its carried value, so
  ``lag(p, 1)`` at an episode's first instant is exactly the previous episode's last
  value, and every deeper lag collapses to it until the ring refills.
- **A dead world's history does not advance.** ``commit`` writes only the rows its
  ``live`` mask selects; a done world's ring, cursor and moving averages stay frozen.

Rows are worlds (S1: one agent per world, so agent and global keys are both ``[N]``).
"""

from __future__ import annotations

from collections.abc import Mapping

import torch

from townlet.world.expression.ast_nodes import ASTNode, PathAccess, Variable

MAX_WINDOW_SIZE = 256


def history_key(node: ASTNode) -> str | None:
    """The history key a temporal operator's first argument names, or None if it names no value."""
    if isinstance(node, PathAccess):
        return ".".join(node.segments)
    if isinstance(node, Variable):
        return f"vfs.{node.name}"
    return None


def history_value(key: str, bars: Mapping[str, torch.Tensor], vfs: Mapping[str, torch.Tensor]) -> torch.Tensor:
    """The current value of one history key in the engine's bar and registry state."""
    root, _, name = key.partition(".")
    sources = {"bar": bars, "vfs": vfs}
    if root not in sources or name not in sources[root]:
        raise KeyError(f"Engine defect: history key '{key}' names no meter or registry variable in the evaluation state")
    return sources[root][name]


class TemporalHistory:
    """Ring buffers (``[N, depth]`` per key) plus the running state of each ``ema``."""

    def __init__(self, history_spec: Mapping[str, int], device: torch.device) -> None:
        for key, depth in history_spec.items():
            if not 1 <= depth <= MAX_WINDOW_SIZE:
                raise ValueError(f"Engine defect: history depth for '{key}' is {depth}; the compiler admits 1..{MAX_WINDOW_SIZE}")
        self.history_spec = dict(history_spec)
        self.device = device
        self._buffers: dict[str, torch.Tensor] = {}
        self._cursor: dict[str, torch.Tensor] = {}
        self._ema: dict[tuple[str, float], torch.Tensor] = {}
        self._commits = 0

    @property
    def seeded(self) -> bool:
        return bool(self._buffers) or not self.history_spec

    def seed(self, bars: Mapping[str, torch.Tensor], vfs: Mapping[str, torch.Tensor]) -> None:
        """Fill every ring with each key's pre-evaluation value (the episode-start value)."""
        if self._buffers:
            raise RuntimeError("Engine defect: history seeded twice in one episode; reset() starts an episode")
        for key, depth in self.history_spec.items():
            value = history_value(key, bars, vfs).to(self.device)
            if value.dim() != 1:
                raise RuntimeError(f"Engine defect: history key '{key}' has shape {tuple(value.shape)}; rows must be [N]")
            self._buffers[key] = value.unsqueeze(1).expand(value.shape[0], depth).clone()
            self._cursor[key] = torch.zeros(value.shape[0], dtype=torch.long, device=self.device)

    def _ring(self, key: str) -> tuple[torch.Tensor, torch.Tensor]:
        if key not in self._buffers:
            if key not in self.history_spec:
                raise KeyError(f"Engine defect: history key '{key}' is not in the compiled history spec")
            raise RuntimeError(f"Engine defect: history key '{key}' read before the episode's history was seeded")
        return self._buffers[key], self._cursor[key]

    def lag(self, key: str, n: int) -> torch.Tensor:
        """The committed value of ``key`` ``n`` instants ago (``1 <= n <= depth``)."""
        buffer, cursor = self._ring(key)
        depth = buffer.shape[1]
        if not 1 <= n <= depth:
            raise RuntimeError(f"Engine defect: lag({key}, {n}) outside the compiled depth 1..{depth}")
        slot = (cursor - n) % depth
        return buffer.gather(1, slot.unsqueeze(1)).squeeze(1)

    def ema(self, key: str, alpha: float, current: torch.Tensor) -> torch.Tensor:
        """``alpha * current + (1 - alpha) * previous``; the previous before the first instant is the seed."""
        state = self._ema.get((key, alpha))
        if state is None:
            if self._commits:
                raise RuntimeError(
                    f"Engine defect: ema({key}, {alpha}) first evaluated after the episode's first instant; "
                    "every expression evaluates at every instant"
                )
            state = self.lag(key, 1).to(torch.float32)
            self._ema[(key, alpha)] = state
        return alpha * current.to(torch.float32) + (1.0 - alpha) * state

    def commit(self, bars: Mapping[str, torch.Tensor], vfs: Mapping[str, torch.Tensor], live: torch.Tensor) -> None:
        """Record this instant's committed value of every key, in the live rows only."""
        live = live.to(device=self.device, dtype=torch.bool)
        for key in self.history_spec:
            buffer, cursor = self._ring(key)
            value = history_value(key, bars, vfs).to(device=self.device, dtype=buffer.dtype)
            if value.shape != live.shape:
                raise RuntimeError(f"Engine defect: history key '{key}' has shape {tuple(value.shape)}, live mask {tuple(live.shape)}")
            slot = cursor.unsqueeze(1)
            buffer.scatter_(1, slot, torch.where(live, value, buffer.gather(1, slot).squeeze(1)).unsqueeze(1))
            self._cursor[key] = (cursor + live.to(torch.long)) % buffer.shape[1]
        for (key, alpha), state in self._ema.items():
            current = history_value(key, bars, vfs).to(device=self.device, dtype=torch.float32)
            self._ema[(key, alpha)] = torch.where(live, alpha * current + (1.0 - alpha) * state, state)
        self._commits += 1

    def reset(self) -> None:
        """Drop every ring and moving average; the next instant seeds a new episode."""
        self._buffers.clear()
        self._cursor.clear()
        self._ema.clear()
        self._commits = 0

    def to(self, device: torch.device) -> None:
        """Move all history to a new device, preserving it."""
        self.device = device
        self._buffers = {key: value.to(device) for key, value in self._buffers.items()}
        self._cursor = {key: value.to(device) for key, value in self._cursor.items()}
        self._ema = {key: value.to(device) for key, value in self._ema.items()}
