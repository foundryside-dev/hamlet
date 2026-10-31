"""Counter-based random draws for VFS expressions, action writes and transition rules.

Every value a sampling call (``uniform``, ``normal_dist``) produces is a pure function

    value = hash(seed, episode, tick, site, world, element)

computed vectorised in torch with integer mixing (the splitmix64 finalizer), turned into a
uniform float, and into a normal by Box-Muller. There is no generator state:

- **S1 independence.** World ``w``'s values depend on ``w`` and nothing about any other
  world, so a world's draws are the same whatever the batch size and whatever any other
  world does.
- **Stable sites.** ``site`` is the owner's identity (the expression variable's id, the
  transition rule's id and write index, the custom action's name and write index) plus the
  draw's ordinal among the owner's draws, in evaluation order of its AST. So moving a
  declaration to another file, reordering declarations, or adding an unrelated random
  mechanic re-rolls nothing else. A transition rule's own condition is one site shared by
  all its writes, so the rule fires for all of them or none.
- **Resume.** The only state is the run seed (captured once, when the environment is
  built) and the episode counter; both travel in the checkpoint (``state`` / ``restore``),
  so a resumed run draws exactly what the original run drew at the same episode and tick.
- **Shape.** A draw fills the full joined shape of its context: one value per world for a
  global expression, per agent row for an agent expression or an action write, per
  ``[world, affordance]`` row for a rule on an affordance target. An argument that already
  carries those axes shapes the draw; every element is its own world's.

The effects engine keeps separate generators for its pipelines
(``townlet.effects.manager.EffectManager.world_rng``), so an effect's ``sample`` never
shifts an expression draw.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import torch

__all__ = ["DrawInstant", "DrawStream", "VFSRandomness", "reference_uniform"]

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


def _instant_key(seed: int, episode: int, tick: int) -> int:
    return _mix64(_mix64(_mix64(seed & _MASK64) ^ episode) ^ (tick & _MASK64))


def reference_uniform(*, seed: int, episode: int, tick: int, site: str, ordinal: int, world: int, element: int) -> float:
    """The uniform value one element draws, in pure Python: the specification the torch kernel must match."""
    z = _mix64(_mix64(_site_key(_instant_key(seed, episode, tick), site, ordinal) ^ world) ^ element)
    return (z >> (64 - _UNIFORM_BITS)) / float(1 << _UNIFORM_BITS)


class VFSRandomness:
    """One environment's draw state: the run seed and the episode counter, nothing else."""

    def __init__(self, seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError(f"VFS random seed must be an int, got {type(seed).__name__}")
        self._seed = seed & _MASK64
        self._episode = 0

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def episode(self) -> int:
        return self._episode

    def reset(self) -> None:
        """Start a new episode."""
        self._episode += 1

    def state(self) -> dict[str, int]:
        """What a checkpoint carries to reproduce every later draw."""
        return {"seed": self._seed, "episode": self._episode}

    def restore(self, state: dict[str, int]) -> None:
        """Adopt a checkpoint's seed and episode counter (the next ``reset`` starts the episode after it)."""
        if set(state) != {"seed", "episode"}:
            raise ValueError(f"VFS random state must carry exactly 'seed' and 'episode', got {sorted(state)}")
        seed, episode = state["seed"], state["episode"]
        for name, value in (("seed", seed), ("episode", episode)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"VFS random state '{name}' must be a non-negative int, got {value!r}")
        self._seed = seed & _MASK64
        self._episode = episode

    def instant(self, *, tick: int, worlds: int, device: torch.device) -> DrawInstant:
        """The draws of one instant of this episode, for ``worlds`` worlds."""
        return DrawInstant(key=_instant_key(self._seed, self._episode, tick), worlds=worlds, device=torch.device(device))


@dataclass(frozen=True)
class DrawInstant:
    """One instant's draw key; ``stream`` hands each owner its own sites."""

    key: int
    worlds: int
    device: torch.device

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

    @property
    def worlds(self) -> int:
        return self._instant.worlds

    def _next_site_key(self) -> int:
        ordinal = self._ordinal
        self._ordinal += 1
        if self._shared_site is not None and ordinal < self._shared_draws:
            return _site_key(self._instant.key, self._shared_site, ordinal)
        return _site_key(self._instant.key, self._site, ordinal - (self._shared_draws if self._shared_site is not None else 0))

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

    def _bits(self, site_key: int, shape: tuple[int, ...], lanes: int, lane: int) -> torch.Tensor:
        device = self._instant.device
        elements = math.prod(shape[1:])
        world = torch.arange(shape[0], device=device, dtype=torch.int64).unsqueeze(1)
        element = torch.arange(elements, device=device, dtype=torch.int64).unsqueeze(0) * lanes + lane
        z = _mix64_tensor(_mix64_tensor(torch.full((), _signed(site_key), device=device, dtype=torch.int64) ^ world) ^ element)
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
