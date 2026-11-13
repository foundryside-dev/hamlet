# Finite checkpoint contract tooling — frozen for review

2026-11-13. Standalone neutral implementation and synthetic regressions are ready for root rerun and independent other-model review. No real selection, assembly, terminal receipt, application qualification, source approval, Git/index action, branch/worktree, remote write or delegation occurred. Application remains frozen at qualified R81. No claim of next-checkpoint publication or closed acceptance gates.

## Source boundary and frozen hashes

Only the two authorized historical source bodies and two new implementation/test bodies were used. Measured historical bodies before reading. New code carries forward the historical guard semantics into the actual neutral tool; it does not import or execute the old selector and is not a compatibility wrapper or execution copy. Imports are standard library only; tests import the new tool only. All fixture writes/assemblies were temporary synthetic DATA.

| File in W/evidence-management | Lines | SHA256 |
| --- | ---: | --- |
| bac_checkpoint_delta.py (unchanged) | 469 | 33e992e31a2bfcdb0fa70fac315acc92ec3e961831b0d612c2ba8148c16ef8f8 |
| test_checkpoint_delta.py (unchanged) | 389 | 8af61971bf01a7e2045d344fabad87905af4aaf0b5004418ecf98fa9e13941e2 |
| bac_checkpoint_contract.py (frozen new tool) | 568 | 66f62969169247eaf3ff90a5859018801bcb87f897fb032857bd263d480eb0d8 |
| test_checkpoint_contract.py (frozen new tests) | 584 | f17f102f486a5c5256e68326624949387a0cf9e1aeebf71eac9e688f3181376b |

Total 2010 lines versus projected2658/hard5000; each new body is below its900-line cap. No fifth implementation dependency. The readiness proposal and EVIDENCE-PROCESS were read as governing prose. Actual published WIP13/WIP14/chain JSON metadata was inspected, without reading object trees: WIP13 has no manifest `schema`, uses `artifacts` and `predecessor`, and plan schema `bac-wip13-delta-plan-v1`; WIP14 has `bac-incremental-checkpoint-evidence-v2`, `objects`, `previous_record`, `interval=[59,72]`, `round=72` and plan schema `bac-wip14-delta-plan-v1`. WIP13 interval is absent from its manifest/plan, so the explicit contract interval is checked against the chain's predecessor round54 and WIP13 round58. These are historical readers, not application fallbacks.

## Exact interface

Python API:

```python
plan(root, work, qualification, contract_path, chain_path, receipt_path, *, draft=False)
assemble(root, work, qualification, contract_path, chain_path, plan_path, report_path)
```

CLI requires positional `plan` or `assemble`, plus `--root`, `--work`, `--qualification`, `--contract`, `--chain`, `--output`. Planning requires `--receipt`, forbids `--plan`, and optionally accepts `--draft`. Assembly requires `--plan` and forbids `--receipt`/`--draft`. JSON output paths must be previously absent with ordinary existing parents. The chain is fixed to `R/docs/remediation/bac/evidence/checkpoint-chain.json`; contract and receipt must be ordinary paths under W. API `plan` returns a dictionary; CLI writes it exclusively. Assembly writes only new object bytes and an incomplete proposal report, never the authoritative manifest/chain/index.

## Contract schema

Required JSON object, `schema=bac-checkpoint-selection-contract-v1`:

- `checkpoint_id`, `series`: safe lowercase letter-led hyphen-separated identifiers; checkpoint starts `series + "-"`; new ID cannot collide with chain or published manifest/plan destinations.
- `interval_start`, `terminal_round`: explicit positive exact integers, inclusive ordered interval. Start must be predecessor terminal+1. No terminal inference.
- `baseline_inventory`: rooted reference `{root,path,sha256,bytes?}` to `bac-evidence-inventory-v1` with zero integrity failures; R/W/Q are the only roots.
- `catalog`: nonempty ordered list of `{checkpoint_id,format,interval:[start,end],manifest:{path,sha256,bytes?},selection_plan:{path,sha256,bytes?}}`. Published paths are exactly `docs/remediation/bac/evidence/<id>.json` and `<id>/selection-plan.json`. Format is explicitly `wip13-artifacts-v1`, `incremental-v2`, or `checkpoint-publication-v1`. The first historical format must be first, with schema-less artifacts manifest and the actual WIP13 plan schema; no guessing. The incremental format requires actual WIP14 schemas. Neutral future format requires the schemas below.
- `required_components`: explicit list of rooted file refs additionally carrying `candidate_tree` and nonempty `scope`. Duplicate root/path pairs are rejected. Receipt coverage must equal the sealed list exactly, including hashes and scope.

Catalog chain is the exact suffix of the maintained chain; it must have an earlier baseline anchor. Anchor manifest path/hash must occur in the inventory and its bytes are checked. Chain entries bind id, manifest, previous_record, selection_plan and round. Every interval is contiguous, every predecessor/plan link agrees, and final manifest equals the current pointer. Object paths/sizes/hashes/actions are normalized and reconciled between manifest and plan. New objects must stay in their own checkpoint directory with no path collision; reuse must refer to an earlier catalog/baseline object. Only selected reused object bytes are rehashed; this is not a full historical archive audit. The plan binds the chain hash.

## Receipt, plan, assembly and future publication schema

Receipt schema is `bac-checkpoint-terminal-receipt-v1`. It retains the historical `status=SEALED FOR EVIDENCE SELECTION`, `base_commit`, `candidate_tree`, exact `execution_subtrees`, `candidate_manifest`, `review_subject`, package accounting, `interval_entries`, `attempt_index`, `component_receipts`, `reviews`, `documents`, `dependencies`, `required_next`, and `scope`. Adds required `checkpoint_id`, `series`, `interval_start`, `terminal_round`, and exact `contract={root:"W",path,sha256,bytes}` matching current contract bytes. Terminal candidate path must be `<series>/r<terminal>-candidate.json`. Frozen review subject is JSON carrying the exact `contract` ref and matching `candidate_tree`; terminal reviews must bind both that frozen subject and exact candidate manifest. This avoids a receipt/review hash cycle.

Attempt/check schema and guard semantics remain as in the historical selector: check identity/kind/status/qualifying/terminal pointer; distinct attempt and semantic record identities; each attempt's candidate manifest/base/tree, exact descendants, environment/hardware/process custody, status and recorded execution or explicit unavailable/unrun reasons. Runtime qualifying terminal attempts additionally require actual positive integer passed count, exit0, command, finite positive numeric duration (bool/NaN/infinities rejected), real result/log/verifier refs, explicit missing absolute-UTC explanation where needed, controller/import-thread witnesses, and exact single-process or xdist worker topology. Child witnesses bind the exact terminal attempt and its own source. Structured result fields reconcile with declarations. Shared-directory command records remain distinct and MIXED status is reconciled. All failed/interrupted/unrun/diagnostic/partial evidence remains selected.

Review refs require role/reviewer/producer/independent/scope/disposition, independence-evidence ref and reviewed subjects; reviewer differs from producer. When independence evidence is JSON, its `reviewer`/`producer` must match the review declaration. Immutable document/review bytes and named helper `required_by` closure are checked. These are structural and byte checks; root still verifies substantive independence, actual source execution and qualification truth.

Plan schema is `bac-checkpoint-selection-plan-v1`; status is `READY FOR ROOT PUBLICATION CHECKS` or `DRAFT PLAN ONLY`. Fields: checkpoint_id, series, contract, ordered catalog, required_components, review_subject, candidate_manifest, authority, interval, interval_inventory (including empty directories), receipt `{original,sha256}`, inventory_sha256, previous_checkpoint, previous_selection_plan, chain `{path,sha256}`, candidate_tree, base_commit, execution_subtrees, inputs, objects, metrics. Inputs retain every alias `{original,logical_path,sha256,bytes}`; content-keyed object rows retain action/path/bytes and source for copy-new. New `.py` snapshots end `.py.txt`. Contract bytes themselves are included among selected inputs. Receipt hash transitively binds all attempt/review/custody identities and dependencies, and their referenced bytes are separately selected and hashed.

Assembly schema is `bac-checkpoint-assembly-proposal-v1`, status `INCOMPLETE PUBLICATION PROPOSAL; ROOT REVIEW REQUIRED`. Includes checkpoint/series/interval/contract/catalog/required components/frozen subject/candidate/base/execution identities, current predecessor and prior plan, selection_plan_sha256, receipt, objects, inputs, copied paths, chain_prior_sha256, publication_tree=null, navigation_approved=false. Assembly exactly recomputes the same plan, rejects drift/draft/output collisions, rechecks all selected sources and reuse, copies exclusively, then checks destination bytes. No deletion or overwrite.

Root's future manifest schema is `bac-checkpoint-publication-v1`: `checkpoint_id`, `series`, `interval`, `round=interval[1]`, `previous_record`, `selection_plan` path/hash/optional size, plus exact plan copies of `objects`, `contract`, `catalog`, `required_components`, `review_subject`, `candidate_manifest`, `receipt`, `inputs`, `base_commit`, `candidate_tree`, `execution_subtrees`. This schema is consumed by the same neutral reader on a later checkpoint; prior plan catalog must equal the current catalog prefix. Root writes final publication metadata; the tool does not manufacture it.

## Synthetic TDD and checks

Working directory for all commands below: `W/evidence-management`.

1. Tests written before implementation, porting all21 historical synthetic cases to the new contract and actual historical formats. Initial RED:
   `python -B -m unittest test_checkpoint_contract.py`
   `ModuleNotFoundError: No module named 'bac_checkpoint_contract'`; `Ran 1 test ... FAILED (errors=1)`.
2. First implementation exposed fixture metadata omission (`action` absent from old synthetic artifacts; actual published artifacts carry it). Corrected only the new fixture to model actual historical metadata; 21/21 ported regressions passed, with original files unchanged.
3. Added contract/catalog/finite-duration/forged-independence/terminal-source cases and two successive synthetic future checkpoints with unchanged implementation. Final command:
   `python -B -m unittest test_checkpoint_contract.py`
   Output: `Ran 28 tests in 0.648s`, `OK`.
4. `python -B -m ruff check --select E9,F63,F7,F82 bac_checkpoint_contract.py test_checkpoint_contract.py` could not run because the host interpreter lacks the ruff module. Used the installed repository tool, without imports of application code:
   `/workspace/hamlet/.venv/bin/ruff check --no-cache --select E9,F63,F7,F82 bac_checkpoint_contract.py test_checkpoint_contract.py`
   Output: `All checks passed!`.
5. `python -B` stdlib `ast.parse` of exactly the two new files: both OK; imported module inventories above are stdlib + test's new selector only. `wc -lc` and stdlib SHA256 verified final lines/hashes and both unchanged historical hashes shown above.

Tests retain the old21 scenarios and add authenticated catalog omission/reorder/duplicate/wrong format/link/interval/objects/reuse provenance; wrong pointer; contract/receipt/series/ID mismatch; omitted component/round/terminal; contract drift; collisions; finite timing; forged separation identity; wrong terminal candidate path; full successive neutral publication consumption. The successive-checkpoint case reuses baseline, both historical catalogs and newly published predecessor; asserts alias dedup, byte-exact assembly and repeated equal pre-materialization planning. Same-name changed bytes, symlinks/traversal/ancestor links, descendant/empty-dir drift, missing semantic records, mixed command consistency, child-source binding, stale reviews/documents, unsupported workers, clock explanations, draft rejection and duplicate outputs remain covered by the ported cases. Replanning after materialization intentionally fails exclusive destination checks; equality checks occur before materialization.

## Self-review and remaining finite root work

No per-future-ID edits are needed: identifiers/series/interval/catalog/components come from the contract. Historical format strings are explicitly versioned readers only. No policy gates were removed. Numeric duration now rejects nonfinite values, worker counts reject booleans, terminal candidate path is checked against the contract's actual terminal, and JSON independence identities are reconciled. Plan equality and exclusive copying preserve post-seal drift refusal. Old files are byte-identical. New files are frozen at the above hashes for independent review; any subsequent fix needs a new hash/review/rerun.

Root still owns: independent other-model review of these exact files and this report; frozen synthetic rerun; actual contract/interval/attempt/component seal beginning73 (tentative WIP15 and R81 only after root seal); immutable qualification subject with contract ref, candidate and genuine terminal independence review; truthful child/process/source/dependency/document custody; actual integrity selection, exclusive assembly, authoritative manifest/chain/index; separately authorized commit/push and exact remote/CI verification. Tooling readiness proves neither source behavior nor global qualification. No actual command below has been run.

### Literal root-only templates — UNRUN actual operations

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


## FIX1 append-only amendment — finite review repair round1/5

2026-11-13. This amendment supersedes only the frozen new-source hashes/results and the two guard descriptions affected by S1/S2 above; the original report prefix is retained byte-for-byte. Its explicitly versioned prose snapshot is `T18e-R0-NEXT-CHECKPOINT-TOOLING-REPORT-V0-SNAPSHOT.md`. Historical code/tests, original independent review and original process draft remain unchanged.

Exact sealed review consumed: `T18e-R0-NEXT-CHECKPOINT-TOOLING-INDEPENDENT-REVIEW.md`, SHA256 `b4d773b33374bb3866acf3004565e0dec166f058a0899c7c5a78974d3f1c66bc`. It requires S1/S2 repairs; neither is an application finding or accusation against R81 evidence. The review documents distinct-agent independence but explicitly cannot independently prove the precise other-model runtime identity; that limitation remains and this fix does not upgrade it.

S1: JSON child witnesses still require matching candidate source. If `attempt_id` is explicitly present, it must now equal the declared child's attempt, already bound to the qualifying terminal attempt. A same-candidate witness for `older-attempt` is rejected; a matching `pass2` is accepted. Absent literal attempt IDs remain supported by the existing fixtures and are not fabricated or retrofitted into historical witnesses. Root must retain the missing-field limitation or establish genuine recorded spec/result/PID/source linkage. This finite fix does not add validation of alternative supplied spec/result/PID fields or imply that candidate equality proves same-attempt execution.

S2: UNRUN now requires a reason and absent/null `exit_code`, `started_at`, `ended_at`, `counts`, and `duration_seconds`. Non-null end/count/duration facts are rejected, including empty count mappings and zero duration: these still represent observed values rather than unknown/null facts. Null fields and unavailable explanations remain supported. Actual execution belongs in its truthful executed/partial status. Supported elapsed-only qualifying runs remain covered by the unchanged existing regression.

Only the two authorized new source files changed. No application runtime/import, actual archive planning/assembly, Git/index, remote action, delegation, branch/worktree or source execution copy occurred. A unified scoped diff is DATA in `T18e-R0-NEXT-CHECKPOINT-TOOLING-FIX1-SCOPED-DIFF.txt`; it contains exactly two new synthetic methods and the two guard changes. No wider cleanup.

### FIX1 tests first and observed results

Working directory remains `W/evidence-management`. Added two focused tests before modifying implementation. The UNRUN subcases independently reset all three tested fields before each mutation.

Exact RED/GREEN focused command:

```sh
python -B -m unittest test_checkpoint_contract.ContractFixture.test_unrun_rejects_observed_execution_facts test_checkpoint_contract.ContractFixture.test_child_witness_attempt_identity_matches_terminal
```

Before implementation changes: `Ran 2 tests in 0.076s`, `FAILED (failures=6)`; each negative reported `AssertionError: ValueError not raised`. Five independent UNRUN subcases cover end timestamp, positive counts, empty counts, positive duration and zero duration; the sixth failure is the same-candidate wrong-attempt child. After the two guard changes: `Ran 2 tests in 0.067s`, `OK`. Positive controls retain null/unavailable UNRUN and matching literal child attempt identity; the earlier 28 tests retain absent-literal witness handling and supported duration-only qualification.

Full regression command: `python -B -m unittest test_checkpoint_contract.py`; observed `Ran 30 tests in 0.638s`, `OK`.

Targeted check: `/workspace/hamlet/.venv/bin/ruff check --no-cache --select E9,F63,F7,F82 bac_checkpoint_contract.py test_checkpoint_contract.py`; observed `All checks passed!`.

### FIX1 frozen identities and handoff

| File in W/evidence-management | Lines | SHA256 |
| --- | ---: | --- |
| bac_checkpoint_contract.py | 573 | 6fc6845ccb73e9bc8a0e24837bf005b0d2cd156107cb8a8341ded9012b7c54b3 |
| test_checkpoint_contract.py | 616 | b0dd9f8a3f7420771f237cc35be453040b134924a59225d1ba7c5fdb88a0d07d |
| bac_checkpoint_delta.py (unchanged) | 469 | 33e992e31a2bfcdb0fa70fac315acc92ec3e961831b0d612c2ba8148c16ef8f8 |
| test_checkpoint_delta.py (unchanged) | 389 | 8af61971bf01a7e2045d344fabad87905af4aaf0b5004418ecf98fa9e13941e2 |

Four-body total2047 lines; both new files remain below900, packet below hard5000. Sources are frozen again. Same-reviewer scoped re-review and root rerun remain required before real use; this producer report does not grant approval. Application R81 remains frozen. Root owns actual terminal/input seal, qualification/independence interpretation, final record/publication and remote/CI gates.

The new process replacement draft is `T18e-R0-EVIDENCE-PROCESS-NEXT-FIX1-DRAFT.md`; it describes the two corrected guards, absent-witness limitation and updated source verification hashes. Original process draft bytes are retained, and no tracked process document was edited. Exact report/snapshot/diff/draft hashes are supplied in the handoff, avoiding self-referential hashes.
