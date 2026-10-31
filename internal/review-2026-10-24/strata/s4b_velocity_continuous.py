from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
u = UniverseCompiler().compile(Path("configs/test/action_space/continuous1d"), primary_level="L0")
env = VectorizedHamletEnv.from_universe(u, level_name="L0", num_agents=1, device="cpu")
env.reset(); env.positions[:] = torch.tensor([[5.0]])
obs, *_ = env.step(torch.tensor([env.action_ids["RIGHT"]]))
for (t, slot, start, end) in env.token_spec.row_layout():
    if t == "self": print("continuous1d self token row (presence, pos..., vel...):", obs[0, start:end].tolist())
print("velocity:", env._velocity.tolist(), " bounds [0,10], movement_delta 0.5")
