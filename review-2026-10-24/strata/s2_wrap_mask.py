"""H1: action mask forbids edge-crossing moves regardless of boundary mode (wrap never reachable)."""
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
u = UniverseCompiler().compile(Path("configs/differential/boundary_wrap"), primary_level="L1_full_observability")
env = VectorizedHamletEnv.from_universe(u, level_name="L1_full_observability", num_agents=2, device="cpu")
env.reset()
print("substrate.boundary =", env.substrate.boundary)
env.positions = torch.tensor([[0, 0], [7, 7]], dtype=torch.long)
masks = env.get_action_masks()
names = {a.id: a.name for a in env.action_space.actions}
for i in range(2):
    print(f"agent{i} at {env.positions[i].tolist()} masked-out:", [names[j] for j in range(masks.shape[1]) if not masks[i, j]])
left = env.action_ids["LEFT"]
print("apply_movement LEFT from (0,0) under wrap gives:", env.substrate.apply_movement(torch.tensor([[0, 0]]), env._movement_deltas[left].unsqueeze(0)).tolist())
# Force the move through step() to prove the env would wrap if the mask allowed it
env.positions = torch.tensor([[0, 0], [0, 0]], dtype=torch.long)
env.step(torch.tensor([left, left]))
print("positions after forced LEFT step from (0,0):", env.positions.tolist(), " velocity:", env._velocity.tolist())
