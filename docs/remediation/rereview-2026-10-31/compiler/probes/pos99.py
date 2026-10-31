import sys, logging; logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
u = UniverseCompiler().compile(Path(sys.argv[1]), primary_level="L0_effects", use_cache=False)
env = u.create_environment(num_agents=1, level_name="L0_effects", device="cpu"); env.reset()
print({k: v.tolist() for k, v in env.affordances.items()}, "grid", u.stratum.stratum.substrate.grid.width, u.stratum.stratum.substrate.grid.height)
