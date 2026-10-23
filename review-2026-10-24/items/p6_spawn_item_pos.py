import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
for pos in ["target", "self", None]:
    def ed(d, pos=pos):
        cmd = {"spawn_item": "apple"}
        if pos: cmd["position"] = pos
        d["affordances"]["affordances"][0]["interactions"]["on_start"] = [cmd]
        return d
    pack = copy_pack("configs/test/items_smoke", f"spawn_{pos}", {"levels/L0_smoke/affordances.yaml": ed})
    try:
        u, env = compile(pack, "L0_smoke"); env.reset()
        place(env, 0, [1, 1]); place(env, 1, [4, 4])
        n0 = len(env.item_manager.active_items)
        act(env, ["INTERACT", "WAIT"])
        print(f"position={pos}: INTERACT ok; items {n0}->{len(env.item_manager.active_items)}")
    except Exception as e:
        print(f"position={pos}: {type(e).__name__}: {str(e)[:300]}")
