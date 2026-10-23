"""hamlet-6c49488b22 position-typing side: items never spawn on non-2D/3D substrates; fixed_positions typed 2-D."""
import shutil, sys, yaml, torch, traceback
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
src = Path("configs/trial_k_cold")
def run(tag, stratum_sub, pos_fn):
    dst = Path(sys.argv[1]) / f"trialk_{tag}"
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".compiled"))
    st = dst / "stratum.yaml"; d = yaml.safe_load(st.read_text()); d["stratum"]["substrate"] = stratum_sub; st.write_text(yaml.safe_dump(d))
    aff = dst / "levels/L0_cold/affordances.yaml"; a = yaml.safe_load(aff.read_text())
    lst = a["affordances"]["affordances"] if isinstance(a["affordances"], dict) else a["affordances"]
    for x in lst:
        if x["deployment"].get("positions"): x["deployment"]["positions"] = [pos_fn(p) for p in x["deployment"]["positions"]]
    aff.write_text(yaml.safe_dump(a))
    try:
        u = UniverseCompiler().compile(dst, primary_level="L0_cold")
        env = VectorizedHamletEnv.from_universe(u, level_name="L0_cold", num_agents=1, device="cpu")
        env.reset()
        print(f"[{tag}] compile+reset OK; active_items after reset:", {k: v.position for k, v in env.item_manager.active_items.items()},
              "| items_appearance declared:", [(r.item_type, r.spawn_count, r.placement.mode, r.placement.fixed_positions) for r in env.level.items_appearance.items])
    except Exception as e:
        print(f"[{tag}] FAILED: {type(e).__name__}: {str(e)[:300]}")
run("grid_control", {"type": "grid", "grid": {"topology": "square", "width": 7, "height": 7, "boundary": "clamp", "distance_metric": "manhattan", "diagonals": False}}, lambda p: p)
run("gridnd", {"type": "gridnd", "gridnd": {"dimension_sizes": [7, 7, 7, 7], "boundary": "clamp", "distance_metric": "manhattan", "topology": "hypercube"}}, lambda p: p + [0, 0])
run("cubic", {"type": "grid", "grid": {"topology": "cubic", "width": 7, "height": 7, "depth": 2, "boundary": "clamp", "distance_metric": "manhattan", "diagonals": False}}, lambda p: p + [0])
# the DTO itself
from townlet.config.items_config import SpawnPlacementConfig
try:
    SpawnPlacementConfig(mode="fixed", fixed_positions=[[1, 0, 0, 0]]); print("SpawnPlacementConfig accepts 4-D fixed_positions")
except Exception as e:
    print("SpawnPlacementConfig refuses 4-D fixed_positions:", str(e).splitlines()[1:3])
