"""The single seeding door for every RNG stream the runtime touches.

Seeding torch alone produces non-reproducible runs (verified by execution,
hamlet-834108b55a): the sequential replay buffer samples off Python's global
`random`, and the prioritized replay buffer off numpy's global RNG. All three
must be seeded together, through this one entry point. Nothing else in
`src/townlet/` may seed a global RNG.
"""

import random

import numpy as np
import torch

__all__ = ["seed_all"]

_NUMPY_SEED_MODULUS = 2**32


def seed_all(seed: int) -> None:
    """Seed torch (CPU and all CUDA devices), Python `random`, and numpy.

    Args:
        seed: Master seed for the run. Recorded in checkpoint provenance via
            the training config, so a run is reproducible from its checkpoint.
    """
    random.seed(seed)
    np.random.seed(seed % _NUMPY_SEED_MODULUS)
    torch.manual_seed(seed)
