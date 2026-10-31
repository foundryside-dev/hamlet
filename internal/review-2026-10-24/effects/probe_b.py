import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects")
from packlib import *
import torch
H = lambda env: env.meters[:, env.meter_name_to_index["health"]].tolist()

def p_if_any():
    d = make_pack("ifany", [effect("c", on_tick=[{"if": "bar.health < 0.5", "then": [{"modify": "bar.energy", "value": "bar.energy - 0.5"}], "else": []}])])
    u, env = compile_env(d, 3); env.meters[1, env.meter_name_to_index["health"]] = 0.1
    spawn(env, "c"); wait(env)
    print("  health:", H(env), "energy (only agent 1 low; expect only agent 1 -0.5):", env.meters[:, env.meter_name_to_index["energy"]].tolist())
run("F `if` command on a per-agent condition", p_if_any)

def p_capacity(observable):
    d = make_pack(f"cap_{observable}", [effect("hb", duration=10, policy="stack", observable=observable)], budget={"global": 0, "agent": 2, "item": 0, "affordance": 0})
    u, env = compile_env(d)
    for i in range(3):
        spawn(env, "hb", target=0); print(f"  spawn {i+1} OK; active={len(env.effect_manager.get_all_active_effects())}")
    wait(env); print("  step OK")
run("G1 capacity: 3 stacked observable effects, budget agent:2", lambda: p_capacity(True))
run("G2 capacity: same but observable: false", lambda: p_capacity(False))

def p_presence_clear():
    d = make_pack("presence", [effect("hb", duration=2, policy="stack", observable=True)], budget={"global": 0, "agent": 2, "item": 0, "affordance": 0})
    u, env = compile_env(d)
    spec = u.get_level("L0_effects").token_spec
    rows = [(t, s, a, b) for (t, s, a, b) in spec.row_layout() if t == "effect"]
    print("  effect rows:", rows)
    spawn(env, "hb", target=0)
    obs, *_ = wait(env); print("  tick1 effect row agent0:", obs[0, rows[0][2]:rows[0][3]].tolist())
    obs, *_ = wait(env); print("  tick2 (despawned?) active:", len(env.effect_manager.get_all_active_effects()), "row:", obs[0, rows[0][2]:rows[0][3]].tolist())
    obs, *_ = wait(env); print("  tick3 row:", obs[0, rows[0][2]:rows[0][3]].tolist())
run("G3 effect token presence/payload cleared after despawn", p_presence_clear)

def p_same_var():
    d = make_pack("samevar", [effect("a", on_tick=[{"modify": "bar.health", "value": "0.3"}]), effect("b", on_tick=[{"modify": "bar.health", "value": "0.7"}])])
    u, env = compile_env(d); spawn(env, "a"); spawn(env, "b"); wait(env)
    print("  a spawned first (sets 0.3), b second (sets 0.7); health after tick:", H(env))
run("H two effects writing the same bar in one tick", p_same_var)

def p_rebind():
    d = make_pack("rebind", [effect("a", on_tick=[{"modify": "bar.health", "value": "0.3"}]), effect("b", on_tick=[{"modify": "target.bar.health", "value": "target.bar.health + 0.1"}])])
    u, env = compile_env(d); spawn(env, "a"); spawn(env, "b", target=1); wait(env)
    print("  health after tick:", H(env))
run("I scalar modify then per-target modify same tick (rebind hazard)", p_rebind)

def p_scalar_rebind_alias():
    d = make_pack("rebind2", [effect("a", on_tick=[{"modify": "bar.health", "value": "0.3"}])])
    u, env = compile_env(d); spawn(env, "a"); wait(env)
    print("  meters health after tick (expect [0.3,0.3]):", H(env))
run("I2 scalar modify of bar writes back to meters?", p_scalar_rebind_alias)

def p_affordance_scope():
    d = make_pack("affscope", [effect("af", scope="affordance", on_tick=[{"modify": "target.bar.health", "value": "target.bar.health - 0.1"}])])
    u, env = compile_env(d, 3); spawn(env, "af", target=1); wait(env)
    print("  affordance-scoped effect spawned on 'affordance 1'; health per agent:", H(env), "stores:", dict(env.effect_manager.affordance_effects).keys())
run("K affordance-scoped effect: who does target.bar.* hit", p_affordance_scope)

def p_global_target():
    d = make_pack("globtarget", [effect("g", scope="global", on_tick=[{"modify": "target.bar.health", "value": "target.bar.health - 0.1"}])])
    u, env = compile_env(d, 3); spawn(env, "g", target=0); wait(env)
    print("  global effect target.bar.health; health:", H(env))
run("K2 global-scoped effect using target.bar.*", p_global_target)

def p_pair_var():
    d = make_pack("pairvar", [effect("p", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.1 * vfs.trust"}])], [var("trust", scope="pair")])
    compile_env(d)
run("L pair-scoped variable referenced from an effect", p_pair_var)

def p_target_vfs():
    d = make_pack("tvfs", [effect("tv", on_tick=[{"modify": "target.vfs.score", "value": "target.vfs.score + 1.0"}])], [var("score")])
    u, env = compile_env(d, 3); spawn(env, "tv", target=1); wait(env)
    print("  target.vfs.score after effect on agent 1:", env.vfs_registry.get("score", reader="engine").tolist())
run("N1 target.vfs.X from agent-scoped effect writes one agent?", p_target_vfs)

def p_self_vfs():
    d = make_pack("svfs", [effect("sv", on_tick=[{"modify": "self.vfs.score", "value": "self.vfs.score + 1.0"}])], [var("score")])
    compile_env(d)
run("N2 self.vfs.X on an agent variable from an effect", p_self_vfs)

def p_bare_vfs():
    d = make_pack("bvfs", [effect("bv", on_tick=[{"modify": "vfs.score", "value": "vfs.score + 1.0"}])], [var("score")])
    u, env = compile_env(d, 3); spawn(env, "bv", target=1); wait(env)
    print("  bare vfs.score after effect attached to agent 1:", env.vfs_registry.get("score", reader="engine").tolist())
run("N3 bare vfs.X from an agent-scoped effect", p_bare_vfs)

def p_str_ternary():
    d = make_pack("strtern", [effect("st", on_tick=[{"modify": "bar.health", "value": 'bar.health - (if (if bar.health > 0.5 then "a" else "b") == "a" then 0.1 else 0.0)'}])])
    u, env = compile_env(d); spawn(env, "st"); wait(env); print("  ran; health:", H(env))
run("P string ternary from expressions.md evaluates?", p_str_ternary)

def p_mean_int():
    d = make_pack("meanint", [effect("mi", on_tick=[{"modify": "vfs.cnt", "value": "mean(vfs.cnt, vfs.cnt)"}])], [var("cnt", type="int", initial=1)])
    u, env = compile_env(d); print("  compiled OK"); spawn(env, "mi"); wait(env); print("  ran")
run("O mean(int,int) compiles then crashes at tick?", p_mean_int)

def p_uniform_scalar():
    d = make_pack("unif", [effect("un", on_tick=[{"modify": "bar.health", "value": "uniform(0.0, 1.0)"}])])
    u, env = compile_env(d, 4); spawn(env, "un"); wait(env); print("  per-agent health after uniform():", H(env))
run("Q uniform() per-agent or shared", p_uniform_scalar)

def p_budget_zero_scope():
    d = make_pack("budget0", [effect("g", scope="global")], budget={"global": 0, "agent": 0, "item": 0, "affordance": 0})
    u, env = compile_env(d); spawn(env, "g"); wait(env); print("  global effect with global budget 0: spawned+stepped OK, active:", len(env.effect_manager.get_all_active_effects()))
run("R scope budget 0 but effect declared observable", p_budget_zero_scope)
