"""Area 1: rerun every R1+R2 verifier repro (verify_R12/RESULTS.md D1-D4 + P3s) at f3a6d115."""
import re, subprocess, os, sys, shutil, yaml
from harness import *  # noqa
import harness, torch
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.references import is_identifier

print("townlet at", __import__("townlet").__file__)
WORK = HERE / "work_r12"; WORK.mkdir(exist_ok=True)
harness.PACKS = WORK

def run(decls, read=None, n=2):
    p = make_pack("ids", variables=lambda v: v["declarations"].extend(decls))
    u, err = try_compile(p)
    if err:
        c = re.findall(r"\[([A-Z_\-]+)\]", err); i = err.find(" - "); return f"REFUSED {c[:1]} {err[i+3:i+200]}".replace("\n", " ")
    env = build_env(u, n); step(env, "WAIT")
    return "OK" + ("" if read is None else f" {read}={env.vfs_registry.get(read, reader='engine').tolist()}")

print("\n##### D1 parser")
p = ExpressionParser()
for s in ["true_count", "truex", "falsey", "false_alarm", "notable", "nothing", "not_x", "iffy", "if_open", "thenx", "elsewhere",
          "orbit", "order", "android", "and_x", "True", "x + notable", "notable + 1", "1.0 + true_count", "a or orbit", "where(notable, 1.0, 0.0)"]:
    try:
        r = p.parse(s); print(f"  {s!r:22} -> {r!r}"[:140])
    except Exception as e:
        print(f"  {s!r:22} -> ERROR {type(e).__name__}: {str(e)[:90]}")
print("D1 e2e notable+able, probe=if notable then 7 else 3:",
      run([decl("able", type="bool", initial_value=True), decl("notable", type="bool", initial_value=True),
           decl("probe", initial_value=0.0, expression="if notable then 7.0 else 3.0")], read="probe"))
print("D1 e2e notable alone:", run([decl("notable", type="bool", initial_value=True), decl("probe", initial_value=0.0, expression="if notable then 7.0 else 3.0")], read="probe"))
print("D1 e2e true_count + 1:", run([decl("true_count", initial_value=1.0), decl("probe", initial_value=0.0, expression="true_count + 1.0")], read="probe"))
print("D1 e2e falsey*2:", run([decl("falsey", initial_value=1.0), decl("probe", initial_value=0.0, expression="falsey * 2.0")], read="probe"))
print("D1 e2e nothing/hing:", run([decl("nothing", initial_value=5.0), decl("hing", type="bool", initial_value=False), decl("probe", initial_value=0.0, expression="where(nothing > 0.0, 1.0, 2.0)")], read="probe"))

print("\n##### D2 placement fallback")
RP = WT / "docs/remediation/rereview-2026-10-31/verify_R12/probes/rp.py"
def rp(src, level, *edits, env=None, steps=None):
    e = dict(os.environ, EXPECT_WT=str(WT), PYTHONPATH=str(WT / "src"), CUDA_VISIBLE_DEVICES="")
    if env: e.update(env)
    d = WORK / "rp"
    out = subprocess.run([sys.executable, str(RP), str(src), level, str(d), *edits], capture_output=True, text=True, env=e)
    return (out.stdout + out.stderr[-300:]).strip()

def rand_fallback(src, level, n, *edits):
    d = WORK / "rf"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(src, d, ignore=shutil.ignore_patterns('.compiled'))
    for i in range(0, len(edits), 3):
        f, old, new = edits[i:i+3]; pth = d / f; t = pth.read_text(); assert old in t, old; pth.write_text(t.replace(old, new, 1))
    try:
        u = compile_pack(d, level)
    except Exception as e:
        return f"REFUSED {short(str(e), 300)}"
    try:
        env = u.create_environment(num_agents=n, level_name=level, device="cpu"); env.reset()
        return f"env built; randomize={env.randomize_affordances}; EAT={env.affordances.get('EAT', env.affordances.get('SLEEP')).tolist()}"
    except Exception as e:
        return f"RUNTIME {type(e).__name__}: {short(str(e), 200)}"
L1 = "L1_full_observability"
for n in (2, 51):
    print(f"  L1 EAT [99,2] n={n}:", rand_fallback(BASE, L1, n, f"levels/{L1}/affordances.yaml", "- - 2\n        - 2\n", "- - 99\n        - 2\n"))
    print(f"  L1 EAT [2,2,2] n={n}:", rand_fallback(BASE, L1, n, f"levels/{L1}/affordances.yaml", "- - 2\n        - 2\n", "- - 2\n        - 2\n        - 2\n"))
sea = WT / "configs/static_epistemic_access"
lv = [p.name for p in (sea / "levels").iterdir()][0]
print(f"  static_epistemic_access {lv} n=61:", rand_fallback(sea, lv, 61))
print(f"  static_epistemic_access {lv} n=2:", rand_fallback(sea, lv, 2))

print("\n##### D3 meter oob")
for label, w in [("overwrite 0.0", rwrite("bar.satiation", "0.0", composition="overwrite")),
                 ("additive -5.0", rwrite("bar.satiation", "-5.0")),
                 ("additive -5.0 rule clamp [0,1]", rwrite("bar.satiation", "-5.0", clamp=[0.0, 1.0]))]:
    for ph in ["ingest_actions", "apply_passive_depletion"]:
        pk = make_pack("oob", rules=[rule("r", [w], phase=ph)])
        u, err = try_compile(pk); env = build_env(u, 1)
        h0 = float(meter(env, "health")[0]); e0 = float(meter(env, "energy")[0])
        step(env, "WAIT")
        print(f"  {label:32} @{ph:24} satiation={float(meter(env,'satiation')[0]):.4f} dhealth={float(meter(env,'health')[0])-h0:+.4f} denergy={float(meter(env,'energy')[0])-e0:+.4f}")
for label, clamp in [("no clamp", None), ("rule clamp [0,1]", [0.0, 1.0])]:
    pk = make_pack("oob2", rules=[rule("over", [rwrite("bar.satiation", "-5.0", clamp=clamp)], phase="apply_threshold_cascades"),
                                  rule("reader", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="apply_transition_rules")])
    u, err = try_compile(pk); env = build_env(u, 1); m0 = float(meter(env, "mood")[0]); step(env, "WAIT")
    print(f"  oob2 {label:18} satiation={float(meter(env,'satiation')[0]):.4f} dmood={float(meter(env,'mood')[0])-m0:+.5f}")

print("\n##### D4 interaction_radius")
c1 = WT / "configs/test/action_space/continuous1d"; lv1 = [p.name for p in (c1 / "levels").iterdir()][0]
print("  ", rp(c1, lv1, "stratum.yaml", "interaction_radius: 1.0", "interaction_radius: 20.0", env={"NOSTEP": "1"}))
from townlet.config.stratum_config import ContinuousConfig
try:
    ContinuousConfig(dimensions=4, bounds=[(0.0, 10.0)]*4, boundary="clamp", movement_delta=1.0, interaction_radius=20.0, distance_metric="euclidean", action_discretization={"type": "cardinal"})
    print("   continuousnd DTO rank4 radius 20: ACCEPTED")
except Exception as e:
    print("   continuousnd DTO rank4 radius 20:", type(e).__name__, short(str(e).replace("\n", " | "), 300))

print("\n##### P3s")
# rank DTO
gnd = WT / "configs/test/gridnd_4d_pack"; lvg = [p.name for p in (gnd / "levels").iterdir()][0]
t = (gnd / "stratum.yaml").read_text(); m = re.search(r"dimension_sizes: \[([^\]]*)\]", t)
for rank in (8, 9, 100):
    print(f"  gridnd rank {rank}:", rp(gnd, lvg, "stratum.yaml", m.group(0), f"dimension_sizes: [{', '.join(['3']*rank)}]", env={"NOSTEP": "1"})[:160])
# DAC-REF and CLOCK locations
L3 = "L3_temporal_mechanics"
print("  DAC-REF modifier bar nosuch:", rp(BASE, L1, f"levels/{L1}/drive.yaml", "bar: energy", "bar: nosuch", env={"NOSTEP": "1"})[:200])
print("  CLOCK period_of nosuch:", rp(BASE, L3, f"levels/{L3}/curriculum.yaml", "period_of: day_phase", "period_of: nosuch", env={"NOSTEP": "1"})[:200])
print("  drive.yaml L1 lines 1-8:"); print("   " + "\n   ".join((BASE / "levels" / L1 / "drive.yaml").read_text().splitlines()[:8]))
print("  curriculum.yaml L3 lines 10-14:"); print("   " + "\n   ".join((BASE / "levels" / L3 / "curriculum.yaml").read_text().splitlines()[9:14]))
# persistent refs
for t_ in ("effect_ref", "affordance_ref", "item_ref", "agent_ref"):
    print(f"  persistent {t_}:", run([decl("pref", type=t_, lifetime="persistent", initial_value=None)]))
# effects_hash on file move
ES = WT / "configs/test/effects_smoke"; lve = [p.name for p in (ES / "levels").iterdir()][0]
def eh(pk):
    return compile_pack(pk, lve).effects_hash
a = make_pack("eh_a", base=ES, level=lve); ha = eh(a)
b = make_pack("eh_b", base=ES, level=lve)
ey = yaml.safe_load(open(b / "effects.yaml")); defs = ey["effect_definitions"]
moved = [defs[-1]]; ey["effect_definitions"] = defs[:-1]; yaml.safe_dump(ey, open(b / "effects.yaml", "w"), sort_keys=False)
yaml.safe_dump({"version": ey.get("version", "1.0"), "effect_definitions": moved}, open(b / "aa_more_effects.yaml", "w"), sort_keys=False)
try:
    hb = eh(b); print("  effects_hash moves when last effect moves to aa_more_effects.yaml:", ha != hb, f"({len(defs)} defs; moved {moved[0]['id']})")
except Exception as e:
    print("  effects move variant:", type(e).__name__, short(str(e), 300))
# docstring
import townlet.training.checkpoint_utils as cu
print("  stale docstring 'four per-level' present:", "four per-level" in (cu.assert_checkpoint_identity.__doc__ or ""))
