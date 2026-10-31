"""Area 4: meter clamp at phase commit (D3)."""
import torch, yaml
from harness import *  # noqa
from harness import make_pack, decl, write, rule, rwrite, try_compile, build_env, step, meter, reg, short, load_yaml, dump_yaml
from townlet.vfs.transition_graph import DEFAULT_TRANSITION_PHASES, DEFAULT_LAST_ACTION_PHASE
print("townlet at", __import__("townlet").__file__)
L1 = "L1_full_observability"
phases = list(DEFAULT_TRANSITION_PHASES); clamp_idx = phases.index("clamp_and_validate")
action_phases = phases[: phases.index(DEFAULT_LAST_ACTION_PHASE) + 1]
print("phases:", phases); print("action phases:", action_phases)

def run(pk, n=1, act="WAIT", steps=1):
    u, err = try_compile(pk)
    if u is None: return None, "REFUSED " + short(err[err.find(" - ") + 3:].replace("\n", " "), 200)
    try:
        env = build_env(u, n)
        for _ in range(steps): step(env, act)
        return env, None
    except Exception as ex:
        return None, f"RUNTIME {type(ex).__name__}: {short(str(ex), 200)}"

print("\n### rule +5.0 (overwrite 7.0) on satiation at every phase before clamp_and_validate; cascade leak signature = dhealth")
for ph in phases[:clamp_idx]:
    for label, w in [("additive +5", rwrite("bar.satiation", "5.0")), ("overwrite 7", rwrite("bar.satiation", "7.0", composition="overwrite")), ("additive -5", rwrite("bar.satiation", "-5.0"))]:
        env, err = run(make_pack("cl", rules=[rule("r", [w], phase=ph)]))
        if env is None: print(f"  {ph:28} {label:14} {err}"); continue
        print(f"  {ph:28} {label:14} satiation={float(meter(env,'satiation')[0]):.4f} health={float(meter(env,'health')[0]):.4f} energy={float(meter(env,'energy')[0]):.4f}")
print("\n### action write (REST) +5 / -5 on satiation at every action phase")
for ph in action_phases:
    for label, expr in [("+5", "5.0"), ("-5", "-5.0")]:
        def actions(a, ph=ph, expr=expr):
            for ca in a["custom_actions"]:
                if ca["name"] == "REST": ca["writes"] = [write("bar.satiation", expr, phase=ph)]
        env, err = run(make_pack("cla", actions=actions), act="REST")
        if env is None: print(f"  {ph:28} {label:4} {err}"); continue
        print(f"  {ph:28} {label:4} satiation={float(meter(env,'satiation')[0]):.4f} health={float(meter(env,'health')[0]):.4f} energy={float(meter(env,'energy')[0]):.4f}")

print("\n### composition within one phase is clamped once (two rules -1.5 and +0.8 from 1.0: composed->0.3, clamp-each->0.8)")
env, err = run(make_pack("comp", rules=[rule("ra", [rwrite("bar.satiation", "-1.5")], phase="ingest_actions"), rule("rb", [rwrite("bar.satiation", "0.8")], phase="ingest_actions")]))
print("  satiation after 1 step:", err or f"{float(meter(env,'satiation')[0]):.4f} (passive depletion also applies later in the tick)")
env, err = run(make_pack("comp2", rules=[rule("ra", [rwrite("bar.satiation", "-1.5"), rwrite("bar.satiation", "0.8")], phase="apply_transition_rules")]))
print("  two writes in one rule, at apply_transition_rules:", err or f"{float(meter(env,'satiation')[0]):.4f}")
# action write then rule in same phase: action commits first; rule reads the committed (clamped?) value
def actions(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["writes"] = [write("bar.satiation", "5.0", phase="ingest_actions")]
env, err = run(make_pack("comp3", actions=actions, rules=[rule("rd", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="ingest_actions")]), act="REST")
envc, _ = run(make_pack("comp3c", actions=actions), act="REST"); print("  control (REST, no rule): dmood =", f"{float(meter(envc,'mood')[0]) - 1.0:+.5f}")
envd, _ = run(make_pack("comp3d", actions=actions, rules=[rule("rd", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="apply_action_effects")]), act="REST"); print("  action +5 at ingest, rule at a LATER phase (apply_action_effects): dmood =", f"{float(meter(envd,'mood')[0]) - 1.0:+.5f}")
print("  action +5 then rule mood += satiation*0.01 in the same phase: dmood =", err or f"{float(meter(env,'mood')[0]) - 1.0:+.5f} (0.01 if the rule reads the clamped 1.0; 0.06 if raw 6.0)")

print("\n### asymmetric bounds (money [0, 999999]) and a meter with min > 0")
for label, w in [("money += 2e6", rwrite("bar.money", "2000000.0")), ("money -= 5e6", rwrite("bar.money", "-5000000.0")), ("money := -3", rwrite("bar.money", "-3.0", composition="overwrite"))]:
    env, err = run(make_pack("asym", rules=[rule("r", [w], phase="ingest_actions")]))
    print(f"  {label:14}:", err or f"money={float(meter(env,'money')[0]):.1f}")
def bars_min(b):
    for m in b["meters"]:
        if m["name"] == "satiation": m["bounds"]["min"] = 0.2; m["bounds"]["lethal_min"] = True
env, err = run(make_pack("minpos", bars=bars_min, rules=[rule("r", [rwrite("bar.satiation", "-0.95")], phase="ingest_actions")]))
print("  satiation bounds [0.2,1] lethal_min, rule -0.95 at ingest_actions:", err or f"satiation={float(meter(env,'satiation')[0]):.4f} done={env.dones.tolist()}")
env, err = run(make_pack("minpos2", bars=bars_min, rules=[rule("r", [rwrite("bar.satiation", "0.25", composition="overwrite")], phase="ingest_actions")]))
print("  same bounds, overwrite 0.25 (above min):", err or f"satiation={float(meter(env,'satiation')[0]):.4f} done={env.dones.tolist()}")

print("\n### lethal check still fires when a write drives a meter to its minimum")
for ph in ["ingest_actions", "apply_passive_depletion", "apply_threshold_cascades", "apply_transition_rules"]:
    for label, w in [("health := 0", rwrite("bar.health", "0.0", composition="overwrite")), ("health -= 5", rwrite("bar.health", "-5.0")), ("health -= 1.0 exact", rwrite("bar.health", "-1.0"))]:
        env, err = run(make_pack("leth", rules=[rule("r", [w], phase=ph)]))
        print(f"  {ph:26} {label:20}:", err or f"health={float(meter(env,'health')[0]):.4f} done={env.dones.tolist()}")
def actions(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["writes"] = [write("bar.health", "-5.0", phase="ingest_actions")]
env, err = run(make_pack("leth_a", actions=actions), act="REST", n=2)
print("  action write health -= 5 at ingest_actions:", err or f"health={meter(env,'health').tolist()} done={env.dones.tolist()}")
# per-world kill
env, err = run(make_pack("leth_w", rules=[rule("r", [rwrite("bar.health", "-5.0", condition="agent_id == 1")], phase="apply_transition_rules")]), n=3)
print("  per-world kill (agent_id==1):", err or f"done={env.dones.tolist()}")

print("\n### effects writing bars: unclamped in-tick? (effect on_tick satiation -5; rule at apply_transition_rules reads it)")
def affordances(payload):
    for aff in payload["affordances"]:
        if aff["name"] == "EAT":
            aff["interactions"]["on_start"].append({"spawn_effect": "e1", "target": "target", "intensity": "1.0"})
def effects(e):
    e["effect_definitions"] = [{"id": "e1", "scope": "agent", "duration": 4, "reapply_policy": "renew", "observable": False, "on_spawn": [],
                                "on_tick": [{"modify": "bar.satiation", "value": "bar.satiation - 5.0"}], "on_despawn": [], "on_interrupt": []}]
    e["max_active_effects"] = {"global": 0, "agent": 2, "item": 0, "affordance": 0}
pk = make_pack("eff", affordances=affordances, effects=effects, rules=[rule("rd", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="apply_transition_rules")])
u, err = try_compile(pk)
if u is None: print("  compile:", short(err, 300))
else:
    env = build_env(u, 1); env.positions[0] = env.affordances["EAT"].clone(); env.meters[:, env.meter_name_to_index["money"]] = 100.0
    m0 = float(meter(env, "mood")[0]); step(env, "INTERACT"); m1 = float(meter(env, "mood")[0]); s1 = float(meter(env, "satiation")[0])
    print(f"  after INTERACT (effect spawns): satiation={s1:.4f} dmood={m1-m0:+.5f}; effects active: {len(list(env.effect_manager.effects_in_world(0)))}")
    m1 = float(meter(env, "mood")[0]); step(env, "WAIT"); m2 = float(meter(env, "mood")[0]); s2 = float(meter(env, "satiation")[0])
    print(f"  next tick (effect on_tick -5): satiation={s2:.4f} dmood={m2-m1:+.5f}  (-0.04 => rule read the raw -4; ~0.0 => clamped)")
