import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
def ed(d):
    for m in d["bars"]["meters"]:
        if m["name"] == "health":
            m["initial"] = 0.5; m["recovery"]["natural"] = 0.05
    return d
pack = copy_pack("configs/test/items_smoke", "natural", {"levels/L0_smoke/bars.yaml": ed})
u, env = compile(pack, "L0_smoke"); env.reset()
hi = env.meter_name_to_index["health"]
vals = []
for _ in range(9):
    act(env, ["WAIT", "WAIT"]); vals.append(round(env.meters[0, hi].item(), 4))
print("health over 9 idle ticks with recovery.natural=0.05:", vals)
# natural_recovery in meter token identity payload
mt = env.token_spec.get_type("meter")
feats = mt.payload_features; idx = feats.index("natural_recovery")
print("meter slot ctx natural_recovery lane:", [round(p[idx], 4) for p in mt.slot_context_payloads], "meters", [b.filler_ref for b in mt.slot_bindings])
# baseline
u0, env0 = compile("configs/test/items_smoke", "L0_smoke")
print("layout_hash differs with natural change:", env0.token_spec.get_type('meter').slot_context_payloads != env.token_spec.get_type('meter').slot_context_payloads)
