"""One random stream per world for the VFS draws (S1: the batch is independent worlds).

A sampling call (``uniform``, ``normal_dist``) in a profile expression, an action write
or a transition rule draws once per row, each row from its own world's generator. World
``w``'s stream is seeded from the run seed (``torch.initial_seed()``, set by
``townlet.determinism.seed_all``), the episode and ``w`` alone, so its draws depend
neither on how many worlds share the batch nor on what any other world does, and a run
is reproducible per seed. The effects engine keeps a separate family of streams for its
pipelines (``townlet.effects.manager.EffectManager.world_rng``), so an effect's
``sample`` never shifts a world's expression draws.

Not checkpointed: a resumed run re-derives the streams from the seed and the episode
counter it restarts at, as the effects streams and torch's global stream do.
"""

from __future__ import annotations

import hashlib

import torch

__all__ = ["WorldRandomStreams"]


class WorldRandomStreams:
    """The per-world generators of one environment, re-derived every episode."""

    def __init__(self, label: str) -> None:
        self._label = label
        self._episode = 0
        self._device: torch.device | None = None
        self._generators: list[torch.Generator] = []

    @property
    def episode(self) -> int:
        return self._episode

    def reset(self) -> None:
        """Start a new episode: every world's stream is re-derived on its next draw."""
        self._episode += 1
        self._generators = []

    def generators(self, worlds: int, device: torch.device) -> tuple[torch.Generator, ...]:
        """World 0..``worlds``-1's generators on ``device``, seeding any not yet drawn from this episode."""
        device = torch.device(device)
        if self._device != device:
            self._device = device
            self._generators = []
        while len(self._generators) < worlds:
            world = len(self._generators)
            digest = hashlib.blake2b(f"{self._label}:{torch.initial_seed()}:{self._episode}:{world}".encode(), digest_size=8).digest()
            generator = torch.Generator(device=device)
            generator.manual_seed(int.from_bytes(digest, "little") & ((1 << 63) - 1))
            self._generators.append(generator)
        return tuple(self._generators[:worlds])
