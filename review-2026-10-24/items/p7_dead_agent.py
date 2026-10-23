import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import torch
u, env = compile("configs/test/items_smoke", "L0_smoke"); env.reset()
mgr = env.item_manager
med = next(i for i in mgr.get_all_items() if i.item_type == "medkit")
place(env, 0, list(med.position)); place(env, 1, [2, 2])
env.dones[0] = True
ei = env.meter_name_to_index["energy"]
e_before = env.meters[0, ei].item(); p_before = env.positions[0].tolist()
masks = env.get_action_masks()
print("dead agent mask all False:", (~masks[0]).all().item())
o, r, d, info = act(env, ["GET", "WAIT"])
print("dead agent GET: inventory", env.item_inventory.slots[0].tolist(), "held", list(mgr.held_items), "reward", r[0].item())
env.reset(); env.dones[0] = True; place(env, 0, [2, 2]); p_before = env.positions[0].tolist(); e_before = env.meters[0, ei].item()
act(env, ["UP", "WAIT"])
print("dead agent UP: pos", p_before, "->", env.positions[0].tolist(), "energy", e_before, "->", round(env.meters[0, ei].item(), 4))
env.reset(); env.dones[0] = True; place(env, 0, [1, 1]); e_before = env.meters[0, ei].item(); env.meters[0, ei] = 0.5
act(env, ["INTERACT", "WAIT"])
print("dead agent INTERACT at energy_station: energy 0.5 ->", round(env.meters[0, ei].item(), 4), "(instant +0.3 would show if executed)")
