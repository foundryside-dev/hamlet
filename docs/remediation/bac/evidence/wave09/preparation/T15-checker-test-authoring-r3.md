# T15 checker preservation — test-first authoring R3

Root cleared source/test authoring after all R2 runtimes closed. This authoring changes only tests/test_townlet/unit/oracle/test_episode_lane_comparator.py. The production checker and population remain unchanged. No project imports, runtime, pytest/collection, source checkout/worktree, .oracle write, index, commit or publication occurred. Root owns causal RED and subsequent repair authorization. The separate checkpointing-test writer's source was not opened.

## Complete source custody

Exactly three whole implementation/test/helper sources, now3557 physical lines; no fourth source was read. Scope remains below5000:

| Complete source | Lines | SHA256 |
|---|---:|---|
| scripts/check_episode_lanes.py |1018|087a9b747af30a30a8b5c68466fbd3fcd81cb5a6bb4ef20a5bd2acca5707553c|
| src/townlet/population/vectorized.py |2146|9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a|
| tests/test_townlet/unit/oracle/test_episode_lane_comparator.py |393|5a259e6ab4236caf3d1b20323ee089522c101b4e91d8a294e2deb84595536d30|

The initial audit's3/3394 is the before-state, not the new count. Its script/population hashes remain exact. The only other write is this ignored prose receipt under /.superpowers/. Using test-driven-development and its writing-good-tests reference, this phase names the intended breaks, writes tests and returns before production repair; root must observe actual failure before GREEN work. No RED or runtime result is claimed by this author.

## Added test provenance and causal nodes

synthetic_identity_producer explicitly documents UNIT provenance. It patches only checker.source_identity to a synthetic40-character revision and64-character source digest; this is test-local metadata, not clean committed-source qualification. It calls the actual in-process run_producer with the existing native configs/test/episode_lanes path. Config compilation/copying, environment/population construction, selector filtering/scatter, canonical reward generation, replay write, warmup/readiness, completions/reset and budget-six DemoRunner execution stay real. The standalone source_identity implementation, CLI, manifests and native capture gate are unchanged. No reference checkout/bootstrap or subprocess capture is invoked by the fixture. Root must retain synthetic labels when reporting these unit results.

New causal nodes, relative to tests/test_townlet/unit/oracle/test_episode_lane_comparator.py:

- test_producer_projects_eligible_selector_and_captures_actual_full_population_transport[authored-two-five]
- test_producer_projects_eligible_selector_and_captures_actual_full_population_transport[two-episodes-reset]
- test_producer_projects_eligible_selector_and_captures_actual_full_population_transport[budget-six]
- test_producer_observes_real_recorded_admission_on_bound_replay

The selector tests wrap/delegate the actual population _select_eligible and the existing checker-assigned provider callback, restoring the provider in finally. They assert actual Q/mask/state slices, exact per-row epsilons and truthful dones, and demand the callback return K actions. Expected K schedules are literal2,2,1,1,1; twice for reset;2,2,1,1 for budget-six. A callback IndexError is reported explicitly as failure to accept the actual eligible K rows, rather than interpreted as a production transport defect. The actual env.step delegate independently checks full-N actions, genuine inactive argmax transport and active schedule legality/identity. After producer completion, actual captured full-N Q/actions/reward totals/components are compared to the real env call and the full existing capture/semantic validator must qualify. Q values are never fabricated from the provider subset.

The admission test isolates an earlier first-write failure before K=1: a delegate installed only after original _bind_training returns observes the actual bound replay's push_recorded, checks the exact committed successor masks from real env.step and confirms original storage grew by the submitted row count. Collector.scalar remains a delegate; its admission assertion demands the checker-reported row hash equal the independently eligible predecessor, after a genuine successful storage call. The stale .push wrapper should therefore fail at tick1's admission equality even though real push_recorded has already stored the rows. Final positive controls require7 genuine rows and replay_size7. This control does not force a replacement or claim every selected pack replaces replay; it follows the actual bound object, and the separately audited production path permits lazy replacement. Original buffer methods are called exactly once with unchanged arguments; neither low-level push nor production collection is rerouted.

No rewards, actions, successor masks or replay results are substituted. Test delegates observe and assert only. The first three tests may later encounter the stale admission observer after the selector is repaired; that is another real required checker defect, not a reason to weaken qualified=True. Root should preserve both causal failure stages and repair both seams narrowly after RED.

## Static checks and root execution handoff

Owned checks actually executed successfully:

```text
.venv/bin/black --check tests/test_townlet/unit/oracle/test_episode_lane_comparator.py
.venv/bin/ruff check tests/test_townlet/unit/oracle/test_episode_lane_comparator.py
```

Black initially ran on this owned test and left it unchanged; final --check and Ruff both passed. No project module was imported/executed by this author. Proposed root selection through its established no-auto-checkout pytest/import harness is the existing file with:

```text
-k 'producer_projects_eligible_selector or producer_observes_real_recorded_admission'
```

Run the observer node separately if needed to distinguish the first-write failure from tick3 selector failure. This receipt does not endorse an uninspected default oracle/pytest bootstrap: root's verified harness owns conftest/plugin and no-new-checkout custody. Keep all prior tests and exact checker outputs. After the causal RED, root can clear only the audited eligibleK callback/fullN witness plus current-bound push_recorded observer repair. No dirty-source identity bypass or new flag is requested.

After required owner/static/full-repository gates pass, root's local exact-tree commit establishes a clean source stamp for the unchanged native capture path and explicit arguments already recorded in T15-checker-consumer-audit.md. Genuine standalone postcommit captures have their new actual source binding, before push/publication qualification. Prior tests retain actual base SHA/tree and synthetic unit provenance; neither is rewritten to that postcommit identity. Capture exit0 must still be accompanied by contract.qualified=true and errors=[] on each native recipe.

Return stationary for root's causal RED; script repair is deliberately not authored yet.
