# B fork verifier — frozen tests-only handoff

2026-11-13. Producer: `/root/bac_b_fork_verifier_impl`; integration and
tooltest execution owner: `/root`. Status: **TESTS FROZEN; ROOT CAUSAL RED
PENDING; VERIFIER UNCHANGED**. No tooltests, application imports, application
execution, child execution, CUDA execution or hardware qualification occurred
in this adaptation. Python AST parsing and Black formatting were the only
source-processing operations performed by this producer.

## Frozen implementation bodies

| Body | Lines | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `E/test_replay_spawn_verifier.py` | 1536 | 68009 | `469a6a5708a384f0563eebf950bc981485e2a64c4e7ffb41a6d51ac8b85b8f08` |
| `Q/verify_bac_replay_spawn_identity.py` (unchanged) | 744 | 37963 | `311f32e05522e1f81b7c2e130f95483568eb642a88b12ed44e7b3188084c7cd0` |

`W=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades`,
`E=W/evidence-management`, `Q=/workspace/bac-review-2026-11-01/qualification`.
The original test SHA-256 was
`dc604fcab0dccbec82feb592be29108b6e4c6cb2899c3f4b5d647725e098228b`.
The two live implementation bodies total 2280 lines, within verifier850,
test1650, combined2500 and hard5/5000 bounds. Historical versions remain inert;
this handoff does not change the retained supplement or publish evidence.

## Contract and tests

Only the inherited-PID local trial changes: its exact action set grows from
five to seven by requiring `domain_local_cuda_policy` and
`domain_resolve_local_cuda_record`. Admission remains exactly four actions;
invocation remains exactly five. Each new synthetic action has the same closed
seven-field result shape: `builtins.RuntimeError`, exact diagnostic
`RNG custody cannot be inherited by another process`, integer zero for all four
effect counters, and boolean `state_unchanged=True`.

The positive fixture now emits seven local actions. All existing 75 method IDs
are preserved, including their inherited unittest IDs. Static AST accounting
predicts **81 method IDs**, adding these six:

- `CudaVerifierTests.test_local_policy_guard_missing_action_refused`
- `CudaVerifierTests.test_legacy_five_action_local_trial_refused`
- `CudaVerifierTests.test_local_policy_guard_extra_action_and_wrong_trial_refused`
- `CudaVerifierTests.test_local_policy_guard_result_closed_schema_refused`
- `CudaVerifierTests.test_local_policy_guard_result_types_refused`
- `CudaVerifierTests.test_local_policy_guard_bad_outcomes_refused`

Both actions receive dedicated missing-action, extra-action, wrong-trial,
missing-result-field, extra-result-field, non-object-result, invalid-field-type
and bad-outcome mutations. Type negatives include boolean/float/string/null
effect counters and nonboolean state witnesses. Outcome negatives include
nonzero and negative counters, wrong exception identity, changed diagnostic and
changed state. Each malformed identity is rehashed into its matching observed
record, preserving integrity linkage so schema/value refusal is exercised.
Existing general guard-schema/effect loops also include the two new actions.
The dedicated five-action negative removes both additions and demands refusal;
neither the old schema nor a union is accepted by the intended contract.

This synthetic packet cannot prove the actual unpatched private methods run
their PID guards before inherited lock/cache/import work. That remains the
separate application/core fork packet's responsibility, using the supplier
capsule and core adaptation grant. No application body was read here.

## Root next step

Rehash both bodies, then run the frozen synthetic tests against the unchanged
verifier and retain actual causal RED evidence. The unchanged verifier should
reject the new positive local schema, while the explicit five-action negative
should expose acceptance of the obsolete schema. Other negative subtests may
already refuse because the new positive schema is not yet admitted; they do
not independently establish causal RED. No runtime outcome is claimed here.

The verifier implementation remains untouched until root observes and accepts
that causal RED. After the separate implementation baton, require the exact
seven-action local schema and preserve every existing role, pair, source, PID,
custody, closed-schema and exclusive-output control. Root owns the later full
synthetic run and independent review. No CUDA server has been supplied; all
hardware qualification remains open.
