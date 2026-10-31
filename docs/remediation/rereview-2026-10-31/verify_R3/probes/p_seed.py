import torch
from r3pack import *
from townlet.determinism import seed_all
pack = build()
VARS = ["g_rand", "a_two", "g_target", "a_target"]
def trace(env, steps=10):
    names = {a.name: a.id for a in env.action_space.actions}
    r = env.vfs_registry
    out = [{v: r.get(v, reader="engine").clone() for v in VARS}]
    for t in range(steps):
        env.step(torch.full((env.num_agents,), names["WAIT"]))
        out.append({v: r.get(v, reader="engine").clone() for v in VARS})
    return out
# N-independence
e4, _ = make_env(pack, 4, 3); t4 = trace(e4)
e8, _ = make_env(pack, 8, 3); t8 = trace(e8)
print("N-indep (worlds 0..3 at N=4 vs N=8):", all(torch.equal(a[v], b[v][:4]) for a, b in zip(t4, t8) for v in VARS))
e1, _ = make_env(pack, 1, 3); t1 = trace(e1)
print("N-indep (world 0 at N=1 vs N=8):", all(torch.equal(a[v], b[v][:1]) for a, b in zip(t1, t8) for v in VARS))
# episodes
eA, _ = make_env(pack, 4, 3); ep1 = trace(eA, 3); eA.reset(); ep2 = trace(eA, 3); eA.reset(); ep3 = trace(eA, 3)
eB, _ = make_env(pack, 4, 3); ep1b = trace(eB, 3); eB.reset(); ep2b = trace(eB, 3)
print("ep2 != ep1:", not torch.equal(ep1[0]["g_rand"], ep2[0]["g_rand"]), " ep2 reproducible:", all(torch.equal(a[v], b[v]) for a, b in zip(ep2, ep2b) for v in VARS))
# two envs in one process, different seeds, interleaved
from townlet.environment.vectorized_env import VectorizedHamletEnv
from harness import compile_pack
u = compile_pack(pack, ILEVEL)
seed_all(1); envX = VectorizedHamletEnv.from_universe(u, level_name=ILEVEL, num_agents=2, device="cpu"); envX.reset()
gx_ep1 = envX.vfs_registry.get("g_rand", reader="engine").clone()
seed_all(2); envY = VectorizedHamletEnv.from_universe(u, level_name=ILEVEL, num_agents=2, device="cpu"); envY.reset()
envX.reset(); gx_ep2_after_Y = envX.vfs_registry.get("g_rand", reader="engine").clone()
# reference: envX alone, seed 1, two resets
seed_all(1); envR = VectorizedHamletEnv.from_universe(u, level_name=ILEVEL, num_agents=2, device="cpu"); envR.reset(); envR.reset()
gr_ep2 = envR.vfs_registry.get("g_rand", reader="engine").clone()
print("envX(seed1) ep2 equals solo seed1 ep2 after constructing envY(seed2):", torch.equal(gx_ep2_after_Y, gr_ep2), gx_ep2_after_Y.tolist(), gr_ep2.tolist())
# what seed does X's ep2 match?
seed_all(2); envS = VectorizedHamletEnv.from_universe(u, level_name=ILEVEL, num_agents=2, device="cpu"); envS.reset(); envS.reset()
print("   ...equals solo seed2 ep2 instead:", torch.equal(gx_ep2_after_Y, envS.vfs_registry.get("g_rand", reader="engine")))
# same seed, two envs: identical streams
seed_all(5); P = VectorizedHamletEnv.from_universe(u, level_name=ILEVEL, num_agents=2, device="cpu"); P.reset()
Q = VectorizedHamletEnv.from_universe(u, level_name=ILEVEL, num_agents=2, device="cpu"); Q.reset()
print("two envs same seed, same episode: identical g_rand:", torch.equal(P.vfs_registry.get("g_rand", reader="engine"), Q.vfs_registry.get("g_rand", reader="engine")))
# initial_seed vs manual_seed-less reseed: does anything in env construction/reset call manual_seed?
seed_all(9); s0 = torch.initial_seed(); E = VectorizedHamletEnv.from_universe(u, level_name=ILEVEL, num_agents=2, device="cpu"); E.reset(); [E.step(torch.zeros(2, dtype=torch.long)) for _ in range(5)]
print("initial_seed unchanged by env construct/reset/step:", torch.initial_seed() == s0)
