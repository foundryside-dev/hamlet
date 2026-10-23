# Remediation — gap analysis and plans per subsystem

Written 2026-10-24 from the review pass in `review-2026-10-24/` (five seams, every finding
reproduced by script; the P1s re-verified independently). Source reviewed: `a44b470f`.

These documents are engineering plans, not acceptance records. Each one states what the
subsystem promises, what it does instead, and the ordered work to close the gap. Every work
package names the reproduction script that becomes its regression test. Zero backwards
compatibility applies throughout: when the plan says delete, delete.

| document | subsystem | P1 | P2 | work packages |
|---|---|---|---|---|
| [vfs.md](vfs.md) | Variable & Feature System: registry, VTC, evaluator, profiles | 3 | 7 | 8 |
| [compiler.md](compiler.md) | Universe compiler: discovery, DTOs, emit, cache, identity hashes, CLI | 2 | 7 | 7 |
| [strata.md](strata.md) | Substrates, movement, masking, placement, position encoding | 4 | 7 | 8 |
| [uac-effects-expressions.md](uac-effects-expressions.md) | Effects lifecycle, commands, expression language | 5 | 12 | 9 |
| [uac-items-affordances-rewards.md](uac-items-affordances-rewards.md) | Items, affordances, meters, DAC rewards | 6 | 8 | 9 |

## The one pattern

CLAUDE.md names the product defect: anything that can only be expressed by editing Python.
The review found its mirror image everywhere: **things that can be expressed in YAML and do
nothing.** Three shapes, across all five seams:

1. **Compiles green, never executes.** A transition phase the engine never runs; a compiled
   reward program with no executor; `for_each … as:` parsed and never bound; `on_drop` compiled
   and never called; opening hours on a non-temporal level. A green suite cannot see these
   because every test asserts on the paths the engine happens to take.
2. **Required by no-defaults, consumed by nobody.** `recovery.natural`, `extents.num_affordances`,
   `action_discretization` off 2-D, `experiment.curriculum_levels`, `environment.cues`,
   `AffordanceDefinition.category`, `training_loop.evaluation`, the whole `capability_config.py`.
   No-defaults was meant to stop hidden behaviour; here it forces authors to write dead config
   and then validates none of it.
3. **Two vocabularies for one fact.** DTO versus AST (`radius`, `quantity`), compiler versus
   runtime (`presentation` by content versus by filename), family versus family (GridND emits
   `WAIT`, Grid2D does not; boundary masking exists for grids and not for ND), declared versus
   literal (`day_length` versus the 24 baked into `time_in_window` and opening hours).

The remediation plans therefore lean on deletion. A dead field deleted is a gap closed; a dead
field "wired up" is a design decision that needs a reason.

## Cross-subsystem sequencing

Some fixes unblock others. Do these first, in this order; everything else in the per-subsystem
plans can proceed in parallel after them.

| order | package | why first |
|---|---|---|
| 1 | compiler WP1: serialize `items_appearance` | every items reproduction after the first compile is wrong until this lands; it also masks `uac-items` WP1 |
| 2 | uac-effects WP1: `EffectManager.reset()` | episode boundaries are wrong for every pack with effects; every learning or reset claim downstream is void until this lands |
| 3 | vfs WP1: phase graph truth | defines which phases exist; strata, effects and items plans all schedule writes against it |
| 4 | compiler WP2: stamp and compare pack hashes | the checkpoint gate must see stratum and items edits before the strata and items fixes change those hashes |
| 5 | strata WP1: boundary-aware masking | the `boundary_wrap` differential cell is meaningless until a policy can cross the seam |
| 6 | uac-items WP2: DAC normalization and defaults | reward semantics must be right before any convergence work |

Shared mechanical work, do once:

- **Whitelist rebuild.** `.defaults-whitelist.txt` names seven files that no longer exist and
  blanket-waives `compiler.py`, `compiled.py`, `compilers/**`, `vectorized_env.py`,
  `affordance_engine.py`, `dac_engine.py`, `items/manager.py`, `action_executor.py`,
  `substrate/**`, `effects/**`, `world/**`. Regenerate it from a clean lint run after the P1s
  land; every surviving entry must name a line and a reason.
- **Residual deletion.** `_encode_scaled`/`_encode_absolute` in all five substrates;
  `EFFECT_OBSERVATION_SLOTS`; `configs/test/vfs_profiles_smoke/`;
  `scripts/validate_substrate_configs.py`'s `substrate.yaml` reader; `from_yaml` readers on
  `ItemsCatalogConfig`/`EnvironmentConfig`/`ActionsConfig`; dead public methods listed per seam.
- **Doc corrections.** Each plan ends with the specific lines in `docs/config-schemas/` and
  `docs/architecture/` that contradict behaviour. Correct them in the same change as the fix;
  a doc that lies is a defect, a doc that is merely thin is not.

## Backlog disposition

Of the 45 triage bugs in filigree, the review found 22 still live, 16 fixed and 7 obsolete
(surface deleted, concern re-checked on the replacement). The per-subsystem plans fold every
still-live bug into a work package by id. The 23 fixed-plus-obsolete entries can be closed on
the CLI with the reviewer's evidence as the closing note; `review-2026-10-24/findings_*.md`
holds it.

## How to use the reproduction scripts

Every work package cites a script under `review-2026-10-24/<seam>/`. They carry absolute
scratchpad paths from the review session; rewrite them once:

```bash
cd review-2026-10-24
grep -rl "/tmp/claude-1000" . | xargs sed -i "s|/tmp/claude-1000/-home-john-hamlet/[^/]*/scratchpad|$(pwd)|g"
```

Run from the repo root with `uv run python review-2026-10-24/<seam>/<script>.py`. The intended
end state is that each script's assertion moves into `tests/` as the fix lands and the script
is deleted.
