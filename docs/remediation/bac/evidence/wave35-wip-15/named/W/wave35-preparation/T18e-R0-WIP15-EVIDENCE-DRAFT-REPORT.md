# WIP15 R73–R81 evidence draft

Status: DRAFT, not publishable. Root owns adoption of the contract, subject and terminal review, final byte checks, selection and publication. No selector/assembler, application runtime, Git/index operation or new implementation-body read was performed for this draft. Historical sealed bytes were preserved.

The finite handoff is evidence-management/wip15-draft/contract.json, terminal-receipt.json, attempt-inventory.json, reference-audit.json and tooling-fix1-pending.json. The last file supersedes provisional tooling metadata in the larger draft receipt; it is not a terminal seal. All paths below are relative to the existing work directory unless explicitly Q.

## Scope and accounting

The proposed interval is R73–R81 over durable base 678513c7540a61114d59a17d1b1e0eb8a06ce0a2. R81 candidate is 4bcb26ec56bc2664949baab7d6b14e3c1da76b01, manifest f16cff139bc7caeb8e4dab7adf995ad5f52f16ca7b058c710bc41f428b8fa80e. Ten authoritative component receipts retain all intermediate candidates, including the additive R76 poison receipt.

The inventory contains 94 Q top-level entries, 292 files, 71 directories including top-level directories, 68 proposed checks: 54 completed command records (35 passed, 19 failed) and 14 UNRUN specs. These are command counts, not unique tests. All 184 receipt path/hash references matched measured bytes; all 54 completed result commands matched adjacent specs and log hashes. Five child receipts matched actual spec/result hashes and candidates. These metadata checks do not replace root selection or runtime verification.

| Round | Completed commands | Passed / failed | UNRUN specs | Test interpretation |
|---|---:|---:|---:|---|
| R73 | 5 | 2 / 3 | 1 | Healthy 9 pass; 8 behavioral failures; API unrun |
| R74 | 4 | 2 / 2 | 1 | 10 pass, 9 fail across executed controls |
| R75 | 3 | 3 / 0 | 1 | Healthy 11 includes the separate fixture case |
| R76 | 10 | 6 / 4 | 1 | 21 distinct runtime cases pass; source review still requested changes |
| R77 | 5 | 2 / 3 | 1 | 45 distinct executed cases: 28 pass, 17 fail; healthy/B4 overlap retained |
| R78 | 1 | 1 / 0 | 2 | Three fixture-repair cases pass; production unchanged |
| R79 | 10 | 6 / 4 | 1 | 53 ordinary plus one poison pass; global gates fail |
| R80 | 6 | 4 / 2 | 5 | 54 collected; four runtime specs held UNRUN |
| R81 | 10 | 9 / 1 | 1 | Root 53+1 and independent 53+1 pass: 54 unique, not 108 |

Nine generated owned specs and the R78 collection template are UNRUN defaults, not proof of execution. Four R80 runtime specs were held after Ruff failures. Every UNRUN record has null actual command/start/end/exit/count/duration and a separate planned command. Collection/static checks do not inflate runtime test totals.

## Custody and dependency closure

Actual replay children at R76/R77/R79/R81 root/R81 independent are separately paired to parent-owned Process PID and actual spec/result/job evidence. Existing witnesses have no literal attempt_id field: local inventory IDs are mappings, not invented child attestation. FIX1 rejects contradictory supplied IDs while preserving this explicit limitation. Current child records include PPID; no retrospective PPID claim is made for old publication records.

Seven runtime helper references are retained: locked harness 180558c2, ordinary verifier b00f16ec, failed verifier aa23117f, static verifier f1b6d694, replay verifier aef826f3, source identity plugin 0a376a64 and capture helper f4c8a6db. Full hashes and bytes are in the receipt. Root's dependency inventory found no missing local imports. The old publication verifier is historical design provenance, not an import dependency of the replay verifier. Generic verifiers do not record their own runtime selfhash; root attests invocation and published-byte equality.

The root freeze observation retains source/config/protected-artifact byte checks and exact execution subtrees without claiming a rerun. WIP14 CI remains Config pass, Lint fail with six known oracle errors, Tests fail with cause/count unknown because raw logs are inaccessible.

Five historical report references were recovered as exact SHA256-matching literal prefixes. Both recovery records and all five snapshots are selected. No original-time snapshot claim is made. The author report's historical API hash is superseded by approved API 1c983b02 and review 0aba60bd, not silently rewritten. The exact reviewed API is now also docs/remediation/bac/CURRENT-REPLAY-CUSTODY-CONTRACT.md; root integration provenance is retained. Publication documentation is distinct from the frozen execution subject.

## Remaining seals and public schema

Root must adopt the contract, reconcile the proposed 68 checks and terminal pointers, freeze an independent qualification subject referencing the exact final contract, and obtain terminal subject/candidate review. review_subject is null and reviews is empty deliberately. No actual publication destination has been chosen here.

The public neutral API is plan(root, work, qualification, contract_path, chain_path, receipt_path, draft=False), then assemble with the exact plan/report inputs. Contract schema is bac-checkpoint-selection-contract-v1; terminal receipt schema is bac-checkpoint-terminal-receipt-v1. The contract retains baseline inventory, ordered WIP13 and WIP14 catalogs with their explicit formats, required component refs, interval and terminal. Future publication schema is bac-checkpoint-publication-v1. Existing contenthash reuse, exclusive destinations and independent terminal subject/byte checks remain required.

FIX1 helper 6fc6845c and tests b0dd9f8a are frozen; public report 13b9190a and root 30-pass observation a50e7b5e are named in tooling-fix1-pending.json. Parent subsequently reports independent scoped approval ac7d85fba3275b1e7eb9183bffa34f6abf1b74818c2f5c33f052ae72c705f132 (8193 bytes), with 30 tests passing in 0.608 seconds. Explicit SOL-medium verification remains pending to settle the prior model-identity limitation. Final neutral process-document hash is separately owned and pending. Preserve initial 28-test observation and failed initial review as history.

Before sealing, refresh provisional tooling/report metadata from the FIX1 supplement and final approvals, align EVIDENCE-PROCESS.md, navigation/index/chain and this checkpoint status, and rehash every selected/reused input. attempt-inventory named_refs is an earlier metadata snapshot; terminal-receipt documents and the FIX1 supplement carry later integration/tooling additions. No stale provisional ref may become a current seal.

Bounded A source and independent actual 54-case R81 execution are supported. Recurrent/caller/BANK/runtime/ENV integration, CUDA implementation/hardware, global gates and package closure remain open. Package accounting stays 28 qualified / 38 remaining / 66 total. The promised 16-worker CUDA server remains unavailable and unqualified.

## Draft bytes at handoff

| Artifact | SHA256 |
|---|---|
| contract.json | ea2351c04b8be5296890dfdf1ed3165aa131a5406302ec5bc87432f7eca35963 |
| attempt-inventory.json | 4c1701b0b53a16e562cde5520d3bab5bdca026e4a2aa857f9c591033879ad918 |
| reference-audit.json | d159dd9b89973ebc03314497cf0133721d696fbccaa48d9f0a3851fdf6ffd2bb |
| terminal-receipt.json | 2f7ba8b12c5a6e52cd78fba25d59fcc33f59da3403facbb1b454ed9a5ea7f8b1 |
| tooling-fix1-pending.json | f545ab3c3ab24b7973111bd2a766a6647de4c82552b54e183ad5c50359d8d28d |

Validation performed: finite JSON/path/hash/spec/result/log reconciliation and jq structural checks only. Actual selector, assembly, application tests and independent review of the proposed terminal subject remain UNRUN by this drafter.
