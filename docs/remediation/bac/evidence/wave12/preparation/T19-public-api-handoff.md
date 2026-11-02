# T19 public API/DATA supplier handoff

Static supplier receipt only. T17 authors tests; root alone integrates. This does not grant T19 implementation clearance or change the accepted T19/P5/P6/B invariants. Requirements and POP observations are attributed to `T19-task-brief.md` and `T19-interface-readiness.md`; only the five implementation files below were inspected here. No sixth implementation/helper/probe/test was opened, no code was executed/imported/compiled/collected/tested/linted, and no index/staging/commit/push/checkout/worktree/delete action occurred. All14 worktrees were left untouched. This new ignored prose file is the only write.

## Pinned source inventory

All paths are relative to `/workspace/hamlet`. Citations such as RND:298–359 refer to the exact hashes below. `wc -l` and `sha256sum` match `T19-supplier-source-baseline.json`; total3983 lines.

| Alias | Path | Lines | SHA-256 |
| --- | --- | ---: | --- |
| RR | `src/townlet/demo/runner.py` | 1017 | `e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf` |
| ENV | `src/townlet/environment/vectorized_env.py` | 1714 | `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d` |
| RND | `src/townlet/exploration/rnd.py` | 661 | `3a774dfb042cdbf20b66555c41f75c2d537b6ff49472395877dfcf5595e26e72` |
| AI | `src/townlet/exploration/adaptive_intrinsic.py` | 226 | `80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9` |
| ER | `src/townlet/config/effective_run.py` | 365 | `9ff2c4e8cc538160abe7188c7a2192b3ee740464d1b0681790e569685d49882c` |

## RND: existing public construction and service DATA

Current public signatures (RND:131–141,213–217,244,289,298,361,395,418,577,586,645):

```python
RNDExploration(obs_dim=70, embed_dim=128, learning_rate=1e-4,
               training_batch_size=128, epsilon_start=1.0,
               epsilon_min=0.01, epsilon_decay=0.995,
               device=torch.device("cpu"))
configure_service(options: RNDOptions) -> None
admit_and_service(observations: torch.Tensor, *, vector_tick: int) -> PredictorServiceReceipt
compute_intrinsic_rewards(observations: torch.Tensor, update_stats: bool = False) -> torch.Tensor
update(batch: dict[str, torch.Tensor]) -> None
update_predictor() -> float
available_state() -> dict[str, Any]
checkpoint_state() -> dict[str, Any]
load_available_state(state: dict[str, Any]) -> None
validate_state(state: dict[str, Any]) -> None
load_state(state: dict[str, Any]) -> None
```

`RNDOptions` is imported at RND:15; its implementation/schema was not inspected. Its four service fields used here are `service_mode`, `max_updates_per_tick`, `max_pending_rows`, `overflow_policy` (298–359); ER:193–194 materializes those exact four selected policy fields into `options.rnd`. A usable explicit fixture input mapping is `{"service_mode":"occupancy_fifo", "max_updates_per_tick":1, "max_pending_rows":4, "overflow_policy":"service_before_admit"}` with `training_batch_size=2`; paced variant uses `"paced_fifo"`, drop variants `"drop_oldest"` or `"drop_newest"`. These are future caller inputs, not executed DTO validation evidence. Consumer checks revalidate `options.model_dump()`, refuse any None field, and require capacity >= minibatch (280–296). Same options configuration is a no-op; changing configuration after buffered work/admission refuses. Constructor initially has `service_options=None` (180); constructor alone does not select bounded service.

Frozen `PredictorServiceReceipt` has **eight required fields**, no defaults (21–36):

| Field | Meaning at return (350–359) |
| --- | --- |
| `admitted_rows: int` | Input row count, including explicit dropped-newest rows |
| `consumed_rows: int` | Actual consumed-row delta this call, including previously pending rows |
| `dropped_rows: int` | Actual drop delta this call |
| `pending_rows: int` | Current total FIFO occupancy, not a delta |
| `optimizer_updates: int` | Paced + mandatory overflow optimizer calls |
| `last_loss: float | None` | Last actual loss, None if no minibatch serviced |
| `paced_optimizer_updates: int` | Ordinary service count |
| `overflow_optimizer_updates: int` | Mandatory service-before-admit count |

Service rows must be finite tensor[K,D], exact `obs_dim` width and predictor dtype; validation is complete before clock mutation (268–278,306). Future CPU fixture: obs_dim=3, embed_dim=4, training_batch_size=2, finite float32 rows such as `[[1,0,0],[2,0,0],[3,0,0]]`; obtain expected dtype from the constructed predictor if framework defaults were changed. Empty input must still be [0,D] with matching dtype. Tick must be exact nonnegative int (bool refused), monotone nondecreasing (310–314). Repeated same-tick calls share paced budget but are **not event deduplication**: repeated content is admitted again. Empty eligible input can service already pending complete batches. Caller selects eligible predecessor rows; provider does not infer activity/world identity (298–305).

Occupancy service drains all complete minibatches FIFO and leaves incomplete tail. Paced service stops ordinary draining when its per-tick budget is exhausted. At full capacity, service-before-admit consumes an old full minibatch even beyond paced budget; capacity >= minibatch guarantees it can do so. Explicit drops are counted. Oversized inputs are admitted in capacity-bounded chunks, detached/to-device/cloned; consumed work is first batch rows, deleted only after optimizer.step (322–359,374–389). No reward RMS mutation occurs in service: intrinsic reward computation separately uses per-row embedding MSE divided by sqrt(running variance)+1e-8 and updates stats only when requested (227–242).

Fixture expectations derived statically, not test results: fresh occupancy B=2/capacity4, three rows at tick0 => admitted3/consumed2/dropped0/pending1/updates1/paced1/overflow0. Fresh paced B=2/capacity2/budget1 with eight rows at tick0 => admitted8/consumed6/pending2/updates3/paced1/overflow2; empty same-tick input does no ordinary work; empty tick1 consumes the remaining two. Cumulative identity is admissions = consumed + dropped + pending; per-call identity requires starting pending too. A consumed minibatch count is `consumed_rows // training_batch_size`; successful service optimizer count matches that quotient (387–388,626–639), never a count inferred from loss being positive.

Legacy/direct paths remain **current implemented facts**, not an instruction to add compatibility:

- `update` without observations returns. Configured `update` chooses next local service tick (at least previous vector tick+1), calls bounded service, increments `step_counter`, discards receipt (244–261). This implicit local tick is not proof of a world admission clock.
- Unconfigured `update` validates, clones input rows to the public buffer, adds admissions, calls exactly one minibatch update (262–266); it does not drain occupancy fully.
- Direct public `obs_buffer` appends + `update_predictor` are supported in this source. `update_predictor` first reconciles admitted count against consumed+dropped+buffer, returns0.0 for a short tail, otherwise performs exactly one real optimizer step and increments consumed/updates (369–389). Direct calls return only float loss, no receipt, and bypass bounded admission policy. Do not make every direct call count as an update or equate loss0.0 to a definitive skip.
- `checkpoint_state()['predictor_service']` is version1 and includes batch size, options, owned FIFO tensor, admitted/consumed/dropped/update counters, optimizer step offset, tick, tick pacing count and step_counter (418–446). `available_state` intentionally omits that service payload (395–416). Full restore validates before install, including policy match, pending shape/dtype/finite, integer/accounting/Adam clocks/capacity/budget (593–661). Historical available-state import retains destination pending work/clocks; no source tail/RNG is invented (577–584,645–650). No private RNG/world state is supplied by these methods.

## Adaptive completion and entropy: exact evidence limit

Public construction is `AdaptiveIntrinsicExploration(obs_dim=70, embed_dim=128, rnd_learning_rate=1e-4, rnd_training_batch_size=128, initial_intrinsic_weight=1.0, min_intrinsic_weight=0.0, variance_threshold=100.0, min_survival_fraction=0.4, max_episode_length=500, survival_window=100, decay_rate=0.99, epsilon_start=1.0, epsilon_min=0.01, epsilon_decay=0.995, device=torch.device('cpu'))` (AI:21–38). It constructs `.rnd: RNDExploration` and passes dimensions/training/epsilon/device, without configure_service (59–68). A configured fixture can use the public contained `adaptive.rnd.configure_service(resolved_options)` before any admissions. There is no adaptive `admit_and_service` or `admit_and_service_at` delegation in this entire226-line source. `update(batch)` delegates `.rnd.update(batch)` (124–130); rewards and action selection delegate (85–122).

`update_on_episode_end(self, survival_time: float) -> None` (132–148) takes steps survived, appends once **per invocation**, trims to survival_window, then checks/anneals. It takes no outcome, reason, world ID, planned horizon, entropy or event ID. It does not deduplicate duplicate completion calls. AI itself cannot prove “once-only completion callback”: the once-only POP finalizer is an attributed fact from interface-readiness (POP not reopened), and must remain the sole callback route. Do not add a second call on runner publication/reset/commit.

Annealing definition/timing actually present: after append, fewer than10 history samples => false; otherwise torch.var(float32 recent history) and torch.mean, with strict variance < threshold and mean > int(min_survival_fraction*max_episode_length); weight becomes max(current*decay_rate,min_weight) (77,150–183). This is survival variance, **not policy entropy**. Entire AI source has no entropy definition, entropy field, legality normalization or final/mean entropy timing. RR only logs a supplied transition event's `entropy` (639–650). Therefore an actual entropy formula/timing cannot be verified within the authorized five-source inventory. The controller/POP supplier must provide it; this handoff does not choose one or substitute annealing variance/epsilon/RND loss. Likewise AI's history is steps, not P6 survival fractions; do not route length-as-reward into a controller through this API.

## RR: existing index/horizon/reset/flush/publication order

Public `DemoRunner(config_dir: Path | str, db_path: Path | str, checkpoint_dir: Path | str, max_episodes: int | None = None, *, level_name: str | None = None, force_new_vfs: bool = False, max_environment_steps: int | None = None)` (88–98) allocates runtime directories/database/loggers (138–158); it is not a side-effect-free fixture constructor. No constructor/run executed here. Public `flush_all_agents()`, `save_checkpoint() -> None`, `load_checkpoint() -> int | None`, `run()` exist (251,259,319,385).

1. `current_episode=0` initially (180). `load_checkpoint` restores saved `episode`, agents and completed live transitions (370–380); run changes loaded index to loaded_episode+1 (521–524). Horizon is `effective_run.training.training_loop.max_steps_per_episode` via loop_cfg, also used for curriculum, adaptive max length, POP configuration and PER's upper-bound vector-tick horizon (400–445,488–496,593). Agent IDs are row-shaped names `agent_{i}` (455).
2. Each while iteration uses current_episode (559), then calls only `population.reset()` (586–589), then initializes runner-owned per-lane reward arrays and zero batch tick/transition counts (592–606). There is no `begin_batch_episode(index, planned_horizon)` call in RR. The P5 call is a future producer contract, not an existing signature supplied by RR.
3. Step loop checks shutdown, then tests whether **all** current live lanes fit remaining transition budget before stepping (608–630). `decide_live_agent_budget(*, completed:int, live_agents:int, budget:int) -> tuple[bool,int]` rejects bool/noninteger, negative completed, nonpositive live/budget, completed>budget; returns (False,remaining) if next indivisible vector step will not fit (58–78). After step, RR increments completed live transitions by entry live count (632–637); summary arrays use `info['active_on_entry']` and exact reward/component rows; ticks +1 and eligible transitions +mask.sum (652–661). Alive mask updates then breaks on all done or reached budget (716–718).
4. No accepted step (`last_agent_state is None`) => continue before publication (720–721). Otherwise flush each still-live lane with reason precedence budget, shutdown, cap; already done lanes are not externally reclosed (723–733). Then require every lane completion, copy survival and final meters, and invoke `population.update_curriculum_tracker(step_counts.float(), all_true)` (735–745). This is the existing length-based consumer, not the new envelope consumer.
5. Publish runner reward arrays into database/recording/per-agent telemetry using current_episode (750–835). No `commit_episode_outcomes` call exists. Current once-per-batch progression is control flow, not an implemented idempotent commit API or completed-batch ledger.
6. Periodic checkpoint if current_episode%100==0 runs **before** epsilon decay, telemetry sync and current_episode+=1 (964–972), including index0. `save_checkpoint` first calls flush_all_agents(reason='checkpoint') across every lane before obtaining/validating snapshots; checkpoint filename and payload episode use current_episode (251–312). Finally always attempts final checkpoint at current index, including error path; no proof here that every such index is committed (974–990). Preserve this distinction when binding new ledger/event identity. Callback dedup remains POP-owned.

## ENV: public fixture inputs, eligible/component shapes and identity limits

```python
VectorizedHamletEnv(*, universe: CompiledUniverse, level_name: str,
                    num_agents: int, device: torch.device | str)
VectorizedHamletEnv.from_universe(universe: CompiledUniverse, *, level_name: str,
                                 num_agents: int, device: torch.device | str) -> VectorizedHamletEnv
reset() -> torch.Tensor
step(actions: torch.Tensor, depletion_multiplier: float = 1.0
     ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]
get_action_masks() -> torch.Tensor
set_exploration_module(exploration: ExplorationStrategy) -> None
attach_runtime_registry(registry: AgentRuntimeRegistry) -> None
vfs_random_state() -> dict[str, int]
restore_vfs_random_state(state: dict[str, int]) -> None
```

Signatures: ENV:76–83,413–427,756,847–874,1043–1065,1288–1294. Fixture input must be an already supplied valid compiled universe with a selected actual level, explicit device (e.g. CPU), num_agents=2; observations use selected level token_spec.total_dims, action_dim from compiled runtime action space, meter count from selected metadata (102–188,282–285). No fixed70-dim ABI or hardcoded action IDs0–4 should be inferred from old docstrings. `get_action_masks()` gives bool[N,A]; choose legal actual actions (1043–1059). `reset()` returns observations[N,D]; step input actions[N], output observations[N,D], rewards[N], dones bool[N] (1061–1087). Compiler/DTO/factory/helper behavior and a complete YAML fixture are outside this source boundary; do not claim new compilation or a new population factory signature was verified.

Eligible timing: entry `prev_dones=self.dones.clone(); active_on_entry=~prev_dones` (1089–1090); physics/effects use that mask. ENV global_tick advances once at1139 after transition phases, before expressions/terminal evaluation; terminal transition increments step_counts once (1148–1153). Authored termination wins retirement coincidence; retirement bonus +1 is added to extrinsic and total; components, rewards and intrinsic weights are zeroed for inactive rows before done composition (1163–1178). Successor observation and cloned legal-action masks are constructed after state/done/hour commit; live rows with no legal successor action refuse (1190–1202). This is terminal-transition-once evidence, not a nonterminal runner cut converted into ENV done.

Actual `info` keys (1204–1216):

| Key | Public value shape/ownership visible here |
| --- | --- |
| `successor_action_masks` | cloned bool[N,A] for returned successor |
| `active_on_entry`, `newly_terminal`, `newly_retired` | cloned bool[N] |
| `step_counts` | cloned long[N], eligible lane counts |
| `positions` | cloned [N,position_dim], substrate dtype |
| `successful_interactions` | dictionary agent_idx -> affordance_name |
| `reward_components` | `_last_reward_components` dict[str,Tensor], passed by reference |
| `intrinsic_weight` | effective Tensor[N], passed by reference |
| `effect_spawn_refusals` | tuple of this step's new refusal objects, or () |

ENV explicitly accesses component `extrinsic`; RR consumes `extrinsic`, `intrinsic`, `shaping` as Tensor[N] under the eligible mask (ENV:1170–1175; RR:652–659). The calculator that populates the dict was not read, so this is the verified consumer shape/key contract, **not** a verified exhaustive producer key set or proof of component algebra/extra fields. Every supplied component is masked (ENV:1174–1175). Retain/snapshot needed scalars at completion: info's dict/weight and returned self.dones are not immutable outcome snapshots. No `policy_entropy`, world IDs, episode IDs, curiosity stamp/context, global tick provenance or envelope is present among ENV info keys. Recorder's optional time_of_day/interaction_progress/q_values accesses in RR are not proof ENV emits those keys (RR:688–714).

Stable identity actually available is limited:

- ENV has level_name/level/universe/config_pack_path and experiment_batch_label (102–106,166–176); they identify configuration/grouping, not unique worlds. Worlds here are row indices/range(num_agents), including item/effect handling (880–1035,1638–1641). No public stable world_id/world_ids, binding map, world_episode_seq, curiosity_epoch or admission event IDs are defined by this1714-line file.
- step_counts is episode-local and global_tick resets to0 on every reset (800–808); neither is stable episode identity. `reset()` also invokes `vfs_randomness.reset()` (827–828). `_vfs_draws` uses tick, num_agents, device (1284–1286).
- Public `vfs_random_state()` delegates `.state()`, documented as run seed+episode counter; restore delegates `.restore(state)` with next reset resuming draws (1288–1294). Exact dictionary key names, initial counter, reset increment semantics and per-world interpretation are not defined in ENV; the unread randomness helper cannot be inferred. RR checkpoints/restores this payload (293,374). It is not a substitute for B's stable world/episode identity.
- RR's current_episode and agent_{i} naming are available run/lane surfaces (RR:180,455,763,810–825), not evidence of stable world IDs or world episode sequence across reorder/reset/resume. Required B bank/context IDs and immutable stamps remain future contracts from the brief, not verified implemented APIs. Do not fabricate IDs from lane index/global tick or weaken world binding to configuration identity.

## Effective configuration identity available to callers

`resolve_effective_run(base: BrainConfig, training: TrainingV2Config, *, primary_level: str, origins: Mapping[str,str], drive_intrinsic: IntrinsicStrategyConfig) -> EffectiveRunConfig` (ER:154–161) requires nonempty primary_level and string->string origins (168–177). Call with already supplied DTOs; DTO constructors/selected exploration resolver were not opened. ER materializes four RND service fields from resolved exploration (193–198), but RR constructs adaptive directly from effective training and makes no explicit RND configure_service call (RR:428–446); POP/provider setup outside this inventory must establish which live service path is selected.

Frozen EffectiveRunConfig publishes base/effective brain, training, authored/resolved options, exploration, primary_level, field_roles, authored_brain_hash, execution_hash, training_hash, derivations, origins (ER:53–68). Model-valued attributes return deep copies (80–84). `authored_identity` hashes schema effective-run-authored-v1/base brain/authored exploration; `execution_hash` hashes schema effective-run-v1/active fields/selected policy identity; training_hash hashes training.model_dump_json, authored_brain_hash delegates compute_brain_hash (69–78,351–365). `to_dict()`, `validate_payload(payload: Mapping[str,Any]) -> None`, `from_dict(payload: Mapping[str,Any]) -> EffectiveRunConfig` are public serialization/validation APIs (86–151). Validation has an explicit old shared payload branch (112–137); that existing fact does not authorize new fallback paths. Hash helpers use sorted canonical JSON for `_hash` (30–31). Field roles distinguish active/inactive_preset/derived/unqualified (19–27,208–215). Configuration/policy identities support provenance and cannot create missing world/event identity or certify private runtime ownership.

## Finite disposition

Ready to supply: current bounded RND receipt/configuration API and legacy accounting; adaptive callback input/timing and its absence of dedup/entropy; RR's exact existing index/horizon/reset/flush/publication/checkpoint/epsilon order; ENV eligible and reward component consumer DATA plus explicit identity limits; effective configuration provenance.

Still required from an authorized owner: actual policy entropy definition/timing and once-only POP callback evidence; T17 test/qualification receipt and POP's live configured service route; actual stable world/episode producer binding and bank lifecycle; new T19 envelope/ledger/begin/commit semantics and their implementation/tests. No architecture choice, fix, invented API, relaxed invariant or execution result is supplied. Stationary after this artifact.

## Addendum: authoritative legacy direct-service accounting API

Static clarification for active T19 POP owner; same pinned five-source boundary, with RND/AI hashes unchanged. Original138 lines retained byte-for-byte. No runtime, imports or source changes. The configured path already returns `PredictorServiceReceipt` from `RNDExploration.admit_and_service` (RND:298–359); this addendum concerns the unconfigured public `update_predictor() -> float` path (361–389), which must remain exactly zero or one consumed minibatch per invocation.

**No cheap public receipt/counter/statistics snapshot API exists in current RND or AI for all five legacy accounting quantities.** The authoritative service counters are private attributes `_admitted_rows`, `_consumed_rows`, `_dropped_rows`, `_optimizer_updates` (RND:181–184); no public property/getter exposes them. Public `step_counter` is a service-adapter cursor, not an optimizer/admission counter (179,255–260). Public `obs_buffer` (178) permits cheap current pending occupancy via `len(rnd.obs_buffer)`, but that alone does not supply admitted/consumed/dropped/optimizer counters. Public `reward_rms` tracks reward normalization, not service (188–189,233–240). There is no legacy `last_receipt` declaration.

Existing public full snapshot declaration is `RNDExploration.checkpoint_state(self) -> dict[str, Any]` at RND:418. Exact service paths in its returned mapping:

| Public payload path | Meaning in unconfigured legacy path |
| --- | --- |
| `['predictor_service']['version']` | 1 (431) |
| `['predictor_service']['training_batch_size']` | Actual predictor minibatch size (432) |
| `['predictor_service']['options']` | None while unconfigured (427–433) |
| `['predictor_service']['admitted_rows']` | Snapshot computes consumed + dropped + current pending when service_options is None (424–426,435); covers manual public-buffer admissions even before update_predictor reconciles private counter |
| `['predictor_service']['consumed_rows']` | Cumulative actual consumed predictor rows (436; increment after optimizer.step at385–387) |
| `['predictor_service']['dropped_rows']` | Cumulative explicit service drops (437); legacy update_predictor itself does not drop rows |
| `['predictor_service']['optimizer_updates']` | Cumulative predictor-service optimizer updates (438; increments after optimizer.step at385–388), not shared Q learner work |
| `['predictor_service']['pending_observations']` | Owned tensor[P,obs_dim]; P is pending row count (421–423,434). There is **no `pending_rows` key** in this checkpoint payload |
| `['predictor_service']['optimizer_step_offset']` | Actual Adam clock minus service optimizer_updates, preserving manual optimizer/history offset (439–441); not a service work delta |
| `['predictor_service']['vector_tick']`, `['paced_updates_this_tick']`, `['step_counter']` | Saved service clock/pacing/adapter cursor (442–444), not legacy receipts or substitutes for service counters |

A before/after pair of those checkpoint snapshots can expose authoritative changes: subtract cumulative admitted/consumed/dropped/optimizer_updates and compare P before/after; pending occupancy after is P_after, pending delta is P_after-P_before. The observation interval must include the caller's public-buffer append if newly appended rows are to count as this interval's admissions. If the first snapshot is taken after append but before update_predictor, admissions are already represented in that first snapshot (424–426); admissions delta for the service-only call is then0, correctly. Existing unconfigured `update(batch)` performs its own clone/append/admission increment before exactly one update_predictor call (262–266). Direct update_predictor first reconciles private admitted count, skips a short tail, otherwise steps once and consumes one minibatch (369–389). These facts do not authorize computing work from returned float loss or Q learner batch size.

**Cost and mutation:** checkpoint_state is not a cheap counters-only read. It first calls public `available_state(self) -> dict[str, Any]` (395,420), which `deepcopy`s the complete returned fixed-network state_dict, predictor-network state_dict and optimizer state_dict alongside epsilon/dimensions/RMS (401–416). It additionally stacks, detaches and clones the entire pending FIFO if nonempty (421–423). The method is a read/owned snapshot here, not counter mutation; selecting only `['predictor_service']` after calling it does not avoid full model/optimizer/FIFO copying. `available_state()` alone also clones the full model/optimizer state and supplies **no predictor_service counters**. It does contain `['optimizer']` with its state_dict, but arbitrary optimizer details/steps and the offset are not a cheaper public service receipt and should not replace versioned service accounting.

Adaptive's only corresponding public snapshot is `AdaptiveIntrinsicExploration.checkpoint_state(self) -> dict[str, Any]` (AI:193): it calls `self.rnd.checkpoint_state()` at200, so the exact prefix becomes `adaptive.checkpoint_state()['rnd_state']['predictor_service'][...]` with the same costs and meanings. Its `survival_history` entry aliases the live history list (208); the adaptive wrapper is not an immutable whole-object snapshot. Alternatively the existing public composition attribute `adaptive.rnd` (AI:59–68) exposes RND's public checkpoint_state directly. AI has no public cheap service-counter getter, legacy receipt, or service-specific snapshot adapter.

Disposition: authoritative legacy deltas can be observed through the existing full checkpoint payload at substantial copy cost; cheap public complete accounting is absent. A counters-only producer adapter, if root separately authorizes one, would be new API rather than an existing declaration. No code/adapter is supplied here; stationary.
