"""Trial M runtime probe (protocol §6 leg (b)). Lives in the trial pack, never under src/townlet/.

Facets:
  1: operations A/B/C and both progression traces exist in the compiled universe
  2: performing A writes its trace on completion; idle ticks change nothing
  3: B gated on the A-trace — no effect and no did_b leak before A; effect after
  4: chain to depth 3 — C refused after A alone, applies after A then B
  5: both traces are observation fields; encoded values flip when A/B complete
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_m_combo")
LEVEL = "L0_combo"

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

print("== Facet 1: compiled operations and traces ==")
spec = universe.observation_spec
trace_fields = {}
offset = 0
for f in spec.fields:
    if "did_a" in f.name or "did_b" in f.name:
        trace_fields[f.name] = (offset, f.dims)
        print(f"  field {f.name!r}: offset={offset} dims={f.dims}")
    offset += f.dims
print(f"  total_dims={spec.total_dims}")

env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=1, device=torch.device("cpu"))
env.reset()
print(f"  affordances in runtime: {sorted(env.affordances.keys())}")

i_a = env.meter_name_to_index["did_a"]
i_b = env.meter_name_to_index["did_b"]
i_energy = env.meter_name_to_index["energy"]

label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
INTERACT = torch.tensor([label_to_action["INTERACT"]])
WAIT = torch.tensor([label_to_action["WAIT"]])


def park(name: str) -> None:
    env.positions[:] = torch.tensor(env.affordances[name], device=env.device, dtype=env.positions.dtype)


def state() -> str:
    return (
        f"did_a={round(env.meters[0, i_a].item(), 4)} "
        f"did_b={round(env.meters[0, i_b].item(), 4)} "
        f"energy={round(env.meters[0, i_energy].item(), 4)}"
    )


print("\n== Facet 3 (first half): B before A does nothing, leaks nothing ==")
print(f"  t0 (post-reset)          {state()}   <- expect did_a=0 did_b=0 energy=0.5")
park("COMBO_B")
env.step(INTERACT)
print(f"  after INTERACT@COMBO_B   {state()}   <- expect NO change: gate closed, no did_b leak")

print("\n== Facet 4 (zeroth half): C at reset does nothing ==")
park("COMBO_C")
env.step(INTERACT)
print(f"  after INTERACT@COMBO_C   {state()}   <- expect NO change")

print("\n== Facet 2: idle ticks change nothing; A sets its trace on completion ==")
for _ in range(5):
    env.step(WAIT)
print(f"  after 5 WAIT ticks       {state()}   <- expect traces still 0 (no drift)")
park("COMBO_A")
obs_a, *_ = env.step(INTERACT)
print(f"  after INTERACT@COMBO_A   {state()}   <- expect did_a=1.0, energy +0.05")
for name, (off, dims) in trace_fields.items():
    print(f"    mid-chain obs[{off}] ({name}) = {round(obs_a[0, off].item(), 6)}   <- expect did_a 1.0, did_b 0.0 (facet 5)")
for _ in range(5):
    env.step(WAIT)
print(f"  after 5 more WAIT ticks  {state()}   <- expect did_a STILL 1.0 (event flag, no decay)")

print("\n== Facet 4 (first half): C after A alone is still refused ==")
park("COMBO_C")
env.step(INTERACT)
print(f"  after INTERACT@COMBO_C   {state()}   <- expect NO change (did_b still 0)")

print("\n== Facet 3 (second half): B after A applies its effect and sets did_b ==")
park("COMBO_B")
env.step(INTERACT)
print(f"  after INTERACT@COMBO_B   {state()}   <- expect did_b=1.0, energy +0.07")

print("\n== Facet 4 (second half): C after A then B applies its effect ==")
park("COMBO_C")
env.step(INTERACT)
print(f"  after INTERACT@COMBO_C   {state()}   <- expect energy +0.11")

print("\n== Facet 5: observation carries both traces ==")
obs, *_ = env.step(WAIT)
for name, (off, dims) in trace_fields.items():
    print(f"  obs[{off}] ({name}) = {round(obs[0, off].item(), 6)}   raw: {state()}")

print("\n== Facet 5 cross-check: fresh env, traces read 0 in the encoding ==")
env2 = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=1, device=torch.device("cpu"))
obs0 = env2.reset()
for name, (off, dims) in trace_fields.items():
    print(f"  fresh obs[{off}] ({name}) = {round(obs0[0, off].item(), 6)}   <- expect 0.0")
