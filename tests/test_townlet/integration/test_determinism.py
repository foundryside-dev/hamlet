"""WS-7 determinism regression: same seed, same trace (hamlet-834108b55a).

Two pins:

1. **Trace determinism** — `seed_all(s)` followed by env construction, reset, and 40
   steps of torch-drawn random actions produces a bit-identical observation/reward
   trace across runs. This is the by-hand experiment from the issue (verified
   2026-08-11), formalized so the differential harness can rely on it.

2. **Spawn placement is independent of Python's global `random` state** — the
   collision-exhaustion fallback in `randomize_affordance_positions` used
   `random.shuffle` off the global RNG. The pin forces the fallback (agents + 14
   affordances ≈ grid capacity, so 10 with-replacement sampling attempts always
   collide) and perturbs the global `random` stream differently between two
   otherwise-identical runs: placements must not move. Reverting the fix
   (torch.randperm → random.shuffle) fails this test by name.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import pytest
import torch

from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

SOURCE_PACK = Path("configs/default_curriculum")
L0 = "L0_0_minimal"


@pytest.fixture(scope="module")
def universe() -> CompiledUniverse:
    return UniverseCompiler().compile(SOURCE_PACK, primary_level=L0, use_cache=False)


def _trace_hash(universe: CompiledUniverse, seed: int, steps: int = 40, device: str = "cpu") -> str:
    seed_all(seed)
    env = VectorizedHamletEnv(universe=universe, level_name=L0, num_agents=4, device=torch.device(device))
    obs = env.reset()
    digest = hashlib.sha256()
    digest.update(obs.cpu().numpy().tobytes())
    for _ in range(steps):
        # Draw actions from the CPU RNG so the action sequence is device-independent,
        # then move them to the env device (a CUDA env must get CUDA actions).
        actions = torch.randint(0, env.action_dim, (env.num_agents,)).to(env.device)
        obs, rewards, dones, _ = env.step(actions)
        digest.update(obs.cpu().numpy().tobytes())
        digest.update(rewards.cpu().numpy().tobytes())
        digest.update(dones.cpu().numpy().tobytes())
    return digest.hexdigest()


def test_same_seed_produces_identical_trace(universe: CompiledUniverse) -> None:
    assert _trace_hash(universe, 42) == _trace_hash(universe, 42)


def test_different_seed_produces_different_trace(universe: CompiledUniverse) -> None:
    assert _trace_hash(universe, 42) != _trace_hash(universe, 43)


requires_cuda = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")


@requires_cuda
def test_same_seed_produces_identical_trace_cuda(universe: CompiledUniverse) -> None:
    """GPU + TorchScript-JIT determinism (WS-7 content 1, previously untested).

    The vtc kernels are @torch.jit.script and unconditionally on the step path, so
    this trace exercises the JIT path on CUDA. Bit-identical means the differential
    harness may trust GPU traces; if this ever fails, the harness must run CPU-side
    (or the offending kernels need deterministic variants) — that is a finding, not
    test noise.
    """
    assert _trace_hash(universe, 42, device="cuda") == _trace_hash(universe, 42, device="cuda")


@requires_cuda
def test_different_seed_produces_different_trace_cuda(universe: CompiledUniverse) -> None:
    assert _trace_hash(universe, 42, device="cuda") != _trace_hash(universe, 43, device="cuda")


def _forced_fallback_placement(universe: CompiledUniverse, perturb: int) -> tuple[list, dict[str, list]]:
    seed_all(42)
    # Perturb ONLY Python's global RNG. If any placement path still consumes it,
    # the two runs of this helper diverge.
    random.seed(perturb)
    env = VectorizedHamletEnv(universe=universe, level_name=L0, num_agents=45, device=torch.device("cpu"))
    env.reset()
    assert env.randomize_affordances, "capacity warning tripped — the pin no longer forces the fallback, shrink num_agents"
    return env.positions.tolist(), {name: pos.tolist() for name, pos in env.affordances.items()}


def test_spawn_placement_ignores_global_random_state(universe: CompiledUniverse) -> None:
    assert _forced_fallback_placement(universe, 111) == _forced_fallback_placement(universe, 222)
