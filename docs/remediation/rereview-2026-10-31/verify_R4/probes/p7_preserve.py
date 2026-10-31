"""Area 7: behaviour preservation vs 636192e0. Usage: p7_preserve.py <WT> <OUT.json> [randomize_false]
Compiles each pack (from a copy; optionally with randomize_affordances forced false), rolls 48 scripted steps at N=4,
hashes obs/reward/done/meters/positions/registry per tick."""
import sys, os, json, hashlib, logging, warnings, shutil, yaml
logging.disable(logging.CRITICAL); warnings.filterwarnings("ignore")
os.environ["CUDA_VISIBLE_DEVICES"] = ""
from pathlib import Path
import torch
WT = Path(sys.argv[1]).resolve(); OUT = sys.argv[2]; FORCE_FIXED = len(sys.argv) > 3
sys.path.insert(0, str(WT / "src"))
import townlet; assert str(WT) in townlet.__file__, townlet.__file__
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.determinism import seed_all
HERE = Path(__file__).resolve().parent
PACKS = [("configs/default_curriculum", "L1_full_observability"), ("configs/default_curriculum", "L3_temporal_mechanics"),
         ("configs/reference/model_pack", "L0_demo"), ("configs/test/items_smoke", "L0_smoke"), ("configs/test/effects_smoke", "L0_effects"),
         ("configs/trial_k_cold", "L0_cold")]
def H(t): return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()[:12]
res = {}
for pack, level in PACKS:
    key = f"{pack}:{level}"
    work = HERE / "work_preserve" / (WT.name + ("_fixed" if FORCE_FIXED else "")) / pack.replace("/", "__")
    shutil.rmtree(work, ignore_errors=True); shutil.copytree(WT / pack, work, ignore=shutil.ignore_patterns(".compiled"))
    tr = work / "levels" / level / "training.yaml"; rand = yaml.safe_load(open(tr))["training"]["randomize_affordances"]
    if FORCE_FIXED:
        d = yaml.safe_load(open(tr)); d["training"]["randomize_affordances"] = False; yaml.safe_dump(d, open(tr, "w"), sort_keys=False)
    try:
        u = UniverseCompiler().compile(work, primary_level=level, use_cache=False)
    except Exception as e:
        res[key] = {"error": str(e)[:300]}; continue
    lv = u.get_level(level); hashes = {}
    for obj, pre in [(u, "u."), (lv, "lv.")]:
        for a in dir(obj):
            if a.endswith("_hash") and not a.startswith("_"):
                try:
                    v = getattr(obj, a)
                    if not callable(v): hashes[pre + a] = str(v)
                except Exception: pass
    seed_all(42); env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=4, device="cpu"); seed_all(42); obs = env.reset()
    reg = env.vfs_registry
    def snap(obs, r=None, d=None):
        parts = [H(obs), H(env.meters), H(env.positions)] + [H(reg.get(v, reader="engine")) for v in sorted(reg.variables)]
        if r is not None: parts += [H(r.float()), H(d)]
        return "".join(parts)
    roll = [snap(obs)]; A = env.action_dim
    for t in range(48):
        a = torch.tensor([(t * 3 + w) % A for w in range(4)], dtype=torch.long)
        obs, r, d, info = env.step(a); roll.append(snap(obs, r, d))
    res[key] = {"randomize_shipped": rand, "hashes": hashes, "roll": roll, "layout": {k: v.tolist() for k, v in env.affordances.items()},
                "actions": [x.name for x in env.action_space.actions], "rng": H(torch.get_rng_state())}
json.dump(res, open(OUT, "w"), indent=0)
print("done", OUT, "from", WT.name, "fixed" if FORCE_FIXED else "as-shipped")
