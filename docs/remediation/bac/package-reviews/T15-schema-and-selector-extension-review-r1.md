# T15 schema and selector extension — Astra medium technical review r1

Verdict: **APPROVE both finite corrections.** Removing the obsolete batch/minimum proxy adds supported configurations while preserving actual sampling requirements. The ICM-specific selector boundary control tests the required selection behavior without claiming its currently broken reward integration works. No material T15 scope weakening or owner permission for capability removal is involved.

This continues the existing technical review; the programme remains66 tasks/54 effective requirements/22 final lenses. Earlier accepted construction/restore/learner/X04 requirements stand. This is technical approval, not implementation review or executable acceptance.

## Evidence and exact context

Observed HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`; root supplies RED candidate tree `f806eee4`. Root reports123 failed/4 passed. Read the data receipt `/workspace/bac-review-2026-11-01/qualification/wave09-red-r2/blocked-prerequisites.json`, SHA256 `3f49ef372169e401a68e411dd3296c91e6f3ece4f94ef579d361d4953e019274`. It records five compile refusals before the intended readiness assertions and the actual ICM observation-only reward failure. Those six blocked cases are not valid causal RED for their intended T15 assertions. This reviewer did not rerun the campaign or inspect its test implementation.

Exactly one added whole source: `src/townlet/config/training_v2_config.py` (TV), **443 lines**, SHA256 `d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68`. Combined context is now **5 whole files/2893 lines**:

| Source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/population/vectorized.py` | 1854 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| `src/townlet/training/replay_contract.py` | 222 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| `src/townlet/training/q_targets.py` | 80 | `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f` |
| `src/townlet/config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| `src/townlet/config/training_v2_config.py` | 443 | `d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68` |

No sixth source, test, fixture or helper was opened. Previously supplied flat/sequential/provider contracts remain prose evidence. The now-existing staged learner test was observed by filename/status only. This review context cannot also read that test as an uncounted sixth source; later implementation verification must retain its own bounded slice.

## Schema extension and exact runtime invariant

TV106–108 declares positive capacity, batch_size and min_size. TV110–118 correctly retains min_size<=capacity. TV120–128 separately rejects every batch_size>min_size with the explanation that one cannot sample more transitions than the minimum buffer size. That explanation incorrectly equates a declared warmup threshold with actual available units, and ignores replacement sampling. The five recorded parse failures follow this exact validator.

Delete only `validate_batch_size_le_min_size`; clarify min_size as the minimum retained eligible-transition warmup, with actual sampleability checked independently. Keep all existing positive bounds, min_size<=capacity, extra-field refusal and the remaining schema rules. Do not introduce an equivalent blanket batch<=capacity or batch<=min constraint elsewhere. All previously valid configurations stay valid, and no authored minimum is silently raised to B or reduced to unblock a test.

The accepted invariant is **scheduled opportunity AND retained eligible transitions >= authored min_size AND backend readiness for the selected sampling law/window policy**. Be precise about cardinality:

- Flat uniform and flat successive PER require at least B retained sampleable rows. With min_size1/B3 and only one or two rows, warmup may be satisfied but sampling must still be unavailable; no draw or optimizer/LR/target advancement occurs.
- Flat replacement PER can draw B3 from one sampleable row after min_size1 is met. Nonempty support is required. Duplicated samples retain the accepted weighting and stable-ID update semantics.
- Recurrent warmup counts retained transitions, while B counts sampled window/context units. Successive recurrent PER requires B distinct sampleable units, not merely B retained transitions. A retained count alone cannot prove that windows exist. Replacement recurrent PER and the accepted with-replacement uniform sequence adapters may serve B greater than their positive sampleable-unit count.
- Fixed-full impossible/window-unavailable diagnostics and adaptive real-prefix behavior remain. For example capacity1/L8 fixed-full is still unavailable even though min_size1 is met. Declared batch and warmup becoming separately authorable does not create padding, windows, or permission to sample an empty population.

This is the existing P2/P3 contract expressed correctly at authoring/runtime boundaries. The DTO lacks the selected replay family/window population and cannot replace backend sampleability. Retain meaningful schema positive/negative controls and the existing runtime law/readiness controls; rerun the five previously blocked cases to obtain causal evidence rather than relabeling their old parse failures. Any old test that solely expects B>min rejection belongs to its existing bounded owner for a contract-preserving correction; other validation negatives remain.

## ICM selector boundary correction

The data receipt shows real ENV reward evaluation calling `compute_intrinsic_rewards(observations, update_stats=True)` and genuine ICM raising: “ICM reward requires actual predecessor/actions/successor; use compute_transition_novelty.” The prior source-verified provider receipt already establishes that ICM inherits the epsilon selector and requires actual transition context for reward/training. This is a real required integration gap, not evidence against selector eligibility.

Approve the proposed ICM-only control:

1. Execute a genuine plain-epsilon population/environment step to establish the intended inactive lane through actual lifecycle state. Do not fabricate dones or replace reward computation.
2. Install the genuine ICM provider through the existing attachment mechanism, retaining the same population/lane state. Distinguish this deliberate selector fixture from natural authored full ICM runtime integration.
3. Exercise actual population selection and genuine ICM.select_actions on the next call. A test-local sentinel at the second env.step boundary records/asserts the full scattered actions, then stops before reward evaluation. Catch only that exact sentinel, and prove that it was reached after the real selector; arbitrary earlier failures must still fail.
4. Assert the actual eligible K, aligned state fields/per-row epsilons, pre-draw live-empty validation where applicable, RNG behavior and full-N scatter/inactive transport. RNG comparison must start after genuine ICM construction/attachment so its initialization draws are not mistaken for action-selection draws. The sentinel must not compute/replace actions or substitute zero rewards.

The other four providers retain their real two-step environment/replay/completion controls. The ICM boundary case establishes selector dispatch/filtering only: it does not prove a second physical transition, reward, replay insertion, completion or ICM learning. No xfail, swallowed ValueError, mocked zero reward or broader provider bypass is approved. This scope statement prevents the bounded test from falsely certifying the failed integration.

Keep the observed ICM reward failure and full-context production integration **REQUIRED OPEN under the already assigned T18e/T18f**, with actual later end-to-end reward/update/continuation evidence owed. It is not optional cleanup, a removed all-provider requirement or whole-BAC success. T15's selector obligation remains fully tested; full ICM reward integration retains its existing owner and gate.

## Custody and return

Only this ignored technical review is written. No source/test/index edits, project imports/runtime, test collection/execution, probes, compiler/linter/gates, branch/worktree/source copies/deletions, subdelegation, commits or publication occurred. All14 worktrees remain untouched. Source hashes and current HEAD/status were checked read-only; the pre-existing staged learner test was not altered. No new permission rule or owner approval requirement is inferred. Return stationary for bounded implementation and fresh execution/review by the assigned owners.
