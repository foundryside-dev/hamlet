# Compiled actual-roster design handoff

Status: read-only preparation; no implementation, imports, runtime, tests, formatter, Git/index, branches, worktrees, copies, deletion or delegation performed. Only this ignored prose report was written. Root owns serial start after T21 stationarity and all runtime/index/commit/publication gates. Base publication `02d1f614` is root-supplied provenance, not independently inspected Git state.

## Authority and bounded inventory

Read AGENTS.md, T21-DESIGN-HANDOFF.md, T21-DESIGN-RULING.md, T21-test-authoring.md and historical T03 implementation prose. T03 known-1.40 compatibility requirements are explicitly SUPERSEDED by current AGENTS/root no-compat authority. Its recorded original data/digests/history remain evidence to preserve, not a loader-support requirement.

Root's latest component refinement governs over the earlier ruling sentence requiring roster on both OP and EF: pure `resolve_bac_options(options, *, training)` stays roster-free for legitimate RP/PER consumers. New OP `resolve_static_baseline_policy(*, declared_meter_names: tuple[str, ...])` owns the immutable named `.5/shaped/1/exact-tuple` declaration. EF requires `declared_meter_names` and carries the declaration with `effective-run-v2` identity/transport. Factory requires resolved `curriculum_options`, `static_policy`, `device`. The component-refinement append was not present in the ruling file at this read; this paragraph consumes the explicit root dispatch plus current T21 test-authoring prose. Before implementation consume the final producer receipt, not another source file.

Only these three existing implementation/test sources were inspected. The fourth file is reserved and absent; no EF/OP/RP/ENV/runner/helper/fixture source was opened. YAML and prose references are exempt.

| Source | Ceiling | Actual lines | SHA256 |
| --- | ---: | ---: | --- |
| src/townlet/universe/compiler.py | 1200 | 976 | 521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92 |
| src/townlet/universe/compiled.py | 2000 | 1615 | 494f9676c236349f12c875c82dde821a85a3bf5077cae15654c78e8ac1630710 |
| tests/test_townlet/regressions/bac/test_effective_run.py | 500 | 330 | 4529f9074600233081014073a32aa737da10e31e5a148fe91745faf38595eda8 |
| tests/test_townlet/regressions/bac/test_curriculum_compiled_roster.py | 700 | absent/reserved | not applicable |

Actual existing total2921; finite projection4/4400. Production/helper reads cannot expand beyond this inventory without root disposition. No claims about external callers or uninspected owner-test assertions follow from this inventory.

## Actual source APIs and roster authority

Public authored route exists today:

```python
compiled = UniverseCompiler().compile(
    Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False
)
run = compiled.effective_run
selected = compiled.get_level(compiled.metadata.primary_level)
declared_meter_names = tuple(meter.name for meter in selected.bars.meters)
```

The relative pack path above assumes repository cwd; a test should use its file-derived repository root. `UniverseCompiler.compile(experiment_dir: Path, primary_level: str | None = None, use_cache: bool = True)` refuses implicit primary selection. `compile` returns `CompiledUniverse`, not a runner or factory wrapper. `get_level(level_name)` returns actual `CompiledUniverse.LevelMetadata`; `to_level(level_name)` delegates to it. `metadata_for_level` projects metadata but does not reselect this universe's effective run. To witness another selected level, compile with that explicit `primary_level`; do not combine a run for L0 with metadata projected for L1.

Actual selected roster is `selected.bars.meters` in authored list order. Compiler source repeatedly uses `tuple(meter.name for meter in level.bars.meters)` for effect symbols. `_compile_level` builds meter metadata and compiler-owned `meter_declarations` from that level's bars, then persists all three in `LevelMetadata`. It computes `bars_hash` over complete `level.bars.model_dump_json()`. No guessed `bars.bars`, `meter_names()` or loader name is needed. Environment-wide declarations are vocabulary, not selected-level roster authority; never sort names or substitute a fixed standard roster.

Existing smoke L0 and L1 YAML both declare `(energy, health, satiation, hygiene, money, fitness, mood, social)` in that order. A second-level witness must deliberately reorder only one test-owned level YAML to prove selection/order rather than reuse identical rosters and call that proof. Changing authored order may legitimately change other compiled identities; the required assertion is exact roster transport and EF/static-policy binding, not that all other identities stay equal.

`CompiledUniverse.effective_run` is init=False on the frozen dataclass. Its properties `authored_brain_hash`, `authored_identity`, `execution_hash` delegate to that run. `__post_init__` validates nonempty levels/primary membership then invokes `_derive_effective_run`. Compiler stage8 invokes `_derive_effective_run` again with explicit inherited/replacement brain, training, drive and capture origins.

There is exactly one production `resolve_effective_run` call within this bounded source: `compiled.py` `_derive_effective_run`, currently passing brain, selected training, primary_level, origins and selected `drive.intrinsic`. Add required `declared_meter_names=tuple(meter.name for meter in level.bars.meters)` there. Compiler stage8 inherits it through its existing method call; no new factory overload is needed. Three direct calls in `test_effective_run.py` (shadowed base, selected provider activity, inactive ICM preset) must supply that same actual selected tuple.

## Current-only persistence and expected-world validation

Current source native label is `1.41`. Propose new sole native label `1.42`, because its required EFv2 policy/actual-roster semantics differ from the existing `1.41` format. Keep existing complete top-level required fields, including mandatory `effective_run`. Delete `V1_40_COMPILED_UNIVERSE_FIELDS` and both from_dict 1.40 dispatch/derivation branches. `_validate_compiled_schema_version` must accept exactly `COMPILED_SCHEMA_VERSION`, never a pair. Missing version, `1.40`, `1.41`, unknown/future values and missing current view refuse on direct dictionary/native load. No synthesized old effective view, conversion, imported history, legacy scope branch or restored old API is introduced.

Actual transport APIs: `to_dict()`, classmethod `from_dict(payload)`, `save_to_cache(path: Path)`, classmethod `load_from_cache(path: Path)`, `clone()`. Native persistence is MessagePack using `msgpack.packb(..., use_bin_type=True)` and unpacking `raw=False, strict_map_key=False`. EF owns policy tuple/list decoding; compiled passes the required effective mapping through real `EffectiveRunConfig.from_dict` and compares against a newly resolved expected run.

Existing from_dict already reconstructs outer selected configs, validates token coherence, reconstructs transported EF, re-derives EF using transported origins and compares complete `validate_payload`. Preserve this stronger expected-world comparison when adding actual roster; EF self-consistency alone would accept a fully rehashed foreign roster. Existing clone has a gap: after constructing cloned outer configs, it installs `EffectiveRunConfig.from_dict(self.effective_run.to_dict())` without comparing it against clone's expected outer inputs. Replace that installation with independent expected-world resolution and full canonical `validate_payload`, then install only the expected run after comparison succeeds. Keep actual caller capture origins. Use the same check before `to_dict` exports an effective view: a frozen dataclass still holds mutable nested DTOs, so changed outer bars or a deliberately substituted self-consistent EF must not be serialized as if world-bound.

Finite implementation choice: introduce a private candidate-resolution method in `CompiledUniverse` (new helper name is to be authored, not an alleged current public API). It uses selected actual brain/training/drive/bars and supplied origins, returns an EF candidate without assigning it. Existing `_derive_effective_run` assigns a successful candidate. Clone/from_dict/to_dict obtain a candidate, compare transported/current EF using existing `candidate.validate_payload(...)`, then install or export only after comparison. This avoids assigning a foreign run before validation and retains EF's canonical NaN-aware complete-tree comparison. No ordinary Python complete-tree equality replacement.

Before resolving/publishing a candidate, validate selected bars roster is exact ordered nonblank unique strings; tuple(), arbitrary names and case are retained. Compare names against selected `meter_declarations` and `meter_metadata.meters` in order so a cache cannot independently forge the bars authority while retaining old compiler token/metadata products. Existing token coherence independently validates declaration-to-token bindings/hashes; preserve it. Existing root metadata is a selected summary: compare its meter_names/count/name-to-index projection with selected meter metadata using the already exposed names/indices when establishing current loaded consistency. Do not require equality with environment-wide vocabulary. Candidate resolution delegates OP policy constraints; do not duplicate hard-coded static policy numbers in compiled code.

Current compiler cache recovery is a separate capability. `_read_cache_artifact` catches load exceptions and returns None; `compile` may rebuild from explicit current authoring. Root explicitly says preserve existing WP6/7 cache-path/source-freshness/CLI-no-traceback behavior. This is not an old-state importer. The bounded default is to leave that recovery intact and prove old-format refusal through `from_dict`/`load_from_cache`. Any proposal to make old-version cache hits terminate compilation, remove the broad catch, change oversize handling or change CLI error wrapping needs a separate precise capability ruling before implementation. Never compile against original protected historical directories: such a cache miss could rebuild/overwrite files through the existing cache behavior. Historical refusal tests only load original paths read-only, with before/after byte checks.

Exact cache facts from `compiler.py`: `_cache_artifact_path` returns `config_dir/.compiled/universe-{primary_level}.msgpack`. The filename/path does NOT include source digest, native schema or provenance ID. `_compute_package_source_digest` hashes relative paths and bytes of every townlet `.py` file; `_build_cache_fingerprint` includes that digest, config hash, resolved experiment path, compiler version and Python/Torch/Pydantic versions in provenance. `cache_staleness` compares artifact experiment path, config_hash, provenance_id and maximum YAML mtime, but is reached only after `_read_cache_artifact` successfully loads an artifact. Therefore compiler/compiled source edits move provenance but do not isolate a new physical cache path. An old-format load refusal currently becomes a miss before freshness comparison; stage8 may write a current artifact to the same mutable cache filename. No current filename-based historical isolation can honestly be claimed.

| Operation | Existing behavior | Bounded proposed behavior |
| --- | --- | --- |
| Direct `from_dict` / `load_from_cache`,1.40 | derive current view | ValueError schema mismatch, no writes |
| Direct1.41 input | validate former current view | ValueError schema mismatch, no writes |
| Direct current1.42 input | not yet implemented | independently validate actual world/EFv2 and succeed |
| Authored compile, fresh matching current cache | load cached object | preserve cache hit and freshness rules |
| Authored compile, stale valid cache | recompile explicit source, save mutable cache entry | preserve behavior |
| Authored compile, old/corrupt/oversize cache | warning/miss, recompile explicit source, save mutable cache entry | preserve recovery; no native old-state import |
| Original protected historical fixture | existing tests directly load/read | direct refusal/read-only digest controls; never run authored compile/save there |

Changing cache filename scheme or adding archival writes is unnecessary for this bounded packet and is not proposed. Fresh current qualification uses temporary authored packs/current cache entries; immutable originals remain untouched. Direct loader raises ValueError with found/expected schema and recompile instruction through existing `_validate_compiled_schema_version`; this report does not claim located compiler errors for those public direct APIs. Existing compile primary-level identity guard still uses located `CompilationError`/`ARTIFACT_LOAD_REFUSED` after successful load; preserve that distinct behavior.

No serialized or cloned roster hash/view is trusted on its own. Corrupted hash, valid-but-foreign self-consistent EF, malformed tuple/list, duplicate/non-string/blank names, missing baseline, outer roster mismatch and reordered selected bars with unchanged declaration/token products refuse before return/install/export. Full current matching artifacts and ordinary cache hits must still succeed.

## Concrete compiled factory witness

After accepted T21 producer APIs exist, the real authored route above feeds the new factory exactly:

```python
curriculum_options = run.options.curriculum
assert curriculum_options is not None
manager = build_curriculum(
    run.training,
    curriculum_options=curriculum_options,
    static_policy=run.static_policy,
    device=torch.device("cpu"),
)
```

`run.static_policy` and the new factory signature are root-accepted forthcoming producer APIs, not observations of uninspected implementation. The actual compiled/compile/run accessors in the first block are source-verified now. Root must supply final producer receipt for exact returned manager initialization/decision methods before this owner writes behavioral accessors; do not inspect a fifth source or invent a manager method. Root supplied decision-field receipt in T21 prose: `difficulty_level`, `active_meters`, `depletion_multiplier`, `reward_mode`, `reason`; this supports checking `.5/shaped/1/selected actual tuple` once the actual manager call route is supplied. No ENV construction or reward/depletion mechanics qualification is claimed by these metadata assertions.

## Tests-first finite packet

Root first supplies stationary OP/EF/factory producer receipt and explicitly starts this serial slice. New test file remains <=700 lines; existing test file <=500; no shared helper/fixture source reads. Root executes causal RED, source implementation then GREEN/guards. Suggested cases:

1. Current authored compile exposes `effective-run-v2` static policy with exact actual selected bars order. Separate L0/L1 authored selection with reordered test-owned L1 bars proves per-level selection. New real factory witness consumes compiled.effective_run and checks actual static decision fields. Keep static metadata application unqualified.
2. Current1.42 dictionary, MessagePack, public cache reuse and clone succeed and retain complete current effective payload, actual tuple, execution/authored identities, origins, brain/pack/per-level hashes and unrelated selected options. Current portable lists decode back to owned tuples. Mutating exported payload/returned DTO does not mutate original.
3. Static policy actual roster order/name changes are bound by EFv2 as producer receipt specifies. For adversarial strategy preserve inactive static-policy behavior and explicit expected-world validation even when static policy does not enter selected execution hash. No claim that a hash alone binds world state.
4. Substitute a self-consistent foreign-roster EF created by the real required EF resolver while leaving outer selected world unchanged; from_dict refuses. Inject it into a clone source with `object.__setattr__` as a deliberate corruption test: clone and serialization refuse without altering source payload/data. Changing outer bars alone refuses declaration/metadata mismatch. Corrupt EF execution hash, policy, roles, missing view, duplicate/non-string/blank roster entries and old policy/schema refuse independently.
5. Direct dictionary/native load rejects exact1.40, pre-change1.41, older/unknown/future/missing versions; fixtures remain byte-identical after refusal. Current artifacts loaded from fresh temporary authored packs continue to work. Preserve original historical data/manifests and all digest checks, with no rewrite/conversion programme.
6. New packet's first RED cannot pre-empt producer implementation: while EF required interface is absent, TypeError is only interface evidence. After T21 exists, failures must reach actual compiled missing-argument/roster/clone/current-format assertions. Root owns execution identity capture and causal evidence.

Existing tests requiring explicit semantic update:

- `test_known_v1_40_compiled_cache_derives_current_effective_view_without_rehashing`: replace obsolete successful derivation expectation with current-only1.40/1.41 refusal and payload unchanged assertions; current hash-preservation success stays in current roundtrip tests.
- `test_original_historical_compiled_caches_stay_readable`: rename/rewrite to preserved-original-bytes plus loud direct-loader refusal; retain real manifest loops, 15-artifact count and the original pre-optimizer sequence digest. Its old recurrent success assertion moves to a current authored recurrent witness rather than being deleted as a capability.
- `test_shadowed_base_fields_remain_authored_presets` and both direct calls in `test_selected_provider_activity_is_schema_owned`: add required actual roster argument; preserve every identity/capacity/preset/provider assertion.

Retain current feature assertions in `test_preset_edit_changes_authored_not_execution` (including real seeded network weights), `test_five_overrides_have_one_runtime_view`, `test_effective_cache_roundtrip`, `test_inactive_raw_nan_presets_survive_real_msgpack`, `test_selected_provider_capacity_materializes_after_rp`, `test_materialized_provider_defaults_are_not_authored_overrides`, `test_field_roles_drive_execution_identity`, and remaining shadowed/provider tests. Do not replace these with mocks or weaken brain-family/provider/replay choices to make schema tests pass. No old-test source outside counted inventory inspected; root must run named T03 owner controls and assess failures without claiming their assertions were reviewed here.

## Remaining limits

No producer implementation was read or qualified; no actual compiler/factory call executed; no serialized/clone GREEN, current cache GREEN, independent review, full suite, ENV application, runner integration or full BAC acceptance claimed. Root must settle final native1.42 label and proposed selected roster/summary validation before tests/source authorization. The missing producer receipt must name final EF serialization/schema policy and factory manager call route. Current compiler cache recovery is retained unless root explicitly approves a separately scoped change.
