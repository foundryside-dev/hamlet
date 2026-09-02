"""Compile check for the documentation reference pack (configs/reference/model_pack).

Nothing else in tests/, scripts/, or .github/ references this pack (confirmed by grep,
task-5-review.md Critical Finding #1) — that absence is exactly why a commit that made
its effects.yaml actually parse (instead of silently defaulting to an empty catalog
through a stray top-level key) went undetected as breaking the pack's self-consistency.
This test closes that gap: it pins the pack compiling end-to-end through the same
UniverseCompiler pipeline the pack's own documented `python -m townlet.universe validate`
command exercises (README.md), so a future edit that reintroduces an undeclared VFS
path — or any other Stage 1-8 regression — fails the suite instead of silently
regressing an example nobody runs.
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "configs" / "reference" / "model_pack"
PRIMARY_LEVEL = "L0_demo"


def test_reference_model_pack_compiles() -> None:
    """configs/reference/model_pack compiles end-to-end (all seven UAC stages)."""
    compiled = UniverseCompiler().compile(CONFIG_DIR, primary_level=PRIMARY_LEVEL, use_cache=False)
    level = compiled.get_level(PRIMARY_LEVEL)

    assert level.token_spec.total_dims > 0

    variables = {variable.id: variable for variable in level.vfs_variables}
    # ate_food (effects.yaml) writes target.vfs.is_digesting on spawn/despawn — the
    # variable this test exists to keep declared (task-5-review.md Critical Finding #1).
    assert variables["is_digesting"].scope == "agent"
    assert variables["is_digesting"].type == "bool"


def test_reference_model_pack_constructs_and_steps() -> None:
    """The reference pack's whole claim: it compiles AND runs (hamlet-5a87550adb)."""
    compiled = UniverseCompiler().compile(CONFIG_DIR, primary_level=PRIMARY_LEVEL, use_cache=False)
    env = VectorizedHamletEnv(universe=compiled, level_name=PRIMARY_LEVEL, num_agents=2, device=torch.device("cpu"))
    obs = env.reset()
    assert obs.shape == (2, env.token_spec.total_dims)
    obs, _rewards, _dones, _info = env.step(torch.full((2,), env.action_dim - 1, dtype=torch.long))
    assert torch.isfinite(obs).all()
