# PDR-0144 — Unit 5 is accepted: every surviving pack runs, every live token type and scope is exercised from a committed pack

Date: 2026-09-02   Status: **accepted** (within the grant; owner-preauthorised roll-in *"once its finished, you're preauthorised to roll into M5"*)
Author: Claude (standing product owner)
Related: `PDR-0132`, `PDR-0141`, `PDR-0142`, `PDR-0143`, `hamlet-55b2826a02`, `hamlet-fa6bb6da4a`,
`project-recovery-3@5973f79b` (scope ruling) … `@a07b889b` (final fix wave)

## Context

`PDR-0143` ruled unit 5's scope; the implementation ran as a five-task plan
(`docs/superpowers/plans/2026-09-02-token-unit5-pack-migration.md`) with a fresh implementer and a
task-scoped review per task, a whole-branch review, and one fix wave. Eleven commits landed on
`project-recovery-3` between the disposition ruling and the fix wave.

## What landed, against the tracker's acceptance

| acceptance bullet | satisfied by |
| --- | --- |
| Every surviving pack compiles and runs through a smoke/integration path | `tests/test_townlet/integration/test_pack_smoke.py` (`079ce167`, `de257b90`): discovered from the tree, 31 pack/level cases compile, construct, reset and step four times; presence lanes checked every step; done agents gated; every agent has a valid action at reset. Reference pack additionally stepped (`cb02851d`). |
| Every live token type and supported scope has a committed config-in/behaviour-out exercise | `self`/`meter`/`affordance`/`item`: pre-existing pack-driven tests re-pinned by measurement (`430eb5af`). `effect`: `test_effect_rows_appear_in_the_observation_when_an_effect_spawns` on `effects_smoke` (`7db18ec9`). `variable_element` global scope: `TestAuthoredDayPhase` on the real L3 pack (`430eb5af`). Agent scope: `token_set_smoke` (pre-existing). Item-arena scope: `test_exposed_item_variable_publishes_through_the_item_arena` on `items_smoke` (`7db18ec9`, guarded by `assert baseline == 1` and a profile-mismatch unit test, `a07b889b`). `agent`: structurally absent, asserted `census["agent"] == 0` on every discovered pack. |
| Unsupported shapes refuse loudly | `observation_mode` (`94656527`); nested `spawn_effect` / unknown command key via the effects command DTO (`cb02851d`); exposed expression variable without `initial_value` (`430eb5af`); exposed item variable at item capacity 0 and item variable type without a token dtype (`7db18ec9`, tests `a07b889b`). |
| `set_encoder_smoke` and L3 authored temporality re-authored on the accepted ABI | `token_set_smoke` already was (`PDR-0143` §1). L3 is one authored `day_phase` global with `cyclical_sin_cos`, sin and cos in one token, asserted at reset and after seven ticks (`430eb5af`). |
| No full-payload ABI, fallback, shim or stale configuration surface remains | `observation_mode` deleted from the DTO, all 30 packs, the shared test fixtures and the four documents that taught it; schema docs (`items.md`, `vfs-profiles.md`) and README realigned to the shipped contract (`a07b889b`, plus the nested `spawn_item` example in this checkpoint). |

**Engine changes and their guards.** Exposure of an expression variable is admitted when it
declares `initial_value` (the registry's reset value, hence the descriptor's `declared_initial`);
the compiler emits item-arena `variable_element` slots from exposed item-profile variables; the
item-arena publisher matches the occupant's profile before publishing (a real cross-profile leak,
found by the committed pack and now pinned by a test that fails without the fix). No engine code
branches on a variable's name. The no-defaults gate is clean without new whitelist entries.

**Oracle discipline.** `DIV-012` records four hash movers the `day_phase` run surfaced, each
bisected to its causing commit by the two-worktree method (`stratum_hash` → `94656527`;
`affordances_hash`, `environment_hash` → `c6c6b524`; `brain_hash` → `d554fb7f`), bound on all ten
cpu cells (`_DIV012` on standing and differential, `_DIV012_PROFILE` on profile cells); full
cpu-matrix run `20260902-100802` and the `items_smoke` run `20260902-110926` are
`DIVERGED_AS_REGISTERED` throughout, exit 0. CUDA cells remain declared, never run.

**Gates on `a07b889b`:** Ruff, Black, mypy (176 files), no-defaults (clean, 715 whitelisted),
compiler CLI validation (26 packs), `git diff --check` all green; pytest recorded in
`metrics.md` at this checkpoint.

## Filed, not folded in

- `hamlet-4b931faaf4` (P1 bug): held/exclusive items are invisible to the entire `item` token
  type — `lift_item` removes the row, so a carried item's presence, coordinates and item-arena
  state never reach the observation. Demonstrated in-tree by the item-arena test.
- `hamlet-obs-b959ce55c0` (observation): 3 of 13 item-arena `durability` rows are structurally
  dead weight (capacity formula versus the manager's allocation range).
- `hamlet-5a87550adb` closed: the reference pack's malformed `spawn_effect` shape now refuses at
  parse and the pack constructs and steps.

## Deferred with reasons (final-review triage)

Agent/Item DTO validator relaxations lack their own failing test (item relaxation is unreachable:
no item-profile evaluator exists); the reference-pack step test only issues WAIT; the smoke
test's done-agent branch is not naturally exercised by any discovered pack; the per-item
occupant loop is unvectorized; `_split_variable_element_slots` dispatches on the compiler's
`filler_ref` string convention (a `scope` on `SlotBinding` would be sturdier — declaration-store
unit territory). None changes behaviour a pack can observe.

## The call

**Unit 5 is accepted** and `hamlet-55b2826a02` closes. The token umbrella `hamlet-fa6bb6da4a`
closes with it: all three child milestones are terminal and the umbrella's own acceptance
(compact width, replay bytes, transfer, visibility, batch 256, the unit-4 floor) is carried by
`PDR-0136`, `PDR-0141` and this record. The `2026-10-06` trial-pack clock is discharged
(`PDR-0142`).

## Consequences

- The **Next** bet at the top of the roadmap is unchanged: the declaration-store compiler unit
  (`PDR-0117`) and the epistemic-access unit (`PDR-0120`). Two facts from this unit feed them:
  the `period: 24` / `day_length: 24` duplication is a one-declaration gap, and the
  `filler_ref` string contract wants a typed scope.
- `hamlet-d6fc84d147` (engine survival counter, `PDR-0140`) and `hamlet-4b931faaf4` are the two
  P1 engine defects on the board outside any unit.

## Reversal trigger

- If the four-cell L2 regression harness, run on any post-unit-5 commit, drops a cell below
  79.19466666666668, the pack-wide `day_phase` exposure reopens (`PDR-0143` trigger).
- If a shared-world declaration surface lands, the smoke test's `census["agent"] == 0` assertion
  fires and the agent-token exercise obligation becomes due on the same commit.
