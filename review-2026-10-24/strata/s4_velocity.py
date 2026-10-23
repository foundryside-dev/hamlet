"""H12: velocity lane in the self token is unbounded under wrap / in world units on continuous."""
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
def self_row(env, obs):
    spec = env.token_spec
    for (t, slot, start, end) in spec.row_layout():
        if t == "self":
            return obs[0, start:end].tolist()
u = UniverseCompiler().compile(Path("configs/differential/boundary_wrap"), primary_level="L1_full_observability")
env = VectorizedHamletEnv.from_universe(u, level_name="L1_full_observability", num_agents=1, device="cpu")
env.reset(); env.positions[:] = torch.tensor([[7, 3]])
obs, *_ = env.step(torch.tensor([env.action_ids["RIGHT"]]))
print("wrap grid: pos after RIGHT from x=7:", env.positions.tolist(), "velocity:", env._velocity.tolist())
print("self token row:", self_row(env, obs))
