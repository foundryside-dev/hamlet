"""Trial B diagnostic B1 probe (countersigned facet 6): the 2-D baseline.

Localization question: if B2 fails, is the failure the 5-D substrate or the
mass representation? This probe answers it by re-running the decisive checks
on a plain 8x8 2-D grid.
"""

from pathlib import Path

import torch
from pydantic import ValidationError

from townlet.config.items_config import SpawnPlacementConfig
from townlet.effects.schema import EffectScope
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_b_organism_2d")
LEVEL = "L0_organism_2d"
A = (0, 0)
W = (7, 7)

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
meta = universe.metadata
print(f"== B1 compiles on 2-D: position_dim={meta.position_dim} grid_cells={meta.grid_cells} ==")


def fresh_env() -> VectorizedHamletEnv:
    e = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=4, device=torch.device("cpu"))
    e.reset()
    return e


env = fresh_env()
label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
WAIT = label_to_action["WAIT"]
INTERACT = label_to_action["INTERACT"]
i_rooted = env.meter_name_to_index["rooted"]
i_biomass = env.meter_name_to_index["biomass"]

print("== Localization check 1: the trail deposit refusal is substrate-independent ==")
env.effect_manager.spawn_effect(
    effect_id="organism_footprint",
    target_entity_id=0,
    scope=EffectScope.AGENT,
    duration=1000,
    intensity=1.0,
    current_step=0,
)
try:
    env.step(torch.tensor([WAIT, WAIT, WAIT, WAIT], dtype=torch.long))
    print("  UNEXPECTED: positional spawn_item executed on 2-D")
    blocked_2d = False
except ValueError as exc:
    print(f"  refused loudly on 2-D as well: ValueError: {exc}")
    blocked_2d = True
assert blocked_2d, "expected the same runtime refusal on 2-D"

print("== Localization check 2: what 2-D has that 5-D lacks — static fixed item placement ==")
ok = SpawnPlacementConfig(mode="fixed", fixed_positions=[(0, 0)], grid_spacing=None, script=None)
print(f"  2-tuple fixed placement parses: {ok.fixed_positions} (5-tuple was refused at parse on B2)")
try:
    SpawnPlacementConfig(mode="fixed", fixed_positions=[(0, 0, 0, 0, 0)], grid_spacing=None, script=None)
    print("  UNEXPECTED: 5-tuple accepted")
except ValidationError:
    print("  5-tuple still refused — the 2-D-only typing is the difference, not the runtime")
print("  => a STATIC root cell is declarable on 2-D only; a GROWING trail is declarable nowhere")

print("== Facets 4/5 on 2-D: declared positions, gated absorption, gradient ==")
env = fresh_env()
for i in (0, 1, 2):
    env.positions[i] = torch.tensor(A, dtype=env.positions.dtype)
env.positions[3] = torch.tensor((4, 4), dtype=env.positions.dtype)
env.step(torch.tensor([INTERACT, INTERACT, INTERACT, WAIT], dtype=torch.long))
rooted_now = [round(env.meters[i, i_rooted].item(), 3) for i in range(4)]
print(f"  affordances: {dict((k, tuple(int(x) for x in v)) for k, v in env.affordances.items())}; rooted={rooted_now}")
assert tuple(int(x) for x in env.affordances["ROOT"]) == A
assert tuple(int(x) for x in env.affordances["WAREHOUSE"]) == W
assert rooted_now == [1.0, 1.0, 1.0, 0.0]
env.positions[0] = torch.tensor(W, dtype=env.positions.dtype)
r_pre = env.step(torch.tensor([WAIT, WAIT, WAIT, WAIT], dtype=torch.long))[1][0].item()
r_int = env.step(torch.tensor([INTERACT, WAIT, WAIT, WAIT], dtype=torch.long))[1][0].item()
print(f"  biomass after rooted absorb: {round(env.meters[0, i_biomass].item(), 3)}; reward pre={r_pre:.6f} interact={r_int:.6f}")
assert abs(env.meters[0, i_biomass].item() - 0.2) < 1e-6
assert abs((r_int - r_pre) - 0.1) < 1e-6
# gradient: step off W then back
moves = [m for m in ("LEFT", "WEST") if m in label_to_action]
back = [m for m in ("RIGHT", "EAST") if m in label_to_action]
r_away = env.step(torch.tensor([label_to_action[moves[0]], WAIT, WAIT, WAIT], dtype=torch.long))[1][0].item()
r_toward = env.step(torch.tensor([label_to_action[back[0]], WAIT, WAIT, WAIT], dtype=torch.long))[1][0].item()
print(f"  reward step-away={r_away:.6f} step-toward={r_toward:.6f}")
assert r_toward > r_away

print()
print("B1 DIAGNOSTIC COMPLETE: the mass-representation failure is substrate-independent;")
print("2-D adds only static fixed item placement (parse-level typing), not growth.")
