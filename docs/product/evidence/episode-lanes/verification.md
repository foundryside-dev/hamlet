# Truthful episode lanes — implementation verification

Status: **accepted — bounded local implementation; Astra criteria1–8 PASS**.
Production evidence: `462e8a3980845d76e7987cfea67fb63432bcb847`; accepted final
test candidate: `7dc1d02e78d8b70bd096fc4c84b4d95a9822c94f`, local
`fix/episode-lane-accounting` execution worktree. Direct parent:
`880f9c90f65aa646a0da04d7ca2ef92e48f85caa`. The complete unfiltered suite passed at this source. Astra has verified
the review repair, final captures and full-suite receipt. Astra accepts all eight criteria after the strictly bound test-reader cleanup.
Its [final review](implementation-review.md) and [machine-readable review](final-review-at-7dc1.json)
identify the accepted candidate; [verification receipt](verification-receipt.json)
binds complete gates, source closure, separate cleanup and retained artifact manifest.

## Contract and implementation

An eligible transition belongs to a lane active on entry. Its ending step is
retained; later sticky terminal flags admit no replay, novelty statistics,
predictor input, reward contribution or repeated completion. Counts freeze at
actual survival. Authored death wins a coincident lifespan boundary; a genuine
retirement adds its existing bonus once to the canonical extrinsic component.
Completion stores owned CPU observations/meters and remains fixed until reset.
External cap, budget, shutdown and checkpoint cuts complete the lane without
rewriting its MDP terminal flag; their last valid successor still bootstraps.

Standard/PER replay selects eligible rows; recurrent replay ends each sequence
once and preserves inactive hidden state while another lane lives. Reset refuses
unfinished nonempty experience. Actual optimizer policy is unchanged: Q/PER
cadence uses vector ticks, target synchronization uses optimizer updates, epsilon
uses batch episodes, and predictor cadence uses eligible occupancy.

Current artifacts are strict cuts: nested population checkpoints require format
6; recordings require format 2 and complete canonical components; SQLite
requires schema 1. Old formats refuse instead of migrating. Database preflight
refuses any original sidecar family before mutation and checks an isolated copy.
Offline readers release custody before the next export opens the database.

DB, per-lane TensorBoard, curriculum, ordinary indexed recordings, replay,
actual observer emissions and both curves exporters use the same completion
ledger. CSV names distinguish slot-zero survival, batch vector ticks, live-agent
transitions and cumulative live-agent transitions. Inclusive recording prefixes
retain earlier positive intrinsic reward when terminal intrinsic reward is zero.

## Evidence against each PRD criterion

All paths below are relative to retained artifact root
`runs/episode-lanes/2026-10-02/implementation/` in the execution worktree.
The repository tests and preregistrations remain the reproducible source.

| Criterion | Concrete evidence | Current disposition |
| --- | --- | --- |
| 1 Runtime | Committed authored END_LANE pack through compiler/compiled brain; independent entry-event ledger; deaths2/5, reversed, simultaneous, single and boundary fixtures | Six final lifecycle recipes pass at462e |
| 2 Replay | `test_episode_lane_population.py`: actual standard/PER row identities, recurrent sequences `[2,5]`, two episodes and once-only finalization | Focused checks pass |
| 3 Learning/exploration | `test_episode_lane_learning.py`: actual samplers, Q/RND loss and optimizer calls, parameter changes, terminal versus cap targets; controlled numerical bank below | Focused and numerical checks pass |
| 4 Rewards/outcomes | `test_episode_lane_environment.py` and population/sink tests: no later dead contribution, death wins coincidence, one retirement, owned final snapshots under live-storage mutation | Focused checks pass |
| 5 Consumers | `artifacts/S3/`: actual two-episode runner, normal queue/thread shutdown, SQLite/EventAccumulator, format2 files/index, real replay and observer handlers, both real CSV exporters | Ordinary pipeline and strict private-read refusal controls pass |
| 6 Endings/reset | Budget6 survival`[2,4]`, explicit caller cap3 below lifespan10, checkpoint flush/load, repeated flush, two episodes, actual replay done flags | Focused checks pass |
| 7 Attribution/gates | Original799 lifecycle coordinates; CPU-controlled five-cut numerical attribution; retained original inherited failures and prospective PDR0161 adjudication | Narrow adjudication and all complete-candidate gates pass |
| 8 Acceptance | Independent Astra implementation review reads source/callers and each criterion | Interim58a refusal preserved; R1 resolved; final7dc1 ACCEPTED, all eight criteria PASS |

## Numerical attribution and preserved failures

Before runtime changes, E1 banked six direct-parent lifecycle recipes and
preregistered **799 concrete changed coordinates** in
[intended-differences.md](intended-differences.md). DIV-016 was registered before
E2. E2 changes counts/entry events; E3 changes canonical terminal composition;
P1 changes replay/predictor admission and once-only completion. Their full causal
SHAs and actual readings are retained. No field or reward-stream wildcard is used.

The original learned numerical bank remains **unqualified**: standard replay
sampling consumes global Torch RNG differently after phantom rows are removed,
so a later natural reset changes world inputs. Countercontrols isolate that
coupling; production RNG isolation remains excluded. [PDR-0160](../../decisions/0160-align-controlled-reset-inputs-without-changing-production-rng.md)
and its independent [Astra review](controlled-reset-review.md) prospectively
approve an external CPU-only controlled-reset fixture while retaining the failed
original bank. The unchanged helper/instrument bytes and original files are
verified by digest. This is controlled comparison evidence, not natural
production world equivalence.

The final eight recipes at `462e8a39` exactly match P1-controlled-reset and the
retained `58a7048e` bank in all
world/numerical rows, actual queue insertions/consumption/history and initial/final
Q and predictor parameter hashes. Five cuts/40 captures independently check
36,000 world fields, 3,240 reset fields, 320 caller CPU RNG restorations,
6,120 normalization values, 3,600 DAC/geometry rows and 1,800 actual predictor
queue calls. Every final recipe normalizes, admits and trains 63 eligible samples,
leaves 0 pending and completes 18 outcomes `[2,5]` across nine episodes. Both
networks change parameters in all eight recipes. Q updates are 45 for
standard/PER and 5 for recurrent: eligible completed sequences change the point
at which the existing recurrent warmup unlocks, without redesigning that policy.
The numerical receipt retains 5,928 canonical/Q chains and 6,848 raw-MSE/RMS
chains with measured values and causal SHAs. Same-network full2-versus-selected1
forward controls reproduce intermediate raw-MSE roundoff (maximum 2.79e-9),
within frozen bounds.

The unchanged inherited static-access and scripted frozen-oracle commands both
return **1** at `8e3ca306`; those failures stay visible. Static discovery retains
31 inventories/884 readings, ten CPU traces and eleven exact reset recipes.
All identities and observation/action/done streams remain unchanged. Exactly
seven row99 reward coordinates change1 → 0 in items/effects smoke cells, each
already dead on entry. E2 alone removes their manufactured retirement bonus;
E3 adds no differences. The genuine items lane2 retirement reward remains
exactly1.0099999904632568. Explicit original frozen-action executions bridge
oracle→parent→E2→E3→candidate. The standing report retains eight registered CPU
verdicts, two DIVERGE and ten CUDA skips, including its original dirty flag.
[PDR-0161](../../decisions/0161-adjudicate-exact-inherited-terminal-bonus-coordinates.md)
authorizes a prospectively frozen exact-coordinate qualifier. Its first execution
returns 0 and rejects all 42 private-copy corruption controls. Independently
reviewed complete source fences, 182 evidence and 434 config bindings remain
unchanged. Four actual final462e bridges match the earlier candidate exactly.
Astra independently audited the executed receipt and qualifies bounded E4.
No harness/matrix/register stream allowance has been broadened and neither
original exit is relabelled 0. The immutable prospective specification/checker
is [registered here](inherited-terminal-registration.md).

## Gate custody and limits

The execution worktree owns its locked `.venv`: Python3.13.15, Torch2.11.0+cu130,
SQLite3.53.1. Imports resolve to its own `src/townlet`. Parent/causal captures use
that interpreter with explicitly selected clean source roots, recorded imports,
complete source/config closures and frozen external instruments. Qualification
receipts retain argv, full SHA/tree, UTC times, statuses, environment, lock and
log digests. Documentation preparation is separately recorded as dirty state;
executable files are committed and checked against their source closures.

Ruff, Black, mypy, no-defaults with the original whitelist, compiler CLI and
33-pack smoke checks return 0 at corrected candidate `462e8a39`. The earlier
`58a7048e` changes only the
enclosing recurrent BPTT test: the original test assumed retained positive
survival meant active; it now uses actual pre-entry dones and additionally
checks completed hidden state. The original enclosing run retains 1078 passes,
seven skips and that failure. Eight affected recurrent cases pass after repair.
An earlier unfiltered run on the superseded test identity was stopped and
retained as an interrupted attempt. The unfiltered suite with coverage at
`58a7048e` collected 4,639 cases without markers, ignores or exclusions, then was
interrupted after Astra found R1. Both incomplete attempts retain
logs/cancellation and actual exit-9 receipts; neither is a passing suite or
coverage reading. The current repaired-candidate suite uses `.venv/bin/pytest -rs` with default
branch coverage: `-rs` reports individual skip reasons and selects no tests. It
collected 4,670 cases: **4,652 passed, 18 skipped, 31 warnings**, exit0,
1187.28 seconds, **85% branch coverage**. All 18 individual skip dispositions
are retained below; no new required witness is skipped. The original warning
reading includes 15 existing configuration UserWarnings and 16 unclosed SQLite
validation-reader ResourceWarnings. Allocation tracing with forced garbage
collection identifies those 16 native connection allocations at five contexts
in exactly two new test modules. The follow-up changes only those contexts to
`contextlib.closing`; no production behavior or test assertions change. Plan F
permits affected gates after executable receipt preparation; Astra independently
requires complete unchanged production/config/scripts/lock/other-test closure,
exact reviewed two-file diff and all 30 affected/pipeline cases with forced
collection and both ResourceWarning and unraisable-warning categories as errors.
The historical full-suite warning count remains 31, never rewritten as 15.

Astra independently ran 60 environment/population/actual-learning regressions,
all passing, and read every production diff area against PRD1–8. Its preserved
interim review is **NOT ACCEPTED**: R1 demonstrates that `mode=ro` on an original
legacy WAL-mode DB creates a zero-byte WAL and 32768-byte SHM before rejecting
missing columns. Both real exporters use that reader. The committed repair reuses
strict raw family/schema preflight and queries only a validated private snapshot,
with whole-family refusal guards through later TensorBoard reconciliation.
Thirty-one custody cases, including both real exporters, preserve original
bytes/existence/dev/inode/size/mtime/ctime and prove no original SQLite opens.
Successful current WAL reads and late event failures preserve the family; an
externally injected journal triggers refusal and its bytes remain retained.
The root checks 42 custody/actual artifact-pipeline cases; the owning repair
checks 163 DB/script/sink cases plus 11 actual artifact-pipeline cases. Astra
independently repeats the original WAL failure scenario and all 31 custody
cases at462e and verifies R1 resolved.
The original failing probe and source identity remain retained separately from
repair checks and eventual acceptance. The final six lifecycle captures preserve
all 799 registered changes, 4,008 other parent readings and all 4,807 P1/58a
readings. Final numerical/lifecycle receipts also verify 246 historical files
unchanged. Astra independently audits their complete payloads, command exits,
source/config/action/recipe identities and preservation digests; no further
confirmed finding remains. The full suite passes. Final cleanup commit `7dc1d02e` changes only two imports
and five test validation reader contexts; all 1,059 other execution files remain
byte-identical to the 1,061-file qualified inventory. The owning forced-GC gate
passes all 30 affected/pipeline cases with zero warnings. Astra independently
repeats those 30 cases, with both warning categories as errors and actual
collection after every call/teardown: 30 passed in26.12s, zero warnings.
Its final verdict is **ACCEPTED**, all PRD1–8 criteria PASS, no blocking findings.
Production source tree remains `325acd476544463f8c3e2b9dddd5c68310775a44`.
The final candidate has no fresh full-suite reading; exact source preservation
and the plan-authorized strict affected gate carry the full462e proof forward.

There is no push, PR/main integration, hosted CI, CUDA, convergence or recovery-exit
acceptance from this local candidate. Effects reset, initial-item cache loss,
production RNG isolation, warmup redesign and complete BAC remain separate work.
Historical/new artifacts and frozen inputs are preserved. Backout uses previous
source with fresh artifact paths; old source must not consume newer formats.

## Individual full-suite skips at 462e

These are the exact `-rs` dispositions from the complete, unfiltered run.

```text
SKIPPED [1] tests/test_townlet/integration/test_determinism.py:70: CUDA not available
SKIPPED [1] tests/test_townlet/integration/test_determinism.py:83: CUDA not available
SKIPPED [1] tests/test_townlet/integration/test_episode_execution.py:108: Flaky test - agent dies from cascade effects intermittently (see git history: c6dbd12, 930b201, 3158cd7)
SKIPPED [1] tests/test_townlet/integration/test_runner_integration.py:242: Flaky: depends on stochastic agent behavior to interact with affordances
SKIPPED [1] tests/test_townlet/integration/test_substrate_factory_nd.py:36: v2.1 GridNDConfig doesn't enforce minimum dimensions at DTO level
SKIPPED [1] tests/test_townlet/unit/environment/test_vectorized_env.py:893: Test config missing 'Bar' affordance
SKIPPED [1] tests/test_townlet/unit/substrate/test_config_nd.py:58: v2.1 GridNDConfig doesn't enforce minimum 4 dimensions at DTO level
SKIPPED [1] tests/test_townlet/unit/substrate/test_config_nd.py:100: v2.1 GridNDConfig doesn't enforce maximum 100 dimensions at DTO level
SKIPPED [1] tests/test_townlet/unit/substrate/test_config_nd.py:253: v2.1 ContinuousConfig doesn't validate range vs interaction_radius
SKIPPED [1] tests/test_townlet/unit/substrate/test_config_nd.py:371: v2.1 SubstrateConfig doesn't validate continuous/continuousnd dimension ranges
SKIPPED [1] tests/test_townlet/unit/substrate/test_config_nd.py:392: v2.1 SubstrateConfig doesn't validate continuous/continuousnd dimension ranges
SKIPPED [1] tests/test_townlet/unit/training/test_prioritized_replay_buffer.py:841: CUDA not available
SKIPPED [1] tests/test_townlet/unit/training/test_replay_buffers.py:373: CUDA not available
SKIPPED [1] tests/test_townlet/unit/training/test_replay_buffers.py:389: CUDA not available
SKIPPED [1] tests/test_townlet/unit/training/test_replay_buffers.py:571: CUDA not available
SKIPPED [1] tests/test_townlet/unit/training/test_replay_buffers.py:1266: CUDA not available
SKIPPED [1] tests/test_townlet/unit/world/expression/test_integration.py:86: Function call type checking deferred to Phase 2
SKIPPED [1] tests/test_townlet/unit/world/expression/test_integration.py:136: Index access type checking deferred to Phase 4
```
