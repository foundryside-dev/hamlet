# BAC checkpoint evidence process

This process governs evidence publication, not acceptance requirements. It adds no package qualification and waives no execution, independent review, coverage, hardware, type, or final CI gate. Existing artifacts, failures, backups, commits and all registered worktrees remain intact.

## Authoritative records and exact-byte references

1. Freeze one candidate manifest with base commit, candidate tree, execution subtree identities and SHA-256 source/config/artifact inventories. A publication commit/tree is a separate identity. Never substitute it for the tree actually executed.
2. For each candidate/check, keep one authoritative check record pointing to immutable attempts. Retain failed and interrupted attempts; identify the terminal attempt explicitly. Each attempt identifies command/selection, timestamps, actual exit/counts, environment/hardware, actual controller/worker/child identities, imports/thread/debug custody, raw log hashes, and verifier identity. Scope each result to its actual source and check. Same-byte evidence reuse authenticates bytes; it does not prove a newer candidate executed them.
3. Seal one checkpoint receipt linking those records, independent reviews, package accounting, overlapping selections, failures, skipped/unexecuted hardware and next required work. Changes to a sealed receipt require a new record linked to its predecessor, never replacement. Do not sum independent reruns or nested selections as unique cases.
4. Store each new artifact's exact bytes once. An artifact reference contains SHA-256, byte size, immutable repository path (or exact Git commit plus path), and original producing path/role. Reuse any already published identical bytes only after checking their hashes. Preserve all logical source aliases in the manifest. A same-name file with different bytes is a new object. Do not reference mutable CURRENT documents by path alone: snapshot their approved bytes once, or record an exact Git commit/path and verified SHA-256.
5. Build an explicit delta selection from the new interval and named additions. Do not recursively copy all wave35 history, execution progress/tasks state, previous source manifests, or helper files. Include changed required helper/verifier versions explicitly; reuse unchanged versions by hash. Retain failed/red evidence in the interval. Do not delete old duplicates as part of this process.
6. Before publication root verifies all selected input hashes and all reused targets, copies only new content into previously nonexistent paths, checks destination hashes, then writes the authoritative checkpoint manifest. Root checks source/execution tree equivalence, exact staged-path scope, existing qualification constraints and final documentation/review hashes before its authorized Git action. If anything changes, stop and reseal a new plan. A selector's success is not qualification or publication approval.
7. Publish a short status delta: what changed, exact tested identity, named bounded result, remaining failures/gates and next dependency. Link the checkpoint and one maintained evidence index. Do not append repeated historical narratives to every future record. Update the index's current pointer while retaining its linked history. Refresh a full baseline inventory only when needed; future checkpoints link prior manifests and add new content records rather than republishing the baseline.

## WIP13 operational contract

The read-only `select_wip13.py` consumes the final R58 receipt, the candidate it names, and `inventory-v2.json`. It includes qualification `wave35-r55*` through `wave35-r58*` only, the exact receipt/candidate plus new R55–R57 historical candidate manifests, hash-checked named reviews and current documents; supplemental helper files or rationale are explicit `--include` arguments. It preserves all files in that finite interval, including failures, rather than filtering solely for successful logs. It makes no Git call and writes only its exclusive output plan. `--draft` produces planning evidence only and is prohibited for publication.

```sh
W=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades
Q=/workspace/bac-review-2026-11-01/qualification
python "$W/evidence-management/select_wip13.py" \
  --root /workspace/hamlet --qualification "$Q" --work "$W" \
  --inventory "$W/evidence-management/inventory-v2.json" \
  --receipt "$W/wave35/r58-checkpoint-receipt.json" \
  --output "$W/evidence-management/wip13-final-plan.json"
```

The final receipt above exists and passed the selector checks. The output path must not already exist; choose a new plan filename for a new run. Add `--include "$Q/changed-helper.py"` for each required new helper version and explicit plan/review artifact. Include the selector/indexer versions themselves if they are used to assemble publication. Do not add mutable progress/tasks snapshots by default.

`objects[sha256]` is the copy/reference table: `copy-new` supplies source, destination and bytes; `reference-existing` supplies an already verified archived target. `inputs` maps every original path and logical role to a content hash, including aliases that do not require a second copy. Root's manifest should embed this table or equivalent records, the final receipt, predecessor path/hash and execution identities. Root must rehash every input immediately before copying; the selector does not lock the filesystem or certify process termination. Reject existing copy destinations and publication from a draft plan. Check `inputs` and explicit additions for all needed witness/verifier dependencies; absolute paths inside legacy raw receipts are provenance, not portable dependencies by themselves.

The prepared draft selected 192 paths, 180 unique objects, 176 new objects (4,197,850 bytes), and four existing objects (5,540 bytes), with 12 intra-selection aliases. Final approved docs and explicit tool additions will change these numbers. The prior 296,657,580-byte archive is referenced, never recopied. The 2.76 MB baseline inventory is a one-time audit artifact; WIP13 need not embed or publish it to preserve the small plan's self-contained object references.

## Root integration

Suggested tracked destinations after review: `docs/remediation/bac/EVIDENCE-INDEX.md`, `docs/remediation/bac/EVIDENCE-PROCESS.md`, `docs/remediation/bac/evidence/checkpoint-chain.json`, and `docs/remediation/bac/evidence/wave35-wip-13.json` with new raw objects below `wave35-wip-13/`. Keep the large audit inventory in ignored working evidence unless a one-time baseline publication is useful. If published, publish once, not under every WIP directory. Keep selection tools beside qualification tooling or deliberately install them under `scripts/` in a later explicit tooling change; this handoff does not alter source or frozen docs.

Root may integrate the accompanying `AGENTS-entry.md` at the same time. Old archive removal, Git history rewriting, moving backups, or any capability reduction is outside this process and requires a separate surfaced decision.

Final-mode verification also checks the full baseline archive path/hash set, required R58 receipt fields, exact named R55–R57 result/log/manifest identities, actual R58 runtime custody/results/logs, compiler profiles and static logs. Approved document deltas are allowed only at explicit receipt paths under docs/remediation/bac, with their approved hashes recorded separately from the candidate inventory. Final measured selection (before supplemental tooling): 199 inputs, 187 unique objects, 183 new objects / 4,932,119 bytes, four reused objects / 5,540 bytes. `wip13-final-plan-v2.json` supersedes the earlier final plan for selection because it additionally preserves the three new historical candidate manifests.

Current tooling verification: `validation-v2.json` / `validation-tests-v2.log` seal the revised selector with 15 passing tests. The earlier `validation.json` / 14-test log is historical. Explicit Python helper inputs retain their original path/hash provenance but new snapshot destinations end in `.py.txt`; existing archived reference paths remain exact and unchanged. This is artifact storage, not a static-check waiver. Regenerate a fresh final plan after current process/review/tooling bytes are sealed.
