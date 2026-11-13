# Flat/PER CUDA producer A — source classification and causal RED plan

2026-11-13. Initial-grant deliverable only. Accepted B6/R0 implementation
preparation; no design restart, implementation/test edit, import/application
execution, Git write, branch/worktree/source copy, delegation or qualification.
Root supplied committed base `9acd85d3ccd897051288a13fd16e610b9ee1fca1`
(WIP17, remote verified). This author did not independently execute Git.

## Source seal and bounded packet

Measured complete bodies before reading. Exactly these three production bodies
were read; the fourth, new test does not exist. No excluded source/test/helper
body was read, including via snippets/diffs or import introspection.

| Authorized body | Actual lines | SHA256 | Planned ceiling |
| --- | ---: | --- | ---: |
| `src/townlet/training/replay_contract.py` | 374 | `8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1` | 650 |
| `src/townlet/training/replay_buffer.py` | 728 | `817495558b45a51ba5df3751f83d1985135e23d9dfe6f827e3e323c45df01214` | 850 |
| `src/townlet/training/prioritized_replay_buffer.py` | 1164 | `b989a8f153cf6a2686140efcfb6ce1d4914f4379785c2c094e1cc5d1142033b8` | 1300 |
| `tests/test_townlet/regressions/bac/test_replay_cuda_producer.py` | absent | absent | 1000 |

Current total 2266 / three; planned maximum 3800 / four; hard user maximum
5000 / five remains an outer limit, not permission for another body. Production
growth reserve is 534 lines, test reserve1000. Remeasure before further reads
and after edits; return to root for reslicing before any ceiling is exceeded.
Never compress or transfer code/controls into uncounted helpers.

Read repository AGENTS.md, the named additive design/FIX1, local-gate
protocol/FIX1, producer preflight/FIX1, and public CURRENT-RNG-CUSTODY-CORE-CONTRACT
and CURRENT-REPLAY-CUSTODY-CONTRACT. Applied writing-plans to this finite handoff;
brief overrides generic plan location, Git/worktree and execution defaults.
Filigree/Loomweave are unavailable under the brief; none reconstructed.

Also consumed prose-only `T18e-R0-REPLAY-HELPER-RNG-FACTS.md`. Root metadata
verification binds its current supplier bodies: historical_checkpoint.py675
SHA256 `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`
and per_sampling.py163 SHA256
`0efe801f01a31082aa52c4b9bd40c356d1c97f89690b07c7835b541b7f2c6de6`.
Those are supplier facts, not two additional source reads in A.

Core821 and core-test1409 are supplied R89 identities, not this author's source
reads. Recurrent and old replay tests are excluded. Root owns runtime capture,
test processes/grants, independent review and publication. No accounting change
from28qualified/38remaining/66total follows this packet.

## Exact classes, dispatch and source-issued identities

Lifetime owners inspected: canonical
`townlet.training.replay_buffer.ReplayBuffer` and
`townlet.training.prioritized_replay_buffer.PrioritizedReplayBuffer`.
`_PrioritizedArchiveValidator` is an actual subclass in the admitted PER body:
its `_init_custody` is deliberately empty, and `_own_archive` constructs it
with CPU selection solely to call the undecorated `_validate_serialized`.
Preserve this detached validation affordance; do not invent a participant,
require a local contract on it, or register it. There is no other concrete
subclass declaration in these bodies. This does not establish absence of
subclasses outside the packet. Arbitrary callback/subclass extensions retain
the public capsule's cooperative profile; no previously supported concrete
GPU subclass may be silently discarded. Root must supply its public capsule
or reslice if such a class is established before activation.

Proposed names below are immutable handoff choices for B. Each name is one
separate opaque constant exported by `townlet.exploration.rng_custody`, with
fixed canonical exact class and route binding; names are NOT existing authority.
No caller-created contract, public issuer, route/purity flag or string fallback.

| Exact owner | Actual public local route | Proposed constant |
| --- | --- | --- |
| ReplayBuffer | `push` | `REPLAY_BUFFER_PUSH_CUDA` |
| ReplayBuffer | `push_recorded` | `REPLAY_BUFFER_PUSH_RECORDED_CUDA` |
| ReplayBuffer | `readiness` | `REPLAY_BUFFER_READINESS_CUDA` |
| ReplayBuffer | `serialize` | `REPLAY_BUFFER_SERIALIZE_CUDA` |
| ReplayBuffer | `validate_serialized` | `REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA` |
| ReplayBuffer | `load_for_mode` validation prelude (`_validate_serialized(..., expected_obs_dim=None)`) | `REPLAY_BUFFER_LOAD_FOR_MODE_VALIDATION_CUDA` |
| ReplayBuffer | `historical_archives` property read | `REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA` |
| ReplayBuffer | `install_historical_archive` | `REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA` |
| PrioritizedReplayBuffer | `push` | `PRIORITIZED_REPLAY_BUFFER_PUSH_CUDA` |
| PrioritizedReplayBuffer | `push_recorded` | `PRIORITIZED_REPLAY_BUFFER_PUSH_RECORDED_CUDA` |
| PrioritizedReplayBuffer | `declare_unconstrained_action_dim` | `PRIORITIZED_REPLAY_BUFFER_DECLARE_UNCONSTRAINED_ACTION_DIM_CUDA` |
| PrioritizedReplayBuffer | `readiness` | `PRIORITIZED_REPLAY_BUFFER_READINESS_CUDA` |
| PrioritizedReplayBuffer | `serialize` | `PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA` |
| PrioritizedReplayBuffer | `validate_serialized` | `PRIORITIZED_REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA` |
| PrioritizedReplayBuffer | `historical_archives` property read | `PRIORITIZED_REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA` |
| PrioritizedReplayBuffer | `install_historical_archive` | `PRIORITIZED_REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA` |
| PrioritizedReplayBuffer | `update_priorities` | `PRIORITIZED_REPLAY_BUFFER_UPDATE_PRIORITIES_CUDA` |
| PrioritizedReplayBuffer | `update_unit_priorities` | `PRIORITIZED_REPLAY_BUFFER_UPDATE_UNIT_PRIORITIES_CUDA` |

These are finite route candidates for exact activation review, not a claim
that every dependency is already source-qualified. Distinguish states:

* Healthy source classification of visible tensor algorithms: no ambient RNG
  calls in `_push`, legality declaration, readiness, serialization tensor loops,
  validation tensor loops or priority update. Inputs are ordinary supported
  tensors/DTOs/arrays and documented scalar fields. CUDA query/bootstrap,
  transfers, reductions, allocations, indexing and copies still need supplier
  and hardware qualification; source observation alone proves no GPU RNG law.
* Archive helpers' ordinary-data local graph is source-classified RNG-free by
  the hash-matched supplier capsule. Combined with visible caller reachability
  below, this classifies the ordinary archive-dependent local producer paths;
  actual supplier CUDA effects and metadata-only inventory remain distinct.
* READY post-poison GPU permission is UNQUALIFIED for every listed candidate.
  B must record healthy permission separately from `post_poison=False` until
  exact supplier/runtime evidence exists. CPU owner-local continuation remains.
* Production manifest is currently EMPTY. A is staged/incomplete until B
  activates the reviewed exact identities. No fabricated constants or private
  CPU fixture policies may make the production route appear integrated.

`sample`/`sample_batch` are full-domain admitted routes, never local contracts.
Flat `_indices` uses selected-device `torch.randperm`; PER direct `sample`
preserves global vectorized NumPy law even with an owned configured Generator;
PER qualified batch preserves external-versus-owned Generator mode, receipt,
weights, stable IDs and continuation. `materialize_validated` and
`prepare_serialized` are real `prepare`; `load_prepared` is real `install`.
All migrate explicitly to `device_operation`, including truthful CPU `()`.
`load_for_mode` and `load_from_serialized` compose local validation then genuine
prepare/install with their exact explicitly supplied lineage. Flat's current
`load_for_mode` calls private validation with optional width directly, unlike
PER's call through public validate_serialized; its separate validation-prelude
contract above covers only that local phase. Do not make its entire load path
a local leaf or erase flat public validate_serialized's required int annotation.

Owner-only metadata routes: both `retained_transitions`, `__len__`, `stats`,
`clear`; PER also `size`, `anneal_beta`, `configure_sampling`. They need no
CUDA runtime query solely because retained fields or the selector are CUDA.
`clear` drops references under owner exclusion; no new tensor kernel is added.
`stats` reads tensor metadata (`numel`, `element_size`). PER configuration
copies/validates an explicit NumPy Generator state onto an offside engine;
preserve caller/persistent/ambient state and local revision discipline.

The listed tensor routes choose owner-only CPU execution only when all actual
input/retained/helper-source work is CPU and no selected CUDA allocation is
needed. A CPU destination with CUDA input is local CUDA work. Conversely,
empty/archive-only preparation must not initialize the configured CUDA target
when it allocates no target tensors. Readiness uses retained legality tensors,
not the configured destination. Priority updates use `td_errors` and NumPy
state, not unrelated retained replay tensors. Serialization uses live rows and
archives, not an unused configured target. Exact branch planning precedes
effects, not a blanket `self.device.type` classification.

## Inputs/effects and inventory functions

Proposed producer-private names and roles (all in the admitted bodies):

* `ReplayCustody._effective_replay_device` is a property returning the current
  private scope's concrete `torch.device`, or the unchanged public CPU selector
  for an authentically CPU-only call. No cached permanent CUDA canonicalization.
* `ReplayCustody._replay_cuda_devices` collects sorted unique concrete indices
  from known supported tensor metadata only. No callbacks/property traversal
  across arbitrary objects, device-count expansion or core private state.
* Family `_replay_inventory` inventories each family's `_STORAGE_FIELDS`,
  `_ReplayRows`/`_PrioritizedRows` DTOs, issuer-held restore candidates and the
  finite route-specific ordinary inputs. Shared issuer material remains private.
* `ReplayCustody._quarantine_replay` sets unhealthy and advances owner revision
  under the existing owner lock; never heals it.

Keep existing public method signatures and typed decorator forwarding,
`PreparedReplay` return transformation and mandatory lineage. Add route-specific
local wrappers without changing recurrent's unreviewed behavior through a
blanket replacement of existing decorators. Internal reuse is limited to
source-declared helper edges: `push[_recorded] -> _push -> _validate_push`,
`sample_batch -> readiness` under its admitted scope, and prepare/materialize
and validation/archive helpers under their one outer scope. No marker grants
public sample/prepare/install implicit lineage or arbitrary callback reentry.

All `_STORAGE_FIELDS` are observations/actions/rewards, three optional reward
components, next_observations/dones, next_action_masks/legality_recorded and
three presence columns. Inspect each present tensor independently: do not
assume one allocation identity or use the first tensor as the inventory.
For push inventory every actual observation/action/reward component/successor/
done/mask input, existing storage read/written and the selected destination
when allocation/index construction is performed. Optional zero/presence
temporaries inherit actual reward/done devices; include those sources.
Legality declaration includes retained actions and selected allocation target.
Readiness inventories legality_recorded; priority updates inventory td_errors.
Sampling includes actual accessed retained fields, selected indices/mask/
weights/lengths/unit-ID outputs and DTO validation/copy temporaries.

Preparation includes known transport tensor fields (or validated DTO fields),
legacy/archive source tensors reached by supported historical operations,
actual destination, and issuer-held material retained by the owner.
Installation includes original candidate tensor devices, live material needed
for archive merge, staged clone devices and publication destinations. Candidate
install clones remain on the candidate's actual devices, not today's selector;
changing the selector must not silently migrate retained or prepared material.
Conservative inclusion of issuer-held candidates is explicit, never omission
because public handles hide their payload. Expired weak handles retire by the
existing registry discipline, not new hidden strong roots.

Transport inspection is finite known field access on supported owned data;
it does not establish purity of arbitrary Mapping methods or Tensor subclasses.
Raw aliases require caller quiescence as before. Ordinary invalid arguments
must reach preserved validation errors; device planning cannot invent a
new authority exception merely by recursively probing arbitrary input objects.

Exact helper reachability combined with supplier facts: both `_own_archive`
call `_record` then `_archive_from_state`; both `_merge_archives` call
`_own_archive` on retained/incoming archives and deduplicate source_digest.
Public historical reads and installation call these paths. Both serialize
routes call `_record`; their validate routes call `_archive_from_state` then
`_own_archive` on embedded current archives and `_clone` on legacy transport.
Both materialize routes `_clone` legacy data or a reconstructed current
mapping, revalidate, then call `archive_standalone_replay` for legacy archival
material and `_merge_archives` for candidate archives. Both install routes
call `_merge_archives` before final validation/publication. PER `_own_archive`
additionally reads owned original_state, constructs the CPU-only detached
validator and calls its undecorated legacy validation; its state cloning and
offside NumPy reconstruction do not draw persistent/global RNG. Visible
SamplingReceipt/validate_successor_masks implementations close the helper
capsule's two named unresolved producer dependencies in this packet.

The supplied archive graph includes detach/clone, dense-tensor reductions,
canonical CPU materialization/contiguous/value bytes and numeric NumPy copy,
with no random primitive/callback for ordinary builtin containers/scalars,
dense ordinary tensors and numeric NumPy arrays/scalars. Archive export,
broader historical access callbacks, training hash/config functions are NOT
reached by these producer paths and receive no local classification here.
Arbitrary Mapping/Tensor/NumPy subclasses/deepcopy hooks remain outside that
proof; do not add a new unsupported-input rejection as a routine workaround.

Remaining exact helper inventory fact: public original_state/source_formats
reads clone through `_Owned.__getattribute__`; therefore invoking those
accessors to discover devices before `complete` would itself do unarmed
tensor work. Root supplier must confirm a metadata-only way to inspect the
canonical archive's retained plain payload (or provide a bounded API delta).
Do not guess archives are CPU, copy before arming completion, broaden to all
devices or silently refuse previously supported GPU archive data. No helper
body was read to settle this fact. RewardTensor is the imported
`townlet.training.state.RewardTensor` from `src/townlet/training/state.py`:
the producer reads its total/extrinsic/intrinsic/shaping tensor DTO fields.
That source is excluded; ordinary field/profile assumptions remain an exact
supplier boundary, with no claim about custom property hooks or introspection.

## Gate order, completion and parent API

Constructors validate CPU/CUDA selector structure without any CUDA attribute
access, leave `self.device` unchanged and register one lifetime owner with `()`.
No init, initialized/count/current query, allocation or index-zero guess occurs.
Explicit invalid CUDA bounds are resolved at actual CUDA work, not construction.

Admitted sequence: authentic `domain.admission(lineage=...)` before owner lock;
resolve needed selection through that gate before owner-held bootstrap; owner
lock/check health/inventory; idle union enrollment only for standalone idle
custody; real `device_operation(participant=..., operation_kind=...,
lineage=..., cuda_devices=...)` inside owner exclusion; actual body and staging;
operation completion; owner-held uncertainty quarantine; release owner, gate.
An active parent validates its enrolled subset through real device_operation;
do not call idle-only enroll under a parent or inspect private active state.

Local sequence: source-issued exact route gate before owner lock; resolve any
actually needed target before owner-held bootstrap; lock/check/inventory;
`gate.complete(cuda_devices=...)` around all actual tensor work; in owner-held
finally inspect `completion_failed()` and quarantine if true; then release
owner and gate/pin. Local gates grant no enrollment, token or draw authority.
Body failure still completes. Preserve body/completion exception identity and
aggregation. A bootstrap failure before owner work poisons the domain without
inventing owner publication corruption.

Planning must be race-safe: inspect branch/device metadata under owner
exclusion, release it before obtaining any new gate/bootstrap authority, and
revalidate the plan under gate then owner exclusion before effects. If the
plan changed, replan outside independently held owner exclusion before work;
never bootstrap under owner or acquire domain from an owner-only leaf. Pure
no-op branches must stay lazy. Internal scope reuse cannot add a new device
after completion is armed. CPU owner-only competition remains blocked by the
owner held through actual CUDA completion.

Finite public API gap to settle before production edits: local gate exposes an
authenticated failed-completion outcome, but the supplied `device_operation`/
`RNGOperation` capsule exposes none. Capturing the body error and comparing the
exit error distinguishes ordinary body failures from most completion failures,
but not the same exception object raised by both body and synchronize after
core deduplication. To preserve clean-body usability AND guaranteed quarantine,
root/core supplier must provide an existing public outcome fact or a separately
bounded public completion-outcome delta. Private operation/status fields,
quarantining every clean argument/body failure, or ignoring uncertainty are
not accepted substitutes.
Root now confirms the exact current source has no operation outcome marker,
standalone operation becomes inactive at exit, and nested scopes share the
parent token; an accessor on that shared token alone cannot identify each
completed nested scope. Root owns the separate scoped-outcome API design.
Independent constructor-laziness/effective-device/inventory RED controls may
proceed after their writer grant while this bounded dependency is settled.

Required new public parent signature:
`ReplayCustody.cuda_preflight(*, anticipated_devices: tuple[torch.device, ...])
-> AbstractContextManager[None]`.
Proposed shared multi-owner signature:
`replay_cuda_preflight(*, owners: tuple[ReplayCustody, ...],
anticipated_devices: tuple[torch.device, ...]) -> AbstractContextManager[None]`.
The anticipated tuple is an explicit finite union for that group, not a default
and not all available devices. Singleton delegates to the same protocol.
Enter before any parent/BANK/ENV lock; synchronous same-thread use only. One
idle admission gate -> strongly pinned exact replay owners -> replay RLocks
in stable identity order -> initialization/resolution/inventory/idle enrollment
with bootstrap before owner-held work -> parent operation/lifecycle locks.
If bootstrap requires releasing temporary metadata locks, complete it before
the final retained lock plan is established. Keep final pins/gate/locks through
nested replay and parent outer completion; release locks in reverse order,
then pins/gate. Caller enters parent inside preflight and passes its exact
authentic lineage. Current-device changes to pre-enrolled indices resolve anew
at each nested invocation; undeclared/unenrolled targets refuse before effects
with preflight-required diagnosis. No active init/enrollment or lineage-None
fallback. Parent call sites themselves are outside A and require their packet.

## B1/B2/B4/B5 and currentness preservation

Keep opaque identity-only PreparedReplay, weak issuer registry and original
`(owner_revision, RNGCurrentToken, owned_material)` binding. A DTO is data,
not authority. Materialize owns its bytes then reruns complete content and
current destination validation. Preserve legality, reward components,
geometry, PER priorities/float32 insertion bounds, stable IDs and exact sampler
engine/state/origin. Archive/captured-format semantics are existing supported
history, not new compatibility adapters.

Every successful or attempted local mutation advances owner revision under
lock before its body, even a no-op or later clean failure; reads do not.
Local successful CUDA gates do not substitute core currentness changes.
Prepare records original material/revision/token only after valid staging;
install stages all fallible ownership copies/merges/Generator reconstruction,
then checks original owner revision/material identity and validate_current
immediately before first publication assignment. Never reissue/refresh a
token to bless stale bytes. Successful install consumes once and advances
revision; partial publication quarantines. Actual initialization/idle membership
expansion stales older tokens by core rules; no-op resolution/enrollment does
not. Same-parent local mutation must fail owner revision independently of
core token fields. Preserve CPU/detached/disposable scratch affordances from
public capsules without reading or rewriting recurrent scratch algorithms.

## Finite tests-first plan — all UNRUN

One new self-contained test body <=1000; no old tests/helper source reads.
Root grants writing then captures RED at unmodified production hashes before
granting production changes. Existing healthy CPU gates are executed by root
through established selections, not copied here. No source-control actions.

| Proposed test group | Actual causal witness / baseline expectation |
| --- | --- |
| `test_empty_constructor_has_no_cuda_access` (flat/PER x cpu/cuda/cuda:3) | Fail-on-any-CUDA-attribute sentinel; actual constructor and lifetime registration. CPU controls pass; unindexed/indexed CUDA defects RED before any GPU simulation. Selector identity preserved. |
| `test_cpu_local_and_admitted_routes_stay_cuda_free` (both families) | Real rows, push_recorded/readiness/stats/serialize/validation/preparation/install/sample/clear; fail-on-CUDA sentinel; genuine output/receipt and original stream-law controls. |
| `test_dynamic_selector_and_retained_inventory` (both) | Actual producer calls with finite simulated runtime/factory seams; selected0 then1, clear/repopulate for supported successful allocation, plus retained/source0 and destination1 metadata. Assert exact completion tuples, no count-wide sweep and unchanged public selector. Baseline missing gate/dispatch RED. |
| `test_priority_update_cpu_destination_cuda_source` | Real PER priority algorithm and original result, td_errors source1 with CPU destination; exact local completion1 and no unrelated retained-device completion. Baseline owner-only dispatch RED. |
| `test_prepare_install_inventory_and_noop_resolution` (both) | Real preparation/owned candidate on source0, destination1, retained candidates and install clones; original token stays valid on no-op resolve/enroll, actual expansion stales it; install does not migrate material to new selector. Genuine core token, never fabricated authority. |
| `test_same_parent_mutation_stales_owner_candidate` (both) | Genuine preflight/parent prepare, local clear or PER configuration/priority mutation, then install; unchanged core token fields cannot rescue owner revision. Positive same-parent prepare/install and pure-read controls. Existing ordinary sibling sampling separately stales core currency. |
| `test_completion_retains_owner_exclusion` (both; local/admitted; success/body failure) | Actual method reaches controlled synchronize barrier; real competing clear/store thread proves it cannot acquire owner until completion ends. Capture body result/error and unchanged identity after clean completion. Baseline releases owner before admitted completion RED; local scope absent RED. |
| `test_completion_uncertainty_quarantines_before_unlock` (local/admitted) | Controlled one/two-device synchronize failures, including body+completion distinct identities and same-object collision. All declared completions attempted, first poison retained, quarantine visible before competitor can enter; no returned batch/handle after failure. Needs public admitted outcome gap settled. |
| `test_failed_preparation_preserves_owned_data` (both) | Invalid mutated validated DTO, destination width change, invalid masks/PER priority/IDs; compare complete real serialized live data and original CPU/NumPy/Torch states. No handle/publication; fresh valid preparation then succeeds after clean failure. |
| `test_preflight_pins_and_declared_switch` (both) | Exact genuine parent lineage, two declared targets, changed selected index inside parent, no-op same-parent prepare/install; competitor excluded through nested AND outer completion. Missing lineage/undeclared target refuses before draw/staging. Multi-owner order and exception unwind retain pins until completion. |
| `test_authentic_local_dispatch` (both) | After B only, actual exported constants and real registered concrete producer routes admit; wrong family/subclass/fabricated contract refusal belongs to B activation controls. No production manifest monkeypatch or arbitrary fixture contract. |
| `test_poison_preserves_cpu_local_capability` | Root-owned isolated poison process: CPU local read/configure/clear usable, ambient sample/prepare/install refused, unqualified/unknown-runtime GPU leaf refuses before init/body, poison never heals. New child schema/custody must be approved before execution. |

Simulation is CPU protocol evidence only. CPU seams may redirect finite CUDA
runtime calls and tensor allocation/transfer to controlled CPU-backed test
representations with explicit device metadata, with all such fixture code in
the counted new test body. They must exercise the actual producer algorithm,
not replace sample outputs, fake a healthy result or fabricate core policy.
Tests of source-owned local permission remain RED/staged until authentic B
activation; do not turn missing production contracts into artificial GREEN.
Real Tensor/DTO output equality and sampler continuation are positive controls;
simulated metadata does not qualify arbitrary production Tensor subclasses.

Hardware matrix remains root-owned: fresh real lazy first-use per selector,
actual init/query RNG preservation, nondefault explicit device, two-device
selected/retained/staged identities, real asynchronous competition, nesting,
failure/quarantine and individually qualified READY post-poison leaves. A GPU
absence skip or CPU simulation cannot close those obligations.

## B and root dependencies / disposition

1. Root supplies remaining canonical archive metadata-only inventory fact and
   RewardTensor ordinary-field fact or reslices those finite supplier boundaries;
   the helper RNG classification is now closed by the hash-matched capsule.
2. Core supplier settles authenticated admitted-completion outcome without
   private access, then freezes its exact required signature/type capsule.
3. B reviews actual A leaves at final hashes and activates only justified exact
   class/route constants via fixed source-owned canonical resolution/cache;
   healthy and post-poison permissions remain separate. No generic issuer.
4. Required separate B core+existing-core-test packet updates exact manifest
   assertion and actual resolver/cache fork/guard state observations; original
   preflight's unchanged-test expectation is superseded by FIX1.
5. Root grants tests-first writer, captures RED, grants implementation, reviews
   final sizes/bytes and integrated CPU controls, then separate independent
   source/spec/quality review, parent integration and real hardware matrix.

No implementation writer or runtime grant is inferred from this capsule.
A remains staged/incomplete until B and these finite proof/API dependencies
are resolved. No healthy-GPU integration, B6 closure, capability removal,
waiver or programme acceptance is claimed.
