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
