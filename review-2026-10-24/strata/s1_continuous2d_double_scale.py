"""H2: Continuous2D bakes movement_delta into action deltas AND apply_movement scales again."""
import torch
from townlet.substrate.continuous import Continuous1DSubstrate, Continuous2DSubstrate, Continuous3DSubstrate
disc = {"num_directions": 8, "num_magnitudes": 3}
s2 = Continuous2DSubstrate(0.0, 10.0, 0.0, 10.0, boundary="clamp", movement_delta=0.5, interaction_radius=1.0,
                           action_discretization=disc, distance_metric="euclidean")
acts = s2.get_default_actions()
full = [a for a in acts if a.name == "MOVE_0_2"][0]   # 0 deg (east), magnitude 1.0
print("MOVE_0_2 declared delta:", full.delta)
pos = torch.tensor([[5.0, 5.0]])
new = s2.apply_movement(pos, torch.tensor([full.delta]))
print("2D displacement for magnitude-1.0 east step (expected 0.5):", (new - pos).tolist())
s1 = Continuous1DSubstrate(0.0, 10.0, boundary="clamp", movement_delta=0.5, interaction_radius=1.0,
                           action_discretization=disc, distance_metric="euclidean")
r = [a for a in s1.get_default_actions() if a.name == "RIGHT"][0]
print("1D RIGHT delta", r.delta, "displacement:", (s1.apply_movement(torch.tensor([[5.0]]), torch.tensor([r.delta])) - 5.0).tolist())
s3 = Continuous3DSubstrate(0,10,0,10,0,10, boundary="clamp", movement_delta=0.5, interaction_radius=1.0,
                           action_discretization=disc, distance_metric="euclidean")
r3 = [a for a in s3.get_default_actions() if a.name == "RIGHT"][0]
print("3D RIGHT delta", r3.delta, "displacement:", (s3.apply_movement(torch.tensor([[5.0,5.0,5.0]]), torch.tensor([r3.delta])) - 5.0).tolist())
print("1D action names:", [a.name for a in s1.get_default_actions()], "(action_discretization 8x3 declared, consumed?)")
print("3D action names:", [a.name for a in s3.get_default_actions()])
