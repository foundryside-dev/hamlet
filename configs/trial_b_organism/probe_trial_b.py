"""Trial B runtime probe (protocol §6 leg (b) + Appendix A.4 leg (c)).

Lives in the trial pack, never under src/townlet/.

Countersigned facets (B2 headline):
  1: 5-D discrete substrate — gridnd, dimension count 5, positions width 5
  2: mass, not point — >=2 cells occupied by the ONE organism at the same tick,
     extent readable in the encoded observation at a compiled offset
  3: rooted outward growth — root A stays occupied, occupied set weakly
     increasing, every new cell adjacent to a previously occupied cell
  4: food warehouse at a declared 5-D coordinate; contact fires the declared
     effect (biomass moves)
  5: trainable spread-toward-food signal — approach_reward in the compiled
     drive; step toward the warehouse rewards strictly more than a step away

The probe demonstrates what IS expressible and records, verbatim, the runtime
refusal of the one surface (positional spawn_item from an effect tick) that the
Spec's durable-trail reading needs.

Leg (c) — trains-without-incident (A.4, non-gating): reward assertion,
double-reset, obs-bounds loop, boundary case (biomass cap), N>=3 (three rooted
agents + one unrooted control), random-policy smoke, reward-relevance note.
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_b_organism")
LEVEL = "L0_organism"
A = (0, 0, 0, 0, 0)  # declared root
W = (3, 3, 3, 3, 3)  # declared warehouse

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)

print("== Facet 1: compiled substrate is gridnd with 5 dimensions ==")
meta = universe.metadata
print(f"  position_dim={meta.position_dim} grid_cells={meta.grid_cells} action_count={meta.action_count}")
assert meta.position_dim == 5 and meta.grid_cells == 4**5

print("== Facet 2 (compiled half): organism_size is an observation field ==")
spec = universe.observation_spec
org_field = None
offset = 0
for f in spec.fields:
    if "organism_size" in f.name:
        org_field = (offset, f.dims)
        print(f"  field {f.name!r}: offset={offset} dims={f.dims}")
    offset += f.dims
print(f"  total_dims={spec.total_dims}")
assert org_field is not None, "organism_size not in observation spec"
ORG_OFF = org_field[0]


def fresh_env(n: int = 4) -> VectorizedHamletEnv:
    e = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=n, device=torch.device("cpu"))
    e.reset()
    return e


env = fresh_env()
print(f"  affordances in runtime: {dict((k, tuple(int(x) for x in v)) for k, v in env.affordances.items())}")
assert tuple(int(x) for x in env.affordances["ROOT"]) == A, "ROOT not at declared A"
assert tuple(int(x) for x in env.affordances["WAREHOUSE"]) == W, "WAREHOUSE not at declared W"
assert env.positions.shape == (4, 5), f"positions shape {env.positions.shape}"
print(f"  positions after reset: shape={tuple(env.positions.shape)} (facet 1 runtime half OK)")

label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
INTERACT = label_to_action["INTERACT"]
WAIT = label_to_action["WAIT"]
print(f"  action labels: {sorted(label_to_action)}")

i_rooted = env.meter_name_to_index["rooted"]
i_biomass = env.meter_name_to_index["biomass"]


def park(e: VectorizedHamletEnv, agent: int, pos: tuple) -> None:
    e.positions[agent] = torch.tensor(pos, device=e.device, dtype=e.positions.dtype)


def creep_cells(e: VectorizedHamletEnv) -> set:
    return {tuple(int(c) for c in inst.position) for inst in e.item_manager.active_items.values() if inst.item_type_id == "creep"}


def member_cells(e: VectorizedHamletEnv) -> set:
    return {tuple(int(c) for c in e.positions[i]) for i in range(3) if e.meters[i, i_rooted].item() >= 1.0}


def occupied(e: VectorizedHamletEnv) -> set:
    """The organism's occupied set under the best reachable representation:
    durable creep cells (root only) + the cells its joined growth tips stand on."""
    return creep_cells(e) | member_cells(e)


def step_all(e: VectorizedHamletEnv, acts: list):
    return e.step(torch.tensor(acts, device=e.device, dtype=torch.long))


print("== BLOCKED demonstrations: every declarative route to a durable cell ==")
print("  (1) trail deposit — organism_footprint declared exactly as effects.md")
print("      documents (spawn_item, position: self, in on_tick); compiles; step:")

tmp = fresh_env()
tmp.effect_manager.spawn_effect(
    effect_id="organism_footprint",
    target_entity_id=0,
    intensity=1.0,
    current_step=0,
)
try:
    tmp.step(torch.tensor([WAIT, WAIT, WAIT, WAIT], dtype=torch.long))
    print("  UNEXPECTED: positional spawn_item executed without error")
    footprint_blocked = False
except ValueError as exc:
    print(f"      refused loudly at runtime: ValueError: {exc}")
    footprint_blocked = True
del tmp
assert footprint_blocked, "expected the positional spawn_item to be refused"

print("  (2) explicit-coordinate plant — spawn_item position: [0,0,0,0,0] in YAML:")
from pydantic import ValidationError  # noqa: E402

from townlet.config.effects_config import CommandConfig  # noqa: E402

try:
    CommandConfig(spawn_item="creep", position=[0, 0, 0, 0, 0])
    print("  UNEXPECTED: list position accepted")
    explicit_blocked = False
except ValidationError as exc:
    first = str(exc).splitlines()[2].strip()
    print(f"      refused at parse: {first}")
    explicit_blocked = True
assert explicit_blocked

print("  (3) static 5-D item placement — appearance fixed_positions is typed 2-D:")
from townlet.config.items_config import SpawnPlacementConfig  # noqa: E402

try:
    SpawnPlacementConfig(mode="fixed", fixed_positions=[(0, 0, 0, 0, 0)], grid_spacing=None, script=None)
    print("  UNEXPECTED: 5-D fixed position accepted")
    fixed_blocked = False
except ValidationError as exc:
    first = str(exc).splitlines()[2].strip()
    print(f"      refused at parse: {first}")
    fixed_blocked = True
assert fixed_blocked
print("  => no declarative route makes any cell durably organism-occupied on this substrate")

print("== Rooting: agents 0-2 join at A; agent 3 is the unrooted control ==")
for i in (0, 1, 2):
    park(env, i, A)
park(env, 3, (2, 2, 2, 2, 2))
step_all(env, [INTERACT, INTERACT, INTERACT, WAIT])
rooted_now = [round(env.meters[i, i_rooted].item(), 3) for i in range(4)]
print(f"  rooted after INTERACT at A: {rooted_now}")
assert rooted_now == [1.0, 1.0, 1.0, 0.0], "rooting flags wrong"
print(f"  durable creep cells after rooting: {sorted(creep_cells(env))} (no declarative plant exists)")

print("== Facet 3: the walk — what growth looks like under the reachable representation ==")
# Agents 0 and 1 walk two distinct 15-step unit paths toward W; agent 2 HOLDS
# the root — the only way A stays occupied is an agent standing there, which is
# policy behavior, not declared structure.
paths = {
    0: ["DIM0_POS"] * 3 + ["DIM3_POS"] * 3 + ["DIM4_POS"] * 3 + ["DIM1_POS"] * 3 + ["DIM2_POS"] * 3,
    1: ["DIM1_POS"] * 3 + ["DIM4_POS"] * 3 + ["DIM0_POS"] * 3 + ["DIM2_POS"] * 3 + ["DIM3_POS"] * 3,
    2: ["WAIT"] * 15,
}
history = [occupied(env)]
shrank_at = None
for t in range(15):
    acts = [label_to_action[paths[i][t]] for i in (0, 1, 2)] + [WAIT]
    step_all(env, acts)
    now = occupied(env)
    if not history[-1] <= now and shrank_at is None:
        shrank_at = (t, sorted(history[-1] - now))
    history.append(now)
final = history[-1]
print(f"  root A occupied throughout: {all(A in h for h in history)} — but only because agent 2 parks on it (behavior, not structure)")
print(f"  final occupied set size: {len(final)} (3 tips; the Spec's durable trail would be ~33 cells)")
if shrank_at is not None:
    print(f"  occupied set SHRANK first at tick {shrank_at[0]}: vacated {shrank_at[1]}")
print("  => growth-as-durable-expansion is NOT expressible: tips move, cells do not stay organism")
assert all(A in h for h in history), "root cell lost even with a parked agent"
assert shrank_at is not None, "expected the workaround representation to vacate cells"

print("== Facet 2 (runtime half): multi-cell extent, one organism, what the observation shows ==")
mc = member_cells(env)
print(f"  cells simultaneously occupied by the organism now: {sorted(mc | creep_cells(env))}")
assert len(mc | creep_cells(env)) >= 2
obs = env._get_observations()
org_obs = [round(obs[i, ORG_OFF].item(), 6) for i in range(4)]
print(f"  organism_size in every agent's observation at offset {ORG_OFF}: {org_obs}")
assert all(abs(v - 0.003) < 1e-6 for v in org_obs), "organism_size should read 3 tips = 0.003"
print("  extent CARDINALITY is observation-encoded; spatial layout of the mass is not")
assert (2, 2, 2, 2, 2) not in occupied(env), "unrooted control counted as organism"
print("  unrooted control at (2,2,2,2,2) is not part of the organism: OK")

print("== Facet 4: warehouse contact by a rooted agent moves biomass; control does not ==")
print(f"  agent 0 position: {tuple(int(c) for c in env.positions[0])}")
assert tuple(int(c) for c in env.positions[0]) == W
b_before = [round(env.meters[i, i_biomass].item(), 4) for i in range(4)]
park(env, 3, W)  # control agent parked at W too, still unrooted
r_pre = step_all(env, [WAIT, WAIT, WAIT, WAIT])[1][0].item()  # baseline tick at W, biomass still 0
out = step_all(env, [INTERACT, WAIT, WAIT, INTERACT])
b_after = [round(env.meters[i, i_biomass].item(), 4) for i in range(4)]
print(f"  biomass before={b_before} after={b_after}")
assert abs(b_after[0] - b_before[0] - 0.2) < 1e-6, "rooted agent biomass didn't gain 0.2"
assert b_after[3] == b_before[3] == 0.0, "unrooted control absorbed food"

print("== Leg (c) reward assertion + Facet 5 two-branch check ==")
# bar_bonuses reward the bar LEVEL each tick, so the assertion compares the
# pre-interact tick (biomass 0) with the interact tick (biomass 0.2): the
# declared component (scale 0.5) must move the reward by +0.1 that tick.
r_interact = out[1][0].item()
print(f"  reward pre-interact tick={r_pre:.6f}, interact tick={r_interact:.6f} (declared delta +0.1)")
assert abs((r_interact - r_pre) - 0.1) < 1e-6, "biomass component did not move the reward by its declared amount"
r_away = step_all(env, [label_to_action["DIM0_NEG"], WAIT, WAIT, WAIT])[1][0].item()
r_toward = step_all(env, [label_to_action["DIM0_POS"], WAIT, WAIT, WAIT])[1][0].item()
print(f"  reward step-away={r_away:.6f} step-toward={r_toward:.6f}")
assert r_toward > r_away, "approach_reward gradient not present"

print("== Leg (c) boundary case: biomass saturates at its declared max 1.0 ==")
for _ in range(6):
    step_all(env, [INTERACT, WAIT, WAIT, WAIT])
b_cap = round(env.meters[0, i_biomass].item(), 6)
print(f"  biomass after 6 more absorbs: {b_cap}")
assert b_cap <= 1.0 + 1e-9, "biomass exceeded declared bounds"

print("== Leg (c) obs-bounds loop ==")
obs = env._get_observations()
lo, hi = obs.min().item(), obs.max().item()
oob = ((obs < -1e-6) | (obs > 1.0 + 1e-6)).nonzero()
print(f"  final observation range: [{lo:.4f}, {hi:.4f}]; components outside [0,1]: {len(oob)}")

print("== Leg (c) double-reset: mechanic state back to declared initials ==")
env.reset()
rooted_r = [round(env.meters[i, i_rooted].item(), 3) for i in range(4)]
biomass_r = [round(env.meters[i, i_biomass].item(), 3) for i in range(4)]
creep_r = creep_cells(env)
obs_r = env._get_observations()
org_r = [round(obs_r[i, ORG_OFF].item(), 6) for i in range(4)]
print(f"  after reset: rooted={rooted_r} biomass={biomass_r} creep_cells={len(creep_r)} organism_size_obs={org_r}")
n_leaked = sum(len(v) for v in env.effect_manager.agent_effects.values())
print(f"  organism effect instances surviving reset: {n_leaked}")
for _ in range(3):
    step_all(env, [WAIT, WAIT, WAIT, WAIT])
obs_r2 = env._get_observations()
org_r2 = [round(obs_r2[i, ORG_OFF].item(), 6) for i in range(4)]
print(f"  after 3 WAIT ticks post-reset: creep_cells={len(creep_cells(env))} organism_size_obs={org_r2}")
reset_clean = (
    rooted_r == [0.0] * 4 and biomass_r == [0.0] * 4 and not creep_r and org_r == [0.0] * 4 and org_r2 == [0.0] * 4 and n_leaked == 0
)
print(f"  double-reset clean: {reset_clean}")

print("== Leg (c) random-policy smoke: 5 episodes, finite non-constant rewards ==")
torch.manual_seed(7)
n_actions = meta.action_count
all_rewards = []
for ep in range(5):
    env.reset()
    for t in range(100):
        acts = torch.randint(0, n_actions, (4,))
        r = step_all(env, list(acts.tolist()))[1]
        all_rewards.extend(r.tolist())
rt = torch.tensor(all_rewards)
print(f"  {len(all_rewards)} rewards: finite={bool(torch.isfinite(rt).all())} min={rt.min():.4f} max={rt.max():.4f} std={rt.std():.6f}")
assert bool(torch.isfinite(rt).all()) and rt.std() > 0

print("== Leg (c) reward-relevance note ==")
print("  organism_size is NOT referenced by any reward component (authoring choice);")
print("  biomass and rooted are (extrinsic bar bonuses); approach_reward targets WAREHOUSE.")

print()
print("PROBE COMPLETE")
