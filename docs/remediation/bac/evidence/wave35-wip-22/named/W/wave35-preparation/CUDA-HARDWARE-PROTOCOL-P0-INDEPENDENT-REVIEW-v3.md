# P0 amendment freeze v3 — independent implementation review

2026-11-14T06:19:38.707162+00:00. **Changes required before adoption.** One P2 SPEC finding remains; no broader architecture change is requested.

## Finding: fixed job layout weakened to arbitrary descendant

Accepted `allocation-cpu-private-addendum-proposal-v2.md` specifies output_root/attempt_id/job_id and scratch_root/attempt_id/job_id. The frozen module `_layout` (lines 305–319) checks only strict descent under root/attempt_id. Both an unrelated basename and a nested path are accepted for each job destination. Interface-contract-v3 likewise publishes the weaker descendant rule. This makes the normalized transport inconsistent with the root-approved P1/P2 layout and allows different consumers to choose different job directories.

Four independent actual-module mutations demonstrate acceptance: wrong-job-id output, wrong-job-id scratch, nested/job output, nested/job scratch. Require exact equality to root/attempt_id/job.id for request and spec, update sealed interface metadata and add bounded regression cases. Existing exclusive-creation/no-follow checks and P2 race duties remain mandatory.

## Verification

- Frozen module SHA-256 `ea1187c4088c05e4009beb1667ed02a205285e42be671069724b651ce23faf68` (520 lines).
- Author tests SHA-256 `43942fe7231f1378028af1c12a12a34eacce9122d3d8ed95437db9faaf707425` (601 lines).
- Independent tests SHA-256 `f60c019231ef2ecf7f1a2298b97c81198e4771df5ec8a213cf5b378f411ee4a5` (232 lines, below 500-line probe cap).
- Independently rerun author suite: **127 passed**, exit 0 (`independent-review/author-suite-v4.json/.log`).
- Independent literal fixtures/adversarial suite: **44 passed, 4 failed**, exit 1 (`independent-review/independent-suite-v5.json/.log`). Earlier 22 probes remain included; counts are not summed into application coverage. New probes cover exact timeout/grace and required fields, role reservation proof fields, replacement×peak accounting, serial-vs-concurrent CPU/RAM and cumulative storage, nonterminal evidence, completed-unverified/nonzero/signal precedence and fixed layout.

Each execution record preserves exact argv, cwd, explicit environment, UTC start/end, result and matching source-before/source-after hashes. Source, schema and interface references from freeze-v3 were independently hash/length verified. Prior independent probe bytes were retained before amendment, and exact revised probe bytes retained as inert text. Only the same three authorized bodies were inspected/authored/executed; no other tool/application body, hardware, server, Git or mutation operation occurred.

The remaining amendment is consistent with accepted finite scope: actual runner controller cannot replace job-controller custody, child envelope lacks terminal/log fields, zero exit with missing proof remains unverified, peak demand is explicit rather than inter-op-width inferred, and private grant/probe/allocation semantics remain mandatory consuming-tool checks. These observations do not certify behavioral evidence or hardware. Root owns a bounded correction authorization and adoption; source stayed frozen during this review.
