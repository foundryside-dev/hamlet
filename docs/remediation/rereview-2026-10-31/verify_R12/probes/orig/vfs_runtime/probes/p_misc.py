"""Hash movement on hidden shape/initializer (V12); rule ordering contract (priority = declaration order?);
priority_write composition; same-phase composition of two rules on one target; item_ref persistent across reset."""
from common import *  # noqa
import sys
import torch


@probe("M1 vfs_hash moves on hidden tensor shape / initial_value_mode / initial_value (V12)")
def m1():
    def lv(u):
        return u.get_level("L0_simple").vfs_hash
    base = compile_sea("m1a", decls=[decl("t", type="tensor2d", shape=[2, 2], initial_value_mode="zeros")])
    shp = compile_sea("m1b", decls=[decl("t", type="tensor2d", shape=[4, 4], initial_value_mode="zeros")])
    ones = compile_sea("m1c", decls=[decl("t", type="tensor2d", shape=[2, 2], initial_value_mode="ones")])
    lit = compile_sea("m1d", decls=[decl("t", type="tensor2d", shape=[2, 2], initial_value=[[1.0, 0.0], [0.0, 1.0]])])
    v1 = compile_sea("m1e", decls=[decl("h", initial_value=1.0)])
    v2 = compile_sea("m1f", decls=[decl("h", initial_value=2.0)])
    print("  shape [2,2] vs [4,4] moves vfs_hash:", lv(base) != lv(shp))
    print("  zeros vs ones moves vfs_hash:", lv(base) != lv(ones))
    print("  mode zeros vs literal eye moves vfs_hash:", lv(base) != lv(lit))
    print("  hidden scalar initial 1.0 vs 2.0 moves vfs_hash:", lv(v1) != lv(v2))


@probe("M2 rule ordering: two rules, same phase, same target, overwrite; declared order r_b then r_a")
def m2():
    decls = [decl("x", initial_value=0.0)]
    u = compile_sea("m2", decls=decls, rules=[rule("r_b", [rwrite("x", "2.0", composition="overwrite")]), rule("r_a", [rwrite("x", "1.0", composition="overwrite")])])
    env = build_env(u, num_agents=1)
    step(env, "WAIT")
    print("  x after step:", reg(env, "x").tolist(), " (doc: priority defaults to declaration order -> later rule r_a wins -> 1.0)")
    print("  compiled order:", [(r.rule_id, r.priority) for r in env.vtc_transition_schedule.transition_rule_program.rules])
    u = compile_sea("m2b", decls=decls, rules=[rule("r_b", [rwrite("x", "2.0", composition="priority_write")]), rule("r_a", [rwrite("x", "1.0", composition="priority_write")])])
    env = build_env(u, num_agents=1)
    step(env, "WAIT")
    print("  priority_write x:", reg(env, "x").tolist(), [(r.rule_id, r.priority) for r in env.vtc_transition_schedule.transition_rule_program.rules])
    # two additive rules compose within the phase; a rule reading x sees phase-entry snapshot
    u = compile_sea("m2c", decls=decls + [decl("y", initial_value=0.0)], rules=[rule("r1", [rwrite("x", "1.0")]), rule("r2", [rwrite("x", "1.0")]), rule("r3", [rwrite("y", "x", composition="overwrite")])])
    env = build_env(u, num_agents=1)
    step(env, "WAIT"); step(env, "WAIT")
    print("  x after 2 steps (two additive rules):", reg(env, "x").tolist(), " y (reads phase-entry x):", reg(env, "y").tolist())


@probe("M3 persistent item_ref across reset points at a re-spawned row; persistent agent var with lag at episode 2")
def m3():
    from harness import make_pack_from, edit_yaml, REPO
    ITEMS = REPO / "configs" / "test" / "items_smoke"

    def mutate(dest):
        def vars_(p):
            p["variables"]["declarations"].append(
                {"id": "held", "readable_by": ["engine", "agent"], "writable_by": ["engine"], "scope": "agent", "type": "item_ref", "lifetime": "persistent",
                 "semantic_type": "custom", "exposed_to": [], "initial_value": None})
        edit_yaml(dest / "variables.yaml", vars_)
    pack = make_pack_from("r_m3", ITEMS, mutate)
    u = compile_pack(pack, level="L0_smoke")
    env = build_env(u, num_agents=2, level="L0_smoke")
    r = env.vfs_registry
    r.set("held", torch.tensor([3, 13 + 3]), writer="engine")  # row 3 of world 0, row 3 of world 1 (items_per_world = 13)
    print("  items_per_world", env.items_per_world, "held", r.get("held", reader="engine").tolist(), "profile at row 3:", r.get_item_profile_for_index(3))
    env.reset()
    print("  after reset held", r.get("held", reader="engine").tolist(), "profile at row 3 now:", r.get_item_profile_for_index(3), "(ref survives, row re-populated by the new episode's spawn)")




@probe("M4 for_each all_agents in an agent/global effect: does it write other worlds' rows?")
def m4():
    decls = [decl("av", initial_value=0.0), decl("gv", scope="global", initial_value=0.0)]
    for scope in ("agent", "global"):
        u = try_compile(f"{scope} effect for_each all_agents modify av", lambda: compile_sea(f"m4_{scope}", decls=decls, effects=[effect("e1", [{"for_each": "all_agents", "do": [{"modify": "av", "value": "av + 1.0"}, {"modify": "gv", "value": "gv + 1.0"}]}], scope=scope)]))
        if u is None:
            continue
        env = build_env(u, num_agents=3)
        spawn(env, "e1", 1)
        step(env, "WAIT")
        print(f"   {scope} effect in world 1: av =", reg(env, "av").tolist(), " gv =", reg(env, "gv").tolist(), " (expect only world 1 touched)")


if __name__ == "__main__":
    which = sys.argv[1:] or ["m1", "m2", "m3", "m4"]
    for name in which:
        globals()[name]()
