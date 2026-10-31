"""Draws on affordance-scope rule targets: [W] draw combined with [W, A] operands."""
import torch, traceback
from harness import *
from townlet.determinism import seed_all

def pack_for(expr, name):
    def variables(v):
        v["declarations"].extend([
            decl("aff_v", scope="affordance", initial_value=0.0),
            decl("aff_w", scope="affordance", initial_value=1.0),
        ])
    return make_pack(name, variables=variables, rules=[rule("ra", [rwrite("aff_v", expr, composition="overwrite")])])

for expr in ["uniform()", "uniform(aff_w)", "uniform() * aff_w", "uniform(0.0, aff_w)", "where(aff_w > 0.5, uniform(), 0.0)", "normal_dist(aff_w, 0.1)", "normal_dist(0.0, aff_w)"]:
    p = pack_for(expr, "aff_" + str(abs(hash(expr)) % 10**6))
    u, err = try_compile(p)
    if u is None:
        print(f"{expr:40s} COMPILE REFUSED: {short(err, 200)}"); continue
    A = None
    for n in [3, 14]:
        try:
            seed_all(1)
            env = build_env(u, num_agents=n)
            env.step(torch.full((n,), action_index(env, "WAIT")))
            val = reg(env, "aff_v")
            # per world: is the row constant across affordances? and does row w use world w's stream?
            rows_const = [bool(torch.all(val[w] == val[w, 0])) for w in range(n)]
            # cross-world leak check: compare world 0's row at N=n vs N=1
            seed_all(1); e1 = build_env(u, num_agents=1); e1.step(torch.full((1,), action_index(e1, "WAIT")))
            same0 = torch.equal(reg(e1, "aff_v")[0], val[0])
            print(f"{expr:40s} N={n:2d} RAN shape={tuple(val.shape)} row-constant={all(rows_const)} world0(N={n})==world0(N=1): {same0}  w0={val[0,:4].tolist()} w1={val[1,:4].tolist()}")
        except Exception as exc:
            print(f"{expr:40s} N={n:2d} RUNTIME {type(exc).__name__}: {short(str(exc), 220)}")
