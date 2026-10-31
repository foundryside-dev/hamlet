"""Item 2: transition rules on meters (authoring A1 fix)."""
import sys, os
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/authoring/probes")
from harness import *  # noqa
import harness, townlet
assert "verify_R12/wt/src" in str(Path(townlet.__file__).resolve()), townlet.__file__
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/meters"); harness.PACKS.mkdir(parents=True, exist_ok=True)
import torch

NIGHT = "tick % 24 >= 18 or tick % 24 < 6"
def night(k): return k % 24 >= 18 or k % 24 < 6

def is_night_decl(): return decl("is_night", scope="global", type="bool", initial_value=False, expression=NIGHT)

@probe("A night hunger: hand model, 4 worlds, 60 steps")
def a():
    p = make_pack("a", variables=lambda v: v["declarations"].append(is_night_decl()),
                  rules=[rule("night_hunger", [rwrite("bar.satiation", "-0.05")], condition="is_night")])
    u, err = try_compile(p)
    if err: print("REFUSED", short(err)); return
    env = build_env(u, 4)
    s = torch.tensor(1.0, dtype=torch.float32)
    maxerr = 0.0; bad = []
    for k in range(60):
        step(env, "WAIT")
        s = s - torch.tensor(0.008, dtype=torch.float32)
        if night(k): s = s + torch.tensor(-0.05, dtype=torch.float32)
        s = s.clamp(0.0, 1.0)
        cur = meter(env, "satiation")
        e = float((cur - s).abs().max()); maxerr = max(maxerr, e)
        if e > 1e-5: bad.append((k, cur.tolist(), float(s)))
        if not torch.equal(cur, cur[0].expand(4)): bad.append(("worlds differ", k, cur.tolist()))
    print("max abs err vs hand model:", maxerr, "bad:", bad[:5])
    print("final", meter(env, "satiation").tolist(), "hand", float(s))

@probe("B dead world gets no rule write; live worlds continue")
def b():
    p = make_pack("b", variables=lambda v: v["declarations"].append(is_night_decl()),
                  rules=[rule("night_hunger", [rwrite("bar.satiation", "-0.05")], condition="is_night")])
    u, err = try_compile(p)
    if err: print("REFUSED", short(err)); return
    env = build_env(u, 4)
    step(env, "WAIT")
    env.meters[2, env.meter_name_to_index["health"]] = 0.0
    obs, r, d, info = step(env, "WAIT")
    print("dones after kill:", d.tolist())
    frozen = meter(env, "satiation").clone()
    for _ in range(5): step(env, "WAIT")
    cur = meter(env, "satiation")
    print("world2 satiation frozen:", float(frozen[2]) == float(cur[2]), float(frozen[2]), float(cur[2]))
    print("live worlds moved:", (cur[[0,1,3]] != frozen[[0,1,3]]).tolist(), "deltas", (cur - frozen).tolist())

def action_pack(name, action_writes, rules_, extra_decls=()):
    def acts(a):
        add_action(a, "POKE", action_writes)
    return make_pack(name, actions=acts, rules=rules_,
                     variables=(lambda v: v["declarations"].extend(list(extra_decls))) if extra_decls else None)

@probe("C priority: action write vs rule on the same meter in the same phase (apply_completion_bonuses)")
def c():
    cases = {
      "overwrite vs overwrite": ([write("bar.satiation", "0.5", composition="overwrite")], [rwrite("bar.satiation", "0.2", composition="overwrite")]),
      "additive vs additive": ([write("bar.satiation", "-0.1")], [rwrite("bar.satiation", "-0.1")]),
      "action overwrite, rule reads meter": ([write("bar.satiation", "0.5", composition="overwrite")], [rwrite("bar.satiation", "bar.satiation * 0.5", composition="overwrite")]),
    }
    for label, (aw, rw) in cases.items():
        p = action_pack("c", aw, [rule("r", rw, phase="apply_completion_bonuses")])
        u, err = try_compile(p)
        if err: print(label, "REFUSED", short(err)); continue
        env = build_env(u, 2)
        before = meter(env, "satiation").clone()
        step(env, ["POKE", "WAIT"])
        print(f"  {label}: POKE world0 -> {meter(env,'satiation')[0]:.4f}  WAIT world1 -> {meter(env,'satiation')[1]:.4f} (start {before.tolist()})")

@probe("D clamp and meter bounds")
def d():
    cases = [
      ("additive +0.5, clamp null @apply_transition_rules", rwrite("bar.satiation", "0.5"), "apply_transition_rules"),
      ("overwrite 7 clamp [0,5] @clamp_and_validate", rwrite("bar.satiation", "7.0", composition="overwrite", clamp=[0.0, 5.0]), "clamp_and_validate"),
      ("overwrite 0.9 clamp [0,0.3] @apply_transition_rules", rwrite("bar.satiation", "0.9", composition="overwrite", clamp=[0.0, 0.3]), "apply_transition_rules"),
      ("additive -5 (below min, non-lethal) @ingest_actions", rwrite("bar.satiation", "-5.0"), "ingest_actions"),
      ("money overwrite 5000 (bounds max 999999)", rwrite("bar.money", "5000.0", composition="overwrite"), "apply_transition_rules"),
      ("money overwrite 2e6 (> max)", rwrite("bar.money", "2000000.0", composition="overwrite"), "apply_transition_rules"),
      ("max composition 0.7 on satiation", rwrite("bar.satiation", "0.7", composition="max"), "apply_transition_rules"),
      ("min composition 0.7 on satiation", rwrite("bar.satiation", "0.7", composition="min"), "apply_transition_rules"),
      ("multiplicative 0.5", rwrite("bar.satiation", "0.5", composition="multiplicative_modifier"), "apply_transition_rules"),
      ("priority_write 0.3", rwrite("bar.satiation", "0.3", composition="priority_write"), "apply_transition_rules"),
      ("composition clamp, clamp [0.2,0.4]", rwrite("bar.satiation", "0.0", composition="clamp", clamp=[0.2, 0.4]), "apply_transition_rules"),
      ("claim_if_free on a meter", rwrite("bar.satiation", "1.0", composition="claim_if_free"), "apply_transition_rules"),
    ]
    for label, w, ph in cases:
        p = make_pack("d", rules=[rule("r", [w], phase=ph)])
        u, err = try_compile(p)
        if err: print(f"  {label}: REFUSED", short(err, 300)); continue
        env = build_env(u, 2)
        step(env, "WAIT")
        m = "money" if "money" in label else "satiation"
        print(f"  {label}: {m} -> {meter(env, m).tolist()}")

@probe("E lethal: rule zeroes health -> done that tick, at several phases")
def e():
    for ph in ["ingest_actions", "apply_completion_bonuses", "apply_passive_depletion", "apply_threshold_cascades", "apply_transition_rules", "clamp_and_validate"]:
        p = make_pack("e", rules=[rule("kill", [rwrite("bar.health", "0.0", composition="overwrite")], phase=ph, condition="tick >= 3")])
        u, err = try_compile(p)
        if err: print(f"  {ph}: REFUSED", short(err, 300)); continue
        env = build_env(u, 2)
        rows = []
        for k in range(5):
            obs, r, dn, info = step(env, "WAIT")
            rows.append((k, round(float(meter(env, "health")[0]), 3), bool(dn[0])))
        print(f"  {ph}: (instant, health, done) {rows}")
    # additive below zero -> clamp to 0 -> lethal
    p = make_pack("e2", rules=[rule("kill", [rwrite("bar.health", "-1.5")], condition="tick == 2")])
    u, err = try_compile(p); env = build_env(u, 2); rows = []
    for k in range(4):
        obs, r, dn, info = step(env, "WAIT"); rows.append((k, float(meter(env, "health")[0]), bool(dn[0])))
    print("  additive -1.5 at instant 2:", rows)
    # only world 1 dies (agent-shaped condition)
    p = make_pack("e3", rules=[rule("kill", [rwrite("bar.health", "0.0", composition="overwrite", condition="agent_id == 1")], condition="tick >= 1")])
    u, err = try_compile(p)
    if err: print("  per-world kill REFUSED", short(err, 300))
    else:
        env = build_env(u, 3); rows = []
        for k in range(3):
            obs, r, dn, info = step(env, "WAIT"); rows.append((k, meter(env, "health").tolist(), dn.tolist()))
        print("  per-world kill:", rows)

@probe("F meter rule at every phase")
def f():
    from townlet.vfs.transition_graph import DEFAULT_TRANSITION_PHASES
    base = None
    p0 = make_pack("f0"); u0, _ = try_compile(p0); env0 = build_env(u0, 2); step(env0, "WAIT"); base = float(meter(env0, "satiation")[0])
    print("  control satiation after 1 WAIT:", base)
    for ph in DEFAULT_TRANSITION_PHASES:
        p = make_pack("f", rules=[rule("r", [rwrite("bar.satiation", "-0.1")], phase=ph)])
        u, err = try_compile(p)
        if err: print(f"  {ph}: REFUSED", short(err, 420)); continue
        env = build_env(u, 2); step(env, "WAIT")
        v = float(meter(env, "satiation")[0])
        print(f"  {ph}: {v:.6f} (control-0.1 = {base-0.1:.6f}) {'OK' if abs(v-(base-0.1))<1e-6 else 'MISMATCH'}")
    # above-bound at early phase: +0.5 at ingest_actions from 1.0, then passive depletion
    for ph in ["ingest_actions", "apply_passive_depletion", "apply_threshold_cascades", "apply_transition_rules", "clamp_and_validate"]:
        p = make_pack("f2", rules=[rule("r", [rwrite("bar.satiation", "0.5")], phase=ph)])
        u, err = try_compile(p); env = build_env(u, 2); step(env, "WAIT")
        print(f"  +0.5 at {ph}: satiation {float(meter(env,'satiation')[0]):.6f}")

if __name__ == "__main__":
    for n in (sys.argv[1:] or ["a", "b", "c", "d", "e", "f"]):
        globals()[n]()
