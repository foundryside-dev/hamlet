# PDR-0143 — Unit 5 scope is ruled: `observation_mode` dies, `day_phase` is authored, agent tokens stay structurally absent

Date: 2026-09-02   Status: **accepted** (within the grant; the owner preauthorised the roll into
unit 5 — *"once its finished, you're preauthorised to roll into M5"*)
Author: Claude (standing product owner)
Related: `PDR-0114`, `PDR-0132`, `PDR-0136`, `PDR-0141`, `PDR-0142`, `hamlet-55b2826a02`,
`hamlet-5a87550adb`, spec `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` §6 unit 5

## Context

`hamlet-55b2826a02` accepts on five conditions: every surviving pack compiles and runs through a
smoke/integration path; every live token type and supported scope has a committed
config-in/behaviour-out exercise and unsupported shapes refuse loudly; `set_encoder_smoke` and
L3 authored temporality are re-authored on the accepted ABI; no full-payload ABI, fallback, shim
or stale configuration surface remains; and a final checkpoint records pack disposition and gates.
Measured on 2026-09-02 after `PDR-0142`:

1. **`set_encoder_smoke` is already re-authored.** `configs/test/token_set_smoke` (landed at the
   compact cut `d554fb7f`) declares the same `need_tokens` `tensor2d [4,3]` agent variable, both
   `L0_test` (mean) and `L1_attention` levels, and is driven config-in/behaviour-out by
   `tests/test_townlet/integration/test_token_set_runtime.py` (seven tests: the declared
   aggregator reaches the built network, tokens change its output, rows pool as a set,
   gradients reach the encoders, attention stays permutation-invariant). Nothing to re-author.
2. **L3 authored temporality is not done.** The engine's temporal observation block was deleted
   at the cut, so an L3 agent cannot observe time at all today. `default_curriculum` declares a
   `time_of_day_phase` global with `expression: tick` but leaves it unexposed, and the compiler
   refuses to expose any expression variable: *"variable_element identity requires one exact
   declared default"*. The spec's unit-5 line is explicit: *"L3 temporality becomes ONE authored
   `day_phase` variable with `cyclical_sin_cos` normalization → one token with the paired value
   block — never two scalar variables"*. The descriptor block already carries scope, semantic
   type, normalization kind and parameters (the cyclical period), dtype, lifetime and the
   declared initial value — everything that identity needs except the initial value an
   expression variable currently cannot declare.
3. **`observation_mode` is declared-but-inert.** `StratumConfig.observation_mode`
   (`full_auto | max_compact | full_manual`) has no consumer anywhere in `src/townlet/` outside
   its own DTO; all 30 compilable packs declare `full_auto`; STRATA.md cites a §6.4 that does
   not exist. Declared-but-inert config is the failure mode this product refuses.
4. **Agent tokens have no declaration surface.** `agent_capacity` is *declared agents-per-world
   − 1* and no pack, fixture or config key can declare a shared world; the type is structurally
   absent in every compiled level (capacity 0, including `L5_multi_agent`) and the publisher is a
   no-op by construction. The tracker has no issue for a shared-world declaration.
5. **`configs/reference/model_pack` compiles but cannot construct an environment**
   (`hamlet-5a87550adb`): `items.yaml` nests `spawn_effect` as a mapping where the command
   grammar wants `spawn_effect: <id>` with sibling `target` / `intensity` keys, and `intensity`
   must be a float literal. The compiler passes the malformed shape and the runtime refuses it.
6. **Several surviving packs are never stepped by any test**: `simple`, `trial002_money_log_gdp`,
   `trial_k_cold`, `gridnd_4d_pack`, `vfs_bar_access`, `vfs_dependency_chain`, and the reference
   pack. Compiling is not running.

## The call

- **Delete `observation_mode`** from the DTO, all 30 packs and the three documents that cite it.
  A pack still declaring it fails validation as an extra field. Deletion, not deprecation.
- **Author `day_phase` (spec form).** `default_curriculum/vfs_profiles.yaml` replaces the
  unexposed `time_of_day_phase` with one global `day_phase`: `expression: tick`,
  `initial_value: 0.0`, `semantic_type: temporal`, `normalization: {kind: cyclical_sin_cos,
  period: 24}`, `exposed_to: [agent]`. To admit it, the profile DTO allows `initial_value`
  **together with** `expression` (the declared reset value; the evaluator overwrites it every
  tick from 3.6 onward), and the compiler's refusal narrows to *an exposed expression variable
  must declare its `initial_value`*. The registry already resets to the declared initial value,
  so the descriptor's `declared_initial` is the true reset value by construction — no runtime
  assertion is needed and none is added. Because `vfs_profiles.yaml` is pack-wide and levels may
  not override it, **L0–L2 also observe the clock token**; their worlds ignore it (temporal
  mechanics inactive), and every `default_curriculum` `layout_hash` moves. The pinned M4 cohort
  is unaffected (its identity is frozen at `9d4e942f`). The `period: 24` duplicates L3's
  `day_length: 24` — a one-declaration gap recorded as a follow-up, not solved here.
- **Agent tokens are recorded as structurally absent, not built.** The inert-guard reads *every
  live token type*; a type with no authoring surface is not live. A shared-world declaration is
  its own authoring feature (WS-4 territory, the roadmap's L5 multi-agent) and is filed as such.
  Unit 5 asserts the absence explicitly (capacity 0 everywhere) so a future surface that makes
  it live also makes the exercise obligation loud.
- **Fix the reference pack's shape and make the malformed shape refuse at parse.** The items DTO
  validates each `on_use` / `on_pickup` / `on_drop` command through the effects command DTO
  instead of only checking a key exists; the reference pack test constructs and steps the
  environment. Closes `hamlet-5a87550adb` inside unit 5.
- **One pack-wide smoke test.** A parametrized integration test compiles, constructs, resets and
  steps every non-negative pack and level in `configs/` (discovered from the tree, so a new pack
  is exercised the day it lands and a deleted one stops silently) and asserts finite,
  correctly-shaped observations with every present row's presence lane set. The three negative
  VFS fixtures are excluded by name.
- **Coverage exercises per type and scope.** One integration test per gap that is not already
  driven from a pack: `variable_element` global scope moved by a declared expression
  (`day_phase` on L3), item-arena scope (`items_smoke`), and `effect` rows from a pack with a
  declared effect budget (`effects_smoke`). Existing pack-driven tests already cover `self`,
  `meter`, `affordance`, `item`, and agent-scope `variable_element` (`token_set_smoke`).

## Options rejected

- *Expose `time_of_day_phase` by exempting expression variables from the identity rule.*
  Rejected: identity would then rest on an opaque expression; the declared reset value is what
  makes two co-scoped clocks distinguishable or refused.
- *Declare `day_phase` only for L3 via a level file.* Rejected: level directories may not carry
  `vfs_profiles.yaml` (`PDR-0117` territory, the declaration-store unit); inventing a per-level
  override here would be a second declaration surface.
- *Build a shared-world declaration so agent tokens go live in unit 5.* Rejected: that is a new
  authoring feature with its own multi-agent semantics, not a migration.
- *Delete `configs/reference/model_pack`.* Rejected: it is the documentation reference the
  config schemas point at, and its defect is a five-line shape fix plus the compile-time refusal
  the tracker already asked for.

## Reversal trigger

- If the `day_phase` exposure moves the L2 token-regression floor result below 79.19466666666668
  when the four-cell harness is next run on a post-unit-5 commit, the pack-wide exposure is
  reopened (level-scoped declaration becomes the forcing case for `PDR-0117`).
- If a shared-world declaration surface lands, agent tokens become live and the coverage
  obligation fires on the same commit.
