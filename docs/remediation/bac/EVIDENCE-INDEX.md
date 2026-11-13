# BAC evidence index

This index points to immutable source-bound evidence. Checkpoint publication, bounded component qualification and whole-programme acceptance are separate. Historical records and backups are preserved; the [evidence process](EVIDENCE-PROCESS.md) governs new additions.

## Current checkpoint: WIP14 / R72

[WIP14 manifest](evidence/wave35-wip-14.json) and [selection plan](evidence/wave35-wip-14/selection-plan.json) bind executed candidate `c4b3765a1b9734a82b1a7eaaccbb1489da23d9bc` to base `1ccc9982cc402bcbe328974962cd8ecb8e12d7b6`. The manifest links the sealed receipt, independent application/evidence reviews and [publication source guard](evidence/wave35-wip-14/publication-guard.json). Its `objects` table gives immutable repository paths; `inputs.original` maps historical absolute provenance paths to those content hashes. Absolute paths in raw records are not portable runtime dependencies.

- Managed BANK/CP restore and atomic owner capture: **bounded CPU component qualified**. Combined selection: **1,290 passed, two unavailable-CUDA skips**. Independent Astra: **155 passed**, overlapping the combined selection; do not add those counts.
- Compiler fleet: **34 packs / 35 actual process profiles passed**. Source/process custody and thirteen combined/four independent fault-injection children are verified.
- Global Ruff, Black, expression documentation, defaults ratchet (600) and owned BANK/CP typing pass. **Six oracle-driver type errors remain.** One known ordinary-runner case was deselected only from this bounded component selection and remains required.
- **28 qualified / 38 remaining / 66 original packages** is unchanged. Full current-parent replay/network/optimizer/scheduler/curriculum restoration, joint all-child publication/failure handling, runner/oracle integration, full-repository coverage ≥70%, slow/applicable hardware and learning checks, fresh final 54-requirement/22-lens review and exact-final-remote CI remain open.

The checkpoint retains R59–R72: **88 checks / 92 attempts** (45 passed, 22 failed, 20 unrun, four diagnostic, one partial). Failed attempts, R64 premature launches, R65 unexecuted partial work, GC attribution and superseded sources remain represented. R64/R67 component receipts retain their own source identities. CUDA is unqualified. Older harnesses recorded elapsed duration without absolute UTC start/end; this limitation is explicit, with no invented timestamps.

The incremental plan contains **584 unique objects: 575 new objects / 10,150,788 bytes and nine verified existing objects**. It preserves 1,157 logical input aliases without rebuilding the historical 296,657,580-byte baseline. Selection/integrity approval is not a passing application, repository or CI result.

## Publication and history

Remote/CI verification is performed against the actual publication commit; it is not inferred from a passing local component or an assembled manifest. Immediately before this assembly, the exact remote branch was verified at WIP13 commit `1ccc9982cc402bcbe328974962cd8ecb8e12d7b6`. Its Config workflow passed; Lint failed on then-existing BANK14/oracle6 errors and Tests failed with individual signatures unavailable. Log retrieval limitations are retained. These are historical WIP13 results, not WIP14 CI results.

[Checkpoint chain](evidence/checkpoint-chain.json) retains every earlier entry and predecessor hash. [WIP13](evidence/wave35-wip-13.json) binds R58 pure bootstrap; [WIP12](evidence/wave35-wip-12.json) binds R54 native configuration/current owner fixtures; [WIP11](evidence/wave35-wip-11.json) and earlier records retain their original scope. The previous index is preserved in Git at commit `1ccc9982cc402bcbe328974962cd8ecb8e12d7b6:docs/remediation/bac/EVIDENCE-INDEX.md`. Earlier source counts, type failures and qualification statements are historical, not current findings or additive case totals.
