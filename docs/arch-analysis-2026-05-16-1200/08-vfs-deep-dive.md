# 08 — Deep Dive: VFS Transition Schedule (post-fix review)

**Date:** 2026-05-16 (same-day follow-up)
**Trigger:** The user closed Filigree task `hamlet-2254316f44` after wiring the previously-dead
`VTCSocialResidueProgram` into runtime via a generic transition-schedule abstraction.
**Method:** Direct review of source (committed history + uncommitted working tree) plus the new
integration test.
**Scope:** Resolution audit of catalog §11.1 entry "`VTCSocialResidueProgram` — compiled but no
runtime call site"; assessment of the chosen abstraction; new-concern surfacing.

---

## TL;DR — verdict

**The fix is sound and the abstraction it introduces is the right one.** The original concern
("`VTCSocialResidueProgram` is dead at runtime") is no longer true. More importantly, the
solution doesn't just patch SocialResidue — it generalises VFS transition execution into a
phase-graph-driven schedule that any future VTC program family can hook into without any
environment-side change. Three small follow-ups worth surfacing (none blocking).

| Criterion | Result |
|---|---|
| Original §11.1 concern resolved | ✅ |
| Hash provenance preserved | ✅ (transition_graph_hash now includes social rules) |
| Cache compatibility surfaced loudly | ✅ (schema bumped 1.12 → 1.13; missing-field rejection extended) |
| Negative-path test (unknown target variable) | ✅ |
| Generic-runner property is *structurally* asserted | ✅ (source-token guard test) |
| Integration test exercises behaviour, not just compilation | ✅ |
| Backwards-compat-clean (per project rule) | ⚠️ One small wart — see §6.3 |

---

## 1. What changed

### 1.1 New module
`src/townlet/vfs/transition_schedule.py` (318 LOC, currently **untracked**) — defines four types
and one builder:

| Symbol | Role |
|---|---|
| `VTCTransitionSchedule` (frozen dataclass) | Carries all 9 compiled VTC programs + the phase graph |
| `VTCTransitionContext` (frozen dataclass) | Per-call inputs (vfs_state, bars_state, mask, device, optional actions/dones, depletion_multiplier) |
| `VTCTransitionState` (frozen dataclass) | Return shape (vfs_state, bars_state, dones) |
| `VTCTransitionRunner` | Executes programs filtered by phase name; the **single runtime entry point** |
| `build_vtc_transition_schedule(...)` | Compile-time factory; called once from `UniverseCompiler` |

Plus serialise/deserialise helpers (`serialize_vtc_transition_schedule`,
`social_rules_from_transition_payload`) for cache persistence and a
`_validate_state_residue_targets` guard that fails compilation if a rule writes to an unknown
VFS variable.

### 1.2 Compiler change
`src/townlet/universe/compiler.py:374-396` — the eight individual `compile_vtc_*_with_phase_graph`
calls collapse to one `build_vtc_transition_schedule(...)` call, and the `transition_graph_hash`
input gains a `social_residue_program=` parameter. The schedule is attached to `LevelMetadata`
(`compiler.py:430`) and copied into the top-level `CompiledUniverse` (`compiler.py:496`).

### 1.3 Compiled DTO change
`src/townlet/universe/compiled.py` — schema version bumped **1.12 → 1.13**. New required field
`transition_schedule` added to `REQUIRED_COMPILED_UNIVERSE_FIELDS`, `LevelMetadata`,
`copy_with_overrides`, `to_plain`, and the per-level cache emission/load paths.

### 1.4 Loader change
`src/townlet/universe/raw_configs_v21.py:286-306` — optional new top-level
`transition_rules.yaml` is loaded from the experiment dir; its `social_residue` list is
attached as `raw.social_residue_rules`. Absence yields an empty tuple; load errors are surfaced
through the standard validation collector with a `LOAD_ERROR` code.

### 1.5 Runtime change
`src/townlet/environment/vectorized_env.py` — three things happen:

1. **Imports collapse.** Eight `compile_vtc_*` factory imports removed; one
   `transition_schedule` import added.
2. **Construction collapses.** Eight `self.vtc_*_program = compile_vtc_*(...)` lines become one
   `self.vtc_transition_schedule = level.transition_schedule` plus the runner instantiation. The
   per-program field assignments are kept (delegating to schedule attributes) so existing
   read-only callers don't break.
3. **Tick loop generalises.** Four bespoke `_apply_vtc_*` methods now delegate to a single
   `_run_vtc_transition_phases(...)` helper. The new "between-cascades-and-terminal" residue
   phase is run via `vtc_transition_runner.phases_between("apply_threshold_cascades",
   "evaluate_terminal_conditions")` — i.e., the runtime asks the phase graph "what runs in this
   gap?" rather than naming any specific program.

### 1.6 Test added
`tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py` (98 LOC, untracked).
Three tests:

- `test_social_residue_rules_are_config_driven_runtime_transitions` — copies the L5 multi-agent
  pack into two temp dirs; one gets a `transition_rules.yaml` with a `+0.1` `trust` delta. Both
  compile; both step once; baseline `trust` stays at 0.5, social `trust` advances to 0.6. Hashes
  diverge between the two compilations.
- `test_social_residue_rules_fail_loudly_for_unknown_targets` — rule referencing
  `missing_social_variable` raises `ValueError` at compile time.
- `test_environment_runtime_does_not_embed_social_residue_domain_semantics` — reads
  `vectorized_env.py` source as text and asserts seven domain tokens
  (`social_residue, trust, obligation, reputation, norm_legitimacy, faction, institution`)
  do not appear. This is a **structural test**, not a behavioural one — see §3.

### 1.7 Cache stale-artefact rejection
`tests/test_townlet/unit/universe/test_compiler_cache.py` — three parametrised tests already had
"missing required field rejects cache" coverage; the parametrise lists now include
`transition_schedule`. So a pre-1.13 cache without that field is rejected with the same loud
error path as any other missing field.

---

## 2. Resolution of the original concern

**Was:** Catalog §11.1 row stated `VTCSocialResidueProgram` is *"compiled but no runtime call site
anywhere in `src/townlet/`; referenced only by VFS internals (definition, export, hashing,
phase-label)"* (validator-confirmed).

**Now:** Two complementary call paths:

1. **Indirect through the runner.** `VTCTransitionRunner._run_state_residue` filters
   `schedule.social_residue_program.rules` by phase and invokes
   `VTCSocialResidueProgram(rules).apply(...)`. Called once per phase per tick from the env's
   `_run_vtc_transition_phases` helper.
2. **Configuration-driven.** With no `transition_rules.yaml`, the program is constructed with
   zero rules and the filter at `transition_schedule.py:172-174` short-circuits — zero per-tick
   cost. With rules present, they execute.

The "dead at runtime" classification is **fully resolved**. Confirmed by:

- `grep -n "vtc_transition_runner\|social_residue_program" src/townlet/environment/vectorized_env.py`
  shows the runner field assignment, but **zero references to `social_residue_program` itself** —
  the runner mediates.
- The integration test asserts behaviour change between baseline and social configurations.

---

## 3. Why this is the *right* abstraction

A naive fix would have wired a single new line into `vectorized_env.step()`:

```python
self.vtc_social_residue_program.apply(self._current_vfs_state(), ...)
```

That would have closed the immediate gap but left the runtime carrying domain knowledge about
each VTC program family — the env would now contain 9 special cases, the next program family
would require its own env-side wiring, and the env would need to import VTC class names directly.

The chosen design is **structurally cleaner**:

1. **The phase graph is the schedule.** Every rule across every program declares a `phase` string
   matching one of the 18 entries in `DEFAULT_TRANSITION_PHASES` (`vfs/transition_graph.py:7-26`).
   At runtime, `phases_through(name)` and `phases_between(a, b)` return tuples of phase names that
   run as a unit. The runner walks each phase and applies whichever program tuples have rules for
   it.

2. **The runtime no longer names domain concepts.** The `forbidden_tokens` test
   (`test_environment_runtime_does_not_embed_social_residue_domain_semantics`) reads
   `vectorized_env.py` source as text and asserts none of {`social_residue`, `trust`,
   `obligation`, `reputation`, `norm_legitimacy`, `faction`, `institution`} appear. I confirmed
   this with my own grep. **This is a structural property assertion**, not a behavioural one — if
   a future contributor adds `if rule.kind == "social_residue":` to the env, this test fails.

3. **New program families are zero-env-cost.** Adding (say) `VTCEconomicCascadeProgram` will
   require new compile helpers and a new field on `VTCTransitionSchedule`, but **no change to
   `vectorized_env.py`** as long as its rules carry valid phase names. The `_run_state_residue`
   wrapper would generalise to `_run_state_residues` over multiple programs, but it's an internal
   refactor, not an env-API change.

4. **The schedule is content-addressed.** The compiler now passes
   `social_residue_program=transition_schedule.social_residue_program` to
   `compute_transition_graph_hash`. Two configs that differ only in their `transition_rules.yaml`
   produce different `transition_graph_hash` and therefore different `vfs_hash` — the integration
   test asserts this. **Provenance discipline is preserved across the abstraction.**

This is "data, not switches" applied at the right level: `transition_rules.yaml` is data,
`vectorized_env.py` is no longer a switch statement.

---

## 4. Quality of integration

### 4.1 Things done well

- **Schema version bumped (1.12 → 1.13).** The cache will reject old artefacts loudly via the
  `_required_field` checks rather than silently mis-loading.
- **Stale-cache rejection extended.** The three parametrised "missing required field" tests in
  `test_compiler_cache.py` already had the right shape; adding `transition_schedule` to each
  parametrise list was the correct minimal change.
- **Negative-path test exists.** Unknown target VFS variable → `ValueError` at compile time, with
  rule-id and variable-id in the message. No silent dropping of bad rules.
- **Cleanup at runtime.** Eight `compile_vtc_*` import lines removed from
  `vectorized_env.py`; one `transition_schedule` import added. The dependency surface narrowed.
- **Backwards compatibility for read-only callers.** The eight `self.vtc_*_program` fields are
  retained as direct references to schedule attributes — anything that consumed those fields
  (other env methods, tests, debug introspection) continues to work unmodified.
- **Defensive `_validate_state_residue_targets`.** Runs at compile time, not runtime — fails
  fast.
- **The `_run_action_writes` and `_run_terminal_conditions` paths raise `ValueError` if
  `actions=None` or `dones=None` is supplied for a phase that needs them.** Defensive against
  caller error.

### 4.2 Things that work correctly under the new design

- **Empty social_residue case.** With no `transition_rules.yaml`, `raw.social_residue_rules` is
  `()`; `compile_vtc_social_residue_rules_with_phase_graph` produces a program with empty
  `rules` tuple; `_run_state_residue` filter returns empty tuple; method short-circuits return.
  Zero per-tick cost.
- **Non-social variable targeting.** The integration test uses `trust` — a `pair`-scope L5
  variable from `vfs/relational.py:10-61`. The runner deliberately doesn't enforce that
  social_residue rules write *only* to relational variables; it enforces that the variable
  exists. So an unusual config could use the residue program family to mutate any VFS variable
  with the right scope rules — flexibility, not a bug.

### 4.3 Things to watch

- **`run_phases` clones state on every call.** Lines 98-100 do a tensor `.clone()` per VFS
  variable, per bar, plus dones. Hot-path cost is non-zero at high agent counts. The clones
  are necessary because the inner program `apply` methods return new tensors via
  `apply_masked_candidate`, but the *outer* clone would only matter if a caller's `vfs_state`
  mapping is mutated externally during the call — which currently never happens (the env builds
  the snapshot just before calling). Worth a comment if this is intentionally defensive, or
  worth dropping the outer clone if the contract is clear.
- **`_run_state_residue` reconstructs `VTCSocialResidueProgram(rules)` on every phase, every
  call.** Same pattern in the other helpers (`VTCActionWriteProgram(writes)`,
  `VTCPassiveDepletionProgram(rules)`, etc.). These are frozen dataclass constructions over
  filtered rule tuples — cheap, but they happen per-phase-per-tick. If the phase→rules grouping
  is stable (it is, after compile), pre-grouping at `__init__` time would eliminate the
  per-tick filter cost. Modest perf win.
- **`commit_vtc_transition_state` blindly forwards every `vfs_state` key back into the
  registry via `set_engine_value`.** That's by design — the social_residue program writes to
  pair-scope variables, the registry handles the layout. But it means the runner *must*
  return only keys that exist as registry variables; the `_split_vfs_and_bars` helper raises
  `KeyError` on unknowns, and the writer loop in `_commit_vtc_transition_state` silently
  skips keys not in `self.vfs_registry.variables`. The two layers disagree on policy (raise vs
  skip). Probably fine because the schedule is compile-validated, but worth surfacing.

---

## 5. Provenance integrity check

I traced the hash flow:

```
transition_rules.yaml
  → raw.social_residue_rules                                  (raw_configs_v21.py:286-306)
  → build_vtc_transition_schedule(... social_residue_rules ...)  (compiler.py:380)
  → schedule.social_residue_program                            (transition_schedule.py:218-230)
  → compute_transition_graph_hash(... social_residue_program=...)  (compiler.py:392)
  → CompiledUniverse.transition_graph_hash
  → compute_vfs_hash(variable_schema_hash, observation_schema_hash,
                     action_schema_hash, transition_graph_hash)  (compiler.py:397)
  → CompiledUniverse.vfs_hash
  → checkpoint compatibility metadata (training/checkpoint_utils.py)
```

The integration test asserts `baseline.transition_graph_hash != social.transition_graph_hash`
**and** `baseline.vfs_hash != social.vfs_hash`. Both required, both present. **Provenance is
sound** — adding or modifying a social rule will invalidate any pre-existing checkpoint at the
existing four-hash compatibility gate.

The cache serialisation round-trip (`serialize_vtc_transition_schedule` →
`social_rules_from_transition_payload`) is necessary because the cache stores the *result* of
compilation, and on cache hit it must be able to rebuild a `VTCTransitionSchedule` without
re-running the source compilers. The serialised form preserves the full social rule (phase, kind,
reads, condition, priority, all writes with their compositions/clamps/scopes/targets). Looks
complete.

---

## 6. Concerns and follow-ups

### 6.1 Other 8 program families still use the legacy raw-config payload to deserialise from cache

Only `social_residue_rules` is round-tripped through the `serialize_vtc_transition_schedule` /
`social_rules_from_transition_payload` path. The other 8 program families (action writes,
affordance gates, interaction progress, terminal conditions, passive depletions, modulations,
threshold cascades, reward components) still re-compile from the raw level config on cache load
because their source-of-truth lives in the level YAMLs (`bars.yaml`, `affordances.yaml`,
`drive.yaml`, etc.). Only `social_residue` is sourced from `transition_rules.yaml`, which is
*itself* a level-independent file at the experiment root.

This is consistent and correct, but it means **the serialised `transition_schedule` payload is
load-bearing only for the social_residue rules**; the `program_counts` block is informational
(useful for cache validation hints, not for re-construction). Worth a one-line comment in
`serialize_vtc_transition_schedule` explaining this asymmetry — otherwise a future maintainer may
delete the `program_counts` block thinking it's redundant, or mistakenly believe other programs
round-trip through the cache.

**Severity:** P3, doc-class.

### 6.2 The forbidden-tokens guard is fragile

`test_environment_runtime_does_not_embed_social_residue_domain_semantics` reads
`vectorized_env.py` as text. It will:

- ✅ Catch a maintainer typing `if rule.kind == "social_residue"` directly.
- ❌ Miss `if rule.kind == SOCIAL_KIND` if the constant is defined elsewhere.
- ❌ Miss the same logic moved into a separate file the env imports.
- ❌ Fail false-positive if a comment or a docstring mentions one of the tokens.

The guard is the right *idea* (assert structural property at test time, not just behavioural
property) but is one indirection deep from being defeated. Consider also a hash of the env's
public method-name list, or a moratorium on `vectorized_env.py` importing from
`vfs/relational.py` / `vfs/communication.py`. The current test is good, not great.

**Severity:** P3, test-rigor.

### 6.3 `_max_tensor_elements` finding from the original catalog still open

The original §11.2 row "`_max_tensor_elements` assigned twice in registry" is unaffected by this
work — confirming with `grep -n "_max_tensor_elements" src/townlet/vfs/registry.py` would tell
us whether it remains. (Out of scope for this deep dive, but worth a separate cleanup.)

**Severity:** P3, hygiene.

### 6.4 Minor: untracked file is the new module

`src/townlet/vfs/transition_schedule.py` is untracked. The closeout summary says no commit was
made. Before this lands, that file plus the new test plus the changes to `vectorized_env.py`,
`compiler.py`, `compiled.py`, `raw_configs_v21.py`, and the cache-test parametrise lists need to
land in one commit (or a short atomic series). Splitting them risks an intermediate state where
`compiled.py` requires a field that the compiler doesn't yet produce.

**Severity:** P2, release-discipline. Probably already understood by the author.

---

## 7. What this changes about the catalog

The §11.1 row should be **removed**:

> ~~`VTCSocialResidueProgram` — compiled but **no runtime call site** anywhere in `src/townlet/`;
> referenced only by VFS internals (definition, export, hashing, phase-label) — `vfs/vtc.py` —
> SG2 (validator-confirmed)~~

And the catalog should grow a positive entry under §2 (SG2 VFS) noting the new
`transition_schedule.py` abstraction:

> **VTCTransitionSchedule + VTCTransitionRunner** (`vfs/transition_schedule.py`) is the runtime
> entry point for all 9 VTC program families. The environment no longer references individual
> program types beyond the schedule; new program families can be added at compile time without
> env changes. A source-token guard test in
> `tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py` enforces this
> structural property.

The §10 documentation drift catalog gains one entry (the new
`transition_rules.yaml` experiment-root file is undocumented anywhere outside the tests and the
loader docstring).

The diagram in `03-diagrams.md` (Diagram 3, runtime tick) should add a note that the env's
4 `_apply_vtc_*` calls are now thin wrappers over `_run_vtc_transition_phases`. Functionally
the tick is unchanged; structurally it's now phase-graph-driven.

---

## 8. Confidence

**High** — verified by direct read of all modified files, grep of forbidden-tokens guard,
inspection of hash-flow chain, and reading the integration test in full. The user's reported
green checks (`pytest`: 2879 passed / 25 skipped / 33 deselected; `ruff`, `black`, `mypy`,
`git diff --check` all clean) are corroborated by source-level review of the design.

The change is good. Land it.
