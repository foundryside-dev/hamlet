# FIX1 independent scoped tooling and process review

2026-11-13. **S1 ADDRESSED; S2 ADDRESSED; Q1 ADDRESSED. SPEC/QUALITY: approved for this bounded FIX1 tooling repair at the exact hashes below.** No new breakage found in the two changed guards or their interactions with the retained synthetic suite. The process replacement draft is factually consistent with these changes and the previously reviewed tool. This closes the original review's two code/test blockers; it does not establish actual checkpoint qualification, publication approval or exact other-model runtime identity.

## Scope and independence

Same independent reviewer agent: `/root/bac_checkpoint_contract_review`. This follow-up covers S1/S2, their regressions, and factual accuracy of the supplied FIX1 process draft. It does not reopen unrelated application/archive work. Prior findings and original review remain preserved at SHA-256 `b4d773b33374bb3866acf3004565e0dec166f058a0899c7c5a78974d3f1c66bc`.

Producer was explicitly selected as `gpt-6-astra` medium; this reviewer used the default/inherited model without an override. Distinct agent identities and this independent run are evidenced. The visible reviewer identity remains ChatGPT/Codex based on GPT-6; no more precise runtime identifier is exposed. The original exact-other-model metadata limitation remains, and this approval does not upgrade it.

The four-body packet totals 2,047 lines, measured before scoped reading. Read the supplied diff, actual changed source/test sections and surrounding guards, author FIX1 report amendment and process draft. Verified the diff accounts for every source change by reversing its hunks in memory against the frozen new files: reconstructed bytes hash exactly to the original reviewed implementation and test hashes. No reconstructed source was written, imported or executed. Historical bodies remain unchanged. No additional implementation body was read.

## Frozen identities

E = `W/evidence-management`; P = `W/wave35-preparation`; W = `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades`.

| File | Lines | SHA-256 verified before and after rerun |
| --- | ---: | --- |
| E/bac_checkpoint_delta.py | 469 | 33e992e31a2bfcdb0fa70fac315acc92ec3e961831b0d612c2ba8148c16ef8f8 |
| E/test_checkpoint_delta.py | 389 | 8af61971bf01a7e2045d344fabad87905af4aaf0b5004418ecf98fa9e13941e2 |
| E/bac_checkpoint_contract.py | 573 | 6fc6845ccb73e9bc8a0e24837bf005b0d2cd156107cb8a8341ded9012b7c54b3 |
| E/test_checkpoint_contract.py | 616 | b0dd9f8a3f7420771f237cc35be453040b134924a59225d1ba7c5fdb88a0d07d |

Additional reviewed artifact hashes:

| Artifact in P | SHA-256 |
| --- | --- |
| T18e-R0-NEXT-CHECKPOINT-TOOLING-FIX1-SCOPED-DIFF.txt | f1173ed4e0ca88447e15b92475141b77a4ba9337aa800642403d1785f8e737ce |
| T18e-R0-NEXT-CHECKPOINT-TOOLING-REPORT.md, with FIX1 amendment | 13b9190ae664255af62dfeb92804dfdc1eb79b50e71a1546db44db9cec2e7aa0 |
| T18e-R0-EVIDENCE-PROCESS-NEXT-FIX1-DRAFT.md | 60e8430c485e8d0881674498700663fa195250cc3cc8ab776a4abc17ac6e1824 |

Reverse-diff verification reproduced original implementation SHA `66f62969169247eaf3ff90a5859018801bcb87f897fb032857bd263d480eb0d8` and original test SHA `f17f102f486a5c5256e68326624949387a0cf9e1aeebf71eac9e688f3181376b`. Thus only the two guard changes and two added synthetic methods differ from the original reviewed sources.

## Actual independent execution

Working directory E, same host Python 3.12.14. Exact command independently executed:

```sh
python -B -m unittest test_checkpoint_contract.py
```

Observed exit code 0:

```text
..............................
----------------------------------------------------------------------
Ran 30 tests in 0.608s

OK
```

This is one independent rerun of the 30 synthetic methods, not 30 new application cases. Author RED-six-failures/GREEN-two-tests and root's separate rerun were supplied as provenance; they were not independently recreated or counted as distinct cases here. I did not revert source to reproduce RED.

## Findings disposition

**S1 — ADDRESSED.** In `bac_checkpoint_contract.py:392`, the JSON witness is parsed once and still checked for matching candidate tree. A present `attempt_id` must equal the receipt child's attempt ID, which the existing qualifying-child guard binds to the terminal attempt. The added `test_child_witness_attempt_identity_matches_terminal` at test line 433 rejects `older-attempt` on the same candidate and accepts matching `pass2`. Existing fixtures with no literal witness attempt ID remain accepted by the unchanged tests. No historical identity field is fabricated or required retroactively.

The finite repair intentionally does not validate alternative spec/result/PID linkage. For an actual witness without a literal attempt ID, root must retain that limitation or establish genuine recorded linkage to the exact terminal execution. Candidate equality alone does not prove it. This remains a root evidence obligation, accurately disclosed by both the amended report and process draft; it is not a claim that a generic linkage validator was added.

**S2 — ADDRESSED.** In `bac_checkpoint_contract.py:328`, UNRUN requires an explicit reason and all five execution fields (`exit_code`, `started_at`, `ended_at`, `counts`, `duration_seconds`) absent/null. The new `test_unrun_rejects_observed_execution_facts` at test line 415 independently resets the tested fields, then rejects recorded end time, positive counts, empty counts, positive duration and zero duration. It accepts absent/null facts with an explicit unavailable-custody explanation. These checks close the reproduced contradictions without treating zero or empty observed values as unknown facts.

**Q1 — ADDRESSED.** The two focused methods cover both inherited gaps and positive controls. The existing duration-only qualifying-runtime test still passes, retaining null UTC with a genuine elapsed duration and explanation. Existing wrong-source/wrong-terminal-child, failure preservation, mixed directory, catalog, drift, exclusive assembly and successive-checkpoint regressions also pass. No historical source/test was changed to obtain the result.

## Process draft factual review

The exact FIX1 draft correctly describes the five null-only UNRUN fields, conditional reconciliation of a supplied JSON witness attempt ID, and the distinction between that mechanical check and root's alternative-linkage duty. Its frozen source hashes/line counts match the files tested here. The contract/receipt/plan/assembly schemas, command templates and neutral future-publication description agree with the previously reviewed implementation; FIX1 does not change those interfaces.

The draft clearly marks WIP15/R81 as tentative until root sealing, disclaims actual next-checkpoint operations, preserves historical formats/bytes, and keeps qualification, substantive independence, failed gates, source-equivalence and publication/remote checks separate. Approval of this draft is scoped factual review for the proposed process text, not attestation that its historical/application status claims were freshly audited or permission to edit tracked process/navigation files.

## Boundaries and disposition

No application runtime/import, actual archive selection/assembly, extra source body, Git/index/remote action, branch/worktree/checkout/source execution copy or delegation occurred. Test mutations/cleanup stayed within authorized temporary synthetic DATA. The only persistent reviewer write is this new FIX1 review; the original review is preserved. Application R81 remains frozen.

The original S1/S2/Q1 tooling objections are resolved at these hashes. **The bounded FIX1 code/tests and supplied process draft pass this scoped independent review.** Root may treat this as completion of the finite code-review repair gate, subject to the explicit model-identity limitation. Genuine terminal/attempt/component sealing, alternative child linkage, substantive independence/qualification, real integrity selection, authoritative publication, Git approval and exact remote/CI remain separate root responsibilities. No acceptance waiver or approval of those operations is granted here.
