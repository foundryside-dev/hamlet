"""DemoRunner seeds the run from training config (hamlet-834108b55a).

The seed is declared in training.yaml (required field), the runner pushes it
through the single seeding door at construction — before anything random is
built — and the checkpoint carries it via the persisted training config, so a
run is reproducible from its own artifact.
"""

import random
from pathlib import Path

import numpy as np
import torch

from townlet.demo.runner import DemoRunner
from townlet.determinism import seed_all

CONFIG_DIR = Path("configs/test/model_config")
LEVEL = "L0_test"
PACK_SEED = 42  # declared in configs/test/model_config/levels/L0_test/training.yaml


def _make_runner(tmp_path: Path) -> DemoRunner:
    return DemoRunner(
        config_dir=CONFIG_DIR,
        db_path=tmp_path / "test.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=1,
        level_name=LEVEL,
    )


def test_runner_init_seeds_every_stream_from_training_config(tmp_path: Path) -> None:
    """After construction, all three RNG streams sit in the seed_all(seed) state."""
    # Deliberately scramble every stream so a runner that fails to seed cannot pass.
    random.seed(999)
    np.random.seed(999)
    torch.manual_seed(999)

    runner = _make_runner(tmp_path)
    try:
        observed = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    finally:
        runner._cleanup()

    seed_all(PACK_SEED)
    expected = (random.random(), float(np.random.rand()), torch.rand(4).tolist())
    assert observed == expected


def test_checkpoint_carries_the_seed(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    try:
        runner.save_checkpoint()
        checkpoint_path = next((tmp_path / "checkpoints").glob("checkpoint_ep*.pt"))
        checkpoint = torch.load(checkpoint_path, weights_only=True)
    finally:
        runner._cleanup()

    assert checkpoint["training_config"]["seed"] == PACK_SEED
