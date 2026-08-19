"""Trial K runtime probe (protocol §6 leg (b)). Lives in the trial pack, never under src/townlet/.

Countersigned facets, probed in the pre-committed order F1→F2→F3→F4→F8→F5→F6→F7:

  F1: exogenous world state — a global variable evolves with NO agent action as its cause
  F2: threshold-gated condition — pressure absent (exactly 0.0) warm-side, present cold-side
  F3: world→agent effect — a meter moves while every agent WAITs, vs a warm-side contrast
  F4: observability — the condition is an observation field, active, and tracks across ticks
  F8: eating the cost — sustained exposure floors the meter, clamped, and fires a consequence
  F5: equipped item modulates the INCOMING effect's own magnitude, declared in item state
  F6: the equip is a runtime verb the agent performs
  F7: location-dependent environmental property (zone scope first, then any surface)

Refusals are caught and printed rather than raised: what the substrate refuses is the finding.
"""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/trial_k_cold")
LEVEL = "L0_cold"
N = 4  # N>=3 rule (A.4): for_each all_agents is cross-agent resolution

universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)


def fresh_env() -> VectorizedHamletEnv:
    e = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=N, device=torch.device("cpu"))
    e.reset()
    return e


def gv(e, name):
    """Read a global VFS scalar."""
    return float(e.vfs_registry.get(name, reader="engine").item())


def attempt(label, fn):
    """Run a probe step; report a refusal instead of dying on it."""
    try:
        return True, fn()
    except Exception as exc:  # noqa: BLE001 - the refusal text IS the evidence
        print(f"  REFUSED [{label}]: {type(exc).__name__}: {exc}")
        return False, None


env = fresh_env()
label_to_action = {label: idx for idx, label in env.get_action_label_names().items()}
WAIT = label_to_action["WAIT"]
INTERACT = label_to_action["INTERACT"]
i_comfort = env.meter_name_to_index["comfort"]
i_bite = env.meter_name_to_index["cold_bite"]
i_ins = env.meter_name_to_index["insulation_worn"]
print(f"== setup: {N} agents; actions {sorted(label_to_action)} ==")
print(f"   affordances: {sorted(env.affordances.keys())}")


def step_all(e, acts):
    return e.step(torch.tensor(acts, dtype=torch.long))


# ─────────────────────────────────────────────────────────────────────────────
print("\n== F1: does the WORLD act with no agent action? (all-WAIT, 12 ticks) ==")
env = fresh_env()
t0_temp, t0_ticks = gv(env, "world_temp"), gv(env, "winter_ticks")
for _ in range(12):
    step_all(env, [WAIT] * N)
t1_temp, t1_ticks = gv(env, "world_temp"), gv(env, "winter_ticks")
print(f"  world_temp   {t0_temp:.4f} -> {t1_temp:.4f}")
print(f"  winter_ticks {t0_ticks:.1f} -> {t1_ticks:.1f}  (ticks the world process actually ran)")
print(f"  comfort agent0 {env.meters[0, i_comfort].item():.4f}")
f1_world_moved = abs(t1_temp - t0_temp) > 1e-9 or t1_ticks > 0.0
print(f"  => F1 exogenous world advanced without any agent action: {f1_world_moved}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n== F1b: the only found route to start the world — an AGENT acts (cheat #2) ==")
env = fresh_env()
env.positions[0] = torch.tensor([0, 0], dtype=env.positions.dtype)
step_all(env, [INTERACT] + [WAIT] * (N - 1))
after_onset = gv(env, "winter_ticks")
step_all(env, [WAIT] * N)
print(f"  winter_ticks after agent0 INTERACTs at WINTER_ONSET(0,0): {after_onset:.1f}")
print(f"  world_temp now: {gv(env, 'world_temp'):.4f}")
world_startable_by_agent = gv(env, "winter_ticks") > 0.0
print(f"  => world process runs once an agent starts it: {world_startable_by_agent}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n== F2/F3: threshold gate + world->agent effect (all agents WAIT throughout) ==")
env = fresh_env()
env.positions[0] = torch.tensor([0, 0], dtype=env.positions.dtype)
step_all(env, [INTERACT] + [WAIT] * (N - 1))
rows = []
for t in range(12):
    step_all(env, [WAIT] * N)
    rows.append((t, gv(env, "world_temp"), env.meters[0, i_bite].item(), env.meters[0, i_comfort].item()))
print("  tick  world_temp  cold_bite  comfort(agent0)")
for t, wt, cb, cf in rows:
    side = "warm" if wt >= 0.5 else "COLD"
    print(f"  {t:>4}  {wt:>10.4f}  {cb:>9.6f}  {cf:>8.5f}   [{side}]")
warm_bites = [cb for _, wt, cb, _ in rows if wt >= 0.5]
cold_bites = [cb for _, wt, cb, _ in rows if wt < 0.5]
print(f"  warm-side bites all exactly 0.0: {all(b == 0.0 for b in warm_bites)}  (n={len(warm_bites)})")
print(f"  cold-side bites all > 0:         {all(b > 0.0 for b in cold_bites)}  (n={len(cold_bites)})")
print("  BOUNDARY 1 (equality): the gate is `world_temp < 0.5`, so temp==0.5 must be WARM")
eq_rows = [(wt, cb) for _, wt, cb, _ in rows if abs(wt - 0.5) < 1e-6]
print(f"    rows at temp==0.5: {eq_rows}  -> bite must be 0.0")
print("  N>=3 check: every agent takes the same cold, none acted")
print(f"    comfort by agent: {[round(env.meters[i, i_comfort].item(), 5) for i in range(N)]}")
print(f"    cold_bite by agent: {[round(env.meters[i, i_bite].item(), 6) for i in range(N)]}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n== F4: is the condition OBSERVABLE to the agent? ==")
spec = universe.observation_spec
offset, found = 0, {}
for f in spec.fields:
    nm = f.name
    if any(k in nm for k in ("world_temp", "season_clock", "winter_ticks", "comfort", "cold_bite", "insulation")):
        found[nm] = (offset, f.dims)
    offset += f.dims
print(f"  total_dims={spec.total_dims}")
for nm, (off, dims) in found.items():
    print(f"  field {nm!r}: offset={off} dims={dims}")
if not found:
    print("  NO observation field matched the condition variables")
mask = getattr(universe, "observation_activity", None)
if mask is not None and getattr(mask, "active_mask", None) is not None:
    am = mask.active_mask
    for nm, (off, dims) in found.items():
        print(f"    active_mask[{nm}] = {[bool(am[off + k]) for k in range(dims)]}")
env = fresh_env()
env.positions[0] = torch.tensor([0, 0], dtype=env.positions.dtype)
step_all(env, [INTERACT] + [WAIT] * (N - 1))
obs_series = []
for _ in range(8):
    out = step_all(env, [WAIT] * N)
    obs = out[0] if isinstance(out, tuple) else out
    obs_series.append(obs[0].clone())
for nm, (off, dims) in found.items():
    vals = [round(float(o[off]), 5) for o in obs_series]
    print(f"  obs[{nm} @ {off}] across 8 ticks: {vals}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n== F8: eating the cost — floor, clamp, and a declared consequence ==")
env = fresh_env()
env.positions[0] = torch.tensor([0, 0], dtype=env.positions.dtype)
step_all(env, [INTERACT] + [WAIT] * (N - 1))
term = None
for t in range(120):
    out = step_all(env, [WAIT] * N)
    dones = out[2] if len(out) > 2 else None
    c = env.meters[0, i_comfort].item()
    if dones is not None and bool(torch.as_tensor(dones).flatten()[0]):
        term = (t, c)
        break
print(f"  comfort floor reached: {env.meters[0, i_comfort].item():.6f} (declared min 0.0)")
print(f"  BOUNDARY 3 (floor saturation): comfort >= 0.0 held: {env.meters[0, i_comfort].item() >= 0.0}")
print(f"  terminal fired: {term}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n== F5/F6: does an EQUIPPED ITEM change the incoming effect's own magnitude? ==")
env = fresh_env()
env.positions[0] = torch.tensor([0, 0], dtype=env.positions.dtype)
step_all(env, [INTERACT] + [WAIT] * (N - 1))
for _ in range(7):
    step_all(env, [WAIT] * N)
print(f"  cold established: world_temp={gv(env, 'world_temp'):.4f} bite={env.meters[0, i_bite].item():.6f}")
print(f"  insulation_worn before equip: {env.meters[0, i_ins].item():.4f}")
print("  F6: the equip as a RUNTIME VERB — walk agent0 onto the coat at (1,0), GET, USE")
print(f"    item-ish actions present: {[a for a in sorted(label_to_action) if any(k in a for k in ('GET', 'USE', 'DROP', 'SLOT'))]}")
env.positions[0] = torch.tensor([1, 0], dtype=env.positions.dtype)
bite_before_equip = env.meters[0, i_bite].item()
for verb in ("GET", "USE_SLOT_0"):
    step_all(env, [label_to_action[verb]] + [WAIT] * (N - 1))
    print(f"    after {verb}: insulation_worn={env.meters[0, i_ins].item():.4f} bite={env.meters[0, i_bite].item():.6f}")
bite_after_equip = env.meters[0, i_bite].item()
print(f"    F5/F6 in ONE episode: bite {bite_before_equip:.6f} -> {bite_after_equip:.6f} via agent actions only")
print(f"    other agents (never equipped) still take full cold: {[round(env.meters[i, i_bite].item(), 6) for i in range(1, N)]}")
step_all(env, [label_to_action["DROP_SLOT_0"]] + [WAIT] * (N - 1))
print(f"    after DROP_SLOT_0: insulation_worn={env.meters[0, i_ins].item():.4f} bite={env.meters[0, i_bite].item():.6f}")
print("  F5: does the incoming bite shrink when insulation is worn? (direct write contrast)")
env2 = fresh_env()
env2.positions[0] = torch.tensor([0, 0], dtype=env2.positions.dtype)
step_all(env2, [INTERACT] + [WAIT] * (N - 1))
for _ in range(7):
    step_all(env2, [WAIT] * N)
bite_bare = env2.meters[0, i_bite].item()
env2.meters[0, i_ins] = 0.6
step_all(env2, [WAIT] * N)
bite_worn = env2.meters[0, i_bite].item()
env2.meters[0, i_ins] = 0.0
step_all(env2, [WAIT] * N)
bite_back = env2.meters[0, i_bite].item()
print(f"    bite bare={bite_bare:.6f}  worn(ins=0.6)={bite_worn:.6f}  after removal={bite_back:.6f}")
print(f"    BOUNDARY 10 (unequip residual exact): {abs(bite_back - bite_bare) < 1e-9}")
print("    BOUNDARY 5 (over-mitigation: ins=1.5 must floor at 0, not invert)")
env2.meters[0, i_ins] = 1.5
step_all(env2, [WAIT] * N)
print(f"      bite at ins=1.5: {env2.meters[0, i_bite].item():.6f}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n== F7: location-dependent environmental property ==")
print("  FIRST SURFACE (the one the corpus names): zone scope")
print("  The pack declared `zone_temp_offset` with scope: zone. It VALIDATED and")
print("  COMPILED, then crashed at env construction. Reproduced directly here:")
from townlet.vfs.registry import VariableRegistry  # noqa: E402
from townlet.vfs.schema import VariableDef  # noqa: E402

for scope_name, extent_attr in (("zone", "num_zones"), ("group", "num_groups"), ("message", "num_message_slots")):
    ok_s, _ = attempt(
        f"VariableRegistry with a {scope_name}-scoped variable (as vectorized_env constructs it)",
        lambda s=scope_name: VariableRegistry(
            variables=[VariableDef(id=f"probe_{s}_var", scope=s, type="scalar", default=0.0,
                                   lifetime="persistent", readable_by=["engine"], writable_by=["engine"],
                                   description="probe")],
            num_agents=N, device=torch.device("cpu"), max_items=0, num_affordances=2,
        ),
    )
    print(f"    scope={scope_name!r} usable with the env's own registry args: {ok_s}  (needs {extent_attr})")
print("    -> vectorized_env.py:621 passes num_agents/max_items/num_affordances/item_profiles ONLY.")
print("       num_zones, num_groups and num_message_slots default to 0 and no YAML sets them.")
print("    is there ANY agent->zone membership mapping on the env?")
print(f"    env attributes mentioning zone: {[a for a in dir(env) if 'zone' in a.lower()]}")

print("  SECOND SURFACE: can an effect gate on the agent's POSITION?")
print("    The effects executor builds its expression context at executor.py:642-726.")
print("    Neither construction passes agent_positions or affordance_positions, so the")
print("    grammar's spatial operators are unreachable from an effect. Demonstrated:")
from townlet.world.expression.context import ExecutionContext as ExprCtx  # noqa: E402
from townlet.world.expression.functions import _require_positions  # noqa: E402

ctx = ExprCtx(bars={}, vfs={}, affordances={}, temporal={}, device=torch.device("cpu"))
attempt("spatial operator inside an effect-shaped context", lambda: _require_positions(ctx))
attempt("temporal.tick inside an effect-shaped context", lambda: ctx.get("temporal.tick"))
print(f"    effect-context agent_positions is {ctx.agent_positions!r}; temporal is {ctx.temporal!r}")

print("\n== BOUNDARY 1 (equality), tested directly: the natural rule never lands on 0.5 ==")
env3 = fresh_env()
env3.positions[0] = torch.tensor([0, 0], dtype=env3.positions.dtype)
step_all(env3, [INTERACT] + [WAIT] * (N - 1))
print("  NOTE: on_tick decrements world_temp BEFORE the threshold reads it, so the")
print("  pre-step value must be 0.6 for the gate to see exactly 0.5.")
env3.vfs_registry.set("world_temp", torch.tensor(0.6), writer="engine")
step_all(env3, [WAIT] * N)
seen = gv(env3, "world_temp")
print(f"  pre-step 0.6 -> gate saw world_temp={seen:.8f}; cold_bite={env3.meters[0, i_bite].item():.6f}")
print(f"    exactly 0.5? {seen == 0.5} — gate is `< 0.5`, so bite must be 0.0 iff the value is exactly 0.5")
env3.vfs_registry.set("world_temp", torch.tensor(0.59), writer="engine")
step_all(env3, [WAIT] * N)
print(f"  pre-step 0.59 -> gate saw {gv(env3, 'world_temp'):.8f}; cold_bite={env3.meters[0, i_bite].item():.6f} (cold side)")

print("\n== LEG (c) — trains-without-incident (A.4, non-gating this corpus) ==")
print("  (1) reward assertion: comfort is a declared drive component (scale 0.5)")
env4 = fresh_env()
env4.positions[0] = torch.tensor([0, 0], dtype=env4.positions.dtype)
step_all(env4, [INTERACT] + [WAIT] * (N - 1))
for _ in range(3):
    step_all(env4, [WAIT] * N)
c_pre = env4.meters[0, i_comfort].item()
r_pre = step_all(env4, [WAIT] * N)[1][0].item()
c_mid = env4.meters[0, i_comfort].item()
r_post = step_all(env4, [WAIT] * N)[1][0].item()
c_post = env4.meters[0, i_comfort].item()
print(f"    comfort {c_pre:.5f} -> {c_mid:.5f} -> {c_post:.5f}; reward {r_pre:.6f} -> {r_post:.6f}")
print(f"    reward delta {r_post - r_pre:+.6f} against comfort delta {c_post - c_mid:+.6f} (scale 0.5)")

print("  (2) double-reset: mechanic state must return to declared initial")
env4.reset()
print(f"    after reset: world_temp={gv(env4, 'world_temp'):.4f} (initial 1.0), "
      f"season_clock={gv(env4, 'season_clock'):.1f} (initial 0.0), "
      f"winter_ticks={gv(env4, 'winter_ticks'):.1f} (initial 0.0)")
print(f"    comfort={env4.meters[0, i_comfort].item():.4f} (initial 1.0)")
obs_after_reset = env4._get_observations()[0] if hasattr(env4, "_get_observations") else None
step_all(env4, [WAIT] * N)
print(f"    one WAIT tick after reset: winter_ticks={gv(env4, 'winter_ticks'):.1f} "
      f"(must stay 0.0 — a surviving effect would tick it)")

print("  (3) obs-bounds loop: every component within its declared normalization range")
env5 = fresh_env()
env5.positions[0] = torch.tensor([0, 0], dtype=env5.positions.dtype)
step_all(env5, [INTERACT] + [WAIT] * (N - 1))
viol = []
for _ in range(20):
    out = step_all(env5, [WAIT] * N)
    obs = out[0] if isinstance(out, tuple) else out
    o = obs[0]
    for idx in range(o.shape[0]):
        v = float(o[idx])
        if v < -1e-6 or v > 1.0 + 1e-6:
            viol.append((idx, round(v, 5)))
uniq = sorted(set(viol))
print(f"    out-of-[0,1] components over 20 ticks: {len(uniq)} distinct -> {uniq[:12]}")

print("  (4) random-policy smoke: 5 episodes, finite non-constant rewards, terminate")
import random  # noqa: E402

rng = random.Random(1234)
n_actions = len(label_to_action)
for ep in range(5):
    e = fresh_env()
    rews, steps, done_flag = [], 0, False
    for _ in range(60):
        out = step_all(e, [rng.randrange(n_actions) for _ in range(N)])
        rews.append(float(out[1][0].item()))
        steps += 1
        d = out[2] if len(out) > 2 else None
        if d is not None and bool(torch.as_tensor(d).flatten()[0]):
            done_flag = True
            break
    finite = all(r == r and abs(r) != float("inf") for r in rews)
    print(f"    ep{ep}: steps={steps} done={done_flag} finite={finite} "
          f"non-constant={len(set(round(r, 6) for r in rews)) > 1} range=({min(rews):.4f},{max(rews):.4f})")

print("  (5) reward-relevance note: comfort IS a declared reward component (bar_bonuses, scale 0.5);")
print("      world_temp is NOT — the world state is observable but not directly rewarded.")

print("\nPROBE COMPLETE")

print("\n== BY-CATCH: is the item `on_drop` hook INERT, or was the drop rejected? ==")
envd = fresh_env()
envd.positions[0] = torch.tensor([0, 0], dtype=envd.positions.dtype)
step_all(envd, [INTERACT] + [WAIT] * (N - 1))
for _ in range(7):
    step_all(envd, [WAIT] * N)
envd.positions[0] = torch.tensor([1, 0], dtype=envd.positions.dtype)
step_all(envd, [label_to_action["GET"]] + [WAIT] * (N - 1))
inv = getattr(envd, "inventory", None)
def inv_snapshot(e):
    iv = getattr(e, "inventory", None)
    if iv is None:
        return "no `inventory` attr on env"
    for attr in ("slots", "item_ids", "contents", "data"):
        if hasattr(iv, attr):
            return f"{attr}={getattr(iv, attr)}"
    return f"inventory obj={type(iv).__name__}"
print(f"  after GET : insulation_worn={envd.meters[0, i_ins].item():.4f}  {inv_snapshot(envd)}")
step_all(envd, [label_to_action["USE_SLOT_0"]] + [WAIT] * (N - 1))
print(f"  after USE : insulation_worn={envd.meters[0, i_ins].item():.4f}  (on_use FIRED -> hook path works)")
step_all(envd, [label_to_action["DROP_SLOT_0"]] + [WAIT] * (N - 1))
print(f"  after DROP: insulation_worn={envd.meters[0, i_ins].item():.4f}  {inv_snapshot(envd)}")
print("  -> if the slot emptied but insulation_worn stayed 0.6, the DROP happened and on_drop is INERT.")
