import time, torch
from harness import *
def mk(name, decls=(), rules=None, wait_writes=None):
    acts = None
    if wait_writes is not None:
        acts = lambda a: [ca.__setitem__("writes", wait_writes) for ca in a["custom_actions"] if ca["name"] == "WAIT"]
    return make_pack(name, variables=lambda v: v["declarations"].extend(decls), rules=rules, actions=acts)
variants = {
  "baseline (no draws)": mk("pf0", [decl("x", initial_value=0.0, expression="bar.energy * 2.0")]),
  "1 agent draw": mk("pf1", [decl("x", initial_value=0.0, expression="uniform()")]),
  "4 draws (2 expr+rule+write)": mk("pf4", [decl("x", initial_value=0.0, expression="uniform() + normal_dist()"), decl("t", initial_value=0.0), decl("w", initial_value=0.0)],
                                   rules=[rule("r", [rwrite("t", "uniform()", composition="overwrite")])], wait_writes=[write("w", "uniform()", composition="overwrite")]),
}
for n in [64, 256]:
    for label, p in variants.items():
        u = compile_pack(p)
        env = build_env(u, n)
        acts = torch.full((n,), action_index(env, "WAIT"))
        for _ in range(10): env.step(acts)
        t0 = time.perf_counter(); steps = 200
        for _ in range(steps): env.step(acts)
        dt = time.perf_counter() - t0
        print(f"N={n:4d} {label:30s} {steps/dt:8.1f} steps/s  ({dt/steps*1000:.2f} ms/step)")
