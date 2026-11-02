# T19 production authoring — frozen, producer adapter and root GREEN pending

Root reports meaningful R0: collection10PASS; actual owned9FAIL/legacy1PASS in49.0925s. Every new case completed real legacy2/5 fixture prerequisites and failed solely at the missing LaneOutcome assertion. Root verified all165 source hashes, absent CL, five actual process/import/thread identities,573configs/13artifacts/14worktrees and index custody, then closed runtime and explicitly cleared POP/EP/newCL authoring. Those execution/custody facts are attributed to root; this worker ran no tests.

## Candidate bytes and exact five-source inventory

| Alias / access | Path relative to `/workspace/hamlet` | Lines | SHA256 |
| --- | --- | ---: | --- |
| POP modified | `src/townlet/population/vectorized.py` |2315|`97e6c64c746414f1163b27a3c83329f8ccb2bce70676b53c1ffc34074caa9ede`|
| EP additive | `src/townlet/training/episode.py` |66|`5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9`|
| CL new | `src/townlet/training/clock_ledger.py` |36|`117caf9f2dfcc486d71284e6d9206f351eef690b6acf425f841beb3b3ba52571`|
| RC unchanged/read-only | `src/townlet/training/replay_contract.py` |222|`3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c`|
| test format-only | `tests/test_townlet/regressions/bac/test_outcome_clocks.py` |329|`b4f05ea4400b3aafa4696244b7a3ce897c36c9dbd209f1195f09ca427e1ef6c2`|

Actual2968 lines, within the same approved five-source POP3000/EP200/CL180/RC250/test500 projection4130. No sixth implementation/helper/probe source was inspected. Original test before authorized formatting:323 lines, `cc76ef887d5849e7ffd7c1a50c23eca77ef872102922c4adefc3a724ca33e86d`. Test changes are Black formatting only (read-only diff reports9 additions/3 deletions); all ten cases, parameters, fixture operations, assertions and scenarios remain unchanged by author edits. Root can compare its frozen R0 test packet independently. No project-source baseline copy was created.

Tracked read-only diff reports POP173 additions/4 deletions and EP47 additions/1 deletion; new CL is36 whole lines. POP's existing constructor, completion DTO, reset/step/flush APIs, replay transport, training schedules and checkpoint payload key set remain supported. Only owned POP/EP/CL source, authorized test formatting and this ignored receipt were written.

## Implemented public API and ownership

- EP retains existing frozen EpisodeCompletion unchanged and adds frozen LaneOutcome with every P5 field plus mandatory concrete world_id/world_episode_seq. Exact nonnegative integer identities, positive planned horizon, nonempty world ID and finite reward/entropy scalars validate at construction. Scalars are owned Python floats; the embedded DTO is copied with detached CPU observation/meter clones, so producer/legacy DTO mutation cannot rewrite the new envelope. Frozen fields prohibit rebinding; consumers must treat owned tensor readings as immutable event data.
- CL adds frozen/slots ClockLedger with all seven explicit units and validated nonnegative increments. POP replaces immutable ledger readings at actual advancing events, preserving previously held readings. `population.clock_ledger` exposes it; `completed_outcomes` returns the current episode's immutable tuple.
- `bind_episode_worlds(*, world_ids: Sequence[str], world_episode_seqs: Sequence[int])` copies and validates full lane geometry, unique concrete names and explicit integer sequences. `begin_batch_episode(index, planned_horizon)` pins that fresh binding, requires an explicit reset before rollout, and refuses reused batch identity or beginning over pending nonempty lanes. Another episode needs another explicit binding; IDs/sequences are never inferred from lane, batch, tick or labels. This validates declared caller DATA, not an unavailable ENV/bank identity attestation.
- Accepted reset clears current outcome tuple and canonical CPU-float64 lane reward/entropy accumulators without changing returned snapshots. A reset following explicit begin retains its pinned identity; ordinary unbegun/reset usage retains legacy DTO-only behavior. A reset without a new begin does not silently reuse the prior world's episode identity.
- POP accumulates only actual eligible reward/DAC component rows and retains the supplied all-column softmax entropy from the lane's last eligible predecessor-Q invocation. No static0 fallback, extra mutating curriculum call, legality reinterpretation or post-successor Q recomputation. `_finalize_episode` creates one complete envelope at the existing guarded completion boundary; external cuts retain the actual nonterminal successor/reason. Existing recurrent storage, survival tracking, adaptive completion callback, metric synchronization and hidden reset remain on the same once-only route.
- `commit_episode_outcomes(outcomes)` validates published events/content before mutation, is idempotent by `(batch_episode, agent_idx)` including reordered repeats, and permits partial publication while advancing completed_batch_episodes only when every lane of that batch is committed. It adds no death/adaptive callback. Retained commit history stores event fingerprints and batch IDs rather than tensors; changed-content duplicate commitments refuse. No new runner epsilon/checkpoint call is added here.

## Clock/service behavior and the exact pending producer contract

Vector ticks advance with existing total_steps; eligible transitions advance by the committed entry-active mask including terminal transitions once. Successful Q optimizer work advances its ledger once immediately after optimizer.step; readiness skips advance zero. Existing vector-based train frequency/PER and successful-update-based target/LR behavior remains unchanged. Committed batch episodes are independent of two lane events. Warmup/capacity still use existing retained replay transitions.

Configured RND, including adaptive `.rnd`, now calls the existing `admit_and_service(eligible_predecessor_rows, vector_tick=total_steps+1)` after replay admission. This is the accepted population vector tick, at the existing preincrement seam. Ledger admissions/drops use receipt deltas; predictor_consumed_minibatches uses **receipt.optimizer_updates** including mandatory overflow work. No loss-based inference or guessed batch division occurs. Empty-new-row shared service remains callable and can drain backlog. None loss maps to the existing float telemetry0.0 only; it never determines an update count. Actual preconfigured provider policy is consumed, not locally guessed/resolved/reconfigured.

**Pending dependency supplied explicitly by root:** reusable RND must add public `predictor_service_counters() -> frozen PredictorServiceCounters` with integer cumulative recorded admitted_rows, consumed_rows, dropped_rows, optimizer_updates and current pending_rows. Root's bounded provider supplier found no existing cheap complete public view; checkpoint_state clones model/optimizer/FIFO and is unsuitable per-step. This worker did not inspect or modify RND, guess private fields/payload keys, or call expensive checkpoints for accounting.

The POP unconfigured path now calls that declared pure view **before** its existing public-buffer append and actual single `update_predictor()` and **after** that exact work. It increments ledger by authoritative admitted/update/drop counter differences. Legacy append order, exactly-one-minibatch service, scalar loss return and pending tail behavior remain unchanged. The configured path continues to use the actual receipt directly. There is no silent zero/unobserved-work fallback and no configured-only restriction on qualified owned RND episodes. The producer view is a concrete callable integration dependency; **this candidate is not runnable/green against today's RND until root's separate serialized producer adapter slice supplies it**. Root owns that slice's RED/authoring/verification and all later candidate checks; no sixth source is absorbed into this worker's inventory.

## Explicit integration/identity/history limits

Existing checkpoint payload/version is unchanged. It contains total_steps and successful Q counters but no complete ledger/owned world-event state. To avoid presenting unknown historical units as genuine zero totals, the new ledger accessor explicitly diagnoses unavailable historical ledger restoration after checkpoint load or construction at nonzero restored tick. No lost eligible events, world identities, rewards, predictor counters or committed batches are invented. Existing checkpoint validation/load APIs still function; full native ledger/identity persistence and continuation remain mandatory T24/T25/later owner integration. This is an exposed provenance limit, not a claim of restored ledger coverage.

Current runner does not yet invoke the new begin/commit APIs or supply actual world binding. Unbegun legacy APIs continue producing their original completion DTOs; only explicitly bound/begun episodes publish qualified complete new envelopes. Production runner sink/epsilon/checkpoint integration remains mandatory under its finite owner. Shared curiosity stays shared, with its actual provider config/origin retained. No bank, world-local predictor clock, private RNG boundary, new controller dynamics, world binding attestation or strict-B isolation is claimed. Actual stable identity/stamp/private-service production remains PW/runner owners; every qualified new envelope here nevertheless requires concrete explicit identity rather than None/row-based guesses.

## Authorized formatter evidence and remaining root work

Executed only these approved code tools, twice as needed after the independent edits:

```text
.venv/bin/black src/townlet/population/vectorized.py src/townlet/training/episode.py src/townlet/training/clock_ledger.py tests/test_townlet/regressions/bac/test_outcome_clocks.py
.venv/bin/ruff check --select I --fix <the same four files>
```

Final Black:4 files left unchanged. Import-order-only Ruff:all checks passed. These do not constitute broad lint, type, compiler, collection or runtime verification. Text reads, hashes/counts and owned-path read-only diff are the other inspection operations.

No project import/runtime/compiler/pytest/collection, Ruff general lint, other static checker, index/staging/commit/push, branch/worktree/checkout/source-copy/deletion/subdelegation occurred. Existing14 worktrees and all unrelated capabilities/options/history were preserved. Root owns dependency completion, GREEN, focused/owner/B03/B11 witnesses, six guards, fresh actual Astra-medium review, actual-patch earlier-full-trigger assessment/G3 and integration/exact-tip CI. Full-suite status and all runtime/static gates:NOT RUN by this worker. No repository-green claim.

**Disposition:** POP/EP/CL authored and frozen; authoritative legacy producer-counter adapter explicitly pending. Stationary for root's serialized dependency work and GREEN/review.
