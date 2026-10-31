"""Area 2: draw-site identity stability, hash coverage, rule-condition sharing, independence, global-RNG consumption."""
import torch, yaml
from harness import *  # noqa
from harness import WT, make_pack, decl, write, rule, rwrite, compile_pack, try_compile, build_env, step, reg, short
from townlet.determinism import seed_all
print("townlet at", __import__("townlet").__file__)
LEVEL = "L1_full_observability"
VARS = ["g_rand", "a_rand", "ra_a", "ra_b", "rb_c", "aw_d"]

def build(name, *, swap_writes=False, insert_write_before=False, reorder_rules=False, rename_rule=False, rename_var=False, add_rule_first=False, rename_action_target=False):
    decls = [decl("g_rand", scope="global", initial_value=0.0, expression="uniform()"),
             decl("a_rand", initial_value=0.0, expression="uniform()"),
             decl("ra_a", initial_value=0.0), decl("ra_b", initial_value=0.0), decl("rb_c", initial_value=0.0), decl("aw_d", initial_value=0.0), decl("zz", initial_value=0.0)]
    if rename_var:
        for d in decls:
            if d["id"] == "ra_a": d["id"] = "ra_a2"
    def variables(v): v["declarations"].extend(decls)
    def actions(a):
        for ca in a["custom_actions"]:
            if ca["name"] == "REST":
                ca["writes"] = [write("aw_d", "uniform()", composition="overwrite")]
    wa = [rwrite("ra_a2" if rename_var else "ra_a", "uniform()", composition="overwrite"), rwrite("ra_b", "uniform()", composition="overwrite")]
    if swap_writes: wa = wa[::-1]
    if insert_write_before: wa = [rwrite("zz", "1.0", composition="overwrite")] + wa
    rules = [rule("rA2" if rename_rule else "rA", wa), rule("rB", [rwrite("rb_c", "uniform()", composition="overwrite")])]
    if reorder_rules: rules = rules[::-1]
    if add_rule_first: rules = [rule("r0", [rwrite("zz", "2.0", composition="overwrite")])] + rules
    return make_pack(name, variables=variables, actions=actions, rules=rules)

def hashes(u):
    lv = u.get_level(LEVEL); out = {}
    for obj, pre in [(u, "u."), (lv, "lv.")]:
        for a in dir(obj):
            if a.endswith("_hash") and not a.startswith("_"):
                v = getattr(obj, a)
                if not callable(v): out[pre + a] = str(v)[:16]
    return out

def trace(pack, n=3, steps=6, seed=9, rename_var=False):
    seed_all(seed); u = compile_pack(pack, LEVEL); env = build_env(u, n); seed_all(seed)
    vs = [("ra_a2" if rename_var and v == "ra_a" else v) for v in VARS]
    out = []
    for _ in range(steps):
        step(env, "REST"); out.append({k: reg(env, v).clone() for k, v in zip(VARS, vs)})
    return hashes(u), out

print("\n### site stability (which draws change; which hashes move)")
h0, t0 = trace(build("s_base"))
for label, kw in [("swap the two writes of rule rA", dict(swap_writes=True)),
                  ("insert a non-random write before them", dict(insert_write_before=True)),
                  ("reorder rules rA/rB", dict(reorder_rules=True)),
                  ("add an unrelated rule first", dict(add_rule_first=True)),
                  ("rename rule rA -> rA2", dict(rename_rule=True)),
                  ("rename target var ra_a -> ra_a2 (rule write 0)", dict(rename_var=True))]:
    h1, t1 = trace(build("s_" + str(abs(hash(label)) % 10**6), **kw), rename_var=kw.get("rename_var", False))
    same = {v: all(torch.equal(x[v], y[v]) for x, y in zip(t0, t1)) for v in VARS}
    moved = sorted(k for k in h0 if h0[k] != h1.get(k))
    print(f"  {label:48s} unchanged={ {k: v for k, v in same.items()} } hashes moved={moved}")
print("  (hash keys:", sorted(h0), ")")

print("\n### rule-level condition shared across writes; write-level conditions independent")
def variables(v): v["declarations"].extend([decl("c1", initial_value=0.0), decl("c2", initial_value=0.0), decl("w1", initial_value=0.0), decl("w2", initial_value=0.0)])
p = make_pack("cond", variables=variables, rules=[
    rule("shared", [rwrite("c1", "1.0", composition="overwrite"), rwrite("c2", "1.0", composition="overwrite")], condition="uniform() < 0.5"),
    rule("own", [rwrite("w1", "1.0", composition="overwrite", condition="uniform() < 0.5"), rwrite("w2", "1.0", composition="overwrite", condition="uniform() < 0.5")]),
])
u, err = try_compile(p); print("  compile:", "OK" if u else short(err, 300))
seed_all(1); env = build_env(u, 64)
agree_shared = agree_own = 0; fired = 0; T = 40; rows = []
for t in range(T):
    # overwrite from 0 each tick so the fire pattern is visible
    env.vfs_registry.set_engine_value("c1", torch.zeros(64)); env.vfs_registry.set_engine_value("c2", torch.zeros(64))
    env.vfs_registry.set_engine_value("w1", torch.zeros(64)); env.vfs_registry.set_engine_value("w2", torch.zeros(64))
    step(env, "WAIT")
    c1, c2, w1, w2 = (reg(env, k) for k in ("c1", "c2", "w1", "w2"))
    agree_shared += int((c1 == c2).sum()); agree_own += int((w1 == w2).sum()); fired += int(c1.sum()); rows.append(c1.clone())
print(f"  shared rule condition: c1==c2 in {agree_shared}/{64*T} rows (expect all); fired {fired}/{64*T} (expect ~half)")
print(f"  independent write conditions: w1==w2 in {agree_own}/{64*T} rows (expect ~half)")
print(f"  c1 constant over worlds? {all(bool((r == r[0]).all()) for r in rows)}  constant over ticks? {all(torch.equal(rows[0], r) for r in rows)}")

print("\n### two draws in one expression are independent; the same draw site is reused by two reads of one var")
p2 = make_pack("two", variables=lambda v: v["declarations"].extend([decl("d", initial_value=0.0, expression="uniform() - uniform()"), decl("e", initial_value=0.0, expression="uniform() * 0.0 + uniform()")]))
u2, err = try_compile(p2); seed_all(1); env = build_env(u2, 2000); step(env, "WAIT")
d = reg(env, "d").double(); e = reg(env, "e").double()
print(f"  d=u1-u2: mean={d.mean():+.4f} std={d.std():.4f} (expect 0.408) zeros={int((d==0).sum())}; e = second draw of its own site; corr(e, d)={float(((e-e.mean())*(d-d.mean())).mean()/(e.std()*d.std())):+.4f}")

print("\n### torch global RNG untouched by a step with draws; manual_seed after construction changes nothing")
seed_all(3); env = build_env(u, 4); s0 = torch.get_rng_state().clone()
for _ in range(5): step(env, "WAIT")
print("  global rng state unchanged over 5 steps:", torch.equal(s0, torch.get_rng_state()))
seed_all(3); envA = build_env(u, 4); torch.manual_seed(999); [step(envA, "WAIT") for _ in range(3)]; a = reg(envA, "c1").clone()
seed_all(3); envB = build_env(u, 4); [step(envB, "WAIT") for _ in range(3)]; b = reg(envB, "c1").clone()
print("  manual_seed(999) after construction leaves draws unchanged:", torch.equal(a, b))

print("\n### engine-defect guard: profile evaluated without draws")
try:
    pr = u2.compiled_vfs_profiles
    env.vfs_evaluator.evaluate_profile(pr.agent_profile if hasattr(pr, "agent_profile") else pr, env.vfs_registry.snapshot() if hasattr(env.vfs_registry, "snapshot") else {}, {}, {}, device=torch.device("cpu"))
    print("  no error raised")
except Exception as ex:
    print("  ", type(ex).__name__, short(str(ex), 200))

print("\n### V1 via arithmetic: affordance-scope rule with [W]-shaped operands (bar / agent scalar)")
for expr in ["uniform(0.0, bar.energy)", "uniform() + a_rand", "uniform() * g_rand", "normal_dist(bar.energy, 0.1)"]:
    def variables(v): v["declarations"].extend([decl("aff_v", scope="affordance", initial_value=0.0), decl("g_rand", scope="global", initial_value=0.0, expression="uniform()"), decl("a_rand", initial_value=0.0, expression="uniform()")])
    pk = make_pack("affar_" + str(abs(hash(expr)) % 10**6), variables=variables, rules=[rule("ra", [rwrite("aff_v", expr, composition="overwrite")])])
    uu, err = try_compile(pk)
    if uu is None: print(f"  {expr:30s} REFUSED {short(err[err.find(' - ')+3:], 220)}"); continue
    for n in (3, 14):
        try:
            seed_all(1); e = build_env(uu, n); step(e, "WAIT"); val = reg(e, "aff_v")
            seed_all(1); e1 = build_env(uu, 1); step(e1, "WAIT")
            print(f"  {expr:30s} N={n:2d} RAN shape={tuple(val.shape)} world0==world0(N=1): {torch.equal(reg(e1,'aff_v')[0], val[0])}")
        except Exception as ex:
            print(f"  {expr:30s} N={n:2d} RUNTIME {type(ex).__name__}: {short(str(ex), 160)}")

print("\n### action write with a draw on an affordance target (occupancy claim) and on a global target")
def variables(v): v["declarations"].extend([decl("occ", scope="affordance", type="agent_ref", initial_value=None), decl("gt", scope="global", initial_value=0.0)])
def actions(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST":
            ca["source_affordance"] = "EAT"
            ca["writes"] = [write("occ", "-1", composition="claim_if_free", condition="uniform() < 0.5", phase="ingest_actions")]
        if ca["name"] == "MEDITATE":
            ca["writes"] = [write("gt", "uniform()", composition="overwrite")]
pk = make_pack("aw_aff", variables=variables, actions=actions)
uu, err = try_compile(pk); print("  compile:", "OK" if uu else short(err[err.find(' - ')+3:], 300))
if uu:
    try:
        seed_all(1); e = build_env(uu, 5); step(e, "MEDITATE"); print("  global target via action write:", reg(e, "gt").tolist())
    except Exception as ex:
        print("  RUNTIME", type(ex).__name__, short(str(ex), 200))
