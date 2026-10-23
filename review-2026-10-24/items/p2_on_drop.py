import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import torch
def ed(d):
    for it in d["items"]["item_types"]:
        if it["id"] == "medkit":
            it["interactions"]["on_drop"] = [{"modify": "target.bar.money", "value": "target.bar.money + 0.5"}]
            it["interactions"]["on_pickup"] = [{"modify": "target.bar.money", "value": "target.bar.money + 0.1"}]
    return d
pack = copy_pack("configs/test/items_smoke", "ondrop", {"items.yaml": ed})
u, env = compile(pack, "L0_smoke")
env.reset()
mgr = env.item_manager
med = next(i for i in mgr.get_all_items() if i.item_type == "medkit")
place(env, 0, list(med.position)); place(env, 1, [4, 4])
mi = env.meter_name_to_index["money"]
print("money before", env.meters[0, mi].item())
act(env, ["GET", "WAIT"]); print("after GET (on_pickup +0.1):", round(env.meters[0, mi].item(), 3), "slots", env.item_inventory.slots[0].tolist())
act(env, ["USE_SLOT_0", "WAIT"]); print("after USE:", round(env.meters[0, mi].item(), 3))
act(env, ["DROP_SLOT_0", "WAIT"]); print("after DROP (on_drop +0.5 expected):", round(env.meters[0, mi].item(), 3), "slots", env.item_inventory.slots[0].tolist(), "active", list(mgr.active_items))
print("--- trial_k_cold compile attempt")
try:
    u2, env2 = compile("configs/trial_k_cold", "L0_cold")
    print("trial_k_cold compiled OK")
except Exception as e:
    print("trial_k_cold refused:", type(e).__name__, str(e)[:300])
