"""N4 indirection routes: null test via a global null sentinel; release via a global bool set from an interaction; bool clamp [0,0]."""
from common import *  # noqa
import torch


@probe("C2 null sentinel + global-bool release")
def c2():
    decls = [decl("occ", scope="affordance", type="agent_ref", initial_value=None),
             decl("nullref", scope="global", type="agent_ref", initial_value=None),
             decl("rel", scope="global", type="bool", lifetime="tick", initial_value=False),
             decl("free_cnt", scope="affordance", initial_value=0.0)]

    def actions(a):
        a["custom_actions"].append({"name": "CLAIM", "description": "claim SLEEP", "enabled_by_default": True, "source_affordance": "SLEEP",
                                    "writes": [write("occ", "agent_id", composition="claim_if_free", phase="resolve_affordance_access_and_occupancy")]})

    def affordances(payload):
        for af in payload["affordances"]:
            if af["name"] == "SLEEP":
                af["interactions"]["on_start"] = [{"modify": "rel", "value": "true"}]
    rules = [rule("isfree", [rwrite("free_cnt", "1.0")], condition="occ == nullref"),
             rule("release", [rwrite("occ", "-1", composition="overwrite")], condition="rel")]
    pack = make_pack("r_claim2", variables=lambda v: v["declarations"].extend(decls), actions=actions, affordances=affordances, extra_files=rules_file(rules))
    u = try_compile("sentinel null test + global-bool release", lambda: compile_pack(pack))
    if u is None:
        return
    env = build_env(u, num_agents=3)
    r = env.vfs_registry
    step(env, "CLAIM")
    print("  after all CLAIM: occ", r.get("occ", reader="engine")[:, 0].tolist(), " free_cnt[:,0]", r.get("free_cnt", reader="engine")[:, 0].tolist(), "(counted free rows before the claim: entry snapshot)")
    step(env, "WAIT")
    print("  after WAIT: free_cnt[:,0]", r.get("free_cnt", reader="engine")[:, 0].tolist(), " free_cnt[:,1]", r.get("free_cnt", reader="engine")[:, 1].tolist())
    env.positions[1] = env.affordances["SLEEP"].to(env.positions.dtype)
    a = acts(env, "WAIT"); a[1] = action_index(env, "INTERACT")
    env.step(a)
    print("  world-1 INTERACT(SLEEP sets rel): occ[:,0]", r.get("occ", reader="engine")[:, 0].tolist(), " rel", r.get("rel", reader="engine").tolist(), "(expect only world 1 released)")
    # identity test: is the claim mine?
    try_compile("rule condition occ == agent_id", lambda: compile_sea("c2id", decls=decls, rules=[rule("mine", [rwrite("free_cnt", "1.0")], condition="occ == agent_id")]))
    decls2 = decls + [decl("me", type="agent_ref", initial_value=None)]
    u2 = try_compile("agent me <- agent_id (action write) then rule condition occ == me", lambda: compile_sea("c2me", decls=decls2, writes=[write("me", "agent_id", composition="overwrite")], rules=[rule("mine", [rwrite("free_cnt", "1.0")], condition="occ == me")]))


@probe("C3 bool clamp [0,0] flips a true write")
def c3():
    decls = [decl("flag", type="bool", initial_value=False)]
    u = try_compile("flag <- true clamp [0,0]", lambda: compile_sea("c3", decls=decls, writes=[write("flag", "true", composition="overwrite", clamp=[0.0, 0.0])]))
    if u is not None:
        env = build_env(u, num_agents=2)
        try_run("  step ADVANCE flag", lambda: (step(env, "ADVANCE"), reg(env, "flag").tolist())[1])


if __name__ == "__main__":
    c2(); c3()
