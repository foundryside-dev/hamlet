"""Trial F runtime probe (protocol §6 leg (b)). Lives in the trial pack, never under src/townlet/.

Facets:
  1: the item carries a declared wear state (item-scoped VFS variable in the compiled universe)
  2: USE decrements wear by the declared amount; idle ticks do not change it
  3: at zero wear the tool stops working (guarded effect no longer fires)
  4: wear is observable to the agent (obs_item_slots block tracks the value)
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_f_durability")
LEVEL = "L0_tools"

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

print("== Facet 1: compiled wear state ==")
spec = universe.observation_spec
vfs_spec = universe.vfs_observation_spec
print(f"  item_profile_vars = {vfs_spec.item_profile_vars}")
print(f"  item_vars_per_slot = {vfs_spec.item_vars_per_slot}, item_vfs_dim = {vfs_spec.item_vfs_dim}")
item_field = None
offset = 0
for f in spec.fields:
    if f.name == "obs_item_slots":
        item_field = (offset, f.dims)
        print(f"  field 'obs_item_slots': offset={offset} dims={f.dims} feature={f.feature!r}")
    offset += f.dims
print(f"  total_dims={spec.total_dims}")

env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=1, device=torch.device("cpu"))
env.reset()

i_energy = env.meter_name_to_index["energy"]
label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
print(f"  item actions available: {sorted(a for a in label_to_action if 'GET' in a or 'SLOT' in a)}")
GET = torch.tensor([label_to_action["GET"]])
USE = torch.tensor([label_to_action["USE_SLOT_0"]])
WAIT = torch.tensor([label_to_action["WAIT"]])


def durability() -> float:
    inst = next(iter(env.item_manager.held_items.values()), None) or next(iter(env.item_manager.active_items.values()), None)
    col = env.vfs_registry.item_profile_map["tool_stats"]["durability"]
    return round(env.vfs_registry.item_vfs[inst.vfs_index, col].item(), 4)


def energy() -> float:
    return round(env.meters[0, i_energy].item(), 4)


def item_obs(obs) -> list[float]:
    off, dims = item_field
    return [round(obs[0, off + i].item(), 4) for i in range(dims)]


inst = next(iter(env.item_manager.active_items.values()))
print(f"\n  spawned hammer at {inst.position}, vfs_index={inst.vfs_index}, durability={durability()}   <- expect 3.0 (facet 1)")

print("\n== Facet 2/4: pick up, use, idle, use again ==")
env.positions[:] = torch.tensor(inst.position, device=env.device, dtype=env.positions.dtype)
obs, *_ = env.step(GET)
print(f"  after GET       durability={durability()} energy={energy()} obs_item_slots={item_obs(obs)}")

obs, *_ = env.step(USE)
print(f"  after USE #1    durability={durability()} energy={energy()} obs_item_slots={item_obs(obs)}   <- expect 2.0, +0.1 energy")

for _ in range(5):
    obs, *_ = env.step(WAIT)
print(f"  after 5 WAITs   durability={durability()} energy={energy()} obs_item_slots={item_obs(obs)}   <- expect durability UNCHANGED (per-use, not per-tick)")

obs, *_ = env.step(USE)
print(f"  after USE #2    durability={durability()} energy={energy()} obs_item_slots={item_obs(obs)}   <- expect 1.0, +0.1 energy")
obs, *_ = env.step(USE)
print(f"  after USE #3    durability={durability()} energy={energy()} obs_item_slots={item_obs(obs)}   <- expect 0.0, +0.1 energy")

print("\n== Facet 3: at zero wear the tool stops working ==")
obs, *_ = env.step(USE)
print(f"  after USE #4    durability={durability()} energy={energy()} obs_item_slots={item_obs(obs)}   <- expect NO energy change, durability stays 0.0")
obs, *_ = env.step(USE)
print(f"  after USE #5    durability={durability()} energy={energy()} obs_item_slots={item_obs(obs)}   <- same")
