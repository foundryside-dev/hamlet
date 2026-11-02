# T15 finite interface proposal — for one technical review

This proposes the concrete interfaces for the already accepted T15. It is **not implementation dispatch, user approval, executable acceptance or predecessor release**. Only this ignored prose is written. Original `T15-preparation.md` remains byte-identical at `b0b132a2dd69cc147d43a8566c3f14a4f72921a08ed428e045bdf5a332417ca1`.

Read identity was HEAD `01f2f64f42c2932177729607b337419355cb2720`, frozen candidate tree `324438ad58d9d5a85bba54e18be1ee225ada5969`. Root subsequently reports an explicitly approved email-only rewrite of32 unpublished commits, preserving source trees/index/all14 worktrees, to HEAD `bb7cf5f9a545fab0f5b4ecfcc042571e44c34cdd`; the external mapping is `/workspace/git-backups/email-only-rewrite.json`. Original receipts retain their true original identities. This worker did not inspect or perform the rewrite or push.

Root reports the T14 R1 full run actually closed **1 failed, 6622 passed, 16 skipped**, with its one stale sequential7 policy expectation routed to a bounded owner repair. T14 is therefore not full-qualified; its owner is now repairing that expectation. No T15 source/runtime work starts from this proposal. Publication authority and the approved identity remedy are unrelated to this technical preparation.

The plan hash remains `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`. The finite programme remains66 tasks/54 effective requirements/22 final lenses, with43 remaining as supplied by root. T15/X04 is mandatory before T15 release/G2. No capability removal/degradation/consolidation, historical exception, task/lens expansion or new user design permission is proposed. Existing preservation/History A/owner rulings govern; no durable rule or user-only fallback was adopted, and the failed rule grants/restricts nothing.

## Evidence and fresh-author boundary

This proposal writer remains exactly the original **four complete implementation files/3971 lines**, with no new implementation/test/helper inspection:

| Source | Lines | Unchanged SHA256 |
|---|---:|---|
| POP `src/townlet/population/vectorized.py` | 1854 | `38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b` |
| RC `src/townlet/training/replay_contract.py` | 222 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| QT `src/townlet/training/q_targets.py` | 80 | `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f` |
| SB `src/townlet/training/sequential_replay_buffer.py` | 1815 | `f958b1ed79bab5a37422353a04a9d78c05969950dfbf994436b4e1ce0e73392c` |

Read the following completed source-verified reports as **prose**, without following their implementation links. Their source inventories are their owners' inventories, not added sources for this writer:

| Report under `wave09-preparation/` | SHA256 |
|---|---|
| `T15-config-contracts.md` | `bdb2ec0a5ec1fe9f97845e6fadf978940781e2854206b71480d97b10d0329417` |
| `T15-flat-contracts.md` | `7b82cb51be4680f3fec91338962ae4da2590bf5357a1ebcbaa0407b4dec1181b` |
| `T15-provider-contracts.md` | `bb5760e1ee1f6d681115ed4b353d073def796b5d8c279ca42d1cc1997284a71f` |

Additional bounded prose: `/workspace/bac-review-2026-11-01/B03.md`, hash `87179b7caf96ec7c8376def705a01ce184643d8577f1f2de7cef576fff071f98`; `docs/remediation/bac/options.md`, hash `f36b745b34f8a1a22cfa8a96affa103935030a299c0edb9f30e907aea6f2ef5b`; relevant T03 report/T16 task passages. B03's source/probe/test links were not opened. The prior preparation's complete guidance/reference receipt remains applicable. The brainstorming skill was read for the technical choices below; root explicitly requested this finite proposal, selected its caller seed/successor/metric direction and prohibited new approval loops or implementation.

Root selects a genuinely **fresh** later author/reviewer context excluding SB source and consuming the already source-verified SB handoff in `T15-preparation.md` and this proposal. Proposed complete future ceilings:

| Future source role | Ceiling |
|---|---:|
| POP | 3000 |
| RC | 250 |
| QT | 100 |
| OP `src/townlet/config/bac_options.py` | 600 |
| Owned `tests/test_townlet/regressions/bac/test_learner_legality.py` | 1000 |
| **Total** | **5 files/4950 lines** |

Arithmetic is correct, leaving50 lines below hard5/5000. Current source sizes attributed by the config receipt give POP1854+RC222+QT80+OP294=2450; with the full1000 test reservation this is3450, leaving1550 actual growth before5000. The projected producer ceilings allow1500 of that growth. The owned test remains absent. A worker who already read SB cannot adopt this smaller inventory retroactively; this proposal writer does not acquire OP as an uncounted fifth source. Recount at actual later dispatch and final review; preserve every accepted control instead of forcing it into the stale350 reservation.

## Selected public construction seam — Q1 and Q2

**Technical proposal:** add one explicit public `VectorizedPopulation.for_training(...)` classmethod in POP, backed by one in-file common initializer. Keep the existing public `__init__` signature callable, all low-level buffer constructors/adapters, the five effective-brain overrides and legacy RNG roles. Do not add implicit default arguments, duplicate the whole population constructor, mutate a brain to bypass recurrent-PER refusal, or attach a replacement replay buffer after constructing a differently configured brain.

The new classmethod takes the current population construction inputs as required keyword arguments, including explicitly supplied `tb_logger`, nullable episode-limit inputs, and these required qualified inputs:

```text
replay_options: ReplayOptions
min_transitions: int
replay_rng: numpy.random.Generator
replay_origin: str
beta_vector_tick_horizon: int
beta_horizon_origin: str
current_vector_tick: int
```

Every argument is supplied even when a selected non-PER route records an inactive value. All six replay leaves must be fully resolved and schema-validated, min_transitions is a nonnegative exact int, horizon a positive exact int, and tick a nonnegative exact int in the accepted backend domain. Initial fresh tick is explicitly0. Preserve the passed effective brain and derive neither additional brain overrides nor architecture geometry in this factory. It owns copies of resolved policy/provenance; callers cannot mutate the runtime policy through aliases.

Factor POP's existing initialization into one in-file initializer receiving an explicit private setup record/discriminant, with no new default-valued parameter. The public constructor and classmethod both call it; the classmethod can allocate the real class instance and call that initializer directly. All actual network/target/optimizer/exploration/environment initialization remains common. The selected prioritized recurrent brain constructs the selected SB factory inside this path, with no temporary non-PER brain/configuration and no manual test attachment. Remove the old refusal only when this working route is wired.

The existing constructor remains a named compiled-environment adapter rather than acquiring undocumented local replay defaults. The actual public training path is `env.level.training`: B03's admitted warmup witness reads its min_size, and the config receipt verifies that the complete training object carries the declared seed/options/caps. Public options documentation supplies the exact resolution call `resolve_bac_options(training.bac_options, training=training)`. Use that central versioned resolver and the actual min_size; do not substitute batch size or16. This preserves direct constructor callers without requiring a new positional argument. Preserve the constructor's existing passed-brain role; T16 forwards the canonical effective brain explicitly.

For constructor-only successive flat PER, preserve its existing external-global-NumPy sampler role; qualified `sample_batch` already supports that legacy ownership. The new explicit classmethod always uses the supplied owned Generator. An explicitly selected replacement mode or newly enabled recurrent PER uses the explicit owned policy below. Uniform flat remains torch-uniform without replacement; recurrent uniform retains its selected Python-random adapter. No global RNG is reseeded by POP, no low-level constructor/sample/update signature is removed, and no opaque global state is relabeled private.

**Caller-owned RNG policy selected by root:** construct a separate `np.random.Generator(np.random.PCG64(resolved_training.seed))`, pass it explicitly, and set `replay_origin='authored'`. This is a narrow reproducible replay stream policy using the authored training seed, not a curiosity KDF, world-isolated RNG, hidden evidence seed or implicit `default_rng()`. The buffer clones/owns that Generator. Its object is separate from global NumPy and curiosity state even though its integer seed is the same training seed. Do not call `seed_all`, consume/copy a curiosity stream or invent a world/provider/component identity to produce it.

`authored` denotes the explicit caller sampler configuration/seed policy here. Actual per-leaf option omission origins still remain `bac-options-v1` or authored in the effective configuration/provenance; the buffer's single allowed origin string must not overwrite those field roles. Record the replay seed-policy description and beta-horizon derivation at the caller/POP receipt boundary, without pretending OP currently defines RNG/horizon authoring fields.

Use the permitted upper-bound horizon `max_episodes * max_steps_per_episode` only from two explicit resolved limits. In the runner, the executed max_episodes is its recorded launch override when supplied, otherwise the declared effective training limit; preserve which source supplied it. The per-episode cap is its explicit loop declaration. Record `beta_horizon_origin` as the named derivation with these sources; it is a vector-tick upper bound, not realized eligible transitions or a promise to reach beta1 after early endings. If either input is unavailable, the qualified caller supplies the explicit positive horizon argument; no constant, N multiplier or transition-budget substitution is invented. A direct constructor adapter uses the actual declared compiled limits/explicit existing overrides, not a hidden numeric fallback. Existing lower-level use lacking compiled training remains a compatibility case that must be preserved by actual affected-consumer tests, not silently refused or guessed into full authored qualification.

T15 tests call this real classmethod with actual resolved options/min_size/effective brain and the explicit Generator/horizon/tick. T16 later replaces RR465–481's ordinary call with this public path, forwarding `effective_run.options.replay`, `effective_run.training.replay_buffer.min_size`, canonical `effective_run.effective_brain` and the explicit caller policy above. RR already stores the effective view; no absent `env.effective_run` property is claimed. T15's immediate public proof and T16's ordinary-runner propagation remain separate evidence.

## Actual replay dispatch and clock seam — Q3

Construct flat RB with its existing `(capacity,device)`; construct PB with its existing `(capacity,alpha,beta,beta_annealing,device)` and, on the owned qualified route, call actual `configure_sampling(*,sampling_mode,rng,origin)`. **There is no flat `for_sampling` factory.** PB accepts configured owned origin only `authored`/`bac-options-v1`. Preserve the external-global physical sample/update pair as its separate public role.

Both flat classes accept exactly:

```text
push_recorded(observations, actions, rewards: RewardTensor,
              next_observations, dones, next_action_masks)
```

There is no flat legality_recorded keyword. First nonempty insertion establishes A from actual successor-mask width and marks inserted bits recorded. Supply `RewardTensor.from_dac` exactly as current POP does; canonical totals/components remain unchanged. If eligible K exceeds capacity, submit successive bounded chunks of the same eligible row order so each insertion respects the backend K<=capacity domain; do not drop eligible rows from accounting or claim all were retained. Do not declare an unconstrained action width as a production-mask substitute.

SB construction is exactly its verified `for_replay(capacity,device,*,options,action_dim,legality_mode='captured')`, or `for_prioritized_replay` adding all explicit alpha/beta/annealing/horizon/tick/Generator/origin inputs. The two-argument SB/public legacy dictionary APIs remain available independently. Its priorities identify actual per-L zero-start contexts, not episode count or physical positions.

| Learner family | Exact request translation |
|---|---|
| Flat uniform | B, L=1, actual min_transitions, sampling_mode=`uniform_without_replacement`, sequence_mode=`feedforward`, objective=`transition` |
| Flat PER | B, L=1, actual min_transitions, selected PER sampling mode, sequence_mode=`feedforward`, objective=`transition` |
| Recurrent uniform/PER | B, selected L, actual min_transitions, selected options.sampling_mode/sequence_mode/sequence_objective; SB selects the separately persisted uniform adapter when non-PER |

On a scheduled opportunity call readiness, then sample_batch only if ready. Sampleability and retained occupancy are separate. Retain fixed-full impossibility/window diagnostics, adaptive real short prefixes, successive B>N refusal and replacement B>N availability. Emit diagnostics on changed reason/counts, not every tick. Pending live episode lists are not retained replay; do not repeatedly store a growing episode as duplicated new episodes. Capture/commit a complete exact eligible fragment once through SB `store_captured_episode(...,next_action_masks=...,legality_recorded=...)`. Preserve the current terminal/flush lifecycle; name any commit-before-gate reordering and test it, rather than quietly counting uncommitted rows.

After each actual vector step advance POP total_steps exactly once, and pace PER **before** any scheduled sample, including warmup/skipped/unscheduled opportunities. Recurrent calls `set_vector_tick(total_steps)`. Flat calls its actual `anneal_beta(horizon,total_steps)`. PB has no monotonic setter, persisted horizon or stored current tick; POP owns the qualified last-paced-tick/horizon provenance and prevents ordinary rewind. Sampling/readiness/priority updates do not pace beta. No method is invented on PB and no batch argument is added to the SB clock.

`training_step_counter`, scheduler.step and target synchronization advance only after a successful optimizer step. Unavailable samples do not update these, consume sampler RNG or clear rollout hidden. Online enters train and target eval for updates. B1 uses squeeze(-1). Flat PER feedback is `update_unit_priorities(owned CPU ndarray[int64] batch.unit_ids, detached residuals[B])`; SB feedback is `update_priorities(batch.unit_ids, detached residuals[B,W], loss_mask=batch.loss_mask)`. No receipt position/physical index is passed as a stable handle, no epsilon is pre-added, and no sampler/reducer mathematics is duplicated in POP.

## Truthful eligible provider composition — Q4

Choose the existing-provider **filter/select/scatter** composition inside POP, with an in-file aligned-state constructor using the already-called BatchedAgentState fields. It preserves the actual public provider selector rather than assuming an absent provider-level eligible method:

1. Use the actual entry eligibility saved before action selection. Validate bool[N] membership and full-N bool[N,A] mask geometry; diagnose eligible live-empty masks before provider RNG. Empty masks never determine membership.
2. Initialize full-N transport actions with unmasked argmax. If no row is eligible, skip the selector entirely.
3. Slice Q/masks and all existing temporary agent-state tensors consistently to actual eligible rows. Preserve the exact supplied per-row epsilons. Pass truthful active dones in the selection view, not the original fabricated full-N all-false temporary dones as the membership source. The existing full-N temporary curriculum DTO can retain its current separate purpose.
4. Call the actual provider `select_actions` once on that aligned subset and scatter its returned actions. Do not call both the strict sampler and provider sampler. The active policy retains its candidate/epsilon draws, including epsilon0; inactive slots make no selection draw.

The combined receipts establish plain epsilon's body, RND's epsilon helper, adaptive delegation and count/ICM's unoverridden inheritance. Thus all five current supported providers read the aligned state epsilons for this action math. No uninspected full-N facade or future private bank is claimed implemented. Public selector signatures remain callable. The production and public population selection routes use actual eligibility consistently; retain the legacy low-level helper's transport role.

Selection remains separate from canonical reward invocation, predictor admission/service, count admission, adaptive completion, snapshots and epsilon decay. Keep terminal-causing eligible transitions once. Preserve eligible predecessor RND admission and independent shared backlog servicing, canonical successor reward and count admission, ICM's actual full-transition route where owned by its existing supplier, and exactly-once adaptive lane completion. T15's action adapter does not remove pending service on an eligible-empty shared tick or fabricate private idle service. RND takes a predecessor tensor+vector_tick; ICM/count take actual context, not a generic observations update. Existing shared/private supplier obligations and PW03/PW04 remain separate; this proposal neither implements their bank nor treats action filtering as S1 isolation proof.

## Exact stored successor under each real prefix — Q5

Root selects **no adjacency assumption**. Group sampled windows by real lengths, zero-start both networks per group, and advance their current-observation prefixes one real step at a time. The existing network's `[B,1,D]` call and `(h,c)` return are already used by POP rollout; no new network API or implementation read is needed.

For each real t in a same-length group:

- Advance online with actual `observations[:,t:t+1]` and its carried online prefix hidden; gather q_pred for the stored action. Keep this current-prefix graph connected across t for BPTT.
- Under no-grad, advance target with that current observation and its own carried target hidden.
- Under no-grad, branch from each network's **after-current-prefix** hidden to the exact stored `next_observations[:,t]`. Double uses the online branch for selection and target branch for evaluation; vanilla needs only the target branch. Detach the online branch input hidden so bootstrap is not a gradient path. Discard bootstrap-returned hidden; it must not advance either current prefix.
- Pass these actual successor Q values and the same row's recorded successor mask/reward/done to QT. There is no interior t+1 substitution, shifted mask, final padded index, crossed hidden state or live-environment legality query.

This requires neither repeated independent prefix recomputation nor a third network/prefix helper. Stochastic train-mode calls may consume a different sequence of random draws than the old unmasked learner; no same-seeded bitwise old-update claim is made. Real grouped-step BPTT and each-network-own-hidden are executable obligations. Never run padding through a network, QT, loss, residual arithmetic or hidden update.

Build per-unit losses from the selected real objective rows. Window_mean averages selected real rows **within each unit**, then applies its returned detached float64 unit weight once and batch-means units. Anchor uses only the last real row for loss/priority while its preceding real observations remain context. Uniform legacy windows can have nonunit correction weights. No global padded/real-row denominator, coverage-count shortcut, second timestep weighting, sample-max normalization or recomputed marginal estimator is permitted. SB owns canonical masks, max/mean reducers, duplicate maximum and eviction-safe handles.

**X04 diagnostic is independent:** for all sampled real recurrent rows, and all sampled flat rows, cast both detached prediction/target operands to float64 before subtraction/absolute-value accumulation/reduction. Select real rows before arithmetic; do not multiply arbitrary padded junk by zero. Return their unweighted arithmetic mean as the existing Python scalar `td_error`, independent of anchor loss selection and IS weights. Preserve repeated sampled rows as sampled observations. Do not clip, zero, omit, reject the admitted reward or change loss/gradient/priority objectives as the metric remedy.

Keep the admitted two-residual~2e38 witness, finite true mean, flat uniform/PER two real finite Huber/Adam updates and recurrent valid-row numerical controls, B1/modest unequal/unequal-length/padded-junk/nonuniform-weight controls. Compare to an independent pre-update float64 oracle, relative tolerance2e-6 for the admitted case. This repairs existing telemetry; it proves neither optimizer divergence nor downstream crash, and no recurrent authored incident is retroactively asserted. T35 consumes the verified producer receipt.

## History and restore boundary — Q6

Use actual storage prepare/validate/materialize/load methods and existing raw POP6 load; do not invent a population prepare/inference API or native10/7 identity. Exercise genuine supported old standalone uniform4/PER4/sequential5, current captured rows and archives via the public storage producers/accepted DATA. POP6 may carry these replay payloads through its actual validator/materializer, with truthful source/native geometry. A labelled storage import/attachment control is distinct from the naturally selected factory learning proof.

Old maskless history remains archive/query/export with original tensors/rewards/provenance and active0. Restore available learned cumulative counters/network/optimizer/scheduler state; archive rows cannot count toward warmup, selected handles or any learning clock. New captured rows eventually produce legal target3 and actual optimizer change. Current captured5/6/7 replay adapters preserve active qualified rows; no fresh0 merely because stable IDs or new PER state were absent. Preserve genuine uniform6→prioritized7 active adaptation with explicit target configuration/Generator/horizon/restored tick and no initial L domains.

For raw current replay7, preserve its actual saved owned RNG/beta/domain state and cross-check the caller's restored total_steps before subsequent pacing; do not rerun configure_sampling or reseed after restore. For flat current PB, preserve saved beta/private sampler through load, then pace the next actual vector tick with the caller's explicit horizon. For captured6→new recurrent PER, the explicit factory target is prepared at the known restored native tick, since6 has no tick/PER state from which SB can infer it. Do not mutate a live target's tick before fallible loading just to make the adapter work.

PB does **not** persist a monotonic clock/horizon, and raw POP6 has no newly invented qualified policy envelope. Therefore T15's runtime clock/horizon guard and supplied matching restore configuration do not establish complete persisted native configuration/continuation. T24/T25 still own the full native10/7 envelope, immutable replay configuration reconciliation, outer archives/accounting, preparation/resource/RNG atomicity and current learned-fresh-episode guarantees. Actual T15-caused current consumer failures must be repaired immediately; those later owners are not a waiver. No existing producer schema is silently retagged or widened here.

## Exact retained B03 gates and finite acceptance — Q7

The known B03 prose supplies the exact existing owner selection below. It is a historical command inventory, **not a current PASS**, and its scratch probes were not opened or executed. Later root runs from its exact current candidate with its established import/fixture/identity harness:

```text
uv run pytest --no-cov -p no:cacheprovider
  tests/test_townlet/unit/population
  tests/test_townlet/integration/test_authored_episode_lanes.py
  tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py
  tests/test_townlet/integration/test_recurrent_bptt_runtime.py
  tests/test_townlet/regressions/test_episode_lane_population.py
  tests/test_townlet/regressions/test_episode_lane_learning.py -q
```

The paths form one command after normal shell line continuation. Test implementations remain unopened. The owned causal command remains `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_learner_legality.py -q`.

All existing acceptance from the original preparation survives the expanded1000-line reservation: four-family×vanilla/Double×global/state-dependent target3/direction matrix; actual recurrent uniform/PER and both PER laws/objectives/reducers; true terminal0 versus cap bootstrap3; sixteen length2/L3 and capacity15 readiness; adaptive capacity1/L8 and fixed-full diagnostics; B1; no skipped optimizer/LR/target/rollout changes; exact per-row prefixes/own hidden/BPTT/padding; once-weighted per-window objective/stable updates; actual old archives/new warmup/current captured continuation; explicit train/eval; constructor/global-adapter preservation; and required finite X04. Do not omit a control merely because another bounded predecessor tested storage mechanics.

Meaningful causal RED observes the intended missing contract, then GREEN and affected replay/population/B03 consumers. Root owns exact candidate collection/import/fixture custody, bounded repair reviews, all six standing guards, the mandatory changed-public-contract/full G2 gate and actual result artifacts. Fresh other-model source/spec review precedes dependent release. Final repository/coverage≥70%/slow/applicable-hardware, same-SHA22 lenses/synthesis, finite T40 and exact-tip remote CI remain unchanged. No source-only proposal or focused predecessor count closes those gates.

## Finite alternatives and technical-review points

The selected factory/common initializer avoids both duplicating POP's constructor and weakening a prioritized recurrent brain merely to construct a non-PER object for later attachment. Reusing a curiosity KDF/stream would invent provider/world semantics; the explicit separate PCG64 training-seed policy avoids that unsupported claim. Shifting interior next-Q requires an unprovided adjacency guarantee; grouped real-step prefix branching uses exact recorded successors with existing public network calls.

There is **no source-proven blocker requiring a user capability decision**. The one Astra-medium review should assess these concrete technical choices, with any correction folded into this same finite proposal:

1. Constructor compatibility: central resolution from actual compiled training plus the named global successive compatibility role must preserve currently callable lower-level/owner cases. Do not introduce a blanket new refusal when a fixture/caller lacks the carrier; obtain its exact bounded supplier contract or preserve its explicit existing role. This is an immediate affected-consumer obligation, not permission to retain an unmasked optimizer branch or ignore an admitted min_size.
2. Provenance: the selected `authored` sampler-origin literal must coexist truthfully with option leaves derived from `bac-options-v1` and launch-adjusted horizon sources; no origin relabeling or absent persisted PB horizon claim.
3. Restore scope: supplied/derived matching horizon and captured6's explicit target tick are required inputs, not information encoded by PB6 or captured6. Native envelope guarantees remain open; no reseeding, live pre-load clock mutation or source-history clearing is justified.
4. Exact-prefix grouped-step evaluation must keep online hidden graph-connected, branch only detached bootstrap hidden, never advance with bootstrap/padding, and preserve target eval. The history-sensitive/BPTT controls must distinguish plausible incorrect implementations.
5. Provider filter/scatter must align the real selection DTO fields and preserve all demonstrated nonselection service/reward/completion work; no full-N old-selector call followed by masking and no double sampler call.

These are bounded review topics, not reopened Q1–Q7, new tasks, user permission questions or claimed implementation results. The technical review may reject an unsound mechanism without authorizing a capability reduction.

## Stationary return

No source/test/OP/helper, runtime/import/pytest/collection, index/metadata/tracker edit, branch/worktree/copy/deletion/subdelegation or commit was performed. The only new write is this ignored proposal. Final checks preserve original preparation hash, all four source pins and the frozen plan; read back the current HEAD and ignore rule. Root's source-frozen T14 owner repair and metadata-only identity mapping remain separately attributed. Return stationary for the finite technical review and later explicit authoring dispatch only after actual predecessor qualification.
