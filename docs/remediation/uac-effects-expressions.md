# Universe-as-Code A: effects and the expression language — gap analysis and remediation plan

Scope: `src/townlet/effects/` (manager, executor, context, parser, compiler, admission, catalog,
collections, affordance_identity), `src/townlet/world/expression/` (functions, type_checker,
evaluator, history, parser, ast_nodes, context), `config/effects_config.py`,
`universe/compilers/effects.py`, and the effect call sites in `vectorized_env.py`.
Evidence: `review-2026-10-24/findings_effects.md`, scripts `review-2026-10-24/effects/`.

## What the subsystem promises

`docs/config-schemas/effects.md` and `expressions.md`: effects are declared in a catalog with a
scope, duration, lifecycle hooks (`on_spawn`, `on_tick`, `on_despawn`) and a command vocabulary
(`modify`, `if`, `switch`, `for_each`, `delay`, `spawn_effect`, `spawn_item`); commands evaluate
expressions over bars, variables, position and time; collections (`all_agents`,
`nearby_agents`, `active_effects`) iterate with a bound iterator; the engine executes effects,
expressions and spawn predicates with checked write authorization.

## What it does

The authorization and rollback story holds: denied writes refuse at compile including inside
delayed commands, a nested refusal rolls bars, stores and ids back, presence and payload clear on
despawn, capacity overflow is loud, and the preflight fix left no evaluate-before-authorize path.
The expression language parses, type-checks and evaluates 48 of its 49 registered functions on a
batch.

What it does not do: survive a reset. Effects spawned in episode N tick in episode N+1 with their
counters intact. Inside the command vocabulary, a scalar `modify` turns the bar into a broadcast
view so the next per-agent write hits everyone, and the `if`/`switch` commands collapse the batch
with `.any()`. Effects cannot read position or time in any spelling. The expression language has a
24-tick day baked in, a `mean` that crashes on ints, distance functions that collapse the batch,
and a temporal family that compiles inside effects and always crashes.

## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_effects.md`
(F-numbers) and filigree ids.

| id | sev | gap | source |
|---|---|---|---|
| E1 | P1 | Effects survive `env.reset()`; no `EffectManager.reset()` | hamlet-d76684f549 |
| E2 | P1 | Scalar `modify: bar.X` rebinds to a broadcast view; next per-agent write hits every agent | F1 |
| E3 | P1 | `if`/`switch` commands reduce the condition with `.any()` | F2 |
| E4 | P1 | `mean` crashes on ints; four functions and `elapsed_ticks` disagree with the type checker on dtype | F3 |
| E5 | P1 | Effects cannot read time (refuses) or position (crashes) | hamlet-a737e444c0 |
| E6 | P2 | `for_each … as:` never bound | F4 |
| E7 | P2 | `nearby_agents`, `spawn_item quantity/initial_state` on the AST, not the DTO; resolver Euclidean | F5 |
| E8 | P2 | `active_effects` iterates self N times | F6 |
| E9 | P2 | `self`/`target` same entity; `self.vfs.X` unspellable; affordance and global effects address an agent row | F7, hamlet-b3a30b82ef residual |
| E10 | P2 | Distance functions refuse vectors and collapse the batch | F8 |
| E11 | P2 | Temporal operators compile in effects and always crash | F9 |
| E12 | P2 | `time_in_window` hardcodes 24 | F10 |
| E13 | P2 | Registry variables shadow effect lifecycle scalars | F11 |
| E14 | P2 | `switch` cases untyped; typo'd keys compile | F13 |
| E15 | P2 | Observable effect in zero-budget scope silently unobserved; non-observable never budgeted | F14 |
| E16 | P2 | Parameter-identical affordances and effects compile | F15 |
| E17 | P2 | `effects.md` and `expressions.md` contradict the DTO and the engine | F12, hamlet-7eadeb214c, hamlet-8f2e13c5a9 |
| E18 | P3 | Same-tick write order; `lag(x,0)`; shared random draws; `simplex_noise` is Perlin | F16-F18, F20 |
| E19 | P3 | Dead surface, swallowed import, 87 hidden defaults under blanket whitelist | F19 |

## Remediation plan

### WP1 — `EffectManager.reset()` (E1)

Add `reset()` that clears every store, the scheduler, `next_instance_id` and per-instance
counters, and call it from `env.reset()` before initial spawns. Decide and write down what a
"legitimately re-spawned" effect is: an `on_reset` or spawn-predicate path that re-creates it in
the new episode is fine; carry-over is not.

Verification: `repro_d766.py` shows money at 1000 after reset and a WAIT, with zero active
effects; `repro_d766_agent.py` shows an empty agent store after reset. Both become tests. Size: S.
**Do this second overall; every episode-boundary claim is void until it lands.**

### WP2 — Per-agent command semantics (E2, E3)

`set_path("bar.*")` copies into the existing tensor (`copy_`) instead of rebinding; a scalar
result is materialised with `expand_as(...).clone()` or broadcast inside the copy. The `if` and
`switch` commands become masked execution: evaluate the condition per agent, run the branch with
the condition as a write mask, so one keyword has one semantics. Scalar conditions remain a
degenerate mask.

Verification: `probe_d.py` I3 expects `[0.3, 0.4, 0.3]`; `probe_b.py` F expects only agent 1
penalised. Both become tests, plus a stride assertion on every bar after any command. Size: M.

### WP3 — Thread time and position into effects (E5, E11, E7)

Inject the engine `tick` and the clock into the effects schema the way the VFS compiler does
(`compilers/vfs.py:38, 78`), so `tick` compiles in an effect. Pass `agent_positions`,
`affordance_positions` and the substrate into `manager.tick` from `vectorized_env.py:1092` and
through `_lifecycle_context` and `_make_eval_context`. Decide the temporal family: either thread
`TemporalHistory` and `step` into the effects context too, or make the effects compiler refuse
history operators and `elapsed_ticks()` with a message naming the VFS-profile surface where they
work. Refusal is the smaller change and the recommended one.

Then `nearby_agents`: add `radius` to `CommandConfig`, route the resolver through
`substrate.distance()`, and delete the Euclidean `torch.norm`. `spawn_item` `quantity` and
`initial_state` either reach the DTO or leave the AST.

Verification: `probe_a.py` C compiles `tick` and D evaluates `distance_to_affordance`;
`probe_d.py` Z refuses `lag` in an effect at compile; `probe_a.py` B3 iterates neighbours by the
declared metric. Size: M.

### WP4 — Type checker and evaluator agree (E4, E10)

For every `FUNCTION_SPECS` entry, the declared return type must equal the evaluated dtype and the
evaluated shape must be `[batch]` for per-agent inputs. `func_sweep.py` already produces the table;
make it a parametrised test over all 49 entries with a batch-3 context and fail on any row where
declared and actual differ. Fix the five known rows (`mean` promotes to float; `sum`/`product`
return float; `clamp01` declares float; `/` declares float; `elapsed_ticks` is injected as float).
Distance functions accept vector variables and reduce over the last axis only. Size: M.

### WP5 — One clock (E12, and `uac-items` F6)

`time_in_window` and every opening-hours path take the period from the context's declared clock,
never a literal. The expression context already carries `temporal.time_of_day`; add
`temporal.period` sourced from `day_length`, and refuse `time_in_window` on a pack with no clock.
Verification: `probe_d.py` X with a 48-tick clock. Size: S.

### WP6 — Entity addressing in effects (E9, E13)

Decide what `self` and `target` mean per scope and write it in `effects.md`:

- agent scope: `self` = attached agent; `target` = the agent the lifecycle hook names (same as
  self for `on_tick`, the interactor for affordance `on_start`).
- item scope: `self` = the item; `target` = the holder or interactor.
- affordance scope: `self` = the affordance (its position, availability, occupancy); `target` =
  the interacting agent.
- global scope: `self` = the world; `target` is a compile-time refusal.

Emit `self.vfs.*` for agent variables in agent scope. Refuse `target.*` where it has no meaning.
Effect lifecycle scalars (`intensity`, `elapsed_ticks`, `duration_remaining`) live in their own
namespace (`effect.intensity`) so no registry variable can shadow them; refuse the bare names.

Verification: `probe_b.py` K, K2, N2 and `probe_d.py` U all refuse or address the right entity.
Size: M.

### WP7 — Typed commands and honest budgets (E14, E15, E6, E8)

`switch` cases become a typed DTO with `extra="forbid"`. `max_active_effects` counts every live
instance regardless of observability, and an observable effect in a zero-budget scope refuses at
compile. `for_each … as:` is either bound into the eval context under the iterator name and added
to the compile-time schema, or deleted; the plan recommends binding it, since the doc teaches it
and the body has no other way to see the iterated entity's id. `active_effects` returns effect
instances with an `effect.*` namespace in the body, or is deleted.

Verification: `probe_d.py` Y refuses the typo; `probe_c.py` R2 refuses at compile; `probe_b.py`
G2 raises capacity; `probe_a.py` B1 compiles `a`; B4 sees two distinct effects. Size: M.

### WP8 — Entity identity across affordances and effects (E16)

Shared with the compiler plan (its WP5): run the indistinguishability check over affordance and
effect signatures. Size: S.

### WP9 — Residue and docs (E18, E19, E17)

Document same-tick write order or make it deterministic by catalog order; fix `lag(x,0)`; make
`uniform()`/`normal_dist()` draw per agent when the context has a batch; rename `simplex_noise`
or implement simplex. Delete the dead surface in E19 and replace the blanket whitelist lines with
nothing; the `getattr(self, "device")` and `.get(name, True)` defaults become explicit arguments.
Rewrite `effects.md` and `expressions.md` from the DTO and `FUNCTION_SPECS`, not from memory;
generate the function table from the registry so it cannot drift again. Size: M.

## Docs to correct in the same changes

- `docs/config-schemas/effects.md`: every line listed under E17; the entity-addressing table from
  WP6; the budget rule from WP7.
- `docs/config-schemas/expressions.md`: regenerate the function inventory (WP9); delete the
  "planned" labels; state which families are VFS-profile-only (WP3).
- `README.md` "Known work ahead": delete "effects reset" once WP1 lands.
