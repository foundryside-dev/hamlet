"""R4: VTC write expressions are type-checked but not shape-proved: a global tensor / pair /
message variable read inside an agent-row action write broadcasts by coincidence of extents."""
from harness import *  # noqa


def run(label, var_decls, write_spec, num_agents, extents=None, show=("public_state",)):
    def vars_(v):
        v["declarations"] += var_decls
        if extents:
            v["extents"].update(extents)

    def acts(a):
        for ca in a["custom_actions"]:
            if ca["name"] == "ADVANCE":
                ca["writes"] = [write_spec]

    print(f"--- {label} (num_agents={num_agents})")
    try:
        pack = make_pack(f"r4_{label}_{num_agents}", variables=vars_, actions=acts)
        u = compile_pack(pack)
        print("   compile: OK")
    except Exception as exc:  # noqa: BLE001
        print(f"   compile: REFUSED {type(exc).__name__}: {str(exc)[:300]}")
        return
    try:
        env = build_env(u, num_agents=num_agents)
        step(env, "ADVANCE")
        for name in show:
            print(f"   after ADVANCE: {name} = {reg(env, name).tolist()}")
    except Exception as exc:  # noqa: BLE001
        print(f"   runtime: {type(exc).__name__}: {str(exc)[:300]}")


@probe("R4 write expression shape")
def main():
    gvec2 = decl("gvec", scope="global", type="tensor1d", shape=[2], initial_value=[10.0, 20.0])
    gvec3 = decl("gvec", scope="global", type="tensor1d", shape=[3], initial_value=[10.0, 20.0, 30.0])
    for n in (2, 3):
        run("global_tensor_read", [gvec2], write("public_state", "gvec"), n)
    run("global_tensor3_read", [gvec3], write("public_state", "gvec"), 3)
    run("global_tensor_condition", [gvec2], write("public_state", "1.0", condition="gvec > 15.0"), 2)
    trust = decl("trust", scope="pair", initial_value=0.5)
    for n in (2, 3):
        run("pair_read", [trust], write("public_state", "trust"), n)
    msg = decl("inbox", scope="message", initial_value=1.0)
    run("message_read", [msg], write("public_state", "inbox"), 2, extents={"num_message_slots": 2})
    run("message_read", [msg], write("public_state", "inbox"), 3, extents={"num_message_slots": 3})


main()
