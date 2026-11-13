# BAC evidence index

Checkpoint publication, bounded component qualification and whole-programme acceptance are separate. The [evidence process](EVIDENCE-PROCESS.md) governs additions; historical evidence is preserved.

## Current checkpoint: WIP17 / R89

The [manifest](evidence/wave35-wip-17.json) and [selection plan](evidence/wave35-wip-17/selection-plan.json) bind executed candidate `8416a6c8f887153d02ce8e19be9328d0fafe661e` to base `e880ab6bd3bd8ec6c16ee6c5ace123b2ed1b6a32`. The [publication guard](evidence/wave35-wip-17/publication-guard.json) records the reviewed core-contract and STATUS prose differences; application source, tests, configurations, scripts and defaults ratchet retain their exact execution identities. Immutable repository paths are in `objects`; `inputs.original` retains logical provenance.

The RNG custody core now supports scoped CUDA admission and idle enrollment, explicit per-invocation device operations, and source-bound local completion with owner-lock, poison and process-identity controls. Its CPU/protocol component is qualified; the production local-GPU contract manifest remains empty. See the [core contract](CURRENT-RNG-CUSTODY-CORE-CONTRACT.md) and [status](STATUS.md). Actual replay producer activation and hardware qualification remain next work.

At R89, **1,515 distinct cases passed: 67 core, 1,290 coherent regressions, 109 replay and 49 owner cases**. Independent Astra execution repeated the same 67 core cases. Two inherited-process fork trials are witnesses within one test, not additional cases. Ten corrected one-job/one-worker child runs have qualified source/process custody. Global Ruff, Black, defaults at600, owned-core types and public-consumer types pass. Global mypy still fails on15 required integration errors: six oracle and nine population-lineage errors.

The finite R86–R89 archive retains **58 logical checks and68 attempts:64 result commands and four unrun templates**, plus the separate failed capture. Original fixture failures and R88 type/default failures remain visible. Ten original two-worker batch jobs genuinely passed pytest but remain rejected for strong child custody and nonqualifying. Nine missing generic custody checks were actually performed later against exact R89 files; all55 original batch files remained unchanged. These later verifications add no test executions or unique passing cases. Corrected terminal runs alone qualify the children.

The plan selects **489 objects:470 new objects /4,690,563 bytes and19 verified reused objects**, with834 input aliases. Four nonexecuted binary/full-index patches preserve intermediate source candidates. Independent terminal review and two scoped metadata reviews passed. [Operational notes](evidence/wave35-wip-17/operational-notes.json) retain the two selector rejections, explicit missing-time explanations and actual later verification. No validator guard or acceptance requirement was weakened.

**28 qualified /38 remaining /66 original packages** is unchanged. Two unavailable-CUDA skips, one required ordinary-runner deselection, global types, actual replay/BANK/ENV/POP/native integration, full/default suites, coverage, slow/learning checks and final fresh review/CI remain required. The offered16-worker CUDA server has not yet been accessed or qualified; its GPU count is unknown. Original absolute execution timestamps remain unavailable; actual elapsed durations and child associations are preserved.

## Publication and history

Before assembly, the exact existing remote branch was verified at WIP16 commit `e880ab6bd3bd8ec6c16ee6c5ace123b2ed1b6a32`. Its Config Validation passed; Lint and Tests failed. Tests completed at2026-11-13 12:43:18 UTC, with its cause still unclassified because raw-log retrieval was unavailable. The local type errors do not establish the hosted Tests cause. WIP17 remote identity and CI are verified after commit/push; neither is inferred from assembly. No PR, merge, release or whole-BAC acceptance is claimed.

The [checkpoint chain](evidence/checkpoint-chain.json) preserves predecessor hashes and earlier records: [WIP16](evidence/wave35-wip-16.json) covers recurrent replay and owner callers; [WIP15](evidence/wave35-wip-15.json) covers shared/flat/PER repair; [WIP14](evidence/wave35-wip-14.json) covers BANK/owner custody; [WIP13](evidence/wave35-wip-13.json) covers pure bootstrap. The previous index remains at `e880ab6bd3bd8ec6c16ee6c5ace123b2ed1b6a32:docs/remediation/bac/EVIDENCE-INDEX.md`.
