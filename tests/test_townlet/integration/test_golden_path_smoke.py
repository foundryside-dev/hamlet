"""Golden-path smoke test for the post-dormancy rescue.

Named regression baseline for the rescue plan
(`docs/plans/2026-05-14-hamlet-rescue-recovery-plan.md`, Tranche 1).

Asserts the minimum viable Hamlet pipeline still works:
`configs/default_curriculum` → `UniverseCompiler.compile(...,
primary_level="L0_0_minimal", use_cache=False)` →
`VectorizedHamletEnv.from_universe(num_agents=2, device="cpu")` → `reset()` →
five deterministic WAIT steps.

Each test recompiles to avoid sharing universe state between functions and
to keep the failure isolation clean (see filigree hamlet-c1260e52ab for an
example of why shared state across this suite has historically been
hazardous).
"""

from __future__ import annotations

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

CONFIG_DIR = Path("configs/default_curriculum")
LEVEL_NAME = "L0_0_minimal"
NUM_AGENTS = 2
NUM_STEPS = 5


def _compile_rescue_universe():
    return UniverseCompiler().compile(
        CONFIG_DIR,
        primary_level=LEVEL_NAME,
        use_cache=False,
    )


def _wait_action_id(env: VectorizedHamletEnv) -> int:
    return env.action_space.get_action_by_name("WAIT").id


def test_compile_l0_0_minimal_no_cache():
    """Stage A: the rescue config compiles with cache disabled."""
    universe = _compile_rescue_universe()

    assert universe is not None
    assert universe.all_levels is not None
    assert LEVEL_NAME in universe.all_levels


def test_env_instantiate_and_reset():
    """Stage B: env instantiates from the compiled universe and reset returns
    a [num_agents, obs_dim] tensor on CPU."""
    universe = _compile_rescue_universe()
    env = VectorizedHamletEnv.from_universe(
        universe,
        level_name=LEVEL_NAME,
        num_agents=NUM_AGENTS,
        device="cpu",
    )

    obs = env.reset()

    assert obs.shape[0] == NUM_AGENTS
    assert obs.shape[1] > 0
    assert obs.device.type == "cpu"
    assert torch.isfinite(obs).all()


def test_env_step_deterministic_sequence():
    """Stage C: stepping five WAIT actions produces well-shaped, finite
    rewards/dones and does not crash. WAIT is chosen so the test does not
    depend on substrate-specific movement validity."""
    universe = _compile_rescue_universe()
    env = VectorizedHamletEnv.from_universe(
        universe,
        level_name=LEVEL_NAME,
        num_agents=NUM_AGENTS,
        device="cpu",
    )
    env.reset()

    wait_id = _wait_action_id(env)
    actions = torch.full((NUM_AGENTS,), wait_id, dtype=torch.long, device="cpu")

    for _ in range(NUM_STEPS):
        obs, rewards, dones, info = env.step(actions)

        assert obs.shape == (NUM_AGENTS, env.observation_dim)
        assert rewards.shape == (NUM_AGENTS,)
        assert dones.shape == (NUM_AGENTS,)
        assert torch.isfinite(obs).all()
        assert torch.isfinite(rewards).all()
        assert dones.dtype == torch.bool
        assert isinstance(info, dict)
