"""Probe 5: meter-name collision with no action writes (silent?) and bare-name resolution in VTC expressions."""
import torch
from harness import *  # noqa: F403

@probe("A. VFS var 'energy' with no action writes: silent? expression resolution")
def probe_a():
    def acts(a):
        next(x for x in a["custom_actions"] if x["name"] == "ADVANCE")["writes"] = []
    p = make_pack("collide_silent", variables=lambda v: v["declarations"].extend([decl("energy", initial_value=0.25), decl("e2", expression="energy * 2.0")]), actions=acts)
    try:
        u = compile_pack(p); env = build_env(u, 2); step(env, "WAIT")
        print("   compiled+stepped OK; meter energy", env.meters[:, env.meter_name_to_index['energy']].tolist(), "vfs energy", reg(env, "energy").tolist(), "e2", reg(env, "e2").tolist())
    except Exception as e:
        print("   ", type(e).__name__, str(e)[-300:])
    # action write whose expression uses the bare meter name when a same-named var exists
    def acts2(a):
        next(x for x in a["custom_actions"] if x["name"] == "ADVANCE")["writes"] = [write("public_state", "energy", composition="overwrite")]
    p = make_pack("collide_expr_vtc", variables=lambda v: v["declarations"].append(decl("energy", initial_value=0.25)), actions=acts2)
    try:
        u = compile_pack(p); env = build_env(u, 2); step(env, "ADVANCE"); print("   public_state := energy ->", reg(env, "public_state").tolist())
    except Exception as e:
        print("   ", type(e).__name__, str(e)[-300:])
    # control: no collision, bare 'energy' in a VTC expression resolves to the meter?
    def acts3(a):
        next(x for x in a["custom_actions"] if x["name"] == "ADVANCE")["writes"] = [write("public_state", "energy", composition="overwrite")]
    p = make_pack("bare_meter_vtc", actions=acts3)
    try:
        u = compile_pack(p); env = build_env(u, 2); step(env, "ADVANCE"); print("   [no collision] public_state := energy ->", reg(env, "public_state").tolist(), "meter energy", env.meters[:, env.meter_name_to_index['energy']].tolist())
    except Exception as e:
        print("   [no collision]", type(e).__name__, str(e)[-300:])

if __name__ == "__main__":
    probe_a()
