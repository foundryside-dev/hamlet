"""Access-policy bypass hunt: engine-only reads, writable_by [] targets from every authored write path, exposure rules,
item-arena bool/ref state through the float32 arena, exposed item state publisher."""
from common import *  # noqa
from harness import make_pack_from, edit_yaml, REPO, ve_rows
import sys
import torch

ITEMS = REPO / "configs" / "test" / "items_smoke"


@probe("A1 engine-only / writable_by [] variables from every authored path")
def a1():
    u = compile_sea("acc0")
    env = build_env(u, num_agents=2)
    try_run("registry.get(hidden_score, reader=agent)", lambda: env.vfs_registry.get("hidden_score", reader="agent"))
    try_run("registry.set(immutable_scale, writer=engine)", lambda: env.vfs_registry.set("immutable_scale", torch.zeros(2), writer="engine"))
    try_run("registry.set(public_state, writer=agent)", lambda: env.vfs_registry.set("public_state", torch.zeros(2), writer="agent"))
    try_compile("effect modify readable_unexposed (writable_by [])", lambda: compile_sea("acc1", effects=[effect("e1", [{"modify": "readable_unexposed", "value": "1.0"}])]))
    try_compile("effect sample store_in readable_unexposed", lambda: compile_sea("acc1s", effects=[effect("e1", [{"sample": "uniform", "params": {"min": 0.0, "max": 1.0}, "store_in": "readable_unexposed"}])]))
    try_compile("rule writes readable_unexposed", lambda: compile_sea("acc2", rules=[rule("r", [rwrite("readable_unexposed", "1.0")])]))
    try_compile("action write readable_unexposed", lambda: compile_sea("acc3", writes=[write("readable_unexposed", "1.0")]))
    try_compile("interaction modify readable_unexposed", lambda: compile_sea("acc4", aff_cmds=[{"modify": "readable_unexposed", "value": "1.0"}]))
    try_compile("interaction modify immutable_scale (global, writable_by [])", lambda: compile_sea("acc5", aff_cmds=[{"modify": "immutable_scale", "value": "1.0"}]))
    try_compile("effect for_each all_agents modify readable_unexposed", lambda: compile_sea("acc6", effects=[effect("e1", [{"for_each": "all_agents", "do": [{"modify": "readable_unexposed", "value": "1.0"}]}])]))
    try_compile("engine-only var exposed_to agent", lambda: compile_sea("acc7", decls=[decl("x", readable=("engine",), exposed=("agent",), normalization={"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True}, initial_value=0.0)]))
    try_compile("expression over engine-only, readable_by [engine, agent], exposed", lambda: compile_sea("acc8", decls=[decl("x", exposed=("agent",), normalization={"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True}, initial_value=0.0, expression="hidden_score")]))


@probe("A2 item arena: bool / item_ref / agent_ref item state through the float32 arena; item var writable_by []; exposed item state")
def a2():
    def mutate(dest):
        def vars_(p):
            p["variables"]["declarations"].extend([
                {"id": "flag", "readable_by": ["engine", "agent"], "writable_by": ["engine"], "scope": "item", "type": "bool", "lifetime": "episode",
                 "semantic_type": "custom", "exposed_to": [], "profile": "food", "initial_value": False},
                {"id": "owner", "readable_by": ["engine", "agent"], "writable_by": ["engine"], "scope": "item", "type": "agent_ref", "lifetime": "episode",
                 "semantic_type": "custom", "exposed_to": [], "profile": "food", "initial_value": None},
                {"id": "locked", "readable_by": ["engine", "agent"], "writable_by": [], "scope": "item", "type": "scalar", "lifetime": "episode",
                 "semantic_type": "custom", "exposed_to": [], "profile": "medical", "initial_value": 1.0},
                {"id": "secret", "readable_by": ["engine"], "writable_by": ["engine"], "scope": "item", "type": "scalar", "lifetime": "episode",
                 "semantic_type": "custom", "exposed_to": [], "profile": "medical", "initial_value": 9.0},
                {"id": "nullref", "readable_by": ["engine", "agent"], "writable_by": ["engine"], "scope": "agent", "type": "agent_ref", "lifetime": "episode",
                 "semantic_type": "custom", "exposed_to": [], "initial_value": None},
            ])
        edit_yaml(dest / "variables.yaml", vars_)

        def items_(p):
            for it in p["items"]["item_types"]:
                if it["id"] == "apple":
                    it["interactions"]["on_pickup"] = [{"modify": "item.owner", "value": "nullref"}]
                    it["interactions"]["on_use"] = [
                        {"if": "item.flag", "then": [{"modify": "bar.energy", "value": "bar.energy + 0.3"}], "else": [{"modify": "item.flag", "value": "true"}]},
                        {"if": "item.flag", "then": [{"modify": "item.freshness", "value": "item.freshness - 1.0"}], "else": []},
                    ]
        edit_yaml(dest / "items.yaml", items_)
    def mutate_lit(dest):
        mutate(dest)
        def items_(p):
            for it in p["items"]["item_types"]:
                if it["id"] == "apple":
                    it["interactions"]["on_pickup"] = [{"modify": "item.owner", "value": "-1"}]
        edit_yaml(dest / "items.yaml", items_)
    try_compile("hook item.owner <- -1 (null literal)", lambda: compile_pack(make_pack_from("r_items_lit", ITEMS, mutate_lit), level="L0_smoke"))
    def mutate_aid(dest):
        mutate(dest)
        def items_(p):
            for it in p["items"]["item_types"]:
                if it["id"] == "apple":
                    it["interactions"]["on_pickup"] = [{"modify": "item.owner", "value": "agent_id"}]
        edit_yaml(dest / "items.yaml", items_)
    try_compile("hook item.owner <- agent_id", lambda: compile_pack(make_pack_from("r_items_aid", ITEMS, mutate_aid), level="L0_smoke"))
    pack = make_pack_from("r_items_bool", ITEMS, mutate)
    u = try_compile("items pack with bool/agent_ref item state in hooks", lambda: compile_pack(pack, level="L0_smoke"))
    if u is None:
        return
    env = build_env(u, num_agents=2, level="L0_smoke")
    names = [a.name for a in env.action_space.actions]
    print("  actions:", names)
    mgr = env.item_manager
    apples = [i for i in mgr.items_in_world(0) if i.item_type == "apple"]
    print("  apples in world 0:", [(a.instance_id, tuple(a.position), a.vfs_index) for a in apples])
    if not apples:
        return
    env.positions[0] = torch.as_tensor(apples[0].position, dtype=env.positions.dtype)
    get = [n for n in names if n.startswith("GET")][0]
    use = [n for n in names if n.startswith("USE")][0]
    a = acts(env, "WAIT"); a[0] = action_index(env, get)
    env.step(a)
    row = apples[0].vfs_index
    r = env.vfs_registry
    print("  after GET: item row", row, "profile", r.get_item_profile_for_index(row), "flag", r.read_item("food", "flag", row, reader="engine"), "owner", r.read_item("food", "owner", row, reader="engine"), "arena row:", r.item_vfs[row].tolist())
    for i in range(3):
        a = acts(env, "WAIT"); a[0] = action_index(env, use)
        e0 = env.meters[0, env.meter_name_to_index["energy"]].item()
        env.step(a)
        print(f"  USE {i}: flag", r.read_item("food", "flag", row, reader="engine"), "freshness", r.read_item("food", "freshness", row, reader="engine"), "energy delta", round(env.meters[0, env.meter_name_to_index['energy']].item() - e0, 3))
    def mutate_not(dest):
        mutate(dest)
        def items_(p):
            for it in p["items"]["item_types"]:
                if it["id"] == "apple":
                    it["interactions"]["on_use"] = [{"if": "not item.flag", "then": [{"modify": "item.flag", "value": "not item.flag"}], "else": []}]
        edit_yaml(dest / "items.yaml", items_)
    u2 = try_compile("apple on_use: if not item.flag (bool item state)", lambda: compile_pack(make_pack_from("r_items_not", ITEMS, mutate_not), level="L0_smoke"))
    if u2 is not None:
        env2 = build_env(u2, num_agents=2, level="L0_smoke")
        ap = [i for i in env2.item_manager.items_in_world(0) if i.item_type == "apple"][0]
        env2.positions[0] = torch.as_tensor(ap.position, dtype=env2.positions.dtype)
        a = acts(env2, "WAIT"); a[0] = action_index(env2, get); env2.step(a)
        a = acts(env2, "WAIT"); a[0] = action_index(env2, use)
        try_run("  USE with `not item.flag`", lambda: (env2.step(a), env2.vfs_registry.item_vfs[ap.vfs_index].tolist())[1])
    def mutate_eff(dest):
        mutate(dest)
        def eff_(p):
            p["effect_definitions"].append({"id": "wear", "scope": "item", "duration": 3, "reapply_policy": "renew", "observable": True,
                                            "on_spawn": [], "on_tick": [{"if": "not item.flag", "then": [{"modify": "item.condition", "value": "item.condition - 1.0"}], "else": []}], "on_despawn": [], "on_interrupt": []})
            p["max_active_effects"]["item"] = max(p["max_active_effects"].get("item", 0), 2)
        edit_yaml(dest / "effects.yaml", eff_)
    try_compile("item-scoped effect: if not item.flag (flag only in food profile -> intersection refusal expected)", lambda: compile_pack(make_pack_from("r_items_eff", ITEMS, mutate_eff), level="L0_smoke"))
    # item var writable_by [] written by a hook
    def mutate2(dest):
        mutate(dest)
        def items_(p):
            for it in p["items"]["item_types"]:
                if it["id"] == "medkit":
                    it["interactions"]["on_use"].append({"modify": "item.locked", "value": "0.0"})
        edit_yaml(dest / "items.yaml", items_)
    try_compile("medkit hook writes item.locked (writable_by [])", lambda: compile_pack(make_pack_from("r_items_locked", ITEMS, mutate2), level="L0_smoke"))
    def mutate3(dest):
        mutate(dest)
        def items_(p):
            for it in p["items"]["item_types"]:
                if it["id"] == "medkit":
                    it["interactions"]["on_use"].append({"modify": "bar.health", "value": "bar.health + item.secret"})
        edit_yaml(dest / "items.yaml", items_)
    try_compile("medkit hook reads item.secret (readable_by [engine]) -- engine pipeline, expected to compile", lambda: compile_pack(make_pack_from("r_items_secret", ITEMS, mutate3), level="L0_smoke"))
    def mutate4(dest):
        mutate(dest)
        def vars_(p):
            for d in p["variables"]["declarations"]:
                if d["id"] == "secret":
                    d["exposed_to"] = ["agent"]; d["normalization"] = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}
        edit_yaml(dest / "variables.yaml", vars_)
    try_compile("item var readable_by [engine] exposed_to [agent]", lambda: compile_pack(make_pack_from("r_items_exp", ITEMS, mutate4), level="L0_smoke"))
    # exposed item state publishes per world only (durability exposed in items_smoke)
    obs = env._get_observations()
    rows = ve_rows(env, obs)
    print("  variable_element rows (all worlds):", {k: v for k, v in rows.items()})


@probe("A3 reference null-test spellings in writes/rules/hooks")
def a3():
    decls = [decl("aref", type="agent_ref", initial_value=None), decl("cnt", initial_value=0.0)]
    try_compile("rule condition aref == -1", lambda: compile_sea("a3a", decls=decls, rules=[rule("r", [rwrite("cnt", "1.0")], condition="aref == -1")]))
    try_compile("rule condition aref == agent_id", lambda: compile_sea("a3b", decls=decls, rules=[rule("r", [rwrite("cnt", "1.0")], condition="aref == agent_id")]))
    try_compile("rule condition aref < 0", lambda: compile_sea("a3c", decls=decls, rules=[rule("r", [rwrite("cnt", "1.0")], condition="aref < 0")]))
    try_compile("action write where(aref == -1, 1.0, 0.0)", lambda: compile_sea("a3d", decls=decls, writes=[write("cnt", "where(aref == -1, 1.0, 0.0)", composition="overwrite")]))
    try_compile("effect if aref == -1", lambda: compile_sea("a3e", decls=decls, effects=[effect("e1", [{"if": "aref == -1", "then": [], "else": []}])]))
    try_compile("rule condition aref == aref2 (ref vs ref)", lambda: compile_sea("a3g", decls=decls + [decl("aref2", type="agent_ref", initial_value=None)], rules=[rule("r", [rwrite("cnt", "1.0")], condition="aref == aref2")]))
    try_compile("action write aref <- -1 overwrite (release)", lambda: compile_sea("a3h", decls=decls, writes=[write("aref", "-1", composition="overwrite")]))
    try_compile("agent expression is_null: bool = aref == -1", lambda: compile_sea("a3f", decls=decls + [decl("isnull", type="bool", initial_value=False, expression="aref == -1")]))


if __name__ == "__main__":
    which = sys.argv[1:] or ["a1", "a2", "a3"]
    for name in which:
        globals()[name]()
