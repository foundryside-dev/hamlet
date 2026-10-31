"""H3 variant: pack asks for randomized placement with deployment.type=random; capacity fallback then breaks reset."""
import shutil, sys, yaml, torch
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
src = Path("configs/test/action_space/grid2d"); dst = Path(sys.argv[1]) / "grid2d_random"
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".compiled"))
aff = dst / "levels/L0/affordances.yaml"; a = yaml.safe_load(aff.read_text())
lst = a["affordances"]["affordances"] if isinstance(a["affordances"], dict) else a["affordances"]
for x in lst: x["deployment"] = {"type": "random", "positions": []}
aff.write_text(yaml.safe_dump(a))
tr = dst / "levels/L0/training.yaml"; tr.write_text(tr.read_text().replace("randomize_affordances: false", "randomize_affordances: true"))
u = UniverseCompiler().compile(dst, primary_level="L0")
print("deployment types:", {x["name"]: x["deployment"]["type"] for x in lst}, "| 8x8 grid")
env = VectorizedHamletEnv.from_universe(u, level_name="L0", num_agents=70, device="cpu")
print("after __init__: randomize_affordances =", env.randomize_affordances, " affordances:", {k: v.tolist() for k, v in env.affordances.items()})
try:
    env.reset(); print("reset OK:", {k: v.tolist() for k, v in env.affordances.items()})
except Exception as e:
    print("reset raised:", type(e).__name__, "-", e)
