# Universe compiler — gap analysis and remediation plan

Scope: `src/townlet/universe/` (compiler, declarations, compiled artifact, validation, emit,
cache, CLI, `dto/token_spec.py`), `src/townlet/config/` as the parse stage, and the checkpoint
identity gate in `training/checkpoint_utils.py` that consumes compiler hashes.
Evidence: `review-2026-10-24/findings_compiler.md`, scripts `review-2026-10-24/compiler/`.

## What the subsystem promises

README: declarations are discovered by content, filenames are transport; duplicates and unknown
families refuse with `file:line`; the artifact carries hash-based identity for every declaration
family; the cache recompiles on any input change; `extra="forbid"` on every DTO so stray keys
fail at parse; resume and serving check identity before loading weights.

## What it does

Discovery, merge and refusal are solid. The reviewer tested nested, deleted and mtime-backdated
files, duplicates across files, missing families, unknown keys and the clock reference; all
refuse or recompile correctly with locations. The msgpack round trip preserves every hash and
field except one.

That one is a level's `items_appearance`, which the artifact never serializes, so every cached
compile returns an item-less world. The identity story is narrower than written: five pack-level
hashes are computed and compared by nobody, so stratum edits that change movement semantics
resume silently. The parse stage is `extra="forbid"` everywhere but one DTO, and no-defaults has
produced a layer of required fields with no consumer.

## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_compiler.md`
(F-numbers) and filigree ids.

| id | sev | gap | source |
|---|---|---|---|
| C1 | P1 | Artifact never serializes `items_appearance`; cached compiles run item-less worlds | F1 |
| C2 | P1 | Five pack hashes plus `config_hash` stamped and compared by nobody; stratum edits resume silently | F2, hamlet-2dde1015fe |
| C3 | P2 | Item catalog nullified on `max_items_per_agent == 0` or `max_items_in_world == 0`, misleading refusal | F3, hamlet-45f501e15b |
| C4 | P2 | Required fields with zero consumers across experiment, environment, training and DAC DTOs; `capability_config.py` whole | F4 |
| C5 | P2 | `RecordingConfig` is `extra="allow"`; typos enter `training_hash` | F5 |
| C6 | P2 | `metadata.py:72` branches on `"money"`; fills dead fields | F6 |
| C7 | P2 | `presentation` discovered by content at compile, read by filename at runtime | F7 |
| C8 | P2 | No discriminator for parameter-identical variables; affordances and effects never checked | hamlet-2aca57c0f0, effects F15 |
| C9 | P2 | `inspect --format json` omits row layout and offsets | hamlet-53bce4af41 |
| C10 | P3 | CLI refusals as tracebacks | F8 |
| C11 | P3 | Cache fingerprint path- and cwd-blind; `inspect` never checks freshness | F9 |
| C12 | P3 | Effects DTO residual defaults | F10 |
| C13 | P3 | Residue: dead constant, dead whitelist entries, un-compilable fixture, dead script path, zero-caller methods | F11 |
| C14 | P3 | Two wall-clock ratio asserts in the default selection | hamlet-f9090ec3e8 |

## Remediation plan

### WP1 — Serialize `items_appearance` (C1)

Add `items_appearance` to the per-level block in `to_dict` and `from_dict`, including the
compiled spawn-predicate ASTs (or re-run `compile_item_spawn_conditions` on load). Add it to the
required level fields so an older artifact refuses. Bump the artifact schema.

Verification: `roundtrip_runtime.py` becomes a test: fresh and cache-served compiles of
`configs/test/items_smoke` spawn the same items after reset. Extend
`test_compiled_universe_round_trip_serialization` to compare every `LevelMetadata` field, not
just hashes. Size: S. **Do this first; the items plan is blind until it lands.**

### WP2 — Stamp and compare pack hashes (C2)

The gate compares `vfs_hash`, `action_schema_hash`, `observation_schema_hash`, `action_count`,
`meter_count`, `drive_hash`. Add `stratum_hash`, `environment_hash`, `actions_hash`,
`experiment_hash` and `items_hash` to `DEMO_CHECKPOINT_KEYS`, to `attach_universe_metadata`, and
to `assert_checkpoint_identity` as hard refusals. `items_hash` is nullable; refuse on
`None`-versus-value as a change like any other. Delete `config_hash` if it stays uncompared, or
compare it too; a stamped-never-compared field is a lie in the checkpoint.

Verification: `gate_cov.py` becomes a test over scratch copies of `configs/simple`: every edit the
script makes must move at least one compared hash, and `assert_checkpoint_identity` must refuse.
Size: S.

### WP3 — Delete dead required fields (C4, C5, C6, C12)

For each field in C4: delete it from the DTO and from every shipped pack. The three that deserve
a consumer rather than deletion:

- `experiment.curriculum_levels`: cross-validate against discovered `levels/` and refuse a
  mismatch, or delete. Deletion is recommended; discovery is the authority.
- `training_loop.checkpointing.{interval,keep_last}`: DemoRunner has a checkpoint cadence
  somewhere; bind it here or delete the field.
- `IntrinsicConfig.*_config`: belongs to the items plan (DAC WP2); delete here only after that
  decision.

`RecordingConfig` gets `extra="forbid"` or is deleted with the recording subsystem. The
`metadata.py` block loses `cost`, `category`, `description`, `critical`, `observable`; if `cost`
must exist, bind it through the declared `money_bar` role. Effects DTO defaults in C12 become
required or are restructured as a tagged union so one command kind per node is a type, not a
default.

Verification: the `dead_fields` scratch pack must refuse at parse on every field it exercises;
`scripts/no_defaults_lint.py` with an empty whitelist reports nothing in `config/`. Size: M.

### WP4 — One vocabulary for `presentation` (C7) and one rule for item capacity (C3)

Carry the parsed `PresentationConfig` on the artifact, validate meter and affordance references
in resolve, and delete the filename reader in `demo/presentation.py`. For C3, drop the `or`: only
`max_items_in_world + max_items_per_agent × num_agents == 0` means "no item arena", and even then
refuse a declared catalog with a message that says so rather than nullifying it.

Verification: `pres` pack with `display.yaml` loads at runtime; an undeclared meter refuses at
compile. Items copy with `max_items_per_agent: 0` and `max_items_in_world: 10` compiles and spawns.
Size: S.

### WP5 — Identity escape hatch and affordance identity (C8)

Two choices. Either add a declared `tag: str` discriminator to `VariableDeclaration` that enters
`describe_variable` and nothing else, or hold the line that two parameter-identical entities are
one entity and make the refusal message say how to differ. The plan recommends the tag: a designer
who wants two identical hidden counters for two mechanics has a legitimate need and no spelling.
Then run `check_indistinguishability` over affordances and effects using the signatures
`affordance_identity.py` already builds.

Verification: twin-variable scratch pack compiles with distinct tags and refuses without; two
identical affordances refuse. Size: S.

### WP6 — CLI and cache hygiene (C9, C10, C11)

Expose `row_layout()`, slot bindings and filler refs under `inspect --format json`. Catch
`ValueError` in `main()` and print the same `[CODE] file:line - message` shape as
`CompilationError`. Validate `--primary-level` against directories only. Add `experiment_dir` to
the cache fingerprint, resolve the git sha from the package root rather than the cwd, and have
`inspect` check staleness and say so. Verification: `cli_out.txt` cases produce no tracebacks;
`cache_exp.py` cases (a) and (b) produce cache misses. Size: S.

### WP7 — Residue and the timing asserts (C13, C14)

Delete the items in C13. Move the two ratio asserts behind a `perf` marker excluded from the
default selection, or delete them; a timing ratio under coverage is noise. Size: S.

## Docs to correct in the same changes

- `README.md` "Compile, train and inspect": artifact schema version after WP1; the identity gate
  paragraph after WP2 (delete "recorded without being independent checkpoint gates").
- `docs/architecture/COMPILER.md`: the artifact field list; the cache fingerprint inputs.
- `docs/config-schemas/declarations.md`: `presentation` becomes a normal family (WP4).
- `docs/config-schemas/variables.md`: the `tag` field if WP5 adds it.
