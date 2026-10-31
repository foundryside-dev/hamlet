"""R13: item spawn conditions compile against VFS namespaces (`env.X`, `vfs.X`, `agent.vfs.X`) that the
runtime evaluation context does not provide under those spellings."""
from harness import *  # noqa

BASE_ITEMS = REPO / "configs" / "test" / "items_smoke"
LEVEL = "L0_smoke"


def run(label, when, extra_vars=()):
    def mutate(dest):
        def v(p):
            p["variables"]["declarations"].extend(extra_vars)
        edit_yaml(dest / "variables.yaml", v)

        def a(p):
            for item in p["items"]:
                if item["item_type"] == "apple":
                    item["when"] = when
        edit_yaml(dest / "levels" / LEVEL / "items.yaml", a)
    print(f"--- {label}: when: {when!r}")
    try:
        u = compile_pack(make_pack_from(f"r13_{label}", BASE_ITEMS, mutate), level=LEVEL)
        print("   compile: OK")
    except Exception as exc:  # noqa: BLE001
        print(f"   compile: REFUSED {type(exc).__name__}: {str(exc)[:300]}")
        return
    try:
        env = build_env(u, num_agents=1, level=LEVEL)
        apples = [it for it in env.item_manager.get_all_items() if it.item_type == "apple"]
        print(f"   reset OK: apples spawned = {len(apples)}")
    except Exception as exc:  # noqa: BLE001
        print(f"   runtime: {type(exc).__name__}: {str(exc)[:300]}")


@probe("R13 spawn-condition namespaces")
def main():
    g = decl("season", scope="global", initial_value=1.0)
    run("control_vfs_false", "vfs.season < 0.5", [g])
    run("env_prefix_agent_bool", "env.has_food")
    run("env_prefix_global", "env.season > 0.5", [g])
    run("vfs_prefix_global", "vfs.season > 0.5", [g])
    run("bare_global", "season > 0.5", [g])
    run("bar_bare", "energy > 0.5")


main()
