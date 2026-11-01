# Review provenance

Final scoped source/spec review at tested tree `f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48`, identical to qualified source `495360d68c167b741d8ed5016c0921f995aac1f4`. Coordinator runtime is attributed; this artifact does not assert independent runtime unless its body does.

Original `T13-owner-tests-independent-review-r4.md`, SHA256 `7e315458a043df32e1e0633738658ec265c1b3075a3f147ac8999e8a3c6c2c9e`, retained unchanged; portable rendering normalizes execution paths.

# T13 existing-owner tests — independent static review R4

Date: 2026-11-01 UTC. Reviewer: /root/bac_astra_t13_owner_tests_r1, continuing the independent Astra medium owner-contract lens. Existing MAIN /workspace/hamlet only.

## Findings and scoped verdict

No P1/P2 defect found in the actual R4 four-file public producer/owner-test contract against approved P3 and History A. The new guard restores the original count-bearing public empty-sampling diagnostic without weakening the existing owner assertion. This is a static scoped verdict, not runtime GREEN or whole-T13/BAC closure. No optional cleanup is requested; root previously confirmed the core covers clear-ID non-reuse.

## Exact identity and inspection scope

HEAD: 41edeb0858cba98a8dcb6ba2af36355457ef4e0a.
R4 candidate tree: f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48.
Manifest: .superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave07/green-r4-candidate.json.
Compared actual four-file diff from reviewed R2 tree e29a9cba67f98960efd29013a284d86997ef2ab5. It contains only seven added lines in PB.sample; all three tests are byte-identical. Prior complete four-file assessments remain applicable to those verified unchanged bytes. The changed public method and its downstream behavior, history/load boundary and relevant owner assertions were reread in context. No fifth source was opened.

| File | Whole-file lines | SHA256 before/after |
| --- | ---: | --- |
| src/townlet/training/prioritized_replay_buffer.py | 1092 | 290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9 |
| tests/test_townlet/regressions/bac/test_per_history.py | 342 | 4ea99d20fa18333d249b0ce1408b91c99c12194e6d7ddcd0788c5b4f8c492da1 |
| tests/test_townlet/unit/training/test_prioritized_replay_buffer.py | 1042 | 52db935fa6ede75d87abacbf22de3f13415463e880b65c2d78114464ff15affa |
| tests/test_townlet/unit/training/test_prioritized_replay_buffer_components.py | 502 | b6dd85342a68223394786c0c6c4a80c4af45662b77df7972689067e7e50ebaaf |

Exactly four complete implementation/test files charged,2978 lines, all helpers inline. Fresh HEAD/hash/line-count checks matched the dispatch and manifest. Before/after read-only GIT_OPTIONAL_LOCKS=0 git diff --cached --quiet f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48 and GIT_OPTIONAL_LOCKS=0 git diff --quiet each returned0. git check-ignore confirms this report is ignored. R1 and R2 reports are retained unchanged.

## Public guard assessment

PB.sample now rejects only a positive int/np.integer request exceeding size_current, explicitly excluding bool and np.bool_. Empty active replay with sample(1) therefore raises ValueError("Buffer size (0) < batch_size (1)") before invoking the sampler. Existing populated size5/request10 retains exactly the count-bearing diagnostic required by U. Valid B<=N bypasses the guard and still follows the same float32 legacy sampling path. Zero, negative, float, boolean and other invalid count inputs bypass this guard and remain subject to the existing sampler validation; they are not accidentally accepted or normalized.

The guard performs no mutation, draw, allocation, ID change, archive access or RNG operation. It does not count archived rows toward size_current, synthesize active replay, or turn an archive into a sampler. After an approved old4 import, active size0 remains meaningful and unavailable; the restored public error is compatible with History A's fresh-qualified-replay policy. No formula, draw law, beta pacing, dictionary float32 weight transport, writable physical index copy, qualified float64 receipt, configured Generator ownership or stable unit mapping changes occur.

An oversized valid request now diagnoses insufficient active count before deeper sampler validation; that is the specifically restored public boundary. This does not authorize accepting malformed priority data or changing the valid sampling path. Core numerical and sampler validation remains independently reviewed outside this source slice.

## Complete owner-contract preservation

The unchanged tests retain exact34-key current6 equality and explicit legacy-constructor metadata/closed RNG descriptor. Empty/partial/wrapped stable IDs and counters stay exact, including physical receipt indices [2,0,1] versus stable IDs [2,3,4] after overwrite. Current version6, supported4/5/6 messages, genuine future7, float5.0/6.0/True and old4 type refusals remain precise.

Independent exact19-key PER4 fixtures retain archive ownership, query/export/source-digest equality, fresh active0, available beta, full-resume refusal, archive preparation failure atomicity, corruption refusal and current embedded archive roundtrip. Exact27-key captured5 continues through its full-resume adapter with deterministic absent IDs; no5→old4/fresh0 substitution or forged fixture is introduced. Valid captured5/current6 state keeps rows, masks, components, priorities, beta, position and archives. Old4's inspection maximum remains separate from active5/6 conversion validation.

R2's shared insertion-priority conversion and coherent maximum update are unchanged. Accepted original maxima remain unmodified at restore; new storage commits cover float32 upward rounding. Strict schema/corruption/configuration/priority dtype controls, pure validators, input/runtime immutability, component optionality/presence/alias checks and mask alignment remain intact. No assertions were broadened, skips added, key-set equality weakened or test expectations edited to hide the reported failure.

## Evidence, governance and limits

Root reports the R3 affected compact-owner result1 failure/104PASS at the original empty archived.sample(1) regex, followed by this producer-only repair. This is attributed evidence; the fifth test source was not opened. Root is running R4 global collection, core/native/history/consumers and six guards. This reviewer does not infer their results or reproduce execution.

Previously read AGENTS/CLAUDE/STATUS, approved T13/P2/P3 and review/verification skills remain applicable. Preservation and History A override generic compatibility deletion. Explicit static/stationary dispatch governs this pass. No durable rule was saved, user-only fallback was not adopted, and a failed rule grants/restricts nothing; existing instructions and actual approvals govern. Permission for this report does not fan out.

No runtime, project import, collection, pytest, probes, helper execution, source/test mutation, index/staging/commit/write-tree, branches/worktrees/checkouts, source copies/deletion or subdelegation occurred. Only this requested ignored report was written. No PS/HC/RC/POP/RewardTensor/native/core-test or compact-owner fifth implementation was read.

focused_commands: none executed.
owner_suite_commands: none executed; root owns actual R4 affected owners.
static_commands: read-only source/diff/hash/line-count checks only; lint/type/guards unrun here.
review_record: this report, retaining R1/R2.
full_suite_status: unrun by reviewer, root-owned.
full_suite_reason: explicit bounded static review; mandatory affected-boundary/full qualification remains.
unrun_checks: R4 collection/import, core/native/history/consumers, six standing guards, full4worker.
next_full_gate: root's required full4worker before affected dependent release, under existing cadence.

X04/T15 P1, native T24/T25 qualifications and final whole-BAC gates remain OPEN. Stationary after this report.
