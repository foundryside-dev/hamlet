"""R3: under active_vision: partial, item-state variable_element rows stay present for items outside view."""
from harness import *  # noqa

BASE_ITEMS = REPO / "configs" / "test" / "items_smoke"
LEVEL = "L0_smoke"


def mutate(dest):
    edit_yaml(dest / "stratum.yaml", lambda p: p["stratum"].update({"vision_support": "both"}))
    edit_yaml(dest / "levels" / LEVEL / "curriculum.yaml",
              lambda p: p["curriculum"].update({"active_vision": "partial", "vision_range": 0.2}))


@probe("R3 item-state variable_element ignores the visibility filter")
def main():
    pack = make_pack_from("r3_items_partial", BASE_ITEMS, mutate)
    u = compile_pack(pack, level=LEVEL)
    env = build_env(u, num_agents=1, level=LEVEL)
    torch.manual_seed(0)
    found = 0
    seen_near = False
    for trial in range(200):
        obs = env.reset()
        items = env.item_manager.get_all_items()
        medkits = [it for it in items if it.item_type_id == "medkit"] if hasattr(items[0], "item_type_id") else \
            [it for it in items if getattr(it, "type_id", getattr(it, "item_type", None)) == "medkit"]
        if not medkits:
            continue
        mk = medkits[0]
        apos = env.positions[0].tolist()
        dist = abs(apos[0] - mk.position[0]) + abs(apos[1] - mk.position[1])
        item_rows = dict(type_rows(env, obs, "item"))
        ve = ve_rows(env, obs, agent=0)
        slot = mk.vfs_index
        dur_ref = f"medical.durability[{slot}]"
        print(f"trial{trial}: agent@{apos} medkit@{list(mk.position)} manhattan={dist} (radius 1) | "
              f"item token slot{slot} presence={item_rows[slot][0]} | {dur_ref} row={ve[dur_ref]}")
        if dist <= 1:
            seen_near = True
        if dist > 1:
            found += 1
            if found >= 3 and seen_near:
                break


main()
