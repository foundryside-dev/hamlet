"""H7: fixed affordance positions outside the grid are accepted at compile and construct time."""
import shutil, sys, yaml, torch
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
src = Path("configs/differential/div003_rect"); dst = Path(sys.argv[1]) / "rect_oob"
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".compiled"))
aff = dst / "levels/L1_full_observability/affordances.yaml"
doc = yaml.safe_load(aff.read_text())
first = doc["affordances"]["affordances"][0] if "affordances" in doc["affordances"] else doc["affordances"][0]
first["deployment"]["positions"] = [[7, 7]]
name = first["name"]; aff.write_text(yaml.safe_dump(doc))
tr = dst / "levels/L1_full_observability/training.yaml"
tr.write_text(tr.read_text().replace("randomize_affordances: true", "randomize_affordances: false"))
u = UniverseCompiler().compile(dst, primary_level="L1_full_observability")
print(f"compile OK on 8x6 grid with affordance {name} at [7,7] (y=7 >= height 6)")
env = VectorizedHamletEnv.from_universe(u, level_name="L1_full_observability", num_agents=1, device="cpu")
env.reset()
print("env.affordances[name] =", env.affordances[name].tolist())
print("normalize_positions([7,7]) =", env.substrate.normalize_positions(torch.tensor([[7, 7]])).tolist())
ok = any(env.substrate.is_on_position(torch.tensor([[x, y]]), env.affordances[name]).item() for x in range(8) for y in range(6))
print("reachable from any in-bounds cell:", ok)
obs = env._get_observations(); print("obs finite:", bool(torch.isfinite(obs).all()), "obs max:", obs.max().item())
try:
    env.validate_affordance_positions(env.get_affordance_positions()); print("validate_affordance_positions accepted")
except ValueError as e:
    print("validate_affordance_positions (checkpoint path) refuses:", e)
