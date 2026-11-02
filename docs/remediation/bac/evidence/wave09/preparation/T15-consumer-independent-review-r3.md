# T15 consumer independent review R3 — final scoped static review

Reviewed the actual frozen script repair against the same bounded three-source context used for R3a. Manifest wave09/r3-candidate.json identifies HEAD75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7 and candidate tree c6beac9d65c88a7063c27f4d64750cb49b7ae97a. Read actual changed script context, wave09/r3-consumer-review.diff and T15-checker-consumer-repair-r3.md. Prior R3a review and findings remain preserved, not rewritten as if they had passed.

Exactly3 complete sources/3091 physical lines, with observed hashes:

| Source | Lines | SHA256 |
|---|---:|---|
| scripts/check_episode_lanes.py |1036|19e0b83130f2467a2bfd890dc79e95de6d7694e79f7fa996fa16c66b43e62eb7|
| tests/test_townlet/unit/oracle/test_episode_lane_comparator.py |393|5a259e6ab4236caf3d1b20323ee089522c101b4e91d8a294e2deb84595536d30|
| tests/test_townlet/integration/test_checkpointing.py |1662|70d13c5df324111b1e9f53aba91360edfe31a0abb1cf2e5a3c7cf46b6e08968d|

No fourth implementation/helper/POP/oracle/conftest source was read. No project import/runtime/collection/test/probe, tracked edit, index, commit, checkout/worktree, source copy, deletion or subdelegation occurred. This ignored report is the only write. AGENTS/CLAUDE and finite root constraints remain applicable; all14 existing worktrees were untouched.

## Specification disposition: PASS within this consumer scope

The two initial P1 blockers are remedied in the actual script:

1. Script605–619 derives eligibility from ~env.dones, requires agreement with population completion, checks eligible K Q/mask geometry and active state rows, indexes the authored schedule by that actual eligibility and returns only K actions. Legal-mask indexing now uses count rather than2. Full-N Q is captured independently at measured_step641–648 from population.last_selected_q_values, with explicit (2,A) geometry. Collector immediately materializes CPU values/hashes before the original environment call. Actual full-N action transport remains untouched in the original measured_step recording. Thus inactive action argmax is preserved rather than fabricated as WAIT, and selected-Q inventory remains full width without inventing provider rows. Exact state-field slices/epsilons and the actual inactive transport are covered by the unchanged strict tests.
2. Script724–756 installs a push_recorded observer on the current bound object at measured_step entry, after the producer's verified binding/selection and before actual storage. Identity tracking prevents repeated wrapping of the same object; a different actual buffer gets a new wrapper. The bound original method is closed over per installation, receives unchanged args/kwargs once for an accepted observation, and returns/raises naturally. replay_rows is updated only after successful original insertion. The available lanes subtract replay_rows.keys(), so a second chunk cannot overwrite an already admitted lane. Unknown/ambiguous hashes still fail. population_readings clears the seen/admission state only after consuming the tick. Direct paths and budget-six's real runner population/env closures share this hook; removing the earlier runner-reset constructor hook correctly avoids observing the obsolete binding.

Identity ambiguity remains an explicit refusal rather than invented lane attribution. This observer is for the existing flat authored lane recipe; it neither changes production buffer semantics nor promises generic recurrent instrumentation. No new material regression was found in the bounded source review.

The checkpoint changes retain the R3a static PASS: actual min_size/batch support and passed capacity are respected; snapshot ownership precedes source continuation; source and restored branches must advance counter and parameters. Current recurrent captured6 retains A, resolved six options, actual masks/bits/IDs/spans and active2 history through a fresh ENV/rollout reset. Completion/idempotence, file/source integrity and tolerance checks remain. Historical maskless5 remains a separate immutable fixture obligation, not an expectation for new captured data.

## Quality disposition: PASS within this consumer scope

The repair is narrow and leaves strict causal tests byte-identical to RED. It changes no reward arithmetic, replay arguments/masks, readiness or seed/horizon, completion/reset/budget logic, inventory schema, source identity or comparison allowance. Hook setup occurs before real env transition and observes storage afterward; failed writes do not become reported admissions. The source methods themselves remain untouched except the intended observer binding in the checker process. Low-level push is neither replaced nor used to reroute qualified collection.

There is no established reachable false qualification from the inherited collector.errors overwrite. It remains solely a diagnostic limitation/optional P3, with intentional retirement float32 reassociation tolerance unchanged; it is not a new blocker. New selector/geometry/identity checks raise directly, so their failures cannot disappear through that overwrite. The finite test coverage limits recorded in R3a remain accurate, but root confirms forced lazy replacement and recurrent continuation are separately covered by strict main-owned R2/native checks. No extra purpose or tests are demanded of this flat lane checker.

## Runtime disposition: PENDING for repaired R3

Root reports actual causal4RED before repair, log SHA2560aa04ee8494d6c4776cc3cb85de697becb89368f320c0c486210c8a73c86fdf9: three K-selector IndexErrors and one genuine recorded write followed by admitted None. Root also reports the exact two repaired checkpoint cases PASS in42.47wall with this unchanged checkpoint source hash. These are attributed results; this reviewer did not execute or inspect full logs. The checker author's Black/Ruff success is likewise attributed.

Root must now run unchanged causal4GREEN and complete67 consumer owner tests plus all standing guards, then required full qualification on frozen identity. The main six scopes are reported provably byte-identical to their R2 qualified source; this does not mean their tests executed under the R3 tree/SHA. No R3 GREEN/full/coverage/native qualification or release is claimed by this static PASS.

## Native acceptance remains separate

Synthetic source_identity in the UNIT fixture stays explicitly UNIT-only. The production clean committed execution-bearing source check remains intact, with no allow-dirty bypass or native identity monkeypatch. After required gates and the local exact-tree commit, root runs the six native recipes against /workspace/hamlet using the exact commands in T15-checker-consumer-repair-r3.md, before push qualification. Existing outputs must be preserved and each new capture gets a nonexisting directory. No source checkout/new worktree/oracle bootstrap/.oracle write is needed or authorized.

For clarity, the command form is:

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe RECIPE --output OUTPUT
```

Use explicit recipe values authored-two-five, two-episodes-reset, budget-six, passive-two-five, death-at-lifespan and healthy-retirement, each with a distinct fresh OUTPUT. Capture exit0 is insufficient: require contract.qualified=true, errors=[], complete readings and genuine new revision/source/import/config/instrument/action bindings. Preserve actual full-N action differences. Older instrument/action manifests are not automatically comparable; do not weaken exact comparison or relabel precommit/synthetic evidence. The guarded root test harness remains necessary because this review does not inspect or certify arbitrary pytest oracle bootstrap paths.

Final scoped verdict: SPEC PASS; QUALITY PASS; repaired R3 RUNTIME PENDING. No unresolved material finding identified in the reviewed repair.
