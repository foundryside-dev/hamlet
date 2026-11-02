# T15 existing checker consumer audit — static, stationary

2026-11-02, existing /workspace/hamlet only. Root retains execution, index, commit, qualification and push ownership. Root reports owned152 plus B03-remaining163 active on frozen tree929bc895; this worker ran no project runtime/import/pytest/collection or gate and made no implementation edit. HEAD observed75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7; HEAD's committed tree7924a5c5b47f680bf011ddff3174719d85ac1d18 is distinct from root's staged candidate identifier. No branch/worktree/checkout/project source copy/deletion/subagent was created. All existing14 worktrees were untouched.

## Exact complete implementation inventory

| Complete source | Physical lines | SHA256 |
|---|---:|---|
| scripts/check_episode_lanes.py |1018|087a9b747af30a30a8b5c68466fbd3fcd81cb5a6bb4ef20a5bd2acca5707553c|
| src/townlet/population/vectorized.py |2146|9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a|
| tests/test_townlet/unit/oracle/test_episode_lane_comparator.py |230|13cbf4306fcd2dcd1fa7ead1fb2edec40cec3caad795f3f4f163816855859d8e|

Exactly3 complete implementation/test/helper sources,3394 lines, below5000. No fourth source, oracle implementation, runner, buffer, fixture, conftest or probe source was read. Filename-only config discovery identified configs/test/episode_lanes; no YAML bodies were needed. Read AGENTS.md and CLAUDE.md, plus these prose handoffs without following their implementation links:

| Prose | SHA256 |
|---|---|
| T15-interface-proposal-r1.md |70b155234f553855675a235d980674afdc3588d92e71dd054bba5b69f0e56d0a|
| T15-constructor-runtime-consumers.md |9048ba713a2540bc8a8e7bf9e45ebbc01ba619b3732a32663dc0049c1104d23c|
| T15-implementation-r0.md |0c556f7c1258ae5834ce2bcbff9aacfca12b52bf5aaef66c7b5332b0eabde75f|

Using-superpowers subagent stop was honored; systematic-debugging was read/applied for causal analysis. Explicit root limits supersede project suggestions to run trackers/indexers, use isolated worktrees or inspect further source.

## Confirmed consumer defects and preservation requirement

The R1 proposal Q7 expressly requires maintaining this checker as an existing learner-dispatch-capable consumer; these are required preservation repairs, not optional improvements.

1. EL711 saves real_population.replay_buffer.push and EL732 patches that constructor instance. POP595 _bind_training can replace a pristine selected buffer, and POP1317 actually calls push_recorded with real successor_action_masks. Even when binding retains identity, collection no longer traverses push. The old observer therefore cannot establish actual admission. Missing admitted_observation does not establish missing production collection. POP preserves RewardTensor.from_dac(total,extrinsic,intrinsic,shaping), exact eligible ordering and bounded chunks. Do not force POP through push or inject masks/history to satisfy instrumentation.
2. An earlier causal failure exists at EL605–613: its provider select callback assumes full N=2, records q_values with num_agents=2, indexes action_masks with arange(2), and returns two actions. POP1022 _select_eligible passes only K eligible rows, slices every state tensor and requires int64[K]. After lane0 terminates on tick2, tick3 has K=1. The observer would index a nonexistent Q row before admission, even with a push_recorded hook fixed. This is a stale consumer shape assumption; do not restore full-N provider sampling.
3. Full-N transport remains real at EL633 measured_step(actions,...), which captures actual actions passed to original_step. POP initializes inactive actions with actual unmasked Q argmax and scatters only eligible provider actions. Consequently inactive transported actions may differ from the old scripted WAIT even though they do not select/transition. Never rewrite those readings to WAIT or pretend the provider received full-N masks. The full-N Q witness is POP.last_selected_q_values (POP1010), already set before measured_step. It can preserve the existing selected_q_values inventory using genuine full-N values; eligible callback Q/masks/state must separately be checked against the independent entry membership.
4. Existing replay row matcher resets unused lanes for each call and overwrites replay_rows[agent]. An additive observation correction should refuse duplicate admission per tick across all chunks rather than hide a second admission. Continue rejecting unknown/ambiguous predecessor identities. Keep terminal-causing entry rows once and inactive rows absent.

No production defect was established by this bounded static trace. Runtime evidence may expose one; report it separately rather than accommodate it in fixture values.

## Small additive correction proposed after root's all-runtime-closed clearance

Keep changes in the existing checker and comparator test only; no new helper/probe file and no POP edit is required by the current evidence.

- Project the schedule onto actual eligible lane indices derived from ~env.dones (and check population completion consistency). Assert callback Q/state/masks have K rows, state fields equal the corresponding full population state rows, and returned scripted eligible actions are truly legal. Do not derive eligibility from nonempty masks. Preserve actual per-row epsilons and truthful active dones.
- Record selected_q_values from population.last_selected_q_values at measured_step, with full-N shape checks and clone/CPU handling. Keep measured_step's actual full-N action tensor unmodified, and validate active actions against the schedule plus inactive transport against those actual Q values' argmax. Record neither invented missing Q rows nor an altered full-N action schedule.
- Bind the observer at the beginning of measured_step, after production _bind_training has selected the actual current buffer and before replay admission. Install an idempotent current-instance push_recorded wrapper, preserving its exact arguments/kwargs/result/exceptions and calling the original method exactly once. Do not call push, insert extra rows, reconfigure sampling, replace the buffer, fabricate legal masks, or change its low-level supported push interface. Check the installed identity each step so lazy replacement cannot strand the hook. Recording successful admission after original returns avoids treating a rejected insert as accepted.
- Match actual supplied observations against independent predecessor identities, maintain one per-tick seen-agent set across chunks and preserve replay_rows until population_readings consumes it. Existing direct and budget-six runner paths both pass through measured_step; the latter replaces the population/env closures in runner_reset, so hook that actual new population as well.
- Retain all exact coordinates, reward totals/components, actual training policy/min_size/seed and horizon, budget6 live-agent accounting versus cap10 vector horizon, completion snapshots, two-episode reset behavior and real supported replay writes. B128 is not warmup128 and does not justify disabling a replacement sampler's real readiness.

Meaningful regressions in the existing comparator test: a genuine small real config run_producer exercise for authored-two-five and two-episodes-reset plus budget-six, with only source identity metadata stubbed if needed for an uncommitted RED/GREEN unit harness. Keep real compilation/environment/population/buffer methods, assert qualified captures with full inventory, exact admissions7/14 and runner6, eligible membership after tick2, true full-N Q/actions and lifecycle snapshots. A narrowly instrumented public push_recorded call counter/delegate can prove original storage was invoked once per actual admission and survived lazy replacement; do not replace storage with a fake. The stale implementation must fail at K=1 or missing actual admission, and the repaired checker must pass without suppressing production errors. Strengthen semantic mutation controls so missing/phantom admitted rows and duplicate admissions cannot be blessed. No regression has been written or executed in this audit.

Existing EL868 constructs collector.errors verdict but EL870–871 immediately replaces it with semantic_errors; validate_capture independently requires exactly the latter. Most local checks are reconstructed semantically, but the producer's exact torch reward-sum check is stricter than semantic retirement's float32 reassociation tolerance. Preserve the intentional retirement rule and exact captured total/component coordinates. Do not silently switch policy, erase this distinction or report collector.errors alone as an enforced verdict. This pre-existing checker limitation is separate from the two confirmed T15 consumer failures.

## Invocation audit and root-only acceptance commands

The inspected checker itself has only capture/_produce/compare subcommands. Its direct capture path EL875 calls source_identity, creates the requested output directory, and launches this same script in a subprocess with explicitly pinned PYTHONPATH and CPU visibility. It does not invoke an oracle utility, git worktree/checkout/archive, source checkout or .oracle writer. Its temporary copy is config YAML only (EL560–577), not a project source checkout. _produce selects the explicitly supplied source root. These are candidate-only lifecycle captures; no preserved reference checkout is required.

source_identity EL483 rejects dirty execution-bearing src/configs/scripts/tests/pyproject/lock paths, including staged changes. The current main working tree has staged candidate files, so a direct capture now must refuse. Root explicitly selects a local exact-tree commit only after required owner/static/full-repository gates pass, then native current capture before push/publication qualification. Keep the clean committed-source requirement; no allow-dirty bypass or identity flag. Prior test artifacts retain their actual base SHA/tree; postcommit captures get a new explicit source binding. Do not monkeypatch this identity gate for acceptance, relabel HEAD as the staged candidate, create a fresh checkout/worktree, or bypass the gate through _produce (which checks it too).

After root closes active runtimes, repairs/reviews the existing consumer and has a clean exact integrated candidate, these direct commands use the existing main only. Output directories must not already exist; preserve them and choose a new explicit suffix for a rerun. The stated paths are proposed artifacts, not executed artifacts:

```bash
cd /workspace/hamlet
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe authored-two-five --output /workspace/bac-review-2026-11-01/t15-checker-authored-r0
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe two-episodes-reset --output /workspace/bac-review-2026-11-01/t15-checker-reset-r0
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe budget-six --output /workspace/bac-review-2026-11-01/t15-checker-budget-r0
```

Repeat direct capture for passive-two-five, death-at-lifespan and healthy-retirement, each with its own nonexisting output directory; none uses POP selection/replay. Important: capture validates schema/verdict consistency but does not exit nonzero merely for contract.qualified=false (EL907–917). Root must explicitly assert every resulting contract.qualified=true and errors=[] and inspect exact readings/manifests, not equate exit0 with qualification.

No default oracle/bootstrap test command is endorsed here. The comparator test's explicit imports contain no oracle helper, but pytest collection loads uninspected conftests/plugins; the task forbids reading that fourth source. Therefore this audit cannot certify an ordinary pytest command avoids automatic oracle checkout creation. Root must use its already verified no-new-checkout import/fixture harness for the existing test path, then the established affected/full gates. Do not run a repository oracle wrapper or default bootstrap on the assumption it is safe. Only the current native capture path above is selected; no reference checkout use is proposed.

For historical comparison, compare requires identical instrument SHA/config/actions inventories plus actual source stamps and ancestry (EL920–973). New genuine inactive transport can change the action manifest, so do not falsify manifests, drop coordinates or relax compare's exact contract to produce a pass. Previously captured old-instrument artifacts are not automatically compatible with the corrected instrument. Candidate lifecycle qualification is distinct from an exact before/after oracle comparison.

## Custody and return

Only this ignored receipt is written; git check-ignore attributes it to .git/info/exclude:7 /.superpowers/. Source/test hashes and counts above, HEAD, and tracked status are checked again after writing. Source reads were static shell reads only. No index or tracked source change is ours; no new runtime result, acceptance pass, release or programme expansion is claimed. Return stationary pending root's all-runtime-closed clearance and any explicit implementation dispatch.
