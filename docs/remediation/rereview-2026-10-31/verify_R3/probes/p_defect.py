import torch
from r3pack import *
pack = build("dfx")
env, _ = make_env(pack, 3, 1)
names = {a.name: a.id for a in env.action_space.actions}
orig = env.vfs_random_streams.generators
def attempt(label, fn):
    s0 = torch.get_rng_state().clone()
    try:
        fn(); print(f"{label:50s} NO ERROR; global RNG consumed={not torch.equal(s0, torch.get_rng_state())}")
    except Exception as e:
        print(f"{label:50s} {type(e).__name__}: {short(str(e), 160)}  global RNG consumed={not torch.equal(s0, torch.get_rng_state())}")
env.vfs_random_streams.generators = lambda n, d: None
attempt("step with world_rngs=None", lambda: env.step(torch.full((3,), names["WAIT"])))
env.vfs_random_streams.generators = lambda n, d: orig(n, d)[:2]
attempt("step with 2 streams for 3 worlds", lambda: env.step(torch.full((3,), names["WAIT"])))
env.vfs_random_streams.generators = lambda n, d: orig(n + 1, d)
attempt("step with 4 streams for 3 worlds", lambda: env.step(torch.full((3,), names["WAIT"])))
env.vfs_random_streams.generators = orig
attempt("normal step", lambda: env.step(torch.full((3,), names["WAIT"])))
