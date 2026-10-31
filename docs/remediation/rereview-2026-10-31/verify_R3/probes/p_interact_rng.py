import torch
from harness import *
from townlet.determinism import seed_all
def aff(a):
    for x in a["affordances"]:
        x["interactions"]["on_start"].append({"modify": "atarget", "value": "uniform()"})
p = make_pack("irng", variables=lambda v: v["declarations"].append(decl("atarget", initial_value=0.0)), affordances=aff)
u = compile_pack(p)
seed_all(4)
env = build_env(u, 3)
for name in env.affordances:
    env.positions[:] = env.affordances[name].to(env.positions.dtype)
    s0 = torch.get_rng_state().clone()
    obs, r, d, info = step(env, "INTERACT")
    print(name, "success:", info["successful_interactions"], "atarget:", [round(x, 3) for x in reg(env, "atarget").tolist()], "global RNG consumed:", not torch.equal(s0, torch.get_rng_state()))
