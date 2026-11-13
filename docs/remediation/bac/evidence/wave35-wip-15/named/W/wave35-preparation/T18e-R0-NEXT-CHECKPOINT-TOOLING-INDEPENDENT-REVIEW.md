# Independent review of frozen checkpoint contract tooling

2026-11-13. **SPEC: changes required. QUALITY: changes required for two missing negative controls. Not approved for actual selection/assembly at these frozen hashes.** The authorized synthetic suite passes. Two independent synthetic probes expose contradictory attempt provenance accepted as integrity-ready. Both gaps are inherited from the historical selector; neither is a new regression. No application finding or acceptance conclusion is made.

## Identity and finite scope

Reviewer: `/root/bac_checkpoint_contract_review`, separate from the tooling producer and root. Root reports producer selected explicitly as `gpt-6-astra`, medium effort; reviewer selected with default/inherited model, no override, and fresh context. Reviewer-visible identity is ChatGPT/Codex based on GPT-6. Neither reviewer nor root has a more precise runtime model identifier. Distinct author/reviewer agents and independent execution are evidenced; exact other-model identity is an explicit metadata limitation, not independently proved. Retain this limitation for any strict other-model gate.

Read `R/AGENTS.md`, this packet's BRIEF, READINESS and REPORT, and `R/docs/remediation/bac/EVIDENCE-PROCESS.md`. Applied `superpowers:requesting-code-review` and its reviewer criteria, `receiving-code-review`, and `verification-before-completion`. User restrictions superseded generic delegation/worktree suggestions. No delegation occurred.

Measured before reading all four authorized complete source bodies: 2,010 lines, below hard 5,000. No fifth implementation body or archived source body was read. Additional reads were governing prose and published WIP13/WIP14 manifest/selection-plan/chain JSON metadata. The actual WIP13 schema-less `artifacts`/`predecessor` layout and WIP14 v2 `objects`/`previous_record` layout match the fixture design. Actual manifest/plan object tables agree on the checked fields. No real selection or assembly was invoked.

E is `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management`.

| Source in E | Lines | SHA-256 verified before and after execution |
| --- | ---: | --- |
| bac_checkpoint_delta.py | 469 | 33e992e31a2bfcdb0fa70fac315acc92ec3e961831b0d612c2ba8148c16ef8f8 |
| test_checkpoint_delta.py | 389 | 8af61971bf01a7e2045d344fabad87905af4aaf0b5004418ecf98fa9e13941e2 |
| bac_checkpoint_contract.py | 568 | 66f62969169247eaf3ff90a5859018801bcb87f897fb032857bd263d480eb0d8 |
| test_checkpoint_contract.py | 584 | f17f102f486a5c5256e68326624949387a0cf9e1aeebf71eac9e688f3181376b |

Sources were unchanged. This review is the only persistent reviewer artifact. Execution imported only authorized synthetic tests/new tooling and standard library modules. Fixture creation, assembly and cleanup stayed within temporary synthetic DATA. No application import/runtime, Git/index/HEAD/remote mutation, branch/worktree/checkout/source execution copy, or historical evidence deletion occurred. R81 application remains frozen.

## Actual independent execution

Working directory E, Python 3.12.14. Exact required command:

```sh
python -B -m unittest test_checkpoint_contract.py
```

Observed exit code 0:

```text
............................
----------------------------------------------------------------------
Ran 28 tests in 0.667s

OK
```

This is an independent rerun of 28 synthetic methods, not additional unique application cases or actual selection/qualification. Producer's claimed initial RED was not recreated and is not independently attested here.

Additional command actually executed in E, exit code 0:

```sh
python -B - <<'PY'
from test_checkpoint_contract import ContractFixture, js, ref, d

f = ContractFixture()
f.setUp()
try:
    a = f.receipt['attempt_index'][0]['attempts'][0]
    a.update(ended_at='2026-11-13T00:00:00Z', counts={'passed': 99}, duration_seconds=1.0)
    f.seal()
    print('unrun_with_observed_end_counts_duration:', f.plan()['status'])
finally:
    f.doCleanups()

f = ContractFixture()
f.setUp()
try:
    a = f.receipt['attempt_index'][1]['attempts'][1]
    child = f.receipt['attempt_index'][1]['expected_children'][0]
    js(f.q / 'wave35-r74-passed/child.json', {'candidate_tree': f.b, 'attempt_id': 'older-attempt', 'child_pid': 123})
    child['witness'] = ref(f.q, 'wave35-r74-passed/child.json', 'Q')
    a['descendants'] = d.descendants(f.q, 'wave35-r74-passed')
    f.seal()
    print('child_witness_conflicting_attempt_id:', f.plan()['status'])
finally:
    f.doCleanups()
PY
```

Observed output:

```text
unrun_with_observed_end_counts_duration: READY FOR ROOT PUBLICATION CHECKS
child_witness_conflicting_attempt_id: READY FOR ROOT PUBLICATION CHECKS
```

These reproduce validation gaps; they are not passing safety assertions. Neither changes source or uses actual checkpoint inputs.

## SPEC findings

### S1 — Important: supplied child witness attempt identity can contradict terminal declaration

Location: `E/bac_checkpoint_contract.py:379`, especially JSON witness check at line 391. Receipt-side child `attempt_id` is checked against the terminal attempt, and candidate trees are checked. The JSON witness's supplied `attempt_id` is never reconciled. The second probe leaves the declaration bound to terminal `pass2`, supplies a hash-verified witness declaring `older-attempt` on the same candidate, updates the descendant inventory, and receives READY.

This violates the brief's exact terminal child-attempt binding when the witness carries an explicit contradictory identity. Retries may use identical source; candidate equality does not resolve the contradiction. The old selector has the same gap: inherited contract weakness, not regression or a finding against actual R81 execution.

Bounded repair: reject explicitly supplied witness attempt identity disagreeing with declared child/terminal attempt; add a same-candidate, wrong-attempt negative control. Do not require historical witnesses to invent a literal `attempt_id` or rewrite bytes. Where absent, preserve the limitation or use genuine recorded command/spec/parent-PID/candidate linkage under root review. Missing facts must not be fabricated; explicit contradictions must not pass.

### S2 — Important: UNRUN attempts may carry observed execution facts

Location: `E/bac_checkpoint_contract.py:328`. UNRUN requires a reason, null exit and null start, but end time, counts and duration are unchecked. The first probe supplies an observed end timestamp, 99 passed cases and positive elapsed duration to UNRUN; final plan remains READY.

These execution facts contradict nonexecution and undermine faithful distinction among unrun, partial and executed attempts, although this path cannot itself satisfy qualifying PASSED. The gap is inherited from the historical selector.

Bounded repair: reject observed end/count/duration claims inconsistent with UNRUN, preserve null/unavailable explanations, and add focused negatives. If execution occurred, preserve the actual executed/partial status rather than erasing facts. Keep supported null-UTC, finite-positive-duration qualifying runtime intact; no invented timestamps are requested.

## QUALITY assessment

The neutral contract/catalog split is coherent. Explicit historical readers check schemas, baseline anchoring, chain suffix/current pointer, predecessor/plan links and earlier-catalog reuse provenance. Plans bind contract bytes and ordered catalog metadata. Historical attempt/descendant/review/dependency checks are retained, nonfinite duration and boolean-worker handling strengthened, and terminal candidate path validated.

The successive-checkpoint test consumes neutral publication without per-ID code edits and exercises reuse from baseline, both historical formats and the new predecessor. Exclusive creation, exact replanning, selected-input/reuse rehashes, post-copy verification, content deduplication/aliases and named `.py.txt` snapshots are present. Draft/collision cases remain covered. No new defect was found in those reviewed paths; this is a finite assessment, not proof against every concurrent filesystem mutation.

Q1 — Important test gap: the 21 ported scenarios reject wrong receipt-side child pointers and wrong witness source trees, but not contradictory witness attempt identity on the same source, nor positive execution facts on UNRUN. The seven added methods do not close these gaps. Add S1/S2 controls, freeze new hashes, rerun the synthetic suite and independent review. Preserve historical source/test bodies.

## Deliberately unjudged boundaries

- Actual qualification truth, process/source execution, substantive independence, review approval, and receipt-versus-frozen-subject facts: separate root gates; structural byte integrity cannot prove them.
- Actual next checkpoint ID/terminal seal, interval/attempt/component completeness, real selection/assembly, authoritative manifest/chain/index, Git publication and remote/CI: not authorized or performed here.
- Application code/runtime, global type/coverage/hardware/whole-package acceptance and R81 qualification: outside the four-body packet; no application source read or execution.
- Full historical archive integrity/archived source behavior: metadata inspection only, no object-tree audit or baseline recopy.
- Hostile concurrent filesystem races after validation: not tested; workflow requires frozen inputs and cannot treat partial assembly as publication.

## Approval disposition

**Do not use these hashes as unqualified tooling approval for actual selection.** Repair S1/S2 only in authorized new tooling/tests, preserve old bodies and this review, then freeze/review/rerun changed bytes. Preserve the exact-model metadata limitation: distinct-agent review is evidenced, strict independently verified other-model identity is not. Root still owns truthful sealing, substantive qualification, publication and remote checks. No application, acceptance, Git or publication approval is granted.
