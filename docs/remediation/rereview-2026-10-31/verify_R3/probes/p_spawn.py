import torch, yaml
from r3pack import *
p = build("spw", when="g_rand > 0.5")
f = p / "levels" / ILEVEL / "items.yaml"
d = yaml.safe_load(open(f))
d["items"][0]["spawn_count"] = 1; d["items"][0]["schedule"]["period"] = 2
d["items"][1]["spawn_count"] = 0; d["items"][2]["spawn_count"] = 0
yaml.safe_dump(d, open(f, "w"), sort_keys=False)
agree = dis = 0
for seed in range(6):
    env, obs = make_env(p, 8, seed)
    g = env.vfs_registry.get("g_rand", reader="engine")
    for w in range(8):
        has = any(it.item_type == "apple" for it in env.item_manager.items_in_world(w))
        agree += has == bool(g[w] > 0.5); dis += has != bool(g[w] > 0.5)
    # retries: a rejected world retries at tick 2 with that tick's g_rand
    names = {a.name: a.id for a in env.action_space.actions}
    before = [any(it.item_type == "apple" for it in env.item_manager.items_in_world(w)) for w in range(8)]
    for t in range(2):
        env.step(torch.full((8,), names["WAIT"]))
    g2 = env.vfs_registry.get("g_rand", reader="engine")
    after = [any(it.item_type == "apple" for it in env.item_manager.items_in_world(w)) for w in range(8)]
    for w in range(8):
        if not before[w]:
            agree += after[w] == bool(g2[w] > 0.5); dis += after[w] != bool(g2[w] > 0.5)
print("spawn decisions agreeing with own world's g_rand:", agree, "disagreeing:", dis)
