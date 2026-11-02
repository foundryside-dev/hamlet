# T19 accounting implementation — frozen handoff

Production authoring completed following root's explicit clearance after its
actual meaningful RED at R1 tree3e59b4d8. Root reported all55 service cases
collected and first appended genuine legacy optimizer-work test failed solely
at the missing public view after real Adam work. That runtime evidence belongs
to root; no worker runtime/pytest/collection or GREEN claim is made.

## Exact additive changes

In src/townlet/exploration/rnd.py only:

- Added frozen dataclass PredictorServiceCounters (line22), with the exact five
  primitive integer fields admitted_rows, consumed_rows, dropped_rows,
  pending_rows, optimizer_updates.
- Added public RNDExploration.predictor_service_counters() ->
  PredictorServiceCounters (line309). It constructs an owned immutable snapshot
  from the four native cumulative counters and len(obs_buffer). It does not
  synchronize counters, admit/service/train, touch RNG, export checkpoints,
  forward models, export optimizer state, or clone networks/optimizer/FIFO.
- Documented that unserviced external appends change occupancy immediately,
  while recorded admissions update in the next update_predictor call, even
  for a partial batch. Caller legacy intervals begin before append and end
  after the genuine update. Snapshot reads never reconcile these counters.

No prior service algorithm, API/signature, checkpoint key/version/roundtrip,
receipt, option, model, optimizer, RNG, or shared alternative behavior changed.
No imports were added. OP/AI remained read-only and byte-identical.

## Test preservation and authorized formatting

No test edits were made during production authoring except running exactly:

    /workspace/hamlet/.venv/bin/black src/townlet/exploration/rnd.py tests/test_townlet/regressions/bac/test_rnd_service.py

Exit0: one test file reformatted, RND left unchanged, wall0.873013267s.
Default Black safe mode was used (no --fast), retaining its AST-equivalence
safety check. No separate compiler/AST/import/collection/lint command was run.
Original43 cases and appended12 cases retain every assertion/scenario; five
appended test functions remain. Original first422 lines still hash to baseline
 ecd2db6e72de5fba9453a6fff217d68113f6ff138c3c7a6cc9b5548e9e340c74,
providing stronger byte-level preservation for all original tests. The appended
suite changed only through Black's default AST-safe formatting.

Appended test function locations now:

- line435: test_public_predictor_counters_follow_genuine_legacy_optimizer_work
- line452: test_public_predictor_counters_bracket_legacy_partial_and_full_direct_updates
- line479: test_public_predictor_counters_count_real_zero_loss_steps (2cases)
- line511: test_public_predictor_counters_agree_with_configured_receipts (6cases)
- line538: test_public_predictor_counters_are_frozen_owned_primitives_and_observationally_pure (2cases)

Their exact expanded IDs/contracts remain as recorded in
T19-accounting-test-authoring.md. The cumulative receipt cases cover both modes
and all overflow policies; real zero-loss actual Adam steps remain independent
from the positive parameter-change control. Purity guards and owned/frozen
primitive assertions all remain intact. No checkpoint cloning per accounting
step was introduced.

## Frozen hashes and complete context counts

| Source | Full lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py | 689 | 821fd3095e896a5b98d44a671906f9c5cbccec2f00fa430a6f5bb8acb24e4109 |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| src/townlet/exploration/adaptive_intrinsic.py | 226 | 80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9 |
| tests/test_townlet/regressions/bac/test_rnd_service.py | 610 | 0477b2531b8a1a109bf71285310c0beda725e295f11c51f61f6713005c2f6a62 |

Four whole files only, total1819 lines; projected
800+294+300+800=2194<5000; each file below its approved cap. No fifth helper,
probe, or imported implementation inspected. Task metadata receipts only are
additional reads/writes. This implementation receipt is ignored, confirmed
with git check-ignore.

No project runtime/imports/compiler/pytest/collection/lint checks, index
mutation, staging, commit, push, branch/worktree creation, source copy/deletion,
or delegation performed. The only executed project tool was explicitly
cleared Black on the two owned files. All14 worktrees remain under root custody;
worker performed no worktree operation. No producer prerequisite required or
service counter synchronization change made.

Stationary. Root owns GREEN, fresh independent Astra-medium review, global
custody checks, and any further integration/index/runtime action.
