import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects")
from packlib import *
import torch

def p_readonly_tick():
    d = make_pack("readonly", [effect("ro", on_tick=[{"modify": "vfs.locked", "value": "vfs.locked + 1.0"}])], [var("locked", writable=())])
    u, env = compile_env(d)
    print("  compiled OK (no refusal) for on_tick write to writable_by: [] variable")
    spawn(env, "ro"); print("  spawned OK")
    wait(env); print("  stepped OK, locked =", env.vfs_registry.get("locked", reader="engine").tolist())
run("A1 readonly var written from on_tick: compile? step?", p_readonly_tick)

def p_readonly_spawn():
    d = make_pack("readonly_spawn", [effect("ro", on_spawn=[{"modify": "bar.health", "value": "bar.health - 0.5"}, {"modify": "vfs.locked", "value": "vfs.locked + 1.0"}])], [var("locked", writable=())])
    u, env = compile_env(d); h0 = env.meters[:, env.meter_name_to_index["health"]].clone()
    try:
        spawn(env, "ro")
    except PermissionError as e:
        print("  spawn refused:", str(e)[:120])
    print("  health after refused spawn (was", h0.tolist(), "):", env.meters[:, env.meter_name_to_index["health"]].tolist(), "effects:", len(env.effect_manager.get_all_active_effects()))
run("A2 readonly var in on_spawn after a bar write: rolled back?", p_readonly_spawn)

def p_delay_carveout():
    d = make_pack("delay_ro", [effect("ro", on_spawn=[{"modify": "bar.health", "value": "bar.health - 0.5"}, {"delay": "1", "do": [{"modify": "vfs.locked", "value": "vfs.locked + 1.0"}]}])], [var("locked", writable=())])
    u, env = compile_env(d)
    spawn(env, "ro"); print("  spawn admitted; health:", env.meters[:, env.meter_name_to_index["health"]].tolist(), "pending:", {k: len(v) for k, v in env.effect_manager.scheduler.pending.items()})
    wait(env); print("  step 1 OK")
    wait(env); print("  step 2 OK")
run("A3 delay carve-out: denied write scheduled inside on_spawn", p_delay_carveout)

def p_for_each_as():
    d = make_pack("foreach_as", [effect("fe", on_tick=[{"for_each": "all_agents", "as": "a", "do": [{"modify": "target.bar.health", "value": "target.bar.health - 0.1 * a"}]}])])
    compile_env(d)
run("B1 for_each `as: a` referenced in body", p_for_each_as)

def p_for_each_target():
    d = make_pack("foreach_t", [effect("fe", on_tick=[{"for_each": "all_agents", "as": "a", "do": [{"modify": "target.bar.health", "value": "target.bar.health - 0.1"}]}])])
    u, env = compile_env(d, 3); spawn(env, "fe", target=1); wait(env)
    print("  health after one tick (expect all -0.1):", env.meters[:, env.meter_name_to_index["health"]].tolist())
run("B2 for_each all_agents with target.bar write works end-to-end", p_for_each_target)

def p_nearby():
    d = make_pack("nearby", [effect("fe", on_tick=[{"for_each": "nearby_agents", "as": "a", "do": [{"modify": "target.bar.health", "value": "target.bar.health - 0.1"}]}])])
    u, env = compile_env(d, 3); print("  compiled OK"); spawn(env, "fe", target=1); print("  spawned OK"); wait(env); print("  stepped OK")
run("B3 for_each nearby_agents from YAML (no radius field exists)", p_nearby)

def p_active_effects():
    d = make_pack("activefx", [effect("fe", on_tick=[{"for_each": "active_effects", "as": "a", "do": [{"modify": "target.bar.health", "value": "target.bar.health - 0.1"}]}]), effect("other", duration=5)])
    u, env = compile_env(d, 3); spawn(env, "fe", target=1); spawn(env, "other", target=1); wait(env)
    print("  health after tick (fe on agent 1 with 2 active effects; expect ???):", env.meters[:, env.meter_name_to_index["health"]].tolist())
run("B4 for_each active_effects: what does it iterate", p_active_effects)

def p_temporal():
    for expr in ["temporal.tick", "vfs.tick", "tick"]:
        d = make_pack("temporal_" + expr.replace(".", "_"), [effect("t", on_tick=[{"modify": "bar.health", "value": f"bar.health - 0.001 * {expr}"}])])
        try:
            u, env = compile_env(d); spawn(env, "t"); wait(env); wait(env)
            print(f"  {expr}: compiled+ran OK; health={env.meters[:, env.meter_name_to_index['health']].tolist()}")
        except Exception as e:
            print(f"  {expr}: {type(e).__name__}: " + " // ".join(m.strip()[:200] for m in str(e).splitlines()[:3]))
run("C temporal access from an effect", p_temporal)

def p_spatial():
    for expr in ['distance_to_affordance("FOOD")', 'in_range("FOOD", 2.0)', 'target.position']:
        val = f"bar.health - 0.01 * {expr}" if "range" not in expr else f"bar.health - (if {expr} then 0.1 else 0.0)"
        d = make_pack("spatial_" + str(abs(hash(expr)))[:6], [effect("s", on_tick=[{"modify": "bar.health", "value": val}])])
        try:
            u, env = compile_env(d); spawn(env, "s"); wait(env)
            print(f"  {expr}: compiled+ran OK; health={env.meters[:, env.meter_name_to_index['health']].tolist()}")
        except Exception as e:
            print(f"  {expr}: {type(e).__name__}: " + " // ".join(m.strip()[:200] for m in str(e).splitlines()[:3]))
run("D spatial access from an effect", p_spatial)
