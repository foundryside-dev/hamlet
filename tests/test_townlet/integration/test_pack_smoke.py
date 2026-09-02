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
from townlet.universe.dto.token_spec import TokenSpec

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


def _assert_presence_lanes(spec: TokenSpec, obs: torch.Tensor) -> None:
    for _type, _slot, start, _end in spec.row_layout():
        presence = obs[:, start]
        assert torch.all((presence == 0.0) | (presence == 1.0)), f"presence lane at {start} is not 0/1"


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

    # Non-vacuity guard: a pack whose compiled artifact has no rows, or whose
    # reset masks leave an agent with zero valid actions, would make every
    # assertion below vacuously true. Both are defects worth catching here,
    # before the step loop can paper over them.
    assert spec.row_layout(), "compiled artifact has no observation rows"
    reset_masks = env.get_action_masks()
    if reset_masks.dtype != torch.bool:
        reset_masks = reset_masks > 0.5
    assert reset_masks.any(dim=-1).all(), "every agent must start with at least one valid action"

    _assert_presence_lanes(spec, obs)

    for _ in range(STEPS):
        masks = env.get_action_masks()
        if masks.dtype != torch.bool:
            masks = masks > 0.5
        any_valid = masks.any(dim=-1)
        if not any_valid.all():
            # A mask row goes all-False only once the env has already marked
            # that agent done — action_mask_builder.py zeroes a done agent's
            # entire row. _execute_actions does not itself gate on `dones`,
            # so a live agent with no valid action would be a real defect,
            # not something to paper over by picking an arbitrary action.
            assert torch.all(env.dones[~any_valid]), "agent with no valid action must already be done"
        # Select the LAST valid action rather than the first: WAIT sits at
        # [-1] under the canonical action ordering, so this prefers WAIT
        # (a no-op) both as the natural choice among ties and as the safe
        # fallback on an all-False row, instead of argmax's default of index
        # 0 — a movement action that would otherwise run physics for an
        # already-terminated agent.
        actions = masks.shape[1] - 1 - masks.flip(-1).float().argmax(dim=-1)
        obs, rewards, _dones, _info = env.step(actions)
        assert torch.isfinite(obs).all() and torch.isfinite(rewards).all()
        _assert_presence_lanes(spec, obs)
