import torch
from r3pack import *
pack = build()
env, obs = make_env(pack, 3, 5)
names = {a.name: a.id for a in env.action_space.actions}
r = env.vfs_registry
prev = None
for t in range(12):
    if t == 3:
        env.meters[0, :] = 0.0
    obs, rew, dones, info = env.step(torch.full((3,), names["WAIT"]))
    row = {v: round(float(r.get(v, reader="engine")[0]), 4) for v in ["g_rand", "a_rand", "a_two", "a_seen", "a_target", "g_target"]}
    print(t, "done0=", bool(dones[0]), row, "obs0 hash", hash(obs[0].numpy().tobytes()) % 10**6, "meters0", env.meters[0,:2].tolist())
# stored-read check: a_seen(t) == a_rand(t-1) for live world 1
env, obs = make_env(pack, 3, 5)
last = r = None
r = env.vfs_registry
last = r.get("a_rand", reader="engine").clone()
ok = True
for t in range(10):
    obs, rew, dones, info = env.step(torch.full((3,), names["WAIT"]))
    seen = r.get("a_seen", reader="engine")
    if not torch.equal(seen[1:], last[1:]):
        ok = False; print("MISMATCH", t, seen.tolist(), last.tolist())
    last = r.get("a_rand", reader="engine").clone()
print("a_seen(t)==a_rand(t-1) (stored, observed value):", ok)
