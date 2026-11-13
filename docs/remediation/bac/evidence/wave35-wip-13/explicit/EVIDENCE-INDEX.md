# BAC evidence index — audited baseline and R58 handoff

This is an additive navigation/index cleanup, not a release or a new qualification. All original files remain in place. Paths below are relative to repository root unless explicitly local. Latest published checkpoint at this audit: `docs/remediation/bac/evidence/wave35-wip-12.json`. R58/WIP13 is a separate local candidate until root finalizes and publishes its receipt.

| Evidence class | Authority and meaning | Current limit |
|---|---|---|
| Original packages | Existing package qualification records, including `evidence/T03-qualification.json`, `T08-qualification.json`, and `wave02`–`wave12` qualification records; WIP12 receipt `package_accounting` | 28 qualified / 38 remaining / 66 total. Component progress does not decrement remaining packages. |
| Bounded components | WIP checkpoint manifests and their named source-bound runtime/review records | Tests prove only the named source, selected behaviors and observed execution profile. Independent repeats overlap owner selections. |
| Whole-programme/final qualification | Required final acceptance and repository/CI records, not any component receipt | Still open: 54 requirements, 22 final review lenses, ordinary runner/direct consumers, applicable full/default coverage≥70/slow/hardware, finite learning and exact-final-remote CI. No all-green release claim. |

## Canonical current receipts and source limits

* WIP12/R54: `docs/remediation/bac/evidence/wave35-wip-12.json#/receipt`, base `b8be82465c06257798247debd08cd7ec3b176699`, candidate `51173768987b6bd451291ca59d90f75cf4bf0b7e`. Root 996 pass / 2 CUDA skips; independent old-owner23 repeats the same 23 cases. Independent native378 is an R52 receipt at candidate `8c401cbc0c4f0b8875d49ba1aaf1e715b1c1bbac`, not R54 execution. Do not add 378 or 23 to 996. CLI34 packs / 35 actual process profiles is a separate check.
* WIP11/R47: `docs/remediation/bac/evidence/wave35-wip-11.json`. Original RNG owner migration evidence; its earlier source remains historical after WIP12. WIP10/R45 standalone core evidence is likewise bounded historical source. Their exact identities are in `canonical-chain.json` and the linked original manifests.
* R58 local handoff: base `93ce825943c104b88a1506a4641e19d1f892466c`, candidate `ef124681f9e1ff9f560b9dfc7da404fcfdeb1c42`. Local `wave35/r58-checkpoint-receipt.json` reports owned56 and independent56 overlapping coherent1052 pass / 2 CUDA skips. The selector checks receipt/candidate and frozen inventories; this audit does not rerun or independently requalify application behavior. The final reviewed receipt is now `wave35/r58-checkpoint-receipt.json`; `wip13-final-plan-v2.json` passed final-mode selection checks. Root still owns publication; selection is not independent application qualification.

## Failed, pending and superseded evidence

* WIP12 retains R53's 23 owner-caller failures and their bounded repairs. Preserve those failures; they are not erased by R54 passing repeats.
* The ordinary DemoRunner native checkpoint test remains OPEN, not waived: required ENV `world_roster/training_seed/lane_world_ids` inputs are missing. It is excluded only from bounded component selection, never counted passing.
* R54 and R58 global mypy20 remains failed: 14 BANK-lineage and six oracle errors. Static custody verification is not an all-green static result. CUDA skips remain unexecuted/unqualified. Latest described prior remote Config pass / Lint fail / Tests fail is historical, not an exact-R58 CI result.
* Native v4 configuration supersedes older native version contracts for current behavior. Old native receipts and prior WIP statements retain historical value but cannot establish current implementation behavior. No compatibility mechanism is implied.
* Actual BANK/CP lineage and locking, native/gradient capture, recovery/final publication, all-provider/both-scope parent, ordinary runner/serving learning and all final programme gates remain required. A passing bootstrap component does not close them.

## Verified archive and navigation

`inventory-v2.json` indexes every archived evidence path by SHA-256 content group, so duplicate paths point to one byte identity. Measured: 14,891 files, 11,792 distinct contents, 296,657,580 bytes; 3,099 duplicate aliases account for 72,563,533 bytes (24.46%). These are audit deduplication opportunities, not permission to delete. Physical filesystem allocation was approximately324 MiB; exact-byte accounting is the reproducible measure.

All 14,809 archived artifact hash assertions across 53 top-level JSON records verified. `canonical-chain.json` provides exact manifest paths/hashes, source identity fields, predecessor record links and scope/accounting pointers. Order is natural checkpoint-label order, NOT a claim of verified Git ancestry. It includes qualification and documentation records; no absent wave labels are invented. Nested source/runtime details stay in their original immutable records.

There are 102 historical references to mutable non-archive documents. Ninety-six have exact bytes already represented in the archive. The other six were resolved and hash-verified against the Git commit that published their citing manifest; see `historical-document-references.json`. This includes one WIP23 contract and five WIP12 current contracts. A present-day path mismatch is not evidence corruption if its exact historical Git bytes verify. No current document was overwritten or copied by this audit.

`inventory-v1.json` is a retained initial diagnostic snapshot: its 19 unsupported-record findings were the older string-digest manifest format, not damaged artifacts. The updated reader accepts that explicit historical shape; `inventory-v2.json` is authoritative for this audit and verifies all records. Retain v1 as a failed diagnostic, never cite it as the current result.

The WIP12 publisher already avoided some unchanged preparation files by comparison with WIP11 originals, but it still gathered a broad round interval, copied helper versions and full progress/tasks/current-state snapshots, and compared against only the immediate predecessor. The new content index checks all archived exact bytes; the WIP13 selector uses only R55–R58 plus explicit additions. It does not execute the old publisher or touch Git.

Use `PROCESS.md` for the finite publication workflow and `ROOT-HANDOFF.md` for integration/verification. All paths named only by basename in this section reside in the local `evidence-management/` handoff directory; root can relocate the short index/process/chain together for publication and adjust those local artifact references.
