"""Identity-keyed VFS draws for expressions, action writes and transition rules.

ENV supplies the exact training seed, world IDs and per-world episode sequences.
This module owns no episode lifecycle or generator cursor. A world's draws depend
only on that identity, tick, stable site, call ordinal and within-world element.
Changing lane order, batch size or another world's context cannot change its keys.

The versioned simulator/VFS domain is separate from learner/provider RNG. This is
a direct draw-domain guarantee, not a claim about ambient simulator spawn/layout
randomness. Uniform and Box-Muller normal draws retain the full joined context
shape, float32 outputs and device-local vectorized integer mixing. Shared rule
condition prefixes retain identical draws across that rule's writes.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import torch

__all__ = ["DrawInstant", "DrawStream", "VFSRandomness", "VFSWorldContext", "reference_uniform"]

_DOMAIN = "townlet.simulator.vfs.world-draw.v1"
_STATE_SCHEMA = "vfs-world-random-v1"

_MASK64 = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15
_MIX1 = 0xBF58476D1CE4E5B9
_MIX2 = 0x94D049BB133111EB
_UNIFORM_BITS = 24
"""A float32 has a 24-bit significand: ``k / 2**24`` for ``k < 2**24`` is exact and below 1."""


def _mix64(value: int) -> int:
    """The splitmix64 step on an unsigned 64-bit Python int."""
    z = (value + _GOLDEN) & _MASK64
    z = ((z ^ (z >> 30)) * _MIX1) & _MASK64
    z = ((z ^ (z >> 27)) * _MIX2) & _MASK64
    return z ^ (z >> 31)


def _signed(value: int) -> int:
    """An unsigned 64-bit value as the int64 with the same bits."""
    value &= _MASK64
    return value - (1 << 64) if value >= 1 << 63 else value


def _shr(tensor: torch.Tensor, bits: int) -> torch.Tensor:
    """Logical right shift of int64 bits (torch shifts int64 arithmetically)."""
    return (tensor >> bits) & ((1 << (64 - bits)) - 1)


def _mix64_tensor(tensor: torch.Tensor) -> torch.Tensor:
    """``_mix64`` elementwise on int64 tensors; integer multiplication wraps modulo 2**64."""
    z = tensor + _signed(_GOLDEN)
    z = (z ^ _shr(z, 30)) * _signed(_MIX1)
    z = (z ^ _shr(z, 27)) * _signed(_MIX2)
    return z ^ _shr(z, 31)


def _label_hash(label: str) -> int:
    return int.from_bytes(hashlib.blake2b(label.encode(), digest_size=8).digest(), "little")


def _site_key(instant_key: int, label: str, ordinal: int) -> int:
    return _mix64(_mix64(instant_key ^ _label_hash(label)) ^ ordinal)


def _nonnegative_integer(value: Any, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"VFS {name} requires an exact non-negative integer")


@dataclass(frozen=True, kw_only=True)
class VFSWorldContext:
    """Owned data projection; only ENV can authorize its use for a live episode."""

    training_seed: int
    world_ids: tuple[str, ...]
    world_episode_seqs: tuple[int, ...]

    def __post_init__(self) -> None:
        _nonnegative_integer(self.training_seed, "training seed")
        if type(self.world_ids) is not tuple or not self.world_ids:
            raise ValueError("VFS world IDs require a nonempty immutable tuple")
        if any(type(value) is not str or not value for value in self.world_ids) or len(set(self.world_ids)) != len(self.world_ids):
            raise ValueError("VFS world IDs require unique exact nonempty strings")
        if type(self.world_episode_seqs) is not tuple or len(self.world_episode_seqs) != len(self.world_ids):
            raise ValueError("VFS sequences require one immutable entry per world ID")
        for sequence in self.world_episode_seqs:
            _nonnegative_integer(sequence, "world episode sequence")


def _world_key(seed: int, world_id: str, sequence: int) -> int:
    encoded = json.dumps([_DOMAIN, seed, world_id, sequence], ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(encoded, digest_size=8).digest(), "little")


def reference_uniform(
    *, training_seed: int, world_id: str, world_episode_seq: int, tick: int, site: str, ordinal: int, element: int
) -> float:
    """One uniform element under the versioned world-identity domain, in pure Python."""
    VFSWorldContext(training_seed=training_seed, world_ids=(world_id,), world_episode_seqs=(world_episode_seq,))
    for name, value in (("tick", tick), ("ordinal", ordinal), ("element", element)):
        _nonnegative_integer(value, name)
    instant_key = _mix64(_world_key(training_seed, world_id, world_episode_seq) ^ tick)
    z = _mix64(_site_key(instant_key, site, ordinal) ^ element)
    return (z >> (64 - _UNIFORM_BITS)) / float(1 << _UNIFORM_BITS)


@dataclass(frozen=True, kw_only=True)
class VFSRandomness:
    """Immutable draw producer for an ENV-projected context, with no reset authority."""

    context: VFSWorldContext
    _world_keys: tuple[int, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.context, VFSWorldContext):
            raise ValueError("VFS randomness requires an explicit world context")
        object.__setattr__(
            self,
            "_world_keys",
            tuple(
                _world_key(self.context.training_seed, world_id, sequence)
                for world_id, sequence in zip(self.context.world_ids, self.context.world_episode_seqs, strict=True)
            ),
        )

    def state(self) -> dict[str, Any]:
        """Portable owned identity data; no live receipt, generator or cursor is serialized."""
        return {
            "schema": _STATE_SCHEMA,
            "domain": _DOMAIN,
            "training_seed": self.context.training_seed,
            "world_ids": list(self.context.world_ids),
            "world_episode_seqs": list(self.context.world_episode_seqs),
        }

    @staticmethod
    def validate_state(state: Mapping[str, Any], *, expected: VFSWorldContext) -> VFSWorldContext:
        """Validate every field and exact producer lane binding before any installation."""
        keys = {"schema", "domain", "training_seed", "world_ids", "world_episode_seqs"}
        if not isinstance(state, Mapping) or set(state) != keys or state["schema"] != _STATE_SCHEMA or state["domain"] != _DOMAIN:
            raise ValueError("VFS native state requires the exact current schema and domain")
        if type(state["world_ids"]) is not list or type(state["world_episode_seqs"]) is not list:
            raise ValueError("VFS native identities require serialized lists")
        context = VFSWorldContext(
            training_seed=state["training_seed"], world_ids=tuple(state["world_ids"]), world_episode_seqs=tuple(state["world_episode_seqs"])
        )
        if not isinstance(expected, VFSWorldContext) or context != expected:
            raise ValueError("VFS native context contradicts the authoritative world context")
        return context

    def instant(self, *, tick: int, device: torch.device) -> DrawInstant:
        """One tick projected independently through every world's exact episode identity."""
        _nonnegative_integer(tick, "tick")
        return DrawInstant(world_keys=tuple(_mix64(key ^ tick) for key in self._world_keys), device=torch.device(device))


@dataclass(frozen=True)
class DrawInstant:
    """One instant's draw key; ``stream`` hands each owner its own sites."""

    world_keys: tuple[int, ...]
    device: torch.device

    @property
    def worlds(self) -> int:
        return len(self.world_keys)

    def stream(self, site: str, shape: tuple[int, ...]) -> DrawStream:
        """The draws of one owner whose context has the full joined ``shape`` (worlds leading)."""
        return DrawStream(self, site=site, shape=shape, shared_site=None, shared_draws=0)

    def stream_with_shared_prefix(self, site: str, shape: tuple[int, ...], *, shared_site: str, shared_draws: int) -> DrawStream:
        """Like ``stream``, but the first ``shared_draws`` draws belong to ``shared_site``.

        A transition rule's condition is combined into each write's condition and evaluated
        first, so the rule condition's draws are the leading ones: keyed on the rule, they
        are the same for every write of the rule.
        """
        return DrawStream(self, site=site, shape=shape, shared_site=shared_site, shared_draws=shared_draws)


class DrawStream:
    """The draws of one owner at one instant, numbered in evaluation order."""

    def __init__(self, instant: DrawInstant, *, site: str, shape: tuple[int, ...], shared_site: str | None, shared_draws: int) -> None:
        if not shape or int(shape[0]) != instant.worlds:
            raise RuntimeError(f"Engine defect: draw site '{site}' has context shape {shape}, not led by {instant.worlds} worlds")
        self._instant = instant
        self._site = site
        self._shape = tuple(int(axis) for axis in shape)
        self._shared_site = shared_site
        self._shared_draws = shared_draws
        self._ordinal = 0
        self._world_keys = torch.tensor([_signed(key) for key in instant.world_keys], device=instant.device, dtype=torch.int64)

    @property
    def worlds(self) -> int:
        return self._instant.worlds

    def _next_site_key(self) -> torch.Tensor:
        ordinal = self._ordinal
        self._ordinal += 1
        if self._shared_site is not None and ordinal < self._shared_draws:
            site = self._shared_site
        else:
            site = self._site
            ordinal -= self._shared_draws if self._shared_site is not None else 0
        return _mix64_tensor(_mix64_tensor(self._world_keys ^ _signed(_label_hash(site))) ^ _signed(ordinal))

    def _shape_like(self, name: str, like: torch.Tensor) -> tuple[int, ...]:
        if like.dim() == 0:
            return self._shape
        try:
            shape = tuple(torch.broadcast_shapes(tuple(like.shape), self._shape))
        except RuntimeError:
            shape = ()
        if not shape or shape[0] != self.worlds:
            raise RuntimeError(
                f"Engine defect: function '{name}' draws in a context of shape {self._shape} but its argument has "
                f"shape {tuple(like.shape)}; the compiled shape proof admits no such argument"
            )
        return shape

    def _bits(self, site_key: torch.Tensor, shape: tuple[int, ...], lanes: int, lane: int) -> torch.Tensor:
        device = self._instant.device
        elements = math.prod(shape[1:])
        element = torch.arange(elements, device=device, dtype=torch.int64).unsqueeze(0) * lanes + lane
        z = _mix64_tensor(site_key.unsqueeze(1) ^ element)
        return _shr(z, 64 - _UNIFORM_BITS)

    def uniform(self, name: str, like: torch.Tensor) -> torch.Tensor:
        """``[0, 1)`` float32 draws of the context's shape (or ``like``'s, where it carries the axes)."""
        shape = self._shape_like(name, like)
        bits = self._bits(self._next_site_key(), shape, 1, 0)
        return (bits.to(torch.float64) / float(1 << _UNIFORM_BITS)).to(torch.float32).reshape(shape)

    def normal(self, name: str, like: torch.Tensor) -> torch.Tensor:
        """Standard normal float32 draws by Box-Muller over two uniform lanes per element."""
        shape = self._shape_like(name, like)
        key = self._next_site_key()
        scale = float(1 << _UNIFORM_BITS)
        u1 = 1.0 - self._bits(key, shape, 2, 0).to(torch.float64) / scale  # (0, 1]: log is finite
        u2 = self._bits(key, shape, 2, 1).to(torch.float64) / scale
        values = torch.sqrt(-2.0 * torch.log(u1)) * torch.cos(2.0 * math.pi * u2)
        return values.to(torch.float32).reshape(shape)
