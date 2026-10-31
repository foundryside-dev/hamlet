"""trace.py <expect_wt> <pack> <level> <tag> <out.pt> [num_agents=4] [steps=64] [seed=0]"""
import sys, os, shutil, logging
logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
import townlet
exp, pack, level, tag, out = sys.argv[1:6]
N = int(sys.argv[6]) if len(sys.argv) > 6 else 4
STEPS = int(sys.argv[7]) if len(sys.argv) > 7 else 64
SEED = int(sys.argv[8]) if len(sys.argv) > 8 else 0
assert townlet.__file__.startswith(exp), (townlet.__file__, exp)
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
work = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/diff8") / tag
shutil.rmtree(work, ignore_errors=True)
shutil.copytree(pack, work, ignore=shutil.ignore_patterns(".compiled"))
u = UniverseCompiler().compile(work, primary_level=level, use_cache=False)
torch.manual_seed(SEED)
env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=N, device="cpu")
torch.manual_seed(SEED)
obs = env.reset()
reg = env.vfs_registry
names = [a.name for a in env.action_space.actions]
g = torch.Generator().manual_seed(1234)
acts = torch.randint(0, env.action_dim, (STEPS, N), generator=g)
def snap():
    d = {"meters": env.meters.clone(), "positions": env.positions.clone(), "dones": env.dones.clone()}
    for vid in sorted(reg.variables):
        d[f"vfs.{vid}"] = reg.get(vid, reader="engine").clone()
    if getattr(reg, "item_vfs", None) is not None:
        d["item_vfs"] = reg.item_vfs.clone()
    return d
trace = [dict(snap(), obs=obs.clone())]
for t in range(STEPS):
    o, r, dn, info = env.step(acts[t])
    trace.append(dict(snap(), obs=o.clone(), reward=r.clone(), step_dones=dn.clone()))
torch.save({"actions": names, "action_dim": env.action_dim, "trace": trace, "acts": acts,
            "hashes": {k: getattr(u, k, None) for k in ("config_hash",)}}, out)
print(tag, "OK action_dim", env.action_dim, "ticks", len(trace))
