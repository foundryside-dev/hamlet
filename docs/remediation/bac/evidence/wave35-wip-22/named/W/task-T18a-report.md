# T18a implementation receipt

Status: fix round 1 source and scoped verification complete; source frozen for fresh same-reviewer review and coordinator gates. The prior review required changes, and fresh same-reviewer approval/root gates remain pending. No staging, commits, pushes, extra implementation/helper source reads, dependency installation, network work, delegation, or root-ledger edits. This receipt does not release a dependent package or claim repository-wide qualification.

- candidate_sha: `050a1a70e979aa03724219b81e848093820f044f` (shared checkout HEAD; owned additions are uncommitted and identified below).
- scope: additive authored exploration resolution only; two new files, no changes to DRIVE/TC/OP or other existing source.
- authorities: extracted T18a brief including its refreshed 5/2950 context table; full same-workspace P5a excerpt SHA256 `aad80569fe0df3a3487c13a87b8654d5ba9b321fd0e8690cb7d78d20039ff654`; frozen original plan SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`; approved B overlay MD `3b82ecc340b936cd5672f248b85508f75136ab76cb994ac54723673989906871`, JSON `2d5547c9a1805ca33cba5f5e0e6fa9a729d711562250721d5848e0c8b8b481a9`.
- review_record: fresh independent review pending coordinator dispatch.
- full_suite_status: not run by this worker; root owns fixed-candidate standing/full gates.
- full_suite_reason: root explicitly retains gate ownership; unused additive resolver does not change existing consumers. Worker does not waive earlier-full triggers or decide release.
- next_full_gate: G1, or earlier if root assesses an applicable trigger.

## Complete source inventory

Exactly five implementation/test files / **2391 whole lines**, within the user 5/5000 bound and root-approved repair ceilings RP850/test500 (no code compression). The refreshed task metadata originally projected 5/2950. No sixth implementation, fixture, helper, conftest, compiler or external probe source was opened. Existing owner tests were executed without opening them. YAML/reference documents and this report are not executable sources. Both new target paths were absent before creation.

| Access | File | Whole lines | SHA256 |
|---|---|---:|---|
| new | src/townlet/config/exploration_policy.py | 653 | 496b988555bc0f23f1a6e335386102acbc1450df1d064d87cfd616a0d953299a |
| read only | src/townlet/config/drive_as_code.py | 605 | 870e44fbc55f4bc7a221e7272cebea893ff95bfe37f23c6e4e01c4e80595150c |
| read only | src/townlet/config/training_v2_config.py | 443 | d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68 |
| read only | src/townlet/config/bac_options.py | 243 | 1de08a7cc36c49772254d8b9dc2d8adf3cac76533eecba5c36568745bc48c8f1 |
| new test | tests/test_townlet/regressions/bac/test_exploration_policy.py | 447 | 77ed751bb431c5203b6c38354b3f6f6e583d4c4a699df5d94d9bd89fd35eafc2 |

## Produced API and ownership boundary

`resolve_exploration_policy(drive_intrinsic: IntrinsicStrategyConfig, training: TrainingV2Config, options: BaCOptions) -> ResolvedExplorationPolicy` consumes **authored** partial `BaCOptions`, or `BaCOptions()` for omission. Do not pass `resolve_bac_options(...).options`: its materialized count/ICM derivations are indistinguishable from explicit typed declarations at this signature. RP internally calls the existing OP resolution function with empty authored options to obtain its versioned omission table/provenance, then applies original authored source/service fields, drive precedence and dependent selected-provider derivations before selected capacity checks. Standalone OP remains unchanged, including its original training-owned capacity checks. T03 must pass authored options and consume the resulting policy, not repeat this resolution.

Local immutable `FieldRole(status, origin, reason)` uses exactly `active`, `inactive_preset`, `derived`, `unqualified`. T03 owns its own EF role type and can convert these three fields structurally; RP imports no future EF module.

`ResolvedExplorationPolicy` is a frozen dataclass containing every P5a scalar, drive selector/base weight/modifier names, selected `provider_parameters`, the two exact observation-phase fields, role map and explicit service fields `service_mode`, `max_updates_per_tick`, `max_pending_rows`, `overflow_policy`. Additional explicit metadata is `provider_parameter_source`, `raw_provider_parameters`, `authored_parameters`, `parameter_units` and `predictor_input_kind`.

Coordinator clarification preserves `predictor_observation_phase='eligible_predecessor'` universally as eligibility/admission origin and adds `predictor_input_kind: Literal['observation','transition']`: transition only for ICM. Reward phase remains exactly `successor_postphysics`. The kind is immutable, validated, recorded with an active role and included in execution identity. This metadata addition neither reduces ICM to observation-only service nor changes the frozen P5a phase literal.

Policy mappings recursively own immutable copies through mapping proxies and tuples. `.to_dict()` returns a new portable dictionary/list tree, and `ResolvedExplorationPolicy.from_dict(payload)` reconstructs the immutable DTO and rejects corrupt active numeric values. Mutating source DTO dictionaries or returned portable data does not change an existing policy. Frozen `FieldRole` values are immutable.

`.policy_identity` is a canonical SHA256 string over the `exploration-policy-v1` tag and the strategy-defined active resolved fields only. The selected strategy/schema, rather than transported role annotations, determines activity. Mandatory selected scalar/map/service values and their role annotations must agree before construction succeeds. `.execution_identity()` returns that same string. `.authored_identity` separately hashes the complete captured authored drive/training/options tree, including retained raw presets. No existing brain, pack, cache or training hash API changed. Runtime providers and EffectiveRun/compiled-policy persistence are not claimed implemented here.

Selected parameter sets:

- `none`: empty provider map; epsilon remains active; runtime intrinsic scale, DAC intrinsic weight/modifiers, RND knobs and service knobs are inactive presets. No authored `enabled` switch is inferred.
- `rnd`: `feature_dim`, `learning_rate`, `predictor_batch_size`, fixed initial runtime scale in the policy.
- `adaptive_rnd`: the RND set plus `min_intrinsic_weight`, `variance_threshold`, `min_survival_fraction`, `max_episode_length`, `survival_window`, `decay_rate`.
- `count_based`: `quantization_width`, `max_entries`.
- `icm`: `feature_dim`, `hidden_dim`, `learning_rate`, `inverse_weight`, `forward_weight`, `training_batch_size`, `max_pending_transitions`.

Drive owns provider selection and DAC base weight/modifier names. Training owns epsilon and initial runtime scale, including valid zero. RND/adaptive recognized raw keys remain presets unless `provider_parameter_source='drive'`; selected aliases at equal precedence diagnose contradictory located entries. Training fallback remains for unprovided recognized drive keys. Typed selected count/ICM fields override recognized raw drive fields, then recorded derived values. ICM hidden width and pending capacity derive from the final selected feature/batch values. Nonselected/unknown raw dictionary values remain in `raw_provider_parameters`, plus located inactive roles; unknown nested mappings/lists survive portable round trip. Portable raw authoring is validated without claiming unknown fields are consumed. Nonfinite active parameters diagnose their authored location. Lower-precedence values that are overridden remain inactive presets.

`IntrinsicTransitionContext(*, predecessor, actions, successor, active_on_entry, vector_tick)` owns detached tensor snapshots with shapes `[N,D]`, `[N]`, `[N,D]`, `[N]`. Accessors return fresh clones. It validates shape, observation dtype, int64 actions, bool eligibility, common device, finite observations and a nonnegative integer vector tick. Caller mutation cannot alter the captured snapshot; private backing attributes are implementation details.

Frozen `ExplorationServiceReceipt(provider, admitted_rows, consumed_rows, dropped_rows, pending_rows, optimizer_updates, mandatory_service_updates, last_loss)` is the exact P5a schema. It validates nonnegative integer counts, finite nonnegative loss, recognized provider kind and mandatory service no greater than total updates. No provider factory or placeholder was added.

## Original pre-review causal red and green (historical evidence)

Used TDD and verification-before-completion skills. All meaningful test processes use installed `.venv/bin/python`, `PYTHONPATH=/workspace/hamlet/src`, empty `CUDA_VISIBLE_DEVICES`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `torch.set_num_threads(1)` and asserted actual `townlet.__file__` at this checkout. No uv sync or network. Green processes record HEAD and five-file SHA256 inventory and assert unchanged files after pytest; final combined run also asserts unchanged HEAD.

focused_commands:

`PYTHONPATH=/workspace/hamlet/src CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python` with the inline import/identity/thread harness invoking `pytest.main(['--no-cov', '-p', 'no:cacheprovider', 'tests/test_townlet/regressions/bac/test_exploration_policy.py', '-q'])`.

- Initial corrected causal red: **29 failed in 0.41s**, all at `authored exploration resolver interface missing`, before production creation. `task-T18a-red.log`. A preceding exploratory attempt had an incorrect fixture-root parent index, which was corrected before this meaningful red; it is not counted as evidence.
- Initial production green: 28 passed, one failed because the test assumed a nonexistent `CompiledUniverse.training_configs` accessor. Root supplied the public `compiled.all_levels[level].training` and `.drive` contracts; no compiler source opened. Runtime dataclass-field introspection independently showed `all_levels`, without reading implementation. Test repaired to use the actual public API.
- Role/transport negative controls: **3 failed in 0.12s**, exposing missing overridden adaptive training provenance, generic ICM derivation provenance, and unchecked corrupt active scalar in `from_dict`. Repaired; `task-T18a-role-red.log`.
- Capacity-provenance negative control: **1 failed in 0.26s** because the correctly selected drive predictor capacity still described the training batch in its derivation reason. Corrected the reason to `max(2 * training.population.size, resolved predictor_batch_size); bounded-service upgrade`; `task-T18a-capacity-red.log`.
- Original pre-review exact focused command: **32 passed in 13.63s**; `task-T18a-focused-final-green.log`. These old32-test bytes/hashes are superseded by the fix-round evidence below.

Assertions cover five selector kinds, training/drive ownership, selected typed overrides, nested inactive authoring retention, equal-rank conflict locations, active nonfinite diagnostics, zero initial scale, active provider/epsilon/annealing/service/DAC identity contrasts, inactive service/nonselected typed/preset identity controls, dependent ICM values, immutable source/portable copies, context/receipt schema and service capacity. No expected diagnostic is silently skipped.

The actual authored portable integration case copies the full canonical curriculum into pytest temporary storage, edits its training YAML with a typed ICM feature override and drive YAML with ICM hidden width/unknown retained values, compiles it through `UniverseCompiler().compile(..., primary_level='L0_0_minimal', use_cache=False)`, performs `CompiledUniverse.to_dict()/from_dict()` and obtains real typed training/drive DTOs through `all_levels`. It verifies typed > drive precedence, retained unknown keys, policy portable identity and an inactive preset authored/execution contrast. It changes no original YAML and writes generated compiler artifacts only inside that temp copy. EffectiveRun integration is expressly T03, rather than an invented helper here.

owner_suite_commands:

The same import/identity/thread harness runs pytest arguments `--no-cov -p no:cacheprovider tests/test_townlet/unit/config/test_drive_as_code_dto.py tests/test_townlet/unit/config/test_training_v2_config_dto.py tests/test_townlet/regressions/bac/test_options.py -q`.

Earlier owner run: **62 passed in 59.48s**; `task-T18a-owner-green.log`. Original pre-review combined run prepended the focused module to that owner selection: **94 passed in 98.54s**, `task-T18a-final-green.log`. Its before/after HEAD and five-file hash assertions passed for the original32-test candidate, not the repaired current candidate. Current evidence follows.

## Static checks and limits

static_commands (all passed on final source):

- `.venv/bin/ruff check src/townlet/config/exploration_policy.py tests/test_townlet/regressions/bac/test_exploration_policy.py`
- `.venv/bin/black --check src/townlet/config/exploration_policy.py tests/test_townlet/regressions/bac/test_exploration_policy.py`
- `.venv/bin/mypy src/townlet/config/exploration_policy.py`
- `.venv/bin/python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet` — clean, unchanged **614** whitelisted/ceiling. An initial local `setdefault` violation was replaced with an explicit key branch, no whitelist/ratchet changes.

Scope/origin/world binding/guarantee/local clock units: this packet resolves the existing shared-learner policy and preserves omission/default coupling. It adds no per-world scope, partition, controller or serving policy fields; PW01 is later. Runtime-scale origin is training; DAC weights/modifier names remain drive-owned. Reward/predictor phases and ICM transition input are explicit. Epsilon factor is per committed batch episode, predictor budget per vector tick, pending/batch capacities count eligible rows or complete ICM transitions, and adaptive survival metadata records lane steps/outcomes. `parameter_units` carries these numeric/phase contracts. This is resolution/schema/identity evidence, not learned competence, real reward execution, provider service, checkpoint restoration or per-world isolation evidence.

unrun_checks: repository-wide Ruff/Black/mypy, compiler CLI/document-generation guard, full pytest/coverage/slow/GPU/applicable-hardware, fixed-SHA independent review, root frozen-input regeneration, remote CI, staging/commit. Root owns their exact candidate and gate selection. No repository-green, merge-ready or whole-BAC-complete claim is made.


## Fix round 1 — both independent P2 findings

Read the complete `task-T18a-review.md`; reviewed old immutable tree `212b3d6d1aa71474c0bfadb3521bbbce3d3b7d5d` and patch SHA256 `6b33bd4e8b28a95e1dd640bfdd3c65fbb88518179c690ce6a9982514cc77f1dc`. This repair addresses the reported failures; it does not self-close the review. No source outside RP and its owned regression module was changed. OP/TC/DRIVE retain exactly their table hashes above.

R1: standalone OP was called on training batch32 before selected raw batch8 participated. Corrected within RP only: obtain OP's versioned omission table using `BaCOptions()`, apply the original authored source/service declarations, select typed > raw > derived provider parameters, derive omitted capacity from the actual selected batch, then enforce selected cross-field capacity. Typed service overrides keep active/authored provenance. No exception is swallowed; no model_construct bypass or standalone validation switch was introduced.

- Causal selection `-k 'final_selected_batch or typed_icm_batch or standalone_options'`: **3 failed, 8 passed in0.26s** before repair; exactly the RND/adaptive/ICM selected8/pending8 valid-input rejections. `task-T18a-r1-capacity-red.log`.
- Same selection after repair: **11 passed in0.12s**, `task-T18a-r1-capacity-green.log`. Positive controls cover exact-fit8/8; negatives reject selected8/7; omitted capacity with N8/selectedbatch8 is16 rather than training-preset32; typed ICM batch4 overrides raw8 and fits typed capacity4. Explicit service8 retains active role. Standalone `resolve_bac_options` still rejects capacities8 against its original training-owned32 interpretation for RND and ICM.

R2: transported roles previously controlled scalar validation/identity and provider maps admitted arbitrary subsets. Added a strategy-defined exact schema for all five providers, including duplicate scalar names. Mandatory selected scalar validation ignores transported role activity. Provider maps must contain exactly the selected required keys, all selected parameters must be valid, and every duplicated RND/adaptive/ICM batch/capacity value must agree. ICM provider pending transitions equal the explicit service capacity, and capacity accommodates the selected batch. Top-level and selected-parameter activity annotations must agree with the selected schema; invalid/inactive annotations cannot remove an active field from validation or identity. Execution identity itself now obtains field membership from the selected schema. Valid inactive presets remain separate and portable.

- Causal selection `-k 'contradictory_selected or exact_selected_provider or roles_cannot or transported_roles or all_selected_policies'`: **32 failed,10 passed in1.72s** before repair. Both `from_dict` and direct dataclass construction accepted conflicting map/scalar values, missing/extra schemas and hidden active scalar NaNs; ten valid round-trip controls already passed. `task-T18a-r1-transport-red.log`.
- Same selection after repair: **42 passed in0.40s**, `task-T18a-r1-transport-green.log`. Covers RND feature/rate/batch mismatches, adaptive variance mismatch, ICM batch/capacity mismatch, extra keys for every provider (including none), empty maps for every non-none provider, hidden selected scalar NaNs, false activity on finite selected scalars, and unchanged complete portable/direct round-trips for all five providers. Finite inactive RND presets for none/count/ICM remain accepted without changing execution identity.

Current final focused command is the exact module command already specified above with fresh import/HEAD/five-hash assertions: **85 passed in12.50s**, `task-T18a-r1-focused-green.log`. Final owner selection: **62 passed in64.43s**, `task-T18a-r1-owner-green.log`, against the identical five-file hashes and HEAD in the table above. Both final test processes asserted unchanged imported checkout, all five files, and HEAD before/after execution. No source changed after either final pass.

Current scoped Ruff/Black/mypy and whole-tree no-defaults guard passed. The first repair-static pass flagged an ordinary logical-OR activity expression as ASG001; it was replaced with equivalent explicit branches. Final defaults remains614 whitelisted at614 ceiling; whitelist/ratchet unchanged.

**Mandatory T03 selected-context handoff:** first resolve RP from original authored partial options. Never run standalone OP against original training32 and explicit capacity8 before RP selects batch8. RP publicly exposes the actual `predictor_batch_size`, selected `provider_parameters` and `service_mode/max_updates_per_tick/max_pending_rows/overflow_policy`, with origins/roles. Materialization of overall effective options must consume that selected context rather than repeat the premature training-preset capacity interpretation. Standalone OP has no selected-provider-context parameter and remains deliberately unchanged in this packet. T03 must document/test its integration choice, keep original authored options separately, and must not feed materialized provider derivations back into RP as authored overrides.

The new joint candidate needs fresh same-Astra review and coordinator full-wave PASS before T03. No obsolete wave/full-gate execution or approval is claimed by this worker. Root's T09a action repair is disjoint and not inspected or edited here.
