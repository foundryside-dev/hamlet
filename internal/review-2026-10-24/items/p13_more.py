import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import torch
print("=== trial002 money_crisis modifier on raw meters")
u, env = compile("configs/trial002_money_log_gdp", "L0_simple"); env.reset()
mi = env.meter_name_to_index["money"]
for money in (1.0, 5.0, 1000.0):
    env.meters[:, mi] = money
    tot, w, comp = env.dac_engine.calculate_rewards(step_counts=env.step_counts, dones=env.dones, meters=env.meters, intrinsic_raw=torch.ones(2))
    print(f" money raw={money} (minmax-normalized {(money-1)/999999:.2e}): intrinsic_weight {w.tolist()}")
print(" money bounds", env.meter_bounds_min[mi].item(), env.meter_bounds_max[mi].item(), "intrinsic.apply_modifiers", env.level.drive.intrinsic.apply_modifiers, "money_crisis ranges", [(r.min, r.max, r.multiplier) for r in env.level.drive.modifiers["money_crisis"].ranges])
print("=== exclusive: false medkit — carried lane")
def ed(d):
    for it in d["items"]["item_types"]:
        if it["id"] == "medkit": it["exclusive"] = False
    return d
pack = copy_pack("configs/test/items_smoke", "shared_med", {"items.yaml": ed})
u, env = compile(pack, "L0_smoke"); env.reset()
mgr = env.item_manager; med = next(i for i in mgr.get_all_items() if i.item_type == "medkit")
place(env, 0, list(med.position)); place(env, 1, [4, 4]); act(env, ["GET", "WAIT"])
lay = next(t for t in env.token_spec.compact_layout().types if t.type_name == "item"); ci = lay.dynamic_features.index("carried")
r = rows(env, "item")[med.vfs_index]
print(" shared medkit after GET: presence", r[:, 0].tolist(), "carried", r[:, ci].tolist(), "active", list(mgr.active_items), "held", list(mgr.held_items))
print("=== opening_hours enabled on a temporal-disabled level")
def e_aff(d): d["affordances"]["affordances"][0]["opening_hours"] = {"enabled": True, "schedule": [{"start": 6, "end": 18}]}; return d
pack = copy_pack("configs/test/items_smoke", "hours_notemporal", {"levels/L0_smoke/affordances.yaml": e_aff})
try:
    u, env = compile(pack, "L0_smoke"); env.reset()
    print(" compiled; _is_affordance_open:", env._is_affordance_open("energy_station"), "temporal_support", u.stratum.stratum.temporal_support)
except Exception as e:
    print(" refused:", type(e).__name__, str(e)[:300])
print("=== spawn_item without position compiles?")
