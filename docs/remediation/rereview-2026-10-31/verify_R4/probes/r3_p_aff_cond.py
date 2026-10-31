import torch
from harness import *
from townlet.determinism import seed_all
def variables(v):
    v["declarations"].extend([decl("aff_v", scope="affordance", initial_value=0.0), decl("aff_w", scope="affordance", initial_value=0.5)])
p = make_pack("affc", variables=variables, rules=[rule("ra", [rwrite("aff_v", "1.0", composition="overwrite", condition="uniform() < aff_w")])])
u, err = try_compile(p)
print("compile:", "OK" if u else short(err, 200))
for n in [3, 14]:
    try:
        seed_all(1); env = build_env(u, n); step(env, "WAIT"); v = reg(env, "aff_v")
        print(f"N={n} RAN; world rows identical across worlds (leak signature): {all(torch.equal(v[0], v[w]) for w in range(n))}; w0={v[0].tolist()}")
    except Exception as e:
        print(f"N={n} RUNTIME {type(e).__name__}: {short(str(e), 160)}")
