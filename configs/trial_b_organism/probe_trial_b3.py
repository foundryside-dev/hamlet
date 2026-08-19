"""Trial B diagnostic B3 probe (countersigned facet 7): contested growth.

Two organisms, one food source. What the reachable representation CAN show:
exclusive, permanent membership (a tip claimed by organism 1 cannot be claimed
by organism 2), both extents observation-encoded, both organisms absorbing
from the single shared warehouse. What it CANNOT show — exclusive CELL
occupancy between two masses — inherits the facet-2/3 gap: there are no
durable cells to contest.
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_b_organism")
LEVEL = "L1_contested"
A = (0, 0, 0, 0, 0)
A2 = (3, 3, 0, 0, 0)
W = (3, 3, 3, 3, 3)

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

spec = universe.observation_spec
offs = {}
off = 0
for f in spec.fields:
    if "organism" in f.name:
        offs[f.name] = off
    off += f.dims
print(f"== Both extents are compiled observation fields: {offs} ==")
assert "organism_size" in offs and "organism2_size" in offs

env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=4, device=torch.device("cpu"))
env.reset()
aff = {k: tuple(int(x) for x in v) for k, v in env.affordances.items()}
print(f"  affordances: {aff}")
assert aff["ROOT"] == A and aff["ROOT2"] == A2 and aff["WAREHOUSE"] == W

label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
INTERACT = label_to_action["INTERACT"]
WAIT = label_to_action["WAIT"]
i_rooted = env.meter_name_to_index["rooted"]
i_biomass = env.meter_name_to_index["biomass"]


def park(agent: int, pos: tuple) -> None:
    env.positions[agent] = torch.tensor(pos, device=env.device, dtype=env.positions.dtype)


def step(acts: list):
    return env.step(torch.tensor(acts, device=env.device, dtype=torch.long))


print("== Two organisms form: agents 0,1 join organism 1; agent 2 joins organism 2 ==")
park(0, A)
park(1, A)
park(2, A2)
park(3, (1, 1, 1, 1, 1))
step([INTERACT, INTERACT, INTERACT, WAIT])
rooted = [round(env.meters[i, i_rooted].item(), 3) for i in range(4)]
print(f"  rooted: {rooted}  (1 = organism 1, 2 = organism 2, 0 = neither)")
assert rooted == [1.0, 1.0, 2.0, 0.0]

print("== Exclusive membership: an organism-1 tip touching ROOT2 is refused ==")
park(0, A2)
step([INTERACT, WAIT, WAIT, WAIT])
rooted_after = [round(env.meters[i, i_rooted].item(), 3) for i in range(4)]
print(f"  rooted after agent 0 INTERACTs at ROOT2: {rooted_after}")
assert rooted_after == [1.0, 1.0, 2.0, 0.0], "membership was not exclusive"

obs = env._get_observations()
o1 = round(obs[0, offs["organism_size"]].item(), 6)
o2 = round(obs[0, offs["organism2_size"]].item(), 6)
print(f"== Both extents in the observation: organism_size={o1} organism2_size={o2} ==")
assert abs(o1 - 0.002) < 1e-6 and abs(o2 - 0.001) < 1e-6

print("== The single shared source: members of BOTH organisms absorb at W ==")
park(0, W)
park(2, W)
step([INTERACT, WAIT, INTERACT, WAIT])
b = [round(env.meters[i, i_biomass].item(), 3) for i in range(4)]
print(f"  biomass: {b}  (agent 0 from organism 1, agent 2 from organism 2, controls 0)")
assert b[0] == 0.2 and b[2] == 0.2 and b[1] == 0.0 and b[3] == 0.0

print()
print("B3 DIAGNOSTIC COMPLETE: exclusive permanent membership, per-organism extents in the")
print("observation, and shared-source absorption all work; exclusive CELL occupancy between")
print("two masses cannot be run — it inherits the facet-2/3 gap (no durable cells exist).")
