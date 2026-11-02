# T15 implementation readiness — stationary preparation

Read-only preparation in existing `/workspace/hamlet`, 2026-11-01. Observed HEAD `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; tracked status clean. Root reports T14 full R3 still running; this note makes no qualification/release claim and authorizes no code/runtime work. Await root's tests-first dispatch after actual qualification.

## Exact complete source context and approved identity

Exactly four existing implementation files were read completely; no SB/PB/RB/runner/provider/brain/network/conftest/helper/other test implementation was opened. The fifth owned learner test remains absent.

| Source | Actual lines / projected ceiling | SHA256 |
|---|---:|---|
| `src/townlet/population/vectorized.py` | 1854 / 3000 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| `src/townlet/training/replay_contract.py` | 222 / 250 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| `src/townlet/training/q_targets.py` | 80 / 100 | `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f` |
| `src/townlet/config/bac_options.py` | 294 / 600 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| `tests/test_townlet/regressions/bac/test_learner_legality.py` | absent / 1000 | not created |

Actual source total **4/2450**; projected total **5/4950**, 50 below hard 5000. Recount before authoring/review and preserve every control. Root reports reconciled metadata 603 shared/interface pairs, 315 ordered mutation pairs and 55 contracts; this worker did not edit that metadata or the frozen 66-task plan.

| Consumed prose artifact | Verified SHA256 |
|---|---|
| Frozen approved plan | `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` |
| Current amended `tasks/task-T15.md` | `19c1f6b4f41c7c97eacbf49787c0f402e807cc2239c50d76b546d365d63318cd` |
| `T15-interface-proposal-r1.md` | `70b155234f553855675a235d980674afdc3588d92e71dd054bba5b69f0e56d0a` |
| `T15-interface-astra-review-r1.md` — APPROVE | `42c211db2a3326cbf018bb94cd774f522fe2bf56fdcacf2e84d0c23c7791e818` |
| `T15-preparation.md` | `b0b132a2dd69cc147d43a8566c3f14a4f72921a08ed428e045bdf5a332417ca1` |
| `T15-config-contracts.md` | `bdb2ec0a5ec1fe9f97845e6fadf978940781e2854206b71480d97b10d0329417` |
| `T15-flat-contracts.md` | `7b82cb51be4680f3fec91338962ae4da2590bf5357a1ebcbaa0407b4dec1181b` |
| `T15-provider-contracts.md` | `bb5760e1ee1f6d681115ed4b353d073def796b5d8c279ca42d1cc1997284a71f` |
| `T15-constructor-runtime-consumers.md` | `9048ba713a2540bc8a8e7bf9e45ebbc01ba619b3732a32663dc0049c1104d23c` |
| `T15-constructor-unit-consumers.md` | `3d4b45239fa0eed2c7a5a87995b5143137eed1a67927e81d06ecb48958490e41` |
| `T15-constructor-fixture-suppliers.md` | `0ce1d3732ba2ff231495dbecbe8f2f73c04da18cf5f2bb850bb71fb5a2793f19` |
| `T15-constructor-factory-bridge.md` | `ffe98bb8fa69aef0c1f338d4816375530e69499956999bb2351ace574e81b789` |

Project AGENTS/CLAUDE and both STATUS documents were read. Using-superpowers' dispatched-subagent stop applies; cloud-runtime and verification-before-completion guidance were read. Managed-environment readiness was checked without credentials; no network/project runtime was used. Newer preservation/addition and approved History A govern. No durable user-only fallback was adopted; the failed rule grants/restricts nothing. Root owns integration/index; all 14 worktrees/backups remain untouched.

## Concrete future owned-test controls

All rows below are **unexecuted** controls for the single owned test. Existing bug REDs must reach behavior through the existing constructor where practical; do not make every case fail solely at the absent `for_training` method. A separate factory/recurrent-PER feature-boundary RED must prove the genuinely selected prioritized brain is refused/missing today. No import/fixture/setup error is causal RED evidence.

| Control | Required observation and distinguishing negative control |
|---|---|
| `test_authored_target_matrix_and_direction` | Four families × vanilla/Double × globally/state-dependent illegal alternatives × uniform/PER. Reward1/gamma0.5/legal successor4/illegal100 yields target3 rather than51; WAIT prediction starts4 and decreases after real finite optimization. Existing flat constructor establishes wrong-target RED; natural `for_training` selected recurrent PER proves production construction/updates, without false-brain attachment. |
| `test_terminal_and_truncation_controls` | Terminal successor may be all-false and gives target0; external cap keeps doneFalse and actual stored mask, giving bootstrap3. Recurrent interior and final-real boundary both covered. Mutate later/current masks independently to prove targets consume the committed stored masks. Preserve canonical total and component provenance. |
| Strict selection/capture | Unequal live lanes; provider sees exactly entry-eligible aligned Q/state/per-row epsilons/masks once, inactive slots draw nothing and use transport argmax; eligible empty masks refuse before RNG. Cover all five supported providers and preserve independent reward/service/completion work. Oversized eligible flat batches use bounded ordered insertions without lost accounting. |
| Real readiness | Sixteen length2 episodes/L3 cannot form full windows; capacity15/L3 controls distinguish retained warmup/sampleability. Adaptive capacity1/L8 learns one real row; fixed-full reports truthful impossibility/window reason. Successive B>N skips; replacement B>N may update. Pending collector rows never count; complete fragments commit exactly once. |
| `test_ready_skip_preserves_update_clocks` | Warmup/window/batch/unscheduled skips preserve optimizer/scheduler/target/update counter and rollout hidden; successful steps advance exactly once. Vector ticks and beta advance independently, including skipped ticks; equal tick idempotent, ordinary rewind refused. Diagnostics change with reason/counts. |
| Exact recurrent prefix/BPTT | Unequal lengths and distinct stored interior successors; online/target with different history-dependent weights catches crossed/reset/shifted hidden. Graph-connected current prefixes carry earlier real-step gradients; detached bootstrap branches do not advance either prefix. Poison padded obs/actions/rewards/Q cannot affect calls, targets, loss, gradients, hidden or telemetry. |
| Objective/stable feedback | Independent per-unit loss oracle distinguishes window-mean from global-row average and anchor-only loss from context rows. Returned float64 weights apply once, including uniform legacy nonunit weights. Both PER laws/objectives/reducers and repeated IDs receive matching detached pre-update residuals/canonical masks through stable IDs, never receipt positions or pre-added epsilon. |
| B1 and modes | Flat B1 remains [B], recurrent B1/L1 remains shaped. Force online eval/target train before an update; observe online train/target eval. Keep working zero-width/presets/mean/attention choices. |
| `test_archived_rows_cannot_drive_learning` | Genuine supported old uniform4/PER4/sequential5 import remains query/export exact, active0 and unsampled; restored learned/vector/LR/target clocks remain. New captured-row warmup blocks then allows legal target3 update. Storage attachment proof is labelled separately from selected-factory production proof. Current captured resume stays active. |
| Lazy binding/current restore | Existing constructor plus current load before first step preserves captured rows, archive, IDs/domains/priorities/private RNG/beta/clocks. Already attached qualified state, including zero-active but owned archive/ID/sampler history, is adopted without replacement/reseed/reconfigure. Required adaptations prepare/materialize offside at restored tick and failure leaves live state/clock unchanged. |
| `test_large_finite_td_mean_is_truthful` — X04 | Actual flat uniform/PER controls run two successful Huber/Adam updates with two finite residuals near2e38, finite loss/parameters/Adam state and real parameter change. Pre-update independent float64 operand-subtract/abs/mean oracle, rtol2e-6. Add recurrent all-real-row, B1, modest unequal, unequal lengths, poison padding, anchor context and nonuniform weight controls. Metric is unweighted over sampled real rows, including repeated samples; no clipping/zeroing/reward restriction/objective change. |

## Fixture prerequisites and later qualification

Use source-verified public fixtures/APIs as prose receipts: real compiled `env_factory`/CPU/custom/config-pack routes and passed brain roles. Their actual selected `env.level.training` supplies central OP resolution, real min_size, seed and declared limits; constructor-only selection/inspection/nullable serving/global sampler roles stay callable. Own test-local controls belong in the reserved test, with no sixth helper read.

The approved public seam uses required `for_training` inputs and one common initializer; normal learning binds central compiled policy before admission. Owned RNG is explicit separate `Generator(PCG64(training.seed))`, origin `authored`, distinct from option-leaf provenance. Horizon is explicit named max_episodes×max_steps with actual declared/launch sources. PB uses actual `configure_sampling`, not nonexistent `for_sampling`; flat and recurrent request geometries remain distinct.

Lazy setup is policy binding/adoption, never unconditional factory/reset. First step or active0 does not prove pristine. Do not rerun initialization or reconfigure a restored private sampler; preserve low-level inspection roles. Raw POP6/current storage checks do not claim complete native10/7; T24/T25 remain required OPEN.

Separate bounded owners maintain eligible projection of `controlled_action_schedule` while retaining the full-N real env.step witness; `check_episode_lanes.py` instrumentation must observe captured insertion. Recurrent manual collector fixtures need truthful successor-mask/recorded lists, and learning/scheduler-progress fixtures need genuine capture/readiness/update evidence. Their implementations remain unopened here.

After root dispatch, causal command is `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_learner_legality.py -q`. Retain population owner suites plus authored episode lanes, recurrent bootstrap/BPTT, episode-lane population/learning and affected replay suites; all six guards, fresh other-model review/repair and mandatory full G2/public-contract qualification remain. Root owns actual import/fixture/collection/source custody, commands/results and four-CPU scheduling, with explicit workspace TMPDIR/basetemp; no bare project Python/pytest under full `/tmp`.

**Blocking ambiguity:** none newly proved by this bounded source inspection. Approved R1 resolves the finite interfaces; acceptance above is preserved. This ignored note is the only write. No code/test/index/tracked/metadata edits, imports/runtime/pytest/collection, branch/worktree/source copy/subagent, commit or publication occurred. Return stationary for root's qualified tests-first dispatch.
