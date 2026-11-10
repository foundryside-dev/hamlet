# T21 finite source-based design handoff

Status: preparation only, not implementation or an accepted producer receipt. Root settles the finite choices below before tests-first authoring. No runtime, imports, tests, formatters, Git/index or source edits performed. The only written file is this report. Full BAC acceptance remains open.

## Actual inventory and authority

Read AGENTS.md, approved no-compat amendment and Astra R2, T21 readiness, accepted T20 implementation/constructor and R11 receipts, and T21 execution brief. T20 accepted tree763ed2ce04718627f15ecf98d52b1e0333ae3fe6 is root-supplied provenance; this worker did not inspect its implementation. Root reports publication02d1f614bfbf603b9742d8fea60984b7b7e1b568. Existing branch/workspace retained.

Only these four whole source files were inspected. Fifth reserved source is tests/test_townlet/regressions/bac/test_curriculum_factory.py650, absent per dispatch; no sixth implementation/test/helper/probe/fixture source inspected. No ENV/POP/RR/CC source inspected. Planned ceilings1200/900/500/200/650 total3450, hard5/5000.

| Source | Actual | SHA256 |
| --- | ---: | --- |
| config/bac_options.py |294|10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916|
| config/training_v2_config.py |435|ad097576f88e1e2a09ae816ccff823e9623e7d5584b0d0411b07efb2f6ba1dfc|
| config/effective_run.py |365|9ff2c4e8cc538160abe7188c7a2192b3ee740464d1b0681790e569685d49882c|
| curriculum/factory.py |70|82f464d5a3dfaaaca4e06cd1fffb7f2ddb5c2646ef62524214598d236846aabe|

Actual four files1164. Paths above are under src/townlet.

## Actual transport facts

OP CurriculumOptions accepts completion/legacy_step/None and stage_band/rate_limited/None. OptionModel is frozen, strict, finite-only and extra-forbid. None is an authored absence marker. resolve_bac_options(options, *, training) owns the omission table and returns ResolvedBaCOptions(schema_version='bac-options-v1', options=BaCOptions, provenance=tuple). It currently has no static declaration or roster input. Explicit values get authored provenance; omitted modes resolve completion/stage_band.

TC holds optional authored training.bac_options, strategy static/adversarial and an optional adversarial block required only when selected. No static-policy authoring fields exist. All adversarial parameters are explicit, validated finite, and nonselected presets survive. adaptation_rate currently requires >0, despite accepted programmatic T20 permitting zero: retain this authored constraint unless root deliberately broadens it. Bounds admit singleton .6. Current threshold/dwell/rate descriptions require completion-unit corrections.

EF resolve_effective_run(base, training, *, primary_level, origins, drive_intrinsic) resolves exploration first, asks OP for omissions with only curiosity_scope authoring, overlays authored values, and installs selected exploration/provider values. This ordering matters: calling full OP resolution on authored options instead can reactivate a training-based capacity refusal for a drive-selected provider. Do not casually replace this logic. EffectiveRunConfig exposes training and options (deep copies), authored_options, exploration and identities; it carries no ResolvedBaCOptions object, no curriculum-specific declaration and no bars/roster. to_dict/from_dict reconstruct and compare the effective payload. Execution hash uses schema effective-run-v1 plus selected field values and exploration identity. Authored training hash separately preserves complete training authoring; authored_identity delegates captured training/drive semantics to exploration.authored_identity (its implementation is outside this inventory).

EF currently marks ALL curriculum options inactive under static, including commit_mode. It already marks adversarial adaptation_rate inactive for stage_band and all adversarial training presets inactive under static. This needs the precise commit-mode correction below. EF also contains a legacy shared-scope payload acceptance branch; its current-only removal remains the designated T24 task, not a reason to expand this slice into exploration source.

CF build_curriculum(training, *, max_steps_per_episode, device) ignores BAC options. Static passes only difficulty=.5. Adversarial passes obsolete max_steps_per_episode and invokes removed configure_from_training. Factory does not initialize population. The six old factory type errors are an explicit repair target, not a reason to restore obsolete APIs.

No compiled object API is defined in these four files. A compiled path cannot honestly be named from this inventory. Required downstream receipt must name its actual effective-run attribute; no getattr/hasattr probing or guessed compiled DTO is proposed.

## Recommended minimal finite design

Use a separate resolved-only immutable StaticBaselinePolicy in OP, with required fields policy_id, difficulty_level, reward_mode, depletion_multiplier, active_meters_source. Canonical instance: policy_id='static-baseline-v1', difficulty_level=0.5, reward_mode='shaped', depletion_multiplier=1.0, active_meters_source='declared_level_meters'. This is a current named declaration chosen by root, not copied constructor defaults. Do not add it to authored CurriculumOptions/BaCOptions or training schema: that would create unwanted authored knobs. Programmatic StaticCurriculum continues accepting its custom fixed parameters directly.

Add required static_policy: StaticBaselinePolicy to ResolvedBaCOptions and EffectiveRunConfig. OP constructs/returns the single baseline; EF transports defaults.static_policy unchanged. This is one semantic resolver; factory never resolves omissions. Include baseline field provenance with the same resolved return, and preserve it in EF roles/derivations. Resolve/serialize the immutable policy for either strategy, with inactive roles under adversarial.

Proposed factory signature (all new arguments required):

    build_curriculum(training: TrainingV2Config, *, curriculum_options: CurriculumOptions,
                     static_policy: StaticBaselinePolicy,
                     declared_meter_names: tuple[str, ...], device: torch.device) -> CurriculumManager

Require curriculum_options.commit_mode == 'completion' and non-None supported difficulty_mode before either branch; unresolved input is an error, never a local resolution request. Transport static_policy fields directly to StaticCurriculum, and list(declared_meter_names) as active_meters. Preserve the real roster's order, empty tuple, arbitrary names; reject non-string/empty-name/duplicate entries without inventing standard names. No population initialization is added: caller retains initialize_population(num_agents) after construction. Adversarial passes all ten supplied policy fields plus device exactly from resolved modes and the selected training DTO, with no horizon constructor argument.

Direct route: resolve_bac_options(training.bac_options, training=training), then pass its options.curriculum and static_policy plus actual roster/device. Effective route: pass effective.training, effective.options.curriculum, effective.static_policy and the actual roster/device. Narrow non-None curriculum at the call boundary explicitly. Compiled route must use its actual transported EffectiveRunConfig from the missing receipt; no additional factory overload/adaptor is needed.

Suggested version disposition: ResolvedBaCOptions schema becomes bac-options-v2 and its current omission provenance follows that version; TC description changes accordingly. Preserve unrelated token-encoder/curiosity provenance meanings rather than mechanically renaming all v1 strings. EF selected hash recipe becomes effective-run-v2 because static baseline/commit semantics now enter it; to_dict requires static_policy and from_dict reconstructs/checks it. Old payloads missing this new required field fail comparison, not migrate. Curriculum native schema remains T20 version2. Root should settle these two label changes explicitly because downstream exact identity expectations require refreshed receipts.

## Roles and identity treatment

| Field | Static selected | Adversarial selected | Execution hash |
| --- | --- | --- | --- |
| training.curriculum.strategy |active|active|included|
| curriculum.commit_mode |active if authored, derived if omitted|same|included for both|
| curriculum.difficulty_mode |inactive preset|active/derived|adversarial only|
| training.curriculum.adversarial.* |inactive preset|active except adaptation_rate under stage_band|selected meaningful fields only|
| static_policy.policy_id/difficulty_level/depletion_multiplier |derived from named baseline|inactive preset|static only|
| static_policy.reward_mode/active_meters_source |unqualified application metadata|inactive preset|bind in explicit selected-policy identity projection, without falsely labeling active|
| actual declared_meter_names |caller-owned roster metadata, application unqualified|unused by factory|requires world/compiled identity receipt, below|

Existing EF record() omits unqualified fields from its active projection. Therefore add an explicit selected static-policy identity projection containing the COMPLETE named declaration, separate from activity labels. This binds reward/meter metadata without pretending environment application is qualified. Both the full declaration and per-field roles serialize; malformed/tampered declaration and identity payloads refuse reconstruction. Keep inactive adversarial presets in authored/training identity but exclude them from selected execution hash, as today. Under adversarial, static declaration is preserved but excluded from selected execution hash.

Critical boundary: EF cannot hash the actual roster, because no roster exists in its input. Do not claim the declared_level_meters marker hashes actual names. Prefer binding the real roster in the existing compiled/world identity owner and current curriculum native config (which T20 already includes active_meters), with a concrete consumer receipt before integrated qualification. If root requires EF.execution_hash itself to vary on roster names, that requires a deliberate new required roster argument to resolve_effective_run, serialization/reconstruction and all external callers; it is a distinct cross-owner change and cannot be hidden in a factory fallback. This is the only material finite identity choice still requiring root disposition.

## Finite tests-first packet

Use the one reserved test file, self-contained test data from permitted YAML or inline literals; no helper/fixture source reads. Root owns execution. Build real models and managers, not constructor-call mocks as the only proof.

1. Authored completion accepted; legacy_step refuses at DTO validation; None/omitted resolve completion/stage_band with current provenance. Explicit rate_limited retained. Unknown values/fields refuse.
2. Direct and effective construction witnesses: static yields fixed .5/shaped/1 and exact supplied roster including unusual names and valid empty roster; mutation of input/returned data cannot change initialized manager policy. Both paths use the exact resolved policy. Unresolved modes refuse, even for static. Obsolete factory horizon kwarg refuses.
3. Real adversarial stage_band versus rate_limited at rates .01/.1 over actual accepted LaneOutcome completions; assert meaningful resulting difficulties, singleton .6 and configured threshold/dwell effects, not merely field presence. Native roundtrip/future behavior may use accepted T20 API without opening producer source.
4. Programmatic StaticCurriculum with custom .8/reward label/meter roster/depletion retains its explicit decisions. Factory baseline does not constrain the constructor's supported custom choices.
5. EF identity/role tests: static commit active/derived; static difficulty mode and adversarial presets inactive; changing inactive preset changes authoring identity/hash but not execution hash. Under adversarial, adaptation_rate changes execution hash only for rate_limited. Static declaration included in serialized effective payload and selected identity; omitted vs explicit equal modes produce same execution hash, different provenance as appropriate.
6. Current payload roundtrip and forged static declaration/roles/hash refusal; missing static declaration and obsolete commit value refuse. Baseline immutability tested. Preserve unrelated replay/provider/brain options through resolution, using existing suites for broader family coverage.
7. Exact three YAML selectors become completion: options/modes-1.yaml and dueling/recurrent levels/L0_0_minimal/training.yaml. Retain rate_limited and every other option. Existing completion profiles remain valid. YAML filenames are supplied by readiness receipt, not new implementation reads.

Causal RED must reach behavior where possible: existing legacy_step acceptance is a direct failing assertion; current factory constructor mismatch is an actual call failure; existing static commit-mode role is demonstrably wrong. New API absence alone is insufficient evidence for all later behaviors. Root should capture distinct initial behavioral witnesses before replacement, then the same assertions after implementation.

## Exact receipts still needed

1. Root/compiled owner: actual expression transporting EffectiveRunConfig into caller, actual declared meters extraction, ordering/uniqueness validation and world/compiled identity inclusion. Received ENV fact is self.bars_config=level.bars and iteration of self.bars_config.meters/bar.name; no guessed list is needed. Supply whether empty roster is valid (T20 static permits it) and where roster binding is checked on resume.
2. Root: settle proposed new required resolved-only policy transport, version labels and roster identity boundary above. No user approval or optional feature brainstorming needed.
3. Tests author needs exact accepted LaneOutcome/EpisodeCompletion construction fields from prose/JSON receipt for meaningful events; the inspected T20 report names the DTOs but does not list every constructor field. Root can supply the already accepted producer contract without allowing sixth source reads.
4. T23 caller receipt must replace old factory horizon argument, pass resolved options/policy/roster and initialize once. T24 must consume the updated EF identity/native envelope and remove its owned obsolete format path. These remain pending integration gates; T21 does not claim environment meter/reward application or final native release.

No branch, worktree, source copy, helper, subagent, cleanup, commit or push was used. Root remains sole integration/runtime/index owner.

## Root-preferred roster-bound refinement (supersedes marker recommendation if selected)

Root's follow-up prefers binding the actual meter tuple at effective resolution. This is feasible within these files, with required current API changes and explicit external caller maintenance; no new authored knobs or fallback resolver is needed.

Exact proposed APIs:

    resolve_bac_options(options: BaCOptions | None, *, training: TrainingV2Config,
                        declared_meter_names: tuple[str, ...]) -> ResolvedBaCOptions
    resolve_effective_run(base: BrainConfig, training: TrainingV2Config, *,
                          primary_level: str, origins: Mapping[str, str],
                          drive_intrinsic: IntrinsicStrategyConfig,
                          declared_meter_names: tuple[str, ...]) -> EffectiveRunConfig
    build_curriculum(training: TrainingV2Config, *, curriculum_options: CurriculumOptions,
                     static_policy: StaticBaselinePolicy, device: torch.device) -> CurriculumManager

StaticBaselinePolicy required fields become policy_id='static-baseline-v1', difficulty_level=.5, reward_mode='shaped', depletion_multiplier=1.0, active_meters: tuple[str,...]. Remove the proposed active_meters_source marker. OP is the sole semantic owner: validates supplied exact tuple entries/duplicates, constructs the immutable declaration, records baseline values with origin static-baseline-v1 and meter tuple with origin declared_level_meters/reason actual declared level.bars.meters names in declared order. Empty tuple is preserved. Factory directly supplies list(static_policy.active_meters), never reads a level or resolves omissions. EF carries the same declaration, with required serialized static_policy. The omission/provenance owner receives the actual roster even when adversarial is selected; declaration then remains an inactive preserved baseline.

EF.from_dict has the serialized static_policy as its explicit roster transport: validate that current typed declaration, pass active_meters to resolve_effective_run, then validate the entire recomputed payload against supplied bytes. JSON lists must use an explicit JSON/typed decoding route to immutable tuple; strict Python model validation must not accidentally reject the ordinary serialized list representation. No old missing-field fallback. Recomputing identity from serialized inputs is self-consistency validation, not proof that the serialized roster matches a separately loaded world. Current-native consumers still compare the expected effective identity from actual current authoring/world against serialized identity before installation; T24/T23 must publish that receipt.

With static selected, execution payload changes to exactly:

    {'schema': 'effective-run-v2', 'fields': active,
     'exploration': exploration.policy_identity,
     'static_policy': static_policy.model_dump()}

With adversarial selected, omit the static_policy key from this selected projection. Keep static_policy serialized and role-labeled inactive under adversarial. Static reward_mode and active_meters remain unqualified application metadata in field_roles while the explicit static_policy identity projection binds their full values and actual tuple order. Baseline difficulty/depletion/policy_id are derived roles. This avoids using active labels to disguise currently unqualified mechanics. Changing real static roster now changes EF.execution_hash. Under adversarial the actual roster is outside this curriculum-static projection and still requires actual compiled/world identity binding; this is not a claim that adversarial world identity is complete.

Exact existing identity facts, without inference from unseen exploration/compiler source:

- execution_hash = _hash({'schema': 'effective-run-v1', 'fields': active, 'exploration': exploration.policy_identity}). primary_level is serialized but NOT in this hash expression.
- authored_identity = _hash({'schema': 'effective-run-authored-v1', 'brain': self.base_brain.model_dump(), 'exploration': self.exploration.authored_identity}). Its docstring says complete captured brain/training/drive authoring; no inspected expression includes primary_level/bars.
- training_hash = hashlib.sha256(training.model_dump_json().encode('utf-8')).hexdigest(). TC has no bars/meter roster field.
- authored_brain_hash = compute_brain_hash(base), whose imported implementation was not inspected.

Therefore none of these inspected sources proves that an authored_hash binds a compiled level or actual roster. No T03 receipt establishing that fact has been supplied in this dispatch. It would be incorrect to assume the binding. The refined explicit static tuple fixes the selected static-policy identity obligation directly while leaving broader world binding to its named owner.

Required caller impact is finite and honest: every OP/EF resolver caller must pass the actual tuple; direct factory calls resolve first; effective and compiled factory calls transport effective.static_policy and resolved curriculum options. T23/current caller-maintenance owns out-of-inventory call sites. Existing old-signature callers will fail until repaired; no signature default or overload will hide the seam. Tests add two genuinely different static meter rosters yielding different execution hashes and unchanged authored training hashes, serialization roundtrip preserving tuple order/empty tuple, unqualified role assertions, and forged roster with stale execution hash refusal. Existing selected adversarial/inactive baseline role checks remain.

## Final root revision: separate pure options and roster-bound baseline

Root supplied verified caller facts without additional source reads: RP468 and POP525/655 consume the pure OP options resolver without any world/level roster. Therefore the previous proposal requiring roster on resolve_bac_options is superseded. Preserve resolve_bac_options(options, *, training) as the pure current options API; completion-only/v2/provenance changes remain. Add OP-owned resolve_static_baseline_policy(*, declared_meter_names: tuple[str,...]) -> StaticBaselinePolicy as the single fixed-policy semantic owner. ResolvedBaCOptions need not carry static_policy. EF still requires declared_meter_names, calls that baseline resolver and transports static_policy. Direct factory callers explicitly resolve options and baseline, then pass both; EF callers transport both resolved components. Factory resolves nothing. This is component decomposition, not an old-signature adapter. EF static policy field provenance is recorded in its field_roles/derivations; it is not added to pure options provenance. All selected static identity, current serialization, role and external compiler maintenance obligations above remain unchanged.
