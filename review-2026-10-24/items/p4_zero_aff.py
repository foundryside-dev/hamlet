import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
print("=== fba3d5aa3c zero affordances")
def e_env(d): d["environment"]["affordances"] = []; return d
def e_aff(d): d["affordances"]["affordances"] = []; return d
def e_tr(d): d["training"]["enabled_affordances"] = []; return d
def e_dr(d): d["drive"]["shaping"] = []; return d
pack = copy_pack("configs/test/items_smoke", "zeroaff", {"environment.yaml": e_env, "levels/L0_smoke/affordances.yaml": e_aff, "levels/L0_smoke/training.yaml": e_tr, "levels/L0_smoke/drive.yaml": e_dr})
try:
    u, env = compile(pack, "L0_smoke")
    obs = env.reset(); o, r, d, i = act(env, ["WAIT", "UP"]); print("compiled+reset+step OK; census", env.token_spec.census, "obs", obs.shape)
    print("INTERACT in action_ids", env.action_ids.get("INTERACT"), "mask interact", env.get_action_masks()[:, env.action_ids["INTERACT"]].tolist() if "INTERACT" in env.action_ids else None)
except Exception as e:
    import traceback; print("FAILED:", type(e).__name__, str(e)[:500])
print("=== approach_reward target not an affordance")
pack = copy_pack("configs/test/items_smoke", "zeroaff_shape", {"environment.yaml": e_env, "levels/L0_smoke/affordances.yaml": e_aff, "levels/L0_smoke/training.yaml": e_tr})
try:
    u, env = compile(pack, "L0_smoke"); env.reset(); o, r, d, i = act(env, ["WAIT", "WAIT"]); print("compiled; shaping component", i["reward_components"]["shaping"].tolist())
except Exception as e:
    print("refused:", type(e).__name__, str(e)[:400])
print("=== completion_bonus affordance not declared")
def e_dr2(d): d["drive"]["shaping"] = [{"type": "completion_bonus", "weight": 1.0, "affordance": "NOPE"}]; return d
pack = copy_pack("configs/test/items_smoke", "badcomp", {"levels/L0_smoke/drive.yaml": e_dr2})
try:
    u, env = compile(pack, "L0_smoke"); print("compiled (no refusal)")
except Exception as e:
    print("refused:", type(e).__name__, str(e)[:300])
