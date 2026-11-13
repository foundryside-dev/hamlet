# BAC checkpoint evidence process

This process governs additive evidence publication. It does not waive application review, package qualification, coverage, hardware, type, final CI or exact remote-identity gates. Preserve historical artifacts, failures, attempts, commits and registered worktrees. Evidence integrity is separate from acceptance and publication approval.

## One authoritative record per candidate and check

1. Freeze the source that actually ran: base commit, candidate tree, execution subtree identities and SHA-256 inventories for source, configuration and protected artifacts. Record publication identity separately; a later publication tree cannot substitute for the execution tree.
2. Keep one authoritative check record with immutable attempts and an explicit terminal attempt. Retain failures, interruptions, diagnostics, partial results, unrun attempts and retries. Each attempt identifies its own candidate manifest/base/tree, command or unrun reason, observed result or explicit unavailable reason, actual environment/hardware and process/import/thread custody. Same-byte evidence reuse proves bytes, not execution of newer source.
3. Seal the finite checkpoint contract before freezing the terminal qualification subject and obtaining independent terminal review. Then seal a receipt binding that contract, exact candidate, attempt inventory and terminal pointers, required components, reviews, overlap-aware accounting, remaining failures and required next work. A changed sealed input requires a new linked seal and plan; never overwrite earlier evidence.
4. Store exact artifact bytes once, retaining every logical alias and original producing path. Reuse requires verified immutable path, size and SHA-256. Same-name changed bytes form a new object. Bind approved documents and reviews to exact bytes; a mutable CURRENT pathname alone is insufficient.
5. Select only the explicit interval and named dependencies/components. Include required helper/verifier versions and their named closure. Preserve every selected failed, unrun and partial result; do not recursively copy old waves, mutable progress state or unrelated helpers.
6. Root reviews qualification, source/custody, terminal review and approved document bytes independently. After integrity selection, root rehashes selected inputs and reused targets, materializes new objects exclusively, verifies destination bytes and writes the authoritative checkpoint record. Selector or assembly success alone authorizes neither acceptance nor Git.
7. Root appends the new chain entry and updates the maintained evidence index without rewriting history. Publish a short status delta with exact tested identity, bounded result, retained failures, remaining gates and next work. Separately verify the exact remote identity and CI after the authorized publication action.

## Historical checkpoints and the next interval

WIP13 is the immutable R55–R58 checkpoint: `docs/remediation/bac/evidence/wave35-wip-13.json` and `wave35-wip-13/selection-plan.json`. WIP14 is the landed R59–R72 checkpoint: `docs/remediation/bac/evidence/wave35-wip-14.json` and `wave35-wip-14/selection-plan.json`. Their receipts, historical selectors/tests and published bytes remain historical evidence. Do not rerun their fixed-interval selectors to select later rounds or rewrite their metadata to fit the new tool.

The next interval begins R73. WIP15 and terminal R81 are tentative until root seals the checkpoint contract, complete actual interval/attempt inventory, frozen qualification subject and terminal receipt. No next-checkpoint selection, assembly or publication is claimed here. Independent tooling review and root's frozen synthetic rerun are prerequisites to real use; passing synthetic tests does not qualify application behavior or actual terminal evidence.

## The sealed contract and finite selection

The neutral tool is `W/evidence-management/bac_checkpoint_contract.py`, where `W=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades`. Its required contract uses schema `bac-checkpoint-selection-contract-v1` and binds:

- Safe `checkpoint_id` and `series`, explicit positive integer `interval_start` and `terminal_round`.
- A hash-bound `baseline_inventory` reference and ordered `catalog` of authenticated published manifest/selection-plan pairs, each with checkpoint ID, explicit format tag and interval.
- An explicit `required_components` list with exact rooted path/hash, candidate identity and scope, including any consciously reused earlier component evidence.

No terminal is inferred from live files. The catalog must be the exact chain suffix anchored to a baseline-inventory manifest. Every predecessor and plan link must agree; intervals must be contiguous; the last manifest must equal the current pointer. The next start must be predecessor terminal+1. Omitted/reordered/duplicate catalog entries, unsupported formats, missing components and destination collisions stop selection. The next receipt must cover the required component list exactly.

Historical parsing is explicit. `wip13-artifacts-v1` requires WIP13's schema-less `artifacts`/`predecessor` manifest and `bac-wip13-delta-plan-v1` plan. Its declared interval is checked against the chain's anchor and terminal rounds. `incremental-v2` requires WIP14's `bac-incremental-checkpoint-evidence-v2` manifest with `objects`/`previous_record` and `bac-wip14-delta-plan-v1` plan. Future manifests use `checkpoint-publication-v1` with the neutral schemas below. These are authenticated readers of immutable historical archive metadata, not application compatibility code or fallback schema guessing.

The tool checks normalized object paths, sizes, hashes, manifest/plan agreement, copy-directory containment and provenance of reuse from earlier catalogs. It rehashes selected reused bytes, not every historical object. The baseline inventory and prior catalogs are referenced rather than recopied or fully re-audited. New Python helper snapshots end `.py.txt`; all aliases remain in the plan's input table. Safe rooted paths, ancestor/descendant symlink refusal and exclusive destinations remain mandatory.

## Receipt, attempts and terminal review

The receipt uses `bac-checkpoint-terminal-receipt-v1`, with status `SEALED FOR EVIDENCE SELECTION`, checkpoint/series/interval matching the contract, and its exact `{root:"W",path,sha256,bytes}` contract reference. It binds terminal candidate manifest/base/tree and execution subtrees, frozen review subject, interval entries, authoritative checks/attempts, components, reviews, documents, dependencies, package accounting, scope and required next work. The terminal candidate path must be `<series>/r<terminal>-candidate.json`.

Every round needs its candidate and fixture-resource-preflight metadata. The receipt must equal the observed `Q/<series>-rN-*` top-level set throughout the finite interval, where `Q` is the supplied qualification root. Attempt descendant inventories include every file's path/size/hash and all descendant directories, including empty ones. Distinct check/attempt/semantic-record identities and exact terminal pointers remain required. Several commands sharing a directory require distinct hash-bound structured records; declarations must agree with their results, and differing statuses require top-level `MIXED` status. No failed or unrun attempt disappears when a later attempt passes.

Each attempt binds its own source, not merely the terminal candidate. Checks distinguish runtime, static, collection, capture, preflight and diagnostic work. PASSED attempts require exit zero. A qualifying terminal runtime requires a positive integer passed count, result/log/verifier references, finite positive numeric elapsed seconds and actual controller/import-thread custody. Booleans, NaN and infinities cannot serve as duration. Missing absolute UTC start/end times remain null with an explicit reason; do not infer them from file metadata. Duration and other structured result fields must agree with the declaration. Single-process claims require integer zero workers; xdist claims require the exact positive worker count and witnesses. Nonruntime absence of execution fields/custody remains explicitly disclosed. Required children bind the qualifying check's exact terminal attempt and its actual source; an earlier child cannot satisfy a later attempt.

The separately frozen qualification-subject JSON contains the exact contract reference and matching candidate tree. Independent terminal review binds both that subject and the exact candidate manifest. Reviews identify distinct producer/reviewer, independence evidence, bounded scope and disposition. JSON independence evidence must agree with the declared producer/reviewer identities. The subject is frozen before the receipt embeds the review hash, avoiding a circular seal. Root still compares the final receipt with the frozen subject and verifies substantive review independence and source execution; byte/structure checks cannot prove those observations. A component review or tooling review is not automatically terminal qualification review.

Reviewed document and review hashes are immutable. Each required helper reference must appear in the named dependency closure with the appropriate `required_by` check relationship. A stale review/document, omitted helper, changed source reference or changed directory membership requires correction and a fresh seal. Integrity readiness neither turns a current FAILED global check green nor treats overlapping tests as unique coverage.

## Planning and root materialization

Python interfaces are `plan(root, work, qualification, contract_path, chain_path, receipt_path, *, draft=False)` and `assemble(root, work, qualification, contract_path, chain_path, plan_path, report_path)`. Both use the same sealed contract. The chain path is fixed under `R/docs/remediation/bac/evidence/checkpoint-chain.json`; contract and receipt reside under W.

The plan schema is `bac-checkpoint-selection-plan-v1`. It binds the contract path/hash, ordered catalog, required components, interval inventory, predecessor and prior plan, chain hash, exact candidate/frozen subject, receipt hash, selected inputs and content-keyed objects. The hashed receipt and selected references retain the attempts, custody, reviews and dependencies. Status `READY FOR ROOT PUBLICATION CHECKS` certifies only finite selection and checked relationships/bytes. `--draft` produces `DRAFT PLAN ONLY`, bypasses full final-receipt validation and can never assemble or serve as publication evidence.

These are root-owned templates, not evidence of executed actual operations. Use previously nonexistent output paths:

```sh
R=/workspace/hamlet
W="$R/.superpowers/sdd/2026-11-01-bac-remediation-upgrades"
Q=/workspace/bac-review-2026-11-01/qualification
python -B "$W/evidence-management/bac_checkpoint_contract.py" plan \
  --root "$R" --work "$W" --qualification "$Q" \
  --contract "$W/wave35/ROOT-SEALED-CHECKPOINT-CONTRACT.json" \
  --chain "$R/docs/remediation/bac/evidence/checkpoint-chain.json" \
  --receipt "$W/wave35/ROOT-SEALED-TERMINAL-RECEIPT.json" \
  --output "$W/evidence-management/ROOT-EXCLUSIVE-CHECKPOINT-PLAN.json"
python -B "$W/evidence-management/bac_checkpoint_contract.py" assemble \
  --root "$R" --work "$W" --qualification "$Q" \
  --contract "$W/wave35/ROOT-SEALED-CHECKPOINT-CONTRACT.json" \
  --chain "$R/docs/remediation/bac/evidence/checkpoint-chain.json" \
  --plan "$W/evidence-management/ROOT-EXCLUSIVE-CHECKPOINT-PLAN.json" \
  --output "$W/evidence-management/ROOT-EXCLUSIVE-ASSEMBLY-REPORT.json"
```

Assembly recomputes exactly the same plan from the same contract and rejects drift, drafts and collisions. It rechecks selected sources/reuse, copies only new objects beneath the checkpoint directory with exclusive creation, and verifies destination bytes. Its `bac-checkpoint-assembly-proposal-v1` report remains `INCOMPLETE PUBLICATION PROPOSAL; ROOT REVIEW REQUIRED`, with no publication tree or navigation approval. Partial assembly is not successful publication; existing destinations are never overwritten or deleted.

Root writes the authoritative `bac-checkpoint-publication-v1` manifest with checkpoint/series/interval/terminal round, predecessor and hash-bound selection plan, and the plan's exact contract/catalog/components, candidate/frozen subject, receipt, input/object and execution-identity bindings. This neutral metadata becomes an explicitly tagged catalog pair for a later checkpoint without per-ID code changes. Root owns final record/chain/index changes, exact staged scope and pre/post document hashes, executed-versus-publication source equivalence, authorized Git action and remote/CI verification. The selector writes none of those authoritative navigation records and performs no application import or Git call.

## Remaining gates

Original-package accounting remains 28 qualified /38 remaining /66 total unless a separately reviewed receipt changes it. The known oracle type errors, required runner obligation, applicable hardware including unexecuted CUDA, remaining repository/coverage≥70/slow work and exact final remote CI remain open as their actual evidence states. Bounded evidence can retain failed current checks and explicit next work; it must not be described as whole BAC acceptance or a green global gate. No evidence-process change weakens these requirements.

---

Source verification for this replacement draft, 2026-11-13: the frozen neutral implementation and tests were verified by SHA-256 without executing application code or changing either source. `bac_checkpoint_contract.py`: 568 lines, `66f62969169247eaf3ff90a5859018801bcb87f897fb032857bd263d480eb0d8`. `test_checkpoint_contract.py`: 584 lines, `f17f102f486a5c5256e68326624949387a0cf9e1aeebf71eac9e688f3181376b`. The exact replacement-document hash is supplied separately in the handoff to avoid a self-referential hash. This preparation draft has not replaced the tracked process document.
