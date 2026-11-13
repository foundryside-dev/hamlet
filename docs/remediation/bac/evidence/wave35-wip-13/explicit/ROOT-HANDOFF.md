# Root handoff — evidence management

The archive is intact. Additive index cleanup and a usable WIP13 delta selector are complete; independent review is tracked separately by root. All outputs reside in this ignored directory. No branch/worktree/checkout, Git write, source/doc/index modification, deletion or receipt rewrite was performed.

Audit: 14,891 files / 296,657,580 bytes; 3,099 duplicate aliases / 72,563,533 duplicate bytes. All 14,809 archived artifact hash assertions verify. All six current-document historical byte references not present in archive content were verified from their exact publication Git commits. No integrity loss found within this bounded scope.

Use `PROCESS.md` for the invocation/copy contract. Final receipt selection has passed with `wip13-final-plan-v2.json`: 199 inputs, 187 content objects, 183 new objects / 4,932,119 bytes, four reused content objects. This retains every R55–R58 artifact and the three new historical candidate manifests, including failed source/run evidence, without copying the old wave history. Add required changed tooling explicitly via `--include` and generate a fresh plan path. Root rehashes every source/target and enforces source tree and staged-path publication checks. The plan is not a Git or acceptance authority.

Suggested publication set (map short documents to their destinations; do not copy the entire working folder):

* `EVIDENCE-INDEX.md` → `docs/remediation/bac/EVIDENCE-INDEX.md`.
* `PROCESS.md` → `docs/remediation/bac/EVIDENCE-PROCESS.md`.
* `AGENTS-entry.md` → append its content to repository AGENTS.md after process/index destinations exist.
* `canonical-chain.json` and `historical-document-references.json` → stable evidence navigation alongside checkpoint manifests. Update the current pointer with WIP13's final manifest hash at actual publication; do not call the candidate itself published prematurely.
* `evidence_index.py`, `select_wip13.py`, `test_evidence_tools.py`, `validation-v2.json`, `validation-tests-v2.log`, this `ROOT-HANDOFF.md`, and the independent process review → WIP13 tooling/audit evidence or the existing qualification tools area. If code is archived as `.py.txt`, retain the original names in provenance for reproduction.
* The final authoritative WIP13 receipt/manifest, selected new raw objects and exact prior references per the approved plan.

Do not publish the intermediate `inventory-v1.json`, draft plan, or first final plan. `inventory-v2.json` is the authoritative local full baseline; it need not be published because the final delta plan has direct prior-object paths/hashes. If desired, publish this baseline exactly once, separately from subsequent checkpoint content. The human index and chain explicitly identify local baseline artifacts; adjust those local-reference notes when relocating them. Preserve all intermediates locally.

Validation: 15 meaningful tests pass, including tampered/missing/unindexed/symlink evidence, legacy hash formats, path traversal, finite interval/deduplication, final completeness, source identity mismatch, draft rejection, receipt symlink and outside-archive reference rejection, plus explicit Python snapshot suffix/provenance and unchanged historical Python reference paths. Final selector also verifies complete baseline bytes/path set, exact final runtime/custody/logs/profiles, historical failed-source manifest/log bindings, required reviewed document hashes, and explicit document-only delta. `validation-v2.json` binds current tested tool bytes; `validation.json` and its 14-test log are historical and do not seal the revised helper. This is data-tool verification, not another application test run.

Next action: root accepts the independent review, builds a fresh final plan including any needed helper changes and this reviewed process evidence, then assembles exactly its copy/reference objects. Continue original-package28/38/66 accounting and all pending qualification obligations unchanged. Do not run the old broad-copy publisher for WIP13.

Artifact-storage revision: explicit `.py` helpers are copied as `.py.txt` snapshots, preserving their original producing paths, exact bytes and SHA-256. Existing archived reference paths are never renamed. This prevents archived reproduction helpers from being enrolled as maintained Python source by repository-wide lint discovery; acceptance requirements are unchanged. `wip13-publication-plan-v2.json` demonstrates four new helper snapshots with `.py.txt` and zero new `.py` targets. Root must generate one fresh final selection after the scoped review and current document edits are sealed; all prior plans remain immutable historical outputs.
