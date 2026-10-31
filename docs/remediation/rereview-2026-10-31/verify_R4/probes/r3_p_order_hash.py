import torch, shutil, yaml
from r3pack import *
from harness import compile_pack
def hashes(p):
    u = compile_pack(p, ILEVEL); lv = u.get_level(ILEVEL)
    out = {}
    for obj, pre in [(u, "u."), (lv, "lv.")]:
        for a in dir(obj):
            if a.endswith("_hash") and not a.startswith("_"):
                v = getattr(obj, a)
                if not callable(v): out[pre + a] = str(v)[:16]
    return out
a = build("oh_a"); b = build("oh_b", decl_order_reverse=True)
ha, hb = hashes(a), hashes(b)
print("hashes moved by declaration reorder:", {k: (ha[k], hb[k]) for k in ha if ha[k] != hb[k]})
# transport-only change: move the two random agent decls into a separate file that sorts before variables.yaml
c = build("oh_c")
v = yaml.safe_load(open(c / "variables.yaml"))
decls = v["variables"]["declarations"]
moved = [d for d in decls if d["id"] in ("a_two",)]
v["variables"]["declarations"] = [d for d in decls if d["id"] not in ("a_two",)]
yaml.safe_dump(v, open(c / "variables.yaml", "w"), sort_keys=False)
(c / "aaa").mkdir(exist_ok=True)
yaml.safe_dump({"variables": {"version": "1.0", "declarations": moved}}, open(c / "aaa" / "early.yaml", "w"), sort_keys=False)
try:
    hc = hashes(c)
    print("hashes moved by moving a_two to aaa/early.yaml:", {k: (ha[k], hc[k]) for k in ha if ha[k] != hc.get(k)})
    def tr(p):
        env, _ = make_env(p, 3, 9); names = {x.name: x.id for x in env.action_space.actions}; out = []
        for _ in range(5):
            env.step(torch.full((3,), names["WAIT"])); out.append(env.vfs_registry.get("a_two", reader="engine").clone())
        return out
    print("a_two trajectory equal after file move:", all(torch.equal(x, y) for x, y in zip(tr(a), tr(c))))
except Exception as e:
    print("move variant:", type(e).__name__, str(e)[:300])
