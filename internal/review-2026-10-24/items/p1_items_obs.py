import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import torch
torch.manual_seed(0)
u, env = compile("configs/test/items_smoke", "L0_smoke")
env.reset()
mgr = env.item_manager
med = next(i for i in mgr.get_all_items() if i.item_type == "medkit")
print("medkit", med.instance_id, med.position, "vfs", med.vfs_index, "exclusive", med.exclusive)
lay = next(t for t in env.token_spec.compact_layout().types if t.type_name == "item")
feat = lay.dynamic_features
ci = feat.index("carried"); osl = feat.index("owner_slot"); oa = feat.index("owner_slot_applicable")
def show(tag):
    obs = env._get_observations()
    r = rows(env, "item", obs)[med.vfs_index]
    v = rows(env, "variable_element", obs)[med.vfs_index]
    print(f"{tag}: item row agent0 presence={r[0,0].item():.0f} carried={r[0,ci].item():.0f} owner_slot={r[0,osl].item():.2f} owner_appl={r[0,oa].item():.0f} | durability ve presence={v[0,0].item():.0f} value={v[0,1].item():.3f}")
    return obs
# --- bf42ac60b5 / 17a7f03bc9 world-resident
show("baseline (durability 100)")
env.vfs_registry.write_item("medical", "durability", 3.0, med.vfs_index, writer="engine")
show("durability=3.0")
env.vfs_registry.write_item("medical", "durability", 0.0, med.vfs_index, writer="engine")
show("durability=0.0 (world)")
# --- 4b931faaf4: GET
place(env, 0, list(med.position)); place(env, 1, [4, 4])
obs, r, d, info = act(env, ["GET", "WAIT"])
print("inventory slots", env.item_inventory.slots.tolist(), "active", list(mgr.active_items), "held", list(mgr.held_items))
show("after GET (held, durability 0)")
# --- 559cc74246: identity
env.reset()
apple = next(i for i in mgr.get_all_items() if i.item_type == "apple")
coin = mgr.spawn_item("coin", apple.position, env.global_tick)
med2 = next(i for i in mgr.get_all_items() if i.item_type == "medkit")
mgr.place_item  # noqa
obs = env._get_observations()
R = rows(env, "item", obs)
pos_lanes = [feat.index(f) for f in feat if f.startswith("position_") or f.startswith("egocentric_")]
mask = torch.ones(R[apple.vfs_index].shape[1], dtype=torch.bool); mask[pos_lanes] = False
a = R[apple.vfs_index][0][mask]; c = R[coin.vfs_index][0][mask]; m = R[med2.vfs_index][0][mask]
print("apple vs coin (same cell) non-position lanes equal:", torch.equal(a, c), a.tolist())
print("apple vs medkit non-position lanes equal:", torch.equal(a, m))
print("static slot ctx payload identical across slots:", len({tuple(p) for p in env.token_spec.get_type('item').slot_context_payloads}) == 1)
# owner_slot ever nonzero?
print("owner_slot batch:", env._item_slot_batch().owner_slot.tolist())
