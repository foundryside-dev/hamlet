# T21 current options, static baseline and factory implementation

Source stationary for root GREEN/guards/review. This report records authored implementation, not passing tests, accepted producer handoff or integrated release. Root supplied original R0 tree987a2ae0ebf692b278a4689a0332c573a4a6e2d9:52 collected/47 FAIL/5 PASS/0 ERROR, with one unsupported custom_reward fixture corrected to supported sparse. Corrected custom control R1:1 PASS/51 deselected/3.7913 seconds; production unchanged and custody PASS. Remaining46 initial failures identify actual current-interface/semantic gaps, including direct legacy_step acceptance/schema/signature assertions; initial EF missing-required-roster TypeErrors do not claim deeper assertions already executed.

## Exact inventory

Only the approved five source/test files and three exact YAML selectors changed. Prose reports are separate ignored handoffs. No sixth source/helper/probe/fixture inspected, no production imports/runtime/tests/guards/Git/index/commits/push/subagents/branch/worktree/copies/deletion executed. Authorized formatter on these five paths reported1 file reformatted,4 files left unchanged, exit0.

| File under src/townlet unless test | Lines | SHA256 | Ceiling |
| --- | ---: | --- | ---: |
| config/bac_options.py |323|cc0b2b9cfbbfd6396a9080b90bd65692f964e04c75693a164408f59f0dab3ee6|1200|
| config/training_v2_config.py |435|2803a9572b9836e857815c734b15f47ae20f2bb65b490f639be49b7fa49bd863|900|
| config/effective_run.py |371|9ec1ddfa5259e9d5ffa2880e2cf65dab1e22b939aae50f80d1396f307fba8999|500|
| curriculum/factory.py |58|10be467c8ca72853bd8c6cceac60e6e13fcb4f202f1511fc7a9040539dbd9c71|200|
| tests/test_townlet/regressions/bac/test_curriculum_factory.py |350|274ac3acfb11a0ef53951075e6a58fdfce7107d7bd68d49faa4aeb1187f1ad0c|650|

Actual5/1537, projection5/3450, hard5/5000. Test retains all52 corrected scenarios and adds one missing_scope payload refusal parameter before production branch removal; collection count53 is projected, not executed here.

Exact YAML changes are solely commit_mode legacy_step to completion, retaining rate_limited and all other substantive configuration:

| YAML | SHA256 |
| --- | --- |
| configs/test/bac_remediation/options/modes-1.yaml |3e7c44b0a644df0b0dde1e6d2191fcad6afaf834202ce98701c27823d9a0b123|
| configs/test/bac_remediation/dueling/levels/L0_0_minimal/training.yaml |b0868d5ab09b3a80d2f92f08cf4f222ed8532f1b5635736d77822eaba1786d1d|
| configs/test/bac_remediation/recurrent/levels/L0_0_minimal/training.yaml |765504acec8ad27b298cb9ea4fa50afb273fa0dc78a16f67156ce0f016e02c48|

Root must regenerate its frozen config inventory; no generator was read or run here.

## Current API and schema receipt

OP retains resolve_bac_options(options: BaCOptions | None, *, training: TrainingV2Config) -> ResolvedBaCOptions. No unrelated caller must fabricate a roster to resolve replay/provider options. Authored None still means absence; the canonical table resolves completion/stage_band. Authored legacy_step now fails strict CurriculumOptions validation. Resolved schema_version is bac-options-v2; omitted table values carry current v2 origin/reason. Unrelated token-encoder/curiosity seed provenance retains its established semantic labels rather than mechanical global renaming.

OP additionally owns resolve_static_baseline_policy(*, declared_meter_names: tuple[str,...]) -> StaticBaselinePolicy. Required immutable fields: policy_id static-baseline-v1, difficulty_level.5, reward_mode shaped, depletion_multiplier1, active_meters exact tuple. The strict model forbids unknown/nonfinite data and alternate baseline constants; tuple names must be strings, nonblank and unique. Empty tuple is valid. This is resolved-only data, absent from authored BaCOptions/TC; programmatic StaticCurriculum retains supported custom difficulty/reward/meter/depletion choices. No factory-local resolver or old API adapter exists.

EF resolve_effective_run retains existing arguments and adds REQUIRED declared_meter_names: tuple[str,...]. It obtains policy from the single OP baseline resolver, stores required static_policy in EffectiveRunConfig, and serializes it explicitly. from_dict requires that declaration, explicitly decodes portable list to tuple, validates the current typed declaration, recomputes effective configuration from authoring plus that tuple and compares the complete canonical payload. Missing/tampered fields refuse. Removed the entire obsolete shared-scope missing-field acceptance branch and its imports from EF. No current old-format EF fallback remains. Uninspected exploration producer decoder and outer checkpoint formats are separately owned; this does not claim their migration is complete.

Current factory signature:

    build_curriculum(training: TrainingV2Config, *,
                     curriculum_options: CurriculumOptions,
                     static_policy: StaticBaselinePolicy,
                     device: torch.device) -> CurriculumManager

It refuses unresolved/obsolete modes before either strategy. Static passes all five accepted required parameters explicitly and copies the tuple to constructor list. Adversarial passes commit/difficulty modes, adaptation rate/bounds, advance/retreat thresholds, entropy gate, dwell and device exactly. No horizon parameter, configure_from_training, constructor defaults, attribute probing or alternate signature remains. Returned manager is uninitialized; caller still owns initialize_population(num_agents).

TC descriptions now name completion survival_time/planned_horizon, eligible-transition dwell, and per-eligible-transition maximum rate movement inactive under stage_band. Authored rate remains >0; programmatic T20 zero rate remains independent. Singleton bounds and substantive nonselected adversarial authoring are retained.

## Meaning, provenance and identity

EF commit_mode is active/derived for both static and adversarial. difficulty_mode is inactive under static; adversarial presets remain inactive there. adaptation_rate remains inactive for adversarial stage_band. No replay/provider/network selector is removed.

Static declaration roles under selected static: policy_id/difficulty/depletion derived from static-baseline-v1; reward_mode and active_meters application remain unqualified. Meter provenance origin is declared_level_meters, with reason actual declared level.bars.meters names in declared order. All baseline fields are inactive presets under adversarial. The complete declaration is separately bound into selected policy-context identity, preserving truthful application labels.

Exact current execution payload: schema effective-run-v2, fields existing selected active projection, exploration existing selected policy_identity; additionally static_policy full model_dump only when static is selected. Thus actual static roster order/names affect execution hash without pretending roster application has been implemented. Inactive static baseline is excluded under adversarial. Existing authored training hash preserves complete training authoring independently; no new authored knob was added. Authored_identity retains its existing brain/exploration-authoring expression. Neither this receipt nor the baseline hashes establish broader compiled-world identity for adversarial.

A serialized self-consistent EF payload is not proof that it matches a separately supplied actual world. Parent current-native validators must compare expected effective/world identity before installation; T24/current world owners retain that obligation.

## Tests, consumers and remaining gates

Tests cover actual completion-driven difficulty/rate/threshold/dwell effects, singleton/native future, fixed static choices and ownership, supported custom sparse reward, actual YAML meter roster and arbitrary/empty tuple, obsolete/unresolved/invalid refusal, inactive/active identity differences, normalization of omitted/explicit equal modes, portable current payload and forged/missing declaration/scope/role/hash rejection. Root must run these and classify actual failures; no passing result is claimed here.

Known compiler API supplied by root: UniverseCompiler().compile(Path(pack), primary_level='L0_test', use_cache=False), compiled.effective_run. Compiler producer maintenance is the next bounded serial owner task, not inspected or implemented here. Existing external EF calls must supply the actual roster, and current direct/effective factory callers must transport the resolved options and policy. Real compiled-route witness remains required after that owner receipt; no guessed stand-in or skipped acceptance substitutes for it. Pure OP callers remain unchanged.

Six obsolete factory-call mypy errors are targeted by the current construction repair; global type health may expose external EF/factory callers until bounded maintenance completes. This report claims no type/default/lint guard success. Root retains all execution, default ratchet and exact-tree custody checks; no ignore/waiver/ratchet increase was authored. Current-native outer validators/T23 pipeline/real world identity/meter-reward application boundaries, independent review, earlier-full pytest/standing guards, substantive native/learning/restart/E2E/final BAC acceptance remain open.
