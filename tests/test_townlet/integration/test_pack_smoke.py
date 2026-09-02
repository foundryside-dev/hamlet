"""Every surviving pack compiles, constructs, resets and steps — discovered from configs/, not listed.

A pack that lands in configs/ is exercised the day it lands; a deleted one stops silently.
The three negative VFS fixtures are excluded by name because refusing is their contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

CONFIGS = Path(__file__).parents[3] / "configs"
NEGATIVE_FIXTURES = {
    CONFIGS / "test" / "vfs_circular_dependency",
    CONFIGS / "test" / "vfs_type_mismatch",
    CONFIGS / "test" / "vfs_undefined_var",
}
STEPS = 4
NUM_AGENTS = 2


def _cases() -> list[tuple[Path, str]]:
    cases = []
    for stratum in sorted(CONFIGS.rglob("stratum.yaml")):
        pack = stratum.parent
        if pack in NEGATIVE_FIXTURES or not (pack / "levels").is_dir():
            continue
        for level in sorted(p.name for p in (pack / "levels").iterdir() if p.is_dir()):
            cases.append((pack, level))
    assert cases, "no packs discovered under configs/"
    return cases


@pytest.mark.parametrize(("pack", "level"), _cases(), ids=lambda v: v.name if isinstance(v, Path) else v)
def test_pack_compiles_constructs_resets_and_steps(pack: Path, level: str) -> None:
    universe = UniverseCompiler().compile(pack, primary_level=level, use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name=level, num_agents=NUM_AGENTS, device=torch.device("cpu"))
    spec = env.token_spec
    obs = env.reset()
    assert obs.shape == (NUM_AGENTS, spec.total_dims)
    assert (
        spec.census["agent"] == 0
    ), "agent tokens have no declaration surface (PDR-0143); a surface that makes them live must add an exercise"
    for _ in range(STEPS):
        masks = env.get_action_masks()
        if masks.dtype != torch.bool:
            masks = masks > 0.5
        actions = masks.float().argmax(dim=-1)  # first valid action per agent
        obs, rewards, dones, _info = env.step(actions)
        assert torch.isfinite(obs).all() and torch.isfinite(rewards).all()
    for _type, _slot, start, _end in spec.row_layout():
        presence = obs[:, start]
        assert torch.all((presence == 0.0) | (presence == 1.0)), f"presence lane at {start} is not 0/1"
