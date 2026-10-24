"""R7: what agent_private can do that `agent` + readable_by:[engine] cannot — and what it cannot do."""
from harness import *  # noqa

LEVEL_DIR = "levels/L0_simple"


def drive_on(var):
    def mutate(dest):
        def f(p):
            p["drive"]["extrinsic"]["variable_bonuses"] = [{"variable": var, "weight": 0.5}]
        edit_yaml(dest / LEVEL_DIR / "drive.yaml", f)
    return mutate


def attempt(label, decls, mutate=None, after=None):
    print(f"--- {label}")
    try:
        pack = make_pack(f"r7_{label}", variables=lambda v: v["declarations"].extend(decls))
        if mutate:
            mutate(pack)
        u = compile_pack(pack)
        print("   compile: OK")
        if after:
            after(u)
    except Exception as exc:  # noqa: BLE001
        print(f"   REFUSED {type(exc).__name__}: {str(exc)[:350]}")


@probe("R7 agent_private")
def main():
    priv = dict(id="hidden_reward", scope="agent_private", readable=("engine",), initial_value=1.0)
    eng_only = dict(id="hidden_reward", scope="agent", readable=("engine",), initial_value=1.0)
    attempt("private_as_reward", [decl(**priv)], drive_on("hidden_reward"))
    attempt("agent_engine_only_as_reward", [decl(**eng_only)], drive_on("hidden_reward"))
    attempt("private_in_agent_expression", [decl(**priv), decl("felt", expression="hidden_reward * 2.0")])
    attempt("agent_engine_only_in_agent_expression", [decl(**eng_only), decl("felt", expression="hidden_reward * 2.0")])

    def check_read(u):
        env = build_env(u)
        try:
            env.vfs_registry.get("p", reader="agent")
            print("   registry.get(reader=agent): allowed")
        except PermissionError as exc:
            print(f"   registry.get(reader=agent): PermissionError {exc}")
        print(f"   compiled policy readable_by = {env.vfs_registry.get_access_policy('p').readable_by}")
    attempt("private_declared_agent_readable", [decl("p", scope="agent_private", readable=("engine", "agent"))], after=check_read)


main()
