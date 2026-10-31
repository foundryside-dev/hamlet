import sys, os, json, hashlib, logging, warnings
logging.disable(logging.CRITICAL); warnings.filterwarnings("ignore")
os.environ["CUDA_VISIBLE_DEVICES"] = ""
from pathlib import Path
import torch
WT = Path(sys.argv[1]); OUT = sys.argv[2]
sys.path.insert(0, str(WT / "src"))
import townlet; assert str(WT) in townlet.__file__, townlet.__file__
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.determinism import seed_all
PACKS = [("configs/default_curriculum", "L1_full_observability"), ("configs/default_curriculum", "L3_temporal_mechanics"),
         ("configs/default_curriculum", "L2_partial_observability"),
         ("configs/reference/model_pack", "L0_demo"), ("configs/test/items_smoke", "L0_smoke"), ("configs/test/effects_smoke", "L0_effects"),
         ("configs/trial_k_cold", "L0_cold")]
def H(t): return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()[:16]
res = {}
for pack, level in PACKS:
    key = f"{pack}:{level}"
    try:
        u = UniverseCompiler().compile(WT / pack, primary_level=level, use_cache=False)
    except Exception as e:
        res[key] = {"error": str(e)[:300]}; continue
    lv = u.get_level(level)
    hashes = {}
    for obj, pre in [(u, "u."), (lv, "lv.")]:
        for a in dir(obj):
            if a.endswith("_hash") and not a.startswith("_"):
                try:
                    v = getattr(obj, a)
                    if not callable(v): hashes[pre + a] = str(v)
                except Exception: pass
    hashes["token_type_schema_hash"] = str(lv.token_spec.token_type_schema_hash) if hasattr(lv.token_spec, "token_type_schema_hash") else "?"
    seed_all(42)
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=4, device="cpu")
    seed_all(42)
    obs = env.reset()
    roll = [H(obs)]
    A = env.action_dim
    for t in range(48):
        a = torch.tensor([(t * 3 + w) % A for w in range(4)], dtype=torch.long)
        obs, r, d, info = env.step(a)
        roll.append(H(obs) + H(r.float()) + H(d) + H(env.meters))
    res[key] = {"hashes": hashes, "roll": hashlib.sha256("".join(roll).encode()).hexdigest()[:16], "rng": H(torch.get_rng_state())}
json.dump(res, open(OUT, "w"), indent=1)
print("done", OUT)
