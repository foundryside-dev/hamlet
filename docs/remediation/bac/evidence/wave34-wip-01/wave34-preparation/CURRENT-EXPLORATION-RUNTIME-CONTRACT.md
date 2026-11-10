# Current exploration runtime contract

Source-verified finite T18d runtime at candidate **tree** `157f141a03570f341e7f67e9a265c11277d56aa5`, based on published commit `47d82ee6c3d138256155c8593e70d0108f8ab877`. The runtime composes existing BANK and EPS producers; actual POP/runner and historical selected-current learned-state admission remain required integration work. Candidate tree identity is not a published commit URL. No runtime accompanied this documentation.

## Sources and qualification boundary

Exactly five implementation/test sources were owned in this runtime slice:

| Source | Whole lines / ceiling | SHA256 |
| --- | ---: | --- |
| [exploration_policy.py](../../../src/townlet/config/exploration_policy.py) |1279/1600|f83fc4e192f289a5741c1e6f40b0188285e495efd328a952ef172b7c3d365b99|
| [epsilon_greedy.py](../../../src/townlet/exploration/epsilon_greedy.py) |118/118|f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059|
| [historical_checkpoint.py](../../../src/townlet/training/historical_checkpoint.py) |675/675|74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4|
| [scoped_curiosity.py](../../../src/townlet/exploration/scoped_curiosity.py) |1284/1284|294ef0f8d9f11e74869567e21f2ca44b623fe1cd54ca5c3eb59819c80681a05f|
| [test_exploration_factory.py](../../../tests/test_townlet/regressions/bac/test_exploration_factory.py) |1226/1300|151742778748b41ef40af13df0b5fbd5ce87d825ef3e3d2a4365c2f2822f314f|

Actual5/4582; ceilings4977. CP/native-provider/ENV/POP/runner/old-helper bodies were not additional inspected sources. Their facts come from qualified public capsules and the [BANK](CURRENT-CURIOSITY-BANK-CONTRACT.md), [checkpoint](CURRENT-CURIOSITY-CHECKPOINT-CONTRACT.md) and [factory](CURRENT-BACKEND-FACTORY-CONTRACT.md) contracts. Root's source-equivalence receipt confirms CP1138/BANK1284/conversion-test1456/none-test233 remain unchanged from47. RP/new runtime test are this runtime component's implementation/test changes. The later repository-collection prerequisite also updates the separately reviewed existing curriculum unit consumer; that source is outside this five-file runtime inspection. The earlier CP+BANK+RP768+conversion-test4646 qualification is historical, not a claimed current combined5157-line inspection. Current parser/runtime qualification belongs to this separate4582-line slice.

## Construction and ownership

In `townlet.config.exploration_policy`, both `build_exploration(*, policy, descriptor, device, validate_accepted_episode, issuer_factory, report_allocation, validate_committed_batch, validate_parent_cadence) -> ExplorationRuntime` and the `ExplorationRuntime` constructor require all eight keyword inputs. RP1258/790 defer producer imports to construction/preparation to avoid the RP/BANK/PF cycle.

`policy` must be an actual ResolvedExplorationPolicy. The runtime owns a current reconstruction and delegates the six existing BANK inputs unchanged to one actual CuriosityBank. BANK owns descriptor/geometry/device/seed validation and eager selected provider construction. The runtime separately creates one live existing EPS selector through make_policy_selector using policy.epsilon_start/epsilon_decay/epsilon_end. Off-side restore candidates are separate temporary selectors, not another learning provider.

`issuer_factory(owner)` receives the actual BANK, whose returned issuer.owner must be that BANK. The real parent registers that same object as ENV curiosity owner. The facade is not a replacement authority token or issuer owner. Parent/global-cadence callbacks are explicit integration requirements; their presence does not mean actual POP/runner currently implements them.

All five families remain selected by authored policy: none, count_based, rnd, adaptive_rnd, icm. Explicit shared scope remains a coupled provider with vector_tick service; per_world uses independently owned exact-ID providers/local eligible service clocks. `legacy_shared_v1` remains a current seed-ownership label. It enables no old-format loader. RP297 derives the exact current policy field set from dataclasses.fields, reconstructs FieldRole/current invariants, and rejects incomplete/obsolete records. The old pre-scope recognizer, synthesis branch and projection are removed.

## Public operations and exact action tensor

All listed keywords are required. `None` is an explicit semantic input where supported, not an omitted default.

| Runtime API | Behavior/result |
| --- | --- |
| read-only `epsilon` | Locked global selector scalar; no provider observation |
| `epsilon_tensor(*, batch_size, device)` | Fresh owned float32 [N] filled from the current scalar; exact nonnegative integer N and selected device required |
| `select_actions(q_values, agent_states, action_masks)` | Existing EPS selection; action_masks is required, including explicit None |
| `begin_episode(*, accepted)` | Existing BANK activation receipt |
| `prepare_step_stamp(*, accepted, world_ids, active_on_entry, vector_tick)` | Existing real step stamp |
| `reward(*, context, stamp, accepted, update_stats)` | Existing owned CuriosityReward |
| `admit_and_service(*, context, stamp, accepted)` | Existing service receipts |
| `prepare_completion(*, accepted, boundary_key, completion_content, outcomes, participated_world_ids)` | Existing actual PreparedBankCompletion |
| `commit_completion(*, prepared)` | Existing genuine dispositions receipt and exact-handle retry |
| `prepare_empty_episode_evidence(*, accepted)` | Existing genuine empty evidence |
| `quarantine_episode(*, accepted, reason)` | Existing BANK authentication/quarantine rules |
| `snapshot_world(*, world_id)` | Owned BANK diagnostic dict with string keys; advances BANK observer revision |
| `commit_batch_episode(*, batch_episode, outcomes)` | Separately authenticated parent-global epsilon transition; None |
| `checkpoint_state()` | Owned current runtime envelope |
| `prepare_restore(*, state, mode, accepted, parent_restore, validate_parent_restore)` | Ordinary same-policy/scope prepared runtime handle |
| `prepare_private_initialization(*, state, initialization, parent_restore, validate_parent_restore)` | Separate explicit source-runtime scope initialization handle |
| `install_restore(*, prepared)` | Publish one prepared runtime; None |

RP864 requires a real BatchedAgentState; finite floating dense Q [N,A] with selected action width/device; selected observation [N,D] and all row tensors [N] on that device. Optional masks must be dense bool [N,A], same device, with at least one legal action in every presented row. The parent supplies its eligible-row view; runtime does not invent inactive-row selection.

EPS43 consumes `agent_states.epsilons`, not its scalar attribute. Runtime therefore builds a short-lived real BatchedAgentState using the parent's other references/info and a fresh owned float32 current-schedule epsilon tensor, without changing parent slots or tensors. It calls the existing EPS and checks int64 [N] result/device/action bounds. Parent epsilon values do not determine the new view's schedule. Empty input returns an empty int64 tensor without action RNG draws. Nonempty selection invalidates prepared runtime handles even if result validation fails, since ambient action RNG may have advanced. Runtime state does not serialize that process-global action RNG.

Reward/service/completion delegate unchanged. Adaptive raw novelty remains unweighted; its scale is actual current provider weight. Count/RND/ICM eligible scale is the selected initial weight. None raw, selected scale and contribution are0 in both scopes, including caches/retries; inactive raw/scales are0. The facade returns raw and runtime scale separately and does not multiply DAC weights/modifiers or replay rewards. Actual canonical ENV/RWC/DAC composition, scale-once integration and original T18e remain required owner work.

## Separate parent-global cadence

BANK completion authenticates actual accepted world episodes/participants and owns adaptive survival-history/weight updates. It never advances the global selector. Parent-global rollout batch identity is a different domain: no equality to BANK accepted.batch_episode/world roster, no one-to-one completion mapping and no added next-begin gate is inferred. Several BANK episodes may occur before a global commit; a global commit may coexist with BANK live work. Parent must order global commitment relative to its next action selection.

`validate_committed_batch(*, batch_episode, outcomes) -> None` must authenticate the complete parent-committed batch, including its own missing-lane/empty-batch policy. Runtime requires an exact nonnegative integer key and a tuple of actual LaneOutcome records, matching integer event batch keys and unique nonnegative lane indices. It reports ownership, owns outcomes and full canonical `(payload.hex(), fingerprint)` content, and passes a separate owned view to the callback. Exact None return, unchanged canonical view and unchanged runtime/BANK revision are required.

The latest exact key/full-content retry is authenticated and returns without another decay. Changed content at that key and older keys refuse. New keys must increase but need not be consecutive. One successful new commit records `before` and `after=max(policy.epsilon_end, before*policy.epsilon_decay)` and changes the global selector once. BANK counters/ticks/provider diagnostic epsilon never substitute for parent commitment.

`validate_parent_cadence(*, cadence, mode, accepted, parent_restore) -> None` separately authenticates retained global cadence against actual parent state during restore/initialization. Its owned view is checked before and after BANK preparation and immediately before install. Required None return, unchanged view and freshness apply. The callback may use its closure-bound real parent state for live mode; a dict or HC envelope is not authenticated parent preparation. The current tests use explicitly cooperative parent callbacks plus genuine ENV authorities, not actual POP/runner cadence implementation.

## Current transport, preparation and publication

Exact runtime top-level keys are `schema, policy, bank, selector, cadence`, schema `exploration-runtime-state-v1`. `policy` is the complete current portable resolved policy; it must reconstruct/roundtrip exactly and ordinarily equal the receiving complete policy, including inactive authoring. `bank` is unchanged complete `curiosity-bank-state-v2`; its nested policy must agree. Execution hash equality alone is insufficient.

`selector` has exactly `epsilon, epsilon_decay, epsilon_min`: finite non-bool numerics, policy.end<=epsilon<=policy.start, and exact policy decay/minimum. `cadence` has exactly `schema, last_committed`, schema `parent-global-epsilon-cadence-v1`. The last record is None or exactly `batch_episode, completion_content, epsilon_before, epsilon_after`. Canonical content is a tuple of nonempty string pairs; payload hex must be canonical. No-record requires initial epsilon. A record requires a nonnegative exact integer key, policy-bounded finite before/after, exact last recurrence and selector epsilon equal to after. Full historical execution is not attested by this last-transition witness; parent authentication remains necessary. The cadence record is independent of BANK phase/completion and transports no capability.

The runtime reports its extra outer tensor ownership before copying the input, then rechecks owned policy/schema/selector/cadence metadata after the allocation callback. Existing CP owned/same/tensor_bytes utilities preserve native transport; RP introduces no native model/optimizer/gradient/tail/RNG/origin decoder. BANK performs native preparation and its existing allocation/parent/accepted checks. Additional parent-commit reports account for two owned outcome tensor views. Canonical metadata/Python objects/callback retention remain declared costs/unknowns; these reports are not total process memory bounds.

Receiving authority rules remain BANK's actual rules:

| Mode | Explicit inputs |
| --- | --- |
| initial | accepted=None; None/None BANK parent pair or genuine INITIAL parent preparation/callback |
| live_episode | actual authenticated receiving accepted token; parent_restore=None and validate_parent_restore=None |
| completed_boundary | accepted=None and genuine retained completed parent preparation/validator |
| private_initialized | accepted=None and genuine parent preparation correlated against archived source history |

The separate validate_parent_cadence callback is always required and called even when BANK's parent pair is explicitly None. Ordinary restore never guesses conversion. BANK/ENV installation order and actual whole-parent all-child publication remain external.

`PreparedExplorationRestore` is an identity-only handle; publication data stays in the receiver registry. Preparation retains the real opaque BANK handle and preallocates an EPS candidate, owned cadence, final tuple, next runtime revision and empty handle registry. Type/registered identity/destination/runtime-and-BANK revision/single-use custody reject foreign, copied, stale and consumed handles. Successful BANK mutations/observers invalidate facade preparations; direct BANK revision changes are also checked at installation. Export/snapshot is not a neutral freshness probe.

Every public operation except harmless scalar epsilon read holds RLock and an operation-active guard. Reentry raises `RuntimeError('reentrant runtime operation')` before ownership/allocation/callback/child/RNG work. Private composition runs under the held guard. The guard spans opaque BANK.install_restore, including its internal final accepted-token validator; RLock alone would permit that same-thread reentry. Propagated guard refusal prevents either child publication and permits healthy retry. A validator catching that refused operation and otherwise returning normally may permit coherent installation.

Before publication the runtime checks its handle/freshness and parent cadence; BANK then performs its own final checks/install. After successful BANK publication there are only preallocated selector/cadence/revision/registry assignments and simple guard cleanup. No callback, loader, validation, allocation or repair follows publication. Expected off-side refusal preserves unchanged live destination state. Existing unexpected BANK failures/quarantine remain its producer contract; arbitrary callback/direct-owner mutation is not rolled back. Trusted-parent quiescence over retained direct BANK references and unrelated RNG users remains required.

## Explicit initialization and historical data

`prepare_private_initialization` accepts a complete current **source runtime envelope**, with exactly `fresh_private` or `clone_learned_archive_pending`. Source current policy and nested BANK policy agree; source/target epsilon schedules must match. Actual BANK owns selected-behavior/geometry/seed/membership/source-boundary checks and requires an untouched private receiver. Source must be ordinary shared INITIAL or committed completed state, not a live or implicit mismatch conversion.

Both choices preserve source global selector/cadence. Fresh/clone concern private curiosity ownership, not restarting global exploration. BANK retains complete independently owned source archive, origin, epoch, truthful episode baseline and inherited/future-local counters; it uses actual fresh or cloned learned state with the specified emptied local tail. Resulting mode is initial for an initial source, otherwise private_initialized. Genuine parent/cadence correlation and ordinary prepared install custody apply. Parent history never becomes fabricated private completion authority.

[Approved historical A](HISTORICAL-REPLAY-DECISION.md) preserves actual old artifacts/provider provenance, recorded rewards and public archive query/export; current captured replay is not discarded. HC available learned payload remains data. Actual old Adaptive root lives under available population_state.exploration_state and its RND learned subtree under rnd_state; existence is not admission authority. No old runtime loader/projector, missing-tail/RNG fabrication, native fallback or POP6/HC7 version bridge is implemented here. Matching selected-current learned-subtree admission and incompatible/full-source preservation remain mandatory later owner implementation.

## Evidence and remaining gates

The approved execution addendum requires an earlier repository gate for removal of the obsolete policy loader. Initial full collection stopped at an obsolete `PerformanceTracker` import in the old curriculum unit tests, before any test case executed. The current consumer migration subsequently collected52 cases and passed227 consumer/event regressions; independent repair review approved the causal low-survival and configured-threshold controls. Full repository collection now passes8547 selected cases, with one default perf deselection. Full repository execution remains owed. The compiler CLI check passed34 packs with all35 process source/import/thread identities verified against the current candidate; final integrated/default/CI qualification remains open.

Root's final coherent collection1126 PASS4.0382s and actual1123PASS/3 unavailable-CUDA skips206.1946s (pytest202.46s) bind candidate tree157f141a and these frozen source hashes; actual child/verifier exited0. Custody356source/573config/13protected artifacts/4pytest/current-index/import/thread/14registry MAIN1 PASS; all packet runtime is closed. Independent final component review SHA294047cb14afa35d1833781f2e0470d846de892c9622b335ab536ae514d17396 reports renewed source/design SPEC/QUALITY APPROVED, zero open findings and actual independent150 PASS,77.57s pytest/83.6671s locked-job wall, child/verifier exit0 and custody PASS. Root's earlier current collection150 PASS3.8355s, prerequisite17 PASS21.3683s and focused39 PASS21.0393s are overlapping gates, not additive totals. Four cheap global guards pass/default601 (Black57.5361s); global mypy retains exactly nine preexisting oracle/POP errors and zero RP errors, so whole-repository mypy is not green. This qualifies the finite current runtime component as bounded work in progress toward original T18d, not parent/historical/runner or BAC completion. No current remote CI result is inferred.

CPU component evidence exercises genuine learning/Adam/gradients/tails/Count/history/RNG/storage, exact post-decay/restored EPS tensors, separate cadence, real ENV accepted/completed preparation, current runtime continuation, explicit initialization, refusal/healthy retry and final-validator non-reentry. Ten actual A-only adaptive episodes demonstrate strict actual weight decrease with positive ENV survival evidence, immediate exact completion retry, next reward scale and real subsequent optimizer update; shared remains coupled and private B remains unchanged. Protected historical native artifacts and captured replay are tested at honest archive/current-component boundaries, without fake historical native validation.

Actual parent callbacks/prepared publication, POP/runner rollout/selection/cadence/save-load and global action RNG, POP6/HC7 consistency, historical selected-current admission, canonical ENV/RWC/DAC/T18e, replay sampling/readiness/learning and T26 remain required and unimplemented integrations. Full parent native continuation, final54requirements/22lenses, full/default suite/coverage>=70/slow/applicable hardware/CLI/learning/CI and original28/66 release count remain open. K01's existing exact stochastic/mid-episode simulator qualification scope is unchanged. No whole T18d/BAC release, actual-parent closure or successful current remote CI follows from this component.
