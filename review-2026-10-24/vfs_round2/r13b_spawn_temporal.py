"""R13b: spawn condition `temporal.is_night` / `temporal.time_of_day` compile on a temporal level;
the runtime spawn context carries only `temporal.tick`."""
from harness import *  # noqa

BASE_ITEMS = REPO / "configs" / "test" / "items_smoke"
LEVEL = "L0_smoke"


def run(label, when):
    def mutate(dest):
        edit_yaml(dest / "stratum.yaml", lambda p: p["stratum"].update({"temporal_support": "enabled"}))
        edit_yaml(dest / "levels" / LEVEL / "curriculum.yaml",
                  lambda p: p["curriculum"].update({"active_temporal": True, "day_length": 24}))

        def a(p):
            for item in p["items"]:
                if item["item_type"] == "apple":
                    item["when"] = when
        edit_yaml(dest / "levels" / LEVEL / "items.yaml", a)
    print(f"--- {label}: when: {when!r}")
    try:
        u = compile_pack(make_pack_from(f"r13b_{label}", BASE_ITEMS, mutate), level=LEVEL)
        print("   compile: OK")
    except Exception as exc:  # noqa: BLE001
        print(f"   compile: REFUSED {type(exc).__name__}: {str(exc)[:400]}")
        return
    try:
        env = build_env(u, num_agents=1, level=LEVEL)
        print(f"   reset OK: apples = {sum(1 for it in env.item_manager.get_all_items() if it.item_type == 'apple')}")
    except Exception as exc:  # noqa: BLE001
        print(f"   runtime: {type(exc).__name__}: {str(exc)[:300]}")


@probe("R13b spawn temporal namespace")
def main():
    run("is_night", "temporal.is_night")
    run("time_of_day", "temporal.time_of_day < 12.0")


main()
