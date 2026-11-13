# Independent evidence-management review — 2026-11-13

**SPEC: PASS for the bounded evidence selection and navigation process. QUALITY: PASS for the reviewed data tooling.** This is not WIP13 publication, application requalification, or acceptance of an open BAC gate.

I reviewed `evidence_index.py`, `select_wip13.py`, `test_evidence_tools.py`, `inventory-v2.json`, `canonical-chain.json`, `historical-document-references.json`, `PROCESS.md`, `EVIDENCE-INDEX.md`, `AGENTS-entry.md`, `ROOT-HANDOFF.md`, and the final selection plan. I did not inspect application source, run application tests, or use Git. The work used the existing `/workspace/hamlet` and data fixtures only.

## Direct checks

* `evidence_index.py verify` passed against the existing archive: 14,891 paths and 11,792 exact content identities. The inventory reports 14,809 in-archive artifact assertions with zero failures, 3,099 duplicate aliases, and 72,563,533 duplicate bytes. The 102 non-archive references are labeled historical, not current-file assertions; the separate ledger lists the six references whose exact bytes are absent from the archive and their claimed publication-commit hashes. I did not independently run Git verification of those six entries.
* All 46 `canonical-chain.json` entries have manifest paths/hashes matching the inventory, and every stated predecessor points to the preceding chain entry's exact manifest path/hash. The chain expressly describes natural label ordering, not verified Git ancestry. The original package receipts are identified separately in the index; no current-source qualification is inferred from old source identities.
* The 14 focused data-tool tests passed. A direct call to final-mode `select()` against the actual R58 receipt reproduced `wip13-final-plan-v2.json` exactly: 199 logical inputs, 187 unique content objects, 183 new objects (4,932,119 bytes), four hash-checked existing objects (5,540 bytes). The input mapping retains all available R55–R58 interval files, including failure and feature-red records, and includes R55–R57 candidate manifests, final receipt, four named reviews, and three approved current documents. No selected logical path contains a backup or bundle marker.
* Final mode checks the fixed R58 candidate/base identity, nonempty 812-source/573-config/13-artifact witness maps, current-file hashes (with explicit approved-document deltas), full prior archive path/hash set, WIP12 predecessor, required document/review/runtime fields, named R55–R57 result/log/manifest identities, R58 runtime custody/results/logs, compiler process profiles, and static logs. The receipt retains 28/38/66 package accounting, the ordinary-runner gap as open, and global static as failing. `--draft` remains explicitly marked `DRAFT PLAN ONLY`.

## Defects found and resolved during review

1. Initial final mode returned `READY` in a fixture with empty runtime/review maps and no R56/R57 raw evidence. The revised final validator rejects this and requires named results and logs across the historical rounds.
2. A work-root receipt symlink to a file outside that root initially passed in draft mode because resolution erased the symlink. The revised selector rejects receipt symlinks and outside-root receipt paths.
3. An unverified inventory could initially steer an existing-content reference outside the immutable archive. Revised final mode verifies the complete archive inventory and rejects non-archive reuse targets.
4. The index initially referred to a missing root handoff file. `ROOT-HANDOFF.md` now exists.

## Publication boundary

The plan is a selection and integrity receipt. Root must rehash inputs immediately before copy, check new destinations and exact staged scope, bind the final WIP13 manifest to the actual executed tree and approved documents, and publish only after its separate gate checks. The existing 14,891 archive paths and historical failures remain intact. Current R58 component results do not qualify the missing ordinary runner inputs, global mypy failures, CUDA skips, BANK/CP adoption, or final programme and remote CI gates.

## Scoped first-use storage re-review

Root found that newly copied explicit Python helpers would have landed in the evidence archive with `.py` suffixes and entered global Ruff's maintained-code scan. The revised selector adds `.txt` only to the logical destination basename of explicit `.py` inputs. It leaves each original producing path, SHA-256, byte count and reused archived object path intact. A focused fixture proves both a new `helper.py` becomes `explicit/helper.py.txt` and identical earlier bytes still reference their original archived path.

I ran that focused test and the full 15-test data-tool suite: both passed. I checked `validation-v2.json` against the revised selector, indexer and test file hashes. The fresh `wip13-publication-plan-v2.json` is `READY FOR ROOT PUBLICATION CHECKS` with 220 logical inputs and 208 unique objects; its four new Python helper objects all end in `.py.txt`, and it has zero `copy-new` `.py` targets. This scoped change leaves the preceding archive and R58 selection conclusions intact. **SPEC: PASS; QUALITY: PASS** for the revised first-use destination rule.
