# T15 caller/configuration/RNG interface facts

Read-only bounded interface collection, 2026-11-01. This report supplies the configuration side of T15-preparation Q1/Q2. It does not authorize implementation, select a new seed recipe, modify the frozen plan, or release T14/T15/T16. Root's full qualification remains active and project source remains frozen.

## Scope and identity

Work was performed in the existing `/workspace/hamlet`, HEAD `01f2f64f42c2932177729607b337419355cb2720`. The complete implementation inventory is exactly **four whole files / 2394 charged source lines**; selective citations do not reduce that charge. No test, fifth implementation/helper, runtime/import, or source-copy inspection was added.

| Alias | Whole source path | Lines | SHA256 |
|---|---|---:|---|
| RR | `src/townlet/demo/runner.py` | 1001 | `94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d` |
| EF | `src/townlet/config/effective_run.py` | 365 | `9ff2c4e8cc538160abe7188c7a2192b3ee740464d1b0681790e569685d49882c` |
| OP | `src/townlet/config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| WS | `src/townlet/exploration/world_curiosity_state.py` | 734 | `8b242ef58af2840c069db3d599606ba4760eea675e6be5bf00d8eb89c23b5b82` |

All source references below use those aliases and verified one-based lines. `TrainingV2Config`, population, buffer factories, compiler/environment internals, `seed_all`, and imported exploration-policy source were **not** opened. Their implementations are outside this receipt. Interfaces attributed to T15-preparation remain attributed prose, not newly inspected source.

`AGENTS.md` and `CLAUDE.md` were read. `docs/remediation/STATUS.md:96–135` supplies S1, no-defaults and standing rules; BAC STATUS:3,11–17,25,31–33 supplies the frozen plan, approved historical A, preserved shared/private alternatives, approval boundary and open integration/qualification state. Frozen plan:15–22 supplies the newer additive/preservation ruling and bounded-source discipline. Public BAC HLD distinguishes implemented behavior from intent; it is not evidence of current wiring.

The coordinator's governance correction applies: no durable permission rule was saved, no user-only fallback was adopted, and actual project instructions/tool approvals govern. This task created no branch, checkout, worktree, helper or subagent. No operation was performed on any of the existing 14 project worktrees.

## 1. Existing resolved configuration carrier

The actual public resolver signature is EF154–161:

```text
resolve_effective_run(base: BrainConfig, training: TrainingV2Config, *,
                      primary_level: str, origins: Mapping[str, str],
                      drive_intrinsic: IntrinsicStrategyConfig) -> EffectiveRunConfig
```

EF53–67 declares a frozen `EffectiveRunConfig` carrying `base_brain`, `effective_brain`, `training`, `authored_options`, resolved `options`, resolved `exploration`, `primary_level`, `field_roles`, authored/execution/training hashes, `derivations` and `origins`. EF80–84 returns a deep model copy when reading either brain, training or either options object. Consumers can carry the selected object without mutating the canonical view. `to_dict()` includes these identities, roles, derivations and origins (EF86–104); `from_dict()` resolves and validates the complete captured view (EF140–151).

The resolver validates/copies base and training (EF168–169), reads authored options only when supplied (EF174–176), resolves exploration (EF177), consumes OP's omission table (EF178–179), then overlays explicit non-None authored fields (EF180). It materializes `BaCOptions` and computes the effective brain at EF198–199. Thus the existing carrier for T15/T16 is **`effective_run.options.replay` plus `effective_run.training`**. `effective_run.authored_options.replay` can still be absent/partial and is not an interchangeable execution input.

Actual override mapping, EF227–233:

| Effective brain field | Existing training source |
|---|---|
| `q_learning.gamma` | `training.q_learning.gamma` |
| `q_learning.target_update_frequency` | `training.q_learning.target_update_frequency` |
| `q_learning.use_double_dqn` | `training.q_learning.use_double_dqn` |
| `optimizer.learning_rate` | `training.q_learning.learning_rate` |
| `replay.capacity` | `training.replay_buffer.capacity` |

EF260–264 records those as derived effective fields. This is source evidence for exactly these five overrides, not an invitation to merge or override more brain fields locally. Effective replay capacity and the original training replay block remain separate data. The full training DTO is preserved in EF57,169,354 and serialized at EF90.

### ReplayOptions is six fields; optional authoring is not a learner default

OP45–51 declares the actual `ReplayOptions` fields and accepted values:

| Field | Accepted authored values | Omission resolution, OP191–198 |
|---|---|---|
| `sampling_mode` | `successive_without_replacement`, `independent_with_replacement` | `successive_without_replacement` |
| `uniform_sequence_adapter` | `legacy_episode_length_with_replacement`, `uniform_windows_with_replacement` | `legacy_episode_length_with_replacement` |
| `sequence_mode` | `fixed_full`, `adaptive_prefix` | `fixed_full` |
| `retention_mode` | `whole_episode`, `transition_tail` | `whole_episode` |
| `sequence_objective` | `window_mean`, `anchor_transition` | `window_mean` |
| `priority_reduction` | `max_abs`, `mean_abs` | `max_abs` |

Each field is typed `Literal[...] | None = None`; OP's module contract explicitly says None is an absence marker, not a constructor-selected behavior (OP1–5). `OptionModel` is strict, frozen, finite-only and extra-forbid (OP17–20). `BaCOptions.replay` itself can be None at authoring (OP138–149). A same-type `ReplayOptions` instance alone therefore does not prove all six values were resolved.

The existing resolution API is OP172:

```text
resolve_bac_options(options: BaCOptions | None, *, training: TrainingV2Config) -> ResolvedBaCOptions
```

Its versioned result has `schema_version='bac-options-v1'`, `options`, and tuple provenance (OP160–169,294). The single table is expressly not a set of consumer defaults (OP189). OP260–289 overlays only authored named leaves; each leaf records `field`, `origin` and `reason`, with omitted leaves originating at `bac-options-v1` and explicit ones at `authored` (OP271–287). EF201–205,300–311 carries corresponding derivations/roles into the effective view, with explicit role origins named `bac_options.<field>`.

Not every resolved replay leaf is active for every family: EF292–299 marks sampling mode active for PER, the uniform-sequence adapter for nonprioritized recurrent, priority reduction for recurrent PER, and other replay leaves for recurrent. Preserve the authored/resolved values and their roles; having complete options does not mean every field must drive every buffer family.

### Warmup is a distinct declared input

The required declared path is `effective_run.training.replay_buffer.min_size`, to become `ReplayRequest.min_transitions`; frozen plan:64,437–453 and design baseline:71–97 give its meaning: **retained eligible transitions**, separate from sampleability and scheduled vector ticks. T15-preparation:92,100 identifies it as a missing population input. This receipt verifies the carrier preserves the complete training object; it does not claim an additional inspection of the `TrainingV2Config` field definition or validators.

The current runner reads `replay_buffer.batch_size` (RR448), not `min_size`. `batch_size` cannot substitute for warmup, and episode count, pending live prefixes, restored historical clocks and archive row count cannot substitute for retained eligible occupancy. No new warmup value is resolved by OP or invented by EF. The exact population-facing constructor/configuration name remains a root integration choice.

## 2. Existing real runner caller and provenance

The actual public constructor is RR87–97:

```text
DemoRunner(config_dir: Path | str, db_path: Path | str, checkpoint_dir: Path | str,
           max_episodes: int | None = None, *, level_name: str | None = None,
           force_new_vfs: bool = False, max_environment_steps: int | None = None)
```

RR111–115 calls `resolve_launch` and stores `self.resolved_launch`, selected compiled universe and `self.effective_run`. Its exact training declaration origin is stored from `declaration_origins[f'levels/{self.level_name}/training']`; RR116–120 requires an absolute path and positive authored line. RR121–124 separately records a supplied runtime `max_episodes` in immutable `launch_overrides`. RR159–169 retains the selected level's training and compiled brain; those are the existing caller inputs, not proof of the internals of launch/compiler resolution.

Current construction in `run()`:

| Input/operation | Actual source |
|---|---|
| `loop_cfg`, `num_agents` | RR400–401, from `self.training_config` |
| Environment | RR408–413 `VectorizedHamletEnv.from_universe(self.compiled, level_name=..., num_agents=..., device=...)` |
| Observation/action geometry | RR415–417, selected `level_meta.token_spec.total_dims` and `level_meta.action_metadata.total_actions` |
| Training frequency/batch/sequence/gradient norm | RR446–450, loop and replay training DTO fields |
| World/agent IDs | RR452–453, `[f'agent_{i}' for i in range(num_agents)]` |
| Current brain derivation | RR456,458,462 `apply_training_overrides(self.brain_config, self.training_config)` |
| Actual population call | RR465–481 |

The current call passes exactly:

```text
VectorizedPopulation(env=self.env, curriculum=self.curriculum, exploration=self.exploration,
    agent_ids=agent_ids, device=device, obs_dim=obs_dim, action_dim=action_dim,
    tb_logger=self.tb_logger, train_frequency=train_frequency, batch_size=batch_size,
    sequence_length=sequence_length, max_grad_norm=max_grad_norm,
    brain_config=effective_brain_config, max_episodes=self.max_episodes,
    max_steps_per_episode=loop_cfg.max_steps_per_episode)
```

This is a **caller quote**, not a newly inspected population constructor signature. It passes no `EffectiveRunConfig`, `ReplayOptions`, `min_size`, explicit replay Generator, sampling origin, named beta horizon or initial vector tick. RR stores the effective view but does not currently forward those replay inputs. Replacing duplicate brain derivation with the canonical effective brain and propagating the selected replay policy is T16's existing scope (frozen plan:447–455), not a completed fact.

The four-file source scope does not verify that an arbitrary existing population caller can read `env.effective_run`, `env.compiled`, or any other particular environment attribute. Frozen plan:449 says existing callers can deterministically derive the policy from their compiled environment; that is an integration commitment. Root must supply a source-verified environment carrier receipt or an explicit additive public input/configuration surface before a worker treats it as callable. T15-preparation:92 describes the current population inputs and absence; its facts are attributed, not re-inspected here.

## 3. Existing seed primitives do not select a replay producer

RR18 imports `seed_all`; RR170–172 calls `seed_all(self.training_config.seed)` before random runtime construction. Only that invocation is verified. The implementation of `seed_all` was not opened, so its comment about every RNG stream is not independently proved here. Runner imports no NumPy module and constructs no explicit Generator anywhere in its 1001 lines. Seeding ambient streams is not a receipt for an owned replay Generator or its immutable origin.

The precise existing WS public KDF signature is WS43:

```text
derive_world_seed(*, training_seed: int, world_id: str, provider_kind: str, component: str) -> int
```

WS45–49 requires a nonnegative exact int seed, exact nonempty world ID/component strings, and a provider kind in imported curiosity `STRATEGIES`. WS50–59 hashes the canonical sorted compact ASCII JSON record containing schema **`world-curiosity-seed-v1`** and those four inputs, then takes the first 16 hex digits masked to 63 bits. Component is any nonempty string in this standalone function; it is not itself restricted to the four descriptor components. Its version/domain and provider semantics nevertheless remain curiosity, not an existing replay policy.

`WORLD_SEED_COMPONENTS = ('model_init', 'target', 'predictor', 'service')` (WS26). `WorldCuriosityDescriptor` records curiosity scope/provider/geometry/world IDs/seed policy/origin/guarantee/training seed/seeds (WS62–82). Private seeds must cover exactly its declared world IDs and exactly those components, and must match that KDF (WS118–136). Shared mode owns no private seed map and `seed_for` refuses shared access (WS147–152). The public descriptor factory is WS154–163:

```text
WorldCuriosityDescriptor.from_policy(policy: ResolvedExplorationPolicy, *,
    world_ids: tuple[str, ...], observation_dim: int, action_dim: int,
    training_seed: int) -> WorldCuriosityDescriptor
```

The RNG factory is WS416–417:

```text
WorldRNGState.create(*, descriptor: WorldCuriosityDescriptor, world_id: str,
                     cuda_devices: tuple[int, ...]) -> WorldRNGState
```

It requires an explicitly private descriptor and exact member world ID (WS307–323); shared curiosity cannot silently use this private factory. It creates all four curiosity streams (WS422–443), including explicitly seeded PCG64 state via the component suffix `numpy-pcg64` (WS424–441). `activate(self, component: str) -> Iterator[WorldRandomSources]` (WS532–533) exposes `.numpy: np.random.Generator` (WS390–393), but this generator belongs to the active curiosity owner/component and its state is captured on exit (WS550–552,570–575). This is not a public replay-generator factory. Copying a curiosity service generator would create a new replay policy decision and would not establish replay ownership/provenance by itself.

Consequently the verified existing inputs are the authored `training.seed`, selected effective identities/origins, and existing curiosity-specific deterministic primitives. **No replay-specific seed derivation, replay-owned Generator producer, deterministic replay origin recipe, or replay RNG policy field exists in these four inspected sources.** OP's replay schema has no RNG/seed/origin/horizon field. The fixed public plan requires an explicit sampler Generator (plan:105), but does not select a production seed derivation recipe there. Test seeds in T15-preparation:94 are not such a selection.

Root's narrow remaining choice is which already-authorized explicit replay stream recipe/origin the caller will supply and how it is carried into the T15 public path/T16 runner path. This report selects none. Do not silently make `default_rng()` without a seed, a global-state copy, a hardcoded evidence seed, a transient object ID, a fabricated world/provider, or an undeclared reuse of curiosity state stand in for that choice. A direct explicitly seeded replay Generator or a selected deterministic derivation must be labeled as root's selection, then passed as a caller-owned input for the buffer to own/clone under its accepted API. There is no need to open an extra helper to recognize that missing handoff.

## 4. Beta horizon and initial/restored clocks

The actual existing runner supplies both potential horizon inputs: `self.max_episodes` and `loop_cfg.max_steps_per_episode` (RR479–480). `self.max_episodes` equals the explicit constructor limit when supplied, otherwise `self.effective_run.training.training_loop.max_episodes` (RR173–177). The explicit override is recorded separately at RR121–124. Thus a chosen horizon based on the *executed runner episode limit* must account for this existing override; it must not be mislabeled purely authored when it came from launch arguments.

Design baseline:94–97 expressly permits **`max_episodes * max_steps_per_episode` as a named upper-bound vector-tick horizon**. That is not actual realized experience and does not promise beta reaches 1 after early episode endings. Plan:111,453 requires vector-tick pacing and an explicitly named horizon. OP and EF currently define no replay beta-horizon field or derivation entry. The expression is therefore an available, public permitted derivation from verified caller inputs; its selection/name/provenance must still be made explicit by root and consumed consistently. This report does not add an authored option or choose between authored and launch-adjusted limits.

RR's `max_environment_steps` is a summed-live-agent transition budget (RR57–77,107–108); it is not a vector-tick count. RR616–618 distinguishes a single population step from the added live-agent count. Do not substitute that budget, retained replay occupancy, optimizer count, current episode index, or `N * horizon` for a vector-tick horizon without an explicit selected conversion contract.

Construction precedes restore: population is created at RR465–481, then RR505–508 calls `load_checkpoint()`. Load requires initialized components (RR325–326), validates state (RR364–367), and invokes `population.load_checkpoint_state(checkpoint['population_state'])` at RR369 before updating runner episode/live-transition counters (RR375–379). This receipt does not inspect or claim the loader's internal beta/RNG/tick behavior.

T15-preparation:50,60–62 is the attributed current replay handoff: recurrent PER factory requires `beta_vector_tick_horizon`, `current_vector_tick`, explicit `rng` and `origin`; fresh population `total_steps` starts 0; `set_vector_tick(total_steps)` advances beta independently of warmup, train frequency and optimizer success. A fresh caller must provide an explicit initial tick 0, not infer it from a missing argument. A restored caller/loader must preserve the restored cumulative vector tick and owned beta/sampler state, not reinstall the fresh initial tick after loading. Horizon reconfiguration or ordinary rewind cannot be invented at the restore boundary. Exact current buffer/loader setter validation remains with the already bounded replay/history owners.

## 5. T15/T16 handoff and the remaining root decisions

These are the existing task seams, not a new design programme:

| Item | Existing fact | Required existing-task handoff / root choice |
|---|---|---|
| Canonical brain/training/options | EF provides all three with roles/provenance; RR stores EF but reconstructs brain separately | T16 forwards one selected effective policy; T15 consumes resolved values rather than resolving omissions locally |
| Replay configuration | Six complete selected replay leaves available at `effective_run.options.replay` | Root names additive public constructor/configuration inputs and the immediate T15 call that consumes them; preserve existing caller roles |
| Warmup | Preserved training carrier; declared `training.replay_buffer.min_size` is distinct from batch size | Pass it explicitly as retained-transition warmup into request/readiness; no hidden fallback |
| Replay RNG/origin | Training seed is available; no replay producer/origin recipe in this source inventory | Root pins the replay-owned explicit stream recipe and stable origin, then supplies Generator/origin consistently to accepted buffer APIs |
| Beta horizon | Actual episode-limit and per-episode-cap inputs available | Root names the permitted upper-bound derivation, launch-override semantics and provenance; no missing-input horizon constant |
| Initial/restore clock | RR constructs before load; attributed replay factory requires current tick | Fresh 0 is explicit; restore preserves cumulative tick/state and subsequent accepted vector ticks advance beta independently of learner readiness |
| Runner release | Plan T16 depends on T15 and real authored runner controls | T15's callable construction/configuration path must work before T16 depends on it; T16 owns ordinary runner propagation and warmup1000/recurrent-PER proof |

Nothing here proves currently passing T15/T16 learning, all-family runtime wiring, native10/7 admission, complete stochastic continuation, or S1 curiosity qualification. Existing functionality, planned integration and root choices are kept separate above. No source-backed claim is made about absent environment carriers or uninspected buffer APIs.

## Reference and postflight custody

Reference prose hashes (not additional implementation inventory):

| File | SHA256 |
|---|---|
| `AGENTS.md` | `184c48c8f99d106870802bd72d4e7fe79baad11ac72234fa47e9bb493c3b9238` |
| `CLAUDE.md` | `a65cd6db26d75dce767d1b23f83be01206f09905d2e40073d6767d67740db4a3` |
| `docs/remediation/STATUS.md` | `767608b88d3c0d81587055923fdd732c9708db703912d1ef03fc883bcd47db6d` |
| `docs/remediation/bac/STATUS.md` | `50a292af188d8d63a5a52413fd1fe91864720319ad98988448dc75c2552fca6d` |
| `docs/architecture/BAC.md` | `1f634a2ce8f99d7ada99073023ed0866ad9086564915493c39e8bd2aa3391999` |
| Frozen plan | `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` |
| `docs/remediation/bac/2026-11-01-design-baseline.md` | `74a5f9ece62cc8ea59cfdc3b93c49400db08535e68c8cbadb3cb8b48c07271d5` |
| `docs/remediation/bac/PER-WORLD-CURIOSITY-ADDENDUM.md` | `3b82ecc340b936cd5672f248b85508f75136ab76cb994ac54723673989906871` |
| `sdd/tasks/task-T15.md` | `9b7f8e3144654f655921b48316e5f73c3a0f2652a2abe30b3522f87882c7417a` |
| `sdd/tasks/task-T16.md` | `9f7b3b9c77aafb4b4a61de6d2b4fca721f5511727d631939dd7f6d7522739132` |
| `sdd/wave09-preparation/T15-preparation.md` | `b0b132a2dd69cc147d43a8566c3f14a4f72921a08ed428e045bdf5a332417ca1` |

`sdd/` abbreviates `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/`. Some reference prose was read only in relevant excerpts. No referenced implementation link was followed.

Entry tracked status comprised the same nine pre-existing staged T14 source/test/data paths: historical checkpoint, sequential replay, three `bac_sequence_current6` fixtures, compact-token acceptance, recurrent-PER regression, recurrent-PER-native regression and sequential-replay owner test. This worker did not mutate the index or tracked paths and makes no independent full-tree qualification claim while root qualification is active.

The only write is this ignored prose report, covered by `.git/info/exclude:7` (`/.superpowers/`). Final postflight confirmed unchanged HEAD, all four source counts/hashes, frozen-plan hash, ignore rule and the same nine staged paths with no unstaged tracked paths. No project runtime/import, pytest/collection, linter/compiler/gate, source/test/config/metadata edit, tracker write, branch/worktree operation or commit was performed. Returned stationary after postflight; root retains all release and design choices.
