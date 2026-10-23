import sys, os, torch; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
print("=== base_reward through the compiler")
for label, fn in [("base_reward: 0.0", lambda d: d["drive"]["extrinsic"].__setitem__("base_reward", 0.0) or d), ("base_reward deleted", lambda d: d["drive"]["extrinsic"].pop("base_reward") and d)]:
    def ed(d, fn=fn): d["drive"]["shaping"] = []; return fn(d)
    pack = copy_pack("configs/test/items_smoke", "br_" + label[:12].replace(" ", "_").replace(":", ""), {"levels/L0_smoke/drive.yaml": ed})
    try:
        u, env = compile(pack, "L0_smoke"); env.reset(); o, r, d, i = act(env, ["WAIT", "WAIT"])
        print(f" {label}: compiled; extrinsic {i['reward_components']['extrinsic'].tolist()}")
    except Exception as e:
        print(f" {label}: refused: {type(e).__name__} {str(e)[:250]}")
print("=== trial002 money after stepping (clamp check)")
u, env = compile("configs/trial002_money_log_gdp", "L0_simple"); env.reset(); mi = env.meter_name_to_index["money"]
print(" initial", env.meters[0, mi].item()); act(env, ["WAIT", "WAIT"]); print(" after WAIT", env.meters[0, mi].item())
print("=== 45f501e15b silent half: max_items_per_agent 0, no level items.yaml")
def ed(d): d["items"]["max_items_per_agent"] = 0; return d
pack = copy_pack("configs/test/items_smoke", "mipa0_silent", {"items.yaml": ed}); os.remove(pack / "levels/L0_smoke/items.yaml")
try:
    u, env = compile(pack, "L0_smoke")
    print(" compiled; items_catalog", u.items_catalog, "GET in action_ids", "GET" in env.action_ids, "item census", env.token_spec.census["item"], "item_manager", env.item_manager)
except Exception as e:
    print(" refused:", type(e).__name__, str(e)[:250])
print("=== timing_bonus on a non-temporal level")
def ed(d): d["drive"]["shaping"] = [{"type": "timing_bonus", "weight": 1.0, "time_ranges": [{"start_hour": 0, "end_hour": 23, "affordance": "energy_station", "multiplier": 1.0}]}]; return d
pack = copy_pack("configs/test/items_smoke", "timing_notemporal", {"levels/L0_smoke/drive.yaml": ed})
try:
    u, env = compile(pack, "L0_smoke"); env.reset(); place(env, 0, [1, 1]); place(env, 1, [4, 4]); o, r, d, i = act(env, ["INTERACT", "WAIT"])
    print(" compiled; succ", i["successful_interactions"], "shaping", i["reward_components"]["shaping"].tolist(), "(all-hours window, interaction happened -> 1.0 expected)")
except Exception as e:
    print(" refused:", type(e).__name__, str(e)[:250])
print("=== approach_reward on aspatial")
lv = os.listdir(REPO / "configs/aspatial_test/levels")[0]
u, env = compile("configs/aspatial_test", lv); env.reset()
print(" aspatial shaping decls:", [s.type for s in env.level.drive.shaping], "affordances:", {k: tuple(v.shape) for k, v in env.affordances.items()})
aff = next(iter(env.affordances)) if env.affordances else None
if aff:
    tot, w, comp = env.dac_engine.calculate_rewards(step_counts=env.step_counts, dones=env.dones, meters=env.meters, intrinsic_raw=torch.zeros(env.num_agents), agent_positions=env.positions.float(), affordance_positions=env._get_affordance_positions(), last_action_affordance=[None]*env.num_agents, affordance_streak={}, unique_affordances_used=torch.zeros(env.num_agents))
    print(" existing shaping on aspatial:", comp["shaping"].tolist())
    from townlet.config.drive_as_code import DriveAsCodeConfig
    from townlet.environment.dac_engine import DACEngine
    cfg = env.level.drive.model_dump(); cfg["shaping"] = [{"type": "approach_reward", "weight": 1.0, "target_affordance": aff, "max_distance": 5.0}]
    e2 = DACEngine(DriveAsCodeConfig(**cfg), env.vfs_registry, env.device, env.num_agents, env.dac_engine.bar_index_map)
    tot, w, comp = e2.calculate_rewards(step_counts=env.step_counts, dones=env.dones, meters=env.meters, intrinsic_raw=torch.zeros(env.num_agents), agent_positions=env.positions.float(), affordance_positions=env._get_affordance_positions(), last_action_affordance=[None]*env.num_agents, affordance_streak={}, unique_affordances_used=torch.zeros(env.num_agents))
    print(f" approach_reward({aff}) on aspatial [N,0] positions -> shaping {comp['shaping'].tolist()} (weight 1.0 = full bonus at 'distance 0')")
