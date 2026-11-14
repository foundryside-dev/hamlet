# APP-C2 ENV exclusion and callback contract — proposed v1

2026-11-14. Metadata/design only. This is one finite producer contract for
independent review, **not an APP baton, implementation acceptance, or a completed
parent/CUDA integration claim**. C1 is still under root qualification. Consume
its approved API, not moving source. The concrete C2 slice below adds real ENV
exclusion and explicit parent-operation binding; complete source/inventory and
outer-completion association remain named dependencies in section 8. Those
dependencies must be resolved before claiming ENV completion/publication safety.

## 1. Exact custody and supplied contracts

Read repository AGENTS.md. Sole admitted implementation body, measured and hashed
before inspection: `src/townlet/environment/vectorized_env.py`, **2889 lines**,
SHA256 `e5a447b0e3d45c861e2fd5e3adcde799f80581053a9512f10af1b365509d8409`.
Relevant regions and whole-file public-entry inventory were inspected; no POP,
C1, core, helper or test body was read. No optional second body was admitted.
No runtime/import/Torch/test/hardware, APP edit, Git write, branch/worktree/copy,
deletion, install or access change occurred. Only this proposal and its handoff
are authored. All existing proposal revisions remain unchanged.

Hash-verified prose suppliers in this preparation directory:

| Artifact | SHA256 |
| --- | --- |
| T18e-R0-PARENT-INTEGRATION-PROPOSAL-V2.md | 45801f6d05a751b4fa7458278f2c781290c094eafa267a65479efb34d9c427c6 |
| T18e-R0-PARENT-C1-CONTRACT-INDEPENDENT-REVIEW-v1.md | a8cb7f8d403740f1b938f31734cdf54698779b75911eca4ca95c497290fe760e |
| T18e-R0-PARENT-ENV-RUNTIME-CURRENT-SUPPLIER.md | 02ac16732bb18dd6613c09cf90f2b20850da402c355cd11604f000f3f91b5b33 |
| T18e-R0-PARENT-REPLAY-CURRENT-SUPPLIER.md | f6c48b621acbc26f9198a8e25f71a6f25b29fc4697d8f3e7d0bf77a0154b7b37 |
| T18e-R0-PARENT-BANK-CURRENT-SUPPLIER.md | 4e118f6b65bbfd4bdc9b877624d9ad5abbbeb607e97374a9776b9e33f11165e4 |
| T18e-R0-PARENT-NATIVE-CURRENT-SUPPLIER.md | 7cb54762da2ecffae75091d06725afac71d83097f615cd364fc79ed1f54f0ba9 |
| T18e-R0-POP-FIXTURE-CURRENT-API.md | 41c31db60be7c2d0f7f65d581bbb3587ca5809a593d58ab967639e46c51cb5b8 |
| T18e-R0-PARENT-C1-FIXTURE-SUPPLIER.md | 659332295bd538fae06d264026985dbbaf525d40423abf9b0f60f56aa889776d |
| T18e-R0-PARENT-C1-FIRST-A-ONLY-STEP-FACTS.md | 9ab8e1b919f31aa14f08c6f804ba9d42ac9dc25d1016206436066238e759604c |
| T18e-R0-PARENT-C2-CALLBACK-GUARD-FACTS.md | e1de4d895c218765d6538fc559a9f973e732bd5bb8064a92c93149fdcf7298f3 |

The last capsule supplies POP3163 at `6c4f7ca085f0a7db34f42bebe22f0240ed12825627c13bcffb3c0d3be3f99022`;
it is attributed source evidence, not another body charged to this author.

## 2. Finite public producer interface

Proposed new API, not a claim of current callables:

* `VectorizedHamletEnv.retain_parent_custody() -> ContextManager[EnvParentCustody]`.
  Enter actual common `domain.admission(lineage=None)` before a new ENV RLock.
  Pin this ENV and its exact current role/runtime/callback binding for the lexical
  scope. Entry is idle, before any active parent invocation. Retention itself
  does not set a method-active flag, register participants, issue receipts,
  inspect a private core record or certify completion.
* `EnvParentCustody.bind_operation(*, operation: RNGOperation) -> ContextManager[None]`.
  Authenticate via public `domain.admission(lineage=operation)` and bind exact
  ENV/scope/thread-object/PID/operation for the lexical body. The controller
  enters its genuine operation inside retained scopes, then explicitly binds
  ENV and C1 runtime with the SAME yielded operation. Binding is execution
  authority for finite ENV entry, not proof of sufficient device inventory or
  healthy completion. Clear binding on every exit; retain the ENV lock until
  outer custody exits, including actual outer completion and consumer work.

Scopes are issuer-retained, nonportable, noncopyable and nonserializable. One
retained scope per ENV; wrong owner/thread/PID, unissued/copied/expired/reentered
scope use refuses before owner-lock waits, callbacks or device work. Check PID
before lock work. An ordinary other-thread ENV caller waits at common admission;
it must not adopt another thread's binding or refuse merely because ENV is busy.
An unbound retained scope cannot execute guarded public work. Partial entry
releases only acquired resources; scope exit drops execution references/pins.
Keep authority outside lifecycle checkpoint/prepared data. Reset, restore and
generation advancement must never revive scopes or reset a completion latch.

Ordinary initialized ENV entry takes common admission(None), then ENV exclusion,
then its per-method active guard. Explicitly bound entry uses only the exact
live binding through admission(operation), then already-held ENV exclusion.
No ambient operation lookup, caller route-policy callback, public permit issuer,
or use of `_participation_busy`/pending/POP flags as a mutex. Existing participation,
phase, revision, generation, record/receipt identity and no-change checks remain.

C2 does not add an ENV RNG invocation around ordinary methods merely to acquire
exclusion. Admission is not a completion phase. A standalone ENV.step still
reaches C1's ordinary runtime/BANK methods; a bound controller must explicitly
retain and bind the actual runtime/BANK first. Existing active-parent entry that
has no ENV binding is not silently adopted. This distinction preserves ordinary
component routes while the full parent producer is migrated separately.

## 3. Actual ordering, including callbacks

For the finite bound route use idle common admission -> existing multi-owner
replay preflight/sorted replay locks if required -> future real POP custody if
present -> ENV custody -> C1 runtime custody -> delegated BANK custody -> enter
actual invocation -> bind ENV/runtime -> finite body -> unbind -> actual
invocation exit -> exact owner outcome consumer -> release in reverse order.
Retained contexts encompass the invocation and consumer. For the empty-abandon
route, retain ENV then the genuine curiosity BANK's public DIRECT-controller
custody, skipping runtime custody entirely; bind that BANK and ENV to the same
operation. This is an explicit finite owner set, not a runtime permit bypass.
Future POP ordering is
a required integration constraint, not a claim that current POP has a lock.
Current POP has none. Native locks remain acquired only by their actual producer
calls; ordinary copied native rewards/stamps do not require blanket retention.

Standalone ENV methods establish domain before ENV. Standalone runtime/BANK
callbacks must not acquire a new ENV lock under runtime/BANK. Their existing
accepted-token callback therefore remains a narrow identity check described
below. Neither source call nesting nor RLock reentrancy proves a safe mutex order.
Never add a new POP lock in claim/empty/commit/cadence callbacks. Their later POP
producer must reuse its already-held actual custody. No new lock, domain entry,
CUDA call, receipt issuance, abandonment call or callback belongs in an eventual
completion-failure assignment consumer.

| Real edge and current source | C2 treatment |
| --- | --- |
| ENV.step -> stored POP claim -> ENV accepted validation and, for owned training, participation validation | ENV retains its actual lock. Source-owned claim-call continuation permits only those exact existing checks and exact-current-token fail-closed cleanup; no peer step/reset/restore/activation/close/scope entry. Preserve POP issued PreparedVectorStep registry and all content checks. |
| ENV empty abandonment -> actual activated population empty proof -> ENV accepted validation | Retain ENV. Preserve POP's real idle requirement, zero counts/outcomes/recurrent rows and genuine issuer. No positive close authority follows. |
| ENV empty abandonment -> actual activated curiosity empty proof -> ENV accepted validation | The actual curiosity owner is BANK, not runtime: activation receipt owner is the role-bound curiosity owner. Use the exact BANK's public direct-controller retained scope, with no runtime-delegated scope, for this finite route. C1 delegated permits must not be bypassed. |
| BANK -> ENV accepted validator; runtime -> POP cadence -> ENV accepted validator | Keep exact accepted-token identity check free of lock acquisition/device work. It is not a healthy snapshot, phase proof, completion certificate or permission for other ENV work. Existing actual caller admission plus ENV's domain-first mutation establishes stability on supported producer paths. Raw standalone validation remains only an instantaneous identity check. |
| POP reset -> ENV reset, participation prepare/commit, final reading validation | Sequential intended public operations under the bound ENV scope; no invented POP participation callback. Preserve exact intent/ready issuers and assignment-only paired publication. |
| Runtime -> POP committed-batch validator | No ENV call in this validator. Preserve actual pending-batch/active/content checks; C1 callback policy is unchanged. |
| Claim/empty/owned-state validation failure -> ENV runtime_failure abandonment | Allow only source-established fail-closed cleanup for this exact accepted episode under already-held ENV custody. Never use this as a general nested mutation permission or completion consumer. Preserve primary exception and existing cleanup-note behavior. |
| Controller close -> ENV freeze/close and boundary authority -> release | Sequential controller effects, not a POP.close callback. Require real curriculum/BANK/POP/epsilon/selection effects and their existing owner receipts. |

The claim continuation must be private, lexical and tied to the exact current
ENV method-call identity, stored callback, thread/PID, accepted identity and
retained ENV scope/binding (or genuine ordinary ENV call). It must expire on all
returns/errors. Its allowlist is source-fixed: accepted validation, the actual
participation check, and exact-current-episode runtime_failure cleanup. Those
checks keep their existing argument/currentness validation and do not issue
general owner authority. An arbitrary nested hook must not inherit a flag that
opens every ENV public method. Exact single-call consumption and legitimate
validator multiplicity require review against the supplied POP facts; do not
guess a sequence that rejects the unowned/no-participation route.

ENV's own internal public-to-public calls need source-controlled continuations
or private implementations, not a general reentry flag: reset -> validate
reservation -> prepare_episode; set affordances -> validate affordances; step
-> get_action_masks; checkpoint -> vfs_random_state; constructor/reset ->
randomize_affordance_positions; physics/reset/helper access -> bars. Move these
internal calls to their private implementations where needed. Public callbacks
cannot obtain that private continuation. Constructor-time partial-object access
is not an initialized scope; section 8 retains its actual lifecycle obligation.

## 4. Complete public ingress and publication inventory

Every entry below must have an explicit disposition in writer and reviewer
coverage. No method disappears because it is inconvenient for the first test.

| Public ingress in ENV body | Disposition |
| --- | --- |
| `__init__`, `from_universe` | Establish exclusion storage before any public helper can observe it; source-complete constructor admission/registration/inventory is a separate mandatory dependency. Do not claim end-of-constructor enrollment protected earlier effects. |
| `attach_runtime_registry`, `set_exploration_runtime`, `bind_boundary_authority` | Guard whole binding operation; preserve one-time exploration binding and exact nine role mapping/equal identity rebind. No arbitrary substitute role owners. |
| `install_boundary_release`, `prepare_episode`, `validate_episode_reservation`, `reset` | Guard whole operation and retries; preserve genuine reservation/release/cursor checks and reset quarantine/provisional VFS cleanup. |
| `validate_accepted_episode` | Narrow lock-free exact identity check only, as above; never promote to a healthy attestation. |
| `prepare_initial_participation`, `commit_initial_participation`, `validate_initial_participation`, `validate_initial_participation_reading`, `activate_episode` | Guard entire physical/receipt work; preserve intended finite reverse validation and fail-closed paths. These validators can perform device work/quarantine and are not the identity-only exception. |
| `step`, `get_action_masks` | Whole-method exclusion; retain actual result/live alias custody across bound outer effects. Claim occurs before first ENV write but after clone/observation work; do not equate claim refusal with zero device work. |
| `prepare_episode_close`, `freeze_episode_close`, `close_episode`, `abandon_episode` | Guard whole lifecycle operation. Distinguish genuine empty proofs from runtime-failure cleanup and normal positive closure. |
| `checkpoint_world_state`, `prepare_world_restore`, `install_world_restore`, `vfs_random_state`, `restore_vfs_random_state` | Guard healthy export/prepare/publication; preserve current fresh destination, generation and VFS projection rules. New uncertainty must not be reset by install. Full joint restore/currency remains a later dependency. |
| `get_affordance_positions`, `set_affordance_positions`, `validate_affordance_positions`, `randomize_affordance_positions` | Include validation/copies/RNG and invalid-prefix effects under exclusion; no destination-only CUDA assumption. Internal randomization uses authored Torch/substrate RNG, including default-device randperm/randint. |
| `get_action_label_names`, `world_ids`, `semantic_execution_identity` | Preserve existing metadata API. Pure immutable identity metadata grants neither mutable-storage custody nor healthy-state authority. Check actual returned object ownership before advertising it as immutable. |
| `accepted_episode_seqs`, `world_phase` | Current diagnostic/identity readings; use an explicit locked external read/private internal read policy. Never turn a phase string into completion authority. |
| `bars` and public tensor/helper attributes | Existing raw cooperative surface remains supported. `bars` returns meter views; raw `positions`, `meters`, `dones`, etc. are not intercepted by method guards. Guarded getter entry cannot protect a later escaped alias. Actual manual/raw use needs explicit retained custody and inventoried effect ownership; preserve capability, do not advertise automatic alias safety. |
| `WorldBoundaryAuthority.bootstrap/completed/prepare_initial_snapshot/restored` | Each complete method runs under its bound ENV guard; `_bound_env` alone is too short. Preserve exact authority identity and actual role receipt validation. They issue real healthy lifecycle authority, so cannot bypass applicable uncertainty refusal. |
| `WorldReceiptIssuer.issue/validate`, `owner` | Generic cooperative identity machinery, not ENV lock acquisition or proof that a role effect happened. Do not alter all issuers globally to manufacture ENV custody. |

Nine actual roles remain population, curiosity, curriculum, exploration, network,
optimizer, scheduler, replay and selection. Fixture binding uses actual POP,
BANK, curriculum, runtime, Q, optimizer, real scheduler-or-POP, replay and runtime.
Receipt kind/owner/issuer identity/generation checks remain decisive. Do not
invent a controller token or mark arbitrary equal objects as role authority.

## 5. Healthy publication and uncertainty boundary

Current ENV reset/install already quarantine guarded body mutation failures;
participation has finer prepare/invalidate/publish rules. Step has no uniform
outer quarantine and returns live `dones`, intrinsic weights and reward component
references. Those are actual ENV-owned reachability, unlike ordinary copied
native rewards/stamps and typed replay batches. Preserve that distinction.

C2 retention/binding alone does NOT certify ordinary ENV completion, raw alias
effects or a parent result. Required eventual consumer: under retained ENV
exclusion, read the exact actually-entered completing invocation's sealed outcome
in unconditional finally; True sets a monotonic ENV uncertainty latch by local
assignment only for the source-established ENV effects/live storage it covers.
False never heals body/participation/restore failure. Healthy mutation,
activation/release/close, export and restore authority must refuse that latch;
diagnostic phase/identity readings remain explicitly nonhealthy. No blanket
BANK/native/replay/other-world latch follows from ENV or parent failure.

Do not implement `mark_uncertain(operation, arbitrary_receipt)` or trust a
caller-supplied bool. A genuine receipt can belong to the wrong owner or an
insufficient inventory. An initially considered `scope.invoke(invocation=...)`
would associate one entered handle with this lexical window, but **would not
authenticate its participant, truthful inventory or designated ENV effects**.
That API is therefore NOT included in this finite C2 interface. The supplied
public core API offers no general public inspector proving those associations;
do not inspect private core records to create one.

The consumer must instead be placed by a later source-controlled producer owning
the actual invocation/inventory and ENV effect plan, with its concrete public
handoff independently reviewed. Until that dependency is sealed, C2 acceptance
is exclusion/callback composition only, not completed ENV completion-health
integration. Existing runtime_failure abandonment is preserved as body cleanup;
it is neither the new assignment-only consumer nor a poison-recovery API.

## 6. Genuine acceptance cases and limits

All are prospective. Use existing fixtures by supplied API; no fake tensors,
private flags, copied authority, fabricated readiness/events or duplicate claim.

1. Real `make_parent(compiled, family, scope)` and genuine activation; retain
   ENV then C1 runtime/BANK, enter registered component-controller operation,
   bind both, run actual ENV.step with `rig.candidate()` and actual
   POP.prepare_vector_step. ENV performs the only claim. Observe actual returned
   handoff and runtime reward/service identities. This is component composition,
   not completed POP progress, learner or runner qualification.
2. Same real ordinary route without explicit parent scope succeeds. Two-thread
   barriers show a competing ENV reset/read/mutation cannot hold ENV while
   waiting for domain and cannot pass the retained post-child/outer-exit/consumer
   window. Other-thread C1/BANK work waits normally. Trace actual exclusions,
   not a test-authored list of lock names.
3. Real claim -> ENV participation validation succeeds. Callback attempts at
   peer step/reset/restore/activation/close/scope entry refuse before their work.
   Genuine owned-state failure can abandon current episode without reopening
   work; original error survives. Forged/stale claim retains existing refusal.
4. Genuine `begin(rig, retired=IDS)` obtains whole retirement. Real ENV empty
   abandonment obtains POP then actual BANK proofs. Test both standalone and
   parent-bound composition using the actual BANK's DIRECT retained scope,
   not runtime delegation. No positive close,
   batch advance or normal release is manufactured from empty proofs.
5. A fresh nonrecurrent A-only first `population.step_population(env)` earns
   one real replay row, stays below genuine readiness2, and supports real
   `prepare_close/close`. This is the supplied positive no-learning route, not
   the ENV-only component route. Preserve real curriculum/BANK/POP commits,
   epsilon synchronization, five effect receipts, closure and release. Fresh
   rigs are required for independent controls: second A-only step can hit the
   still-unmigrated sample. No hidden threshold change is allowed.
6. Real reset/participation/activation, identical retry, changed-retirement
   refusal, empty cleanup, positive close/release/next reset and standalone
   restore retain semantics. Probe boundary-authority entry too. Standalone
   cadence/accepted callbacks continue without fresh ENV locks under BANK.
7. Wrong owner/thread/PID, unbound/expired/forged/copied scopes, unrelated
   same-thread work, failed partial entry and callback exception cleanup are
   causal refusals. No authority survives reset/restore or lexical exit.
8. Once the consumer/inventory dependency is implemented: exact body exception
   E plus clean completion versus same E also raised by sync, child False/outer
   True and child True/outer False; source-proven ENV health assignment before
   unlock, no callbacks/CUDA/new locks, no False healing. Poison cases run in
   fresh root-qualified children. This is REQUIRED later evidence, not a C2
   exclusion test renamed completion proof.
9. Preserve all selected none/count/RND/adaptive/ICM shared/per_world routes and
   existing manual/raw/recurrent/GPU capability. CPU cases establish causal
   control flow only. Actual CUDA source/destination/rejected-prefix inventory,
   asynchronous completion, recurrent learning and runner publication require
   their named later packets; no skipped profile becomes optional.

## 7. Bounded file and review budget

Root accepted this growth reservation as a planning budget, not implementation
authorization. A fresh writer AND reviewer remeasure full bodies before work.

| Body | Current | Projected maximum |
| --- | ---: | ---: |
| src/townlet/environment/vectorized_env.py | 2889 | 3350 |
| src/townlet/environment/parent_custody.py (new concrete helper) | 0 | 450 |
| tests/test_townlet/regressions/bac/test_environment_parent_custody.py (new) | 0 | 1000 |
| TOTAL | 2889 | 4800 / three bodies |

200 lines remain below the packet ceiling; five files/5000 is a hard full-body
ceiling, not permission to add an unmeasured body. The earlier 4339 arithmetic
did not reserve ENV growth. No C1/POP/core/helper/fixture body may be smuggled into
this packet. Use sealed supplier APIs and root-run external suites. If callback
or inventory resolution needs another producer edit/body, split coherently at
root; never delete required behavior to fit. No tests or executable probes have
been authored by this preparation worker.

## 8. Specific resolution questions and mandatory next dependencies

1. **Actual BANK empty-proof route — selected finite composition for review:**
   `_world_consumers[1]` is the genuine BANK from its activation receipt. ENV
   calls it directly. Retain this actual role owner's public direct BANK scope
   after ENV, without runtime retention/delegation, and bind both to the same
   operation. The fixture exposes the actual BANK; the controller already owns
   its genuine nine-role binding and receipts. Do not infer BANK identity from
   a private runtime field. Review this route-specific owner set explicitly.
   Empty abandonment inside an already runtime-delegated scope is NOT enabled
   by C2; its later alternative requires source-controlled runtime forwarding
   and a genuine pre-call runtime/BANK identity association. Existing standalone
   empty behavior remains supported. A wrong mixed scope may reach POP proof
   before BANK refuses, so do not claim that composition is a no-effect refusal.
2. **Finite callback authentication:** review the claim-call continuation against
   real owned and unowned paths and transparent callback observers. Preserve
   the public callable binding surface without pretending every callable is
   POP. An immutable list of allowed method names alone is not caller identity;
   bind actual source-owned dynamic continuation/current ENV call and exact
   existing episode/participation authorities. No blanket callback exception.
3. **Completion association/inventory:** which separately bounded producer owns
   actual ENV invocation and truthful source/destination/rejected-prefix plan,
   and the exact non-CUDA consumer handoff? ENV's configured device is not a
   complete inventory: actions clone before claim; participation reads external
   predecessor; reset/randomization use substrate/helpers and default-device
   Torch allocations; helper/hook results may introduce sources. Root must
   obtain finite helper/constructor facts before claiming coverage. Do not add
   an arbitrary-invocation API as a shortcut. C2 exclusion may proceed only
   with this explicit incomplete-completion scope and independent design review.
4. **Later real POP/runner and idle cohort protocol:** POP needs actual lock,
   participant/inventory, constructor staging, full public/manual/recurrent and
   checkpoint paths, finite callback reuse and outer result consumer. Runner
   post-POP telemetry/statistics/checkpoint effects retain their own final cut.
   C1 bound restore/cohort remains intentionally unsupported pending its idle
   registration protocol; standalone behavior remains supported. These are
   mandatory sequential dependencies, not optional hardening.

Next action is independent bounded contract review after root resolves the
selected empty-proof route and callback continuation policy. Only then may root
assign a sole C2 APP writer after C1 qualification. No gate is closed here.
