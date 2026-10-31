# REVIEW 2026-08-24 — Universe Compiler architecture assessment

Commissioned question (John, verbatim): *"it was carefully architected and badly
implemented, and then it was better implemented but poorly architected so I'm curious
what we have and where does it need to get to and what could we get to with a bit more
effort."*

Sources: `src/townlet/universe/` read end-to-end (`compiler.py`, `raw_configs_v21.py`,
`symbol_table.py`, `pipeline.py`, `errors.py`, `source_map.py`, `cues_compiler.py`,
`loaders/`, `validation/`, `compilers/`, `compiled.py` structure, `__main__.py`);
design intent from `archive/COMPILER_ARCHITECTURE.md` (2025-11) and
`archive/UNIVERSE-COMPILER.md` (current-era). Read-only; nothing edited.

## Verdict on the characterization

**Both halves are right, and the halves are localized.** The 2025-11 design was
genuinely careful — a seven-sub-compiler dependency graph, source maps with file:line
diagnostics, an error-code taxonomy, three-tier orchestration (UAC → BAC → Training) —
and almost none of that architecture survived contact: the orchestrator was never
built, the design's input files (`substrate.yaml`, `variables.yaml`, `cascades.yaml`,
`global_actions.yaml`) don't exist, `CuesCompiler` was built and never wired
(`compiler.py:69`), `SourceMap` was built and never wired (`source_map.py` — zero
references outside its own file). The current compiler kept the design's *vocabulary*
(stages, symbol table, `CompilationError`) but not its *structure*.

The 2026 implementation is genuinely good at the leaves and honest at the boundaries —
fail-loud no-defaults enforcement, real provenance fingerprinting, careful cache
semantics, multi-error collection, ~5,070 lines of tests, PDR-anchored comments. One
refinement to John's framing: the current trunk is not so much *poorly* architected as
**unarchitected** — a hardcoded linear method whose stage numbering disagrees with
itself, typed stage boundaries it defines and then ignores, the same validations run
in three places, and an error taxonomy that fragmented. The leaf sub-compilers
(effects, actions, optimization) are clean; the debt is concentrated in the trunk
(`compiler.py` + the validation split) and in the dual-declaration-surface config
model it inherited.

---

## 1. What we have

### 1.1 The real pipeline vs the claimed seven stages

`_log_stage` emits **eight** numbered stages; the comments and method names carry a
*different* numbering (`Stage 0` twice, `1b`, `1c`, then methods named
`_stage_5_/_stage_6_/_stage_7_` that log 6/7/8). The actual sequence:

| # | logged as | what actually runs | evidence |
|---|---|---|---|
| — | — | scoping preflight, no YAML parse | `compiler.py:103`, `loaders/preflight.py:37` |
| — | — | cache fast-path (hash+mtime+provenance staleness; mislabel guard) | `compiler.py:115-147` |
| — | — | YAML syntax sweep, filename manifest hardcoded | `preflight.py:102-168` |
| 1 | Parse | `RawConfigsV21.from_experiment_dir` — 16 filenames hardcoded, per-file error aggregation | `raw_configs_v21.py:84-321` |
| 2 | Limits | size caps | `validation/limits.py` |
| 3 | **Cross-validate semantics** | scoping *again*, temporal/vision/substrate checks, **vocabulary-lockstep police** (see 1.4) | `validation/semantics.py:55-363` |
| 4 | Symbol table | registers env.yaml meters/cascades/affordances/variables + profile vars + custom actions + items | `validation/references.py:14-58` |
| 5 | Resolve references | level cascade/affordance/item refs + DAC references (more cross-validation) | `references.py:228-294` |
| 6 | Shared artifacts | VFS profiles compile, effects schema+catalog, history spec | `compiler.py:292-335` |
| 7 | Per-level compile | obs spec, activity, actions, meter/affordance metadata, spawn predicates, optimization data, VTC schedule, **all hashes** | `compiler.py:337-479` |
| 8 | Emit | `CompiledUniverse` + msgpack cache (loud cache-write failure) | `compiler.py:481-573` |

Two structural notes: **cross-validation is split across stages 3 and 5, sandwiching
the symbol table** — the design's clean parse → symbols → resolve → cross-validate
order exists only in the doc; and metadata/optimization are not stages at all but
per-level loop steps. `compiler.py:1` still says *"Stage 1 scaffolding."*

### 1.2 Clean seams (the "better implemented" evidence)

- **`EffectsCompiler`** (`compilers/effects.py`, 89 lines) — a real boundary: build
  schema, compile catalog, done.
- **`CompilationErrorCollector`** (`errors.py`) — multi-error aggregation with hints;
  an author sees *all* pack errors at once. Used consistently at parse/limits/
  semantics/references.
- **Cache/provenance discipline** — fingerprint = config_hash + compiler version +
  git SHA + python/torch/pydantic versions (`compiler.py:613-626, 734-759`); missing
  fingerprint fields = stale; mislabelled artifact = loud failure outside the
  defensive read (`:115-127`); failed cache write fails the compile (`:557-570`).
  Per-level artifacts with an explicit comment refusing a pack-wide default
  (`:668-677`). This is learned experience captured in code.
- **`compiled.py` serialization** — no pickle; msgpack with `_required_field`
  discipline and `COMPILED_SCHEMA_VERSION = "1.19"`. Disciplined — but see 1.5.
- **No-Defaults threading** — explicit refusals for `day_length`,
  `experiment.version`, `interaction_radius` (`metadata.py:125-151`,
  `semantics.py:158-165`).
- ~5,070 lines of tests under `tests/test_townlet/unit/universe/`.

### 1.3 Dead architecture (complete inventory, grep-verified no callers)

| item | size | evidence |
|---|---|---|
| `CuesCompiler` — designed as "first-class component" (§5.3), instantiated, never called; no cues.yaml loader exists; `symbol_table.cues` + `register_cue` never populated | 143 lines + `config/cues.py` | `compiler.py:69`; grep: only def sites |
| `SourceMap` — designed §2.6 as Stage-1 output; fully implemented **including a line-number-annotating YAML loader**; referenced nowhere | 101 lines | `source_map.py:24`; grep: zero external refs |
| `UniverseCompiler.__init__` result fields — six `self._*: X | None = None` never read or written again | 6 fields | `compiler.py:70-75` |
| `pipeline.py` typed bundles — `ResolvedConfigBundle` **returned and discarded** (`compiler.py:171` ignores the return); `CompiledArtifactBundle` constructed nowhere; `LoadedConfigBundle` a one-field wrapper | ~30 lines | `pipeline.py:23-59`, `references.py:294` |
| `semantics.py:344-347` — loops DAC modifiers, computes the invalid-reference condition, then `pass`. An unfinished validation that reads as if it works | 4 lines | `semantics.py:341-347` |
| `OptimizationCompiler.resolve_day_length` — never called; the same check lives inline at `semantics.py:88-94` **and** `metadata.py:125-135` (three copies) | 13 lines | grep: def only |
| `UniverseMetadata` economics — `max_sustainable_income=0.0, total_affordance_costs=0.0, economic_balance=0.0` hardcoded | 3 fields | `metadata.py:172-174` |

### 1.4 Load-bearing tangles

- **`ObservationCompiler`** (965 lines) is the center of gravity: meter
  normalization + profile exposure + item slots + activity masks + **synthesizing
  `VariableDef`s from environment.yaml with the hardcoded
  `readable_by`/`lifetime`** the VFS audit flagged (`observation.py:811-812,
  865-867`). Three distinguishable concerns (variable synthesis, exposure/
  normalization policy, layout spec) share one class. The unit-3 token cut lands
  directly on it.
- **The dual-surface vocabulary police.** `semantics.py`'s largest section
  (`:167-269`) exists to enforce that environment.yaml's meters/affordances/
  cascades/modulations **exactly mirror** each level's bars.yaml/affordances.yaml —
  the compiler spends its cross-validation budget policing a duplication the config
  model shouldn't have. The same dual-surface split is why `MetadataCompiler`
  stitches meters from environment.yaml order with initials from bars.yaml
  (`metadata.py:40-57`, with a silent `0.0` fallback at `:46` that only stays
  unreachable because the lockstep check runs first).
- **Provenance knot**: `MetadataCompiler` takes three callbacks into
  `UniverseCompiler` privates (`compute_config_mtime`, `build_cache_fingerprint`,
  `get_git_sha`, `metadata.py:25-38`) — hashing/provenance logic split across two
  classes in a circular hand-off.
- **`getattr`-probing on required fields** throughout `references.py`,
  `semantics.py`, `effects.py` (`getattr(env, "meters", []) or []`) — the compiler
  doesn't trust its own DTO types, which mutes mypy and hides schema drift.
- **`validate_dac_references`** (`references.py:61-226`): a 165-line elif chain over
  `shaping.type` with 13 near-identical blocks — works, but every new shaping type
  edits a wall.

### 1.5 Error reporting & provenance quality

Good bones, fragmented delivery:

- **Code namespaces fragmented**: `UAC-VAL-*` (cues only — dead), `UAC-RES-*`,
  `DAC-REF-*`, `SCOPING_*`, `CONFIG_LIMIT_EXCEEDED`, `LOAD_ERROR`,
  `YAML_SYNTAX_ERROR`, plus bare `ValueError`s escaping the taxonomy entirely from
  `OptimizationCompiler` (`optimization.py:57,72,81`) and `MetadataCompiler`
  (`metadata.py:127,147`). No registry anywhere.
- **Locations are file-level only.** `SourceMap` is unwired, so no diagnostic
  carries a line number — while `archive/UNIVERSE-COMPILER.md` §4 claims "file:line
  info". Doc-drift in the *current-era* doc.
- **Ghost filename**: every `DAC-REF-*` location cites `drive_as_code.yaml`
  (`references.py:77-224`) — a file that does not exist in any pack (the real file
  is `drive.yaml`; CLAUDE.md explicitly warns the name is dead). The compiler's own
  diagnostics point authors at a nonexistent file.
- VFS domain errors are wrapped at stage granularity with directory-level location
  (`compiler.py:187-193, 234-240`) — a profile type error reports
  `vfs_profiles.yaml` or `levels/`, nothing finer.
- Duplicate-registration policy is inconsistent: `register_variable` raises on
  duplicates, `register_profile_vfs_variable` silently `setdefault`s
  (`symbol_table.py:34-46`).

---

## 2. Where it needs to get to

The four decided directions all land on the same two structures, which is the good
news — one target shape serves all four without a second rewrite:

**Target shape in one sentence:** a *declaration-store* compiler — a discovery/merge
front end producing one provenance-carrying declaration store; a middle that compiles
typed declaration families (variables, actions, affordances, effects, drive,
transitions) against one symbol table; and an emission layer that serializes the
artifact and hash tree mechanically instead of by hand-maintained mirror.

1. **PDR-0117 (files are transport)** replaces exactly the front third:
   `RawConfigsV21.from_experiment_dir`'s 16 hardcoded filenames, `preflight.py`'s
   manifest sweep, and — this is the payoff — the **entire vocabulary-lockstep
   police** in `semantics.py` and the level-scoping checks, all of which become
   merge-by-id rules with loud collision refusal instead of duplication police.
   `SourceMap`'s parallel line-annotating loader is the right provenance mechanism
   and is already written (it must stay a parallel load — its `__line__` injection
   would violate `extra="forbid"` if fed to the DTOs).
2. **Variable-surface unification** (the VFS audit's systemic gap) is the *same
   work*: one `VariableDef` semantics regardless of arrival surface kills the
   environment.yaml/vfs_profiles/variables_reference triplication, the hardcoded
   `readable_by`/`writable_by`/`lifetime` (`observation.py:811-867`,
   `compilers/vfs.py:313-320`), and the symbol-table hole
   (`references.py:35-49` never registers `variables_reference` variables).
   PDR-0117 without unification is half a fix; plan them as one unit.
3. **Unit-3 TokenSpec emission** (Tasks 6-9) replaces the layout third of
   `ObservationCompiler` plus the hash computations at `compiler.py:398-419`. It
   effectively performs the concern-split 1.4 asks for — after the cut,
   `ObservationCompiler`'s remaining halves (variable synthesis, exposure policy)
   should be named as their own modules rather than left in the 965-line file.
4. **Trio mirroring (Strata/UAC/BAC)**: mirror the trio at the **artifact and hash
   level**, not as three monolithic sub-compilers. Strata already has a real seam
   (`SubstrateFactory` consumed at `metadata.py:111` and validation); BAC's seam is
   `brain_hash` + the ObservationSpec/TokenSpec handoff. The world half is
   intrinsically multi-pass (declarations → schemas → programs) — forcing it into
   one "UAC sub-compiler" box would recreate the observation.py tangle at larger
   scale. The `CompiledUniverse` field list and the hash tree are where the trio
   should be legible.

**Sequencing constraint:** the front-end rewrite (1+2) is its own unit *after* the
token cut — it touches the same files unit 3 is frozen against, and the cut's
delta-check gates assume today's parse behavior.

---

## 3. What a bit more effort buys

Ranked; S = hours, M = days, L = a week+.

| # | effort | opportunity | unlocks | risk |
|---|---|---|---|---|
| 1 | S | **Delete the dead seams**: CuesCompiler + `config/cues.py` + cues/`register_cue` registry; the six `__init__` result fields; `resolve_day_length`; the `semantics.py:344-347` pass-loop (or finish it — decide which, it currently *looks* like validation); economics fields in `UniverseMetadata`; retire or honor `pipeline.py`'s unused bundles | ~500 lines gone; the new `COMPILER.md` documents an honest structure | nil — grep-verified no callers |
| 2 | S | **One authoritative stage enum** used by `_log_stage`, comments, method names, and error `stage` labels | tests/docs can assert pipeline order; ends the 0/0/1/1b/1c/5-logs-6 drift | log-string assertions in tests need a sweep |
| 3 | S | **Error-code registry + fix the `drive_as_code.yaml` ghost filename**; route `OptimizationCompiler`/`MetadataCompiler` raises through `CompilationError` | triage-able diagnostics; no author chases a nonexistent file | nil |
| 4 | M | **Wire `SourceMap`** for today's files: parallel line capture at parse, thread `file:line` into the top error classes (load, reference, DAC, vocab, scoping) | line-level diagnostics *now*, and it is the provenance rail PDR-0117 requires — pre-work, not throwaway | double-parse cost is negligible at pack sizes |
| 5 | M | **Honor the typed pipeline**: make `compile()` a fold over stage functions consuming/producing the `pipeline.py` bundles; extract the provenance callbacks into one `Provenance` helper | independently testable stages; the seam incremental compilation would need later | churn in files the token cut touches — fold into or sequence after Task 7 |
| 6 | M | **Deduplicate triplicated validation**: day-length ×3, cascade refs ×3 (resolve/semantics/optimization), scoping ×2 (preflight/semantics) — one pass each | single source of truth per rule | subtle ordering differences; keep the oracle matrix green |
| 7 | L | **Schema-driven serialization** for `compiled.py` (derive to_dict/from_dict from dataclass introspection) — ends the hand-mirror behind 19 schema bumps | every future schema change stops taxing two more functions | this is the layer Task 7 rewrites hashes through — do it **with or after** the token cut, never before |

**Explicitly do NOT:**

- Build the 2025-11 three-tier `HamletOrchestrator` — nothing needs it; the CLI and
  DemoRunner are the real entry points.
- Resurrect the seven-sub-compiler dependency-graph engine — a linear pipeline with
  honest stages is the right size for this compiler; the design's graph solved a
  coordination problem this codebase doesn't have.
- Add incremental/partial compilation beyond the existing artifact cache — compile
  is fast at shipped pack sizes; that's complexity with no measured pain. Revisit
  only if discovery-merge (PDR-0117) makes packs large enough to hurt, with a
  measurement in hand.

## Cross-references

- `archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md` — the VFS audit whose
  variable-surface findings this assessment's target shape incorporates.
- PDR-0117 (files are transport), PDR-0118 (five-doc HLD) —
  `docs/product/decisions/`.
- Unit-3 plan Tasks 6-9 (`docs/superpowers/plans/2026-08-24-token-obs-unit3-baselines-div008-cut.md`)
  — the committed emission-layer work this assessment sequences against.
