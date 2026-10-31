"""distance_to_affordance correct at reset / step / next-episode reset, per substrate, randomize on/off, POMDP."""
import torch, yaml
from harness import *
from harness import WT
from townlet.determinism import seed_all

import sys
DEPLOY = "nodeploy" not in sys.argv
ONLY = [a for a in sys.argv[1:] if a != "nodeploy"]
NORM = {"kind": "minmax", "min": 0.0, "max": 100.0, "clip": True}

def pack(base, level, aff, randomize, name):
    def variables(v):
        v["declarations"].extend([
            decl("d_aff", initial_value=-1.0, expression=f'distance_to_affordance("{aff}")', exposed=("agent",), normalization=NORM),
            decl("d_euc", initial_value=-1.0, expression=f'distance_to_affordance("{aff}", "euclidean")'),
            decl("inr", type="bool", initial_value=False, expression=f'in_range("{aff}", 1.0)'),
        ])
    p = make_pack(name, variables=variables, base=base, level=level)
    t = p / "levels" / level / "training.yaml"
    d = yaml.safe_load(open(t))
    if randomize is not None:
        d["training"]["randomize_affordances"] = randomize
    if d["training"]["enabled_affordances"] == [] and DEPLOY:
        d["training"]["enabled_affordances"] = [aff]
    yaml.safe_dump(d, open(t, "w"), sort_keys=False)
    return p

def check(env, aff, label):
    pos = env.positions.to(torch.float32)
    a = env.affordances.get(aff)
    if a is None:
        print(f"   {label}: affordance {aff} not deployed; d_aff={reg(env,'d_aff').tolist()}"); return
    a = a.to(torch.float32)
    diff = pos - a
    man = diff.abs().sum(-1); euc = diff.pow(2).sum(-1).sqrt()
    d = reg(env, "d_aff"); e = reg(env, "d_euc"); i = reg(env, "inr")
    ok = torch.allclose(d, man) and torch.allclose(e, euc) and torch.equal(i, man <= 1.0)
    print(f"   {label}: {'OK ' if ok else 'BAD'} d_aff={[round(x,3) for x in d.tolist()]} hand={[round(x,3) for x in man.tolist()]} euc_ok={torch.allclose(e,euc)} inr_ok={torch.equal(i, man<=1.0)}")

CASES = [
    ("grid2d L1 randomize=T", WT/"configs/default_curriculum", "L1_full_observability", "EAT", True),
    ("grid2d L1 randomize=F", WT/"configs/default_curriculum", "L1_full_observability", "EAT", False),
    ("grid2d L2 POMDP", WT/"configs/default_curriculum", "L2_partial_observability", "EAT", True),
    ("gridnd 4d", WT/"configs/test/gridnd_4d_pack", "L0_test", None, None),
    ("continuous1d", WT/"configs/test/action_space/continuous1d", "L0", None, None),
    ("aspatial", WT/"configs/aspatial_test", "L0", None, None),
]
for label, base, level, aff, rnd in CASES:
    if ONLY and not any(o in label for o in ONLY): continue
    if aff is None:
        d = yaml.safe_load(open(base/"levels"/level/"affordances.yaml"))
        aff = d["affordances"]["affordances"][0]["name"]
    print(f"== {label} (aff={aff})")
    p = pack(base, level, aff, rnd, "sp_" + label.replace(" ", "_").replace("=", ""))
    u, err = try_compile(p, level)
    if u is None:
        print("   COMPILE REFUSED", short(err, 300)); continue
    seed_all(3)
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=4, device="cpu")
    obs0 = env.reset()
    check(env, aff, "reset")
    print("   reset obs == re-encoded obs:", torch.equal(obs0, env._get_observations()))
    names = [a.name for a in env.action_space.actions]
    for t in range(3):
        env.step(torch.tensor([t % len(names), (t+1) % len(names), (t+2) % len(names), 0]))
    check(env, aff, "after 3 steps")
    env.reset()
    check(env, aff, "episode-2 reset")
