# T19 full orchestration scoped independent re-review

Actual reviewed helper: /workspace/bac-review-2026-11-01/qualification/qualify_wave12_full.py
Actual SHA256: 81fdb2c535590960c13fcc8137870fb66be62436f2217656022d872758408305

Verdict: all four material findings from T19-full-orchestration-independent-review.md are addressed. No open material finding in this scoped helper re-review. This is static approval of the corrected orchestration checks, not evidence that collection/full runtime has executed or passed.

- Current manifest hash, base and candidate tree are now explicitly compared to saved preflight before processing full results. Existing stationary checks therefore bind to the same frozen manifest as the result.
- stationary() now requires exactly573 configuration and13 artifact digests, in addition to checking every listed byte hash and the complete14worktree registry.
- Collection now explicitly requires0<selected<=total before comparing both numbers with root's expected counts.
- Preflight now records each prerequisite result JSON digest and its manifest path/digest, including all six guard results. Postflight rechecks each result JSON hash, its referenced log hash and its manifest hash. Previously pinned reviews/harnesses/prerequisite declaration remain checked as before.

Previously noted optional freshness and internal worker-label checks remain optional; they do not reopen the four material findings. Root continues to own unique run tags, truthful prerequisites after actual reviews/direct checks, frozen source/index/tracked-doc custody, and the actual full-gate execution. No broadened wholeBAC/G3 closure is inferred.

Read only the same fifth helper source; no wrapper/plugin implementation, core source or sixth implementation read. No runtime/import/compiler/pytest/collection/lint executed. Producer four-source binding and independent12PASS receipt are unchanged. Only this ignored re-review receipt written. Stationary; no next-package work.
