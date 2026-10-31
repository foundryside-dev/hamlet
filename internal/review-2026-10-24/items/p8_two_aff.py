import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import copy
def e_env(d):
    d["environment"]["affordances"].append({"name": "health_station", "description": "h", "category": "x"}); return d
def e_aff(d):
    a = copy.deepcopy(d["affordances"]["affordances"][0]); a["name"] = "health_station"
    a["interactions"]["on_start"] = [{"modify": "target.bar.health", "value": "target.bar.health + 0.3"}]
    d["affordances"]["affordances"].append(a); return d
def e_tr(d): d["training"]["enabled_affordances"] = ["energy_station", "health_station"]; return d
pack = copy_pack("configs/test/items_smoke", "twoaff", {"environment.yaml": e_env, "levels/L0_smoke/affordances.yaml": e_aff, "levels/L0_smoke/training.yaml": e_tr})
try:
    u, env = compile(pack, "L0_smoke"); env.reset()
    place(env, 0, [1, 1]); place(env, 1, [4, 4])
    ei, hi = env.meter_name_to_index["energy"], env.meter_name_to_index["health"]
    env.meters[0, ei] = 0.5; env.meters[0, hi] = 0.5
    o, r, d, info = act(env, ["INTERACT", "WAIT"])
    print("two affordances at [1,1]: compiled; after one INTERACT energy", round(env.meters[0, ei].item(), 3), "health", round(env.meters[0, hi].item(), 3), "successful_interactions", info["successful_interactions"])
except Exception as e:
    print("refused:", type(e).__name__, str(e)[:400])
