# Parent ENV/runtime current-source supplier

2026-11-14. Read-only bounded source supply for `/root/bac_astra_parent_integration_prepare`; implementation, execution and qualification remain frozen/root-owned. Repository `/workspace/hamlet`, observed HEAD `2f579092eae2b67eb3efd514aa7b61c909efa9f1`. Read `AGENTS.md`; no source edits, tests, application imports, runtime, branches/worktrees/copies, Git writes or deletions. Sole write is this preparation capsule.

## Source custody and limits

Whole-file costs were measured before admitting each body. Three implementation bodies charged in full, 4,322 lines total; 678 lines/two bodies remain unused. Relevant regions and whole-file structural searches were inspected; this is not a claim to review every unrelated simulator implementation. No implementation body is smuggled through a prose capsule.

| Body | Whole lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/environment/vectorized_env.py` | 2889 | `e5a447b0e3d45c861e2fd5e3adcde799f80581053a9512f10af1b365509d8409` |
| `src/townlet/population/runtime_registry.py` | 134 | `1425748c6abbb01aff170be023547f5a5c11eb35c92d29ea416bbf848b461f50` |
| `src/townlet/config/exploration_policy.py` | 1299 | `fbda6a2178e794747ef1e9b7771d450463051aeba53a598dd40fc334c2754e67` |

The reserved `runtime_registry.py` is telemetry, not the epsilon/cadence runtime. ENV imports `ExplorationRuntime` from the third body, which was added after measuring its 1,299 lines. No POP, core, BANK, CP, runner, replay, reward-calculator, factory or validator implementation was opened. BANK metadata only: current `scoped_curiosity.py` is 1,414 lines, SHA256 `3b9b5476530317fc48991ba096545e3e2bad3593deb92d9caeb3a3bbab6e1027`; it does not fit this packet's remaining allowance.

Read parent proposal `T18e-R0-PARENT-OUTER-COMPLETION-CONSUMER-PROPOSAL.md`, SHA256 `ba6128eb2fa12df3cdf2fddad402e8c8a9a99ad36314776c80a75a3ae0d7eab6`, and peer review `T18e-R0-PARENT-OUTER-COMPLETION-CONSUMER-PEER-REVIEW.md`, SHA256 `f8abc8c88a7aa24f17a88bb4c3c45f0ce1504ed7be626d36fb565bd57a0099e6`. Their outer completion/health design is prospective; neither supplies the absent custody interface described below.

## Decision-ready facts

1. ENV has **no owner mutex, domain admission, lineage argument or public retained-exclusion scope** in this body. Its `_participation_ingress` explicitly says “Synchronous cooperative fence, not an inter-thread lock” (2258). The fence tests `_participation_busy` or pending participation; those private flags must not become a public parent lock API.
2. ExplorationRuntime does have a private `RLock`. Every decorated public operation holds it for the entire method and rejects same-thread operation reentry using `_operation_active` (755–766). The only explicitly permitted reentrant observation is `epsilon`, which acquires the RLock but does not test the operation flag (867–871). No public retained runtime lock/custody capability, parent-scope token, lineage argument, or completion-uncertainty transition exists in this body.
3. Runtime calls parent commit/cadence validators while holding its RLock. ENV calls the parent vector-step claim with no ENV mutex. Adding a blanket POP lock around existing callbacks can introduce a cycle; there is no source-established total lock order to copy from these bodies.
4. Runtime enters every BANK forwarding operation while already holding runtime's RLock. The current BANK report attributes domain-before-BANK admission to its source. On that attributed contract the existing path is runtime-lock → domain admission → BANK lock. A new parent domain → runtime-lock path needs an explicit integration change; simply naming domain-first order does not make the old ordinary entry obey it.
5. No ordinary runner implementation was inspected. A local POP/ENV return does not prove it is the final effect owner or the final healthy publication boundary.

## ENV public authority and lifetime

`WorldReceiptIssuer(*, owner: object)` owns a weak identity registry; `issue(*, kind: str, payload: Mapping[str, Any]) -> WorldOwnerReceipt` freezes payload and retains issued identity. `WorldReceiptIssuer.validate(receipt: Any, kind: str, owner: object) -> WorldOwnerReceipt` requires actual receipt type, actual issuer, exact retained receipt identity, kind and owner identity (93–119). These receipts authenticate cooperative ownership; they do not acquire locks or grant a general caller-defined reentry exemption.

`set_exploration_runtime(*, exploration: ExplorationRuntime, claim_vector_step: Callable[..., int]) -> None` binds those exact references once in `fresh-unbound`; even equal rebinding refuses (616–625). It checks the actual runtime class and callable but does not authenticate the claim's bound method/parent identity or establish exclusion. `attach_runtime_registry(registry: AgentRuntimeRegistry) -> None` likewise only checks participation ingress and assigns the reference (611–614).

`bind_boundary_authority(*, owner: object, role_owners: Mapping[str, object]) -> WorldBoundaryAuthority` requires the exact nine role names, non-None owners, and fresh phase; an equal identity rebind returns the existing authority (2116–2130). The roles are population, curiosity, curriculum, exploration, network, optimizer, scheduler, replay and selection. The authority remains bound by exact object identity; manually constructing another authority does not satisfy `_bound_env`. Its public methods are:

- `bootstrap(*, first_batch_episode: int) -> WorldRecord`.
- `completed(*, closure: WorldRecord, effects: WorldOwnerReceipt) -> WorldRecord`.
- `prepare_initial_snapshot(*, release: WorldRecord, owners: WorldOwnerReceipt) -> WorldRecord`.
- `restored(*, restore: WorldRecord, boundary: WorldOwnerReceipt) -> WorldRecord`.

These validate phase/current closure/actual role receipts and issue release/snapshot records (121–237). They do not retain exclusion across caller work. ENV's `_valid_record` requires actual type, kind, owner, current generation and exact weak-registry identity (2091–2099). Reset/restore advance generation; an equal serialized value is not a substitute for the current issued capability.

Parent-facing reset/activation and participation signatures:

- `install_boundary_release(release: WorldRecord) -> WorldRecord` (2132).
- `prepare_episode(*, batch_episode: int, release: WorldRecord) -> WorldEpisodeReservation` (2154).
- `validate_episode_reservation(reservation: WorldEpisodeReservation) -> None` (2170).
- `reset(*, reservation: WorldEpisodeReservation) -> WorldRecord` (2187).
- `validate_accepted_episode(*, accepted: WorldAcceptedEpisode) -> None` (2254).
- `prepare_initial_participation(*, accepted: WorldAcceptedEpisode, intent: WorldOwnerReceipt) -> WorldRecord` (2340).
- `commit_initial_participation(*, prepared: WorldRecord, population_ready: WorldOwnerReceipt) -> WorldRecord` (2453).
- `validate_initial_participation(*, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor) -> None` (2594).
- `validate_initial_participation_reading(*, accepted: WorldAcceptedEpisode, participation: WorldRecord, predecessor: torch.Tensor) -> None` (2601).
- `activate_episode(*, accepted: WorldAcceptedEpisode, population_receipt: WorldOwnerReceipt, curiosity_receipt: WorldOwnerReceipt) -> WorldRecord` (2626).

`validate_accepted_episode` checks only exact current accepted-token identity and explicitly leaves phase checks to callers. It acquires no lock and does not call `_participation_ingress`. The initial-participation validators additionally enforce their fixed phase policies and exact committed physical reading; their private busy fence is synchronous, with no held mutex. Mutation/failure checks can quarantine ENV, so these validators are not automatically side-effect-free diagnostics.

Reset validates reservation/release/cursors, sets phase `resetting`, mutates physical ENV state and increments generation before returning a reset record/current accepted token in `active-awaiting-activation`. Any BaseException in that guarded body sets `quarantined`; provisional VFS context clears in `finally` (2187–2248). Exact duplicate reset returns the retained record only in allowed later phases. `_reset_world_state` (955–1045) includes device tensor allocation/mutation and substrate position initialization with `generator=None`; neither that call nor the owner flag certifies completion of asynchronous CUDA. No runtime parent validator is directly called by reset in this body. Helper internals remain uninspected.

Participation preparation retains exact intent, accepted/reset/reservation/generation/revision and owned physical readings. Pending preparation fences other cooperative ingress. Commit validates actual population-ready receipt and exact retained preparation, performs fallible checks/copies before assignment, then publishes dones/committed state/revision without another callback. Before-publication failures invalidate preparation with physical checks; publishing failures quarantine (2340–2540). This existing discipline cannot be reused as a general parent completion-health latch.

## ENV step and reverse callbacks

`step(actions: torch.Tensor, depletion_multiplier: float = 1.0, *, vector_step: PreparedVectorStep) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]` (1277).

After ingress/active-phase/current accepted/participation checks it clones predecessor, actions and active mask. Before the first ENV state write it invokes the stored parent callback exactly as:

`claim_vector_step(prepared=vector_step, accepted=accepted, world_ids=self.world_ids, predecessor=predecessor, actions=actions, active_on_entry=active_on_entry) -> vector_tick` (1318–1325).

**ENV holds no mutex at this callback.** There is no overall step-busy flag in this method. The callback may perform fail-closed cleanup; ENV rechecks active phase, accepted identity and participation immediately afterward, before incrementing revision and running physics (1326–1333). POP's own locks and callback authentication must be supplied by POP's owner; this file cannot establish them. An ordinary claim exception occurs before ENV's first state write, although prior observation/clone device work has already occurred.

After physics/tick/status writes, ENV invokes runtime `prepare_step_stamp(accepted=accepted, world_ids=self.world_ids, active_on_entry=active_on_entry, vector_tick=vector_tick)` (1416–1421), and calls its reward-calculator helper with the current context/stamp/accepted. The helper's internals are outside this packet. Runtime entry takes runtime's lock. The returned observation/rewards/dones/info are assembled only after these effects; `self.dones`, intrinsic weights and reward components can be live aliases. ENV step has no outer catch that uniformly quarantines every exception and no CUDA invocation-outcome consumer. Do not strengthen reset's failure rule into an invented step rule.

`abandon_episode(*, accepted: WorldAcceptedEpisode, reason: str) -> WorldRecord` (2723) supports exactly `empty_participation` and `runtime_failure`. Runtime-failure cleanup has a deliberate path through the participation fence to quarantine a current accepted episode. Empty abandonment verifies no participated step and then calls each actual activated consumer's `prepare_empty_episode_evidence(accepted=accepted)` in stored order: population then curiosity (2743–2751). **No ENV mutex is held**; evidence is validated against each exact owner. This is a second authentic ENV→POP/BANK-facing callback edge. Do not blanket-refuse this existing failure cleanup when designing guarded healthy entrypoints.

Closure/restore/export APIs requiring inclusion in any future finite custody coverage are `prepare_episode_close(*, accepted, boundary_key, completion_content, participated_world_ids, dispositions) -> WorldRecord`, `freeze_episode_close(prepared: WorldRecord) -> WorldRecord`, `close_episode(prepared: WorldRecord, *, dispositions: WorldOwnerReceipt) -> WorldRecord`, `checkpoint_world_state(*, kind: str, release: WorldRecord, retained_binding_batches: tuple[int, ...], initial: WorldRecord | None) -> dict[str, Any]`, `prepare_world_restore(*, kind: str, state: Mapping[str, Any], world_roster: WorldRosterDeclaration, destination_world_ids: tuple[str, ...], semantic_execution_identity: str) -> WorldRecord`, and `install_world_restore(*, prepared: WorldRecord, release: WorldRecord) -> WorldRecord` (2645–2889). No method has a lineage/custody parameter. Restore installation quarantines on guarded mutation failure. `vfs_random_state() -> dict[str, Any]` refuses resetting/restoring/quarantined phases; `restore_vfs_random_state(state: Mapping[str, Any]) -> None` validates only the actual current projection in its allowed stable phases (1568–1581).

## ExplorationRuntime lock, callbacks and failure ownership

Exact constructor (810–820): `ExplorationRuntime(*, policy: ResolvedExplorationPolicy, descriptor: Any, device: torch.device | str, validate_accepted_episode: Callable[..., None], issuer_factory: Callable[..., Any], report_allocation: Callable[..., None], validate_committed_batch: Callable[..., None], validate_parent_cadence: Callable[..., None])`. `build_exploration` (1280) takes the same keyword arguments and returns `ExplorationRuntime`.

Construction creates private RLock, sets `_operation_active=True`, initializes BANK with accepted validator/issuer/report, creates selector/cadence, then clears the flag in `finally`. **The constructor does not hold that RLock while calling BANK or its callbacks.** Partial construction callback reentry is not a supported initialized public scope; `_state` may not yet exist.

`_runtime_operation` acquires runtime RLock, rejects active operation, sets active, calls the whole method, and clears active in `finally`. Lock releases on return/error. It does not itself mark runtime health uncertain, perform CUDA completion or preserve a retained exclusion after return. The RLock prevents another cooperating thread entering decorated runtime work; the active flag rejects same-thread callback reentry into decorated methods even though the lock itself is reentrant. `epsilon` is the sole harmless reentrant property and returns selector epsilon without BANK access.

Decorated selector APIs: `epsilon_tensor(*, batch_size: int, device: torch.device | str) -> Tensor`; `select_actions(q_values: Tensor, agent_states: Any, action_masks: Tensor | None) -> Tensor` (879–950). Selection validates actual state/geometry, creates an epsilon tensor, invokes selector, and invalidates runtime revision/restore handles in `finally` around selector work because RNG may already have been consumed on error. Empty selection returns before that selector/invalidation block. Neither API exposes custody/lineage or quarantines based on an outer completion outcome.

Decorated BANK forwarders, all under runtime lock (952–1006):

- `begin_episode(*, accepted: Any) -> Any`.
- `prepare_step_stamp(*, accepted: Any, world_ids: tuple[str, ...], active_on_entry: Tensor, vector_tick: int) -> Any`.
- `reward(*, context: IntrinsicTransitionContext, stamp: Any, accepted: Any, update_stats: bool) -> Any`.
- `admit_and_service(*, context: IntrinsicTransitionContext, stamp: Any, accepted: Any) -> Any`.
- `prepare_completion(*, accepted: Any, boundary_key: int, completion_content: Any, outcomes: tuple[Any, ...], participated_world_ids: tuple[str, ...]) -> Any`.
- `commit_completion(*, prepared: Any) -> Any`.
- `prepare_empty_episode_evidence(*, accepted: Any) -> Any`.
- `quarantine_episode(*, accepted: Any, reason: str) -> None`.
- `snapshot_world(*, world_id: str) -> dict[str, Any]`.

`_bank_call` observes BANK mutation revision before/after and invalidates runtime revision/retained restore handles if BANK changed, including on exception (859–865). It forwards exactly the listed keyword arguments through `getattr(self._bank, method)(**kwargs)`. **Runtime neither accepts nor forwards a `lineage` argument on these current public methods.** The prepare/initialization wrappers likewise forward their listed state/mode/accepted/parent-restore fields only, and final install calls `self._bank.install_restore(prepared=publication.bank_handle)` without lineage. How current BANK admits these ordinary calls, and whether an ancestor operation can lawfully contain them, must be supplied by BANK. This establishes runtime forwarding/invalidation behavior only; it does not independently prove BANK callback/lock semantics. `quarantine_episode` is the existing exact BANK episode operation, not an authenticated new parent-triggered CUDA-uncertainty API. A public parent has no legal public API here to hold runtime's RLock across calls; direct `_lock` access would create a private-field dependency, not authenticate custody.

`commit_batch_episode(*, batch_episode: int, outcomes: tuple[Any, ...]) -> None` (1027): runtime lock and active flag remain held through allocation reporting, deepcopy/canonicalization and `validate_committed_batch(batch_episode=batch_episode, outcomes=view)`. Validator must return None; supplied view must remain canonically unchanged; runtime and BANK revisions must remain equal. An equal committed batch/content is a no-op retry; a new accepted commit changes selector epsilon, cadence and revision. Callback runs **before** publication. No BANK operation scope is retained around the direct parent callback by this method; external caller-held scopes cannot be inferred here. Runtime callback reentry into any decorated API refuses; epsilon observation is permitted. Parent callback must not assume it can call runtime snapshot/selector to authenticate itself.

`prepare_restore(*, state: Any, mode: str, accepted: Any, parent_restore: Any, validate_parent_restore: Any) -> PreparedExplorationRestore` (1204) and `prepare_private_initialization(*, state: Any, initialization: str, parent_restore: Any, validate_parent_restore: Any) -> PreparedExplorationRestore` (1231) hold runtime lock while reporting/copying, invoking cadence validator, forwarding preparation/parent-restore validator to BANK, and retaining a newly allocated opaque handle. Direct cadence invocation is exactly `validate_parent_cadence(cadence=view, mode=mode, accepted=accepted, parent_restore=parent_restore)` (1157), with None-return, unchanged owned view and revision checks. `_retain` invokes it again before storing the handle. `validate_parent_restore` timing/arguments inside BANK require the BANK supplier; runtime merely forwards it.

`PreparedExplorationRestore` has empty slots; constructing an object is not authority. `install_restore(*, prepared: PreparedExplorationRestore) -> None` (1261) requires exact class and membership in this runtime's retained dictionary, rechecks runtime/BANK revisions and cadence callback under runtime lock, then calls BANK install. After successful BANK return it publishes preallocated runtime state/revision/empty-handle dictionary, with no further callback/loader/allocation/check in this method. Handles are receiver-bound, staled/cleared by invalidation and consumed by installation. They are publication capabilities, not retained exclusion or general owner-health tokens. A BANK install exception prevents those final runtime assignments; the runtime does not add a separate general uncertainty latch in this body. BANK's publication/exit failure policy remains BANK-owned.

`checkpoint_state() -> dict[str, Any]` (1163) holds runtime lock through selector/cadence copies and BANK checkpoint, returning `exploration-runtime-state-v1` with policy/bank/selector/cadence. It does not directly invoke the parent cadence validator at snapshot time. Allocation reporting callbacks (`_report_extra`, 1008) during commit/prepare also execute under runtime lock/active guard. Callbacks from opaque BANK occur under at least the runtime lock on decorated forwarding paths; BANK's additional locks/admission must be sourced separately.

## Telemetry registry

`AgentRuntimeRegistry(agent_ids: list[str], device: torch.device)` stores per-agent survival/curriculum/epsilon/intrinsic-weight tensors; it has no lock, callback, parent cadence authority or owner-health state. `get_curriculum_stage_tensor()` and `get_survival_time_tensor()` return the actual stored tensors. Scalar getters and `get_snapshot_for_agent(agent_idx: int) -> AgentTelemetrySnapshot` read/item the current tensors without exclusion. Setters `record_survival_time(agent_idx, steps)`, `set_curriculum_stage(agent_idx, stage)`, `set_epsilon(agent_idx, epsilon)`, `set_intrinsic_weight(agent_idx, weight)` perform device conversion and indexed assignment. `AgentTelemetrySnapshot.to_dict()` is serializable telemetry, not a healthy checkpoint certificate. Captured raw tensor aliases remain outside any future cooperative entry wrapper unless explicitly inventoried.

## Existing BANK evidence, explicitly attributed

`T18e-BANK-CP-STAGEB-REPORT.md`, SHA256 `7c79abf34c60c598084e55f0495e29ef9d54e4d517d4d121bbd1b6c23f2b7a3f`, begins with the exact current BANK 1414/seal recorded above. Its current summary attributes domain-before-BANK-lock/exact lineage, final token/publication and mandatory fail-closed exit to BANK; historical sections must not be mistaken for current source. Source hash equality binds this metadata, not my inspection of BANK implementation. Earlier `T18e-BANK-CORE-ADOPTION-READINESS.md` and `T18e-BANK-PAYLOAD-ADOPTION-FACTS.md` describe older 1284-line BANK and are not current ordering authority.

`T18e-BANK-PARENT-CORRELATION-API.md`, SHA256 `b25835bacdac5d0b663c1d7e809f2ecbe0e615baf135e4eda2d5588c3b53cbd6`, attributes parent-restore correlation, native ledger validation and its proposed pure parent-domain seam to BANK/CP. Its proposed spellings are not current runtime custody APIs. No source-verified current BANK outer scope, callback lock stack or externally callable uncertainty transition is claimed here.

## Finite integration recommendation and mandatory supplier handoffs

Current APIs cannot authenticate an outer parent retention window across ENV/runtime/child operations and outer completion. Add a finite producer-owned custody interface for the selected parent routes, rather than reaching into ENV/runtime private fields. Exact spelling belongs to the implementation proposal; required semantics are:

- Bind the actual parent/ENV/runtime identities once, accept genuine already-admitted lineage where required by the core contract, and issue an opaque thread/operation/lifetime-bound scope. A fabricated/copied/expired scope cannot grant entry. Retain real exclusion through outer completion/outcome consumption, then expire before release.
- Distinguish entering an outer scope from executing one operation inside it. Existing same-thread runtime callback refusal must remain effective; a retained outer scope must not simply leave `_operation_active=True` and make all intended child operations fail, nor disable that guard globally.
- Define a finite authenticated callback path for claim, accepted/participation checks, committed-batch/cadence/restore validators and existing failure cleanup. Reuse held custody only when authentication proves it is the current operation; do not acquire a new parent lock opportunistically while holding runtime/BANK locks. Preserve existing view-purity, revision, phase and receipt checks.
- Reconcile ordinary runtime entry with domain admission **before** runtime locking if that is the selected shared order. The present runtime-lock-first forwarder cannot coexist safely with a new opposite-order outer path without this change. Do not claim a total POP/ENV/runtime/BANK/replay order until the BANK and runner/POP suppliers establish all edges.
- A completion-based health transition must be owner-issued, non-CUDA, callback-free and operate under already-retained exclusion. No blanket ENV/BANK/replay quarantine follows solely from participation/common poison. Existing runtime revision invalidation and ENV phase quarantine are distinct mechanisms; neither proves completion health for another owner.

Separate bounded BANK supplier is required for current public admission/lineage signatures; exact lock stack at accepted/parent/report callbacks; permitted ancestor versus forbidden peer reentry; constructor and restore idle-registration lifetimes; a public mechanism to retain relevant BANK/native custody beyond a child return if the parent actually needs it; and who consumes later completion failure affecting actual BANK-owned storage. This packet cannot open the 1,414-line body within its 678-line remainder.

Separate bounded ordinary-runner supplier is required for the actual outermost reset/step/batch/checkpoint effect and publication boundaries, direct runtime/ENV calls outside POP, callback registration bindings, post-POP work on returned/raw tensors, and retention through final healthy return/publication. No runner filename/body is asserted from guesswork. POP planner supplies authentic parent→ENV/runtime calls and parent exclusion/reentry policy; this capsule only establishes their observable targets and reverse edges.

Acceptance should causally discriminate competing-thread exclusion, callback refusal versus authenticated current-scope reads, runtime→parent versus parent→runtime contention, runtime/domain opposite-order attempts, ENV claim cleanup before first write, initial-participation cleanup, and outer completion after an internally cleared vector record. These are prospective cases, not tests executed here. No qualification/programme gate is closed by this supplier.
