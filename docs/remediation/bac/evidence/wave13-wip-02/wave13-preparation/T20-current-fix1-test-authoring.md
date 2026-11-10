# T20 current-only fix round 1 — tests-first handoff

Stationary, tests only. Read the full `T20-current-only-independent-review-r4.md` before authoring. Root supplied historical R4 observations: 104 PASS in23.8531 seconds; Ruff/Black/owned four-module mypy/no-defaults passing at601; six unchanged factory old-call errors remain assigned T21. Those are received observations, not new execution. Runtime remains closed; no tests/imports/collection/formatter/runtime/git/index/subagents/branch/worktree/copy/cleanup command was run. Production hashes remain exactly R4.

Root approved test ceiling900 before expansion, recorded in `T20-current-fix1-budget.json`; same five full-file projection2420, unchanged hard5/5000. Only the owned regression and this ignored prose handoff were authored. No sixth implementation/test/helper/probe inspected or created.

## Exact inventory

| Whole file | Actual lines | SHA256 | Projection |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` | 66 | `d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268` |150|
| `src/townlet/curriculum/adversarial.py` |480|`7bca1e8cf60826eaa83525c5425566d15337ecc095756bb1033cb99b8c6a83ad`|950|
| `src/townlet/curriculum/static.py` |64|`22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59`|220|
| `src/townlet/training/episode.py` |176|`53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`|200|
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` |856|`f7b114f496d8588977d4e20d65b0425eb33e77dd3417b90304ce3dff798fbf45`|900|

Actual5/1642. Test headroom44 lines before future formatting; stop/reslice before exceeding900. EP has24 lines of current headroom, CA470; no source-budget expansion or new journal is proposed.

## Meaningful P2/P3 RED witnesses

`test_logically_impossible_native_effects_refuse_without_invalidating_prepared_owner` creates genuine current native state, prepares a real fresh outcome before attempting restore, and then changes only the named plausible-range lane values. Nine parameter cases:

- `dwell`: one real4-step event, dwell inflated4→1000. Existing R4 accepts, allowing a later8-step event to advance with fabricated dwell.
- `stage`: same one-event history, stage5 and matching stage-band difficulty1. Existing R4 accepts an unreachable stage despite unchanged authentic event/fingerprint.
- `rate`: one real10-step/rate.01 completion, difficulty.1→.9 within the configured [0,1] band. Existing R4 accepts an impossible first-event effect.
- `static_count`: one real static10-step event, completed episode count1→0.
- `static_zero`: same static event, count and dwell both changed to0.
- `multi_latest_dwell`: two genuine4/8-step completions, dwell12→7 while the latest event alone records8.
- `multi_zero_count`: same two-event adversarial history, episode count2→0 while positive dwell12 remains.
- `multi_stage`: same two-event history, stage4 and matching difficulty.75 despite at most two available transitions from initial stage1.
- `multi_static_count`: two genuine static completions, episode count2→1.

Every case expects `ValueError`, compares the entire existing snapshot (native state, telemetry, decisions, lane info and CPU torch RNG), and then commits its already-prepared receipt. A separately produced uncorrupted control commits the same future event and must match the complete resulting snapshot. This proves rejection cannot silently replace the owner token or damage future prepared-receipt usability. No missing constructor/schema/preflight blocks these R4 witnesses; intended failures are actual `DID NOT RAISE` at the malformed-load assertion.

`test_genuine_first_event_native_effects_restore_exactly` provides literal positive controls for stage-band (stage1/dwell4/count1/difficulty0), rate-limited (stage2/dwell0/count0/difficulty.1), and static (stage0/dwell10/count1/difficulty.6). Both sides use genuine events; already-published telemetry is drained before save. These controls must continue passing as semantic validation tightens.

`test_static_multi_event_resume_keeps_exact_clocks_and_old_equal_retry` saves genuine4/8-step static history, loads it, replays the old equal first event without changing dwell12/count2, then commits a fresh3-step budget completion to both uninterrupted/restored instances. Literal dwell15/count3/fixed.6 decisions and complete snapshots must agree.

`test_future_generation_equal_receipt_refuses_but_older_equal_retry_survives` prepares/commits event1, commits event2, then replaces the old equal receipt generation with99. R4 currently returns no-op; new contract expects refusal with unchanged snapshot, followed by successful original older equal receipt retry with no effects. No stale equal-retry capability is removed.

## Codec coverage within the same file

Expanded the existing dtype×shape matrix from its original five dtypes to every claimed12 dtype while retaining every original dtype/shape/value/ownership assertion: bool, uint8, int8/16/32/64, float16/bfloat16/float32/float64, complex64/128; shapes (0,), (2,0), (0,3), (2,). No original104 substantive scenario/value was removed.

`test_codec_preserves_nonzero_complex_scalar_and_noncontiguous_logical_readings` adds a float64 scalar, complex64 scalar with nonzero imaginary part, transposed nonzero complex128 matrix, and transposed float matrix. It checks exact owned tensor readings after decode, identical logical-content fingerprint for contiguous/noncontiguous equivalents, and continued frozen ownership after caller tensor mutation.

`test_codec_malformed_metadata_bytes_and_content_refuse` checks invalid fingerprint, unknown dtype, negative/boolean/wrong-length shape metadata, invalid hex, invalid byte length, unknown envelope field, and encoded nonfinite reading. Except for the deliberately bad fingerprint case, modified payloads receive recomputed valid SHA256 so metadata/content validation is actually reached rather than every test merely exercising the outer digest check.

Case counts were not collected or executed. Root should distinguish P2/P3 intended assertion RED from valid native/codec passes or unexpected errors. No new tests claim old-format compatibility or reconstruction of unavailable payload history.

## Bounded proposed repair after root RED

No production repair is authorized by this handoff alone. After root observes intended R5 RED and clears semantic changes, validate only invariants derivable from retained current data:

- Recompute the exact first-event lane effects from authored initial state and its retained canonical event using the existing pure policy, comparing stage/dwell/counter/difficulty. This detects fabricated first-event effects without a new format or redundant stored fields.
- Static completion count must equal its lane's retained unique identity count; static never resets stage clocks.
- Bound adversarial stage reachability by initial stage plus available completion count; require zero/nonzero stage-counter consistency and minimum dwell from the retained latest event when counters show no transition reset. Existing nonnegative/band checks remain.
- Reject future prepared generations before the all-known retry shortcut; keep valid older equal retries and current-only owner semantics.

Earlier payloads survive only as fingerprints. Do not invent/reconstruct their durations/rate path or claim universal detection of arbitrary plausible historical scalar alteration. No compatibility state, journal protocol, archival import or unrelated source cleanup is proposed. Root retains runtime, ratchet/global-gate ownership and fresh full-source review after scoped repairs. T21/current caller/integration obligations remain open.
