import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import os
os.environ["PYTHONWARNINGS"] = "ignore"
print("=== (i) multi_tick affordance with active_temporal: false")
def e_cur(d): d["curriculum"]["active_temporal"] = False; d["curriculum"]["day_length"] = None; return d
pack = copy_pack("configs/reference/model_pack", "mp_notemporal", {"levels/L0_demo/curriculum.yaml": e_cur})
try:
    u, env = compile(pack, "L0_demo"); env.reset()
    place(env, 0, [1, 1]); place(env, 1, [0, 0])
    o, r, d, i = act(env, ["INTERACT", "WAIT"]); print("INTERACT at SLEEP ok", i["successful_interactions"])
except Exception as e:
    print("FAILED:", type(e).__name__, str(e)[:300])
print("=== (ii) completion_bonus on multi_tick SLEEP (duration 3), temporal active")
u, env = compile("configs/reference/model_pack", "L0_demo"); env.reset()
place(env, 0, [1, 1]); place(env, 1, [0, 0])
for t in range(5):
    o, r, d, i = act(env, ["INTERACT", "WAIT"])
    print(f" tick {t}: progress={env.interaction_progress[0].item()} last_aff={env._last_affordances[0]} shaping={round(i['reward_components']['shaping'][0].item(),4)} succ={i['successful_interactions']}")
print("=== (ii-b) interrupted by movement")
env.reset(); place(env, 0, [1, 1]); place(env, 1, [0, 0])
act(env, ["INTERACT", "WAIT"]); act(env, ["INTERACT", "WAIT"]); print(" progress after 2 INTERACT:", env.interaction_progress[0].item())
act(env, ["UP", "WAIT"]); print(" after UP:", env.interaction_progress[0].item(), "pos", env.positions[0].tolist())
act(env, ["DOWN", "WAIT"]); act(env, ["INTERACT", "WAIT"]); print(" after return+INTERACT:", env.interaction_progress[0].item())
print("=== (iii) opening hours vs day_length 48, window 6-18")
def e_cur2(d): d["curriculum"]["day_length"] = 48; return d
def e_aff(d):
    for a in d["affordances"]["affordances"]:
        if a["name"] == "SLEEP": a["opening_hours"] = {"enabled": True, "schedule": [{"start": 6, "end": 18}]}
    return d
pack = copy_pack("configs/reference/model_pack", "mp_day48", {"levels/L0_demo/curriculum.yaml": e_cur2, "levels/L0_demo/affordances.yaml": e_aff})
try:
    u, env = compile(pack, "L0_demo"); env.reset()
    print(" day_length", env.day_length, {h: env._is_affordance_open("SLEEP", hour=h) for h in (3, 10, 20, 30, 40, 47)})
except Exception as e:
    print("FAILED:", type(e).__name__, str(e)[:400])
print("=== (iv) current_tick passed to multi-tick effects")
