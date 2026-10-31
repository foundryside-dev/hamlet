"""R9: temporal history operators (lag/delta/ema/...) — the DSL implements them, VFS compiles a
history spec for them, but the profile shape proof refuses every one of them."""
from harness import *  # noqa


def attempt(label, decls):
    print(f"--- {label}")
    try:
        u = compile_pack(make_pack(f"r9_{label}", variables=lambda v: v["declarations"].extend(decls)))
        print(f"   compile: OK  vfs_history_spec={u.vfs_history_spec}")
        env = build_env(u, num_agents=1)
        for k in range(3):
            step(env, "ADVANCE")
            print(f"   step{k+1}: " + ", ".join(f"{d['id']}={reg(env, d['id']).tolist()}" for d in decls))
    except Exception as exc:  # noqa: BLE001
        print(f"   REFUSED {type(exc).__name__}: {str(exc)[:300]}")


@probe("R9 history operators")
def main():
    attempt("agent_lag_bar", [decl("prev_energy", expression="lag(bar.energy, 1)")])
    attempt("agent_delta_var", [decl("d_public", expression="delta(public_state)")])
    attempt("global_lag_tick", [decl("prev_tick", scope="global", expression="lag(tick, 1)")])
    attempt("global_ema_tick", [decl("ema_tick", scope="global", expression="ema(tick, 0.5)")])
    attempt("global_rising_edge", [decl("g", scope="global", initial_value=0.0, writable=("engine",)),
                                   decl("edge", scope="global", type="bool", initial_value=False, expression="rising_edge(tick > 1.0)")])


main()
