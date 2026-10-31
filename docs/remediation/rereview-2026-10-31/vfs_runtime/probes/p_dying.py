"""An agent dying mid-step: what its world's rules, effects, history, expressions, tick and observation do on the dying
step and after. Uses the r_iso pack (p_isolation.py build) plus a smaller pack with an affordance-scoped rule and a global effect."""
from common import *  # noqa
import sys
import torch


def kill_next_step(env, w):
    e = env.meter_name_to_index["energy"]
    env.meters[w, e] = 0.005  # passive depletion 0.01 -> 0 -> lethal_min


@probe("D1 dying step and the step after: rules/effects/history/expressions/tick in the dead world (r_iso pack)")
def d1():
    from townlet.universe.compiler import UniverseCompiler
    u = UniverseCompiler().compile(PACKS / "r_iso", primary_level="L0_simple", use_cache=False)
    env = build_env(u, num_agents=3)
    r = env.vfs_registry
    spawn(env, "eg", 1)   # global effect in world 1, duration 2
    spawn(env, "e1", 1)   # agent effect in world 1, duration 3
    step(env, "ADVANCE")
    step(env, "ADVANCE")
    kill_next_step(env, 1)
    before = {k: r.get(k, reader="engine")[1].clone() for k in r.variables}
    obs, rew, dones, info = env.step(acts(env, "ADVANCE"))
    print("  dones after dying step:", dones.tolist(), " newly_terminal:", info["newly_terminal"].tolist())
    dying = {k: r.get(k, reader="engine")[1].clone() for k in r.variables}
    changed = {k: (before[k].tolist(), dying[k].tolist()) for k in before if not torch.equal(before[k], dying[k])}
    print("  world 1 registry changed ON the dying step (expected: rules/writes still apply, entry mask):")
    for k, v in changed.items():
        print(f"     {k}: {v[0]} -> {v[1]}")
    obs_dead = obs[1].clone()
    frozen = {k: r.get(k, reader="engine")[1].clone() for k in r.variables}
    obs2, rew2, dones2, _ = env.step(acts(env, "ADVANCE"))
    after = {k: r.get(k, reader="engine")[1].clone() for k in r.variables}
    moved = {k: (frozen[k].tolist(), after[k].tolist()) for k in frozen if not torch.equal(frozen[k], after[k])}
    print("  world 1 registry changed on the step AFTER death (expected: only tick-driven state):")
    for k, v in moved.items():
        print(f"     {k}: {v[0]} -> {v[1]}")
    print("  dead world obs changed after death?", not torch.equal(obs_dead, obs2[1]), " reward:", rew2[1].item())
    print("  dead world effects:", env.effect_manager.effects_in_world(1))
    print("  live world 0 g, av:", r.get("g", reader="engine")[0].item(), r.get("av", reader="engine")[0].item())
    # history frozen? lagged = lag(av, 2) + delta(bar.energy); in dead world av frozen -> lagged frozen after the ring stops
    for _ in range(3):
        step(env, "ADVANCE")
    print("  world 1 after 3 more steps: lagged", r.get("lagged", reader="engine")[1].item(), "acc", r.get("acc", reader="engine")[1].item(), "gexp", r.get("gexp", reader="engine")[1].item(), "tick", r.get("tick", reader="engine")[1].item())


@probe("D2 affordance-scoped rule row and claim in a dying world; global effect in a dead world writes nothing")
def d2():
    decls = [decl("aff_v", scope="affordance", initial_value=0.0), decl("g", scope="global", initial_value=0.0),
             decl("cnt", scope="global", initial_value=0.0, expression="tick * 1.0")]
    rules = [rule("ra", [rwrite("aff_v", "1.0")]), rule("rg", [rwrite("g", "1.0")])]
    effects = [effect("eg", [{"modify": "g", "value": "g + 100.0"}], scope="global", duration=6)]
    u = compile_sea("dying2", decls=decls, rules=rules, effects=effects)
    env = build_env(u, num_agents=3)
    r = env.vfs_registry
    spawn(env, "eg", 2)
    step(env, "WAIT")
    kill_next_step(env, 2)
    step(env, "WAIT")
    print("  dones:", env.dones.tolist())
    g_dying, a_dying = r.get("g", reader="engine").tolist(), r.get("aff_v", reader="engine")[:, 0].tolist()
    step(env, "WAIT"); step(env, "WAIT")
    print("  g on dying step", g_dying, "-> two steps later", r.get("g", reader="engine").tolist(), " (world 2 frozen after death)")
    print("  aff_v[:,0] on dying step", a_dying, "-> two steps later", r.get("aff_v", reader="engine")[:, 0].tolist())
    print("  cnt (tick expression) per world:", r.get("cnt", reader="engine").tolist(), " tick:", r.get("tick", reader="engine").tolist())
    print("  effects in dead world 2:", [(e.effect_id, e.elapsed_ticks, e.duration_remaining) for e in env.effect_manager.effects_in_world(2)])


if __name__ == "__main__":
    which = sys.argv[1:] or ["d1", "d2"]
    for name in which:
        globals()[name]()
