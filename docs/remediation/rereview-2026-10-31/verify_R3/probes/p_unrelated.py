import torch
from r3pack import *
from harness import decl, rule, rwrite
VARS = ["g_rand", "a_two", "g_target", "a_target"]
def trace(pack, steps=8):
    env, _ = make_env(pack, 3, 9)
    names = {a.name: a.id for a in env.action_space.actions}
    r = env.vfs_registry
    out = [{v: r.get(v, reader="engine").clone() for v in VARS}]
    for _ in range(steps):
        env.step(torch.full((3,), names["WAIT"]))
        out.append({v: r.get(v, reader="engine").clone() for v in VARS})
    return out
def cmp(a, b):
    return {v: all(torch.equal(x[v], y[v]) for x, y in zip(a, b)) for v in VARS}
base = trace(build("un0"))
variants = {
    "unrelated non-random agent var": dict(extra_decls=[decl("zz", initial_value=0.0, expression="bar.energy + 1.0")]),
    "unrelated non-random global var": dict(extra_decls=[decl("zg", scope="global", initial_value=0.0, expression="tick * 2.0")]),
    "unrelated static var": dict(extra_decls=[decl("zs", initial_value=3.0)]),
    "declaration order reversed": dict(decl_order_reverse=True),
    "unrelated RANDOM agent var (declared last)": dict(extra_decls=[decl("zr", initial_value=0.0, expression="uniform()")]),
    "unrelated RANDOM global var (declared last)": dict(extra_decls=[decl("zrg", scope="global", initial_value=0.0, expression="normal_dist()")]),
    "unrelated random rule on new var": dict(extra_decls=[decl("zt", initial_value=0.0)], extra_rules=[rule("rz", [rwrite("zt", "uniform()", composition="overwrite")])]),
}
for label, kw in variants.items():
    print(f"{label:45s}", cmp(base, trace(build("un_" + str(abs(hash(label)) % 10**6), **kw))))
