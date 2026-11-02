# T16 affected-consumer failure audit — read only, stationary

Prepared on 2026-11-02 in the existing `/workspace/hamlet`. Root reports R3 candidate tree `0bdd6133f2224b25bce5668e15021fa1353accba`, base/observed HEAD `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`, and the 266-item affected-owner suite ACTIVE in session59974. The candidate tree is taken from the supplied failure records, not inferred from HEAD or regenerated through an index write. This receipt makes no suite PASS/GREEN claim and supplies no implementation/runtime clearance.

The four unique failures have two source-proven causes: a stale late fixture configuration target, and a stale population-construction observer. The approved sources do not demonstrate a failure of cap completion, live nonterminal replay semantics, or hyperparameter forwarding. Both fixture corrections below preserve the original assertions and scenarios without changing production configuration identity or public caller controls. Their runtime results remain unverified.

## Exact complete source custody

Exactly **five whole sources / 3743 physical lines** were read. Their hashes/counts were checked at entry and again before writing this receipt and were unchanged:

| Source | Physical lines | SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` (RR) |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` (POP) |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` (SINKS) |304|`29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b`|
| `tests/test_townlet/integration/test_runner_hyperparams_v21.py` (HP) |119|`ced5b1cb1a4d239112d2dadf24df3876aca08bcf758e0e611e8716483e72584c`|
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` (LANES) |157|`9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f`|

No sixth source/helper/test/probe, imported implementation, environment/config/sampler source, source copy or new checkout was read/created. The imports printed in these five sources were not followed. `AGENTS.md` and ignored `T16-task-brief.md`, `T16-interface-readiness.md`, `T16-implementation.md` were read as guidance/prose. Existing source-verified prose describes the canonical effective training carrier's owned deep-copy behavior; this audit independently observes RR's choice of that view and the failing mutation's different target. The diff of RR against HEAD was also read. Root's explicit preservation/read-only rules supersede generic deletion/tracker/index workflow instructions.

The systematic-debugging skill was applied to trace the actual recorded call paths before proposing corrections. Verification-before-completion was read for evidence/claim custody. No attempt was made to reproduce while the root runtime barrier is active.

## Actual failure records, deduplicated

Evidence: `/workspace/bac-review-2026-11-01/qualification/wave10-r3-affected/affected.log` and the eight `affected/failure-*.json` records. `jq` grouping by exact nodeid confirms four failures, each duplicated as a controller record plus its xdist-worker record. Every record has phase `call`, outcome `failed`, and the same R3 candidate tree above.

| Unique nodeid | Recorded workers | Actual failure |
|---|---|---|
| `tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_keeps_authored_terminal_and_live_bootstrap[end_ticks0]` |controller, gw2|`end_ticks=(2,5)`: expected3 ticks, observed5 at SINKS238|
| `tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_keeps_authored_terminal_and_live_bootstrap[end_ticks1]` |controller, gw2|`end_ticks=(5,2)`: expected3 ticks, observed5 at SINKS238|
| `tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_completes_lanes_before_curriculum_publication` |controller, gw2|expected reasons `authored_terminal, cap`; observed `authored_terminal, authored_terminal` at SINKS300; survival tensor `[2.,5.]`|
| `tests/test_townlet/integration/test_runner_hyperparams_v21.py::test_demorunner_threads_training_loop_hyperparameters` |controller, gw3|expected stop sentinel from patched `__init__`; actual `_initialize` rejects `DummyEnv` without compiled `token_spec` at POP307|

The log read during this audit shows four workers/266 items and the failures, but contains no final summary. Its partial progress is not a final affected-suite disposition.

## Three cap failures: stale configuration injection, intact completion mechanism

LANES34–43 authors training max_steps_per_episode from its `lifespan` argument. SINKS29 calls it with lifespan10. The fixture then waits until population reset, checks the real environment's `agent_lifespan == 10`, and writes cap3 to `runner.training_config.training_loop.max_steps_per_episode` at SINKS60–64. This is deliberately a late caller-loop truncation fixture: it must not turn the world terminal at tick3.

Before the T16 RR change, `loop_cfg` was the nested object under `self.training_config`. Thus that reset-time write changed the object subsequently read for the episode range. The actual diff replaces that binding with `effective_training = self.effective_run.training` at RR401 and `loop_cfg = effective_training.training_loop` at RR402. RR593 still reads the captured loop object after reset, and RR608 still executes `range(max_steps)`. The fixture continues mutating the compiled-level view installed as `self.training_config` at RR170; it does not modify the captured runtime-copy loop.

Consequently the real runtime cap remains10. With the controlled named-action schedules at SINKS67–81, one lane naturally ends at2 and the other at5. RR716–718 stops when all authored dones are true. POP1341–1347 has already finalized both as authored terminals. There is no surviving lane for RR731–733 to cap-flush. This predicts both observed five-tick failures and the observed two authored-terminal completion reasons, in either lane ordering. The third failure is the same cause, not a separate publication-order bug.

The cap mechanism itself is still present: RR723–734 selects the actual external stop reason and flushes each surviving lane before RR735–745 builds completion tensors and calls the curriculum. POP1139–1141 explicitly documents and implements completion for an external stop without changing replay done; POP1114–1137 retains once-only final readings. Eligible rows and actual successor masks/dones are stored at POP1307–1324 before completion. No new cap-related completion/storage change appears in the RR patch or unchanged POP source.

### Smallest proposed correction preserving the original cap scenario

Change only SINKS fixture plumbing, after root clears source writes:

1. Observe and forward the real existing `townlet.demo.runner.build_curriculum` call. Retain the exact `training.training_loop` object supplied to that call, then invoke the original function exactly once with every original argument and return its real result. RR422–426 supplies the same runtime training copy that owns RR402's loop object; this is directly verified in the approved RR source. Capture the original function from the already approved runner module, without opening another implementation.
2. In the existing reset-time cap branch, keep the environment-lifespan10 assertion and direct the existing cap3 assignment to that retained runtime-copy loop object. Assert that the observer captured it before reset. Leave cap=None cases untouched. The original compiled/canonical training views are not edited.
3. Keep both authored end-tick permutations, episodes1, budgetNone, cap3, real compiler/environment/forwards/replay/completion/sinks, and every original test assertion. In particular preserve3 vector ticks, eligible counts `[2,3]`/`[3,2]`, five retained live rows, one actual terminal, live successor bootstrap eligibility, reason `cap` for the survivor, DB values, and completion-before-curriculum checks.

This relocates the fixture's existing late configuration injection to the actual runtime-copy object; it does not fake a terminal/transition/completion or change production policy/identity. It also preserves initialization timing: environment, curriculum and population are constructed with declared lifespan10 before the caller cap is applied, as in the original fixture. The already-created PER upper-bound vector horizon is unchanged, as it was under the original late cap fixture. No readiness/minimum, budget, authored lifespan or assertion needs relaxation. No edit to LANES, RR or POP is required for this proposed correction.

Changing authored max_steps_per_episode to3 would fail to preserve the deliberately separate lifespan10/caller-cap3 scenario and could turn the survivor into an authored terminal. Replacing this with budget5 would change the asserted external reason. Mutating/replacing canonical effective policy/identity, reverting canonical forwarding, changing expected5, or accepting two terminals would evade the existing test rather than repair its configuration observer. None is proposed.

### Public capability boundary and owner decision limit

RR88–110 exposes/documented launch controls for `max_episodes`, `max_environment_steps`, level selection and force-new-VFS. The complete runner source contains no named public `max_steps_per_episode` launch argument or cap setter. Existing named controls remain present and active at RR129–136, RR174–178, RR559 and RR614–637. These records therefore do not establish that a named public caller-control API was removed. The changed behavior of direct mutation of the public-looking `runner.training_config` attribute is real; this audit does not relabel that fact as a validated API guarantee.

Within the approved source/prose boundary, the failing tests document a controlled late fixture injection and can retain that scenario through the narrow observer correction above. If an existing owner ruling or documentation outside this bounded context promises arbitrary runtime mutation of `runner.training_config` as a supported caller API, that contract must be supplied to root and preserved through an explicit owner decision before any implementation that would abandon it. Do not infer removal approval from AGENTS' pre-release language. A separate additive, provenance-bearing public cap override could be considered if that stronger capability is required; this audit neither invents that requirement nor implements/degrades such an API.

## Hyperparameter failure: obsolete observer bypassed by qualified factory

HP38–43 authors train_frequency7, sequence_length5 and max_grad_norm3.5. HP78–103 replaces `VectorizedPopulation.__init__` with a recorder that raises the existing `stop-after-population-init` sentinel, intentionally preventing real population initialization. Its DummyEnv is designed only for that bounded observation and has no compiled token_spec.

RR474–497 now calls the already existing public `VectorizedPopulation.for_training`. POP225–234 validates/builds the explicit replay setup, POP235 allocates with `cls.__new__(cls)`, and POP236–253 calls `_initialize` directly. Python does not call the monkeypatched `__init__` on this route. The actual initializer reaches its valid compiled-token-spec check at POP304–310, yielding the recorded ValueError before the stale observer can record anything.

The failure record independently shows `_initialize` receiving train_frequency7, sequence_length5 and max_grad_norm3.5; RR449–452/483–486 and POP243–247 trace those exact authored values. This is direct counterevidence to a hyperparameter-forwarding regression. It is not evidence that a real compiled environment lost token_spec, because the environment in the failure is HP's own DummyEnv. Weakening POP's token-spec requirement or fabricating a token artifact to push the stub farther into initialization would address the wrong cause.

Smallest proposed correction: update HP's existing capture-and-stop observer to the actual public `for_training` classmethod boundary, with its current keyword-only inputs from POP198–223 (including all explicit replay/horizon arguments) and no invented defaults. Record the same three arguments and raise the same sentinel before real initialization. Keep the actual authored YAML values, DummyEnv scope, existing `pytest.raises` assertion, and all three numerical assertions unchanged. Update only the stale observer name/signature/installation and explanatory comments. This retains the original narrow parameter-threading scenario; a real-population integration exercise is additional coverage rather than a prerequisite change to this test.

## Verification and stationary disposition

The concrete two-test-file correction above is a static proposal, not a tested fix. Root must first close its current runtime and explicitly clear edits. Afterwards root can run the same four nodeids, the complete SINKS/HP files and its causally selected affected owners under the locked harness. Preserve the existing no-cap unequal-lane, live-transition budget, zero-work-budget, real DAC and owned-final-meter controls alongside the cap cases. Runtime/collection/static/full-G2 decisions remain root-owned. Neither these four records nor this source audit declares repository GREEN.

Only this ignored report was written. `git check-ignore -v` confirms `.git/info/exclude:7` matches `/.superpowers/`. No project imports/runtime, pytest/collection/compiler/linters/probes, source/test/config/tracked-doc/index/tracker writes, branch/worktree/checkout/source copy/deletion, commit/push or subdelegation occurred. No operation changed any of the14 existing checkouts. Remain stationary; do not implement from this receipt without root clearance.

## Subsequent root disposition and explicit repair clearance

Before the audit handoff, root closed the affected suite: **4 failed,261 passed,1 skipped**,587.0036 harness wall seconds. The now-complete log independently confirms those counts and reports581.58 pytest seconds. Root supplies log SHA256 `e2f632b2e87f97ba215cb7a56439b593478d1de54ffa12cb97e2f614a8212efd` and preserves original custody in `failed-custody.json`. Root reports verification of all160 source hashes, five process identities,573 configs,13 protected artifacts and all14 worktree records. These are root-owned execution/custody results; this agent did not run the suite.

Root accepts the classification that no named public per-episode cap API was removed and explicitly clears exactly the two proposed test-file repairs. Real build_curriculum must be forwarded exactly once; the runtime-copy cap injection, authored environment lifespan10, cap3, canonical carrier/hash, original completion/bootstrap/curriculum and hyperparameter assertions, budgets and scenarios must remain. Production, YAML and additional sources/helpers remain out of scope. Only AST checks are cleared locally; root retains exact-four runtime, independent review and required gates. The later implementation receipt is `T16-consumer-fixture-repair-r4.md`. This addendum closes the earlier read-only clearance dependency; it does not claim implementation or GREEN.
