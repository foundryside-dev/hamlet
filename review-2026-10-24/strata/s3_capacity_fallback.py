"""H3: randomize_affordance_positions capacity fallback strands affordances at origin / breaks reset."""
from pathlib import Path
import logging, torch
logging.basicConfig(level=logging.WARNING)
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
u = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L1_full_observability")
lvl = u.get_level("L1_full_observability")
print("training.randomize_affordances =", lvl.training.randomize_affordances)
print("deployment types:", {a.name: a.deployment.type for a in lvl.affordances.affordances})
env = VectorizedHamletEnv.from_universe(u, level_name="L1_full_observability", num_agents=60, device="cpu")
print("after __init__: randomize_affordances =", env.randomize_affordances)
print("after __init__: affordance positions:", {k: v.tolist() for k, v in env.affordances.items()})
try:
    env.reset()
    print("after reset #1:", {k: v.tolist() for k, v in list(env.affordances.items())[:4]}, "...")
    env.reset()
    print("after reset #2:", {k: v.tolist() for k, v in list(env.affordances.items())[:4]}, "...")
except Exception as e:
    print("reset raised:", type(e).__name__, e)
