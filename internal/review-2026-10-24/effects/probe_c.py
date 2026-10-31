import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects")
from packlib import *
import torch
H = lambda env: env.meters[:, env.meter_name_to_index["health"]].tolist()
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.context import ExecutionContext as EC
P = ExpressionParser()
def ev(expr, schema, bars):
    ast = P.parse(expr); t = TypeChecker(schema).check(ast)
    v = Evaluator(EC(bars=bars, vfs={}, affordances={}, temporal={})).evaluate(ast)
    return t, v
for expr in ['if bar.health > 0.5 then "healthy" else "injured"', 'bar.health - (if bar.health > 0.5 then 0.1 else 0.0)', "42 / 10", "mean(1, 2)", "7 % 2.5", "2 ** bar.i", "bar.i / 0", "bar.health / 0.0", "-bar.b", "bar.i ** -1", "bar.i % 0"]:
    try:
        t, v = ev(expr, {"bar.health": "float", "bar.i": "int", "bar.b": "bool"}, {"health": torch.tensor([0.2, 0.8]), "i": torch.tensor([2, 3]), "b": torch.tensor([True, False])})
        print(f"  {expr!r}: declared={t} value={v if not isinstance(v, torch.Tensor) else (v.dtype, v.tolist())}")
    except Exception as e:
        print(f"  {expr!r}: {type(e).__name__}: {str(e).splitlines()[0][:140]}")

def p_tick():
    d = make_pack("tick2", [effect("t", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.001 * vfs.tick"}])])
    compile_env(d)
run("C2 vfs.tick full message", p_tick)

def p_dur1():
    d = make_pack("dur1", [effect("d1", duration=1, policy="stack", on_spawn=[{"modify": "bar.health", "value": "bar.health - 0.1"}], on_tick=[{"modify": "bar.health", "value": "bar.health - 0.3"}])])
    u, env = compile_env(d); spawn(env, "d1"); print("  after spawn:", H(env)); wait(env); print("  after 1 tick (doc: only on_spawn executes for duration 1):", H(env), "active:", len(env.effect_manager.get_all_active_effects()))
run("S duration: 1 — does on_tick fire?", p_dur1)

def p_identical():
    d = make_pack("ident", [effect("a", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.1"}]), effect("b", on_tick=[{"modify": "bar.health", "value": "bar.health - 0.1"}])])
    compile_env(d); print("  two effects identical in every declared parameter except id: compiled OK")
run("T indistinguishable effects", p_identical)

def p_budget_obs0():
    d = make_pack("budget_obs0", [effect("g", scope="global", observable=True)], budget={"global": 0, "agent": 0, "item": 0, "affordance": 0})
    u, env = compile_env(d); spawn(env, "g"); obs, *_ = wait(env)
    spec = u.get_level("L0_effects").token_spec
    print("  observable global effect, global budget 0: compiled OK; effect census:", spec.census.get("effect"), "active:", len(env.effect_manager.get_all_active_effects()))
run("R2 observable effect in a zero-budget scope", p_budget_obs0)

def p_mean_pack():
    d = make_pack("meanpack", [effect("m", on_tick=[{"modify": "bar.health", "value": "bar.health * mean(1, 2)"}])])
    u, env = compile_env(d); print("  compiled OK"); spawn(env, "m"); wait(env); print("  ran:", H(env))
run("O2 mean(1,2) in a pack", p_mean_pack)

def p_nearby_runtime():
    # bypass DTO: set radius on the compiled node to see whether the resolver would even be correct
    from townlet.effects.schema import CommandType
    d = make_pack("nearby2", [effect("fe", on_tick=[{"for_each": "nearby_agents", "as": "a", "do": [{"modify": "target.bar.health", "value": "target.bar.health - 0.1"}]}])])
    u, env = compile_env(d, 3)
    node = env.effect_manager.catalog.effects["fe"].on_tick[0]; node.radius = 1.5
    env.positions[0] = torch.tensor([0, 0]); env.positions[1] = torch.tensor([1, 0]); env.positions[2] = torch.tensor([5, 5])
    spawn(env, "fe", target=0); wait(env); print("  with radius hand-set and positions [0,0],[1,0],[5,5] self=0:", H(env))
run("B3b nearby_agents resolver when radius is forced (positions threaded by env.tick?)", p_nearby_runtime)
