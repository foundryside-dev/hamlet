# Parent integration V2: current outer facts and first producer APP contract

2026-11-14. PROPOSED implementation contract, pending independent bounded review
and root APP baton. No implementation, runtime or test execution occurred.
Preserves V1 `T18e-R0-PARENT-INTEGRATION-CURRENT-PREPARATION.md` SHA256
`781a98a7e8ca67b4d7cfa15a7852314c14d8beb7da8f57a5d62777a434111815`
and its compact handoff SHA256
`76edaa308dd9b54e6311af1f4195292496d5cbc27c0c160591bae474731ee4f4`.
V1's full public POP inventory and ten acceptance schedules remain applicable;
this version resolves additional suppliers, corrects diagnostic accounting and
replaces its tentative first-APP ordering with the concrete producer slice below.
The accepted parent attribution/outcome design is not reopened.
The pre-native V2 bytes are preserved as
`T18e-R0-PARENT-INTEGRATION-PROPOSAL-V2-PRE-NATIVE-SNAPSHOT.md`, SHA256
`3139424328b4b5ab2c21d20df96c77e54665f88df326903588eccb76e6153cbf`.

## Exact source custody

Measured/hash-verified before each new body read; four complete bodies3924 lines:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| population/vectorized.py | 3163 | 6c4f7ca085f0a7db34f42bebe22f0240ed12825627c13bcffb3c0d3be3f99022 |
| demo/unified_server.py | 616 | 626634171c744ecac9ac825f5db5727e3407031efd6c8fe0dcac5a1058e2a02c |
| agent/token_input.py | 116 | 2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3 |
| determinism.py | 29 | 73b8cd748bf1d495d0dfa22842e85c2e5a52421bd3081afbfd401eb0c0f14244 |

All paths above relative to `src/townlet`. No fifth body admitted. Supplier
capsules consumed as source-qualified prose, not additional body inspection:

| Capsule in P | SHA256 |
| --- | --- |
| T18e-R0-PARENT-REPLAY-CURRENT-SUPPLIER.md | f6c48b621acbc26f9198a8e25f71a6f25b29fc4697d8f3e7d0bf77a0154b7b37 |
| T18e-R0-PARENT-ENV-RUNTIME-CURRENT-SUPPLIER.md | 02ac16732bb18dd6613c09cf90f2b20850da402c355cd11604f000f3f91b5b33 |
| T18e-R0-PARENT-BANK-CURRENT-SUPPLIER.md (includes device-inventory addendum) | 4e118f6b65bbfd4bdc9b877624d9ad5abbbeb607e97374a9776b9e33f11165e4 |
| T18e-R0-PARENT-FACTORY-RUNNER-CURRENT-SUPPLIER.md | d0e6452aafa5a7f870f69c10aa155e1a0b1da1a8a5533ac03210333d6c2fb5ef |
| T18e-R0-PARENT-NATIVE-CURRENT-SUPPLIER.md | 7cb54762da2ecffae75091d06725afac71d83097f615cd364fc79ed1f54f0ba9 |

Root's WIP21 hosted lint classification reports Ruff/Black PASS and 15 mypy
diagnostics: six oracle, nine POP. **Nine POP diagnostics are not nine diagnosed
unique callsites.** Lines698 and699 each contain two nested replay calls;
701 and702 one each; line800 one sample call generates three union diagnostics.
That is seven diagnosed invocations across five lines, generating nine errors.
Source inventory additionally finds two missing required lineage arguments at
3067 materialize and3070 install, whose values are dynamically typed. Therefore
V1's nine source-level omissions is a valid broader call inventory, but must not
be equated to the nine hosted errors or treated as nine independently reported
type failures. No hosted log or lint execution is newly claimed by this worker.

## Ordinary server and real outer ownership

UnifiedServer imports actual DemoRunner at module level. `start`177 first admits
the resolved launch and creates checkpoint/log paths, then starts non-daemon
`TrainingThread`206 targeting `_run_training`. That target398 constructs
`self.runner=DemoRunner(...)`417 and calls `self.runner.run()`428 on the training
thread. This closes the CLI -> UnifiedServer -> DemoRunner source question.
Factory supplier's outdated runtime assembly/reset call defects are on this
ordinary path, not an unused alternate runner inferred from its filename.

The same start creates daemon `InferenceThread`216 targeting `_run_inference`.
It constructs LiveInferenceServer465 with the same checkpoint directory,
config root, level and episode count, then runs a fresh asyncio event loop and
uvicorn server. No live POP/ENV/Q/optimizer reference is passed to it here.
It is nevertheless a concurrent process-global RNG participant and checkpoint
consumer whose internal construction/load/selection semantics are unsupplied.
No server data lock, RNG admission, invocation, model publication lock, or
checkpoint handoff appears in this616-line body. Its only mutex is
`_shutdown_lock`, protecting a short stop-flag transition; it owns no training
effects. Do not use it as parent mutation exclusion or span a synchronous RNG
operation across thread creation, await, or inference event-loop work.

Training success sets both `training_completed_normally=True` and
`shutdown_requested=True`432–433. Training Exception439 and inference
Exception509 also set shutdown_requested. `start`'s loop notices failures and
sets that flag itself254/259, then exits without a finally calling stop.
`stop`356 returns immediately if the flag is already true358. Consequently a
worker's normal/error shutdown request can make a later stop skip its joins and
file-handler cleanup. This is a source-visible lifecycle gap, not an executed
test failure. The normal stop branch asks uvicorn to exit and joins inference10s,
sets runner.should_shutdown then joins training30s; it warns if either is still
alive but logs all components stopped and closes the handler anyway. Stop must
distinguish requested shutdown from completed cleanup and must not claim all
owners released after timeout. Preserve bounded joins and primary failures.

The supplier's DemoRunner post-POP reward accumulations, ENV positions/meters/
action-mask recorder inputs, episode statistics, database/TensorBoard events
and save_checkpoint remain genuine later effects/publication. Thus POP local
False does not establish runner completion. Actual final consumer belongs on
the training thread around each finite effect/publication scope, not around
the entire server lifetime. The runner's unconditional final save after failure
must not publish an uncertain model as a healthy checkpoint; cleanup must not
replace primary failure or strand resources. This is later runner APP work.

## Token assembler and seed inventory now source-complete at these boundaries

TokenInputAssembler is an nn.Module. For every token type its constructor41–48
allocates float32 context_rows and two long lane-index tensors with no device
keyword, registers all three as `persistent=False`, and stores only names and
scalar layout metadata in `_TypeAssembly`. Effect contexts come from the catalog;
other types from slot payloads. The constructor has no RNG primitive or mutable
cache, but actual default device can affect these allocations. Registered
nonpersistent buffers participate in ordinary Module.to; their omission from
state_dict does NOT mean they can be omitted from device/clone inventory.

`expand_type`63 validates type/shape/floating dtype before tensor operations.
It computes presence, obtains the actual registered context buffer and either
copies `.to(dynamic_rows.device, dynamic_rows.dtype).expand(...).clone()`83 or
validates present effect selectors through finite/integrality/float32 roundtrip/
bounds reductions, then builds safe long selectors and index_selects a converted
context108. Empty effect catalog allocates zeros on dynamic_rows.device100.
It directly indexes/scatters using registered dynamic/fixed lane buffers115,
then returns torch.where with zeros_like116. There is no cached converted
context or custom `.to` override. Sources therefore include actual context and
lane buffers plus dynamic_rows; destinations include its device, converted
context, selectors, fixed_rows and output. A late invalid selector can follow
presence/gather/reduction/conversion work; unknown type or bad metadata can be
genuine no-work refusal. Keep actual rejected-prefix ordering.

These facts complete the delegated token expansion inventory without reading
another model/library body. Current POP independently constructs Q385 and
target397 then `.to(device)`, copies Q to target400 and sets target.eval401.
OptimizerFactory receives Q.parameters406. Learning sets Q.train801 and
target.eval802; rollout does not switch Q mode. Factory-proven dropout/LSTM
training effects remain relevant despite no_grad. Constructor default-device
sources and target transfer destinations both matter; do not silently force CPU
construction or ban hooks/replacements to simplify an inventory. Lazy optimizer
slots on actual parameter devices and all current gradients/state remain covered.

`seed_all`20–29 calls exactly random.seed(seed),
np.random.seed(seed % 2**32), torch.manual_seed(seed), in that order. It neither
acquires custody nor snapshots/restores state. Torch's documented CPU/all-CUDA
seeding behavior is delegated library behavior, not a source-local inventory
loop. Earlier setters can have changed state if a later setter fails; no rollback
exists. DemoRunner invokes it before network construction and before a temporal
gap, while UnifiedServer starts inference independently. A future seed scope must
be actual standalone common admission at the seeding boundary and coordinate
other initialized consumers; no reseeding during private activation or imagined
constructor-only protection. Do not add per-step seed/reset or process resume
promises. The separately qualified independent dense CPU Adam exception remains.

## Resolved ordering facts and why producer APP comes first

Replay already supplies public retained preflight: domain admission -> sorted
replay-owner locks, with resolution before locks. Current core1195 supplies
qualified invocation outcomes. No core or replay redesign is needed for ordinary
copied-batch retention. New replay owners and restore destinations must be
registered idle; prepare and install belong to the same actual issuer, never
a deepcopy of participant/token/lock authority.

BANK public methods currently have NO incoming lineage argument. BANK's private
_admission always opens domain.operation(lineage=None), THEN BANK RLock, and
forwards its own issued lineage to native owners. An active POP ancestor makes
that public BANK call refuse; changing only runtime keywords is insufficient.
Runtime ordinary methods hold runtime RLock before calling BANK. Adding an
unchanged domain-first parent path creates the concrete potential cycle
parent holds domain/waits runtime versus ordinary runtime holds runtime/waits
domain. Both producer layers must change coherently before parent activation.

BANK releases its lock before its own operation completes. This is an absent
future ancestor-retention capability, NOT a demonstrated current standalone
healthy-window P1/P2 defect: common poison is established while domain remains
held and all supported BANK public routes refuse before body after poison.
Ordinary publication failures have current inner fail-closed latches. Preserve
that classification and the existing healthy-saved-payload restore capability;
neither licenses parent completion recovery or poison reset.

ENV has no mutex; runtime has no public retained-custody scope. Reverse accepted/
claim/cadence/commit/report/issuer callbacks need existing checks plus genuine
current-scope reuse. A parent must not acquire a new POP lock under runtime/BANK
just because an arbitrary callback says it validates a parent. Relevant native
locks need retention ONLY where actual post-child storage effects demand it;
ordinary CuriosityReward and replay batches are copied. No blanket quarantine
or native-lock requirement is inferred solely from membership/device overlap.

The native supplier now closes the stamp/ordinary native-copy question: managed
private/shared call results detached-clone ordinary Tensor/container material;
CuriosityStepStamp constructor clones all three tensors and each public tensor
property returns another clone. Its retained identity still authenticates the
step, but normal property access is not a live native-storage alias. Native
operations already complete their OWN full declared member tuple before return,
even under genuine ancestor lineage; private RNG activation additionally
synchronizes capture/restoration. Parent union completion remains a separate
later phase. C1 must not change native work to deferred completion or wrap a
whole multi-owner parent in a private RNG callback (cross-owner/private-frame
rules would reject that). No native retention/late-quarantine API is required
for these copied-output C1 routes, and no such current public API is claimed.

Native owners expose rng_participant and required-lineage methods, but no public
member-device getter. Arbitrary callback-return/hook tensors and RND/CP rejected
source-device finite checks/copies are not bounded merely by a destination
attribute. Complete expanded CUDA source-prefix coverage is a separate producer
inventory obligation, not evidence supplied by a passing CPU C1 component test.
Conditional future raw native routes need their producer-owned retained scope
and exact uncertainty mechanism; C1 neither enables nor removes raw/manual APIs.

## First producer APP-C1: exact proposed additive runtime/BANK custody contract

Implement and qualify **retained runtime/BANK exclusion plus authenticated
operation binding for existing non-cohort operations**, before adding POP's
active wrapper. This is useful source integration, not a standalone unused
health flag. The new names below are proposed APIs for independent review;
they are not claims of current callables. Existing method signatures can remain
unchanged because the new capability is an explicit retained owner context,
not a backwards-compatibility mode or implicit lookup of ambient lineage.

Public runtime API:

* `ExplorationRuntime.retain_parent_custody() -> ContextManager[RuntimeParentCustody]`.
  Entry uses actual `domain.admission(lineage=None)` BEFORE runtime RLock and
  then BANK retained RLock. It therefore enters only while operation-idle;
  parent calls it after earlier approved replay/POP/ENV custody and before
  entering its active invocation. It yields an opaque issuer-authenticated
  scope, not lineage, registration authority, inventory or recovery permission.
* `RuntimeParentCustody.bind_operation(*, operation: RNGOperation) -> ContextManager[None]`.
  Caller enters its actual registered parent invocation inside retained scope,
  then passes its yielded genuine operation here. Authenticate using public
  `domain.admission(lineage=operation)`; never read core private active state.
  Bind exact runtime/BANK/scope/thread/PID and operation for the lexical body.
  No caller-supplied callback/route policy or fabricated parent marker exists.
  Clear operation binding on all exits; retain locks until outer scope exits.

BANK-facing implementation interface, also an explicit producer context:
`CuriosityBank.retain_parent_custody() -> ContextManager[BankParentCustody]` and
`BankParentCustody.bind_operation(*, operation: RNGOperation) -> ContextManager[None]`.
Runtime retains its own BANK's returned identity internally and binds it along
with its own scope. BANK direct controllers may use the same finite interface;
ordinary callers cannot construct/copy/serialize scopes or borrow private locks.
One scope per actual owner; simultaneous/nested retention on that owner refuses.
Weak issuer registries or equivalent finite owner-held identity records must
release all references at scope exit. Wrong-thread/PID/expired/unissued/reentered
use refuses before waiting on owner locks or running callbacks. Thread identity
is the actual Thread object; PID is checked before lock/CUDA work.
This immediate refusal concerns misuse of the scope handle. An ordinary method
on another thread still waits at common admission; it must neither adopt that
thread's retained binding nor fail merely because a legitimate owner is busy.
Partial scope entry releases exactly acquired locks/pins; all bindings expire
on error as well as success, without suppressing the primary exception.

Retained locks are separate from `_operation_active`/`_entered`. Retention alone
sets neither per-method active flag. Actual method entry still sets/checks its
existing flag and preserves every current revision/view/receipt/phase guard.
Runtime ordinary decorators now enter common admission(None) BEFORE runtime
lock; within an explicitly bound scope they reuse that authenticated operation
through admission(operation) and then the already-held locks. BANK _admission
likewise selects ONLY its own live explicitly bound scope operation, or explicit
None for genuinely standalone entry; it never adopts ambient domain state.
An unbound retained scope cannot run decorated methods: refuse before effects,
preventing accidental unrelated operation/token changes during the idle window.

For supported BANK calls, move actual owner lock lifetime outside invocation
exit while keeping outer common admission before it. Use a fresh existing
device_invocation and entered flag; consume its own sealed outcome under BANK
exclusion before releasing it. Completion True sets a monotonic BANK uncertainty
latch through a non-CUDA/callback-free assignment, retaining existing body-error
latches. False does not heal them. Standalone ordinary healthy restore remains
available under its existing contract; the new completion latch cannot be reset
by existing restore `_failed=False`. Poison already blocks normal work, but
owner outcome attribution is explicit for the new ancestor capability.

Runtime has no separate RNG participant today; C1 need not invent one merely
to retain its lock or relay lineage. POP remains consumer of its own later
outer completion. C1 does NOT automatically mark BANK/native uncertainty after
parent True with copied child outputs; no parent-facing quarantine API is added.
Own BANK device membership/current-device behavior must follow the current
source-defined inventory, without importing replay's fixed18 local contracts.
Empty CPU scope invokes no CUDA attribute.
Exact BANK supplier clarification resolves the C1 invocation argument:
`self._devices: tuple[int, ...]` is set once at BANK325–330 to () for CPU or
(explicit device.index,) for CUDA, after the constructor's selector checks;
the same tuple is registered333–335 for call/prepare/install. No later assignment
or enrollment exists in that body. Replacement cohorts use it1133/1137/1141;
restore copies the owner's dictionary1370 and does not replace device/_devices/
participant/lock before the swap1411. Thus the BANK producer can pass its OWN
`self._devices` into device_invocation as the exact existing full-member
equivalent, without exposing a getter or reading another producer's private
participant inventory. Descendant admitted native tuples still join the real
outer union. This preserves existing declared inventory; it does not certify
foreign-device rejected-prefix, callback-return or newly expanded CUDA routes.
Do not add a guessed native inventory accessor to C1 just to make that claim.

Supported bound methods are the existing non-cohort operations: runtime epsilon/
epsilon_tensor/select_actions, begin_episode, prepare_step_stamp, reward,
admit_and_service, prepare_completion, commit_completion, empty evidence,
quarantine_episode, snapshot_world, checkpoint_state, commit_batch_episode;
BANK counterparts use the same real methods and semantics. Parent callbacks
execute under existing active flags, so peer callback reentry still refuses;
epsilon's existing harmless read remains permitted. C1 authenticates runtime/
BANK reuse; POP/ENV callback lock reuse is a later producer/parent obligation.

`prepare_restore` and `prepare_private_initialization` deliberately leave
admission to register cohorts at idle today. They must remain fully usable
standalone after C1. Inside a bound active parent scope they must explicitly
refuse BEFORE copies/reports/callbacks/registration until the separate idle
cohort protocol is implemented. `install_restore` under bound scope is likewise
not enabled in C1 until its authentic prepared token/publication contract is
reviewed; existing standalone install remains unchanged and tested. These
nested routes do not work today; defining this boundary removes no supported
capability. No fallback, automatic reprepare, or invented recovery is added.

## APP-C1 files, growth and acceptance

Fresh writer AND independent reviewer must use the following complete-body
budget (this planner already has different four bodies and is not that writer):

| File | Current | Maximum after change |
| --- | ---: | ---: |
| src/townlet/config/exploration_policy.py | 1299 | 1600 |
| src/townlet/exploration/scoped_curiosity.py | 1414 | 1750 |
| src/townlet/exploration/parent_custody.py (new proposed concrete scope types) | 0 | 300 |
| tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py (new) | 0 | 900 |
| TOTAL | 2713 | 4550 / four |

450 lines contingency remains; core/native/CP/ENV/POP/test fixtures are supplied
as sealed contracts, not extra bodies. Reading existing test_bank_rng_custody1468
would break this budget and is forbidden without a fresh split. Consume genuine
fixture API capsules or obtain a narrowly bounded fixture supplier before test
authoring; do not copy helper implementations or synthesize positive authority.
The existing hash-matching POP fixture capsule supplies a usable component
route: real make_parent/enter earns actual accepted episode, rig.candidate()
supplies actual tensors, public POP.prepare_vector_step issues the handle, and
real ENV.step(actions, vector_step=handle) earns the context/stamp/handoff for
one runtime.admit_and_service. Retain runtime/BANK scope and a genuine registered
test-controller invocation across this component sequence. This demonstrates
producer composition without calling the still-unmigrated POP learning sample;
label it a component controller test, never full POP step/runner qualification.
Any discovered absent fixture argument is a supplier question, not permission
to fabricate tokens, dimensions, actions, ready state or service receipts.
If the concrete scope logic exceeds300 or needs unrelated native files, stop
and split; do not erase supported branches to fit. No source edits granted here.

Finite C1 acceptance, with real instances/operations and causal barriers:

1. Healthy explicit parent operation: retain runtime/BANK, enter genuine parent
   invocation, bind operation, perform real selected BANK reward/service and
   runtime selectors; both actual child and parent complete, flags clear only
   per method, locks remain held until outer consumer has inspected its result.
2. Standalone runtime and direct BANK controls still work; domain admission is
   observed before runtime lock. A contender already seeking runtime cannot
   retain runtime while waiting on a parent-held domain. Test real two-thread
   contention using events/time bounds, not a synthetic asserted order list.
3. Competing runtime/BANK mutation blocks through injected parent completion
   and owner consumer. Exclusion spans the gap between child return and outer
   receipt. No callback, CUDA work or new lock is invoked by the outcome latch.
4. Unbound/expired/forged/copied/wrong-thread/PID scopes and forged/expired
   lineage refuse before body; no raw private field writes in positive setup.
   Preserve unrelated same-thread entry refusal outside explicit binding.
5. Actual accepted/report/issuer/commit/cadence callbacks cannot reenter an
   active runtime/BANK method; genuine callback checks still execute, unchanged
   view/revision checks remain decisive, harmless epsilon remains available.
6. BANK own body E with clean exit versus same E from body and sync: identity
   preserved, only own completion True sets the new completion latch; clean
   body policy remains as currently justified. Distinct error aggregation kept.
7. Child False then parent True with copied reward results leaves BANK-local
   health unchanged; child True then own-parent False retains BANK uncertainty.
   Isolated poison cases require fresh root-qualified children, never reset.
8. All five families/shared+per_world retain genuine continuation/clock/retry/
   inactive-owner semantics. Existing standalone restore/private-init/install
   and source-hash-matched regression suites must pass; bound cohort attempts
   refuse before first effect without changing ordinary capability.
9. Empty CPU and no-work scope/refusal make zero CUDA calls; actual device
   inventory/completion tests preserve source devices and current producer rules.

Parent's accepted ten schedules remain the later integration acceptance, not
automatically satisfied by C1. New C1 nodes/child roles must be sealed after
fixture-healthy RED; root owns runtime, fresh-source provenance and independent
review. No existing test count is relabeled as this new contract's evidence.

## Dependency-coherent remaining APP sequence

1. C1 above: runtime/BANK domain order, retained scope and authentic operation
   binding. Native-owner API and BANK declared-inventory capsules are now
   supplied; no new native body read/getter is required for that replacement.
2. C2 ENV genuine exclusion/callback custody (ENV2889 + concrete helper<=450 +
   focused test<=1000 =4339/three). Bind actual POP/ENV roles; cover actual step,
   reset/participation, claim and empty-abandon callbacks. No mutex borrowed from
   synchronous flags. Finite concrete API requires its own producer proposal.
3. C3 idle constructor/cohort protocol: preserve actual BANK prepare-examine ->
   idle register -> revalidate -> stage/seal, and POP replay offside destination.
   Native1361 + CP1158 + BANK<=1750 =4269/three leaves731 for a focused helper/
   test only if remeasured and explicitly reserved. This is not a grant to load
   all three plus existing large tests. Establish exact source semantics first.
4. P1 actual POP constructor and selector/flat-PER step integration, full public
   health refusal inventory from V1; vectorized<=3500 + boundary<=350 + tests
   <=750 =4600/three. Registration occurs idle, constructor tensor/RNG work under
   genuine owning invocation, body lineage forwarded through explicit scopes.
   Constructor seed/ambient-default device/token buffers/lazy slots all covered.
5. P2 native parent restore/publication and P3 recurrent integration in separate
   bounded packets. Preserve recurrent/raw/manual/custom functionality; obtain
   recurrent storage/return/child inventory rather than extrapolate flat/PER.
6. R1 ordinary DemoRunner assembly and outer publication plus UnifiedServer
   lifecycle: runner1017 + server616 + seed29 + new helper<=500 + focused tests
   <=1500 =3662/five, subject to fresh measurements and source dependencies.
   Inference consumer and recorder/VFS/curriculum helpers remain opaque suppliers
   before claiming cross-thread/cross-owner e2e. No live server needed for causal
   thread/unit harness qualification; hardware/network/server launch not granted.

Final order intended after those concrete producer contracts is common idle
admission and bootstrap/preflight -> sorted replay custody -> POP/ENV custody
in their reviewed callback-safe order -> runtime -> BANK -> relevant managed
native children, with actual invocation/consumer inside all required retained
contexts. Only the domain/replay/runtime/BANK parts are concrete here. Do not
call that provisional full order established while ENV/native/runner edges are
still being integrated. No new all-owner registry/recovery framework is proposed.

Current core outcomes + healthy18 activation + fresh cold proof remain qualified
CPU evidence; R1161001 and separate R11554 unchanged. B/B6, actual parent and
recurrent/runner/hardware, mypy15 and final programme gates remain open.
