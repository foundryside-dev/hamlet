# SG2 — Variable & Feature System (VFS)

**Location:** `src/townlet/vfs/` (7,080 LOC, 15 files)
**Confidence:** High — read all 15 module files in full or in targeted sections; cross-verified consumers in `src/townlet/environment/vectorized_env.py`, `src/townlet/environment/dac_engine.py`, `src/townlet/items/manager.py`, `src/townlet/effects/context.py`. VTC acronym expansion confirmed directly from source docstring (`src/townlet/vfs/vtc.py:1` — "VFS Transition Compiler").

## Responsibility

The VFS is the declarative state-space layer for Townlet's vectorized environment. It owns three concerns:

1. **State storage and access control.** Pydantic schemas (`schema.py`) describe variables, observation fields, action writes, and normalization. The `VariableRegistry` (`registry.py`) allocates GPU/CPU tensors for every declared variable, indexed by scope (`global`, `agent`, `agent_private`, `item`, `pair`, `group`, `affordance`, `zone`, `message`), and enforces reader/writer ACLs at every `get`/`set` (`registry.py:512-525`, `545-565`).
2. **Compiled transition execution (VTC = VFS Transition Compiler).** `vtc.py` and `vtc_kernels.py` define nine families of frozen-dataclass "compiled" rule programs plus their TorchScript inner kernels. Each program walks its rules in declared phases and produces a new VFS/bar snapshot under masked, mask-broadcasted, optionally clamped writes. The environment hot path in `vectorized_env.step()` invokes these programs once per tick (`vectorized_env.py:1106-1169`).
3. **Observation construction and profile evaluation.** `observation_builder.py` flattens registry tensors into per-batch observation rows according to a `VFSObservationSpec`; `evaluator.py` runs profile-compiled ASTs (`profiles.py`) over a per-step `ExecutionContext` with optional mark-and-sweep gating and temporal-history tracking.

The package is also the source of canonical schema-hash provenance (`schema_hashes.py`) used to fingerprint variable/observation/action/transition-graph identity for checkpoint compatibility.

## Conceptual model

- **Variables.** Defined by `VariableDef` (`schema.py:359-533`). Each variable has an `id`, a typed `scope` (`VariableScope` StrEnum at `schema.py:28-39`), a `type` from a closed set (scalar, vec2i/3i/2f/3f/vecNi/vecNf, bool, agent_ref/item_ref/affordance_ref/effect_ref, tensor1d/2d/3d/Nd, message_token), a `lifetime` (`tick` / `episode` / `persistent`), and explicit `readable_by` / `writable_by` reader lists. `lifetime="tick"` is reset by `VariableRegistry.reset_tick_scoped()` and `"episode"` by `reset_episode_scoped()` (`registry.py:589-600`).
- **Observation fields.** `ObservationField` (`schema.py:288-356`) maps a `source_variable` to an output observation field with `shape`, optional `NormalizationSpec`, `semantic_type` ∈ {bars, spatial, affordance, temporal, custom}, and `curriculum_active` flag used to mask padded dims out for transfer learning (`observation_builder.py:302-311`).
- **Features / VFSObservationSpec.** `VFSObservationSpec` (`observation_builder.py:147-299`) is the compile-time spec that fixes the order and dimensionality of the observation contribution: `global_vfs_dim`, `agent_vfs_dim`, `item_vfs_dim`, ordered name tuples, and per-section active masks. It is built from compiled VFS profiles (`from_compiled_profiles`, `observation_builder.py:281-299`) and used at runtime by `build_vfs_observation` (`observation_builder.py:314-474`).
- **VTC programs.** Each VTC program is a frozen `@dataclass` containing a tuple of compiled rules; `apply(...)` evaluates the rules in declared phase order, snapshotting per phase and committing masked candidates per variable. Inner numerics go through `@torch.jit.script` kernels in `vtc_kernels.py`. The phase vocabulary is fixed by `transition_graph.DEFAULT_TRANSITION_PHASES` (`transition_graph.py:7-26`).
- **Schema hashing.** `schema_hashes.py` produces canonical, sorted JSON payloads for variable, observation, action, and transition-graph schemas, then SHA-256s them. `compute_vfs_hash` concatenates the four digests into a combined VFS identity (`schema_hashes.py:124-132`). The registry exposes `variable_schema_hash` as a property (`registry.py:200-202`) and tracks a `variable_schema_generation` counter incremented on every dynamic add/remove (`registry.py:368-385`).

## Key components

- `schema.py:28-39` — `VariableScope` StrEnum: nine scopes (global, agent, agent_private, item, pair, group, affordance, zone, message).
- `schema.py:42-183` — `NormalizationSpec` with ten kinds (none, minmax, zscore, cyclical_sin_cos, one_hot, binary, log_scaled, clipped_log_scaled, rank_scaled, masked_value). Validators enforce per-kind required params (`schema.py:128-164`).
- `schema.py:186-285` — `WriteSpec`: variable_id, expression string, optional condition, composition (11 strategies: overwrite, additive_delta, multiplicative_modifier, min, max, clamp, priority_write, last_write_wins, claim_if_free, capacity_claim, append_event), phase, integer priority ≥ 0, optional clamp, telemetry_label.
- `schema.py:288-356` — `ObservationField` with `semantic_type` and `curriculum_active`.
- `schema.py:359-533` — `VariableDef` with `validate_vector_types` enforcing dims/shape consistency.
- `schema.py:536-570` — `load_variables_reference_config`: parses `variables_reference.yaml`, rejects expressions and item-scoped vars (those belong in `vfs_profiles.yaml`).
- `registry.py:79-874` — `VariableRegistry`: storage allocator + ACL enforcer. CPU and CUDA both supported (`device: torch.device`, `registry.py:139`). Tensors are torch tensors typed by variable type (float32 for scalars/vectors/tensors, long for ref types, bool for bool) (`registry.py:395-414`).
- `registry.py:43-53` — `DynamicVariableMutation` audit record. Dynamic add/remove is gated by `dynamic_variable_mode=True` and must declare `network_shape_effect` ∈ {`shape_stable_internal`, `observation_schema_changed`}; agent-observable variables MUST use the latter (`registry.py:321-385`).
- `registry.py:877-1049` — `ScopedVariableRegistry`: an alternative simpler scoped store (global/agent/item) with its own `check_access` (`registry.py:1013-1049`). Not the registry used by `vectorized_env`; it is parallel scaffolding. (Open question — see below.)
- `evaluator.py:26-219` — `VFSEvaluator`: holds an optional `TemporalHistory` (from `townlet.world.expression.history`), supports `MARK_AND_SWEEP` (requires explicit `marks`) and `EAGER` modes (`evaluator.py:19-23`). `evaluate_global_profile` builds an `ExecutionContext` and runs the profile's variables in topo order, updating `context.vfs` so later vars see earlier results (`evaluator.py:91-206`). History keys with `bar.` and `vfs.` prefixes are pushed after each step (`evaluator.py:53-83`).
- `vtc.py:1-2990` — VTC programs and compilers (catalog below).
- `vtc_kernels.py:1-80` — five `@torch.jit.script` kernels: `apply_masked_candidate`, `apply_passive_depletion`, `apply_threshold_cascade`, `apply_modulation_multiplier`, `apply_terminal_condition`.
- `observation_builder.py:25-53` — `_variable_observation_dim`: flattening rules per type.
- `observation_builder.py:83-144` — `apply_normalization`: implements all ten normalization kinds.
- `observation_builder.py:147-299` — `VFSObservationSpec` dataclass + `_from_variable_iterables` constructor; `max_items_per_agent` defaults to 3, `max_item_profiles` to 5, `max_tensor_elements` guardrail 1,000,000.
- `observation_builder.py:314-474` — `build_vfs_observation`: concatenates `[global | agent | item]` segments for a batch.
- `profiles.py:74-346` — `VFSProfileCompiler`: builds dependency DAG with NetworkX (`profiles.py:88-118`), parses each expression to AST via `ExpressionParser`, type-checks via `TypeChecker`, raises `CircularDependencyError` on cycles (`profiles.py:200`). Produces `CompiledGlobalProfile` and `CompiledItemProfile`.
- `history.py:25-108` — `HistoryCollector` + `collect_history_requirements`: walks compiled profile ASTs and computes per-key window requirements for the seven temporal functions {lag, delta, moving_average, ema, rate_of_change, rising_edge, falling_edge} (`history.py:8`).
- `dynamic_needs.py:17-159` — canonical fixed-slot and set-encoder dynamic-need variable factories; `DynamicNeedTokenLayout` describes the set-encoder tensor shape (id_embedding + 3 scalars + tag_embedding + satisfaction_embedding per token; `dynamic_needs.py:33-71`). All declare `writable_by=["engine","vtc"]`, `readable_by=["agent","engine","social_model"]`.
- `communication.py:10-27` — `canonical_l6_message_variables`: one `message`-scope `message_token`-typed variable `recent_message_tokens` written by `vtc`, read by `agent` and `social_model`.
- `relational.py:10-61` — `canonical_l5_relational_variables`: pair-scope `trust` and `obligation`, agent-scope `public_reputation`, group-scope `norm_legitimacy`. All written by `vtc`.
- `transition_graph.py:7-71` — `DEFAULT_TRANSITION_PHASES` (18 phases, `transition_graph.py:7-26`) and `TransitionPhaseGraph` with canonical payload + edge enumeration + `sort_key`.
- `schema_hashes.py:26-271` — five canonical-payload builders and SHA-256 hashers; `_canonical_transition_rule` is a structural walker that handles both `WriteSpec`-style action writes and rule-style transition entries (`schema_hashes.py:178-232`).
- `generalisation.py:106-451` — held-out generalisation harness; rewrites surface labels through a per-pack symbol table (`_SurfaceSymbols`, `generalisation.py:142-153`), then asserts train/test packs share causal-profile and operator-grammar counters. `_STABLE_IDENTIFIERS` and `_STABLE_PATH_SEGMENTS` (`generalisation.py:70-102`) enumerate identifier names that are preserved unmasked.

## VTC programs catalog

VTC = "VFS Transition Compiler" (`vtc.py:1`). All nine programs are frozen dataclasses with `apply(...)` methods; compilation is done at env construction time and apply is called per env step. Cross-references to caller sites are in `src/townlet/environment/vectorized_env.py`.

| Program | File:line | Compiles | Computes (per step) | Caller |
|---|---|---|---|---|
| `VTCActionWriteProgram` | `vtc.py:395-930` | `compile_vtc_action_writes(actions)` (`vtc.py:2163`) — one `CompiledVTCActionWrite` per action's `WriteSpec` | Phase-grouped writes: composes 11 strategies (overwrite, additive_delta, multiplicative_modifier, min, max, clamp, priority_write, last_write_wins, claim_if_free, capacity_claim, append_event) and commits via masked `apply_masked_candidate` | `vectorized_env.py:1226` (`_apply_vtc_action_writes`) |
| `VTCThresholdCascadeProgram` | `vtc.py:933-1003` | `compile_vtc_threshold_cascades(cascades)` (`vtc.py:2277`) | Applies one-sided threshold cascades (source < threshold → delta on target); uses `vtc_kernels.apply_threshold_cascade` (`vtc.py:970-979`) | `vectorized_env.py:1260` (`_apply_vtc_threshold_cascades`) |
| `VTCPassiveDepletionProgram` | `vtc.py:1006-1079` | `compile_vtc_passive_depletions(meters)` (`vtc.py:2354`) | Per-bar passive decay multiplied by `depletion_multiplier` (curriculum); uses `vtc_kernels.apply_passive_depletion` (`vtc.py:1048-1055`) | `vectorized_env.py:1245` (`_apply_vtc_passive_depletion`) |
| `VTCModulationProgram` | `vtc.py:1082-1158` | `compile_vtc_modulations(modulations)` (`vtc.py:2415`) | Per-affordance multiplicative modifier from a low-bar; uses `vtc_kernels.apply_modulation_multiplier` (`vtc.py:1119-1127`). Returns `[num_agents]` multiplier tensor per affordance. | `vectorized_env.py:487` (passed into env factory wiring) |
| `VTCAffordanceGateProgram` | `vtc.py:1161-1214` | `compile_vtc_affordance_gates(affordances)` (`vtc.py:2715`) — opening-hours gates | Evaluates per-affordance scalar boolean from current `time_of_day` via expression AST | `vectorized_env.py:612` (`is_affordance_open(...)` per-affordance) |
| `VTCInteractionProgressProgram` | `vtc.py:1217-1355` | `compile_vtc_interaction_progress(affordances)` (`vtc.py:2498`) | Multi-tick affordance progression: advances ticks_done when same agent stays on same affordance and position, fires completion event on duration reached. Returns `VTCInteractionProgressResult` (`vtc.py:383-391`) | (compiled at `vectorized_env.py:411`; runtime caller not located in this scan — see Concerns) |
| `VTCTerminalConditionProgram` | `vtc.py:1358-1419` | `compile_vtc_terminal_conditions(meters)` (`vtc.py:2611`) | OR-merges triggered terminal flags into existing `dones` via `vtc_kernels.apply_terminal_condition` (`vtc.py:1396-1402`) | `vectorized_env.py:1274` (`_apply_vtc_terminal_conditions`) |
| `VTCSocialResidueProgram` | `vtc.py:1422-1750` | `compile_vtc_social_residue_rules(...)` (`vtc.py:1810`); kinds `{visibility_effect, social_residue, institutional_rule}` (`vtc.py:1807`) | Per-phase masked writes against social/relational VFS variables; supports pair-scope and agent-scope masking with broadcast (`vtc.py:1713-1750`) | (compiled but runtime caller not located in this scan — see Concerns) |
| `VTCRewardProgram` | `vtc.py:1753-1806` (continues past 1800) | `compile_vtc_reward_components(drive_config)` (`vtc.py:2011`) | Wraps the DAC backend's `calculate_rewards(...)`; validates that declared components (`extrinsic`, `intrinsic`, `intrinsic_raw`, `shaping`) are present and shape-aligned to `dones` (`vtc.py:1782-1800`) | `vectorized_env.py:418` (compiled); reward backend is `DACEngine` (`environment/dac_engine.py`) |

The compiler entry points each have a `_with_phase_graph` variant (e.g. `compile_vtc_action_writes_with_phase_graph`, `vtc.py:2168`) that takes a `TransitionPhaseGraph` plus an affordance-id sequence and pins each compiled rule's `phase` against the canonical phase ordering.

## Access-control model

Variables declare two lists of role strings: `readable_by` and `writable_by` (`schema.py:458-466`). The enforcement points in `VariableRegistry`:

- **Read** — `VariableRegistry.get(variable_id, reader)` checks `reader in var_def.readable_by` and raises `PermissionError` otherwise (`registry.py:512-514`). For `scope="agent_private"`, the `agent` reader is additionally rejected even if listed (`registry.py:518-522`).
- **Write** — `VariableRegistry.set(variable_id, value, writer)` checks `writer in var_def.writable_by` (`registry.py:551-553`) and validates shape and dtype against the recorded `_expected_shapes` / `_expected_dtypes` (`registry.py:555-562`).
- **Engine bypass** — `VariableRegistry.set_engine_value` is a permission-checked write path for VFS evaluator outputs that may have a different per-agent shape than the declared global scalar (e.g., an expression batch-projects a global). It still requires `"engine" in writable_by` (`registry.py:567-587`).

Canonical role vocabulary observed in source: writers `{engine, actions, vtc}`; readers `{agent, engine, acs, bac, other_agents, social_model}` (collected from `dynamic_needs.py`, `communication.py`, `relational.py`).

There is a second access model in `ScopedVariableRegistry.check_access` (`registry.py:1013-1049`) using path strings (`"profile.var"`) and operation strings, but this class does not appear to be wired into `vectorized_env`; see Open questions.

## Public API surface

`__init__.py` re-exports:
- Schema: `VariableDef`, `ObservationField`, `NormalizationSpec`, `WriteSpec`
- Registry: `VariableRegistry`, `VFSRegistryProtocol`, `DynamicVariableMutation`
- Observation builder: `VFSObservationSpec`, `apply_normalization`
- Canonical variable factories: `canonical_fixed_slot_dynamic_need_variables`, `canonical_set_encoder_dynamic_need_variables`, `canonical_l6_message_variables`, `canonical_l5_relational_variables`, `dynamic_need_token_layout`, `DynamicNeedTokenLayout`
- Schema hashing: `canonical_{variable,observation,action,transition_graph}_schema`, `compute_{variable,observation,action,transition_graph,vfs}_hash`
- Transition graph: `TransitionPhaseGraph`, `DEFAULT_TRANSITION_PHASES`
- VTC: all nine `CompiledVTC*` dataclasses, all nine `VTC*Program` dataclasses, the `VTC*Source` protocols (`VTCActionWriteSource`, `VTCRewardConfigSource`, …), `VTCInteractionProgressResult`, and all `compile_vtc_*` / `compile_vtc_*_with_phase_graph` functions
- VTC kernel module: `vtc_kernels`
- Generalisation harness: `VFSGeneralisationPack`, `VFSGeneralisationReport`, `VFSGeneralisationSignature`, `assert_held_out_generalisation_split`, `build_vfs_generalisation_signature`, `operator_grammar_signature`

`VFSEvaluator` and `EvaluationMode` from `evaluator.py` are **not** exposed in `__init__.py` (`__init__.py:1-182`); consumers must import from `townlet.vfs.evaluator` directly (cf. `environment/vectorized_env.py:30`).

## Dependencies

**Inbound** (importers of `townlet.vfs.*`, evidence from `grep "from townlet.vfs"` over `src/townlet/`):
- `townlet.environment.vectorized_env` — primary consumer; imports the eight runtime VTC programs, `VFSEvaluator`, `EvaluationMode`, `VFSObservationSpec`, `VariableRegistry`, and the eight `compile_vtc_*` entry points (`vectorized_env.py:30-49`). Calls registry/programs in `step()` (`vectorized_env.py:1102-1283`).
- `townlet.environment.dac_engine` — imports `VariableRegistry` and uses it as the canonical state source for DAC reward computation (`dac_engine.py:25, 51`).
- `townlet.environment.action_executor`, `townlet.environment.observation_encoder`, `townlet.environment.action_config` — consume VFS types and registry (per import grep).
- `townlet.effects.context.EffectContext` — holds an optional `VariableRegistry` (`effects/context.py:10, 30`); the effect executor reads `.variables` to introspect declarations (`effects/executor.py:684`).
- `townlet.items.manager.ItemManager` and `townlet.items.action_handlers` — accept `VariableRegistry` for item-scoped VFS state (`items/manager.py:65`, `items/action_handlers.py:35`).
- `townlet.universe.*` — `universe.compiler`, `universe.pipeline`, `universe.compilers.observation`, `universe.compilers.vfs`, `universe.compiled`, `universe.adapters.vfs_adapter`, `universe.symbol_table`, `universe.raw_configs_v21` all import VFS types as part of the seven-stage UAC pipeline that produces `compiled_vfs_profiles` and `vfs_observation_spec` for the environment.
- `townlet.config.vfs_config` — imports VFS schema types.

**Outbound** (what `townlet.vfs.*` depends on):
- Stdlib: `enum`, `pathlib`, `typing`, `collections.abc`, `dataclasses`, `hashlib`, `json`, `logging`, `math`
- Third-party: `torch` (registry, kernels, evaluator, programs); `pydantic` (`BaseModel`, `ConfigDict`, `Field`, `model_validator`, `ValidationError`) in `schema.py`; `yaml` (in `schema.load_variables_reference_config`); `networkx` (`profiles.py:8`); `pyparsing` (only `ParseException` re-raised in `generalisation.py:11`)
- Internal: `townlet.world.expression` — `ASTNode`, `ExpressionParser`, `Evaluator`, `ExecutionContext`, `TemporalHistory`, `TypeChecker`, all AST node classes (used by `evaluator.py`, `profiles.py`, `vtc.py`, `history.py`, `generalisation.py`)
- Internal: `townlet.config.vfs_profiles_config` — `GlobalVFSProfileConfig`, `AgentVFSProfileConfig`, `ItemVFSProfileConfig` and their variable configs (consumed by `observation_builder.py`, `profiles.py`)

There are **no** outbound imports from `townlet.vfs.*` into `townlet.environment.*` or `townlet.universe.*`, so the VFS package sits below the env/universe layers.

## Patterns observed

- **Compile-once-apply-many.** Every VTC program is built once in `VectorizedHamletEnv.__init__` (`vectorized_env.py:409-418`) and reused per step. Compiled rules carry pre-parsed `ASTNode` for both `expression_ast` and `condition_ast`, avoiding per-step re-parsing.
- **Phase-grouped masked commits.** All VTC `apply()` methods iterate `_iter_phase_groups()` (e.g. `vtc.py:436-452`), snapshot the start-of-phase state, compute every effect against that snapshot, then commit. This is consistent across `VTCActionWriteProgram`, `VTCThresholdCascadeProgram`, `VTCPassiveDepletionProgram`, `VTCModulationProgram`, `VTCSocialResidueProgram`.
- **TorchScript inner loops.** All numeric kernels (`vtc_kernels.py:8-80`) are `@torch.jit.script` annotated — five small functions, each ≤ ~12 LOC, designed to be JIT-compiled away from Python overhead.
- **Frozen-dataclass rules.** All `Compiled…` containers are `@dataclass(frozen=True)`, giving immutable per-rule provenance suitable for hashing.
- **ACL on every read/write.** No hot-path bypass except the explicitly named `set_engine_value` (`registry.py:567`), and that still checks `"engine" in writable_by`.
- **Protocol-based source ducktyping.** Each compiler entry point declares a `VTC…Source` `typing.Protocol` (`vtc.py:19-148`) describing the minimal shape it needs, decoupling the VTC compilers from the universe-compiler DTO types.
- **Schema hashing as identity.** `schema_hashes._hash_payload` (`schema_hashes.py:255-262`) commits to a strict canonical JSON (`sort_keys=True, separators=(",", ":")`) — deterministic across Python implementations.
- **`_with_phase_graph` overloads.** Every compiler ships a variant that consumes a `TransitionPhaseGraph` to pin rule phases against the canonical ordering, supporting transition-graph hashing in `schema_hashes.canonical_transition_graph_schema` (`schema_hashes.py:56-91`).

## Concerns

- `VariableRegistry.get` returns `value.clone()` (`registry.py:524`) and `set` clones the input (`registry.py:565`). Two defensive copies per read/write on every variable touched is potentially expensive in the env step; consumers that read many variables (e.g. `_current_vfs_state`, `vectorized_env.py:1287`) clone every variable in the registry per step. Not necessarily a bug, but a measurable cost surface.
- **`ScopedVariableRegistry` (`registry.py:877-1049`) appears to be parallel/legacy scaffolding.** It implements an alternative access-control model based on path strings (`registry.py:1013-1049`) but is not imported or instantiated anywhere in `src/townlet/environment/`. The CLAUDE.md "ANTIPATTERN: Keeping obsolete code 'just in case'" rule applies if this is dead.
- **Two VTC programs compiled but no caller located in this scan.** `VTCInteractionProgressProgram` and `VTCSocialResidueProgram` are compiled in env init (`vectorized_env.py:411, 414` and the missing social-residue line) but no `_apply_vtc_interaction_progress` / `_apply_vtc_social_residue` method appears in the lines I inspected (`vectorized_env.py:1102-1300`). Either the caller is elsewhere in the env file, or these programs are computed-but-unused. Worth verifying in a follow-up sweep.
- The `__init__.py` exports `VFSGeneralisationPack` / `assert_held_out_generalisation_split` etc. but never `VFSEvaluator` or `EvaluationMode`. Consumers must reach into `townlet.vfs.evaluator`, which is inconsistent with the package's otherwise comprehensive `__init__` re-export pattern.
- `VTCRewardProgram.apply` (`vtc.py:1760-1781`) delegates entirely to an external `reward_backend.calculate_rewards(...)` whose signature is implicit (`**dict(reward_context)`). The VTC layer only validates output shapes and component-name presence (`vtc.py:1783-1799`), not input contract — surfaces a tight coupling to `DACEngine`'s exact kwargs convention that is not documented at the VTC interface.
- `VTCInteractionProgressProgram.apply` uses a per-agent Python loop (`vtc.py:1257-1291`) — not vectorized. For low agent counts this is fine; at scale this is a serial bottleneck inside an otherwise GPU-native pipeline.
- `_extract_variable_refs` in `profiles.py:120-167` walks AST attributes via `hasattr(...)` chains rather than using an `ASTVisitor`. `history.py` already shows the `ASTVisitor` pattern works fine here. Mild duplication and brittleness if new AST node fields are added.
- `VariableRegistry._max_tensor_elements = 1_000_000` is assigned twice — once at `registry.py:144` and again at `registry.py:173`. Cosmetic, but indicates either historical drift or copy-paste residue.
- `set_engine_value` (`registry.py:567-587`) only honours `_expected_shapes` for sparse-pair variables and otherwise lets the engine write an arbitrary shape. This is the documented intent ("expressions can legitimately produce per-agent batches for variables declared as global scalars") but means the registry's shape invariant is conditional on the writer identity — a subtle invariant worth calling out in the schema docs.

## Open questions

- Is `ScopedVariableRegistry` (`registry.py:877`) live, or stale duplicate scaffolding? Tests `test_scoped_registry.py` exist in the unit suite, but no production import site found.
- Where are `VTCInteractionProgressProgram` and `VTCSocialResidueProgram` actually executed at runtime? They're compiled in env init but my scan of `vectorized_env.step()` did not surface the call sites. Tests `test_vtc_interaction_progress.py` and `test_vtc_social_residue.py` exist, so the programs are exercised under test — production wiring needs confirmation.
- The `transition_graph.DEFAULT_TRANSITION_PHASES` lists 18 phases, but only a subset map to VTC programs (no obvious VTC program for `ingest_actions`, `advance_global_time`, `compute_action_legality_masks`, `apply_action_effects`, `apply_completion_bonuses`, `clamp_and_validate`, `emit_observation_features`, `emit_telemetry`). Are those phases enforced elsewhere, or are they nominal ordering hints only?
- `VFSEvaluator.evaluate_all` (`evaluator.py:208-219`) is described as a "Utility for benchmarks". Whether it has any production callers should be verified.
