"""M11 item state decays while held (items_smoke base); spawn predicate context; M2c ticks-since via action write."""

from harness import *  # noqa: F403

import torch

ISM = WT / "configs" / "test" / "items_smoke"
LV = "L0_smoke"


def items_pack(name, **kw):
    return make_pack(name, base=ISM, level=LV, **kw)


@probe("M11a transition rule targeting item-scoped state (VFS route)")
def m11a():
    p = items_pack("m11a", rules=[rule("rot", [rwrite("freshness", "-1.0")])])
    u, err = try_compile(p, LV)
    print("COMPILED" if u else "REFUSED " + short(err.split(" - ", 1)[-1], 400))


@probe("M11b item-scoped expression (VFS route)")
def m11b():
    def variables(v):
        for d in v["declarations"]:
            if d["id"] == "freshness":
                d["expression"] = "100.0 - tick"

    p = items_pack("m11b", variables=variables)
    u, err = try_compile(p, LV)
    print("COMPILED" if u else "REFUSED " + short(err.split(" - ", 1)[-1], 300))


@probe("M11c item-scoped effect decaying item.condition while held (effects route): spawn from on_pickup")
def m11c():
    def items(payload):
        for it in payload["items"]["item_types"]:
            if it["id"] == "apple":
                it["interactions"]["on_pickup"] = [{"spawn_effect": "food_decay", "target": "item", "intensity": 1.0}]

    p = items_pack("m11c", extra_files={})
    import yaml as _y

    path = p / "items.yaml"
    payload = load_yaml(path)
    items(payload)
    dump_yaml(path, payload)
    u, err = try_compile(p, LV)
    if err:
        print("REFUSED", short(err.split(" - ", 1)[-1], 400))
        return
    env = build_env(u, 1, LV)
    im = env.item_manager
    print("active items", [(i.item_type, tuple(i.position.tolist()) if hasattr(i, "position") else None) for i in im.active_items][:4] if hasattr(im, "active_items") else im)
    try:
        apple = next(i for i in im.active_items if i.item_type == "apple")
        env.positions[0] = torch.as_tensor(apple.position)
    except Exception as exc:  # noqa: BLE001
        print("could not place:", exc)
    obs, *_ = step(env, "GET")
    print("after GET: inventory", env.item_manager.inventories if hasattr(env.item_manager, "inventories") else "?")
    for t in range(3):
        step(env, "WAIT")
        arena = env.vfs_registry.item_arena if hasattr(env.vfs_registry, "item_arena") else None
        print("tick", t, "arena rows profile/condition:", env.vfs_registry.item_profile_map if hasattr(env.vfs_registry, "item_profile_map") else "?")
        try:
            print("  condition rows:", env.vfs_registry.read_item("food", "condition", reader="engine").tolist())
        except Exception as exc:  # noqa: BLE001
            print("  read_item:", short(str(exc), 200))


@probe("SPAWN: function admission in an item spawn predicate (when)")
def spawn():
    exprs = ["bar.energy < 0.9", "lag(bar.energy, 1) > 0.5", "uniform(0.0, 1.0) < 0.5", "time_in_window(tick, 2, 6)", "distance_to_affordance(\"EAT\") < 3.0", "elapsed_ticks() > 2", "phase_sin(tick, 24) > 0.0"]
    for e in exprs:
        p = items_pack("spawn")
        path = p / "levels" / LV / "items.yaml"
        payload = load_yaml(path)
        payload["items"][0]["when"] = e
        dump_yaml(path, payload)
        u, err = try_compile(p, LV)
        print(f"{e:42s} | ", "OK" if u else "REFUSED " + short(err.split(" - ", 1)[-1].replace("\n", " "), 200))


@probe("M2c ticks-since via an action write that raises energy (isolates the expression)")
def m2c():
    p = make_pack(
        "m2c",
        variables=lambda v: v["declarations"].extend(
            [decl("ticks_since_nap", initial_value=-1.0, expression="where(delta(bar.energy) > 0.0, 0.0, lag(ticks_since_nap, 1) + 1.0)")]
        ),
        actions=lambda a: add_action(a, "NAP", [write("bar.energy", "0.3", clamp=[0.0, 1.0])]),
    )
    u, err = try_compile(p)
    if err:
        print("REFUSED", short(err))
        return
    env = build_env(u, 2)
    seq = []
    for t, acts in enumerate([["WAIT", "WAIT"], ["WAIT", "WAIT"], ["NAP", "WAIT"], ["WAIT", "WAIT"], ["NAP", "WAIT"]]):
        step(env, acts)
        seq.append((acts[0], reg(env, "ticks_since_nap").tolist(), [round(x, 2) for x in meter(env, "energy").tolist()]))
    for s in seq:
        print(s)


if __name__ == "__main__":
    import sys

    names = sys.argv[1:] or ["m11a", "m11b", "m11c", "spawn", "m2c"]
    for n in names:
        globals()[n]()
