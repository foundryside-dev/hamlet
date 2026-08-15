"""WS-7 determinism: the single seeding door (hamlet-834108b55a).

The runtime touches three RNG streams — torch (network init, sampling, randperm),
Python `random` (sequential replay buffer), and numpy (prioritized replay buffer).
Seeding only torch was verified by execution (2026-08-11) to produce divergent runs;
seeding all three produces bit-identical 40-step traces. `seed_all` is the one door
that seeds every stream; nothing else in the codebase may seed globals ad hoc.
"""

import random

import numpy as np
import torch

from townlet.determinism import seed_all


def test_seed_all_reproduces_every_stream():
    seed_all(42)
    first = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    seed_all(42)
    second = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    assert first == second


def test_seed_all_different_seeds_diverge():
    seed_all(42)
    a = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    seed_all(43)
    b = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    assert a != b
