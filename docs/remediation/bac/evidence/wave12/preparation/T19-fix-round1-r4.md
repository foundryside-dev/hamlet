# T19 R4 core repair round1 — authoring frozen, root verification pending

Root's meaningful R3 evidence: new14 cases produced7FAIL/7PASS in30.3607s with no errors and source/import/config/artifact/worktree custodyPASS. Four failures demonstrated exposed canonical observation/meter mutation, two demonstrated lost delayed/partial commitment authority after valid reset, and one demonstrated the actual compiled WAIT-only A=1 finite world's entropy failure. The singleton configuration/mask prerequisite is now root-proven. Scalar forgery, duplicate begin/reset/history, actual POP unconfigured accounting and three nonfinite-Q-before-physics controls passed. Original ten cases remained byte-identical. All those execution facts are attributed to root; no execution was repeated here.

Root closed runtime and cleared this production repair for the three required findings plus the optional-loss guard violation. Only POP and this new ignored receipt changed. EP/CL/RC/tests and separate producer sources/review/evidence were not edited. No next package was started; the user-requested halt remains after root completes current T19 verification/publication.

## Exact candidate inventory

| Source relative to `/workspace/hamlet` | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` repaired |2329|`629efddfd259aa5bc39f8c4c119b506f1c1eeb17b338c564751dc0ddc820cd92`|
| `src/townlet/training/episode.py` unchanged |66|`5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9`|
| `src/townlet/training/clock_ledger.py` unchanged |36|`117caf9f2dfcc486d71284e6d9206f351eef690b6acf425f841beb3b3ba52571`|
| `src/townlet/training/replay_contract.py` unchanged/read-only |222|`3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c`|
| `tests/test_townlet/regressions/bac/test_outcome_clocks.py` unchanged |538|`66069b051f1165ee50a15cc106aac0919f3447f9ef0ed1395aeaaa70e5dc21e9`|

Actual3191 lines, within the same-five-path projection4280. POP was2315 lines/hash `97e6c64c746414f1163b27a3c83329f8ccb2bce70676b53c1ffc34074caa9ede`; no sixth implementation/helper/probe was read or written. The whole owned test hash is identical to meaningful R3, preserving all24 parameterized cases and every assertion/scenario, not merely the original ten-case prefix.

## Exact remedies

**Returned tensors and canonical publication authority:** `completed_outcomes` now returns `tuple(replace(event) for event in private_current_outcomes)`. Existing LaneOutcome construction already clones both embedded DTO tensors to detached CPU ownership, so every public reading has its own tensor storage. Mutating an exposed sink reading cannot rewrite another sink's fresh read or POP's private current canonical envelope. Frozen scalar/rebinding semantics are unchanged. No read returns the actual private tuple's LaneOutcome objects.

At the once-only finalizer publication boundary, POP now computes and records each canonical envelope's fingerprint before public exposure. `commit_episode_outcomes` validates against that publication-time fingerprint, never against a later recomputation from exposed objects. Forged tensor/scalar content is rejected both before and after first commitment; validation of the entire incoming sequence still precedes any committed-identity/counter mutation.

**Delayed/partial commitment across accepted reset:** publication fingerprints are retained separately from the current-episode outcome tuple. Reset still clears the current tuple/episode accumulators and preserves its existing accepted behavior; it does not erase publication authority. An old legitimate never-committed event can therefore commit after reset, including completion of a partially committed batch. Reordered replay remains idempotent through existing event/batch bookkeeping, and changed-content old replay still refuses against the original fingerprint. Only fingerprints/identity metadata persist; old episode tensor payloads are not retained solely for authority. No commit-before-reset requirement, delayed-publication restriction, added adaptive callback or scope downgrade was introduced.

**Singleton action entropy:** eligible predecessor Q values are explicitly checked finite before entropy handling. A one-column finite vocabulary produces exact zero entropy with `zeros_like` on that column, representing its deterministic action. Width>1 retains the original all-column softmax, epsilon-inside-log sum and log(actual-width) normalization expression unchanged. The existing finite-entropy check and last-eligible snapshot remain. NaN/infinite Q never enter the singleton-zero branch, and rejection remains before physics; no static-curriculum/global invalid-input zero fallback was added.

**Optional predictor loss / unchanged guard ceiling:** replaced the added conditional expression with explicit `if receipt.last_loss is None: last_rnd_loss = 0.0; else: last_rnd_loss = receipt.last_loss`. This preserves existing float telemetry for a no-minibatch receipt while actual ledger work continues using authoritative receipt.optimizer_updates. No loss inference, provider work change,612 ceiling increase or whitelist/guard relaxation occurred. Root still must run the actual guard to verify the reported613>612 violation is resolved.

## Preservation and limits

Existing completion DTO/reset/flush behavior, nonterminal external-cut successors, configured shared backlog/overflow/drop service, unconfigured direct-one-minibatch accounting, Q/predictor clock units, fresh explicit concrete world binding and batch commitment semantics remain unchanged. No RND/OP/AI/RC or separate producer source was edited. Retained identity/fingerprint metadata remains run-length bookkeeping as previously disclosed; the review's optional P3 is not addressed by weakening replay guarantees.

Ordinary reset still drops owned mode when not explicitly begun; qualified envelope identity remains mandatory, with no inferred world sequence. The historical checkpoint ledger-accessor diagnostic and native ledger/identity persistence limits remain unchanged. Full runner/bank/private-clock/native-checkpoint integration retains its finite later-owner obligations; none is relabeled complete here. This repair closes current canonical publication/singleton/lifecycle behavior without starting those packages.

Executed only authorized Black formatting and Ruff import-order repair on POP:

```text
.venv/bin/black src/townlet/population/vectorized.py
.venv/bin/ruff check --select I --fix src/townlet/population/vectorized.py
```

Black:one file left unchanged. Import-order-only Ruff:all selected checks passed. These are formatter/import-order results, not general lint, type, no-default, collection, runtime or GREEN evidence. Other operations were bounded text reads, hashes/counts and this prose write. No project runtime/import/compiler/pytest/collection/general-lint, index/staging/commit/push, branch/worktree/source copy/deletion or subdelegation occurred; all14 worktrees remain preserved.

**Disposition:** candidate source frozen. Root owns actual GREEN for all24 cases, fresh scoped independent rereview, producer/owner gates and mandatory full gate before source checkpoint/release/halt, then complete T19 evidence commit/push. No runtime pass or finding self-closure is claimed here. Stationary; no next packet.
