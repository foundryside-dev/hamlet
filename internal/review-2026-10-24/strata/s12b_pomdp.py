import torch
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
torch.manual_seed(0)
for pack, level in [("configs/differential/div003_rect", "L1_full_observability"), ("configs/aspatial_test", "L0"), ("configs/test/gridnd_4d_pack", "L0_test"), ("configs/test/action_space/continuous1d", "L0")]:
    u = UniverseCompiler().compile(Path(pack), primary_level=level)
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=3, device="cpu"); env.reset(); live_allfalse = 0
    for t in range(40):
        m = env.get_action_masks(); live_allfalse += int(((~m.any(dim=1)) & (~env.dones)).sum())
        env.step(torch.multinomial(m.float() + 1e-9, 1).squeeze(1))
    print(f"{pack}: live agents with all-False mask rows over 40 ticks = {live_allfalse}")
u = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L1_full_observability")
a, b = u.get_level("L1_full_observability").token_spec, u.get_level("L2_partial_observability").token_spec
hashes = [n for n in dir(a) if "hash" in n and not n.startswith("_")]
print("POMDP same tensor: total_dims", a.total_dims, b.total_dims, {n: getattr(a, n) == getattr(b, n) for n in hashes})
u = UniverseCompiler().compile(Path("configs/differential/div003_cubic_partial"), primary_level="L2_partial_observability")
env = VectorizedHamletEnv.from_universe(u, level_name="L2_partial_observability", num_agents=1, device="cpu"); env.reset()
env.positions[:] = torch.tensor([[4, 4, 1]]); obs = env._get_observations()
pos, dep = env._affordance_layout(); dist = (pos - env.positions).abs().sum(1)
pres = [obs[0, s] for (t, slot, s, e) in env.token_spec.row_layout() if t == "affordance"]
print("cubic POMDP radius", env.substrate._token_vision_radius(0.5), "| (manhattan dist, presence):", sorted(zip(dist.tolist(), [float(p) for p in pres])))
