import torch
from harness import *
from townlet.determinism import seed_all
p = make_pack("reginit", variables=lambda v: v["declarations"].append(decl("noise", type="tensor1d", shape=[2], initial_value_mode="random_uniform", initial_value_params={"low": 0.0, "high": 1.0})))
u = compile_pack(p)
out = {}
for n in [2, 4]:
    seed_all(5); env = build_env(u, n); out[n] = (reg(env, "noise").clone(), env.positions.clone())
print("random_uniform tensor init, world 0 at N=2 vs N=4 equal:", torch.equal(out[2][0][0], out[4][0][0]), out[2][0][0].tolist(), out[4][0][0].tolist())
print("agent spawn position, world 1 at N=2 vs N=4 equal:", torch.equal(out[2][1][1], out[4][1][1]))
