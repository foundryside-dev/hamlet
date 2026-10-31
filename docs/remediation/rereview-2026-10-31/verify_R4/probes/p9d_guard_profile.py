import torch
from harness import *  # noqa
from harness import make_pack, decl, try_compile, build_env, short
from townlet.determinism import seed_all
u, err = try_compile(make_pack("guardp", variables=lambda v: v["declarations"].append(decl("g", scope="global", initial_value=0.0, expression="uniform()"))))
seed_all(1); env = build_env(u, 3); s0 = torch.get_rng_state().clone()
vfs = env._current_vfs_state(); bars = env._current_bar_state()
env.vfs_evaluator.begin_instant(bars, vfs, env.device)
try:
    env.vfs_evaluator.evaluate_global_profile(profile=u.compiled_vfs_profiles.global_profile, bars=bars, vfs_state=vfs, marks={"g"}, device=env.device, agent_positions=None, affordance_positions=None, draws=None)
    print("  global profile with draws=None: NO ERROR")
except Exception as ex:
    print(f"  global profile with draws=None: {type(ex).__name__}: {short(str(ex), 160)}")
print("    global rng consumed:", not torch.equal(s0, torch.get_rng_state()))
