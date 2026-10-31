"""World-0 differential with random draws: worlds 1..N-1 must be bitwise identical between A (all cycle) and B (world 0 perturbed)."""
import sys, torch
from r3pack import *

def run(pack, n, steps, seed, mode):
    env, obs = make_env(pack, n, seed)
    names = {a.name: a.id for a in env.action_space.actions}
    ids = [a.id for a in env.action_space.actions]
    cycle = [names[x] for x in ["WAIT", "UP", "RIGHT", "WAIT", "DOWN", "LEFT", "GET"]]
    zero = torch.zeros(n)
    snaps = [[snap(env, w, obs, zero, env.dones) for w in range(n)]]
    for t in range(steps):
        a = torch.tensor([cycle[(t + w) % len(cycle)] for w in range(n)], dtype=torch.long)
        if mode == "B":
            a[0] = ids[(t * 5) % len(ids)]
            if t % 3 == 0:
                env.positions[0] = env.affordances["energy_station"].to(env.positions.dtype)
                a[0] = names["INTERACT"]
            if t == 20:
                env.meters[0, :] = 0.0  # kill world 0's agent
        obs, rewards, dones, info = env.step(a)
        snaps.append([snap(env, w, obs, rewards, dones) for w in range(n)])
    obs = env.reset()
    snaps.append([snap(env, w, obs, zero, env.dones) for w in range(n)])
    for t in range(6):
        a = torch.tensor([cycle[(t + w) % len(cycle)] for w in range(n)], dtype=torch.long)
        obs, rewards, dones, info = env.step(a)
        snaps.append([snap(env, w, obs, rewards, dones) for w in range(n)])
    return snaps, env

def eq(x, y):
    if isinstance(x, torch.Tensor):
        return x.dtype == y.dtype and x.shape == y.shape and bool(torch.equal(x, y)) or (x.is_floating_point() and bool(torch.equal(torch.isnan(x), torch.isnan(y))) and bool(torch.equal(torch.nan_to_num(x), torch.nan_to_num(y))))
    if isinstance(x, dict):
        return x.keys() == y.keys() and all(eq(x[k], y[k]) for k in x)
    return x == y

pack = build()
for n in [2, 4, 7]:
    A, envA = run(pack, n, 64, 11, "A")
    B, envB = run(pack, n, 64, 11, "B")
    A2, _ = run(pack, n, 64, 11, "A")
    bad = []
    for t, (sa, sb) in enumerate(zip(A, B)):
        for w in range(1, n):
            for k in sa[w]:
                if not eq(sa[w][k], sb[w][k]):
                    bad.append((t, w, k))
    aa = all(eq(sa[w], s2[w]) for sa, s2 in zip(A, A2) for w in range(n))
    w0diff = sum(1 for sa, sb in zip(A, B) if not eq(sa[0], sb[0]))
    sv_nonzero = sum(1 for s in A + B for w in range(n) if float(s[w]["registry"]["sv"]) != 0.0)
    items_seen = sum(len(s[w]["items"]) for s in B for w in range(n))
    print(f"N={n}: diffs in worlds 1..N-1: {len(bad)} first={bad[:5]}; A/A identical={aa}; world0 differs at {w0diff} snaps; sv nonzero snaps={sv_nonzero}; item rows seen={items_seen}; B dones end={envB.dones.tolist()}")
