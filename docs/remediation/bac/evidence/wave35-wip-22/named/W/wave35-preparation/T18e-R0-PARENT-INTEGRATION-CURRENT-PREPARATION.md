# Parent integration: current source preparation and bounded APP split

2026-11-14. Preparation only, by `/root/bac_astra_parent_integration_prepare`.
No APP writer baton, implementation edit, test/import/application execution,
Git write, branch/worktree/checkout/copy, deletion, or subagent dispatch occurred.
This continues the accepted finite design; it does not restart high-level design.

## Authority, evidence and body budget

The preserved consumer proposal is SHA256
`ba6128eb2fa12df3cdf2fddad402e8c8a9a99ad36314776c80a75a3ae0d7eab6`;
peer review `f8abc8c88a7aa24f17a88bb4c3c45f0ce1504ed7be626d36fb565bd57a0099e6`
approves SPEC and QUALITY at design level. Adopted invocation FIX1 is
`e18de5be6abaa11c1e2ba14929a917ca547c2e41b349dd9102c2ea49cf55c723`.
The parent handoff and flat/PER alias capsules were consumed as supplied prose.
Their historical statements that outcome API implementation is pending are
superseded: current core1195 is qualified at R113/R116. Do not rebuild it.

Only one complete implementation body was read, after measurement:
`src/townlet/population/vectorized.py`, 3163 lines, SHA256
`6c4f7ca085f0a7db34f42bebe22f0240ed12825627c13bcffb3c0d3be3f99022`.
All line references below are to that body. Clock48 and test791 were measured
but NOT opened. Core/replay/ENV/runtime/network/runner bodies were NOT opened.
Current metadata-only measurements:

| Path | Lines | SHA256 |
| --- | ---: | --- |
| exploration/rng_custody.py | 1195 | 6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8 |
| training/replay_contract.py | 881 | 8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4 |
| training/replay_buffer.py | 816 | 683e0b9b0f500cc523391b8574acbfc31bf8dc8a36d92ad0547323621261838d |
| training/prioritized_replay_buffer.py | 1310 | 7a76183ded0712103c81ebd31b3e05425b3738e9338689cacfbefbc8fd493a29 |
| tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py | 791 | 6cea1235f8dc149aceb5ca7352b855ac001a8bfb1e758a9c3b116f3654f2acb0 |

Production paths in this table are relative to `src/townlet/`.
Fresh bounded supplier capsules now supplement this one-body POP inspection:
`T18e-R0-PARENT-REPLAY-CURRENT-SUPPLIER.md` SHA256
`f6c48b621acbc26f9198a8e25f71a6f25b29fc4697d8f3e7d0bf77a0154b7b37` (four source bodies4202;
current seals match the table) and
`T18e-R0-PARENT-ENV-RUNTIME-CURRENT-SUPPLIER.md` SHA256
`02ac16732bb18dd6613c09cf90f2b20850da402c355cd11604f000f3f91b5b33`
(ENV2889 + telemetry134 + exploration runtime1299 =4322/three).
These are source-qualified external contracts, not additional bodies read here.
The test hash matches the current POP fixture API capsule, so that callable
contract can be consumed without another body read. Old replay capsules carry
older hashes: their copy semantics are attributed supplier facts, not a claim
that this preparation freshly inspected current replay storage code.

Root R116 record reports 1001 unique CPU passes (89 existing core + 5 new core
+ 67 activation + 840 producer); included isolated children are not additive.
R115 replay54 remains separate. B/B6, parent/recurrent/runner integration and
hardware remain required. Global mypy's 9 missing POP lineage arguments and 6
oracle errors remain open. No check was rerun here, and no aggregate acceptance
is newly claimed. Current published WIP21 HEAD is root-supplied
`2f579092eae2b67eb3efd514aa7b61c909efa9f1`.

## Concrete entrypoint inventory and refusal requirements

Current POP has phase flags/revisions/opaque-handle registries but no process
RNG participant, threading lock, invocation outcome consumer or monotonic
completion-health field. `_require_operation_idle` (855) checks only local
phase flags. `_failed_step` is not an adequate completion-health replacement:
it is tied to existing body policies and is assigned False during restore.

| Existing public entrypoint(s) | Current gate/effects | Required integration treatment |
| --- | --- | --- |
| `__init__`, `for_training` (192,230) | Both reach `_initialize`; construction Q/target, optimizer, registry, replay, tensors, optional hidden, replay serialize | Own real construction admission and idle child registration; initialize real lock/health before exposed callbacks can run. Do not claim postconstruction enrollment protected initialization. |
| `reset(reservation, retired_world_ids)` (1108) | Idle/failed/pending checks; ENV reset, POP tensors/hidden/registry, initial-participation callbacks and activation | Guard whole real operation; preserve accepted-reset idempotence and existing reset quarantine; inspect outer receipt after local finally cleanup. |
| `prepare_empty_episode_evidence` (1250) | Idle/owned-state/ENV validation, creates authority | Refuse uncertainty before tensor checks or proof issuance. |
| `prepare_vector_step` (1353) | Idle then `_step_inspection`; clones/compares actual tensors and issues handle | Real exclusion and inventory before effects; public preparation is distinct from claim. |
| `claim_vector_step` (1384) | Only inspection reentry gate; ENV calls it during actual step; validates/clones, mutates participant roster/stage | Authenticated nested callback must reuse the same parent custody and lineage; an ordinary idle-only public decorator would break genuine ENV callback. |
| `bind_episode_worlds`, `begin_batch_episode` (1452,1471) | Idle/failed/pending checks plus tensor state checks and CPU publication | Refuse before effects under owner custody; preserve concrete roster/sequence requirements. |
| `commit_episode_outcomes` (1533) | Fingerprints/canonicalizes CPU/tensor DTOs; retained runtime retry; commits ledger/cadence | Whole commit consumer; keep retry custody and exact child return cut. |
| `validate_committed_batch`, `validate_parent_cadence` (1613,1619) | Runtime callbacks authenticate retained parent work/correlation; latter can call ENV | Nested validation contract, not unrelated standalone admission; no healthy attestation from uncertain parent. |
| `sync_exploration_metrics` (1908) | Idle/pending checks, creates device epsilon tensor, writes registry | Guard actual publication and registry child effects. |
| `flush_episode` (1981) | Idle/failed/pending, owned-state/ENV, completion DTO/recurrent store/hidden changes | Retain whole completion boundary and existing body quarantine. |
| `select_greedy_actions`, `select_epsilon_greedy_actions` (2013,2044) | `_begin_selection`; Q forward/hidden/display state, ENV masks, optional direct epsilon helper | Both are mutation/RNG-capable entrypoints, even greedy/no_grad. Retain lock beyond selection-frame finally. |
| `step_population` (2079) | Full ENV/replay/runtime/Q path; clears vector record and finally `_step_active` | Parent wrapper outside entire existing method; outer receipt is consumed even after record/flags clear. |
| `update_curriculum_tracker` (2431) | Idle/pending, external tracker update with caller reward/done tensors | Guard and inventory selected callback contract; do not silently remove tracker support. |
| `get_checkpoint`, `get_checkpoint_state` (2453,2473) | Child snapshots; latter Q/target/optimizer/scheduler and diagnostic failed-vector exception | Healthy export refuses uncertainty. Preserve existing failed-vector diagnostic capability explicitly; a diagnostic label must not allow uncertain model snapshots to masquerade as healthy recovery authority. |
| `prepare_checkpoint_state` (3040) | Idle/failed/fresh receiving ENV, deepcopy, child/candidate publication | Preserve real fresh-boundary rules, own candidate staging and truthful source devices; cannot register children inside an active lease. |
| `install_checkpoint_state` (3110) | Handle/revision/fresh ENV, runtime install then assignment suffix; clears flags/registries | Parent completion cut after suffix, monotonic uncertainty cannot be healed by existing `_failed_step=False`. |
| `validate_checkpoint_state`, `load_checkpoint_state` (3145,3149) | Delegate real prepare / prepare+install | Explicit supported nesting; held same lineage must preserve candidate currency across load's prepare/install. Validation currently issues a retained candidate, so is not a pure schema-only no-effect path. |
| `load_token_network_cross_universe` (3159) | Existing unconditional protocol refusal after token-native check | Preserve current capability status/refusal; no fake implementation or recovery route. |
| `completed_outcomes`, `clock_ledger` (1446,1439) | Owned event cloning / immutable clock reading | Healthy publication reads need custody/health policy; clock/event data alone is not current completion authority. |
| `build_telemetry_snapshot`, `get_training_metrics` (2413,2439) | Registry snapshots / scalar metric dict; no current idle gate | Classify explicitly as diagnostics or healthy snapshots. Diagnostics may expose retained failed-state values under exclusion, without promising a healthy live state. |
| `vector_step_progress`, `batch_commit_progress` (1274,1517) | Deepcopied portable failure/progress diagnostics | Keep available as diagnostics under safe owner reads; they never authenticate successful completion. |

Private helpers `_learn`, `_bind_training`, `_execute_population_step`, and
initial/reset/selection helpers must receive/reuse the owning scope rather than
open unrelated ambient calls. Raw public Q/target/optimizer/scheduler/replay
attributes remain exposed and cooperative; no proxy, hook ban, pointer detector,
or implicit raw-alias safety guarantee follows from guarded method coverage.

## Authentic call graph, boundary and currently missing lock facts

Source-established parent paths:

* Construction attaches runtime registry and `claim_vector_step` to ENV before
  building Q/target. Runtime callbacks are wired by the genuine fixture to
  `validate_committed_batch` and `validate_parent_cadence`.
* Step: POP -> owned-state ENV validations -> replay binding -> Q rollout ->
  curriculum -> ENV masks -> runtime selector -> prepared vector -> ENV.step
  -> ENV calls POP.claim -> returned handoff -> replay pushes -> runtime service
  -> vector/replay pacing -> sample -> Q/backward/optimizer -> later PER update
  -> ENV validations/finalization -> returned BatchedAgentState.
* Reset: POP -> ENV reset/prepare/commit initial participation -> POP paired
  publication -> ENV final reading validation -> activation return.
* Commit: POP -> runtime commit -> runtime invokes POP retained-batch validator.
* Restore: POP preparation -> runtime prepare -> runtime invokes POP cadence
  validator; install -> runtime install -> POP reference assignment suffix.

These are real reverse callbacks. They rule out assuming that acquisition order
equals lexical call order, or putting a nonreentrant public parent lock around
every method. There is NO established total order for POP/ENV/runtime/BANK in
current source. The fresh supplier resolves replay retention concretely:
`replay_cuda_preflight(*, owners: tuple[ReplayCustody, ...], anticipated_devices:
tuple[torch.device, ...]) -> Iterator[None]` already exists. It takes idle
`domain.admission(lineage=None)`, pins/deduplicates owners, resolves anticipated
and owner selectors BEFORE owner locking, acquires replay locks sorted by id,
inventories retained and prepared sources, enrolls replay unions and yields None
while retaining all locks/gate/pins. Singleton `owner.cuda_preflight` delegates.
It is NOT a lineage/inventory getter. Enter before POP lock or active invocation;
put POP invocation exit and unconditional outcome consumer inside this retained
scope. An outer idle public admission may first resolve/enroll POP's own sources;
replay preflight does not enroll POP. No parent copy of replay private inventory
is needed. Intended child calls reuse the held reentrant lock while their own
active lifecycle guard continues to reject unrelated reentry.

The fresh ENV/runtime supplier establishes an actual gap: ENV has NO mutex or
domain admission; its participation fence is synchronous only. Runtime's private
RLock is held across every decorated public operation, including BANK forwarding
and POP cadence/commit validators. Its public APIs accept/forward NO lineage and
expose NO retained custody scope. Its active flag rejects same-thread decorated
reentry; only epsilon reading is explicitly harmless. Attributed current BANK
admission is domain-before-BANK, so ordinary runtime has runtime-lock -> domain,
which cannot safely coexist with a new domain -> runtime parent path unchanged.
This needs a bounded runtime/ENV producer integration contract, with actual BANK
supplier facts, before parent activation. Do not simply acquire runtime._lock,
leave its active flag set across all children, or disable callback checks.

The remaining implementation dependency is exact: supplier must name BANK and
outer-runner locks and approved new ENV/runtime custody entry APIs, total order,
authenticated callback rules,
idle registration/device preflight, plan revalidation, and retained custody
through completion. POP then acquires that preflight set after common admission,
enters its own invocation inside the held owner stack, exits it, consumes its
sealed outcome in unconditional finally, performs assignment-only fail-closed
health transition, then releases child/parent locks and admission. No new lock,
CUDA call, user callback or ENV abandonment may occur in that failure consumer.
Existing body-error cleanup remains distinct and preserves original exceptions.

The current standalone step success cut is 2093-2105: state is constructed,
progress marked completed, `_vector_steps={}`, and state returned; finally
clears `_step_active`. Reset and selectors similarly clean up before outward
return. The NEW wrapper's healthy return must be after exit receipt inspection,
not conditional on any remaining record. A bound runner can itself be a larger
effect owner; its actual source/custody is unsupplied. Local POP success cannot
be promoted to proof of that later outer phase (accepted schedule9).

## Lineage migration: exact current call sites

There are nine omitted required replay `lineage` arguments in seven lines:

| Current line | Actual calls | Owning path / constraint |
| --- | --- | --- |
| 698 | `sequential.prepare_serialized(transport, expected_obs_dim=...)` and `sequential.load_prepared(...)` | `_bind_training` recurrent adaptation; create candidate at idle first, then same authentic operation for prepare/install. |
| 699 | `prepare_archived_import(buffer.historical_archives, expected_obs_dim=...)` and `load_prepared(...)` | Same adaptation; archive snapshot may be ordinary work, so order token issuance after snapshots. |
| 701,702 | `prepare_serialized(state, expected_obs_dim=...)`, `load_prepared(prepared)` | Same candidate path, no intervening ordinary operation. |
| 800 | `self.replay_buffer.sample_batch(request)` | `_learn`, after readiness; supply active POP operation, never None inside parent. |
| 3067 | `replay_target.materialize_validated(validated_replay)` | Parent restore staging. |
| 3070 | `replay_target.load_prepared(prepared_replay)` | Current source deepcopies replay target between materialization and load if it is the live replay (3068-3069). Fresh supplier confirms this is NOT an authority-transfer route: core participant/token deepcopy refuses, and a fresh destination cannot consume the original issuer's handle. Prepare on the actual offside destination registered at idle, then load its own handle under genuine shared lineage. |

Required explicit lineage does not belong on arbitrary owner-local push/readiness/
priority methods merely by analogy. Their current producer API must be followed.
Standalone parent calls use explicit None at their own admission boundary;
supported nested calls use actual yielded RNGOperation. Do not obtain lineage
from status, private active fields, copied handles or a thread-local guess.
`_bind_training` can create a fresh replay inside step today (694,706), and
checkpoint validation can create one (2985). Merely adding lineage keywords
does not repair active membership mutation. Preconstruct/revalidate genuine
offside owners at idle through the supplier-approved lifecycle contract.

Outcome API to consume is the existing required-argument
`domain.device_invocation(participant=..., operation_kind=..., lineage=...,
cuda_devices=...) -> RNGDeviceInvocation`; enter yields genuine RNGOperation;
`completion_failed()` is readable after an entered invocation exits, including
exceptional exit/poison, without new lock/CUDA access. Entry failure has no
outcome. Own phase False must not heal body failures; True monotonically marks
POP uncertain. Same-object error deduplication is why exception catches alone
are inadequate. Registration/enrollment remains idle-only; CPU inventory is ().

## Actual source/destination inventory and rejected prefixes

The following is concrete POP reachability, NOT a claim that generic reflection
over arbitrary Python objects is an approved inventory algorithm.

| Region | Actual inputs/retained sources and destinations |
| --- | --- |
| Constructor | Two actual network factories and `.to(device)`; Q->target load; optimizer/scheduler factory; registry device tensors; episode counts/completion/current_obs/epsilons; recurrent hidden. Replay constructor/initial serialization is separate child work. Device selector may be unindexed: never use step's historical index-zero comparison as a resolver. |
| Selection | current_obs, episode_completed, ENV.dones/masks, Q parameters/buffers, optional hidden h/c and inactive clones; Q output/display tensor; epsilon tensor and direct helper. Greedy still runs real module forward in retained mode. |
| Step prefix | owned reading snapshots and finite/equality reductions; ENV counts/dones, actions, predecessor; curriculum state and callback outputs; entropy/probability tensors, CPU entropy destinations; temp state device tensors. |
| ENV return/push | next_obs/rewards/dones, active/new-terminal/new-retired, reward-component tensors, intrinsic scale, successor masks, context predecessor/actions/activity/successor; `_returned_step` deepcopy; successor snapshots; RewardTensor components; chunked push inputs; registry/logger effects. |
| Q learning after sample | Every batch observation/action/reward/done/mask/weight/length/loss-mask field actually used; Q/target parameters and buffers; Q gradients; predictions/targets/errors/loss temporaries; optimizer tensor state and param groups; scheduler selected state; target load source Q state. PER handles copy to CPU and error conversion are later child input effects. |
| Recurrent branch | Parent-owned collected episode lists, stack outputs, CPU successor/mask/component copies; Q/target initial hidden and per-length tensors; rollout h/c mutation; sequential store/update child calls. Returned/stored replay ownership remains unsupplied. |
| Completion/export | Current observation and ENV meter slices -> CPU EpisodeCompletion; LaneOutcome copies/fingerprint CPU contiguous bytes; registry metrics; Q/target/optimizer/scheduler state_dict; runtime and replay snapshots. Q state_dict output can expose retained storage: do not describe whole POP checkpoint as detached owned transport without separate proof. |
| Restore | Whole incoming checkpoint deepcopy BEFORE `_validate_checkpoint_state`; known network input tensors and current state_dicts; optimizer state step/exp_avg/exp_avg_sq/max_exp_avg_sq, SGD momentum_buffer, RMSprop step/square_avg/momentum_buffer/grad_avg as selected; scheduler nested exact values; tuple deepcopy of Q/target/optimizer/scheduler; load sources/destinations; replay DTO/material/candidate and runtime candidate; installed replacement references. |

Concrete rejection distinctions:

1. Parent `prepare_checkpoint_state` deepcopies the entire input at 3056 before
   version, exact-key, universe, or tensor checks at 2825 onward. Extra/malformed
   tensor-valued fields can therefore be copied before rejection. A planner
   based only on accepted checkpoint keys would miss actual source work. This
   differs from replay's direct raw-schema early rejection.
2. `_checkpoint_clocks` deepcopies progress before validating progress keys.
   Network validation visits current keys in order: previous finite reductions
   survive a later tensor type/shape/dtype rejection. Optimizer validation can
   read scalar `.item()` or earlier tensor finite reductions before a later
   invalid state field. Exact nested comparison can run tensor operations.
3. Step/selection/flush validate owned state using tensor equality/reductions
   and clone readings before later callback or relation refusals. A refused
   action/mask/cadence path need not be a no-work path. Selection Q forward can
   already mutate hidden/display state before bad masks are rejected.
4. `_bind_training` serializes before policy comparison and can construct a
   replacement before subsequent binding validation. No-work early metadata
   branches must remain lazy, but these executed prefixes cannot be omitted.
5. Foreign/consumed population install handle and wrong ENV phase refuse before
   install publication; a valid handle exposes previously prepared candidate
   devices that must remain covered through runtime install and final cut.
6. Per supplied replay capsule, stale replay installs can stage clones before
   currentness refusal, DTO materialization can clone before full revalidation,
   while some raw top-level schema refusals are earlier no-work branches.
   Preserve the producer's actual traversal/order; do not replace it with a
   blanket all-input CUDA scan or impose generic completion-tail visitation.

Q actual call is bare `optimizer.step()` (837), preceded by zero_grad/backward/
clip, optional scheduler.step and target load. Source installs no hook/closure,
but this does not prove factory/library/hook randomness or purity. Preserve
manual/replacement/closure/hook capabilities and the qualified independent CPU
Adam exception. Constructor/forward/gradient-generation stochastic regions still
need genuine admission; same-owner exclusion remains necessary independently.

## Narrow replay owner response

Ordinary typed flat/PER ReplayBatch fields are supplier-proven detached clones;
receipt arrays are copied. POP's actual `_learn` reads those fields after sample
return; it does not read raw replay row columns. Normal push retains copies;
serialized transport/DTO/materialized/prepared/install chains own their storage.
Thus child False followed by outer True quarantines POP, leaves that sampled
replay's owner-local health unchanged, and retains common poison restrictions.
PER update is a later child invocation with its own receipt/response.
Current replay supplier rechecked these ownership facts against shared881/
flat816/PER1310, and confirms child completion consumer now runs before owner
unlock. Local replay CUDA gates can nest under the authentic active parent
without a caller lineage argument, but their device sets do NOT automatically
join the parent's union. Admitted sample/prepare/install descendants DO join
it. Parent inventories must therefore cover actual later parent effects and
local-only paths explicitly, rather than relying on every local child to enroll
the eventual outer completion set.

Untyped PER `sample` relies on advanced-index semantics, not an explicit clone.
No recurrent inference is made. Public replay attributes remain raw alias
escape routes, but this POP body establishes no ordinary post-child raw-column
CUDA effect. A future supported raw route needs exact preflight owner custody,
storage/effect proof and producer-owned authenticated uncertainty transition.
Until supplied, no private replay-health write or blanket same-device quarantine
is an implementation shortcut. This does not remove any raw API or promise
concurrent uncooperative mutation detection.

## Accepted ten schedules: executable evidence ownership

New tests below are prospective names/categories, not existing collected nodes.
Use real `make_parent(compiled, family, scope, selected_policy=...)`, enter/reset,
actual `step_population` and real replay samples from the hash-matching POP
fixture capsule. It constructs CPU8, batch2, train_frequency1, min_transitions2;
one all-active real step can learn. It has NO device/lineage override argument.
Never fabricate runtime receipts or use fake warmup transitions as e2e proof.

| Accepted schedule | Meaningful parent regression/e2e evidence | Existing owner suite/control to retain |
| --- | --- | --- |
| 1 copied child False / parent True | Actual flat and PER sample then Q+optimizer work, injected outer completion only; trace receipt/health/unlock, next step/selector/export refuse, replay and unrelated owner unchanged | replay CUDA producer and core phase-pair controls; new parent outcome suite |
| 2 healthy counterpart | Same real participants/effects/inventory, successful exit; competitor blocked until receipt consumed and result observable | parent_intrinsic_handoff + initial_participation_population healthy flow |
| 3 same error object | Real wrapper body E with clean completion versus body E and sync E; identity and health discrimination; distinct-error order counterpart | test_rng_cuda_admission existing outcome semantics; parent policy assertions new |
| 4 later child failure | Successful sample then actual PER update/push failure; separate child outcome, own parent completion False if it completes; preserve body consistency failure | test_replay_cuda_producer + test_replay_rng_custody; real parent PER route new |
| 5 normal ownership | Actual post-sample parent training, storage separation and mutation noninterference for normal returned tensors/input/restore transport | existing replay copy/currentness tests plus parent integration assertion |
| 6 admission/order | Real thread barriers with parent and replay competitor; actual preflight lock held through sync/read/transition; entry refusal zero body/getter; observe no added lock/CUDA in consumer | core thread/refusal and producer lock controls; concrete joint owner test new |
| 7 progress cleared | Actual completed vector record and `_step_active` cleanup before injected outer failure; parent still uncertain, no healthy return | test_parent_intrinsic_handoff failed progress characterization + new late cut |
| 8 conditional raw route | Only after authentic supplier mechanism: exact live alias effect and exact owner transition; copied/unrelated owners unchanged | no source-established POP raw route now; not a claimed pass or permission to drop support |
| 9 larger outer handoff | Genuine controller/runner holds actual owner stack, local POP False then ancestor True, ancestor consumes before final release | runner/outer-owner suite and supplier required; a synthetic nesting control is plumbing only |
| 10 inventory/rejected prefix | Actual deepcopy-before-bad-version/extra-key, earlier tensor reductions/later refusal, selected source/destination sets, genuinely no-work laziness | replay producer prefix matrix; new POP restore/selection prefix tests |

Poison schedules require fresh isolated children and root-approved finite
node/role/message/import/PID custody extension; no old role reuse or domain
reset. Root execution separately covers existing owner suites and eventual
real CUDA/multi-device schedules. CPU stand-ins establish causal ordering only.
Test imports may consume published fixture signatures without copying helper
bodies; any actual new body inspection counts in the writer/reviewer budget.

## Smallest coherent APP and finite splits

**Next APP slice recommendation: APP-P1 actual parent custody/health and the
ordinary selector + flat/PER step completion consumer**, after the bounded
supplier contracts below make owner acquisition and child preflight concrete.
It is not useful to add a disconnected health boolean and call parent integration
done. P1 must install a real lifetime owner/custody boundary, thread authentic
lineage into the actual learning sample, preserve constructor/idle registration,
and prove late outer failure/refusal on real parent execution. All public
entrypoints listed above must at least refuse completion-uncertain work; full
candidate restore/runner/recurrent activation can follow in separate packets.
Do not disable recurrent, restore or any existing path to simplify P1. Where
shared wrappers affect those paths, retain them and characterize obligations;
do not claim P1 closed until regressions show no capability degradation.

Proposed P1 writer AND independent source-review body ceilings:

| Body | Current | Ceiling | Purpose |
| --- | ---: | ---: | --- |
| src/townlet/population/vectorized.py | 3163 | 3500 | Actual construction/public integration, required lineage threading, health refusal cuts |
| src/townlet/population/rng_boundary.py (new, proposed) | 0 | 350 | Small concrete POP owner/invocation consumer; no generic registry/policy framework |
| tests/test_townlet/regressions/bac/test_population_rng_custody.py (new, proposed) | 0 | 750 | Real fixture-backed healthy/refusal/order/late-failure controls |
| tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py (existing, read-only unless separately granted) | 791 | NOT in P1 read scope | Consume exact API capsule instead; adding full body would exceed 5000 ceilings |

P1 total ceiling4600 / three bodies, 400-line contingency. No core/replay/ENV/
network/test-helper body can be added opportunistically. Clock48 can be added
only after explicit budget update (4648/four), but current capsule suffices.
If vectorized exceeds3500 or helper/test scope grows, stop and split before
crossing budget; no extraction/removal of existing capability merely to fit.

P2 parent snapshot/restore candidate/lineage packet: remeasure vectorized,
retain its full ceiling3500 + boundary350 + a new focused restore test<=750 =
4600/three. It resolves all candidate registration/deepcopy/issuer/currentness
questions, source-prefix inventory and nested load atomicity. Previous P1 test
is an execution dependency via capsule, not a fourth unread implementation.

P3 recurrent parent adapter: separate source owner for sequential replay and its
ownership/device contract; parent writer retains vectorized<=3500 + boundary350
+ recurrent-parent tests<=750 =4600/three. No flat/PER extrapolation. If changes
touch sequential, assign a separately bounded sequential packet instead of
importing its whole body into parent context.

P4 genuine runner/outer-consumer integration: source supplier first measures
runner and owner helpers, then proposes <=5/5000 with explicit growth ceilings.
No honest exact runner budget can be stated from this POP-only source; this is
a missing bounded inventory, not a license to guess source names/line counts.
Root can execute all accepted suites without every writer reading every suite.

## Exact missing-fact requests before APP-P1 activation

S1 — ENV/runtime/BANK custody supplier: current source seals; actual existing
owner locks and acquisition APIs; whether any acquire common domain while
already owner-held; POP claim/cadence/commit callback call sites and same-thread
reuse; finite owner order and genuinely held outer boundary; selected device
inventory and bootstrap preflight. This task must be divided if combined whole
bodies exceed5000. Return prose/API capsules, not excerpts of hidden bodies.
**ENV/runtime facts delivered** by the sealed capsule above. Remaining: current
BANK1414 (metadata SHA256
`3b9b5476530317fc48991ba096545e3e2bad3593deb92d9caeb3a3bbab6e1027`)
and genuine runner, plus a finite producer implementation contract for the
currently absent ENV/runtime retained custody. A practical producer packet can
retain runtime1299 + BANK1414 + new custody helper<=450 + focused tests<=1000 =
4163/four, contingent on BANK supplier determining those are the actual files.
ENV must be separate: ENV2889 + new helper<=450 + focused tests<=1000 =4339/three.
These are ceilings for bounded follow-on planning, not granted writes or proof
that all producer changes are known. No new settled-design review is needed;
the new source-specific lock/callback contract requires its own ordinary review.

S2 — current replay integration supplier: hash-match current shared881/flat816/
PER1310; exact public preflight lock-retention capability (or explicitly absent),
idle enrollment and per-route source/destination inventory contract, permitted
same-owner reentry while outer holds exclusion, real participant lifecycle on
deepcopy, and whether POP's prepare-then-deepcopy-then-load is still legal.
Raw-owner uncertainty transition only if an actual supported raw route is
established. Existing child completion correctness is not the missing fact.
**Delivered** by current replay capsule. Existing public replay_cuda_preflight
supplies retention; current core API metadata and no-deepcopy-authority facts
are settled. No replay retention API implementation is needed for copied batches.

S3 — Q/factory/optimizer source supplier: actual selected factory construction
RNG and CUDA effects, device/parameter/buffer/gradient/optimizer state inventory,
supported hooks/closures/replacements, forward mode behavior and genuine
registration/admission dependency. Do not re-audit Torch wholesale or remove
manual/independent CPU Adam capability.

S4 — real outer controller/runner supplier: current call sites for constructor,
selection/step/restore and stable-role binding; actual larger exclusion lifetime
and where the final completion receipt must be consumed. Source-measured bounded
packet required; this preparation cannot certify the outermost release.

S5 — current core API metadata freshness only: confirm unchanged required gate
resolve/enroll/invocation APIs against current1195 and the new source-issued18
manifest. This is a supplier capsule update if necessary, NOT a new core design
or implementation review. Existing adopted outcome semantics are settled.
**Delivered** by the current replay/core supplier; current1195 required APIs are
source-verified. Do not send a redundant new core task for this question.

Root should obtain the remaining BANK/Q/runner source facts and producer custody
contracts, seal the P1 exact files/contracts,
then grant independent plan/source review and actual APP implementation. No new
review of the settled parent attribution design is requested. This preparation
is complete as POP source inventory; cross-owner locking and activation readiness
remain explicitly incomplete until the named suppliers answer.
