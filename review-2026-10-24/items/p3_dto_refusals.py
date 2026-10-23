import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import traceback
print("=== 45f501e15b max_items_per_agent: 0")
def ed(d): d["items"]["max_items_per_agent"] = 0; return d
pack = copy_pack("configs/test/items_smoke", "mipa0", {"items.yaml": ed})
try:
    u, env = compile(pack, "L0_smoke")
    print("compiled; items_catalog is", u.items_catalog, "; level items_appearance:", u.get_level("L0_smoke").items_appearance is not None, "; item_manager", env.item_manager)
    print("GET in action ids?", "GET" in env.action_ids)
except Exception as e:
    print("refused:", type(e).__name__, str(e)[:600])
print("=== 6c49488b22 fixed_positions 3-tuple")
from townlet.config.items_config import SpawnPlacementConfig, ItemAppearanceRuleConfig
try:
    SpawnPlacementConfig(mode="fixed", fixed_positions=[(1, 2, 3)])
    print("accepted 3-tuple")
except Exception as e:
    print("refused:", str(e).splitlines()[0:3])
print("=== 6b24c0bd83 capabilities key on affordance")
from townlet.config.affordances_v2_config import AffordanceParamConfig
try:
    AffordanceParamConfig(name="X", interaction_type="instant", interactions={}, opening_hours={"enabled": False}, deployment={"type": "fixed", "positions": [[1,1]]}, capabilities=[{"type": "cooldown", "cooldown_ticks": 5}])
    print("accepted")
except Exception as e:
    print("refused:", str(e).splitlines()[0:3])
print("=== 1b9af9088c CommandConfig position as coordinates")
from townlet.config.effects_config import CommandConfig
try:
    CommandConfig(spawn_item="apple", position=[1, 2]); print("accepted list")
except Exception as e:
    print("refused:", str(e).splitlines()[0:3])
print("=== 787aaa29f1 item var vec2f")
for exposed in ([], ["agent"]):
    def ed2(d, exposed=exposed):
        for v in d["variables"]["declarations"]:
            if v["id"] == "freshness":
                v["type"] = "vec2f"; v["initial_value"] = [100.0, 50.0]; v["exposed_to"] = exposed
                if exposed: v["normalization"] = {"kind": "minmax", "min": 0.0, "max": 100.0, "clip": True}
        return d
    pack = copy_pack("configs/test/items_smoke", f"vec2f_{len(exposed)}", {"variables.yaml": ed2})
    try:
        u, env = compile(pack, "L0_smoke")
        print(f"exposed={exposed}: compiled; item_vfs shape", env.vfs_registry.item_vfs.shape)
        try:
            env.reset(); print("  reset OK; items", [(i.item_type) for i in env.item_manager.get_all_items()], "row0", env.vfs_registry.item_vfs[0].tolist())
        except Exception as e:
            print("  reset crashed:", type(e).__name__, str(e)[:300])
    except Exception as e:
        print(f"exposed={exposed}: compile refused:", type(e).__name__, str(e)[:400])
