# T15 flat replay and strict selection contracts — stationary source receipts

Prepared read-only in existing `/workspace/hamlet` at HEAD `01f2f64f42c2932177729607b337419355cb2720` on 2026-11-01. This resolves the flat API facts requested by Q3 and the helper/base/epsilon portion of Q4 in `T15-preparation.md`; Q1/Q2 and provider-wide composition choices remain distinct below. Root's predecessor full gate was active at dispatch. No result here upgrades its status or authorizes T15 implementation/runtime.

No durable rule was saved; the user-only fallback was not adopted; the failed rule grants or restricts nothing. Existing project instructions and actual tool approvals govern. The user-directed preservation/addition requirement and approved History A take precedence over conflicting blanket deletion guidance. All existing 14 worktrees remain untouched. No branch, checkout, worktree, source-tree copy, subagent, project import/runtime, pytest/collection, source/test/index/metadata/tracked mutation, tracker claim, compiler/linter/gate execution or commit was performed. The sole intended write is this ignored prose file, covered by `.git/info/exclude:7` (`/.superpowers/`).

Skills read: `superpowers:using-superpowers` (its explicit dispatched-subagent stop applies), `cloud-environment:cloud-environment-runtime`, and `superpowers:verification-before-completion`. Managed-environment readiness was read without credential values; no network work was needed. This is static inspection of an accepted task, not new design or an implementation plan.

## Exact source inventory and reference boundary

Exactly **five whole source files / 2,125 lines** were read. No other implementation, test, conftest, helper, provider or harness source was opened. Line references below use RB/PB/AS/EB/EG from this table. Imported RC/history/per-sampling/state implementations were not followed. Their behavior is stated only where these files directly demonstrate it or where explicitly attributed to accepted prose.

| Abbreviation / complete source | Lines | SHA256, entry and exit |
|---|---:|---|
| RB — `src/townlet/training/replay_buffer.py` | 677 | `d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8` |
| PB — `src/townlet/training/prioritized_replay_buffer.py` | 1092 | `290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9` |
| AS — `src/townlet/exploration/action_selection.py` | 120 | `2a2ddfbd9aaf01afa14b0d1907fa1f3c8823f253dcdc8d16a8ff4054bf3768b8` |
| EB — `src/townlet/exploration/base.py` | 118 | `49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae` |
| EG — `src/townlet/exploration/epsilon_greedy.py` | 118 | `f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059` |

Governance/prose was read in applicable portions: root `AGENTS.md`, `CLAUDE.md`, `docs/remediation/STATUS.md` owner rulings/method/severity/gates, `docs/remediation/bac/STATUS.md`, the frozen plan's P1/P2/P3 interface prose, accepted `T13-implementation.md` and `T13-interface-readiness.md`, and existing `wave09-preparation/T15-preparation.md`. References to other source facts inside that prose remain attributed receipts, not extra implementation inspection.

## Construction and actual factory/configuration surface

| Route | Exact callable source surface | State/limits visible in source |
|---|---|---|
| Uniform flat | `ReplayBuffer(capacity: int, device: torch.device)` — RB119 | Starts active0, `action_dim=None`, `legality_mode='unconstrained'`. No ReplayOptions, action dimension, captured-mode, origin or RNG constructor arguments. |
| Prioritized flat | `PrioritizedReplayBuffer(capacity: int, alpha: float, beta: float, beta_annealing: bool, device: torch.device)` — PB170 | Preserves passed initial/current beta, active0, unconstrained geometry, monotonic ID counter0 and explicit legacy sampler. No options, seed, origin, horizon or vector-tick constructor arguments. |
| Qualified PER selection | `configure_sampling(*, sampling_mode: str, rng: np.random.Generator, origin: str) -> None` — PB202 | Requires all three keywords and a real NumPy Generator. Validates and clones the entire sampler configuration before assigning it; does not advance the supplied generator or clear rows/priorities/IDs/beta. |

**No `for_sampling`, `for_replay` or `for_prioritized_replay` factory exists in either complete flat source at these hashes.** T13 readiness prose describes `for_sampling(...)` as an additive convenience constructor that **may** be exposed; it is not evidence of a shipped callable. Existing T15 preparation's “configure_sampling or for_sampling” must be consumed through the actual `configure_sampling` route here. No new factory is required to use this current API.

Production captured construction is the existing constructor, then actual-mask `push_recorded`; PER additionally calls the explicit sampler configuration when selecting the owned-generator qualified route. Flat legality state is named **`recorded`**, not a constructor keyword `legality_mode='captured'` (RB301–305, PB533–537). Recurrent factory arguments must not be copied into these constructors.

PB accepts configured modes through `per_sampling.WEIGHT_RULES` and checks the corresponding objective/rule metadata (PB279–309). The frozen accepted P1/P3 prose supplies the two literal mode names `successive_without_replacement` and `independent_with_replacement`; the imported per-sampling implementation was not opened. Owned-generator provenance accepts exactly **`authored` or `bac-options-v1`**. The broader persisted origin enumeration also contains `legacy-constructor` and `captured5-physical-slot-adapter`, but those are the external-global legacy ownership cases; passing either to `configure_sampling` with an owned Generator refuses (PB284–306).

Owned generator families are PCG64, PCG64DXSM, MT19937, Philox and SFC64 (PB74–80). PB deep-copies generator state into a validated independent engine (PB202–218,227–277). The internal explicit `engine(0)` is a restore-only placeholder immediately replaced by the complete supplied/saved state; it is **not** production seed derivation (PB270–277). No seed/scope producer, KDF or hidden seeded `default_rng()` is provided by this API. RB uniform sampling uses `torch.randperm` on its device and exposes no generator/origin/seed API (RB310–316).

## Exact captured insertion and geometry admission

Both classes expose the same six required, positional-or-keyword insertion arguments:

```text
push_recorded(
    observations: torch.Tensor,
    actions: torch.Tensor,
    rewards: RewardTensor,
    next_observations: torch.Tensor,
    dones: torch.Tensor,
    next_action_masks: torch.Tensor,
) -> None
```

Receipts: RB234–247 and PB428–440. `rewards` is the extant RewardTensor-shaped object: these files consume `.total`, `.extrinsic`, `.intrinsic` and `.shaping`; they do not accept a bare scalar reward tensor in place of that object. The state/RewardTensor implementation was not opened.

Directly checked input requirements (RB174–214,249–308; PB372–417,468–537):

- Observations and exact next observations are float32 `[K,D]`, equal shape, positive D; subsequent D matches installed storage. Each insertion K must be at most capacity. Observations/next observations/total and each present reward component must be finite.
- Actions are nonnegative int64 `[K]`; total and each present component are float32 `[K]`; dones are bool `[K]`. Components are independently optional. Canonical total is stored unchanged, never recomposed from components.
- `next_action_masks` must be a two-dimensional tensor. Both entry points call imported `validate_successor_masks(masks,dones,action_dim=masks.shape[1])`, then internal insertion calls it again. Accepted RC/P2 prose establishes bool `[K,A]`, positive A, nonterminal nonempty support and legal terminal all-false masks; those validator internals were not opened here.
- The first **nonempty** recorded insertion establishes `action_dim=A` from mask width. Every subsequent supplied width must match. Actions must be `<A`, including already-present unconstrained actions before the first vocabulary admission. A zero-row call validates then returns before adopting geometry or inserting IDs.
- Caller rows/masks/components are detached, moved to the buffer device and cloned. FIFO ring indices preserve the exact successor/mask alignment. Every inserted captured row gets `legality_recorded=True`; no separate caller `legality_recorded` parameter exists.
- Component absence uses zero storage placeholders with per-row bool presence; a sampled wholly absent component is `None`, while partial presence returns zeros only at absent rows. Presence never changes total reward (RB278–287,373–397; PB492–501,618–637).

The preserved `push(observations,actions,rewards,next_observations,dones)` explicitly serves unconstrained callers (RB216–232; PB419–426). Before A exists it stores no masks. After A exists it supplies all-true masks. When a first captured insertion establishes A after earlier unconstrained live pushes, those earlier rows are explicitly filled all-true and marked recorded (RB292–295; PB521–523). That is the retained unconstrained interface role; production constrained experience must use actual successor masks from its same transition. It cannot use this conversion to claim reconstructed historical legality.

Only PB additionally has `declare_unconstrained_action_dim(*, action_dim: int) -> None` (PB442–455). It validates positive integer width, checks existing actions, refuses width mismatch, and declares all existing unconstrained live actions legal. RB has **no equivalent declaration method**. Neither this PB method nor plain push is a substitute for actual constrained capture.

## Flat request, readiness and sampling contracts

The existing T15 preparation's RC receipt and frozen P2 prose give the six required request fields:

```text
ReplayRequest(batch_size, sequence_length, min_transitions,
              sampling_mode, sequence_mode, sequence_objective)
```

No RC implementation was opened. These flat implementations themselves enforce the following restrictions:

| Field | RB — `_check_request`, RB331–341 | PB — `_check_request`, PB573–581 |
|---|---|---|
| Request type | Must be ReplayRequest | Must be ReplayRequest |
| sequence_length | `1` | `1` |
| sequence_mode | `feedforward` | `feedforward` |
| sequence_objective | `transition` | `transition` |
| sampling_mode | `uniform_without_replacement` | Must equal the currently configured sampler mode |

Thus flat requests cannot copy recurrent `fixed_full`/`adaptive_prefix` and `window_mean`/`anchor_transition` fields. PER alpha0 still uses its selected PER request mode; it is not an RB request. `min_transitions` is effective retained-transition warmup, independent of B. The current caller carrier for that effective value is not established by these five sources.

Both expose `retained_transitions: int`, `readiness(request: ReplayRequest) -> ReplayReadiness` and `sample_batch(request: ReplayRequest)` (RB142,343,356; PB333,583,598). Flat `len` equals active retained transitions; PB also preserves `size() -> int` (RB400, PB702–706).

Readiness is observational and makes no sampler draw. Source precedence:

1. Validate the flat request/mode first.
2. Sampleable population is active size only when A exists, the legality-recorded tensor exists and every retained bit is true; otherwise sampleable0. Archives never contribute.
3. If active retained size is below `min_transitions`, return not-ready `warmup`, even if another condition would also fail.
4. RB requires sampleable >=B, otherwise `batch_unavailable`. PB requires nonzero sampleable, and additionally sampleable >=B only for successive mode; independent replacement can serve B>N from nonempty qualified replay.
5. Otherwise return `ready`, with retained and sampleable counts.

Receipts: RB343–354, PB583–596. Flat paths do not emit sequence-window readiness reasons. Readiness does not call the priority sampler or prove its later numeric support/weight representability; those checks occur in the delegated sampling path. No masks are invented during readiness.

`sample_batch` calls readiness and refuses unavailable requests with reason and retained/sampleable counts before drawing (RB356–362, PB598–615). Returned classes are `UniformReplayBatch` and `PrioritizedReplayBatch`, extending ReplayBatch with the three component-presence tensors (RB48–75; PB92–115). Flat shapes and common dtype/ownership requirements are attributed to the accepted RC receipt in `T15-preparation.md`; directly visible construction sets bool `[B]` all-true `loss_mask`, int64 `[B]` all-one `lengths`, sampled stored masks/recorded bits, optional components/presence, float64 returned receipt weights and int64 unit IDs (RB363–398; PB616–637).

RB uses one `torch.randperm(N)[:B]`, without replacement. Its SamplingReceipt has physical indices int64, unit float64 weights, population N, ordered proposals `1/(N-arange(B))`, mode from request, objective `transition`, rule `unit_weights` (RB310–316,363–372). RB `unit_ids` equal those selected physical indices; no priority feedback or overwrite-safe ID API is present/needed for uniform storage.

PB `sample_batch` delegates with current float64-converted priorities/current alpha/current beta, selected mode and owned Generator (PB608–615), or its explicit external-global legacy adapter when no private Generator is installed (PB539–542,605–607). Its SamplingReceipt indices are **sampler/physical positions**, while returned `batch.unit_ids` map them to stored stable IDs. Preserve receipt weights as returned; do not normalize by batch maximum or recalculate a marginal estimator in the learner. Exact estimator guarantees are the accepted T13/P3 receipt, not a fresh sampler implementation review here.

## Stable priority feedback and retained legacy pair

Qualified feedback is exactly `update_unit_priorities(unit_ids: np.ndarray, td_errors: torch.Tensor) -> None` (PB644). Pass the sampled `batch.unit_ids`, explicitly transferred to a detached owned CPU NumPy **int64** `[B]` array, and the matching pre-update real TD residual tensor `[B]`. `batch.sampling.indices` are not those IDs. IDs are scoped to this buffer/checkpoint history, not globally namespaced IDs valid in arbitrary buffers.

PB649–693 validates the entire request before assigning priorities/maximum:

- IDs must be a one-dimensional ndarray with exact int64 dtype. TD errors must be a real, noncomplex tensor of the same one-dimensional shape. They are detached and promoted to CPU float64 before finiteness/absolute-value arithmetic.
- Every stable ID must still resolve in `_id_to_slot`; a retired/unknown ID refuses instead of updating a new occupant. Allocation is monotonic from `next_unit_id`, with an overflow check before insertion; overwritten IDs are removed (PB482–483,506–530).
- Candidate priority is `float32(abs(error_float64)+1e-6)`, and must remain positive finite representable float32. Repeated addresses reduce deterministically by maximum candidate priority. The stored maximum never decreases. The learner supplies residuals, not already-epsilon-adjusted priorities; it does not duplicate the reducer.

The retained physical pair is **`sample(batch_size: int) -> dict` / `update_priorities(indices: np.ndarray, td_errors: torch.Tensor) -> None`** (PB544–571,639–642). Legacy sample always delegates to the global-NumPy successive sampler even after configuring a separate qualified replacement sampler. It returns writable copied physical indices, float32 torch weights, the old transition dictionary and available legality fields. It checks count-bearing insufficient-buffer errors and float32 weight representability. Physical update accepts a 1-D integer ndarray (not necessarily int64) and addresses only currently active slots; it cannot protect a stale physical index against later overwrite. Stable and physical meanings must remain separate. Both update routes share the all-before-assignment validation/reduction above.

RB's preserved `sample(batch_size: int) -> dict[str,Tensor]` remains without replacement, returns observations/actions/rewards/next_observations/dones, bool all-true `mask`, and masks/recorded bits when allocated; it does not acquire a PER weighting role (RB318–329).

## Beta, vector ticks, RNG custody and restore

PB's only pacing callable is **`anneal_beta(total_steps: int, current_step: int) -> None`** (PB695–700). Here total_steps is the horizon argument, not the current tick. When annealing is enabled and horizon>0:

```text
progress = min(current_step / total_steps, 1.0)
beta = beta_initial + (1.0 - beta_initial) * progress
```

Disabled annealing or horizon<=0 is a no-op. It draws no RNG and does no sampling preflight. Equal tick with the same horizon computes the same beta. **It has no `set_vector_tick`, stored current tick, monotonicity check, ordinary-rewind refusal, lower clamp, horizon persistence, current-tick constructor argument or batch-size argument.** A decreasing tick can decrease beta; caller integration must enforce the accepted no-ordinary-rewind pacing contract rather than claim this buffer already does. Serialization stores current/initial beta and the annealing flag, not a horizon/tick (PB733–754). Recompute from the explicit current/restored vector tick and established horizon at the appropriate caller boundary; selecting/provenancing those inputs remains a root integration decision.

PB constructor-only sampler is explicit successive/global-NumPy with origin `legacy-constructor` and no private generator (PB195–200). This preserves an external global RNG role; buffer load does not overwrite global NumPy state or promise its exact continuation. Configured owned RNG is cloned on configuration, serialization and restore, along with mode/origin/objective/rule and stable IDs/counter (PB202–218,311–330,733–754,973–986,1063–1079). Do not reconfigure after restoring a current private RNG merely to manufacture a fresh seed without an explicit accepted reason; that would change continuation.

`clear()` removes only active experience/geometry, preserving archives. PB also preserves current beta, next-ID allocation counter and sampler configuration/RNG; it resets active priorities/ID slots and max_priority1 (PB708–718). RB clears its active tensors/geometry and preserves archives (RB403–410). No archive counts or prior cumulative ticks become new-row warmup occupancy.

## Public historical/current storage import hooks

Both buffers expose the following current public route; `expected_obs_dim` is a **required keyword**, even when explicitly None is allowed:

| Method | RB | PB |
|---|---|---|
| `validate_serialized(state: Mapping[str,Any], *, expected_obs_dim: ...)` | annotation `int`; returns `_ValidatedReplayState` — RB639 | annotation `int | None`; returns `_ValidatedPrioritizedState` — PB1053 |
| `materialize_validated(state)` | returns `_ReplayRestoreCandidate` — RB643 | returns `_PrioritizedRestoreCandidate` — PB1057 |
| `prepare_serialized(state, *, expected_obs_dim: int | None)` | returns `_ReplayRestoreCandidate` — RB647 | returns `_PrioritizedRestoreCandidate` — PB1060 |
| `load_prepared(candidate) -> None` | RB650 | PB1063 |
| `load_for_mode(state, *, requested_mode: history.AccessMode) -> None` | RB664 | PB1081 |
| `load_from_serialized(state) -> None` | delegates to auto — RB675 | delegates to auto — PB1091 |
| `install_historical_archive(archive: history.HistoricalReplayArchive) -> None` | RB169 | PB368 |
| `historical_archives` | owned archive tuple — RB146 | owned archive tuple — PB337 |

`validate_serialized` is separate from materialization/installation. `prepare_serialized` composes validation/materialization; `load_prepared` installs the type-specific candidate. No new public native wrapper API follows from these storage hooks. RB load_prepared transfers prepared tensors; PB clones candidate tensors, arrays and sampler before assigning live fields (RB650–662, PB1063–1079).

These files accept exact closed standalone **uniform4/5** and **PER4/5/6** schemas with compatible capacity/geometry/configuration (RB467–598; PB812–1002). Uniform4/PER4 maskless imports materialize original standalone history as archives and fresh active0, not all-true reconstructed learner masks (RB600–613; PB1004–1022). PB preserves saved current beta while fresh priorities reset, retains its target's current next-ID counter/private sampler for this old4 route, and does not reissue the target's retired IDs (PB977–982,1009–1021). Available optimizer/vector clocks belong to population/native owners, not to these standalone buffer files.

Current uniform5 retains captured rows/masks/components and archives. Captured PER5 retains active physical rows/position/priorities/current-initial beta/geometry/masks/components/archives, assigns deterministic live IDs `arange(size)` and counter=size, and records `captured5-physical-slot-adapter` with external-global successive ownership. PER6 restores its saved live IDs/counter and sampler descriptor/private state (PB973–986). This is an actual captured5 adapter, not a private RNG reconstruction claim. Uniform serialization returns chronological rows; PER serialization preserves physical rows aligned with its priorities/position (RB423–450; PB733–767).

At the buffer layer, `load_for_mode` accepts exactly `auto`, `recorded_full_resume`, `archived_history_fresh_episode`, `inference`. Explicit recorded-full-resume of maskless4 raises HistoricalLegalityUnavailable before installation; explicit archival-fresh mode cannot discard current-format qualified replay (RB664–673, PB1081–1089). Do not extrapolate from the accepted `inference` spelling to complete native/network/RNG guarantees: these are storage installers, and root's separate population/native contracts still govern. Archive query/export methods are attributed to approved History A/P2 prose; their implementation was not opened.

## Strict eligible action helper and preserved exploration protocol

The exact strict helper is:

```text
epsilon_greedy_action_selection_eligible(
    q_values: torch.Tensor,
    epsilons: torch.Tensor,
    action_masks: torch.Tensor | None,
    *, eligible: torch.Tensor,
) -> torch.Tensor
```

AS91–120: all four inputs are required; `action_masks=None` must be explicit and permits all actions. Eligibility is actual producer membership, not inferred from masks or `agent_states.dones`. `eligible` must be bool `[N]` on q_values.device. Non-None masks must be bool, exactly q_values shape/device. Any eligible row with an all-false action set raises `ValueError('eligible rows have no legal actions')` **before draws**. Inactive all-false rows are permitted.

It first builds unmasked `q_values.argmax(dim=1)` transport indices for all rows. Only if any row is eligible does it call the existing epsilon helper on `q_values[eligible]`, `epsilons[eligible]`, and corresponding masks, then scatter those selected actions back. Inactive transport indices consume **no random action or epsilon-coin draws**. The helper does not take a Generator or seed. It adds no explicit epsilon shape/range/finite checks or general Q validation beyond those visible eligibility/mask checks; do not assert such validation exists.

The retained helper is `epsilon_greedy_action_selection(q_values, epsilons, action_masks=None) -> Tensor` (AS11–88). It uses masked argmax; all-false legacy rows keep the **unmasked greedy** result. With masks it samples a uniform legal random action only for nonempty rows using torch.multinomial; without masks it uses torch.randint for all rows. It then draws torch.rand for each supplied row and compares to epsilon. Consequently even epsilon0 eligible rows still consume random-action and coin draws, while the strict wrapper's inactive rows do not. Preserving this exact eligible draw behavior does not mean optimizing away epsilon0 draws or inferring activity from empty masks.

`ExplorationStrategy.select_actions(self,q_values: Tensor,agent_states: BatchedAgentState,action_masks: Tensor | None=None) -> Tensor` remains the abstract protocol (EB24–48). **It has no eligible keyword, strict selection method, base implementation or state-slicing adapter.** Other abstract lifecycle methods are `compute_intrinsic_rewards(observations,update_stats=False)`, `update(batch)`, `checkpoint_state()` and `load_state(state)` (EB50–118). Selection and those intrinsic/update/checkpoint effects remain distinct; this base file does not supply a unified eligibility lifecycle.

`EpsilonGreedyExploration` retains constructor `(epsilon: float=1.0,epsilon_decay: float=0.995,epsilon_min: float=0.01)` and that three-argument selector (EG25–64). Its selector calls the **legacy** helper with `agent_states.epsilons`, not `self.epsilon`, and reads no dones. It has no selection-side state mutation here. `compute_intrinsic_rewards` returns `[N]` zeros on the observation device; update is a no-op; `decay_epsilon()` changes self.epsilon to max(min,self.epsilon*decay); checkpoint/load preserve those three scalar fields (EG66–118). Do not silently replace per-agent epsilons with the provider's scalar epsilon when adding strict membership.

## Required interface choices, separate from established facts

These are root handoff decisions owed before dependent authoring, not new scope, code changes or user-permission requests:

1. **Resolved caller inputs:** identify the narrow additive public carrier for resolved replay options/effective min_size, while preserving the existing population constructor/caller roles. This five-file receipt establishes no already-existing effective-run carrier or local option resolver. Flat requests must translate to their actual feedforward/transition ABI; recurrent options remain their separate factory/request roles.
2. **RNG/provenance/horizon producer:** supply the actual source-verified producer of Generator seed/scope and origin, plus explicit authored/derived vector-tick horizon and initial/restored tick. These files require/own the supplied state but do not derive it. Temporary witness seeds, global-RNG copies, object identity, omitted seed and guessed horizon are not producer policy. Use actual PB constructor + configure_sampling rather than invoking an absent factory.
3. **Flat pacing integration:** select where the caller applies `anneal_beta(horizon,current_vector_tick)` for every advancing vector tick independently of optimizer success/readiness/schedule. Since PB has no monotonic setter/state, establish caller-owned no-rewind behavior and restore ordering truthfully; do not describe recurrent `set_vector_tick` as a flat method.
4. **Provider-wide strict selection:** combine this helper/base/epsilon receipt with root's separate provider receipts. A direct strict epsilon helper is faithful for this source's epsilon action math, but it does not prove equivalence for all providers or preserve their lifecycle automatically. A truthful filter/select/scatter adapter must prevalidate eligible live-empty masks, slice all provider-required state consistently, invoke only actual eligible rows and preserve returned action/provider effects. No BatchedAgentState construction/slicing implementation was inspected, so no fabricated constructor is supplied here. The all-false temporary dones state does not establish membership.
5. **History test route:** choose the actual public population-level import/attachment route using these storage APIs and the accepted population/native receipt. Label manual buffer attachment separately from naturally authored construction, retain active captured current restore, and preserve learned cumulative clocks while maskless history starts active0. Complete native10/7 admission remains with its named owners; this receipt does not close it.

## Prose identities and stationary verification

| Reference used in applicable portions | SHA256 |
|---|---|
| `AGENTS.md` | `184c48c8f99d106870802bd72d4e7fe79baad11ac72234fa47e9bb493c3b9238` |
| `CLAUDE.md` | `a65cd6db26d75dce767d1b23f83be01206f09905d2e40073d6767d67740db4a3` |
| `docs/remediation/STATUS.md` | `767608b88d3c0d81587055923fdd732c9708db703912d1ef03fc883bcd47db6d` |
| `docs/remediation/bac/STATUS.md` | `50a292af188d8d63a5a52413fd1fe91864720319ad98988448dc75c2552fca6d` |
| Frozen `docs/superpowers/plans/2026-11-01-bac-remediation-upgrades.md` | `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` |
| `docs/remediation/bac/package-reviews/T13-implementation.md` | `07c0b4901b600acf375758a19a9cacb72d019c0648246387e4d38bf7ee61aef7` |
| `wave07-preparation/T13-interface-readiness.md` | `2b076c4bc1ba53183e37eb008ca8d21c6b748ca7a56a49b6cb535a718b649ca9` |
| `wave09-preparation/T15-preparation.md` | `b0b132a2dd69cc147d43a8566c3f14a4f72921a08ed428e045bdf5a332417ca1` |

Preparation file paths above abbreviate `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/`. Public reference `docs/remediation/bac/P2-P8-INTERFACE-CLARIFICATION.md` was searched in passing; no implementation source was followed from it.

Entry/exit checks re-read hashes and counts of all five sources, HEAD, this file's ignored status and tracked `git status --short`. The same nine pre-existing staged T14 paths remained; this worker did not mutate the index and makes no independently manufactured candidate-tree or full-tree identity claim. These are static API receipts, not executed behavior/test results. No runtime or gate was run. Return stationary for root's separate predecessor qualification, interface decisions and later bounded dispatch.
