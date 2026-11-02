# T15 artifact fixture causal audit

2026-11-02. Read-only source audit in existing `/workspace/hamlet`; only this requested ignored prose report is written. Root supplied frozen HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, candidate tree `c6beac9d65c88a7063c27f4d64750cb49b7ae97a`. Full runtime91551 remains under root custody; this worker neither polls nor cancels it and makes no source edits before root explicitly clears them after actual closure. No runtime success is claimed.

## Exact source inventory

Exactly four complete implementation/test/helper sources, 3024 lines, were read. AGENTS/CLAUDE and the source-verified interface R1, existing fixture repair R1, independent fixture review R1 and lane supplier repair R1 were read as guidance/prose; their implementation links were not followed. Failure JSON was supplied qualification DATA. No fifth runner, recorder, database, TensorBoard, conftest or other implementation source was opened.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 297 | `7e4aa29416b3fcfd01470ba143d3eec43172d66cff9aa4120ef6e28b245dcd8a` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |

## Established cause

The controller/worker failure records under `/workspace/bac-review-2026-11-01/qualification/wave09-full-r0/full/failure-*.json` identify the same artifact test setup failure, before artifact assertions. `persisted_run` calls `run_lane_runner`, which installs its own selector rather than using the separately repaired `controlled_action_schedule` helper. At sinks lines 67–75, that selector still asserts Q shape `(2,A)` and two observation rows, indexes masks as full2, and returns two actions.

POP `_rollout_q` retains the actual full-N network output and stores it in `last_selected_q_values`. `step_population` passes full-N Q/state to curriculum, obtains actual full-N ENV masks, and calls `_select_eligible`. That method projects Q/state/masks by actual entry eligibility before calling the provider; returned K actions are installed into the full-N transport. At tick3 in `(2,5)`, world0 has completed and world1 remains eligible, so provider input `(1,8)` is correct. The failing full2 assertion is a fixture contract mismatch. It provides no evidence of recording, queue, SQL, TensorBoard or export failure.

## Proposed narrow repair after root clearance

Edit only the selector inside `run_lane_runner` in `test_episode_lane_sinks.py`:

1. Derive ascending original-world indices with `torch.nonzero(~env.dones, as_tuple=False).flatten()` and set K from their count.
2. Preserve finite-Q checking and require Q shape `(K,env.action_dim)` and observation count K.
3. Keep the existing tick and complete two-world END_LANE/WAIT schedule, resolved through compiled `action_ids`; require its shape `(env.num_agents,)`.
4. Project scheduled actions by those original-world indices. Require selected shape `(K,)`, mask presence and exact `(K,A)` geometry. Check actual supplied masks with K-local `torch.arange(K, device=env.device)` and projected selected actions. In particular, K-local row0 may represent original world1; indexing K masks with original index1 would be wrong.
5. Return only K selected actions. Do not create, widen or replace masks, perform another brain/provider call, alter rewards/dones or prescribe inactive transport actions.

This mirrors the separately reviewed helper's contract without editing that helper or importing another test's private selector. No artifact-pipeline source change is causally needed by this failure. Its assertions use actual full-N ENV observations, not provider witness rows; no old K/N zip assumption exists in the audited artifact source. Other qualified T15 source hashes must remain unchanged.

## Preservation assessment

The real full-N network forward, `last_selected_q_values`, curriculum Q/state and entropy path, full-N ENV transport and returned Q information remain production-owned. The fixture continues wrapping original ENV execution. Its tick ledger retains independent pre-step active bits, terminal bits, full-N applied actions, observations, meters, canonical rewards, all reward components and weights. The proposed selector projects the authored control schedule only; it does not substitute schedule values for observed inactive transport.

All sink assertions remain: both `(2,5)` and `(5,2)` world orders; exact survival and eligible counts; two episodes and resets; batch ticks5/live transitions7; completion reasons and final owned meter/observation snapshots; custom-action use; curriculum publication; effective real DAC components and zero terminal frame; budget6 survivor truncation, cap3 nonterminal bootstrap and exactly-once flush; zero-work indivisible budget; completion snapshot aliasing and completion-before-curriculum ordering. No replay minimum, training budget, cap, authored config content or learner gate changes are proposed.

Artifact assertions remain: real queue acceptance/dequeue identity/order, empty queue and writer buffer after ordinary cleanup, terminated writer thread, exactly four frames/two markers/two files/two SQL rows, actual fourteen eligible transitions; exact queued/persisted metadata and frames; file sizes/index/SQLite/TensorBoard agreement; per-world reward ledgers; real ReplayManager and observer seek/reset/reload; both exporters and realized transition metadata; all eight corruption controls including structural refusals and independently detected consistent phantom/raw-intrinsic corruption. No assertion drop, xfail, skip, synthetic artifact or changed threshold is justified.

Controlled selection remains unsuitable as sole evidence for real epsilon/provider randomness or exact K-state/epsilon/mask alignment. Independently owned provider/learner qualification carries those requirements. Neither the existing fixture helper witness nor the proposed local selector is evidence of inactive action application.

## Root-owned focused verification after edit

Use the existing identity/import/qualification harness, preserving its budgets and recording exact candidate identity. Minimum focused source commands are:

```text
.venv/bin/black --check tests/test_townlet/regressions/test_episode_lane_sinks.py tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py
.venv/bin/ruff check tests/test_townlet/regressions/test_episode_lane_sinks.py tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py
git diff --check -- tests/test_townlet/regressions/test_episode_lane_sinks.py tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py
.venv/bin/pytest tests/test_townlet/regressions/test_episode_lane_sinks.py tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py
```

The direct consumers comprise nine sink cases and eleven artifact cases (the latter share module fixture `persisted_run`). Qualify both entire modules so the opposite original-world survivor, budgets/caps, recording cleanup and corruption controls execute. Preserve `EPISODE_LANE_ARTIFACT_EVIDENCE_DIR` through the existing harness when retaining generated artifacts. Broader B03 and full G2/BAC/final gates remain root-owned. Further failures must be triaged from actual evidence; this static audit does not predict a green run.

No project import, pytest/collection, compiler, executable probe, source edit, branch/worktree/source copy/deletion, subdelegation, index/tracker/commit or publication operation occurred. Existing fourteen worktrees and finite programme66 tasks/22 lenses/54 effective requirements are preserved. Return stationary pending root clearance.
