import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import torch
print("=== item reset at episode boundary")
u, env = compile("configs/test/items_smoke", "L0_smoke"); env.reset()
mgr = env.item_manager
med = next(i for i in mgr.get_all_items() if i.item_type == "medkit")
place(env, 0, list(med.position)); place(env, 1, [4, 4])
act(env, ["GET", "WAIT"]); env.vfs_registry.write_item("medical", "durability", 7.0, med.vfs_index, writer="engine")
print(" before reset: slots", env.item_inventory.slots[0].tolist(), "held", list(mgr.held_items), "row", env.vfs_registry.item_vfs[med.vfs_index].tolist(), "next_id", mgr.next_instance_id)
env.reset()
print(" after reset: slots", env.item_inventory.slots[0].tolist(), "held", list(mgr.held_items), "active", [(i.instance_id, i.item_type, i.vfs_index) for i in mgr.get_all_items()], "next_id", mgr.next_instance_id, "timers", mgr.respawn_timers, "cooldown", mgr.cooldown_until)
print(" item_vfs rows:", env.vfs_registry.item_vfs.tolist()[:5], "index->profile", dict(env.vfs_registry.item_vfs_index_to_profile) if hasattr(env.vfs_registry, 'item_vfs_index_to_profile') else None)
print("=== same-tick GET race (2 agents on one exclusive item)")
env.reset(); med = next(i for i in mgr.get_all_items() if i.item_type == "medkit")
place(env, 0, list(med.position)); place(env, 1, list(med.position))
act(env, ["GET", "GET"]); print(" slots", env.item_inventory.slots.tolist(), "holders", med.holder_agent_ids)
print("=== drop onto occupied cell")
apple = next(i for i in mgr.get_all_items() if i.item_type == "apple")
place(env, 0, list(apple.position)); act(env, ["DROP_SLOT_0", "WAIT"])
print(" items at", apple.position, ":", [i.item_type for i in mgr.active_items.values() if i.position == apple.position], "position_index", mgr._position_index.get(tuple(apple.position)))
print("=== spawn_initial_items counts a None return (capacity)")
def ed(d): d["items"]["max_items_in_world"] = 2; return d
pack = copy_pack("configs/test/items_smoke", "cap2", {"items.yaml": ed})
u2, env2 = compile(pack, "L0_smoke"); env2.reset()
print(" max_items 2, rules want 3 apples+1 medkit: spawned", [(i.item_type) for i in env2.item_manager.get_all_items()], "rule_spawn_counts", env2.item_manager.rule_spawn_counts)
print("=== approach_reward distance metric (substrate manhattan)")
u3, env3 = compile("configs/test/items_smoke", "L0_smoke"); env3.reset()
place(env3, 0, [4, 4]); place(env3, 1, [1, 1])  # station at (1,1); L1 dist 6, L2 dist 4.24
def e_dr(d): d["drive"]["shaping"] = [{"type": "approach_reward", "weight": 1.0, "target_affordance": "energy_station", "max_distance": 5.0}]; return d
pack = copy_pack("configs/test/items_smoke", "approach", {"levels/L0_smoke/drive.yaml": e_dr})
u4, env4 = compile(pack, "L0_smoke"); env4.reset(); place(env4, 0, [4, 4]); place(env4, 1, [1, 1])
tot, w, comp = env4.dac_engine.calculate_rewards(step_counts=env4.step_counts, dones=env4.dones, meters=env4.meters, intrinsic_raw=torch.zeros(2), agent_positions=env4.positions.float(), affordance_positions=env4._get_affordance_positions(), last_action_affordance=[None, None], affordance_streak={}, unique_affordances_used=torch.zeros(2))
print(" substrate metric", u4.stratum.stratum.substrate.grid.distance_metric, "agent0 at (4,4) target (1,1) max_distance 5: approach bonus", round(comp["shaping"][0].item(), 4), "(manhattan 6 -> 0; euclid 4.24 -> 0.15)")
print("=== retirement bonus outside drive.yaml")
u5, env5 = compile("configs/test/items_smoke", "L0_smoke"); env5.reset()
for t in range(100):
    o, r, d, i = act(env5, ["WAIT", "WAIT"])
    if i["newly_retired"].any(): print(" tick", t, "newly_retired", i["newly_retired"].tolist(), "reward", r.tolist(), "extrinsic", i["reward_components"]["extrinsic"].tolist()); break
print("=== items on GridND: reset spawn path")
import yaml
def e_items(d):
    d["items"]["item_types"] = [{"id": "rock", "name": "Rock", "icon": "R", "tags": ["rock"], "vfs_profile": "default_item", "interactions": {"on_pickup": [], "on_use": [], "on_drop": []}, "duration": None, "cooldown": None}]
    d["items"]["max_items_in_world"] = 2; return d
pack = copy_pack("configs/test/gridnd_4d_pack", "gridnd_items", {"items.yaml": e_items})
(pack / "levels/L0_test/items.yaml").write_text(yaml.safe_dump({"version": "1.0", "items": [{"item_type": "rock", "spawn_count": 2, "placement": {"mode": "random"}}]}))
try:
    u6, env6 = compile(pack, "L0_test"); env6.reset()
    print(" gridnd: items_appearance rules", len(u6.get_level("L0_test").items_appearance.items), "spawned after reset:", [(i.item_type, i.position) for i in env6.item_manager.get_all_items()])
except Exception as e:
    print(" gridnd FAILED:", type(e).__name__, str(e)[:400])
