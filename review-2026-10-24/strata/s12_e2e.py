import torch
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
torch.manual_seed(0)
for pack, level in [("configs/differential/div003_rect", "L1_full_observability"), ("configs/aspatial_test", "L0"),
                    ("configs/differential/div003_cubic_partial", "L2_partial_observability"), ("configs/test/gridnd_4d_pack", "L0_test"),
                    ("configs/test/action_space/continuous1d", "L0"), ("configs/differential/boundary_wrap", "L1_full_observability")]:
    u = UniverseCompiler().compile(Path(pack), primary_level=level)
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=3, device="cpu")
    obs = env.reset(); bad = 0; lo = torch.full((env.substrate.position_dim,), 1e9); hi = -lo.clone()
    for t in range(40):
        m = env.get_action_masks()
        if not bool(m.any(dim=1).all()): bad += 1
        acts = torch.multinomial(m.float() + 1e-9, 1).squeeze(1)
        obs, r, d, info = env.step(acts)
        if env.substrate.position_dim: lo = torch.minimum(lo, env.positions.float().min(0)[0]); hi = torch.maximum(hi, env.positions.float().max(0)[0])
        assert torch.isfinite(obs).all(), "non-finite obs"
    print(f"{pack}/{level}: dims={env.observation_dim} 40 steps OK; ticks with an all-False mask row={bad}; pos range lo={lo.tolist()} hi={hi.tolist()}; obs min/max={obs.min().item():.3f}/{obs.max().item():.3f}")
u = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L1_full_observability")
a, b = u.get_level("L1_full_observability").token_spec, u.get_level("L2_partial_observability").token_spec
print("POMDP same tensor: total_dims", a.total_dims, b.total_dims, "layout_hash equal:", a.layout_hash == b.layout_hash)
# cubic partial: presence of affordance tokens vs manhattan distance, radius from longest axis (8) -> ceil(0.5*4)=2
u = UniverseCompiler().compile(Path("configs/differential/div003_cubic_partial"), primary_level="L2_partial_observability")
env = VectorizedHamletEnv.from_universe(u, level_name="L2_partial_observability", num_agents=1, device="cpu"); env.reset()
env.positions[:] = torch.tensor([[4, 4, 1]]); obs = env._get_observations()
pos, dep = env._affordance_layout(); dist = (pos - env.positions).abs().sum(1)
pres = [obs[0, s] for (t, slot, s, e) in env.token_spec.row_layout() if t == "affordance"]
print("cubic POMDP radius", env.substrate._token_vision_radius(0.5), "| (manhattan dist, presence):", sorted(zip(dist.tolist(), [float(p) for p in pres])))
