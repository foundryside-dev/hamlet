# Future T15 interface/preparation provenance

This is bounded source-verified preparation or technical design review, not T15 implementation, executable acceptance or owner approval for any reduction. Original T15-preparation.md SHA256 `b0b132a2dd69cc147d43a8566c3f14a4f72921a08ed428e045bdf5a332417ca1`; its actual earlier read/runtime identities remain explicit. T14 status in the body records its historical preparation time.

# T15 bounded preparation — stationary, no implementation dispatch

Prepared in existing `/workspace/hamlet` against HEAD `01f2f64f42c2932177729607b337419355cb2720`. Root supplies frozen T14 candidate tree `324438ad58d9d5a85bba54e18be1ee225ada5969`; this preparation did not run `git write-tree` or independently manufacture a candidate. T14's mandatory 6,712-selected full suite was **RUNNING, not passed**, when this task was dispatched. No T15 implementation, regression authoring, collection or runtime is authorized by this preparation. Root owns predecessor qualification and any later dispatch.

The original approved plan remains byte-frozen at SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`. This is finite preparation for existing T15, not a new design programme: 66 tasks, 54 effective requirements and 22 final lenses remain unchanged. X04 is required T15 producer acceptance before release/G2; T35 consumes its verified metric receipt.

## Custody, guidance and complete source inventory

Read applicable root AGENTS/CLAUDE guidance, STATUS owner rulings/method/severity, the extracted T15 brief and own requirements, frozen-plan P1–P4, approved execution/history/native handoffs and the bounded predecessor prose listed below. The user's preservation/addition instruction and approved History A supersede conflicting blanket deletion guidance. Public constructors, old interface roles, four network families, working presets/zero-width policies, mean/attention, sampling choices and current captured history remain preserved. Only the specific approved pre-capture maskless optimizer-history reduction is selected.

No durable rule was saved; the user-only fallback was not adopted; the failed rule grants or restricts nothing. Existing instructions and actual tool approvals govern. Existing 14 worktrees are preserved. No checkout/branch/worktree/source-tree copy/deletion, subdelegation, staging/commit, index/metadata modification or unrelated tracker claim occurred.

Skills read: `superpowers:using-superpowers` (its explicit subagent stop applies), `cloud-environment:cloud-environment-runtime`, and `superpowers:verification-before-completion`. Managed-environment status was read without credentials; no network work was needed. This is inspection of the accepted task, not creative implementation or a new plan.

Exactly **four complete existing implementation sources / 3,971 lines** were read, including their complete checkpoint/legacy portions. No implementation/test/helper contents outside this table were opened. Public contracts attributed to accepted prose below are not extra source inspection.

| Source | Complete lines | SHA256, checked before/after |
|---|---:|---|
| `src/townlet/population/vectorized.py` (POP) | 1854 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| `src/townlet/training/replay_contract.py` (RC) | 222 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| `src/townlet/training/q_targets.py` (QT) | 80 | `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f` |
| `src/townlet/training/sequential_replay_buffer.py` (SB) | 1815 | `f958b1ed79bab5a37422353a04a9d78c05969950dfbf994436b4e1ce0e73392c` |

Reserved fifth source `tests/test_townlet/regressions/bac/test_learner_legality.py` is **ABSENT**. Its old reservation is 350 lines, not an already-created/read test. No OP, BrainConfig, runner, environment, flat replay/PER implementation, network, seed helper, other test, conftest, external probe or harness implementation was opened. Path inventories and public prose were inspected without executing the project.

## Actual predecessor boundary

Root's R1 common binding reports core69/native65/sequence-history136/native-consumers118 and all six guards PASS, plus independent core69/native65/owners63 PASS and three fresh source/spec reviews. Counts overlap and are not summed. This preparation neither reran nor upgrades those results; the mandatory full suite is still pending in the supplied binding.

SB now supplies explicit prioritized sequence construction, absolute vector ticks, request-owned multiple-L context domains, both PS laws, both objectives/reducers, portable owned five-family RNG state, strict prioritized7 and genuine captured6 active adaptation. It does **not** supply the population consumer changes below. Existing POP construction still rejects recurrent `prioritized=True` (POP254–265), uses unconfigured two-argument SB, and emits raw population format6 (POP46,1178–1197). T14's explicit factory attachment proof exercises rawPOP6/inner7 save/validate/load; it is not natural authored recurrent-PER construction, native10/7 admission, evolved optimizer continuation, or complete C07.

Keep genuine original118-wide/34-row DATA distinct from the native105 matching-geometry capture and newly authored labelled3-row archive. Neither source geometry nor fixture identity is changed by describing their roles. Complete native10/7 admission/registry/accounting/atomic install remains T24/T25. A newly caused failure of an existing consumer must still be repaired before release; a future-task label never waives it.

## Concrete collection and successor-legality hooks

1. **Eligibility already exists.** POP727 clones `~envs.dones`, prevents completed lanes reentering, preserves inactive recurrent rollout hidden at POP737–742, and later consumes committed `info['active_on_entry']` at POP793. Collection at POP809–833 already filters these eligible rows. Keep terminal-causing eligible actions once and completed transport lanes inert. The temporary curriculum state deliberately has `dones=False` (POP748–757); it is not a truthful source of action-selection eligibility.
2. **Selection is not yet strict.** POP781 calls the old exploration `select_actions(q_values,temp_state,action_masks)` protocol; public epsilon selection POP686 uses the legacy action helper. Accepted T08a/T15 prose supplies `epsilon_greedy_action_selection_eligible(q_values, epsilons, action_masks, *, eligible)`. T15 must use that strict helper or truthful filter/select/scatter, passing the actual entry eligibility, diagnosing eligible live-empty masks and avoiding inactive RNG draws. Preserve the public selectors and exploration protocol; root must resolve the producer adapter rather than pretend temp-state dones establishes membership.
3. **Exact successor is available but mask is ignored.** POP791 receives `(next_obs,rewards,dones,info)` from ENV; accepted T09 receipt states that the same committed info owns cloned bool[N,A] `successor_action_masks`, including valid terminal all-false sets. POP currently never reads this key. Capture it from that same step and eligibility selection, before any later environment query/mutation. Learning must not call `env.get_action_masks()`.
4. **Recurrent collector changes are local and explicit.** Add owned successor-mask and legality-capture lists to `_new_episode_container` (POP336–351), append per-eligible-row values beside exact `next_obs` at POP812–819, stack them beside the existing canonical episode data in `_store_episode_and_reset` (POP468–482), and call public SB `store_captured_episode(episode, *, next_action_masks, legality_recorded)` (SB1181–1230). The episode mapping itself accepts only its existing row/component keys; masks/recorded bits are keyword arguments, not invented extra episode keys. Every real production row records True. Keep canonical total and independently optional components; do not recompose DAC reward.
5. **Flat collection needs the qualified adapter.** POP827 currently calls plain `push` without masks. Accepted T10/T11/T13 prose names `push_recorded` for actual constrained masks; the exact current flat signatures are not present in the four sources. Root owes the source-verified call contract before authoring. Never satisfy production capture by declaring an unconstrained/all-legal invariant.
6. **Commit timing matters.** Current recurrent episodes enter SB only on `_finalize_episode`/`flush_episode` (POP587–614). Training currently runs before terminal finalization at POP841–1068 versus1073–1080. SB has a complete-fragment `store_captured_episode` API, not an incremental prefix-replacement API. Pending live lists are not retained replay and cannot count toward warmup. Repeatedly storing growing prefixes would duplicate transitions/contexts. Preserve exact-once storage and define any deliberate ordering change explicitly; do not invent an unprovided incremental backend.

## Qualified replay APIs and update clocks

RC47–60 requires all six request fields: batch_size, sequence_length, min_transitions, sampling_mode, sequence_mode, sequence_objective. Shapes are flat[B,D]/[B]/[B,A] or recurrent[B,L,D]/[B,L]/[B,L,A]; lengths/unit_ids/weights are[B]. Weights are positive float64 and exactly match the receipt; actions and IDs are int64; masks/dones/recorded/loss bits are bool. RC validates real prefixes from lengths, rejects unknown real legality, terminal continuation, malformed loss masks and nonterminal empty successor masks, then owns cloned tensors. It intentionally does not validate padding as experience (RC151–222).

| Route | Actual available hook / obligation |
|---|---|
| Recurrent uniform | SB808 `for_replay(capacity,device,*,options,action_dim,legality_mode)` with fully resolved six-field ReplayOptions and `legality_mode='captured'`. The two-argument constructor remains public legacy transport, not a qualified production factory. |
| Recurrent PER | SB951 `for_prioritized_replay(capacity,device,*,options,action_dim,legality_mode,alpha,beta,beta_annealing,beta_vector_tick_horizon,current_vector_tick,rng,origin)`. All are required. Initial beta differs from effective annealed beta. Caller Generator is cloned; no hidden seed/global stream. |
| Recurrent readiness/sample | SB1257 `readiness(request)` is observational; SB1270 `sample_batch(request)` returns `SequentialReplayBatch`, including component presence bits. Modes must match persisted options. Use retained_transitions, never `len(SB)` (episode count). |
| Recurrent priority update | SB1399 `update_priorities(batch.unit_ids, td_errors[B,W], *, loss_mask=batch.loss_mask)`. Pass detached pre-update residuals and the canonical objective mask. SB owns max/mean reducer, epsilon, duplicate maximum, handle resolution and support checks; the learner must not duplicate them. |
| Flat uniform | Accepted P2/T10 receipt supplies retained_transitions/readiness/sample_batch and preserved uniform without-replacement law. Exact captured insertion/current construction method must be supplied as verified prose by root. |
| Flat PER | Accepted T13 interface receipt preserves constructor and legacy physical `sample`/`update_priorities(indices,errors)`. Qualified entry is `configure_sampling(*,sampling_mode,rng,origin)` or `for_sampling(...)`; `sample_batch(request)` supplies stable tensor unit IDs. Qualified feedback is `update_unit_priorities(ndarray[int64], td_errors)`. Convert owned batch unit IDs explicitly; never pass receipt positions or reinterpret old physical indices as IDs. |

SB readiness precedence (SB1257–1268): fixed-full L>capacity → capacity_window_impossible; retained<min → warmup; zero windows → window_unavailable; prioritized successive B>population → batch_unavailable; otherwise ready. Uniform recurrent adapters sample with replacement and can serve B>N; PER replacement can too. Adaptive-prefix capacity1/L8 has one real row, not eight invented rows. Fixed-full short fragments are a diagnostic/no-update state, not a reason to remove accepted authoring.

Replace POP845's hardcoded16/batch-count gate with scheduled vector tick AND the real request/readiness. Keep diagnostics tied to changed readiness state/reason/counts rather than every tick. An unavailable sample performs no optimizer step, LR step, target sync, replay draw or rollout-memory reset. Recurrent terminal commitment can change readiness for the next scheduled opportunity; describe the chosen ordering truthfully.

`total_steps` is the existing vector-tick clock (POP842), while `training_step_counter` increments only after successful optimizer steps (POP969/1063). `scheduler.step()` is already optimizer-paced (POP961–963,1039–1041): preserve that invariant. Target synchronization remains successful-update-paced. Do not reset rollout hidden to make learning easier; `_unroll_recurrent` is local zero-start memory and does not own rollout state (POP500–519,973–976).

For recurrent PER call `set_vector_tick(total_steps)` (SB983–992) for every advancing vector tick independently of warmup/readiness/training frequency/optimizer success. Its monotonic setter does not draw, preflight hypothetical weights or accept a batch-size argument. Flat PER currently exposes `anneal_beta(horizon,current_tick)` only in accepted/current POP call sites; root must verify the selected qualified flat pacing ABI. Current POP1047–1060 anneals only after successful updates; that is not the required independent vector-tick pacing. Existing max_episodes×max_steps inputs can provide an explicitly recorded derived horizon only when both exist. Missing inputs cannot authorize a hidden new horizon or seed.

## Legal targets, actual recurrent contexts and objective

QT59 `legal_td_target(rewards,dones,q_online,q_target,legal,*,gamma,double_dqn)` is detached, accepts arbitrary real leading dimensions and uses only recorded successor legality. Vanilla passes no online selector; Double selects online and evaluates target. Terminal/no-bootstrap rows become exact zero before argmax/max; unused illegal/terminal outputs may be nonfinite. Gamma0 never reads Q numerically. Call QT on real rows, not padded transport; its real reward validation deliberately rejects nonfinite rewards. Preserve the existing admitted finite high reward.

Flat POP993's unconstrained `squeeze()` must become dimension-specific `squeeze(-1)` for B1. Replace POP995–1005's unmasked max/argmax with QT and the sampled mask. Uniform/PER both perform real forward/loss/backward/optimizer work; the only sampling-weight difference belongs to the returned receipt. Detached pre-update absolute residuals drive priorities, independently of telemetry.

For recurrent batches group by each real `lengths` value and slice exactly `:length`. Zero-start each local window. Online prediction unroll retains its autograd graph across real timesteps (BPTT). Target unroll runs no-grad. Bootstrap each real successor under that network's own prefix state; the final-real successor is stored `next_observations[row,length-1]`, not padded index -1. Double's boundary online selector uses online final hidden; target evaluation uses target final hidden. Never cross those states, reset each timestep, or run either trajectory through padding.

Current POP863–919 correctly distinguishes each network's boundary hidden on full-length windows, but assumes all L rows real and uses unmasked shifted interior outputs. Neither RC nor SB validates `next_observations[t] == observations[t+1]`. Root must make the exact consumed adjacency/producer contract explicit before choosing interior-shift reuse. The preserved requirement is the actual recorded successor under its real prefix; arbitrary shape agreement is not an adjacency proof. This is a concrete missing consumer contract, not a request to open a sixth network/environment implementation.

Use `loss_mask` independently of real-prefix membership. For window_mean, compute each unit's mean over its selected real loss rows, multiply once by its detached float64 unit weight, then batch-mean units. For anchor_transition select the final real row's loss once. Do not divide by one global count of padded/real rows, apply the weight per-timestep again, normalize by batch maximum, or reuse marginal-probability formulas. Uniform legacy length-weighted draws can legitimately carry nonunit window weights; PER flags alone cannot decide whether weights matter. SB already returns exact objective masks/receipts and performs priority reducers.

Before actual updates explicitly call online `train()` and target `eval()`; current learner contains no online train-mode restoration. Preserve target eval at constructor and transfer (POP222,1812) and restore it at update boundaries. Do not change serving-mode/isolation contracts owned by later tasks or claim source-only mode placement proves dropout/isolation behavior.

## X04 finite unweighted TD mean — required producer work

Source defects remain exactly POP947–948 (recurrent float32 masked sum/count) and POP1029 (flat float32 mean). `.item()` after reduction cannot recover an overflowed intermediate. The public `get_training_metrics()` returns the stored scalar unchanged (POP1129–1141).

The admitted actual T13 learner evidence has two finite residuals `1.9999999360571385e38`, finite representable true mean of the same value, and reported `Inf`. High-alpha0 performs two real finite optimizer updates; high-alpha1 also reaches this independent producer error. Do not claim optimizer divergence, a downstream crash, or an executed recurrent authored incident. X04 is confirmed existing telemetry P1 under the authored wrong-behavior bar; recurrent coverage is the bounded same-expression risk control.

Promote the residual/selected diagnostic values **before** absolute-value accumulation/reduction, with a sufficiently wide representation such as float64. Keep the unweighted sample/valid-row mean and Python scalar API. No clipping, zero substitution, omitted field, fabricated denominator or reward-cap restriction. Loss, gradient clipping, priority epsilon/reducer and PER objective remain their configured independent operations. In particular, changing Huber/MSE, weighting TD telemetry by IS weights or using a window-weighted mean is not this repair.

Preservation-consistent recurrent telemetry uses the lengths-derived real-prefix mask, which corresponds to the old valid-row mask, separately from anchor-only loss selection. Root should pin this explicitly when adding anchor mode; silently substituting loss_mask would change which real rows the public diagnostic averages. Exclude padding by selection before arithmetic rather than multiplying arbitrary junk by zero. Preserve duplicated sampled-window rows as sampled observations; no unique-transition deduplication is justified.

Finite controls in the owned test must include flat uniform/PER and recurrent valid-row paths; two large real residuals near2e38; B1; modest unequal values; unequal real lengths; identifiable invalid/padded junk; and nonuniform weights proving telemetry stays unweighted. Compare against an independent pre-update float64 oracle, tolerance2e-6 relative for the admitted case. Require two actual successful updates for the admitted flat witness, finite configured Huber loss/parameters/Adam state and real parameter change. T35 consumes this verified producer result; no sink masking workaround closes X04.

## Actual configuration inputs and exact questions for root

POP112–129 accepts env, curriculum, exploration, IDs/device, BrainConfig, obs/action dimensions, train frequency, batch size, sequence length, grad norm and optional max_episodes/max_steps_per_episode. POP179–182/248–252 reads gamma, Double/target frequency, PER alpha/beta/annealing/capacity from the passed brain. It has **no replay options, effective-run object, training replay min_size, explicit sampler Generator, seed, sampling origin or beta-horizon parameter**. It imports no option resolver/seed helper. Existing `total_steps` begins0 after replay construction. Do not claim absent values are already available through env or brain without a source-verified receipt.

P1 commits to effective brain replacement plus exactly five training overrides, retained authored/execution identities and fully resolved option provenance. T13 public learner recipe supplies a real construction sequence using runner public config, `apply_training_overrides`, env dimensions and explicit public population lifecycle, but that historical recipe does not wire the new inputs. Its temporary seeds731/authored42 are evidence/test settings, not production seed-derivation policy.

These questions are integration decisions for root from actual code/prose; they are not user approval requests or new requirements:

| # | Exact unresolved handoff | Required root resolution before dependent authoring |
|---|---|---|
| Q1 | How does POP receive resolved six-field ReplayOptions and effective warmup `training.replay_buffer.min_size` while preserving the callable existing constructor and legacy caller roles? | Name the already-existing source-verified carrier if one exists, or choose the narrow additive public construction/configuration surface. Identify which current caller T16 will wire and which immediate T15 public path actually consumes it. Do not use batch_size as min_size or locally resolve omitted options. |
| Q2 | Who supplies the accepted replay Generator, its seed/scope derivation, deterministic origin and authored/derived beta horizon? | Provide exact public producer/signature/provenance as a receipt without adding a sixth helper read. No `default_rng()` with omitted seed, global-RNG copy presented as owned policy, hardcoded seed or transient object identity as immutable origin. Record how initial0 and restored ticks enter the factory. |
| Q3 | What are current exact flat captured construction/insertion/readiness signatures and request-mode restrictions? | Source-verify RB/PB `push_recorded` arguments, action-dimension declaration, flat request L/mode/objective requirements and the configured flat PER factory/update ABI. Existing T13 prose establishes roles but not every insertion argument. Keep legacy physical sample/update pair separate. |
| Q4 | How is strict eligible selection composed with the extant exploration protocol for all currently supported providers? | Supply source-verified strict adapter contract or select truthful eligible filter/scatter inside POP while preserving public selectors and provider effects. Temp-state all-false dones is not an answer; current action helper is a public prose contract, not an implementation read. |
| Q5 | What exact interior successor/prefix invariant may the recurrent learner rely on, and what is the new anchor diagnostic row set? | Pin actual captured adjacency or evaluate exact stored successors under real per-row prefix hidden. Pin unweighted real-row telemetry separately from selected loss rows; keep BPTT/each-network hidden/padding requirements. |
| Q6 | Which actual public history import route should T15's archive/warmup test exercise without pretending native10/7 is implemented? | Use existing buffer prepare/load APIs and actual POP6 path where qualified, with truthful construction/attachment labels. Preserve query/export/original rewards, learned cumulative clocks and fresh active0; leave complete native wrapper integration with T24/T25. Do not defer a failure caused by T15 itself. |
| Q7 | What are the exact existing B03 bootstrap/BPTT/lane-learning command selectors, and the final source/test reservation? | Supply accepted owner-suite node names/commands as prose, execute them later without opening their implementations, and reconcile the budget below before dispatch. Current task prose names the gates but does not spell every selector. |

## Finite implementation/test handoff after qualification and dispatch

All rows are prerequisites/acceptance owed, not executed results. Put controls in the owned learner file; reuse public APIs and accepted YAML/prose. No new implicit shared fixture or sixth test is available.

| Required control | Concrete observation / negative control |
|---|---|
| `test_authored_target_matrix_and_direction` | Four families × vanilla/Double × global/state-dependent illegal alternatives; target3 rather than51, WAIT bias decreases from4, actual optimizer/parameter change. Uniform/PER both update, including authored recurrent PER through its real selected construction, not only manually attached storage. |
| `test_terminal_and_truncation_controls` | True terminal target0, terminal all-false successor valid; external cap/bootstrap doneFalse target3 with its real stored mask. Distinguish current-mask changes from stored-mask values. Include recurrent interior and final-real boundary. |
| Real sequence readiness | Sixteen length2 episodes with L3 do not become a full window merely because len(SB)>=16. Capacity15/L3 controls retain actual sampleability/transition warmup. Adaptive short mode learns from real lengths, including capacity1/L8; fixed-full impossible/window-unavailable skips with truthful counts. |
| `test_ready_skip_preserves_update_clocks` | Warmup, missing window, insufficient successive batch and unscheduled ticks preserve optimizer state/count, LR scheduler and target bytes; successful opportunities advance exactly once. Total vector ticks and PER beta can advance while optimizer clocks do not. Equal tick is idempotent; no ordinary rewind. |
| Local recurrent context/BPTT | Unequal real lengths; zero-start local windows; parameter gradients from earlier real timesteps; history-dependent online/target with different weights catches crossed hidden states. Padded observations/actions/rewards/Q junk cannot affect hidden/loss/gradients or metrics; do not run invalid padding through validation/QT. Training never clears mid-episode rollout memory. |
| Unit objective and priority feedback | Independent per-unit loss oracle distinguishes window means from global-row mean and anchor loss from all-prefix loss. Returned weights apply once; selected pre-update residuals plus canonical masks reach stable update APIs. Both PER laws, both reducers and repeated IDs remain supported; receipt positions cannot masquerade as unit IDs. |
| B1 and modes | Flat B1 predictions/targets stay[B]; recurrent B1/L1 stays shaped. Force online eval before update to show train restoration; target eval remains. Do not narrow zero-width/pooling/preset choices to get a test fixture through. |
| `test_archived_rows_cannot_drive_learning` | Genuine supported old history remains queryable/exportable with original reward/component/tensor provenance; active retained0 and zero sampled archive IDs; restored optimizer/LR/target/vector counters persist; new-row warmup blocks updates, then captured legal target3 updates. Captured current history remains active on full restore. No test accepts target51 as live historical optimizer behavior. |
| `test_large_finite_td_mean_is_truthful` (X04) | Actual admitted flat uniform/PER two-update witnesses plus recurrent real-row path; pre-update float64 oracle; large equal/B1/modest unequal/masked junk/nonuniform-weight controls; objective and priority unchanged. |

Meaningful causal RED must target the missing guarantee (mask-free target, recurrent-PER construction refusal, wrong readiness/objective, B1 shape, train mode or finite metric), not import/syntax failure. GREEN later runs exactly `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_learner_legality.py -q`, followed by the actual affected B03 and replay/population owner suites, all six standing guards and required full G2/public-contract trigger. Root owns exact candidate/import/fixture/collection custody, four-CPU scheduling and actual result logs. No T14 result substitutes for these changed-source gates.

Keep standing guards `ruff check .`, `black --check src tests scripts`, `mypy src/townlet`, no-defaults lint with whitelist/ratchet, compiler CLI validation and expression-doc check. Fresh other-model review/repair precedes dependent release. Preserve final coverage≥70%, slow/applicable-hardware, same-SHA22 lenses/synthesis, finite T40, token-schema prefix/frozen inputs and exact-tip remote CI. Receipts retain candidate_sha/scope/focused/owners/static/review/full status/reason/unrun/next gate. No whole-BAC, native10/7 or learning-quality completion is implied.

## Growth arithmetic and bounded reservation to reconcile

The actual current4/3971 plus old test350 is **5/4321**, leaving **679 lines total source growth**. The stale metadata projection POP3000+SB1250+RC250+QT100+test350=4950 would become5515 if only SB is corrected to1815. The task brief's older SB1100/QT180 variant becomes5595 with SB1815. Neither may be reported as a current below-cap reservation.

With SB1815/RC222/QT80 pinned and test350, the absolute POP maximum is2533 (+679). A test550 reservation instead leaves POP maximum2333 (+479). These are arithmetic limits, not evidence that every accepted control fits. Do not compress away matrix, native-history, context/BPTT, padding or X04 coverage to preserve an obsolete350 number.

A concrete in-task reconciliation candidate is **POP2250 + SB1815 + RC222 + QT80 + owned learner test550 = 5/4917**, leaving83 lines contingency. This increases the test reservation and allows396 net POP growth without a sixth source. It is proposed bookkeeping for root, not an adopted task/metadata edit or permission to author now. Root must inspect the real final count before dispatch/review, including any source growth since these pins.

If implementation needs more, re-slice the same T15 producer/consumer work before exceeding the cap. For a genuinely fresh author/reviewer context, POP/RC/QT/owned learner test can consume this source-verified SB public handoff as prose, with SB mechanics remaining under its existing owner; POP3000+RC250+QT100+test700 would be4/4050. A worker/reviewer who has already opened SB still charges all1815 lines and cannot retroactively un-read it. A separate caller/config integration context must name every actual source/test and its ceilings. No source extraction/copy, renamed helper, uncounted fixture or programme expansion is proposed. Required acceptance survives either bounded arrangement.

## Prose/data identity inventory

Paths below are reference material, not implementation/test inventory. Some were searched/read only in relevant excerpts. Paths beginning `sdd/` abbreviate `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/`; `reviews/` abbreviates `docs/remediation/bac/package-reviews/`. No referenced source/probe implementation was followed.

| Reference | SHA256 |
|---|---|
| `AGENTS.md` | `184c48c8f99d106870802bd72d4e7fe79baad11ac72234fa47e9bb493c3b9238` |
| `CLAUDE.md` | `a65cd6db26d75dce767d1b23f83be01206f09905d2e40073d6767d67740db4a3` |
| `docs/remediation/STATUS.md` | `767608b88d3c0d81587055923fdd732c9708db703912d1ef03fc883bcd47db6d` |
| `docs/remediation/rereview-2026-10-31/BRIEF.md` | `dec8cfa495f5ddce25348e340c1c3e26d2fbab38138be9bcc0ecab655495d2bb` |
| Frozen plan | `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` |
| `sdd/tasks/task-T15.md` | `9b7f8e3144654f655921b48316e5f73c3a0f2652a2abe30b3522f87882c7417a` |
| `sdd/CURRENT-SESSION-CHECKOUT-RESTRICTION.md` | `44446fb6da2c90e352006b98bd379af9d6a264029dc87c7cfebe956d5c2e483d` |
| `sdd/wave07/X04-acceptance-overlay.json` | `bd1e028dd6df9ed2bbaad38cb93a9aa0adeffd28ba227e8441110c2d27b68d8c` |
| `sdd/wave07-preparation/MEAN-TD-TRIAGE.md` | `d4562d2cb241dff87e921e0a0c9540cb54832785a6dbf36c6ef8f1ee8fae8b76` |
| `sdd/wave08-preparation/T14-interface-proposal-r1.md` | `d6708084cb8bb63ba3febf8860b24a5f8b7a846da609c18ac2988aca35e77239` |
| `sdd/wave08/r1-common-source-binding.md` | `0771c9fe9e30e4600171547171f25a0644a5e841771aeae31874ec71d112349b` |
| `sdd/wave08-preparation/T14-HC-native-preparation.md` | `b3a5e3e238e25d9ece19dee987bbecd69599539dfbe42c0ecd8cb5b8518868d7` |
| `sdd/wave08-preparation/T14-native-independent-execution-r1.md` | `25fcb814c347d6732a20d8823c44b341da4b93af145d01bad857766010304dc1` |
| `sdd/wave08-preparation/T14-native-independent-review-r1.md` | `019e596df71db1fb371291981e16c937c3719a9819f47677d4ae6a92f5a0f26b` |
| `sdd/wave08-preparation/T14-owner-maintenance-independent-execution-r1.md` | `07756a35bcd559a43249f06ae4501f84dce85124881caf50885e1a7a14472fa8` |
| `sdd/wave08-preparation/T14-core-implementation-r0.md` | `914ab72aa4128b8d1ae85e137589a1fdac1cc807de53ee54ff0973874d5228c2` |
| `sdd/wave08-preparation/T14-existing-owner-maintenance-r1.md` | `e413de7484ac48484fb002ed31d6877f338b8bc6f516be579051860dd4351079` |
| `docs/remediation/bac/NATIVE-CURRENT-HANDOFF.md` | `77f6479d2df123f9508cb6a5ba1925a24a68d2058d0317b27384231a4507ccf8` |
| `docs/remediation/bac/P2-P8-INTERFACE-CLARIFICATION.md` | `548523c1c23c9901cf461ef33bc8ed74a705c43977772acf6817d1f1caed06b1` |
| `docs/remediation/bac/plan-reviews/execution-addendum-approved.md` | `5451e86b108b43e3c8f5fe0826ced7fc33a493d04ff7eb8a13063a16f2122cd0` |
| `reviews/T10-implementation.md` | `067feb35dfb87660d7863a575c80f35053e2ca54daf7b8781f6251480e8c36b1` |
| `reviews/T11-implementation.md` | `9c79533e65adc501fe3714d7cc29d1a56b8ccf7676afd17744f8f2c98ff2483c` |
| `reviews/T13-implementation.md` | `07c0b4901b600acf375758a19a9cacb72d019c0648246387e4d38bf7ee61aef7` |
| `reviews/T13-authored-reachability.md` | `d87871f80fc20c8ee6936dd9a83deb9b95a8793aa698b5feb750e60ef43f83ec` |
| `reviews/T10-population-owner-independent-review.md` | `063af1822488154311a45f2ca14beb6df5d9ea17d2686985e8b50e59ab70666d` |
| `reviews/T11-independent-review.md` | `cf88d21b87a53dcced008cdc8a4482b410fb28f3b22ad6fd2ce62c8202602b8e` |
| `reviews/T13-independent-review.md` | `ae44aa60413f65c03e1308f72abdbc5fd6d37c105acca0e06e3e051c4a9f082b` |
| `sdd/wave07-preparation/T13-interface-readiness.md` | `2b076c4bc1ba53183e37eb008ca8d21c6b748ca7a56a49b6cb535a718b649ca9` |
| `sdd/wave07-preparation/T13-public-learner-recipe.md` | `301ccdfee5ed7c7a5ee63b3089da3b301579d6d7227ba6eb4ab0173831399bd8` |
| `sdd/wave07-preparation/T13-preparation.md` | `dd3585c6db9331a4221c1e95a4c941f1d37adf5ba59af0152096d6d30374b088` |
| `sdd/wave05-preparation/T11-preparation.md` | `8ae4aa002793c03e32c9e5889be9b5668a00652d21ae8a206f8b3f9f0e93c303` |
| `sdd/wave04-preparation/T10-phase1-brief.md` | `839e3281c414dc6d924eb7884e7a184b4dd7d683a66981a9fdd6d63025190503` |
| `sdd/wave04-preparation/T10-independent-review.md` | `03d2530fafbef363aed23d184838a49a6cc081f29ce38faee487777b964a27cf` |
| `sdd/wave04-preparation/T10-fixed-independent-review-r2.md` | `ad945837951b409b9016abb739785fee9ce6f89a0bf5086ce3cdd74a76015517` |
| `sdd/preflight.md` | `65a7ea8ef4b890154b798111342b090e22af521a913461adb62e089a465bc3ae` |

## Preparation verification and return state

Read-only source hashes/counts and HEAD were checked at entry and after inspection. T14's pre-existing nine staged paths remained the same; this worker performed no index mutation and makes no independent full-tree identity claim. The only intended write is this ignored file, covered by `.git/info/exclude` line7 `/.superpowers/`. The reserved learner test remains absent. Final post-write checks recheck the four hashes, frozen plan, HEAD, ignore status and tracked status; no project runtime is needed or authorized for this prose-only result.

No imports, pytest/collection, project runtime, external probes, compiler/linter/gate execution, source/test edits or metadata changes were performed. Source facts above are static inspection; predecessor results are explicitly attributed; future test rows are unexecuted. Returned stationary for root to resolve the concrete interfaces/budget and dispatch only after actual T14 qualification.
