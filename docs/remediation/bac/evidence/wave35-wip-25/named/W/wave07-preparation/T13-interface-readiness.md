# T13 additive API wiring readiness — stationary

The two prior coordination questions are resolved by the adopted HC coordination and public learner recipe. No new plan review or user scope decision is needed. The choices below give the core implementer a concrete additive route within PS/PB/OP/HC/counted regression. Authoring remains blocked on predecessor qualification and root dispatch; the active full suite is untouched.

## Source and authority receipt

Read the effective task-T13 header; its core projected five/4200 and separate witness five/4753 supersede older counts. Consumed T13-public-learner-recipe.md as prose only; no POP/compact/witness/RC or helper implementation was opened for this readiness task. Reused previously inspected core source bytes after exact verification:

- PB783: `47b0070b5e519c6703d87861da07d8971b6e466f2c3f04c7417fc58db3038c2f`.
- OP294: `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916`.
- HC666: `013fe456f867bc9b5e28ab95ee9b07e5b0fa155653abfd07de3a35159c969761`.
- PS and test_per_estimator.py remain the two reserved new paths, not authored here.

HEAD `44e9d494eb94da1450b3e7a1832acea23dbbdb8e`; index SHA256 `d8dfd9c392ea19fb101672e156f4912f89f94efe0feb663ccce1b7d4e118c5b5`. Only read-only identity checks with GIT_OPTIONAL_LOCKS=0; no write-tree. No imports/runtime/tests/prototypes/helpers/source/index/tracked edits, branches/worktrees/copies/deletion/subdelegation. Only this ignored note is written. Existing project authority/tool approvals apply; no durable user-only fallback or expanded approval is adopted. Original approved plan and frozen reviews remain unchanged.

## Selected public interfaces

Preserve the existing constructor exactly: `PrioritizedReplayBuffer(capacity, alpha, beta, beta_annealing, device)`. It explicitly retains the old public successive/global-NumPy adapter. This is documented compatibility behavior with recorded origin, not a newly inferred option or a locally seeded Generator.

Add one configuration entry point:

`configure_sampling(*, sampling_mode: str, rng: numpy.random.Generator, origin: str) -> None`

Accept only the two P3 modes. Require a real Generator and explicit provenance `authored` or `bac-options-v1`; the caller passes `resolved.options.replay.sampling_mode` and its corresponding resolved origin. OP already supplies both mode vocabulary and omission-resolution provenance; do not edit OP or resolve None inside PB. Validate and deep-copy the supplied generator/mode configuration completely before assignment, without advancing the supplied RNG. This owns an independent generator state: callers cannot mutate or consume the supplied generator to perturb an installed sampler after configuration. Reconfiguration is explicit and atomic, preserves rows/priorities/IDs and changes only the selected qualified sampler configuration; no implicit buffer clearing.

An additive convenience constructor may expose the exact same required arguments without a separate policy:

`PrioritizedReplayBuffer.for_sampling(capacity, alpha, beta, beta_annealing, device, *, sampling_mode: str, rng: numpy.random.Generator, origin: str) -> PrioritizedReplayBuffer`

It creates the preserved constructor and delegates once to configure_sampling. No default arguments for mode, origin or RNG; no default_rng() or hidden fixed seed. This factory does not infer action geometry, capture masks or construct a ReplayOptions DTO. Existing push/push_recorded/declare_unconstrained_action_dim remain responsible for storage admission.

Keep `sample_batch(request: ReplayRequest) -> PrioritizedReplayBatch` callable exactly as today. In explicit-generator mode it checks request mode against the persisted selected mode and calls approved PS `sample_units(..., mode=selected_mode, rng=owned_rng)` with float64 priorities/current alpha/beta. Existing constructor-only callers retain its previously supported successive mode through the explicit global legacy adapter below, now with the corrected P3 estimator. Unconfigured independent requests refuse clearly and direct callers to configure_sampling/for_sampling rather than inventing an RNG. Qualified readiness for replacement permits B>N when retained population is nonempty and warmup is met; successive still needs B<=N. Neither mode weakens captured-legality readiness.

Keep `sample(batch_size: int) -> dict` and `update_priorities(indices: ndarray, td_errors: Tensor) -> None` as the legacy physical-slot pair. `sample` continues to draw successive without replacement from the global np.random stream and returns physical `indices` plus legacy float32 dictionary weights, with corrected P3 weights. This route remains explicitly successive even when a separate qualified mode is configured; it must not silently turn replacement on for existing consumers. The chosen qualified mode governs sample_batch, not a retroactive reinterpretation of the legacy dictionary. Document both routes and test their separation. Existing population's ordinary sample/update calls thus receive corrected numerics/weights without any new constructor or RNG prerequisite.

Add `update_unit_priorities(unit_ids: ndarray[int64], td_errors: Tensor) -> None` for qualified stable IDs. sample_batch maps PS's local positions to retained buffer IDs for `unit_ids`; PS receipt indices remain ordered sampler positions. Legacy `indices` are never reinterpreted as stable IDs. Both update methods validate their entire request and finite representable candidate priorities before any write. Only the ID method performs ID-to-live-slot resolution; duplicate live IDs reduce by maximum absolute error, and stale/unknown IDs refuse atomically. Legacy physical-index semantics stay explicitly immediate-slot semantics; a caller needing overwrite safety must use the qualified pair. No claim that old physical indices suddenly became durable is permitted.

## PS internal sharing and global RNG adapter

Keep the approved public `sample_units(priorities: ndarray[float64], *, alpha, beta, batch_size, mode, rng: numpy.random.Generator) -> SamplingReceipt` unchanged.

Add a narrowly named module adapter in the SAME PS source:

`sample_legacy_units(priorities: ndarray[float64], *, alpha: float, beta: float, batch_size: int) -> SamplingReceipt`

It uses global `np.random.choice(..., replace=False)` with the same stable validated float64 probabilities and shared deterministic receipt/weight construction as sample_units. It does not create a Generator, copy global MT state into a different engine, or seed anything. Preserve the existing successive ordered distribution and global seeding surface. One vector choice call can retain the familiar public draw interface; reconstruct ordered residual q from the returned indices using the same validated scores. sample_units uses the supplied Generator for the chosen mode. Both routes share score preparation, ordered-q and estimator implementation inside PS, not duplicate mathematical code in PB. Tests must exercise actual draws through each path, including the global adapter, rather than only a shared weight oracle.

The PS private implementation may factor a choice callable or deterministic receipt builder; that is an in-file routine choice, not another helper source or exposed API requirement. Same seeded bitwise sample sequence across a float32-to-float64 numeric repair is not promised; ordered distribution and the explicitly controlled RNG ownership are preserved.

## Persistence and origin semantics

Use distinct strict PER6 for the new persisted ID/sampler metadata, as adopted. Persist existing captured storage plus the selected qualified sampling mode, its origin, objective/rule version, stable live IDs/next-ID allocation counter and explicit RNG ownership descriptor. Two RNG cases must remain distinguishable:

- `numpy_global_legacy`: constructor-only compatibility route, successive mode with explicit legacy compatibility origin, no buffer-private Generator. Persist a null private RNG state plus the ownership label. This is the already-existing externally owned np.random stream, not a newly introduced unpersisted RNG. Loading a buffer must NOT overwrite process-global np.random state or claim its exact continuation. Native/runtime RNG ownership remains separately required.
- `owned_numpy_generator`: configured qualified route. Persist the exact standard NumPy bit-generator kind and a deep-owned complete bit-generator state. Validate the closed tagged state and restore it off-side without consuming live/global RNG. Accept the installed standard Generator engine families through an explicit class table, not import-by-string or pickle dispatch. Copying a configured engine then applying validated state, or constructing a known engine with an explicitly restore-only deterministic placeholder immediately replaced by the complete saved state, is materialization—not a hidden behavioral seed. No sampled value may occur before state installation. On successful restore, later draws use the restored owned state; on malformed state, source/target/RNG remain unchanged.

The legacy public sample route always retains global ownership even in a buffer whose qualified mode has an owned Generator; do not serialize its global state as though it were private. Persist/documents distinguish the qualified mode from this fixed legacy adapter law. No exact full training stochastic continuation follows merely from retaining one sampler state: environment, policy, optimizer, scheduling and other RNG domains still need native acceptance.

Stable IDs are monotonic within the persisted buffer identity/history; clear and overwrite do not reuse issued IDs. Preserve next counter even when active storage is empty; allocation exhaustion refuses before mutation. Restored same-history IDs/counter retain their mapping. Qualified handles are scoped to the buffer/checkpoint history from which they were sampled, not arbitrary other buffer instances; no global cross-buffer ID uniqueness is implied. Restore/new history boundaries must be documented rather than treating another object's numerically equal ID as authenticated provenance.

## Required current5 adapter and HC coordination

Exact closed27-key captured PER5 remains accepted through its explicit adapter, preserving every row, physical slot/position, finite priority/max, initial/current beta, masks/legality/action geometry, component presence and all archives. It initializes previously absent stable IDs deterministically from physical retained slots with a fresh next counter, and records a named current5 adapter origin and external-global legacy RNG ownership. There was no buffer-private RNG to reconstruct. It restores full captured replay, never old4/fresh0. Unknown keys under tag5 still refuse; new persisted fields belong only to6.

Old exact19-key maskless PER4 remains approved archival import with original artifact/query/export and fresh active0. HC's adopted explicit supported-current mapping recognizes captured5/6 at both classifier and policy/decode boundaries, while historical `_KINDS['prioritized']` remains4. T24/T25 complete validators, canonical outer accounting, empty PER handling and off-side native resource/RNG installation remain required open; the narrow HC mapping does not discharge them.

## Readiness and limits

No actual blocker remains for core authoring after root dispatch. Concrete API choices above preserve current callable signatures and isolate the new mode/RNG/handle interface without constructor defaults, hidden RNG creation, changed physical-index meaning or captured5 loss. Required core controls include both RNG routes/global-seed positive, owned-generator caller-alias isolation/state roundtrip, invalid configuration/load no-mutation, corrected actual legacy consumer weights, independent B>N readiness, duplicate/stale ID refusal, and source5-to6 preservation.

Production wiring of resolved options into actual population construction is not silently claimed: the public learner recipe explicitly confirms today's ordinary learner uses global sample/update and does not consume OP's mode. The separately bounded witness can qualify C01 through that unchanged public route; it cannot claim replacement-mode integration merely because core sample_batch supports it. T13/T16 integration remains an explicit consumer handoff rather than a fabricated source edit outside this core scope.

The adopted public learner recipe resolves the earlier exact construction/fixture question. Its compiler admission, real first optimizer change and subsequent actual normalization boundary still require execution; C01 remains API-only until then. Root's separate bounded witness and independent review provide that evidence. No test execution, mathematical re-review, source implementation, full-suite PASS or release clearance is asserted here. Stationary.
