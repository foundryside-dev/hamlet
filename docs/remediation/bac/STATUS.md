# BAC implementation status

The implementation plan is approved at SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`; Astra's verdict is [round 03](plan-reviews/round-03.md). Approval starts the autonomous implementation, independent review and repair cycle.

T01 is committed at `bd683e4f9c14840822a0c32213df4a403e62e18c`. It rejects negative widths, nonfinite typed numerics and invalid selected Nesterov settings while preserving zero-width policies, presets, all optimizer choices and gamma zero. Its fresh Astra review approved specification and code quality. Focused checks and the full standing repository gate passed against its exact committed tree: 5599 passed, 15 skipped; all lint/type/configuration/documentation checks passed. This qualifies T01, not all BAC behavior.

T02 schema/transport implementation received independent scoped approval, but its first full gate failed an old exact-field test that omitted the approved encoder addition. The expectation repair is under fresh verification; T02 remains unreleased. A separate nonblocking permanent encoder-transport assertion gap is recorded as P3.

The remaining packages and final acceptance are open. [The finite ledger](acceptance-ledger.json) traces 31 material findings/gaps, 13 contracts, six qualified known items and the separate numerical API candidate. No row is closed solely because a plan or package test mentions it. Dependency-coherent implementation, adversarial checks, fresh final spec/design/source review, joint end-to-end evidence and finite learning qualification remain required.

John approved [historical replay Option A](HISTORICAL-REPLAY-DECISION.md): preserve original artifacts and history for inspection/export; restore compatible learned state and clocks; start qualified learning with fresh replay for old maskless history. Current captured-history full resume remains required. Genuine old uniform/PER/recurrent fixtures have passed independent original-runtime restores; this is fixture evidence, not implementation of the new archive policy.

Completion requires zero unresolved P1/P2 and zero unapproved in-scope capability gaps, executable acceptance at the final candidate, required repository gates and source-verified documentation. Optional P3 work remains separate. Additions/options/complexity are permitted; capability removal, degradation or consolidation requires John or Emmy approval. Emmy has delegated scope-approval and recall/surfacing authority.

Measured capacity is four CPU quota and 16 GiB RAM. Independent checks share that capacity with explicit thread limits and source/fixture preflight. Local CUDA is unavailable and GPU qualification will not be silently reported as passing.

The internal execution ledger is `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/progress.md`. The [reviewed execution addendum](EXECUTION-ADDENDUM.md) is active under [John’s explicit cadence approval](CADENCE-DECISION.md). Package evidence, impact-triggered/full integration gates and all final requirements remain binding. T02 requires an early full suite because configuration serialization/identity changes. The approved plan remains unchanged.
