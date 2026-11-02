# T17 ENV public API — finite read-only supplier receipt

Inspection: 2026-11-02 UTC, existing `/workspace/hamlet`, observed HEAD `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`. This receipt supplies current ENV API facts for the authored two-variable pack / two-world reset-and-WAIT handoff. It does not clear T17 implementation or runtime work, qualify T16R2, or alter the active frozen qualification barrier. Root remains the sole integration owner.

## Read boundary and provenance

Exactly one implementation file was opened, whole: `src/townlet/environment/vectorized_env.py` (ENV), lines 1–1714, in contiguous reads 1–430, 431–860, 861–1290, and 1291–1714. `wc -l` reports **1714** physical newline lines; SHA256 is **`849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d`**. This matches the ENV hash in the supplied T15 action-metadata prose.

The other repository files read were prose only: root `AGENTS.md`; ignored `wave11-preparation/T17-interface-readiness.md`; ignored `wave09-preparation/T15-action-metadata-api.md`; and ignored `wave09-preparation/T15-constructor-factory-bridge.md`, all under `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/` except AGENTS. No implementation links in those documents were followed. ENV line citations below refer to the exact source/hash above. Imported helper internals are explicitly outside this inspection.

## Exact callable surface

The module-qualified class path is `townlet.environment.vectorized_env.VectorizedHamletEnv`; direct import spelling is `from townlet.environment.vectorized_env import VectorizedHamletEnv`. This identifies the inspected module, without asserting an additional package re-export.

```text
ENV:76  VectorizedHamletEnv.__init__(
            self, *, universe: CompiledUniverse, level_name: str,
            num_agents: int, device: torch.device | str)
ENV:847 @classmethod
ENV:848 VectorizedHamletEnv.from_universe(
            cls, universe: CompiledUniverse, *, level_name: str,
            num_agents: int, device: torch.device | str) -> VectorizedHamletEnv
ENV:756 reset(self) -> torch.Tensor
ENV:1043 get_action_masks(self) -> torch.Tensor
ENV:1061 step(self, actions: torch.Tensor,
              depletion_multiplier: float = 1.0)
              -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]
ENV:730 get_action_label_names(self) -> dict[int, str]
```

All four constructor inputs are required; `universe`, `level_name`, `num_agents`, and `device` are keyword-only for the initializer. In the classmethod, `universe` precedes the keyword-only separator. ENV:98–100 rejects `device is None` and converts a string through `torch.device`; ENV:102 gets the selected level through `universe.get_level(level_name)`. Neither initializer nor classmethod automatically calls `reset()`: initialization ends with observation-encoder construction at ENV:372, and the classmethod returns its factory delegation at ENV:868–874.

The exact normal two-world classmethod call, with an independently supplied compiled artifact and its actual level name, is `VectorizedHamletEnv.from_universe(universe, level_name=level_name, num_agents=2, device="cpu")`. ENV:868–874 delegates `cls` and all supplied arguments to `env_factory.from_universe`. The separately supplied constructor-factory bridge attributes the additional fact that its inspected helper directly returns `env_cls(universe=universe, level_name=level_name, num_agents=num_agents, device=torch_device)` at helper lines 56–81; this worker did not open or reverify that helper. The bridge records helper SHA256 `ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232` at historical HEAD `b3003550b7c1dad76a52e596b2af01658fa2b92d`.

## World count, dimensions, and selected token schema

| Public extraction | What ENV establishes |
| --- | --- |
| `env.num_agents` | Set directly from `num_agents` at ENV:107. ENV:958–963 and ENV:1638–1641 describe the batch as independent single-agent worlds; `num_agents=2` therefore denotes two worlds, each with one agent. The class defines no public `num_worlds` alias. |
| `env.device` | The explicit device after string conversion, assigned at ENV:108. |
| `env.level`, `env.level_name`, `env.universe` | Selected level and input artifact retained at ENV:102–105. |
| `env.token_spec` | **Selected level** `level.token_spec`, assigned at ENV:181. ENV:177–180 explicitly explains why the primary-level alias must not replace it. |
| `env.observation_dim` | `env.token_spec.total_dims`, assigned at ENV:188. No dimension 147 or fixed variable-column offset is established by this module. |
| `env.action_dim` | `env.action_space.action_dim`, assigned at ENV:284 after building from the selected level's runtime artifact at ENV:283. Do not derive it from a historical substrate action count. |
| `env.action_ids` | Assigned from `level.runtime_action_space.action_ids` at ENV:285 and passed to the imported mask builder at ENV:305. ENV does not establish its mapping keys or name-lookup API. |

The public schema extraction for either network-family factory is thus the selected instance's `env.token_spec`, with action width `env.action_dim`. ENV does not define TokenSpec/context DTO constructors, compact-row descriptor coordinates, immutable semantic permutation construction, or compiler APIs. Those remain the separate suppliers' interfaces.

## Reset return and instant-0 observation

`observations = env.reset()` is the complete return extraction. It is **one tensor**, not `(observations, info)` or a wrapper with an `.observations` field: ENV:845 returns `_get_observations()` directly. ENV:876–878 annotates and documents serialization as `torch.Tensor` shaped `[num_agents, total_dims]`, and directly returns `self._observation_encoder.encode(self.num_agents, self._build_token_publish_context())`. Therefore the documented two-world shape is `[2, env.observation_dim]`.

The encoder is imported from `townlet.environment.observation_encoder` at ENV:25 and built at ENV:372. Its actual allocation, observation dtype, normalization implementation, compact row order, absence encoding, and output-storage ownership are not independently proved here. The public method annotation/docstring and direct return are source-verified; no extra tensor/container extraction is present in ENV.

Reset's visible phase order is:

1. Refresh configured/randomized affordance layout and initialize positions (ENV:775–788); zero velocity (ENV:790–795); clone expanded compiled initial meter values (ENV:797–798); reset boolean dones, long step counts, and intrinsic weights (ENV:800–802).
2. Set `global_tick = 0`, call registry episode reset, publish engine `tick`, and derive hour (ENV:804–812). `_publish_engine_tick()` at ENV:510–516 writes a same-valued tick row for every registry world.
3. Reset episode tracking; optional effects; optional VFS history; VFS randomness; optional item state/inventory (ENV:814–831).
4. Evaluate compiled VFS profiles at instant 0 (ENV:833–834), then spawn initial items if configured (ENV:836–843), then return the observation (ENV:845).

Consequently this normal path evaluates authored expressions before the first returned observation. It does not expose a pre-evaluation observation of the declaration's literal initial value. The evaluator call is conditional on both evaluator and compiled profiles existing (ENV:1222). ENV:1233–1254 evaluates the global profile and writes back its expression outputs, then re-snapshots before the agent profile at ENV:1263–1278. ENV:1390–1407 commits only names with non-None ASTs, checks agent-expression shape `[num_agents]`, and expands a scalar global-expression output to registry world count. The imported evaluator's parsing and exact arithmetic/`where` semantics remain outside this source.

For the supplied complementary `tick` expressions, ENV proves reset's tick-0 evaluation and the next step's tick-1 evaluation schedule. The exact `.25`/`.75` values, declaration validity, exposed-variable roster, static `.125`/`.875` descriptors, and normalization require the authored DATA/compiler/token-schema handoffs; they cannot be inferred from this file alone.

## Named WAIT lookup, legality, and action tensor

ENV provides a source-verified raw-record route: `env.level.runtime_action_space.actions`. ENV:520–536 iterates those records and directly reads `.id`, `.name`, `.type`, `.delta`, `.enabled`, costs/effects and the remaining fields to build the runtime action configs. Match the authored name **exactly**: the WAIT record satisfies `action.name == "WAIT"`; its action identifier is `action.id`. WAIT presence, name uniqueness, and its numeric identifier depend on the selected compiled artifact. No fixed WAIT ID or `.actions` list-position rule follows from ENV.

`env.get_action_masks()` has no arguments and returns the imported builder's result directly at ENV:1050–1059. ENV:1044–1048 documents it as a boolean tensor `[num_agents, action_dim]`, with **True meaning valid**. ENV passes current positions/dones, inventory/item handlers, deployed affordances, and an opening-hour callback. The normal public legality check for the selected WAIT ID is the returned mask column for that ID in both worlds, i.e. `masks[:, wait_id]`; calling a WAIT step “legal” requires that column to be true for every lane being stepped. Reset's dones are all false (ENV:800). ENV does not itself assert that WAIT must always be legal or even present.

The tensor spelling for the declared action ID repeated in the two-world batch is `torch.full((env.num_agents,), wait_id, dtype=torch.long, device=env.device)`. This is ordinary PyTorch caller construction matching the documented `[num_agents]` action input at ENV:1063 and ENV:1079. No project code was imported or run for it. ENV passes `actions` unchanged to its imported executor at ENV:1096 and to compiled transition phases at ENV:1097–1101. ENV contains no action rank/dtype/device validator; the exact executor validation and WAIT's no-op/write behavior are not proved by this receipt.

The runtime ID is the identifier, not the enumeration position. ENV itself uses movement records' `.id` as action-indexed tensor rows at ENV:712–726. Its mask docstring supplies the action-column contract, but imported DTO validation of full ID contiguity/range and imported mask/executor interpretation of every action are outside the one-file boundary. No uninspected `get_action_id`, `.WAIT`, `.by_name`, or `env.action_ids["WAIT"]` API is supplied.

`get_action_label_names()` is only a display-label route: ENV:730–742 returns `self.action_labels.get_all_labels()`. Labels are copied from compiled selected-level metadata at ENV:154–164. ENV does not prove that a display label equals the authored action name, so label lookup is not substituted for the record-name route.

## Step return, successor mask, and expression timing

The complete normal extraction is `next_observations, rewards, dones, info = env.step(actions)`; explicitly supplying `depletion_multiplier=1.0` is equivalent to the visible default. ENV:1218 returns exactly `(observations, rewards, self.dones, info)`, with documented shapes at ENV:1082–1087:

| Tuple entry | Source-verified structure |
| --- | --- |
| `observations` | Direct token encoder tensor, `[env.num_agents, env.observation_dim]`, obtained at ENV:1192. There is no `.obs` extraction or reset-style tuple. |
| `rewards` | Tensor documented `[env.num_agents]`; calculated through imported reward helper at ENV:1168, then adjusted/masked at ENV:1169–1175. The helper's reward formula/dtype is not inspected. |
| `dones` | Current `self.dones`, documented bool `[env.num_agents]`; returned without a clone at ENV:1218. This is a combined completion flag; there are no separate terminated/truncated tuple entries. |
| `info` | A dictionary whose exact keys and ownership are below. |

The action is taken at existing instant k. ENV clones entry dones and computes activity (ENV:1089–1090), resets tick-scoped registry state (ENV:1091), executes the action (ENV:1095–1101), applies passive depletion/cascades/effects and remaining compiled phases (ENV:1103–1136), increments `global_tick` once and publishes it (ENV:1138–1140), then evaluates VFS profiles (ENV:1142–1146). Terminal evaluation, eligible step counting, item aging/respawn, lifespan/rewards, and hour update occur before the returned observation (ENV:1148–1192). Thus a first normal step after reset returns the observation at tick 1; WAIT does not suppress passive rules or expression reevaluation in this orchestration. Frozen meter behavior must come from the authored compiled pack, not state injection or an assumed effect of WAIT.

At ENV:1195 the method constructs `successor_action_masks = self.get_action_masks().clone()` **after** the observation/status/hour commit. This is the owned mask associated with the returned successor observation. It rejects any nonterminal row with no legal successor action at ENV:1196–1202, including pack/level/tick/agent IDs in the `ValueError`. Completed rows may be empty (ENV:1193–1194). There is no automatic episode reset in this method.

The exact `info` dictionary at ENV:1204–1216 is:

| Key | Visible value / ownership |
| --- | --- |
| `successor_action_masks` | The cloned bool `[num_agents, action_dim]` successor mask from ENV:1195. |
| `active_on_entry` | Clone of the entry activity mask. |
| `newly_terminal` | Clone of authored-terminal-or-newly-retired mask. |
| `newly_retired` | Clone of lifespan completion mask. |
| `step_counts` | Clone of current step counts; initialized as long at ENV:801. |
| `positions` | Clone of current positions; substrate-dependent width/dtype. |
| `successful_interactions` | Direct executor result; comment documents `{agent_idx: affordance_name}`. |
| `reward_components` | Direct `self._last_reward_components` dictionary, not a clone; comment calls it DAC breakdown. |
| `intrinsic_weight` | Direct `self.intrinsic_weights`, not a clone. |
| `effect_spawn_refusals` | Empty tuple if no effect manager; otherwise a tuple of its new refusal records since step entry. Record structure is external. |

## Required compiled settings and cleanup boundary

Construction consumes the real selected compiled level, including its `training`; it does not accept a separate observation specification or runtime action-count override. Visible local requirements include explicit non-null `training.enabled_affordances` (ENV:123–125), compiled action labels (ENV:154–157), a truthy `experiment.experiment_name` (ENV:169–175), bounds for every compiled meter (ENV:227–248), and an explicit `curriculum.day_length` when temporal mechanics are active (ENV:126–139). Configured spatial affordances require explicit positions when randomization is off (ENV:448–480). When an item catalog is supplied, item profiles must exist and compiled item token capacity must equal the per-world arena size (ENV:644–661). The lifespan comes from `training.training_loop.max_steps_per_episode` at ENV:147; a one-step live case therefore also depends on its actual authored terminal rules/lifespan. These are visible ENV dependencies, not a complete validator/schema for valid pack YAML. All additional compiler/DTO/helper validations are outside this source.

The complete 1714-line class defines **no `close()`, `__enter__`, `__exit__`, `__del__`, or other public disposal method** and exports no explicit environment cleanup function. Reset is episode-state reset, not disposal. This receipt therefore cannot supply an `env.close()` or `with VectorizedHamletEnv...` protocol. Ordinary release of the Python reference (`del env`) is not a project-defined cleanup contract and does not prove immediate release of any imported helper's resources or torch allocator storage. If an external factory/harness requires cleanup beyond ordinary object lifetime, that exact API is missing from ENV and must come from its separate supplier. No speculative cleanup call is needed to extract the reset/step tensors from the visible API.

## Custody and disposition

Only this ignored receipt was written. The destination is covered by `.git/info/exclude:7:/.superpowers/`. No project import, runtime, collection, pytest, compiler, linter, probe, helper/test/source/tracked-document edit, index/commit/push, new branch/worktree/checkout/copy/deletion, `.oracle` action, or subdelegation occurred. No checkout was created, removed, or switched; all 14 existing checkouts were left untouched. The running T16R2 frozen qualification and source/runtime barrier remain intact. This is static API evidence, not runtime acceptance. Worker returns stationary after handoff.
