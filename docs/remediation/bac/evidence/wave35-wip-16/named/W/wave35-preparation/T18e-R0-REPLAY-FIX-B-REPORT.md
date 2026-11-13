# Recurrent replay repair B — tests-only freeze

2026-11-13. Author implemented only the new regression module after root's explicit test-writer grant. WIP15 base supplied by root: commit `29d0204a70b6eef0017b3cee638812e2cc5c7899`, tree `f71ae2bdee57ebf7e5949f02e40cbc1b91a4c83d`. Four retained bodies still exactly match R81 source hashes. No production changes, application imports, pytest, mypy, Git/index/remote actions, source copies, new worktrees/branches/checkouts, deletion or delegation occurred. New test source is now FROZEN; root owns capture/runtime and any next writer transfer.

## Source budget and actual checks

Five admitted whole bodies total4304 lines, below hard5000 and planned4921. New module577/900. Original four total3727 remain unchanged. The accepted preflight remains the source investigation; no sixth implementation body was opened.

| Body relative to /workspace/hamlet | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/training/sequential_replay_buffer.py` |1884|`b29a5be9b48c99180ef64730802f041cf4536b30b8771d2ad945ceca7569bad6`|
| `src/townlet/training/replay_contract.py` |374|`8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1`|
| `src/townlet/exploration/rng_custody.py` |371|`9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`|
| `tests/test_townlet/regressions/bac/test_replay_rng_custody.py` |1098|`5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7`|
| `tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py` |577|`be1d4a56c30c4aa6bd797904a8d8f6ca7502059dcda992d3132fc06d2e2abadb`|

Permitted development commands actually executed against the final new test bytes:

- `.venv/bin/ruff check tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`: exit0, `All checks passed!`.
- `.venv/bin/black --check tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`: exit0, `1 file would be left unchanged.`

No runtime or collection result is claimed. Static parameter expansion gives54 prospective cases:12 intended malformed-DTO RED,41 ordinary controls expected already passing,1 isolated child control. Actual pytest collection/node identity and fixture behavior remain for root to verify. Repeated selections must not be counted as additional distinct controls.

## Causal assertions and fixture prerequisites

B1's12 intended failures are10 captured cases (uniform/prioritized × NaN reward, nonterminal all-false successor mask, negative transition ID, invalid fragment offset, unexpected row key),1 mutated nested priority provenance,1 mutated inspection row. They obtain the real public validation DTO, mutate ordinary returned data and require materialization to refuse before authority issuance while complete replay data/health remain unchanged. Current source is expected to issue these malformed DTOs; expected RED is a missing ValueError, not a signature/import/fixture error. No claim of runtime confirmation is made yet.

Current width uniform/priority controls validate width1, genuinely clear/store width2, and require both fresh serialized preparation and old DTO materialization to reject without state change. Inspection retains a genuine width1 archive: it checks fresh width2 mismatch refusal and successful still-compatible DTO restoration. This intentionally differs from the uniform width2 repopulation schedule because inspection preserves its archive. Width rejection is existing behavior, not a fix B will claim. Legacy mutation targets selected `original_state`, whose archive validation should already reject; valid legacy5 remains archival, inspection remains active inspection, and captured6/7 remain valid active restores.

B4 uses real recurrent storage/sampling and actual domain lineage. Same-held outer preparation/install must work; real sibling uniform sampling and same-owner storage invalidate publication through distinct currency/revision checks. Constructors/registering peers happen before held outer operations. Staging faults delegate actual episode clone, real archive merge, policy copy or priority reconstruction, then raise; full live data/health must remain unchanged, followed by fresh preparation/install and a real healthy sample. Archive fixture builds a real legacy5 archive through normal serialized loading. Partial publication raises at the actual `_configured` assignment after count and episode deque have changed from3 to6 rows; stable counters still show the uncompleted suffix. All managed operations then refuse quarantine, including clear/serialize. Alias controls mutate source tensors/options before install and retained candidate episode bytes/metadata, policy, priority arrays/initialization/generator after install, requiring installed data to stay independent.

B3 exercises both real priority-update and store-refresh routes with all5 exact supported NumPy engine families and both successive/independent laws:20 controls. A real qualified sample first establishes a populated length2 priority domain. Transparent instrumentation delegates the actual selected sample_units call and observes a distinct disposable engine with advanced complete state, beta0 and batch1. Every support operation must preserve complete Python/global NumPy/Torch CPU and persistent generator state while producing a real changed priority/episode result. A separately constructed, equivalently operated owner then provides the next real selection/receipt and complete generator-continuation comparator. This retains actual scratch sampling; it is neither literally RNG-free nor a substitute sampler.

Imports use the already inspected `test_replay_rng_custody` sibling's fixture/comparison helpers and the supplied bootstrap wrapper protocol. Root's normal pytest prepend/import environment must make these sibling modules available without test-inserted sys.path changes. Tests add no bootstrap/helper source body. The new module has its own ambient-restoring fixture because sibling module import does not enroll that module's autouse fixture. Physical replay comparisons include complete episode values, transport, capacity/device, configuration/options, count/identity counters and health; authority revision/domain currency may conservatively advance after refusal and are intentionally not treated as replay data. Owner subclasses only observe genuine issuance or inject a selected assignment exception; no production test hooks exist.

The child performs actual healthy-owner scratch update/store after public poisoning of its own authentic lease, then checks sample/new preparation/preissued installation refusal and clear nonhealing. It remains separate from the existing `replay_poison` role. Exact protocol is published in `T18e-R0-REPLAY-FIX-B-CHILD-API.md`; external verifier admission is pending, so the child is not execution-qualified by this report.

## Exact prospective node inventory

Every suffix below is relative to `tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py::`. Parameter IDs follow the explicit/decorator order in source; root must verify them in actual collection. “Existing control” means expected alreadyPASS on current source, not an execution result.

- `test_recurrent_validated_width_rechecks_current_destination[uniform]` — existing control.
- `test_recurrent_validated_width_rechecks_current_destination[priority]` — existing control.
- `test_recurrent_validated_width_rechecks_current_destination[inspection]` — existing control.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[nonfinite-uniform]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[nonfinite-priority]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[successor-uniform]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[successor-priority]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[transition-id-uniform]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[transition-id-priority]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[fragment-offset-uniform]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[fragment-offset-priority]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[extra-row-key-uniform]` — intended B1 RED.
- `test_recurrent_mutated_captured_dto_cannot_gain_authority[extra-row-key-priority]` — intended B1 RED.
- `test_recurrent_mutated_priority_dto_provenance_cannot_gain_authority` — intended B1 RED.
- `test_recurrent_mutated_inspection_dto_cannot_gain_authority` — intended B1 RED.
- `test_recurrent_legacy_selected_original_state_is_revalidated` — existing control.
- `test_recurrent_valid_dto_preserves_selected_restore_capability[uniform]` — existing control.
- `test_recurrent_valid_dto_preserves_selected_restore_capability[priority]` — existing control.
- `test_recurrent_valid_dto_preserves_selected_restore_capability[inspection]` — existing control.
- `test_recurrent_valid_dto_preserves_selected_restore_capability[legacy]` — existing control.
- `test_recurrent_same_outer_lineage_can_prepare_and_install[uniform]` — existing control.
- `test_recurrent_same_outer_lineage_can_prepare_and_install[priority]` — existing control.
- `test_recurrent_nested_preparation_refuses_intervening_work[sibling-sample-uniform]` — existing control.
- `test_recurrent_nested_preparation_refuses_intervening_work[sibling-sample-priority]` — existing control.
- `test_recurrent_nested_preparation_refuses_intervening_work[owner-storage-uniform]` — existing control.
- `test_recurrent_nested_preparation_refuses_intervening_work[owner-storage-priority]` — existing control.
- `test_recurrent_staging_fault_preserves_live_state_and_healthy_use[episode-copy]` — existing control.
- `test_recurrent_staging_fault_preserves_live_state_and_healthy_use[archive-merge]` — existing control.
- `test_recurrent_staging_fault_preserves_live_state_and_healthy_use[policy-copy]` — existing control.
- `test_recurrent_staging_fault_preserves_live_state_and_healthy_use[priority-copy]` — existing control.
- `test_recurrent_partial_publication_quarantines_all_managed_routes` — existing control.
- `test_recurrent_install_owns_input_and_retained_candidate_material[uniform]` — existing control.
- `test_recurrent_install_owns_input_and_retained_candidate_material[priority]` — existing control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-successive-PCG64]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-successive-PCG64DXSM]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-successive-MT19937]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-successive-Philox]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-successive-SFC64]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-independent-PCG64]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-independent-PCG64DXSM]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-independent-MT19937]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-independent-Philox]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[priority-update-independent-SFC64]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-successive-PCG64]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-successive-PCG64DXSM]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-successive-MT19937]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-successive-Philox]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-successive-SFC64]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-independent-PCG64]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-independent-PCG64DXSM]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-independent-MT19937]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-independent-Philox]` — existing scratch control.
- `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[store-refresh-independent-SFC64]` — existing scratch control.
- `test_isolated_recurrent_scratch_work_cannot_heal_common_poison` — isolated existing-boundary control; verifier admission pending.

## Pending production and acceptance

Root must first verify fixtures, seal source and witness genuine malformed-DTO RED, then separately grant production writes. Planned production scope remains public `materialize_validated` owning/revalidating selected DTO transport against current target; a bounded reconstruction helper; recurrent policy ASG002 line814; scratch classification wording and Black formatting. Shared identity-only authority, static typed guard signatures, existing sampling algorithms and all archive/inspection/adapter capabilities remain unchanged. B3 classification and already-correct B4 controls do not justify speculative production changes.

B6 CUDA design/implementation/hardware, external caller/BANK/ENV migration, retained and broader checks, independent reviews and final programme gates remain open. No implementation completion, package acceptance or programme GREEN is claimed. Accounting stays28/38/66.


## R82 retained results and tests-only correction round1/5

2026-11-13. This appended section supersedes only the earlier current-source/count and UNRUN statements for their respective versions; the original report bytes are preserved exactly in `T18e-R0-REPLAY-FIX-B-REPORT-V0-SNAPSHOT.md`, SHA256 `1c89987fbf210ee88811fbb728bd997abb097edf3b41f66de929896045caebe9`. Initial child API bytes are similarly preserved in `T18e-R0-REPLAY-FIX-B-CHILD-API-V0-SNAPSHOT.md`, SHA256 `a5e327d4ca409f6c7c29e6ddf825f7201a053e3ed3b2c4d92cc95ba3c288c89e`. These are authorized prose snapshots, not source execution copies. No prior evidence or failed result was removed.

Root's authoritative R82 receipt `../wave35/r82-recurrent-tests-receipt.json` and independent reviewer addendum establish54 collected;8 fixture PASS;33 ordinary controls with31 PASS/2 FAIL;12 malformed DTO cases all failing with intended missing ValueError. Total53 unique runtime cases39 PASS/14 FAIL; child UNRUN. This is attributed root evidence, not author execution. Source/process custody816/573/13/14 MAIN1 is reported verified, sessions closed. R82 tree `690c51f8a89653b9bdcf4b52c002b3fe73c7f27c`, base `29d0204a70b6eef0017b3cee638812e2cc5c7899`, manifest SHA256 `8c8b157d1dc4c47472bc039812fbc9146758d342bc4ce7547a668011438783ee`. The malformed-DTO omission now has causal RED evidence. The two additional failures were unsupported assignment to frozen ReplayOptions, not a production alias defect. Read initial independent review SHA256 `fb76a7b0891b8b5548483519c531c8ddae052895b997a3070f4b37db706c9879` and R82 addendum SHA256 `7248b65d0d27e16f26e5e1a279d229d818e3da46116efa39bb39b75dffe1595d`.

Under the separate tests-only grant, changed only `tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`. Final640 lines (+63 net from R82), SHA256 `1044513adaab42b3d6caef624cd4b3e6d70298ed3096f5dfe3dd4de0f32ad5b0`. Other four whole bodies remain exact hashes/lines in the earlier table:1884/374/371/1098; total4367/5000, newtest640/900, projected cap4921 unchanged. Production/shared/domain/oldtest are unmodified. No sixth body, pytest/application imports/mypy, Git/index/remote actions, new checkout/branch/worktree, source execution copy, deletion or delegation occurred.

Scoped diff data (three source regions; all other test bodies unchanged):

- New `test_recurrent_captured6_dto_adapts_to_prioritized_destination` starts257: adds34 lines including spacing. Real format6 uniform source goes through destination public validate→materialize→install after that prioritized destination has already sampled. Checks all incoming active transport fields, resulting format7, exact captured6 adapter provenance, retained alpha/beta/tick/origin/complete RNG, reset maximum/empty domains, then real selected sample with hand-specified possible rows, legality, population2, persistent RNG advance and ambient preservation.
- Existing `test_recurrent_install_owns_input_and_retained_candidate_material` starts424: replaces one unsupported policy assignment with distinct policy-object assertion, genuine `pytest.raises(ValueError, match="frozen")` assignment refusal, and unchanged policy-value assertion. Net+3 lines. All subsequent real mutable candidate priority arrays/initialization/generator mutations and complete installed-state comparison remain. No reflection/immutability bypass and no assertion removal.
- `_scratch_work` starts452: net+26 lines. Snapshots actual pre-state, locates the selected real unit ID, requires its prior priority differ from7+epsilon, then asserts the complete priority vector changes only that slot to7+epsilon while IDs/windows/episodes remain. Store-refresh compares preserved old episodes and explicit appended observations/successors/rewards/actions/dones/masks/recorded flags and episode/transition identities; checks the complete expected four length2 window keys and stable unit IDs. Retains scalar count/max checks. Transparent real sampler observation, scratch advance, persistent/ambient preservation and continuation comparator are unchanged.

New/changed nodes, all suffixes relative to the new regression module:

- NEW `test_recurrent_captured6_dto_adapts_to_prioritized_destination` (1 existing-capability positive control).
- CHANGED `test_recurrent_install_owns_input_and_retained_candidate_material[uniform]` and `[priority]` (2 fixture corrections; actual repaired outcomes UNRUN).
- STRONGER `test_recurrent_support_draw_preserves_ambient_and_persistent_stream[WORK-MODE-FAMILY]`, all20 exact prior suffixes enumerated above: WORK priority-update/store-refresh, MODE successive/independent, FAMILY PCG64/PCG64DXSM/MT19937/Philox/SFC64. Only the delegated `_scratch_work` assertions changed; algorithms are unchanged.
- STRONGER shared-helper effects in `test_isolated_recurrent_scratch_work_cannot_heal_common_poison` (1 child node). Role/message/module map/parent protocol unchanged; child still UNRUN by author.

Prospective inventory now55 cases:12 retained intended DTO RED,42 ordinary controls,1 isolated child. Actual collection remains for root; no new runtime result is claimed. Suggested narrow root validation is the23 alias/scratch/adapter cases plus the separately qualified child, preserving R82's existing causal RED and passing unchanged controls as source-bound history before any broader repeat. Production-write grant remains outstanding.

Development checks actually rerun on final corrected bytes:

- `.venv/bin/ruff check tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`: exit0, All checks passed.
- `.venv/bin/black --check tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`: exit0, one file unchanged.

Tests-only source now FROZEN and writer relinquished to root. Child current-source capsule is appended separately; root owns R83 capture, actual tests/child custody and independent readiness review. ASG002/Black production repair, B1 implementation, B6/callers/hardware and programme gates remain open; accounting28/38/66 unchanged.


## Production1 implementation — source freeze after R83 readiness

2026-11-13. This is the first B production implementation after tests readiness, triggered by the original12 R82 missing-ValueError failures; it is not a restarted design/fix loop. Read the production grant, accepted preflight, R82/R83 receipts, scoped fixture review and skill fix-loop reference. Root restrictions retain all runtime, capture, index/Git and independent review ownership. Prior report bytes preserved exactly in `T18e-R0-REPLAY-FIX-B-REPORT-V1-SNAPSHOT.md`, SHA256 `e81b4e67e0093072efa939d117cba875d40c320d357aaf7492c8bea38f5cb578`; V0 snapshot/history remains intact.

Root R83 receipt `../wave35/r83-recurrent-fixture-fix-receipt.json`, SHA256 `b860548d7e8e3955c3e0506df6e3298108d336f4683fdf83d60a6d5381a96e4e`, records55 collected and23 amended/new ordinary cases plus1 actual isolated child PASS. Strong child custody pairs PID60791/PPID60759 with parent60759; full816/573/13/14 MAIN1 custody verified. Scoped independent readiness review SHA256 `a93e68c48233be76b48034775ff1615937fa86b29a9b8630a3dff39a096d0254` approves the three fixture corrections and finite CPU scratch/poison control. These are attributed tests-only results, not fixed-production GREEN. Original12 R82 causal failures remain the repair trigger.

Only `src/townlet/training/sequential_replay_buffer.py` changed in this production step. Tests remain640 lines at exact R83 bytes; no new test nodes or helper/source bodies. Final whole packet4413 lines; sequential1930/2100, shared374/450, domain371/371, retainedtest1098/1100, newtest640/900. No application imports/pytest/mypy, source execution copies, Git/index/remote changes, new branches/worktrees/checkouts, deletion or delegation occurred.

| Body relative to /workspace/hamlet | Final lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/training/sequential_replay_buffer.py` |1930|`e261a0caca68c74cc36bdb9469b126aa0bdae38eeababf358a20bf96f8373317`|
| `src/townlet/training/replay_contract.py` |374|`8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1`|
| `src/townlet/exploration/rng_custody.py` |371|`9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`|
| `tests/test_townlet/regressions/bac/test_replay_rng_custody.py` |1098|`5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7`|
| `tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py` |640|`1044513adaab42b3d6caef624cd4b3e6d70298ed3096f5dfe3dd4de0f32ad5b0`|

### Exact change and self-review

- Added `_validated_transport`699–747: checks the actual DTO class/capacity, then reconstructs owned selected material. Legacy archival DTOs clone their selected `original_state` mapping, preserving mapping representation. Inspection reconstructs its actual mutable active episodes plus archives as the existing inspection envelope; absent optional legacy reward components receive their established explicit None transport encoding. Required keys, unexpected keys, row values and device/dtype remain visible to validation. Captured DTOs reconstruct complete format6 metadata and selected episodes; original priority presence selects format7 with the existing complete priority/RNG/provenance encoder. It does not materialize format6 through an adapted format7 state prematurely.
- `materialize_validated`821–825 now calls this helper, then the complete existing `_validate_serialized` against the current target, then `_materialize_serialized`. The shared `@replay_prepare` still holds the actual domain-before-owner lock through reconstruction, validation and issuance. Caller-mutated row masks/values/IDs/fragment metadata, extra row keys, inspection rows and priority provenance therefore reach the same full validator that originally approved them. No original saved captured/inspection transport is substituted to conceal the mutations. No new handle/default lineage/compatibility mode is introduced.
- `load_prepared` policy staging854–856 now takes the actual optional policy and explicitly copies it when present. This removes the reported conditional-None ASG002 expression without ratchet/whitelist changes and preserves the unconfigured policy-None case. All staged publication, token checks, quarantine and clone ownership remain unchanged.
- `_support`1100–1105 documents the real disposable-generator draw as ambient- and persistent-stream-preserving. Existing `_clone_rng`, selected sample_units call, owner-only exclusion, algorithms and post-common-poison boundary are unchanged. No literal RNG-free claim, suppressed draw, domain acquisition under owner lock or status lookup was added.
- Black reformatted the recurrent file's existing long/short layouts, including method signatures and predicates; these are formatting changes only. Net source growth46 lines from1884 to1930. Shared contract/domain/retained tests/new tests remain byte-identical to the admitted starting snapshot.

Self-review traced all12 causal DTO damage cases through the new owned reconstruction and the real rejecting validators. It also traced valid archived5/inspection/current6/current7, configured/unconstrained identity checks and the actual captured6-to-prioritized `_restore_priority(None)` branch. Captured and inspection cloning preserves tensor devices before validation; materialization moves only validated owned rows afterward. Inspection's explicit optional-absence encoding is existing format serialization, not a fallback for missing required data. Common domain/owner currency, identity-only issuer material and typed mandatory lineage remain owned by the unchanged shared implementation. The already-correct width guard is characterization and is not represented as a repaired defect.

### Actual development verification and remaining gates

Commands executed by author:

- `.venv/bin/black src/townlet/training/sequential_replay_buffer.py`: exit0, recurrent file reformatted.
- `.venv/bin/ruff check src/townlet/training/sequential_replay_buffer.py tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`: exit0, All checks passed.
- `.venv/bin/black --check src/townlet/training/sequential_replay_buffer.py tests/test_townlet/regressions/bac/test_recurrent_replay_rng_custody.py`: exit0, two files unchanged.

No fixed-production runtime/type/defaults-ratchet result is claimed. Existing12 causal cases and the complete retained/new replay controls cover this change; root owns their captured fixed-source execution, static/type/defaults checks, child requalification and independent source review. The public delta is in `T18e-R0-REPLAY-FIX-B-CURRENT-API.md`, independently reviewable with these exact bytes. The R83 child capsule's test module hash/role/message/import map is unchanged, but any new qualified child must bind the new production source through a fresh manifest.

Source is now FROZEN and sole-writer authority relinquished to root. No new source supplier fact is required for this implementation. Arbitrary callback/subclass/library internals remain outside the finite ordinary-data profile; CUDA/B6, external callers/BANK/ENV, broader suites and programme gates remain open. No self-approval, full replay acceptance or programme GREEN; accounting28/38/66 unchanged.
