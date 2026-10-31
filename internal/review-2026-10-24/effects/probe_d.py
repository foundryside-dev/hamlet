import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects")
from packlib import *
import torch
from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType

def p_rebind_min():
    schema = {"bar.x": "float", "target.bar.x": "float"}
    c = CommandCompiler(schema)
    a = c.compile_command(CommandNode(type=CommandType.MODIFY, path="bar.x", value_expr="0.3"))
    b = c.compile_command(CommandNode(type=CommandType.MODIFY, path="target.bar.x", value_expr="target.bar.x + 0.1"))
    bars = {"x": torch.tensor([1.0, 1.0, 1.0])}
    ctx = ExecutionContext(bars=bars, target_index=1)
    ex = CommandExecutor(); ex.execute(a, ctx)
    print("  after scalar modify: bars.x =", bars["x"].tolist(), "stride:", bars["x"].stride(), "is_contiguous:", bars["x"].is_contiguous())
    ex.execute(b, ctx)
    print("  after target.bar.x += 0.1 on agent 1 only:", bars["x"].tolist())
run("I3 minimal: scalar modify rebinds bar to a stride-0 view; next indexed write hits every agent", p_rebind_min)

def p_intensity_shadow():
    d = make_pack("intens", [effect("i", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.1 * intensity"}])], [var("intensity", initial=5.0)])
    u, env = compile_env(d); spawn(env, "i", intensity=1.0); wait(env)
    print("  registry var 'intensity'=5.0, spawn intensity=1.0; health (expect 0.9 if effect intensity wins):", env.meters[:, env.meter_name_to_index['health']].tolist())
run("U registry variable named `intensity` shadows the effect's intensity?", p_intensity_shadow)

def p_elapsed_dtype():
    d = make_pack("elapsed", [effect("e", on_tick=[{"modify": "vfs.score", "value": "elapsed_ticks"}])], [var("score")])
    u, env = compile_env(d); spawn(env, "e"); wait(env); wait(env)
    t = env.vfs_registry.get("score", reader="engine"); print("  score tensor after assigning elapsed_ticks:", t.dtype, t.tolist())
run("V elapsed_ticks declared float, injected int64 — written to a float var", p_elapsed_dtype)

def p_nested_rollback():
    # README: nested refusal rolls back immediately. Inject a runtime PermissionError on the inner effect's write.
    d = make_pack("nested", [
        effect("outer", on_spawn=[{"modify": "bar.health", "value": "bar.health - 0.5"}, {"spawn_effect": "inner", "target": "target", "intensity": 1.0}]),
        effect("inner", on_spawn=[{"modify": "bar.energy", "value": "bar.energy - 0.5"}, {"modify": "vfs.score", "value": "vfs.score + 1.0"}]),
    ], [var("score")])
    u, env = compile_env(d)
    reg = env.vfs_registry; orig = reg.authorize_write
    def deny(variable_id, *, writer):
        if variable_id == "score": raise PermissionError("injected denial for score")
        return orig(variable_id, writer=writer)
    reg.authorize_write = deny
    h0 = env.meters[:, 1].clone()
    try:
        spawn(env, "outer")
    except PermissionError as e:
        print("  PermissionError propagated:", str(e)[:60])
    print("  health/energy after denied cascade (expect unchanged 1.0):", env.meters[:, env.meter_name_to_index['health']].tolist(), env.meters[:, env.meter_name_to_index['energy']].tolist(), "active effects:", len(env.effect_manager.get_all_active_effects()), "next_instance_id:", env.effect_manager.next_instance_id)
run("W nested refusal rolls back immediately (README PR #44)", p_nested_rollback)

def p_time_in_window():
    from townlet.world.expression.functions import FUNCTION_SPECS
    from townlet.world.expression.context import ExecutionContext as EC
    f = FUNCTION_SPECS["time_in_window"].eval_fn
    ctx = EC(bars={}, vfs={}, affordances={}, temporal={})
    print("  time_in_window(tick=25, 1, 3) with a 24-tick period hardcoded:", f([torch.tensor(25.0), torch.tensor(1.0), torch.tensor(3.0)], ctx, []).item(), "(day_length is authored per pack; function ignores it)")
run("X time_in_window hardcodes a 24-tick day", p_time_in_window)

def p_switch_typo():
    d = make_pack("switchtypo", [effect("sw", on_tick=[{"switch": "1", "cases": [{"when": "1", "doo": [{"modify": "bar.health", "value": "0.0"}]}], "default": [{"modify": "bar.health", "value": "0.5"}]}])])
    u, env = compile_env(d); spawn(env, "sw"); wait(env); print("  compiled; case 'doo' typo silently empty → health:", env.meters[:, env.meter_name_to_index['health']].tolist())
run("Y switch case with typo'd key compiles silently", p_switch_typo)

def p_lag0():
    d = make_pack("lag0", [effect("l", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.1 * lag(bar.energy, 0)"}])])
    u, env = compile_env(d); print("  compiled OK (lag in effect)"); spawn(env, "l"); wait(env); print("  ran")
run("Z temporal lag() from an effect (no history on effects context)", p_lag0)
