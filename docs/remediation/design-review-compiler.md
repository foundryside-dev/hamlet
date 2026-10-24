# Compiler design review: first principles

Written 2026-10-24 against `fix/compiler-effects-remediation` at `e9a19a86` with compiler WP3 and
WP4 in the working tree. Read-only; nothing in `src/`, `configs/` or `tests/` was changed. This is
a design review, not a bug hunt: `findings_compiler.md` F-numbers and `compiler.md` C-numbers are
cited, not re-reported. The input is `design-review-vfs.md` and its five changes (independent
worlds, one spelling and one resolver, meters folded into VFS, a nine-field declaration,
synchronous dataflow with `prev` and events); the question is what the compiler must become to
serve them while staying the thing a web form calls.

Evidence base: `docs/architecture/{COMPILER,HLD}.md`, `docs/config-schemas/declarations.md`,
`CLAUDE.md`; every file under `src/townlet/universe/` (compiler, declarations, raw configs,
symbol table, the four validators, the six sub-compilers, `compiled.py`, `token_spec.py`,
`token_hashes.py`, `error_codes.py`, `errors.py`, `source_map.py`, `__main__.py`), the 22 DTO
modules in `src/townlet/config/`, `training/checkpoint_utils.py`, `vfs/schema_hashes.py`,
`vfs/transition_schedule.py`, the runtime compile sites in `environment/affordance_engine.py`,
`items/manager.py` and `effects/catalog.py`, `scripts/validate_compiler_cli.py`, the CI
workflow, the round-1 findings, the remediation plan, the synthesis and the risk document. Two
probes were run on scratch copies of `configs/simple` (section 4).

## Summary for the owner

The compiler has one good idea at its centre and it is already built: declarations are discovered
by content, merged with provenance, and refused with both origins when they collide. Around that
front end sits a pipeline designed for a pre-VFS ontology: nine stages where the docs say seven,
four validators that check the same fact in two to four places, five expression schemas for one
symbol table, three command compilers of which only one runs inside the compiler, nineteen
declared hashes computed by three different hashing functions, and 145 bare `ValueError`s beside
111 structured diagnostics. The five changes, in the order I would make them:

| # | change | one-line reason |
|---|---|---|
| 1 | The compiler compiles every program: affordance interactions and item hooks move from `affordance_engine.py:114` and `items/manager.py:96` into the compiler, compiled programs ride on the artifact, and the runtime owns no parser, type checker or schema dict | Two of the three command compilers run at environment construction, so "compiles green, never executes" is structural: the universe compiler never sees those programs |
| 2 | One symbol table and one resolver: `ExpressionSchema.for_context(kind)` built from the symbol table replaces the five schema builders; the validators collapse into one `check` pass with one collector; family compilers become lowering passes that validate nothing | VFS change 2 is this resolver; the duplicate checks in section 1 exist only because five code paths each rebuild the same name table |
| 3 | One diagnostic record, everywhere: `code, severity, location (file:line and declaration path), what, why, fix, docs`; every refusal in `universe/`, `vfs/`, `effects/compiler.py` and `token_spec.py` goes through it; `validate` returns a list and never raises | The form renders diagnostics or it renders tracebacks; today 145 refusals bypass the shape and the indistinguishability message tells the author to alter behaviour |
| 4 | One canonical semantic form, hashed once: `universe_hash` over the artifact minus provenance and prose, with named sub-hashes as subtrees of the same form; delete the pydantic-dump family hashes, `COMPILED_SCHEMA_VERSION` and the raw-bytes cache key | Verified today: editing a meter `description` refuses resume (section 4); three hashing functions cannot agree on what identity is |
| 5 | Family models replace the DTO-per-file layer: delete the wrapper classes, `from_yaml` and `base.py`; a consumer lint fails CI on any family field with zero readers outside `config/`; a `compile_pack` API with JSON Schema, symbols-by-context and a layout `inspect` is the front-end contract | Required-and-inert fields are what no-defaults produces without a consumer rule; the form needs schemas and scope-aware completion the resolver already knows |

The risk document's 80-95% reopen estimate is a measurement, not a guess: six `fix(vfs)` commits
today (`7b5304f3`, `7b0f6b9b`, `a19217a1`, `995a1e21`, `5290a0fb`, `adb76a71`) each touched
`src/townlet/universe/` or `src/townlet/config/`, two of them five files apiece. A VFS change is
a compiler change because the compiler rebuilds VFS's name table five times over.

Do 1 first: it is one afternoon, it is deletable, and every later change assumes the compiler sees
the whole program. Do 2 before VFS change 2 lands (they are the same resolver) and before VFS WP12
writes shape proofs. Do 3 with 2, because the collector is where the single `check` pass reports.
Do 4 after VFS change 3, which is the last planned hash move. Do 5 last; it is the largest edit by
file count and the smallest by risk.

How the compiler changes serve the VFS changes:

| VFS change | what the compiler must become |
|---|---|
| 1 independent worlds, `agents_per_world` | the symbol table carries a world axis per scope and `agents_per_world` from `experiment`; the shape checker proves every expression and write against `[W]`, `[W, A]`, `[W, F]`; `agent_capacity` and `item_capacity` in `token_spec.py:1294-1316` already take the declared count, nothing else does |
| 2 one spelling, one resolver | change 2 here is that resolver; the five builders (`compilers/vfs.py:109-126, 195-221`, `compilers/effects.py:18-53`, `vfs/vtc.py:421-441`, `vfs/profiles.py:339-384`) are deleted, not merged |
| 3 meters folded into VFS | `MeterConfig`, `CascadeConfig`, `ModulationConfig`, the `bars` and `environment` families, `compile_meter_declarations`, `build_meter_metadata`, `OptimizationCompiler` and nine `ErrorCode` members (`METER_VOCAB_MISMATCH`, `CASCADE_*`, `MODULATION_*`, `AFFORDANCE_INVALID_METER`) go; `symbol_table.meters` goes; the `meter` token type leaves the roster and moves `token_type_schema_hash` once |
| 4 nine-field declaration | `_variable_to_definition` (`compilers/vfs.py:83-107`) becomes a copy; `describe_variable` loses `semantic_type` and gains dynamics; `_validate_compiled_policy_coherence` (`compiled.py:697-757`) loses the `readable_by`/`writable_by`/`exposed_to` legs |
| 5 synchronous dataflow, `prev`, events | the symbol table gains an event vocabulary (`did`, `started`, `completed`) derived from actions and affordances; the lowering pass topologically sorts expressions with `prev` as the only back-edge; the transition schedule becomes derived from declarations, and `vfs/transition_schedule.py:219-260`'s nine hand-ordered program families shrink to the ones writes still need |

What should not change: the declaration store (discovery, merge, both-origin collisions, the
clock reference); the source map and its fallback lookup; the error-code registry and the stage
enum as the only authorities for their strings; the collector's collect-then-raise within a
phase; the token spec, its coherence re-derivation on load, and the transfer-hash result; the
checkpoint gate's "no `is not None` escape" discipline; fail-loud cache writes. Section 8 says why.

## 1. Pipeline shape

What runs (`compiler.py:84-264`): discover (`DeclarationStore.discover`), validate the primary
level by directory listing, cache probe, parse DTOs (`RawConfigsV21.from_declarations`), limits,
semantics, symbol table, resolve, presentation resolve, static write targets, `SHARED` (VFS
profiles, effects catalog), `LEVELS` (per level: actions, meter and affordance metadata, spawn
predicates, optimization tensors, runtime variables, token spec, VTC schedule, nine hashes), emit.
`stages.py` numbers nine stages 0 to 8; `COMPILER.md` §2 and `CLAUDE.md` say seven; the error
registry groups codes under stage comments 0 to 7. Three counts for one pipeline is the first
sign the decomposition is a label, not a structure.

Is it the right decomposition? No. The stages are named for what a pre-VFS compiler did to
files; the post-pivot surface is one symbol table of entities (variables, affordances, actions,
items, effects, events) each carrying programs (expressions, command lists, writes), from which
four products are derived (token spec, transition schedule, action table, reward program) and
two run configurations are passed through (brain, training). For that surface a stage is one of
three things: a front end that builds the symbol table, a checker that proves every reference,
type and shape against it, or a lowering pass that produces a product. Nothing else earns a stage.

### One authored fact, several checks

| fact | checked at | notes |
|---|---|---|
| meter vocabulary equal across `environment` and `bars` | `semantics.py:206` (`METER_VOCAB_MISMATCH`), `compilers/observation.py:126-134` (`ValueError`), `compilers/metadata.py:43-46` (docstring relies on it) | second site is a bare raise with no location |
| cascade endpoints name meters | `semantics.py:176`, `references.py:305-313`, `compilers/optimization.py:33-55`, `vfs/vtc.py` cascade compile | four sites, three codes |
| modulation references | `semantics.py:168`, `semantics.py:249-255`, `compilers/optimization.py:60-98` | three sites, four codes |
| `day_length` present when temporal is active | `declarations.py:504-588` (`CLOCK_REFERENCE`), `semantics.py:66-77`, `compilers/metadata.py:94-112` (`UAC_META_DAY_LENGTH`) | the third is unreachable after the first two |
| `drive` declared per level | `declarations.py:459` (`_require_families`), `semantics.py:310-336` (`LEVEL_DRIVE_*`) | second is unreachable: `CurriculumLevel.drive` is non-optional |
| primary level exists | `compiler.py:653-664` (directory listing, admits files), `semantics.py:18-24` (after parse) | two semantics, both `ValueError` (F8) |
| affordance `modify` target exists | `semantics.py:279-287` (`target.bar.` by spelling), `references.py:324-330` (`vfs.`/`target.vfs.`/`self.vfs.` by last segment), then the real check at runtime in `affordance_engine.py:112-132` | compile checks a shadow of the runtime check |
| normalization present at exposure | `variables_config.py` validators, `token_spec.py:890-930` (`ValueError`) | second site is the one with the good message and no location |
| grid capacity | `semantics.py:300-307` (`enabled_affordances + population.size`), `vectorized_env.py:1600` (`len(affordances) + num_agents`) | two formulas |

Every duplicate above has the same cause: each validator rebuilds its own name sets from the raw
DTOs (`env_meter_names`, `meter_lookup`, `bar_schema`, `vfs_variable_ids`) instead of asking the
symbol table, and the symbol table (`symbol_table.py:17-76`) is a bag of seven dicts with no
scope, no shape, no world axis and no programs. It is consulted by `references.py` and by nothing
after it.

### Compilation that happens outside the compiler

| program | parsed and type-checked where | when |
|---|---|---|
| effect definitions | `effects/catalog.py:104` via `compilers/effects.py:66` | compile |
| VFS profile expressions | `vfs/profiles.py:270` via `compilers/vfs.py:56-74` | compile |
| VTC writes, rules, cascades | `vfs/vtc.py` (eight `ExpressionParser()` sites) via `transition_schedule.py:219` | compile |
| item spawn predicates | `compilers/vfs.py:159-193` | compile, against a schema the runtime does not serve (F6) |
| affordance interaction commands | `environment/affordance_engine.py:112-132` | environment construction |
| item hooks (`on_pickup`, `on_use`, ...) | `items/manager.py:92-110` | `ItemManager` construction |

The last two are the structural root of the synthesis's dominant defect. The artifact carries
`effects_schema` as a `dict[str, str]` (`compiled.py`, `vectorized_env.py:215-217`) precisely so
that a second compiler can run at runtime. A pack whose affordance program is ill-typed compiles,
caches, and fails when `DemoRunner` builds the environment, with no code, no location and no
stage. Section 5 recommends the fix.

### Five schemas for one symbol table

`compilers/vfs.py:109-126` (`bar.`, `vfs.`, `self.vfs.`, `target.vfs.`), `compilers/vfs.py:195-221`
(`env.`, `temporal.*`, `vfs.`, `agent.vfs.`), `compilers/effects.py:18-53` (`bar.`, `target.bar.`,
`vfs.`, `target.vfs.`, `global.vfs.`, `self.vfs.`, `intensity`, `elapsed_ticks`),
`vfs/vtc.py:421-441` (bare and `bar.`), `vfs/profiles.py:339-384` (bare, `bar.`). The VFS review's
change 2 deletes the spellings; the compiler side is that all five builders go and one
`for_context` call remains. That is not a merge; each builder is deleted when its last caller
takes the resolver.

### The post-pivot shape

```text
discover ──> symbol table ──> check ──> lower ──> canonical form ──> emit
 (store)   (entities, scopes,  (one      (token spec,  (one encoder,   (artifact,
            world axis,         pass,     schedule,     one hash,       cache,
            programs, events)   one       programs,     sub-hashes)     diagnostics)
                                collector) action table)
```

Three properties the current pipeline lacks and this one has by construction: every reference
is resolved exactly once, in `check`, against the same table every lowering pass reads; a
lowering pass cannot refuse an authored fact, so a refusal in `lower` is a compiler bug and may
raise singly; and the artifact is the canonical form, so identity (section 4) and inspection
(section 6) are projections of one object.

### Migration in deletable steps

1. Move the two runtime `CommandCompiler` sites into `LEVELS`; carry compiled affordance and item
   programs on the artifact the way `compiled_effect_catalog` already is; add an import-linter
   rule that only `townlet.universe` imports `ExpressionParser`, `TypeChecker`, `CommandCompiler`.
2. Add `ExpressionSchema.for_context(kind)` on the symbol table; point the five builders at it
   one at a time; delete each builder when it is a pass-through.
3. Give the symbol table scope, type, shape and world axis per entity; move the name-set
   construction out of `limits.py`, `semantics.py`, `references.py`, `static_access.py` into it.
4. Merge the four validators into `check(symbols) -> Diagnostics`; delete the later duplicate of
   every row in the table above (the `ValueError` in `observation.py:126-134`,
   `UAC_META_DAY_LENGTH`, `UAC_OPT_*`, `LEVEL_DRIVE_*`, the second primary-level check).
5. Strip validation from the sub-compilers; rename them `lower_tokens`, `lower_schedule`,
   `lower_actions`, `lower_programs`; delete `MetadataCompiler`'s pass-through fields.
6. Renumber: `CompilationStage` becomes `DISCOVER, SYMBOLS, CHECK, LOWER, EMIT`; `COMPILER.md` §2
   is rewritten against the enum, not beside it.

Each step leaves the suite green and deletes code; none needs a flag.

## 2. The DTO layer and no-defaults

What it is: 22 modules, about 400 `Field(...)` declarations, `extra="forbid"` on every model
(`RecordingConfig` is fixed in the working tree). The store maps each family to one model
(`raw_configs_v21.py:107-116, 150-158`), which is the right boundary: a family is a declaration
with an identity, and a pydantic model is a fine parser for it. Three things are wrong with the
layer, none of them "pydantic".

First, the file is still visible in the types. `ExperimentConfig.experiment.experiment_name`,
`StratumConfig.stratum.substrate`, `EnvironmentConfig.environment.meters`,
`CurriculumConfig.curriculum.active_vision` are double-wrapped because the wrapper class was the
file's root key; the store adds and strips that key (`declarations.py:parse`, `wrapped=True`) so
the wrapper classes are dead weight every consumer pays for. Six `from_yaml` classmethods and
`config/base.py` (`load_yaml_section`, `format_validation_error` citing a `configs/templates/`
that does not exist) have zero callers outside `config/`. They are filename readers that
survived the declaration store.

Second, prose is behavioural. `MeterConfig.description`, `CascadeConfig.description`,
`ModulationConfig.description`, `ExperimentMetadata.description` are required, which is
defensible, and hashed into `environment_hash` and `experiment_hash`, which is not (section 4).
CLAUDE.md exempts "metadata (descriptions)" from no-defaults; the compiler does not exempt them
from identity. Either a behavioural family has no prose fields (presentation owns descriptions,
and the artifact now carries presentation) or the canonical form excludes them. I recommend the
first: one place for every human-readable string, and the form has one panel for them.

Third, "required" has no consumer rule. WP3 is deleting `curriculum_levels`, `cues`,
`category`, `evaluation.*`, `keep_last`, `author`, `created`, `tags` (working tree). The sole
consumer of `curriculum_levels` in the whole tree was `scripts/validate_compiler_cli.py`, which
used it to pick the level to validate; the in-flight WP3 rewrote the script to take the first
discovered level directory, and `validate_compiler_cli.py configs/simple` passes in the working
tree. That is the pattern in one line: a field required of every author so that one script
could choose a level, which discovery already knew. No-defaults asks "is it explicit"; nobody
asks "is it read".

Recommendation: a consumer lint beside `no_defaults_lint.py`. For every field on every family
model, walk `src/townlet` with `ast` for attribute access by that name (qualified by the model
class when the name is ambiguous, which `ast` can do for annotated parameters and for
`level.training.x` chains); zero readers outside `config/` fails the Lint job; the whitelist is
empty by rule and a field that needs one is a field to delete. Run it against the artifact's
`to_dict` too: a serialized field nobody deserializes is the same defect. Cost: one script, S.
The DTOs themselves: delete the wrappers, `from_yaml`, `base.py`; rename `*V2Config`,
`*_v21` and `RawConfigsV21` (the `v2.1` suffix is a pre-pivot version of a format that no longer
has versions); make `RawConfigsV21`/`CurriculumLevel` the store's typed product directly.

The no-defaults whitelist is also wider than the principle. `.defaults-whitelist.txt:104-110,
158, 179, 223-226` carry blanket `*` waivers on `compiler.py`, `compiled.py`, `compilers/**`,
`raw_configs_v21.py`, `__main__.py`, `validation/limits.py`, `validation/references.py`. The
compiler is where a hidden default becomes a hidden world fact (F6's `cost=0.0` lived under one
of these); narrow them to structural entries and delete the seven entries naming files that no
longer exist (F11).

## 3. Refusals as the new-user interface

Audit numbers (grep, this tree): 67 codes in `error_codes.py`; 111 `errors.add`/`CompilationMessage`
sites in `universe/`; 145 bare `raise ValueError|TypeError|RuntimeError` in `universe/`, 84 of
them in `token_spec.py`; 83 more in `vfs/{profiles,vtc,transition_schedule}.py`; 41 raises in
`effects/compiler.py`. `compile()` converts exactly four exception types
(`EffectCompileError`, `CircularDependencyError`, `TypeCheckError`, `VTCWriteRefusalError`,
`compiler.py:178-195, 234-240, 435-446`); every `ValueError` from `build_token_spec`,
`compile_meter_declarations`, `validate_item_profile_bindings`, `build_universe_metadata` and the
primary-level check propagates raw, and `__main__.py:217-227` catches only `CompilationError`
and `FileNotFoundError`. By site count the structured path is the minority.

Location fidelity where the shape is used: `VFS_PROFILE_COMPILE` locates at the whole
`variables` declaration (`compiler.py:193`), `VFS_LEVEL_COMPILE` at the `levels` directory
(`compiler.py:238`), `VISION_INCOMPATIBLE` and `TEMPORAL_DAY_LENGTH_MISSING` at the curriculum
family, `SUBSTRATE_ACTION_*` at the actions family, `AFFORDANCE_INVALID_METER` at the affordance
entity but not the offending command. The source map can answer at key depth
(`levels/L/affordances:EAT.interactions.on_start[0].modify`); most callers ask it at family depth.

Voice: three. Terse (`Cascade references unknown source meter 'x'.`), structured
(`Invalid cascade entry...\n  Unknown source meter: ...\n  Valid meters: ...`, `optimization.py:38-44`),
and lecture (`Rule: under permutation-invariant pooling two such tokens alias for every weight
setting (spec §1)`, `token_spec.py:1107-1112`). The fix is named in a minority (`rename one of
them`, `Pass --no-cache`, the two YAML hints); it is wrong in one (indistinguishability tells the
author to change `semantic_type`, `lifetime`, range or initial value to satisfy the compiler,
hamlet-2aca57c0f0); `add_hint` has four callers, all in the vocabulary-mismatch block; no message
carries a docs anchor. The stage label in every message is an internal number that moved twice
this year.

The contract a form can render, and how far `CompilationMessage` (`errors.py:10-25`) is from it:

| field | today | needed |
|---|---|---|
| `code` | yes, closed enum | keep; one registry for `universe/`, `vfs/`, `effects/`, `token_spec.py` |
| `severity` | no; `add_warning` has zero callers, advisories are `logger.warning` | `error`, `warning`, `advisory`; the mean-census note is the first advisory |
| `location` | `file:line` string, often family-deep | `file`, `line`, `column`, and the declaration path the source map already keys on; a form has no files |
| `what` | `message`, three voices | one sentence, the entity named first |
| `why` | sometimes folded into `message` | one sentence, optional |
| `fix` | `hints` on the error, not the message, four callers | required on every author-facing code; the registry holds a template per code so a code without a fix cannot be added |
| `docs` | none | an anchor per code into `docs/config-schemas/`, held in the registry |
| `stage` | internal number in the string | drop from the author-facing text; keep in the record |

The registry is the lever. Make `ErrorCode` carry `(severity, fix_template, docs_anchor)` and
make a code without them a test failure (`test_error_codes.py` exists); then every raise site
is a `code.at(location, **fields)` call, and the three voices collapse because the template owns
the voice. `token_spec.py` needs a sink: pass a `Diagnostics` collector into `build_token_spec`
and have its refusals be `collector.add(code, entity=var.id)`, with the compiler resolving
`entity` to a location through the source map. The same for `vfs/profiles.py` and
`effects/compiler.py`: they already raise typed errors with an `effect_id` or variable name; the
compiler should map, not wrap `str(exc)`.

Collect across stages? Yes across the front end and the `check` pass; no across lowering. Today
each of the five validators raises at its own end, so a pack with a limits error and a semantics
error shows one, and a token-spec refusal shows after everything else passed. After section 1's
merge there is one collector for `check`; a `validate` call returns every author-facing
diagnostic at once, and the only single raises left are lowering bugs, which are the compiler's
fault and should say so. The rule for the CLI and the API: an author never sees a traceback from
`validate`; if one escapes, that is a P1 in the compiler regardless of exit code.

## 4. Identity, hashes and the artifact

Inventory at this tree: seven top-level hashes (`brain`, `pack_brain`, `experiment`, `stratum`,
`environment`, `actions`, nullable `items`) and twelve per level (`token_type_schema`, `layout`,
`action_schema`, `transition_graph`, `vfs`, `observation_schema`, `variable_schema`, `drive`,
`curriculum`, `bars`, `affordances`, `training`), nineteen in all, plus `config_hash` and
`provenance_id`. They come from three hashing functions with three notions of canonical form:
`_compute_pydantic_hash` (`model_dump_json` of the DTO, so field order and prose included),
`vfs/schema_hashes._hash_payload` (sorted-key JSON over a hand-projected dict),
`compute_brain_hash`. The gate (`checkpoint_utils.py:224-455`) hard-compares twelve, one of the
two token hashes by architecture, `action_dim` and `primary_level`; `DEMO_CHECKPOINT_KEYS` has 31
members. `COMPILED_SCHEMA_VERSION` is `1.34` in the working tree; its history comment
(`compiled.py:121-137`) records four bumps in the last day (1.31, 1.32, 1.33 landed, 1.34 in
the tree) and every bump reads "the cache key does not move for an unchanged pack, so the bump
is what refuses it", which is a confession that the cache key is the wrong key.

Two probes on scratch copies of `configs/simple` (`compile(use_cache=False)`, hashes compared):

| edit | moved | gated? |
|---|---|---|
| one meter `description` in `environment.yaml` | `environment_hash`, `config_hash` | yes, since `dda94ac5`: a doc edit refuses resume |
| `experiment.metadata.description` | `experiment_hash`, `config_hash` | yes |
| rename `environment.yaml` to `world.yaml` | `config_hash` only | no (correct) |

The round-1 refutation that "content hashes do not include descriptions" held for `bars` and
`affordances` and does not hold for `environment` and `experiment`, because it depends on which
DTO happens to carry prose. That is the defect in one sentence: identity is a property of the DTO
class layout, not of the world.

Is there a simpler model? Yes, and the artifact is most of it already. Define the canonical
semantic form as the artifact's `to_dict` with provenance (`compiled_at`, `compiler_git_sha`,
`config_mtime`, `experiment_dir`, versions), transport (`config_hash`) and prose (descriptions,
presentation) removed, serialized by one canonical encoder (sorted keys, no floats-as-strings,
tuples as lists). Hash that once: `universe_hash`. Every other hash is the same encoder over a
named subtree of the same dict:

| hash | subtree | who compares it |
|---|---|---|
| `universe_hash` | everything | resume: equal means continue |
| `world_hash` | symbol table, programs, schedule, action table, substrate | resume diagnostics: "the world changed" |
| `observation_hash` (today `layout_hash`) | token spec | flat nets |
| `token_type_schema_hash` | type schemas only | token nets; the transfer contract, unchanged |
| `action_hash` | action table | both |
| `brain_hash`, `drive_hash`, `training_hash` | their subtrees | resume diagnostics |

Because every sub-hash is a subtree of one form, a mismatch message is a diff of subtrees, and
`gate_cov.py`'s question ("does this edit move a compared hash") has a structural answer: an edit
moves `universe_hash` if and only if it changes the canonical form, which is the definition of
semantic. The nineteen fields, `_compute_pydantic_hash`, the hand-projected dicts in
`schema_hashes.py:160-224` and the per-family stamps in `DEMO_CHECKPOINT_KEYS` go.

What should move an author-visible hash: any change to a declared parameter, program text,
ordering of an authored array, or the roster of entities. What should not: a file rename or
move, a comment, a description, a presentation entry, YAML key order, a `---` split, the
compiler's own version. Today a description moves two gated hashes and a reordered affordance
list correctly moves `layout_hash`; under the canonical form both answers fall out without a
rule per field.

`COMPILED_SCHEMA_VERSION` should not exist. The loader already re-derives the token bindings and
contexts from the persisted declarations and refuses disagreement (`compiled.py:759-800`); that
self-validation is the real schema check, and the hand-bumped integer is a belt over it that
must be remembered on every artifact edit (it was, four times, in one day). Replace it with a
`compiler_hash` in provenance: the hash of the compiler's own source (`townlet.universe`,
`townlet.vfs`, `townlet.effects.compiler`, `townlet.world.expression`) computed at import. The
cache key becomes `(canonical hash of the declaration store, compiler_hash)`: a comment edit does
not recompile, a compiler edit always does, mtime and the second YAML parse in
`_compute_config_hash` (`compiler.py:713-724`, `_normalize_yaml` at 601-631 re-reads every file
`DeclarationStore` already parsed) are deleted, and C11's path- and cwd-blindness goes with the
`git rev-parse` call. Checkpoints stamp `universe_hash` and `compiler_hash`; the gate compares
the first and reports the second.

## 5. The compile/runtime seam

The evidence is in section 1's second table: of three command-bearing surfaces, one is compiled
by the compiler and two at runtime, against a schema dict the artifact carries for that purpose;
the spawn predicate is compiled against a fifth schema the runtime context does not serve
(`items/manager.py:596-619` builds `ExprExecutionContext(bars, vfs, temporal)` while the compile
schema advertises `env.X`, `agent.vfs.X`, `temporal.*`); and the phase graph listed phases
`step()` never ran until `7b0f6b9b`. Three mechanisms were asked about:

| mechanism | what it closes | what it leaves open | cost |
|---|---|---|---|
| runtime consumes the compiled schema | spelling drift between compile and runtime name tables | two compilers still exist; a program the compiler never saw is still compiled late; schedules can still name phases nothing runs | S, and it is the status quo for effects |
| conformance test: every compiled program executes once | detects dead programs, dead phases, context mismatches | detects after the fact; does not stop the next one; needs the compiler to enumerate "every program", which it cannot while two are compiled elsewhere | S to write, permanent to maintain |
| compiler emits executable closures | the runtime cannot reinterpret | closures do not serialize, so the cache and the hash cannot cover them; determinism across compiler versions is unprovable; the oracle cannot diff them | M, and it breaks section 4 |

Recommend the first table's missing row: the compiler compiles every program to the serializable
IR it already uses for effects (parsed AST plus resolved bindings, persisted the way
`compiled_effect_catalog` is), the runtime constructs no `ExpressionParser`, `TypeChecker` or
`CommandCompiler`, and the artifact carries no schema dicts (`effects_schema`,
`vfs_expression_schema` are deleted). Enforce it with an import rule, not a convention. Then add
the conformance test as the guard that the enumeration is complete: for each shipped pack, build
the environment from the artifact, run `reset` and K steps with a policy that exercises every
action, and assert that every entry in the artifact's program table was executed at least once,
naming the dead ones. The test is possible only after the move, because only then does the
artifact know what "every program" is.

Cost: moving two call sites and serializing two program tables, M; the spawn context rewrite so
the evaluator is built from the compiled binding rather than a hand-assembled dict, S; the import
rule, S; the conformance test, S plus one fixture pack per program family it must reach. What it
buys: "compiles green, never executes" becomes a compiler bug class with a test, instead of a
property of the architecture; the VFS review's spelling change lands in one place; and the
runtime's `vectorized_env.py` loses the branch at 215-217 and the schema plumbing through
`affordance_engine.py` and `items/manager.py`.

## 6. The front-end contract

Today: `python -m townlet.universe {compile, inspect, validate}`. `validate` is `compile` with
the cache off and the result discarded, so it stops at the first stage that raises and prints a
traceback for every non-`CompilationError` (F8). `inspect --format json` returns hashes, census
and advisories but no row layout, slot bindings or filler refs (hamlet-53bce4af41, still live
after narrowing). There is no Python entry point that returns diagnostics: `compile()` raises.
The only in-tree consumers are `demo/runner.py:153`, `demo/live_inference.py:100` and
`oracle/driver.py:95`; `frontend/src` has no compile or validate call anywhere (it reads the
simulation socket). `scripts/validate_compiler_cli.py` is the single CI consumer and it drives
the CLI by subprocess per pack.

What a form-based editor needs, and what exists:

| surface | input | output | today |
|---|---|---|---|
| `validate(pack)` | directory or an in-memory declaration store | every diagnostic (section 3 record), never raises | CLI only; raises; stops early |
| `inspect(pack or artifact)` | path | JSON: `row_layout`, census, slot bindings with filler refs, symbol table (id, scope, type, shape, declared-at), transition schedule (phase, rules, origins), action table, hashes, provenance | hashes and census only |
| `symbols(pack, context)` | context kind (`agent_row`, `world`, `item`, `pair`, `spawn`, `reward`) | the ids and types the resolver admits there | does not exist; the five schema builders each know a different answer |
| `schema(family)` | family name | JSON Schema from the family model (`model_json_schema()` is free) | does not exist; the models have it |
| `compile(pack, level)` | path | artifact, or diagnostics | exists, raises |
| incremental recompile | one declaration | diagnostics for that change | not needed: a full compile is about one second on `default_curriculum`; a form can revalidate the pack per edit. Say so and do not build it |

The missing piece that none of the others can substitute for is `location` as a declaration
path. A form does not have files; it has a family, an entity and a field. The source map is
already keyed that way (`declarations.py:_record_sources`,
`levels/L0/affordances:EAT.costs.money`); the diagnostic record should carry both the key path
and the `file:line` it resolves to, and the form binds errors to fields by the key path.

One Python function underneath: `compile_pack(store_or_path, level) -> CompileResult` with
`artifact: CompiledUniverse | None` and `diagnostics: list[Diagnostic]`; the CLI is a printer
over it with `--format json` on every subcommand; a web server is a thin HTTP wrapper over the
same function. Nothing in `__main__.py` should know how to compile.

## 7. What to delete, add, rename

Deletions first. Cost is to a practitioner, benefit is to a new user.

| # | action | why | cost | benefit |
|---|---|---|---|---|
| D1 | delete the runtime `CommandCompiler` sites (`affordance_engine.py:112-132`, `items/manager.py:92-110`) and the `effects_schema`/`vfs_expression_schema` artifact fields; compile in `LEVELS` | section 5 | none; same programs, earlier errors | an ill-typed affordance refuses at `validate`, with a location |
| D2 | delete four of the five schema builders once `for_context` exists | section 1 | none | one spelling (VFS 2) |
| D3 | delete the duplicate checks named in section 1's first table and the dead `LEVEL_DRIVE_*`, `UAC_META_DAY_LENGTH` codes | one fact, one refusal | none | one message per mistake |
| D4 | delete the 145 bare raises' author-facing subset by routing through the registry (section 3) | tracebacks are not diagnostics | none | every refusal has code, location, fix |
| D5 | delete `_compute_pydantic_hash`, the twelve per-family hashes, the per-family checkpoint stamps, `COMPILED_SCHEMA_VERSION`, `_normalize_yaml`, `_compute_config_mtime`, `_get_git_sha` | section 4 | one regeneration of every checkpoint, free pre-release | resume refuses on world changes and nothing else |
| D6 | delete the wrapper DTO classes, six `from_yaml`, `config/base.py`, `loaders/v21.py` (test-only) | dead filename readers | none | models are the families |
| D7 | delete prose fields from behavioural families (`description` on meters, cascades, modulations, experiment metadata); presentation owns them | section 2 | moving strings to `presentation` in every pack, mechanical | descriptions never move identity |
| D8 | delete blanket `*` whitelist entries on the compiler and the seven entries naming deleted files | section 2 | none | no-defaults holds in the compiler |
| D9 | delete `EFFECT_OBSERVATION_SLOTS`, `SymbolTable` zero-caller methods, `SourceMap.bulk_record`, `to_level`, `add_warning` (F11) | residue | none | smaller surface |
| A1 | add `ExpressionSchema.for_context` on a symbol table that carries scope, type, shape, world axis, programs and events | section 1; VFS 1, 2, 5 | none | completion and refusals agree |
| A2 | add the diagnostic record and the registry triple `(severity, fix_template, docs_anchor)`; a code without them fails `test_error_codes.py` | section 3 | none | every refusal names the fix |
| A3 | add `compile_pack` returning diagnostics; `validate` never raises; JSON on every CLI subcommand | section 6 | none | the form's one call |
| A4 | add `inspect` layout, symbols, schedule; `symbols(context)`; `schema(family)` | section 6 | none | "where did my variable land" without Python |
| A5 | add the canonical form, `universe_hash`, subtree sub-hashes, `compiler_hash`, cache keyed on them | section 4 | none | identity means world identity |
| A6 | add the consumer lint to the Lint job | section 2 | a field with no reader must be deleted, which is the point | no inert required fields |
| A7 | add the conformance test over every shipped pack's program table | section 5 | one fixture pack per program family | dead programs are test failures |
| R1 | rename `CompilationStage` to `DISCOVER, SYMBOLS, CHECK, LOWER, EMIT`; drop the number from messages | section 1 | none | docs and code agree |
| R2 | rename `*V2Config`, `*_v21`, `RawConfigsV21` to family names | pre-pivot version suffix on a format that no longer versions | find-and-replace | one vocabulary |
| R3 | rename `compilers/*` to `lower_*` once they validate nothing | section 1 | none | the name says what runs |

## 8. What is right and should not change

- The declaration store. Discovery by content, scope by directory, `files are transport`,
  catalog merge in sorted path order, duplicate identities refused with both `file:line`,
  the `period_of` reference resolved before the DTO sees it. Round 1 could not break it; it is
  the piece a form writes to and should be the compiler's only front end.
- The source map and `locate`'s fallback through shorter keys. It already answers at field depth;
  the fix in section 3 is to ask it at that depth, not to replace it.
- The collector's collect-then-raise within a phase, the closed `ErrorCode` enum, and
  `CompilationStage` as the one authority for stage strings. The shape is right; it is
  under-used, not wrong.
- The token spec: fixed payload widths, per-universe capacities, identity by declared payload,
  presence-led rows, the loader's re-derivation of bindings and contexts from persisted
  declarations, and the transfer-hash result (`token_type_schema_hash` identical across 2-D,
  3-D, N-D, continuous and aspatial at HEAD). Section 4 keeps that hash as a named subtree.
- The checkpoint gate's discipline: every leg a hard refusal, no `is not None` escape, a stamped
  `None` is a value. Section 4 reduces what it compares, not how.
- Fail-loud cache writes (`compiler.py:575-589`) and the mislabelled-artifact guard outside the
  defensive read.
- `extra="forbid"` and no defaults in the parse layer; section 2 adds a consumer rule beside
  them, it does not weaken them.
- Required `primary_level` and one artifact per level.
- The in-flight WP3 and WP4 (dead fields, `extra="forbid"` on recording, presentation on the
  artifact, the item-capacity rule) are consistent with everything above and should land as
  written; WP5's `tag` discriminator should wait for VFS change 3, which gives the descriptor
  declared dynamics and may make the escape hatch unnecessary; WP6's cache work and VFS WP10
  (expression text into `vfs_hash`) are both absorbed by A5 once programs enter the canonical
  form, so neither should be done as a separate change if A5 is scheduled.
