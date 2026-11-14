# Parent factory and demo runner: current source supplier

2026-11-14. Read-only bounded supplier by `/root/bac_parent_factory_runner_supplier`, for root and `/root/bac_astra_parent_integration_prepare`. Existing checkout `/workspace/hamlet` only. Read AGENTS.md. No APP edit, test, import, runtime, Git write, branch/worktree/checkout/source copy, deletion or delegation. Sole write is this preparation capsule. This continues the adopted parent consumer design and does not qualify implementation or hardware.

## Source custody

Complete body costs measured before opening. Five bodies, **2228 lines**; file-count budget exhausted despite 2772 unused lines. No POP, ENV, runtime, replay, core, library or sixth implementation body was opened. Large output truncation was resolved with bounded reads within these same charged bodies.

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/agent/network_factory.py` | 179 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| `src/townlet/agent/optimizer_factory.py` | 162 | `56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d` |
| `src/townlet/demo/runner.py` | 1017 | `e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf` |
| `src/townlet/agent/networks.py` | 655 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| `scripts/run_demo.py` | 215 | `0029a2d758ed45907be30c6e8a21003798ddaef99dad392acc2c8a0ce3abd43a` |

Consumed opaque prose: parent proposal SHA `ba6128eb2fa12df3cdf2fddad402e8c8a9a99ad36314776c80a75a3ae0d7eab6`, design peer review `f8abc8c88a7aa24f17a88bb4c3c45f0ce1504ed7be626d36fb565bd57a0099e6`, current POP preparation `781a98a7e8ca67b4d7cfa15a7852314c14d8beb7da8f57a5d62777a434111815`, and current ENV/runtime supplier `02ac16732bb18dd6613c09cf90f2b20850da402c355cd11604f000f3f91b5b33`. The latter capsules supply current POP3163/ENV2889/runtime1299 facts; they are not additional inspected bodies. Prior `T18e-Q-PARENT-RNG-ENTRYPOINT-FACTS.md` describes older POP2612 and is historical corroboration only. `T18e-CPU-ADAM-RNG-PROFILE-CONTRACT-DRAFT.md` supplies the separately qualified narrow CPU exception; no test was repeated.

## Decision-ready facts

- The actual factory chain is `NetworkFactory` -> ordinary Torch modules / `networks.py` token constructors. It contains no domain participant, registration/enrollment, RNG lineage, CUDA preflight, explicit Generator or RNG save/restore. Q/target construction must be admitted before these initializers execute. Enrolling an already-built POP does not protect this prefix.
- Constructors omit explicit device/dtype for Linear, LayerNorm, LSTM and zero type embeddings. Normal default CPU construction is not a guaranteed profile: ambient default device/dtype can affect allocation before POP's later `.to(device)`. The parent inventory cannot be just its destination `device`.
- OptimizerFactory returns real Torch Adam/AdamW/SGD/RMSprop plus selected real scheduler; it installs no hook/closure or replacement wrapper. Empty optimizer state at construction is not a complete later allocation inventory. Parameters, gradients, actual state tensors, and anticipated lazy slots must remain covered.
- `DemoRunner` is **not integrated with the current exploration/episode authority protocol**. It constructs `AdaptiveIntrinsicExploration`, does not build/bind `ExplorationRuntime` callbacks, and later calls `population.reset()` without the current required reservation. Current source mismatch is statically established against the supplied current POP/ENV APIs; no claim of an executed failure is made.
- Actual CLI is `scripts/run_demo.py` -> `UnifiedServer`. Its implementation and training-thread handoff are outside this five-body packet. Thus this capsule establishes DemoRunner's work, but cannot certify it as the ordinary outermost executing owner or prove server locks/callback ordering.

## Actual Q constructors, modes and effects

`NetworkFactory.build_feedforward(config, obs_dim, action_dim)` (25–71) creates a Linear per hidden layer, optional LayerNorm, selected activation, optional Dropout when configured positive, and final Linear. `build_dueling` (96–135) delegates to `DuelingQNetwork`, whose real constructor builds independent shared/value/advantage Linears and optional LayerNorm; only shared layers contain the configured Dropout (networks71–139). These are ambient Torch parameter initializations, not generator-scoped project calls. The source does not override normal library initialization or install RNG custody.

`build_token_set` (138–160) resolves encoder policy and calls `TokenSetQNetwork.from_resolved_encoder`; `build_recurrent` (74–93) calls `RecurrentTokenQNetwork.from_resolved_encoder` with actual encoder/LSTM options. These classmethods allocate by `__new__` then initialize exactly the selected encoder; no throwaway linear model is constructed (networks448–510,552–631).

Token encoder initialization (274–357) validates options and compact roster, constructs `TokenInputAssembler(token_spec)` at312, then a per-live-type Linear or Linear/ReLU/Linear row encoder, zero-initialized learned per-type embedding Parameters, and optional Q/K/V/output Linear projections. The token Q head adds Linear/LayerNorm/ReLU/Linear (505–510). Recurrent construction additionally creates `nn.LSTM(..., num_layers=..., dropout=..., batch_first=True)` (619–625), followed by its Q head. LSTM construction initializes its Parameters by library behavior; its configured dropout remains a possible stochastic training forward region. Type-embedding zero initialization does not make the surrounding constructor RNG-free.

No `train()`/`eval()` switch or hook registration occurs in these factories/models. Standard module construction leaves normal training semantics intact. Feedforward/dueling Dropout and recurrent LSTM dropout therefore cannot be declared absent merely because a caller uses `no_grad`. Current POP capsule establishes Q forward/gradient work and retained mode; its earlier detailed capsule attributes target.eval at initialization and online.train during learning. Current planner owns exact POP line/mode confirmation. Token attention explicitly pins the MATH SDPA backend (411–412); its call supplies only query/key/value/attention mask, no nonzero dropout argument. That is not a proof of arbitrary hooked/replaced modules or every library path being deterministic.

Token forward reads actual observations, calls assembler.expand_type for every live type (364–385), applies row encoders and type embeddings, builds masks, and performs pooling or QKV attention (387–418). Recurrent forward reshapes observations, runs encoder and LSTM with caller hidden, then Q head and returns new hidden (641–655). `initial_hidden(batch_size, device)` allocates two zero tensors on the supplied device (637–639). These real allocation/copy/forward paths must be represented in the parent phase inventory. No project CUDA stream selection, synchronization, RNG-domain enrollment or completion receipt appears in these bodies; generic module `.to` and CUDA library effects remain real work even without a source-level `torch.cuda` call.

**Opaque delegation gap:** `TokenInputAssembler` is imported from `townlet.agent.token_input`; its 116-line file was measured, SHA `2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3`, but not opened. Its buffers, initialization device, expansion copies/cache and `.to` participation are not established here. A separate bounded supplier must answer those facts before claiming complete token model device inventory. This is not permission to drop token/recurrent support.

## Optimizer and scheduler supported profile

Exact `OptimizerFactory.build(config: OptimizerConfig, parameters: Iterator[nn.Parameter]) -> tuple[optim.Optimizer, LRScheduler | None]` (24–111) forwards:

| Type | Explicit actual arguments |
| --- | --- |
| Adam | parameters, lr, betas, eps, weight_decay (55–66) |
| AdamW | parameters, lr, betas, eps, weight_decay (68–79) |
| SGD | parameters, lr, momentum, nesterov, weight_decay (81–91) |
| RMSprop | parameters, lr, alpha, eps, weight_decay (93–103) |

Foreach/fused/capturable/differentiable/maximize and other unlisted knobs are omitted, so their concrete values and dispatch remain installed-library facts; there is no factory-specific forced CUDA implementation. Scheduler construction is None for constant, otherwise StepLR(step_size,gamma), CosineAnnealingLR(T_max,eta_min), or ExponentialLR(gamma) (113–162). Unsupported type/schedule refuses; invalid schedule can refuse after the optimizer has already been constructed. Parameter iteration is supplied externally; custom iterator effects are not excluded by annotations.

Factories do not step optimizers, create fake gradients, warm state, invoke closure, install hooks, call `.to`, or register children. The planner's current POP capsule supplies the real `.to(device)` on both independently constructed networks, Q-to-target loading, parameter iterator used to build optimizer, and bare `optimizer.step()` after real backward/clipping. A later real step may lazily allocate optimizer slots even when constructor `state` is empty. Future inventory must include selected parameter/gradient devices, existing optimizer state, and anticipated new state on actual parameter devices; CPU scalar counters may coexist with CUDA moment tensors. Restored/custom groups and replacement optimizers require actual profile inspection, not deduction from factory name. No dummy optimizer step is justified as enrollment.

The existing CPU Adam profile separately qualifies ordinary dense real CPU float32 Parameters/gradients, exact built-in unmodified eager Adam, no closure/user hooks/custom dispatch/AMP/compilation/capture, specific float options and defaults, first empty-state and subsequent warm-library steps. It establishes no Python/legacy NumPy/Torch CPU RNG consumption for that profile. It does not qualify construction, gradient generation, CUDA Adam, AdamW/SGD/RMSprop, custom hooks or a complete Q training path. Preserve that independent RNG-free step exception and ordinary public manual/hook/closure/replacement capabilities; no blanket interception, proxy or capability ban follows from this capsule.

## Required constructor and idle ordering

The current POP capsule establishes real Q/target `.to(device)`, Q->target state loading, optimizer/scheduler construction, registry tensors, recurrent hidden, and replay creation before later stable owner binding. The bounded implementation must make these actual effects admitted, not add an inert postconstruction participant.

Before an active outer invocation: establish the real owner/participant and resolve/enroll actual destination selectors plus any default-device constructor allocation sources using current core's idle-only supplier contract. Preserve CUDA laziness for truly CPU/no-work paths. Resolve unindexed CUDA using the core resolver, not an index-zero convention. Construct/register replay/BANK/native and any offside candidate owners at their approved idle boundaries; discovery inside active parent work is too late. Existing default-device construction cannot be silently changed to explicit CPU if that changes supported semantics; either source-qualify the selected profile or account for the actual defaults.

Then, under approved admission/exclusion and actual invocation lineage, execute the stochastic constructors, actual copies/`.to`, optimizer/scheduler setup and tensor/hidden creation, and consume completion before healthy publication. Existing module/optimizer instances do not require fictional RNG participant APIs; the parent owns this region. Slot devices and input source devices must be anticipated before work even when the future tensor does not exist. Later additions/replacements/candidate loads need the same idle plan/revalidation discipline. Exact core resolver/enrollment spellings are intentionally delegated to the current core/replay capsule, not invented here.

This packet does not establish library cold-import purity, global seed implementation, arbitrary default-device contexts, custom tensor dispatch, hook storage effects or external stream use. `seed_all` is called by DemoRunner, but determinism.py29 was only measured (SHA `73b8cd748bf1d495d0dfa22842e85c2e5a52421bd3081afbfd401eb0c0f14244`), not read. No exact seed implementation is asserted.

## DemoRunner actual owner boundaries

No RLock/Lock, domain admission, invocation lineage, retained child custody or completion-health latch appears anywhere in DemoRunner. Signal handler `_handle_shutdown` merely sets `should_shutdown` (200–203); optional worker-thread construction catches signal-registration ValueError (191–198). This explicitly anticipates an orchestrator, but does not prove its implementation.

Construction `__init__` (88–198) resolves launch, creates checkpoint directory/database/logger, calls `seed_all(training_config.seed)` at173, sets component references None, and registers signal handlers. Random construction happens later in `run`, with a temporal gap after seed_all; neither region has process RNG custody here.

`run` (385 onward) chooses `torch.device("cuda" if torch.cuda.is_available() else "cpu")` at396; calls `VectorizedHamletEnv.from_universe`410, `build_curriculum`422, `AdaptiveIntrinsicExploration`430, then `VectorizedPopulation.for_training`474. Replay Generator is explicitly `np.random.Generator(np.random.PCG64(effective_training.seed))`492. Curriculum initialization499, optional EpisodeRecorder511, load_checkpoint522 and hyperparameter publication542 all precede the loop's try558. A shutdown during initialization returns547 without this method's final cleanup; a surrounding context/server may clean up, but that is not established here.

There is no `build_exploration`, current runtime callback binding, world role authority binding, reservation/activation/closure/batch-commit protocol in this runner. `AdaptiveIntrinsicExploration` is a concrete old class import (21), not a local alias for current ExplorationRuntime. Current ENV supplier requires an actual ExplorationRuntime at binding; POP current protocol requires explicit reset reservation. Their implementation must be reconciled at real assembly, not shimmed by fabricated receipts or compatibility aliases.

### Step/reset and post-POP effects

At episode5000 runner directly randomizes ENV affordance positions (569–583). It calls `population.reset()`589; then allocates four device reward totals and alive mask (594–606). Per vector tick it computes alive sum/item614, calls actual `step_population(self.env)`632, immediately updates runner counters634–637, publishes curriculum events640–650, and then performs more CUDA-capable work:

- accesses returned active mask/reward-component tensors and creates zeros_like; torch.where plus in-place reward accumulation655–659;
- active sums, scalar action/reward/done/epsilon reads661–710;
- direct `env.get_action_masks()`695 and live `env.positions[0]`/`env.meters[0]` passed to recorder697–714, plus returned Q values and action masks;
- alive mask in-place update716 and done reduction717.

The parent return does not complete this outer work. ENV supplier explicitly allows live returned dones/reward/weight aliases; this packet cannot prove every returned POP field is detached. Recorder's handling of passed raw views/async work is opaque. Do not infer replay raw alias access from these ENV references: no direct replay column use is present here.

Episode closure flushes surviving lanes733, reads public `episode_completions`, allocates step-count tensors739 and curriculum tensors743–744, calls population.update_curriculum_tracker745, and converts completion/reward/stage tensors to CPU742,750–758. Database episode publication starts762, recorder publication807 and TensorBoard830 onward. These are actual final publication boundaries for this file, not protected by a parent receipt. Direct exploration.decay_epsilon969 and POP metric sync970 occur after optional checkpoint966; no current runtime commit_batch_episode call occurs.

### Snapshot/restore and teardown

`save_checkpoint`259 flushes each POP lane, obtains POP/curriculum state and ENV layout, calls population.validate_checkpoint_state276, reads VFS state/random state and private POP epsilon, validates transport, then torch.save312, digest313 and database pointer317. Current POP prepare/validation has fresh-boundary and retained-candidate semantics; it cannot be assumed a harmless schema-only check at this live save call. Source does not prove exported model state_dict tensors are detached; retain custody through materialization/completion before durable healthy publication.

`load_checkpoint`319 verifies digest, loads payload, validates nested components, invokes POP load370, then curriculum load371, ENV layout/VFS writes372–374, directly replaces population.agent_ids375 and runner counters376–380. POP's successful local return does not certify later independent installs or coherent cross-owner publication. No common transaction/exclusion, world restore/role binding protocol or outer completion consumer is present in this method.

The loop catches BaseException974 only to set failed and reraises; finally977 unconditionally logs and calls `save_checkpoint()`990 even on failure. A save failure can replace the earlier exception and prevent later training_status publication1002 and cleanup1013. `_cleanup`205 only shuts recorder and closes DB/TensorBoard with caught Exception warnings; it neither waits for CUDA completion nor owns POP/ENV/runtime teardown. `__exit__`237 calls cleanup and propagates. A future uncertain owner must refuse healthy checkpoint output; teardown must preserve the primary failure and complete resource cleanup without treating an uncertain snapshot as recovery authority.

## Actual CLI and mandatory remaining supplier

`demo/runner.py`1016–1017 refuses direct execution and names `scripts/run_demo.py`. The latter imports `townlet.demo.unified_server.UnifiedServer`24, constructs it155 with launch/level/episodes/checkpoint/inference arguments, installs signal callbacks that call server.stop181, and calls server.start196. Exception path calls stop204. No DemoRunner instantiation is present in this CLI body. Thus the observed source path is **CLI -> UnifiedServer**, and any claim about ordinary training worker/serving owner must follow that real imported class.

Measured only: `src/townlet/demo/unified_server.py`,616 lines, SHA `626634171c744ecac9ac825f5db5727e3407031efd6c8fe0dcac5a1058e2a02c`. Root was notified to assign a separate bounded supplier for training-thread construction, actual runner selection, competing serving/checkpoint readers, stop/join/cleanup and callback lifetime. No sixth-body read is hidden behind structural search. Server might delegate elsewhere; that supplier must measure before admitting additional complete bodies.

## Smallest coherent prerequisite APP slice and explicit limits

Before parent activation, implement the already identified ENV/runtime/BANK custody prerequisites and **actual POP constructor admission/device planning** including genuine idle child registration. The factory itself needs no guessed new `lineage` keyword: existing factories are ordinary constructors that can execute under their real owning scope. A narrow parent constructor packet can consume this sealed factory contract plus the separate assembler/seed facts and test actual feedforward/dueling/token/recurrent construction, real transfers, first optimizer slot work, and rejected-prefix effects. It must preserve custom/manual APIs and the narrow independent CPU Adam exception.

Ordinary runner integration is a distinct bounded prerequisite for claiming schedule9 or end-to-end training, not a one-line outer wrapper around the current loop. First complete the actual UnifiedServer supplier, then migrate real assembly to current ExplorationRuntime and genuine world authority/episode/closure/restore contracts; integrate runner-owned post-POP effects and final publication under retained approved custody. No compatibility fallback is permitted by AGENTS.md. Do not activate an incompatible runner just because standalone POP tests pass.

The runner slice must include the final checkpoint/error cleanup decision and clarify recorder/curriculum/VFS external effects. If live ENV views remain supported through recording or metrics, retain their producer-approved custody and completion policy through the last actual use; copied outputs alone can justify a narrower handoff only when proved. Do not blanket-quarantine all replay owners or inspect private health. Future tests must distinguish POP child False / runner outer True, retained locks through receipt consumption, coherent successful snapshot publication, failure teardown preserving primary exception, and genuine worker stop/join lifetime. These are prospective acceptance obligations, not executed results.

This capsule does not establish a total POP/ENV/runtime/BANK/server lock order, model Tensor-subclass safety, library-wide optimizer purity, default-device coverage, complete token assembler buffers, recorder ownership, real CUDA/multi-device behavior, or current unified server execution. It closes the five-source factory/demo/CLI inventory only. Root retains the implementation/test baton and all programme gates remain unchanged.
