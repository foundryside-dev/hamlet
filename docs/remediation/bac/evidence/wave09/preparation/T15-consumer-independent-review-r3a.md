# T15 consumer independent review R3a — initial test-first candidate

Static independent review at HEAD 75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7, root-supplied frozen candidate d0bb822eb387153342fb2aa82186d3df9b6bb30b. Candidate manifest wave09/r3a-candidate.json and consumer diff were consulted. This is an initial test-first disposition, not approval of a repaired checker. Root owns the active causal four-test RED and two checkpoint-test executions. No project runtime, import, pytest collection, source mutation, index, commit, branch, worktree, source copy, deletion or delegation was performed. All14 worktrees remain outside this review's mutations. Only this ignored report is written.

## Exact source scope

Exactly three complete implementation/test sources,3073 physical lines; no fourth implementation/helper/conftest/oracle/POP source opened:

| Source | Lines | SHA256 |
|---|---:|---|
| scripts/check_episode_lanes.py |1018|087a9b747af30a30a8b5c68466fbd3fcd81cb5a6bb4ef20a5bd2acca5707553c|
| tests/test_townlet/unit/oracle/test_episode_lane_comparator.py |393|5a259e6ab4236caf3d1b20323ee089522c101b4e91d8a294e2deb84595536d30|
| tests/test_townlet/integration/test_checkpointing.py |1662|70d13c5df324111b1e9f53aba91360edfe31a0abb1cf2e5a3c7cf46b6e08968d|

Read AGENTS.md/CLAUDE.md and the requested checker audit/test-authoring, checkpoint audit/repair, sequence serialization bridge and R1 interface proposal as prose. Supplier implementation assertions remain attributed to those bounded reports; they are not independently reread source evidence here. Root's finite no-runtime/no-extra-source restrictions govern this review. Prior main/config/B03/native/guard pass counts are root-attributed and do not qualify this changed consumer slice.

## Findings and disposition

**P1, known and intentionally unrepaired in this candidate:** checker605–613 assumes provider input has N=2 rows, records two Q rows, indexes two mask rows and returns two scripted actions. Under the verified T15 K-only provider contract, tick3 has K=1 and this callback cannot run. Preserve full-N Q at measured_step from population.last_selected_q_values and actual full-N actions from env.step; project only scripted selection to independently eligible lanes. Inactive transport must remain genuine argmax, never rewritten WAIT. This blocks checker production acceptance, not acceptance of the test-first authoring phase.

**P1, known and intentionally unrepaired:** checker710–735 observes constructor replay_buffer.push, while actual producer admission calls the bound buffer's push_recorded after lazy binding. The checker can report no admission despite real storage. Hook the actual bound instance before admission, idempotently per identity, delegate unchanged arguments/results/exceptions exactly once, and record only successful writes. Matching must reject duplicate lane admission across all chunks in a tick, as well as unknown or ambiguous predecessor identities. The current wrapper resets its unused-lane set on each call and overwrites replay_rows; do not retain that weakness in the repair.

**Test/spec disposition: PASS for the initial causal test design, with runtime RED still owned by root.** The three parameterized producer tests delegate actual selection and environment execution, verify all listed state slices/epsilons/dones, exact K schedules, actual full-N transport and Q, and canonical reward totals/components. They demand complete semantic qualification, covering authored7, reset14 and runner6 admissions through the existing semantic checker. The fourth test isolates first-write admission before the K=1 failure, follows actual post-bind storage and validates real successor masks, storage growth and final7 rows. No fake replay, fabricated action/reward/legality or lowered warmup is introduced. Synthetic identity is explicitly UNIT-only in the fixture and patches only source metadata; it is not evidence of clean committed native qualification.

**Checkpoint repair/spec and quality disposition: PASS statically for the two targeted repairs; runtime acceptance pending.** Training resumption derives max(actual selected min_size,batch size), asserts support under the separately passed brain/public buffer capacity, proves positive training counter and retained occupancy, owns checkpoint tensors via deepcopy before source continuation, and requires counter plus parameter changes on both source and resumed branches. Restored weights/counters/occupancy are checked before reset; the atol1e-6 weight test and architecture check remain. The fixture bridge supplies actual min_size1000 and passed capacity10000, explaining why old100+50 never trained. No production readiness is weakened.

The new recurrent checkpoint is correctly asserted as current captured6: action_dim A, captured legality, all six resolved option leaves, actual bool successor masks and recorded bits, int64 transition IDs, episode IDs/spans, active2 transitions and no fabricated history archives. Complete source/restored learner state equality now includes replay. Fresh ENV/completion/count/hidden/current-episode reset is distinct from retained learned history. Completion once, repeated-save survival history, pending rollout exclusions, nonterminal successor semantics, source checkpoint bytes and source state immutability remain. Removing old-format5 expectations for newly produced current state is correct; genuine immutable old5 archival guarantees belong to the separately protected fixtures, whose passing status is attributed to root.

## Coverage limits and inherited confounders

- The admission test follows the actual bound object but does not force lazy replacement, and its fixture is not chunked by a tiny capacity. It proves this real first-write route, not every replacement/chunk scenario. Final source review must inspect the idempotent binding and cross-chunk duplicate guard explicitly.
- No new explicit missing/phantom/duplicate-admission mutation test was added. Existing semantic equality and replay-size checks detect ordinary missing/phantom admissions; the four real-producer tests should not be described as independent mutation coverage for every bad observer implementation.
- The repaired recurrent checkpoint test proves exact captured replay roundtrip and active occupancy, but performs no readiness/sample request or post-resume learner step. Do not call it an executable proof of sampleability/optimizer continuation. The initial audit's proposed sampling check was not implemented. This is a coverage limitation, not a discovered serialization defect; separate native producer/learner proofs must carry that claim.
- Checker868–871 overwrites collector.errors with semantic_errors. Thus collector-only exact torch reward-sum diagnostics do not decide qualification; semantic reconstruction intentionally accepts small float32 reassociation at retirement. This inherited distinction must remain explicit. It is not fixed by adding new collector.errors messages. Actual Q/action identity checks that are essential to repair should fail directly or enter independently enforced semantics.
- Existing unrelated checkpoint tests with50 or100 ticks may preserve initial weights below warmup. They test roundtrip preservation, not optimizer advancement. Only the repaired resumption node establishes resumed training here.

## Required safe root execution and native obligations

Root must observe the intended causal failures before authorizing production repair; then run the same four UNIT nodes and full comparator file, the exact two checkpoint repairs and affected/full required gates on frozen identities. Use the already verified no-auto-checkout import/fixture harness. No ordinary pytest/oracle bootstrap is certified safe by this review because conftests/helpers were deliberately not read. No oracle checkout, new worktree or .oracle write is authorized.

Production source_identity483–492 still rejects dirty execution-bearing src/configs/scripts/tests/pyproject/lock paths, including staged changes. Do not introduce an allow-dirty flag, monkeypatch native provenance or call _produce to evade it. Genuine native captures follow the local exact-tree commit only after its required gates pass, and precede push qualification. The committed revision and source binding must be recorded honestly; UNIT synthetic stamps and precommit gate artifacts retain their actual labels.

For each of authored-two-five, two-episodes-reset, budget-six, passive-two-five, death-at-lifespan and healthy-retirement, execute the existing native CLI with a separate previously nonexistent output directory, using this exact command shape (replace RECIPE and OUTPUT explicitly):

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe RECIPE --output OUTPUT
```

The CLI pins subprocess PYTHONPATH/CPU and copies config data only; inspected code has no source checkout/worktree/bootstrap action. Native exit0 validates artifact consistency but does not require contract.qualified. Explicitly require every capture contract == {qualified: true, errors: []}, complete coordinate inventory, real imports/revision/config/instrument/action bindings and exact recipe budgets/completions. Preserve outputs; choose a fresh suffix on rerun. Source/config stamps are checked before and after production. Old-instrument captures or changed real inactive action manifests are not automatically comparable: compare requires identical instrument/config/actions and exact declared differences. Do not relax that contract to obtain a before/after pass.

Overall: initial test-first authoring and narrow checkpoint fixture repairs are statically acceptable; checker production remains BLOCKED by the two known defects. Await root RED and script-only repair, then reuse this bounded three-source context for final review. No runtime PASS, full qualification, release or push approval is claimed.

### Root clarification incorporated

No reachable case has been established here in which a real required capture failure appears only in collector.errors and final semantic reconstruction wrongly qualifies it. The exact torch-sum versus retirement float32-tolerance distinction is intentional, not evidence of false acceptance. Treat the overwrite observation solely as an inherited diagnostic limitation/optional P3, not a material gap or new repair requirement. Root confirms forced lazy replacement and recurrent continuation have separate strict main-owned R2/native coverage. This existing flat authored lane checker need not acquire those purposes; its test boundaries above neither block the checkpoint repair nor expand this task.
