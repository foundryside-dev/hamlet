"""Trial L runtime probe (protocol §6 leg (b)). Lives in the trial pack, never under src/townlet/.

Facets:
  1: per-agent timer state per gated affordance exists in the compiled universe
  2: timer advances +1/tick while unused; resets on a successful use
  3: interaction effect applies iff timer >= declared cooldown (time gate, not stock)
  4: timer is an observation field the policy reads; encoded value tracks facet 2
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_l_cooldown")
LEVEL = "L0_effects"

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

print("== Facet 1: compiled timer state ==")
spec = universe.observation_spec
timer_fields = {}
offset = 0
for f in spec.fields:
    if "since_bed" in f.name or "since_food" in f.name:
        timer_fields[f.name] = (offset, f.dims)
        print(f"  field {f.name!r}: offset={offset} dims={f.dims}")
    offset += f.dims
print(f"  total_dims={spec.total_dims}")

env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=1, device=torch.device("cpu"))
env.reset()

i_bed = env.meter_name_to_index["since_bed"]
i_food = env.meter_name_to_index["since_food"]
i_energy = env.meter_name_to_index["energy"]

label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
INTERACT = torch.tensor([label_to_action["INTERACT"]])
WAIT = torch.tensor([label_to_action["WAIT"]])


def park(name: str) -> None:
    env.positions[:] = torch.tensor(env.affordances[name], device=env.device, dtype=env.positions.dtype)


def meters() -> tuple[float, float, float]:
    return (
        round(env.meters[0, i_bed].item(), 4),
        round(env.meters[0, i_food].item(), 4),
        round(env.meters[0, i_energy].item(), 4),
    )


print("\n== Facet 2/3: use, immediate reuse, idle ticks, reuse after cooldown ==")
print(f"  t0 (post-reset)            since_bed/since_food/energy = {meters()}")

park("BED")
env.step(INTERACT)
print(f"  after INTERACT@BED         {meters()}   <- expect since_bed reset (~0/1), energy +0.1")

env.step(INTERACT)
print(f"  immediate 2nd INTERACT@BED {meters()}   <- expect NO energy change (on cooldown), timer keeps counting")

for _ in range(9):
    env.step(WAIT)
print(f"  after 9 WAIT ticks         {meters()}   <- expect since_bed ~ +1/tick monotone")

env.step(INTERACT)
print(f"  INTERACT@BED post-cooldown {meters()}   <- expect energy +0.1 again, since_bed reset")

print("\n== Facet 1/2 independence: FOOD timer is separate ==")
park("FOOD")
env.step(INTERACT)
print(f"  after INTERACT@FOOD        {meters()}   <- since_food resets; since_bed keeps counting")
env.step(INTERACT)
print(f"  immediate 2nd INTERACT@FOOD{meters()}   <- no energy change (4-tick cooldown)")
for _ in range(4):
    env.step(WAIT)
env.step(INTERACT)
print(f"  INTERACT@FOOD post-cooldown{meters()}   <- energy +0.2 again")

print("\n== Facet 4: observation carries the timer ==")
obs, *_ = env.step(WAIT)
for name, (off, dims) in timer_fields.items():
    print(f"  obs[{off}] ({name}) = {round(obs[0, off].item(), 6)}   raw meter = {meters()}")
env.step(WAIT)
obs2, *_ = env.step(WAIT)
for name, (off, dims) in timer_fields.items():
    print(f"  two ticks later obs[{off}] ({name}) = {round(obs2[0, off].item(), 6)}")
