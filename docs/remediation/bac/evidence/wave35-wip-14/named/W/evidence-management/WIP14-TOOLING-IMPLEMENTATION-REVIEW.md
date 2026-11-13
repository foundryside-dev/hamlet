# WIP14 tooling implementation review — 2026-11-13

Disposition: changes requested; author notified. Reviewed only the new bac_checkpoint_delta.py and test_checkpoint_delta.py bodies (642 lines combined at initial review), current tooling report, and small existing JSON schema/path facts. The revised design addresses the earlier source/review/membership requirements. A separate frozen qualification subject avoids circular receipt/review hashing; root's explicit final receipt-to-subject comparison remains necessary. No new application acceptance gate is introduced.

## Concrete findings

1. **Passing results are not reconciled.** In the synthetic fixture, changing the terminal PASSED attempt's exit_code to 9 while leaving its structured result at exit 0 still produces READY FOR ROOT PUBLICATION CHECKS. Enforce successful exit for PASSED and reconcile declared exit/count/status with available structured result fields. Missing historical facts must remain explicit rather than invented.
2. **Required child evidence can belong to the failed predecessor.** A qualifying check with failed candidate A and passing terminal candidate B accepts a required child witness for A: membership in any attempt's trees is sufficient. The synthetic mutation produced READY. Bind qualifying child witnesses to the terminal attempt/source (and identify their attempt where retries share a tree); preserve older witnesses separately without letting them satisfy terminal gates.
3. **Partial/interrupted evidence requires invented completion facts.** A historical PARTIAL attempt with null exit/counts is rejected as executed custody incomplete. Preserve genuinely unavailable fields with explicit reasons for partial/interrupted/failed diagnostics; those records must not qualify. Synthetic reproduction confirmed rejection.
4. **No-symlink checks miss direct metadata and root ancestors.** safe/output_path inspect the supplied root itself and relative descendants, but not ancestor components of the root. _lookup directly reads inventory, predecessor manifest/plan and chain without safe(); plan/report output paths bypass parent checks. Apply a shared absolute-component/no-symlink check to these inputs and outputs, retaining exclusive creation and exact hash/size verification.
5. **The published receipt example is not executable contract documentation.** It shows candidate_manifest_sha256 and result_path where implementation requires candidate_manifest and result; it permits null UNRUN terminal pointers while implementation requires an actual indexed attempt ID. Synchronize the example and explicit historical unavailable-custody convention before root authors the final receipt.

Three focused checks used only the existing tiny temporary synthetic fixture, with no application execution or real archive materialization. Their outcomes were respectively READY, READY and ValueError as described above. Author is repairing findings; fresh body hashes, regression results and a bounded rereview are pending. Review is not application qualification or publication approval.

## Bounded repair rereview — 2026-11-13

Disposition: the five findings above are addressed for the documented selection/integrity scope. No remaining blocking finding in this bounded rereview. The original findings remain historical evidence; this disposition applies only to the exact helper/test hashes below.

- bac_checkpoint_delta.py: 433 lines; SHA256 `bf5ea38c2331252ecc74551ebd9e4bc55112addbd5bea4008b50b60aac868cac`.
- test_checkpoint_delta.py: 334 lines; SHA256 `a4e22f6d68d66dc5bbefa8ec290de508cc5dbf0c128009d82065b7152ba18d60`.

Independently ran `python -B -m unittest -q test_checkpoint_delta.py` in evidence-management: 19 tests passed, 0.469 s, exit 0. This executed only tiny synthetic fixtures and synthetic assembly destinations, with no application/runtime qualification or real archive mutation.

PASSED exit and available structured-result fields are reconciled; required qualifying children point to the terminal attempt and source. Historical missing fields remain null with explicit reasons. Absolute ancestor checks cover direct metadata and outputs. The receipt example now uses the implementation's manifest/result/terminal-pointer fields. Explicit check kinds and runtime topology correctly distinguish static/collection records from qualifying runtime custody without inventing pytest counts or workers.

Operational limits remain explicit: root supplies and independently reviews the completeness and truth of the semantic receipt, required child/dependency lists and custody; the helper validates declared relationships and exact bytes, not arbitrary raw-log semantics or reviewer identity authenticity. Root compares final receipt facts with the separately frozen reviewed qualification subject, pins the known WIP13 predecessor, and completes source-equivalence/navigation/staging/publication guards. This tooling review neither seals a final BANK candidate or interval nor qualifies application behavior, package accounting, hardware or CI. Real final receipt selection has not been exercised by this review.

## Actual-data representation rereview — 2026-11-13

Disposition: ready for root's finite receipt review and real final-mode selection, within the same integrity-only scope. Round-two inspection found a shared-directory bypass: mandatory `record` could omit `result`, so a recorded static exit 1 could coexist with a declared PASSED/exit 0. A tiny-fixture reproduction returned READY. The repaired shared-directory closure now requires each executed record's matching result root/path/hash, a distinct record within its declared top directory, and the existing structured-result reconciliation. New tests reject missing results and out-of-directory records. No remaining blocker in this scoped repair review.

Duration-only results retain null absolute timestamps with explicit reasons and actual elapsed seconds; available raw `seconds` must agree. This represents missing historical clock metadata truthfully and does not create UTC evidence or relax application acceptance. Shared top directories retain complete inventories and distinct semantic record/check/attempt identities, with MIXED status for mixed outcomes. Source, process, child and independent-review requirements remain in force. The process draft correctly distinguishes integrity READY from qualification and reserves real selection/materialization for root.

Reviewed seals:

- Helper: 469 lines; SHA256 `33e992e31a2bfcdb0fa70fac315acc92ec3e961831b0d612c2ba8148c16ef8f8`.
- Tests: 389 lines; SHA256 `8af61971bf01a7e2045d344fabad87905af4aaf0b5004418ecf98fa9e13941e2`.
- W/wave35-preparation/r72-docs/EVIDENCE-PROCESS.md: 61 lines; SHA256 `95c787200b0a7f3f4cceaf0cad2b899fcfb9f2053a3ff0fbffd17856f4d3f07d`.

Independent verification: `python -B -m unittest -q test_checkpoint_delta.py`, 21 tests passed, 0.290 s, exit 0. Only synthetic fixtures ran. No real plan, real archive, application test or Git operation was performed. Final subject/attempt-index review remains separate and pending; helper success does not authenticate independently authored semantic facts or replace root's publication guards.
