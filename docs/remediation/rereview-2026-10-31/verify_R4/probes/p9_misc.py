"""Leftovers: shared-prefix with write-level random conditions; S1 world-0 differential with affordance targets at N in {2,5};
site correlation at 1e5; effects sampling in the differential."""
import torch
from harness import *  # noqa
from harness import HERE, WT, make_pack, decl, write, rule, rwrite, try_compile, compile_pack, build_env, step, reg, short, action_index
from townlet.determinism import seed_all
print("townlet at", __import__("townlet").__file__)

print("\n### rule condition draws shared even when each write also draws in its own condition")
def variables(v): v["declarations"].extend([decl("c1", initial_value=0.0), decl("c2", initial_value=0.0)])
p = make_pack("shared2", variables=variables, rules=[rule("shared", [rwrite("c1", "uniform()", composition="overwrite", condition="uniform() < 0.99"),
                                                                       rwrite("c2", "uniform()", composition="overwrite", condition="uniform() < 0.99")], condition="uniform() < 0.5")])
u, err = try_compile(p); print("  compile:", "OK" if u else short(err, 300))
seed_all(1); env = build_env(u, 64); both = neither = one = 0; T = 40
for t in range(T):
    env.vfs_registry.set_engine_value("c1", torch.zeros(64)); env.vfs_registry.set_engine_value("c2", torch.zeros(64)); step(env, "WAIT")
    f1 = reg(env, "c1") != 0; f2 = reg(env, "c2") != 0
    both += int((f1 & f2).sum()); neither += int((~f1 & ~f2).sum()); one += int((f1 ^ f2).sum())
print(f"  rows: both fired {both}, neither {neither}, exactly one {one} of {64*T}  (shared rule draw => 'exactly one' ~1-2%; unshared => ~25%)")
f1v = reg(env, "c1"); f2v = reg(env, "c2"); print("  c1 and c2 values differ where both fired (independent expression sites):", bool((f1v[(f1v != 0) & (f2v != 0)] != f2v[(f1v != 0) & (f2v != 0)]).all()))

print("\n### S1: world-0 differential on default_curriculum with global/agent/affordance/action/effect draws, N in {2, 5}")
def variables(v):
    v["declarations"].extend([decl("g_rand", scope="global", initial_value=0.0, expression="uniform()"), decl("a_rand", initial_value=0.0, expression="normal_dist(bar.energy, 0.1)"),
                              decl("aff_v", scope="affordance", initial_value=0.0), decl("aff_w", scope="affordance", initial_value=1.0), decl("a_target", initial_value=0.0), decl("sv", initial_value=0.0)])
def actions(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["writes"] = [write("a_target", "uniform(-1.0, 0.0)", composition="overwrite")]
def affordances(payload):
    for aff in payload["affordances"]:
        if aff["name"] == "EAT": aff["interactions"]["on_start"].append({"spawn_effect": "e1", "target": "target", "intensity": "0.5"})
def effects(e):
    e["effect_definitions"] = [{"id": "e1", "scope": "agent", "duration": 4, "reapply_policy": "renew", "observable": True, "on_spawn": [],
                                "on_tick": [{"sample": "uniform", "params": {"min": 0.0, "max": 1.0}, "store_in": "sv"}, {"modify": "bar.energy", "value": "bar.energy - 0.01 * uniform()"}], "on_despawn": [], "on_interrupt": []}]
    e["max_active_effects"] = {"global": 0, "agent": 2, "item": 0, "affordance": 0}
p = make_pack("s1diff", variables=variables, actions=actions, affordances=affordances, effects=effects,
              rules=[rule("ra", [rwrite("aff_v", "uniform() * aff_w", composition="overwrite", condition="uniform() < aff_w")]), rule("rb", [rwrite("aff_w", "uniform(0.5, 1.0)", composition="overwrite")], condition="tick % 3 == 0")])
u, err = try_compile(p); print("  compile:", "OK" if u else short(err, 400))
VARS = ["g_rand", "a_rand", "aff_v", "aff_w", "a_target", "sv"]
def snap(env, w):
    return {"meters": env.meters[w].clone(), "pos": env.positions[w].clone(), **{v: reg(env, v)[w].clone() for v in VARS}, "eff": tuple(sorted((e.effect_id, int(e.duration_remaining)) for e in env.effect_manager.effects_in_world(w)))}
def run(n, perturb, seed=7, steps=40):
    seed_all(seed); env = build_env(u, n); seed_all(seed); env.reset()
    layout = {k: v.clone() for k, v in env.affordances.items()}
    env.meters[:, env.meter_name_to_index["money"]] = 100.0
    out = []
    for t in range(steps):
        names = ["REST" if t % 2 else "WAIT"] * n
        if perturb:
            if t == 5: env.positions[0] = env.affordances["EAT"].clone(); names[0] = "INTERACT"
            if t == 15: env.meters[0, env.meter_name_to_index["health"]] = 0.0
        step(env, names); out.append([snap(env, w) for w in range(n)])
    return out, layout
def equal(a, b): return all(torch.equal(a[k], b[k]) if isinstance(a[k], torch.Tensor) else a[k] == b[k] for k in a)
for n in (2, 5):
    base, lb = run(n, False); pert, lp = run(n, True); aa, _ = run(n, False)
    diffs = [(t, w) for t in range(len(base)) for w in range(1, n) if not equal(base[t][w], pert[t][w])]
    w0 = sum(not equal(base[t][0], pert[t][0]) for t in range(len(base)))
    sv_nonzero = sum(bool(pert[t][0]["sv"] != 0) for t in range(len(base)))
    print(f"  N={n}: layouts equal={all(torch.equal(lb[k], lp[k]) for k in lb)}; worlds 1..{n-1} diffs: {len(diffs)} first={diffs[:2]}; world0 differs at {w0}/{len(base)} ticks; A/A identical: {all(equal(base[t][w], aa[t][w]) for t in range(len(base)) for w in range(n))}; effect sampled (sv!=0) at {sv_nonzero} ticks")
# N-independence of world 0 for every var including affordance targets (layouts differ across N: compare draws only)
seed_all(7); e1 = build_env(u, 1); seed_all(7); e5 = build_env(u, 5)
ok = True
for t in range(12):
    step(e1, "WAIT"); step(e5, "WAIT")
    for v in ("g_rand", "aff_v", "aff_w"):
        ok &= torch.equal(reg(e1, v)[0], reg(e5, v)[0])
print("  world-0 draws (g_rand, aff_v, aff_w) equal at N=1 vs N=5 over 12 ticks:", ok)

print("\n### site correlation at W=1e5 (var:a vs var:b; seed 1 vs 2)")
from townlet.vfs.random_draws import VFSRandomness
def corr(a, b): return float(((a - a.mean()) * (b - b.mean())).mean() / (a.std() * b.std()))
W = 100000; r = VFSRandomness(7); r._episode = 1; ins = r.instant(tick=5, worlds=W, device=torch.device("cpu"))
a = ins.stream("var:a", (W,)).uniform("u", torch.zeros(())).double(); b = ins.stream("var:b", (W,)).uniform("u", torch.zeros(())).double()
s1 = VFSRandomness(1).instant(tick=0, worlds=W, device=torch.device("cpu")).stream("var:x", (W,)).uniform("u", torch.zeros(())).double()
s2 = VFSRandomness(2).instant(tick=0, worlds=W, device=torch.device("cpu")).stream("var:x", (W,)).uniform("u", torch.zeros(())).double()
print(f"  corr(var:a, var:b) = {corr(a, b):+.5f}; corr(seed1, seed2) = {corr(s1, s2):+.5f}  (sigma ~ 0.003)")
