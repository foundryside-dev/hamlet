"""claim_if_free / release on an affordance-scoped agent_ref from a custom action with source_affordance; per world; dead world."""
from common import *  # noqa
import torch


@probe("C1 claim_if_free per world, idempotent, release, dying world")
def c1():
    decls = [decl("occ", scope="affordance", type="agent_ref", initial_value=None), decl("cnt", initial_value=0.0)]

    def actions(a):
        a["custom_actions"].append({"name": "CLAIM", "description": "claim SLEEP", "enabled_by_default": True, "source_affordance": "SLEEP",
                                    "writes": [write("occ", "agent_id", composition="claim_if_free", phase="resolve_affordance_access_and_occupancy")]})
        a["custom_actions"].append({"name": "RELEASE", "description": "release", "enabled_by_default": True, "source_affordance": None,
                                    "writes": [write("rel", "1.0", composition="overwrite")]})
    rules = [rule("release", [rwrite("occ", "-1", composition="overwrite")], condition="tick > 4.0")]
    pack = make_pack("r_claim", variables=lambda v: v["declarations"].extend(decls + [decl("rel", lifetime="tick", initial_value=0.0)]), actions=actions, extra_files=rules_file(rules))
    try_compile("rule occ <- -1 with agent-shaped condition rel > 0.5", lambda: compile_pack(make_pack("r_claim_rel", variables=lambda v: v["declarations"].extend(decls + [decl("rel", lifetime="tick", initial_value=0.0)]), actions=actions, extra_files=rules_file([rule("release", [rwrite("occ", "-1", composition="overwrite")], condition="rel > 0.5")]))))
    try_compile("interaction modify occ (affordance var from a pipeline)", lambda: compile_sea("claim_int", decls=decls, aff_cmds=[{"modify": "occ", "value": "occ"}]))
    u = try_compile("claim pack", lambda: compile_pack(pack))
    if u is None:
        return
    env = build_env(u, num_agents=3)
    r = env.vfs_registry
    aff_ids = [a.name for a in u.get_level("L0_simple").affordances.affordances]
    print("  affordance rows:", aff_ids)
    a = acts(env, "WAIT"); a[1] = action_index(env, "CLAIM")
    env.step(a)
    print("  after world-1 CLAIM:", r.get("occ", reader="engine").tolist())
    env.step(a)
    print("  again (idempotent):", r.get("occ", reader="engine").tolist())
    step(env, "CLAIM")
    print("  all CLAIM:", r.get("occ", reader="engine").tolist())
    a = acts(env, "WAIT"); a[0] = action_index(env, "RELEASE")
    env.step(a)
    print("  world-0 RELEASE:", r.get("occ", reader="engine").tolist())
    env.meters[2, env.meter_name_to_index["energy"]] = 0.005
    a = acts(env, "WAIT"); a[2] = action_index(env, "RELEASE")
    env.step(a)
    print("  world-2 RELEASE on its dying step:", r.get("occ", reader="engine").tolist(), "dones", env.dones.tolist())
    step(env, "CLAIM")
    print("  all CLAIM after death:", r.get("occ", reader="engine").tolist(), "(world 2 frozen)")
    env1 = build_env(u, num_agents=1)
    step(env1, "CLAIM")
    print("  N=1 claim:", env1.vfs_registry.get("occ", reader="engine").tolist())


if __name__ == "__main__":
    c1()
