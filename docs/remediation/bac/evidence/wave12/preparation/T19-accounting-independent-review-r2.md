# T19 accounting R2 independent static review

Verdict: no blocking or nonblocking implementation defect found in this bounded additive producer slice. Static review only; no project imports, collection, pytest, compiler, formatter, lint or other runtime executed. This is not GREEN, integration acceptance, or programme closure.

Binding: base bc47e44662f7bea953156a668610a20e6bced9f2; frozen sum tree ed3cf26770875fc28dab25d89567dd65a19764fe. Working source SHA256 matches r2-candidate.json DATA for all four whole sources:

| Path | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py | 689 | 821fd3095e896a5b98d44a671906f9c5cbccec2f00fa430a6f5bb8acb24e4109 |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| src/townlet/exploration/adaptive_intrinsic.py | 226 | 80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9 |
| tests/test_townlet/regressions/bac/test_rnd_service.py | 610 | 0477b2531b8a1a109bf71285310c0beda725e295f11c51f61f6713005c2f6a62 |

1819 actual lines; approved projection2194 below5000. No fifth implementation/helper/probe/POP source inspected. Peer T19-implementation.md was read only as consumer-contract prose. Source diff base-to-tree confirms exactly the DTO and getter added to RND, and no OP/AI changes. Existing first422 test lines hash ecd2db6e72de5fba9453a6fff217d68113f6ff138c3c7a6cc9b5548e9e340c74, matching the supplied baseline.

## Contract evidence and refuted concerns

- RND lines309–325 construct a new frozen five-int dataclass from native fields and list length only. Native initialization, update arithmetic and validated full-state installation retain Python int values. No referenced mutable service/model/optimizer/FIFO object is exposed. There is no checkpoint export, clone, RNG call, forward, admission, synchronization or training in the accessor. Ordinary frozen assignment and later-snapshot ownership are tested at lines538–610.
- Direct legacy admissions are reconciled in update_predictor at line397 BEFORE its undersized-batch return. After a successful call the append-before/update-after consumer interval therefore observes actual admissions even for partial buffers. Getter timing between append and update is explicitly documented and tested at lines452–475; the temporarily unmatched occupancy/admission reading is intentional, not a missing synchronization defect.
- Actual update ordering is Adam.step, FIFO consumption, consumed-row increment and optimizer-update increment (lines413–419). Zero loss never selects the counter increment. Tests at479–506 use matching real networks, actual Adam post hooks and Adam moment steps, independently of the positive parameter-change control at435–449. Thus zero-loss successful work is not inferred from loss or queue occupancy.
- Configured admission returns real per-call receipts at377–386; native work is recorded by the same update_predictor path, including overflow service. Added configured cases at511–534 compare cumulative receipts with snapshots across both modes/all three policies, same-tick repeats, empty admission and later ticks; real optimizer hooks and Adam clocks corroborate work. Existing original cases separately cover exact dropped/FIFO rows, pacing and boundedness. Configured POP uses these receipts per peer contract; no guessed minibatch division is required.
- The source patch leaves service/update signatures, single-minibatch behavior, existing receipt fields, options, checkpoint keys/version, loading/atomicity and adaptive wrapper untouched. No checkpoint schema addition is necessary for this observation-only DTO. The existing native service optimizer counter intentionally excludes unrelated manual optimizer steps; existing test at407 and optimizer_step_offset preserve that distinction. It is not a universal Adam lifetime counter.

## Optional coverage and limits

Optional, not a defect or required repair: add an explicit new-view assertion immediately after full checkpoint restore (and after historical available-state import) to directly pin snapshot semantics across those operations. Existing tests already verify full saved native fields and continuation, and the new getter reads those exact fields without alteration. No source evidence indicates a restore regression.

Arbitrary external removal/replacement of public-buffer rows, concurrent access, or mixing unserviced external appends into the configured receipt protocol are not newly guaranteed by this view. The approved legacy consumer interval is serialized append plus update; configured consumer admission uses the actual receipt path. Review does not broaden those contracts or claim POP integration verified.

## Proposed bounded independent runtime, pending root scheduling

Run the five existing appended test functions in tests/test_townlet/regressions/bac/test_rnd_service.py (12 parameter-expanded cases):

- test_public_predictor_counters_follow_genuine_legacy_optimizer_work
- test_public_predictor_counters_bracket_legacy_partial_and_full_direct_updates
- test_public_predictor_counters_count_real_zero_loss_steps
- test_public_predictor_counters_agree_with_configured_receipts
- test_public_predictor_counters_are_frozen_owned_primitives_and_observationally_pure

Root-reported meaningful RED/55 collection and ongoing joint65/six guards are attributed to root, not this reviewer. Root remains sole runtime/integration/index owner. Only this ignored review receipt written; no source/index/commit/push/branch/worktree/source-copy/deletion/subdelegation action. Stationary.
