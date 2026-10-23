"""Probe 4: VFS id colliding with a meter name; social residue at a never-run phase; bool additive_delta."""

import torch
from harness import *  # noqa: F403


def try_compile(name, **kw):
    p = make_pack(name, **kw)
    try:
        u = compile_pack(p); print(f"[{name}] compiled OK"); return u
    except Exception as e:
        print(f"[{name}] REFUSED {type(e).__name__}: {str(e)[-500:]}"); return None


@probe("A. VFS variable id == meter name ('energy')")
def probe_a():
    u = try_compile("name_collide", variables=lambda v: v["declarations"].append(decl("energy", initial_value=0.25)),
                    actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("energy", "1.0")]))
    if u:
        env = build_env(u, 2)
        print("   meter energy before", env.meters[:, env.meter_name_to_index["energy"]].tolist(), "vfs energy", reg(env, "energy").tolist())
        step(env, "ADVANCE")
        print("   meter energy after ADVANCE(+1 to 'energy')", env.meters[:, env.meter_name_to_index["energy"]].tolist(), "vfs energy", reg(env, "energy").tolist())
    # expression-only collision (no write)
    u = try_compile("name_collide_expr", variables=lambda v: v["declarations"].extend([decl("energy", initial_value=0.25), decl("e2", expression="energy * 2.0")]))
    if u:
        env = build_env(u, 2); step(env, "WAIT"); print("   e2 (expression 'energy * 2.0'; vfs energy=0.25, meter energy~0.99):", reg(env, "e2").tolist())


@probe("B. social residue rule scheduled at never-run / actions-less phases")
def probe_b():
    for phase in ("emit_telemetry", "compute_rewards", "clamp_and_validate", "apply_action_effects"):
        rules = {"version": "1.0", "social_residue": [
            {"id": "inc", "kind": "institutional_rule", "phase": phase, "reads": ["public_state"], "condition": None,
             "writes": [{"variable_id": "public_state", "expression": "public_state + 1.0", "composition": "overwrite", "condition": None, "clamp": None, "effect": None, "scope": "agent"}]}]}
        u = try_compile(f"residue_{phase}", extra_files={"transition_rules.yaml": rules})
        if u:
            try:
                env = build_env(u, 2); step(env, "WAIT"); step(env, "WAIT")
                print(f"   phase={phase}: 2 steps -> public_state {reg(env, 'public_state').tolist()}")
            except Exception as e:
                print(f"   phase={phase}: RUNTIME {type(e).__name__}: {str(e)[:150]}")


@probe("C. bool target with additive_delta / overwrite float expression")
def probe_c():
    u = try_compile("bool_add", variables=lambda v: v["declarations"].append(decl("flag", type="bool", initial_value=False)),
                    actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("flag", "1.0")]))
    if u:
        env = build_env(u, 2)
        try:
            step(env, "ADVANCE"); step(env, "ADVANCE"); print("   flag after 2x additive_delta 1.0:", reg(env, "flag").tolist())
        except Exception as e:
            print("   RUNTIME", type(e).__name__, str(e)[:200])
    u = try_compile("bool_ovw", variables=lambda v: v["declarations"].append(decl("flag", type="bool", initial_value=False)),
                    actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("flag", "0.0", composition="overwrite")]))
    if u:
        env = build_env(u, 2); step(env, "ADVANCE"); print("   flag after overwrite 0.0:", reg(env, "flag").tolist())
    # int reference var written with float
    u = try_compile("ref_write", variables=lambda v: v["declarations"].append(decl("buddy", type="agent_ref", initial_value=None)),
                    actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("buddy", "0.6", composition="overwrite")]))
    if u:
        env = build_env(u, 2); step(env, "ADVANCE"); print("   agent_ref after overwrite 0.6:", reg(env, "buddy").tolist(), reg(env, "buddy").dtype)


if __name__ == "__main__":
    for fn in (probe_a, probe_b, probe_c):
        fn()
