# T02 implementation receipt

Status: scoped implementation complete; frozen for coordinator full gate and fresh independent review. No staging, commits, pushes, dependency installs, network access, delegation, or extra implementation/test/helper source reads. No claim of whole BAC qualification.

Base HEAD: `5c91dfb9d09b8ba2d422c6fef5c3e468eadfebaf`.
Approved plan: `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` (read extracted T02 brief only, not full plan).
Tracked source diff SHA256: `90c7278b714204065318a51287f3e25bfebed3c30e2ebc9aa414c5996a8548c7` (`git diff HEAD -- src/townlet`). Root staging now includes the new options module in this diff; worker did not change the index. Full five-file identities are captured below and in logs.

## Whole source inventory

Exactly five implementation/test files, 1545 whole lines; no hidden helper/conftest reads.

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/config/brain_config.py | 568 | 6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079 |
| src/townlet/config/training_v2_config.py | 443 | d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68 |
| src/townlet/config/bac_options.py | 243 | 1de08a7cc36c49772254d8b9dc2d8adf3cac76533eecba5c36568745bc48c8f1 |
| tests/test_townlet/regressions/bac/test_options.py | 219 | 1b36cce6095aff8bbccf77164fdbe0a5cfbdebf799ecde450036e9fb3511e200 |
| tests/test_townlet/unit/agent/test_recurrent_token_qnetwork.py | 72 | cfe1b821ded9c815404f721424600c675d88620e9cfc1969c4af34b5559f6ab5 |

Non-source: docs/remediation/bac/options.md plus 134 YAML files: four complete 33-file copies of configs/default_curriculum under configs/test/bac_remediation/{feedforward,dueling,token_set,recurrent}, plus options/modes-0.yaml and options/modes-1.yaml. Exact all-owned file list, linecounts and hashes: sibling `task-T02-manifest.json` (140 files; manifest SHA256 `d9ed31513861af1edde26353d778761c778d13ed0e25f001c4b521aca4a9f35a`). No original authored YAML changed. The coordinator's untracked execution-addendum/review documents are not T02-owned files.

## Preflight and meaningful red

Read AGENTS.md, extracted T02 brief, C01/C02 baseline (within design reference), B01 owner report, complete two bounded existing DTOs, original canonical raw brain/wrapped L0 training/experiment YAML. Used TDD skill. Original complete pack compiled using public `UniverseCompiler().compile(path, primary_level='L0_0_minimal', use_cache=False)` with asserted import path/HEAD before test development. Runtime signature introspection confirmed public signature; root supplied compiled/cache boundary facts without another source read. All 134 positive fixture YAMLs then loaded as complete mapping documents, and collection of final selections succeeded: 136 tests.

Initial test command from /workspace/hamlet:
`PYTHONPATH=/workspace/hamlet/src CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_options.py -q`

Meaningful red: **26 failed in 0.22s**, each at assertion `additive bac_options interface missing`, before importing the not-yet-created options module. Production code did not exist yet. This was absence of the intended additive schema, not malformed fixture/import syntax. The initial test process asserted actual townlet import path; HEAD was verified in the preceding preflight rather than reasserted inside that first red process (process-identity procedural limitation). Final green processes strengthen this with before/after complete four-file hashes and HEAD/diff checks. Six additional encoder omission/geometry and receipt portability cases bring final focused count to32.

First exploratory green:26 passed in71.13s. That run overlapped lint repairs and is not the frozen acceptance evidence. Initial no-defaults failures were repaired without modifying whitelist/ratchet: use Annotated numeric constraints and None omission sentinels, explicit central resolution branches instead of fallback .get/ternaries. No constructor behavioral defaults were added.

## Production and actual integration controls

- Immutable strict finite BaCOptions and nested replay/RND/curriculum/serving/checkpoint/provider/evaluation declarations; unknown keys and compiler geometry reject. All approved literal alternatives present. None is only an omission marker.
- `resolve_bac_options(options, training=...)` returns versioned immutable ResolvedBaCOptions with selected/derived values and immutable per-leaf origin/reason entries. Derived pending capacities accommodate predictor batches; explicit undersized values diagnose. ICM dependent hidden/pending derivations follow explicit feature/batch overrides.
- Drive remains owner of all five provider selections. Count/ICM overrides are typed, RND/adaptive source ownership has explicit training/drive choice. Raw-drive precedence/conflict resolution and actual field roles are expressly T18a work, not falsely implemented here.
- OP defines immutable TokenEncoderOptions(mode, hidden_width) and central resolve_token_encoder; BC imports these and adds optional token_encoder fields for both token-native families. Omitted linear has recorded origin; explicit linear rejects hidden width; interaction_mlp requires positive hidden_width. ICM retains its separate hidden_dim.
- TC adds optional bac_options; old required fields/presets/five overrides/complete level replacement and T01 repairs unchanged.
- Actual integration: generic CompiledUniverse per-level training DTO serialization, from_dict and msgpack save/load preserve authored nested options; brain DTO serialization preserves encoders. No compiler source changes. Each family pack compiled and transport-only brain/training rename compiled again with equal resolved receipts.
- All new literals exercised by the four positive packs, including drop_newest and four evaluation metrics; both aggregators and encoders covered. Unknown keys/nonfinite values, service capacity, encoder width and compiler geometry have negative controls. Unqualified recording criteria and adversarial presets remain retained.
- options.md states units, old-resolution table, active/inactive roles, K02/K04 preservation, and explicitly separates declarations/transport from runtime wiring.

## Superseded pre-contract green evidence

Both final processes used /workspace/hamlet/.venv/bin/python, PYTHONPATH=/workspace/hamlet/src, CUDA_VISIBLE_DEVICES empty, OMP_NUM_THREADS=1, MKL_NUM_THREADS=1 and torch.set_num_threads(1). Two independent one-thread processes, no xdist auto. Both asserted townlet import path, exact base HEAD, tracked source-diff hash, recorded four-file SHA256 inventory, and reasserted unchanged four-file inventory after pytest. Their logs begin with identities.

Focused exact pytest arguments: `--no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_options.py -q`.
Result: **32 passed in71.94s**; sibling `task-T02-green.log`.

Owner/T01 arguments: `--no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_numerics.py tests/test_townlet/unit/agent/test_brain_config.py tests/test_townlet/unit/agent/test_loss_factory.py tests/test_townlet/unit/agent/test_network_factory.py tests/test_townlet/unit/agent/test_optimizer_factory.py tests/test_townlet/unit/config/test_training_v2_config_dto.py -q`.
Result: **104 passed in70.16s**, two expected PyTorch zero-element tensor warnings for preserved constant-policy witnesses; sibling `task-T02-owner-green.log`. This is40 T01 regressions plus64 B01 owner tests, executed without opening their sources.

Scoped `ruff check` and `black --check` on the four files passed. Scoped `mypy` on three production files passed. Repository `scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet` passed, **614 whitelisted at unchanged614 ceiling**, no new non-whitelisted violations.

## Limits and remaining coordinator work

Root owns full repository gate, immutable snapshot/fresh other-model review, frozen-live-input regeneration, staging/commit. Those are not claimed run by this worker. No whole-BAC/runtime learning qualification, GPU, coverage, final detached gate, compiler CLI/doc-generation gate was run here. Existing hash functions remain untouched; adding serialized optional encoder fields can alter old native DTO hashes, and T03a owns recorded native identity adaptation. Effective-run receipt persistence and active field-role maps belong T03/T18a; runtime option consumption belongs later tasks.

All newly owned fixture directories contain YAML files only; tests compile temp copies and write explicit cache files under pytest temp. Existing configs/default_curriculum has five .compiled/universe-{level}.msgpack files. Initial preflight compiled the original with use_cache=False; absence of a before-timestamp inventory means this receipt does not assert those old caches were untouched. Do not stage generated .compiled artifacts. No original authored fixture content was modified.


## P4 contract repair (current candidate)

Coordinator caught an implementation mismatch before publication/gate: the first draft used encoder type/hidden_dim in BC; approved P4 specifies mode/hidden_width in OP. Corrected the implementation, both token-native fixture encoder declarations, documentation and tests to the approved interface. No alias preserves the erroneous unpublished spelling. BC imports/re-exports OP's declaration/helper for its field types. ICM's independent hidden_dim remains untouched. Encoder runtime consumer is T17 (corrected the earlier documentation's mistaken T04 reference). Inspected owned replay schema against the extracted exact brief: sampling_mode, uniform_sequence_adapter, fixed_full/adaptive_prefix, whole_episode/transition_tail, window_mean/anchor_transition and max_abs/mean_abs all match. No additional literal discrepancy found.

Contract red was run before repair with exact HEAD/source-diff and import-path assertions in that process: pytest test_options.py -k 'token_encoder_contract or encoder_schema_is_portable_option_interface or encoder_omission or encoder_geometry'. **6 failed,12 passed,17 deselected in0.15s**. Failures cover both families rejecting approved mode/hidden_width, missing mode on omitted resolution, and missing OP declaration. Log: task-T02-contract-red.log. Negative controls also explicitly reject draft hidden_dim/type keys and compiler-owned geometry.

Current frozen source inventory/hashes are the table above; manifest is regenerated for all139 owned files. Final preflight loaded all134 YAML documents, asserted OP's exact two schema fields mode/hidden_width, and collected35 focused tests. Scoped ruff/black/mypy passed; global no-defaults guard passed unchanged614. Current green logs and results follow; prior32/104 logs above are superseded by the repaired candidate's checks.


Current acceptance evidence: **35 passed in66.80s** in task-T02-contract-focused-green.log; **104 passed in65.08s**, two expected constant-policy warnings, in task-T02-contract-owner-green.log. Exact pytest selections and environment are identical to the prior frozen commands above, with35 focused cases now. Both new processes assert the current HEAD/diff/import path, log all four current file hashes, and assert unchanged hashes after pytest. Source remains frozen for coordinator snapshot/full gate/independent review. No stage/commit performed.


## Full-gate expectation repair (current candidate)

Coordinator reported the stopped, non-passing full gate: qualification/T02-full-tests.log,1 failed2861 passed9 skipped interrupted after549.24s. Failure: tests/test_townlet/unit/agent/test_recurrent_token_qnetwork.py::test_recurrent_schema_is_only_the_token_native_contract. This does not establish a production defect. Root explicitly expanded the bounded inventory to that exact72-line module (five total files,1545 actual lines); no imported helper source was read.

An initial harness attempt stopped before pytest because root staging changed source diff identity by including the new OP module. HEAD and all prior four file hashes were unchanged. Corrected harness expectation to current90c7278b… and verified those hashes. Exact node red then reproduced **1 failed in0.05s**, extra token_encoder relative to its four-field assertion; task-T02-schema-red.log. Changed only its exact-field set to require token_encoder alongside all four original names. No source behavior, other strictness assertion, helper or forward test changed. Full module green: **5 passed in0.17s**, task-T02-schema-module-green.log.

Separate P3 qualification gap remains recorded and unfixed as instructed: the compiled-family round-trip test asserts training options and selected architecture family, but does not explicitly assert compiled encoder option equality across every cache/rename step. Direct encoder DTO tests establish authored validation/round-trip; they do not substitute for that missing compiled-encoder assertion. No additional cleanup or expanded guarantee is claimed.

All five scoped files pass ruff and black checks; the three production modules pass mypy. Global no-defaults guard remains614 at unchanged614 ceiling. Full root gate must be rerun on a fresh immutable candidate; the earlier interrupted run is not a pass.

Current five-file acceptance reruns: **35 passed in65.30s** (task-T02-schema-focused-green.log), **104 passed in75.97s** with two expected zero-width warnings (task-T02-schema-owner-green.log), plus the **5 module tests passed** above. These latest runs supersede the previous four-file35/104 checks for candidate qualification. Commands are the same focused and owner selections already recorded; all three latest processes assert exact import path/HEAD/current source diff and before/after five-file hashes. The fifth file remains72lines, so actual bounded context is1545lines. Current all140-owned-file manifest SHA256 is `d9ed31513861af1edde26353d778761c778d13ed0e25f001c4b521aca4a9f35a`. Worker performed no staging or commits. Candidate frozen again for coordinator immutable snapshot, fresh bounded review and full-gate rerun.
