# T18e parent fixture factual capsule

READONLY extraction, 2026-11-10. Metadata preceded bodies. Exactly the five whole sources below were inspected (3484 lines); no sixth implementation/test/helper, compiler implementation, Training DTO, ENV, POP, BANK, import, introspection, probe, runtime, compilation, git/index operation, branch/worktree/checkout, source copy or subagent. This ignored prose is the sole write. No test result is claimed. Public contracts and actual YAML were read as dependency API/data; their historical execution receipts are not executions here.

## Exact source inventory

| Whole source | Lines | SHA256 |
|---|---:|---|
| src/townlet/config/brain_config.py |568|6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079|
| src/townlet/universe/compiled.py |1663|d8e2734b0845c7d23ac79180a724b216d7c881e079352356f108cb294d2b7384|
| src/townlet/exploration/world_curiosity_state.py |883|cb8a7fd9f27c73537ec3f18f37b6cd5a3d88ca23c281b76376cece8be5f9dfb1|
| src/townlet/curriculum/factory.py |58|10be467c8ca72853bd8c6cceac60e6e13fcb4f202f1511fc7a9040539dbd9c71|
| src/townlet/config/world_roster.py |312|1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33|
| Total |3484|exactly five sources, <=5000|

Bodies were displayed in bounded chunks, including all1663 compiled lines and all883 world-state lines. Initial concatenated output truncation was followed by separate bounded reads. Supporting contracts: wave17 CURRENT-COMPILED-POLICY-UPDATED; wave15 CURRENT-CURRICULUM-POLICY-UPDATED; wave18 CURRENT-WORLD-IDENTITY-UPDATED; wave22 CURRENT-BACKEND-FACTORY-CONTRACT; wave26 CURRENT-ENV-ACCEPTED-AUTH-CONTRACT; wave33 T18d-RUNTIME-FIXTURE-API; wave34 CURRENT-EXPLORATION-RUNTIME-CONTRACT and CURRENT-CURIOSITY-CHECKPOINT-CONTRACT; wave35 parent brief/report/config fixture capsule. These are attributed API prose, not extra implementation reads.

## Genuine compiled/environment/carrier route

The public compiled contract qualifies (compiler body not inspected):

```python
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
compiled = UniverseCompiler().compile(
    Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False,
)
```

Actual signature is compile(experiment_dir: Path, primary_level: str | None = None, use_cache: bool = True) -> CompiledUniverse; explicit real primary level is required by the current producer. No compilation was run here. A fixture may instead explicitly re-export the genuine module-scoped `compiled` fixture documented in wave33 T18d-RUNTIME-FIXTURE-API. This imports a dependency API without reading its helper body.

Source-backed access paths (compiled.py263-474):

- `compiled.metadata.primary_level`; `compiled.available_levels` returns sorted names.
- `selected = compiled.get_level(compiled.metadata.primary_level)` returns the actual LevelMetadata, or raises ValueError for absent name. `to_level` delegates.
- `selected.training` is an actual TrainingV2Config; `selected.curriculum`, `.drive`, `.bars`, `.affordances` are actual config objects. `compiled.brain` is an actual BrainConfig. There is no `selected.brain` field.
- `selected.token_spec`, `.action_metadata.total_actions`, `.runtime_action_space`, `.meter_declarations`, `.meter_metadata`, hashes and optimization products are real per-level products.
- `compiled.metadata_for_level(name)` returns a projection with `observation_dim=selected.token_spec.total_dims`, `action_count=selected.action_metadata.total_actions`, and selected primary_level. It does not switch `compiled.effective_run` to that level. Compile the desired primary level.
- `compiled.effective_run` is derived against actual brain/selected training/selected drive intrinsic/selected bars roster during construction; schema1.42 transport independently validates the complete expected view. No fake CompiledUniverse/LevelMetadata construction is needed.

The source-backed constructor adapter (compiled.py778-819) is:

```python
env = compiled.create_environment(
    num_agents=N, level_name=compiled.metadata.primary_level, device=device,
    world_roster=roster, training_seed=seed, lane_world_ids=ids,
)
```

It forwards all arguments to genuine VectorizedHamletEnv.from_universe. The public world contract independently qualifies the direct constructor with the same required keywords plus universe=compiled. No automatic bootstrap/reset occurs. N must equal the actual declared membership cardinality and requested lane tuple, never a synthetic curiosity row count. Use the actual selected compiled TokenSpec dimensions/action count and confirm against actual ENV public geometry in the parent author's already-qualified ENV capsule. The exact *ENV geometry attribute spellings* are not established by these five sources; compiled public carriers above are established. No hardcoded D=3/A=2 or guessed ENV accessor is necessary.

Actual YAML data verified: pack `configs/test/token_set_smoke`, level `L0_test`, training seed42, population size8, max episodes10000, horizon1000, train frequency4, sequence length8, max grad norm10; replay capacity100000/batch32/min_size1000. Stratum is square grid8x8/clamp/manhattan/no diagonals; L0 active vision global and active_temporal false. Actual eight-meter declaration order is energy,health,satiation,hygiene,money,fitness,mood,social. Actual actions declaration inherits substrate actions and defines WAIT enabled-by-default and REST disabled-by-default; selected training explicitly enables REST. This data does **not** prove an integer action width or token width; those come from the actual compiled products.

For faithful unchanged-pack population construction N=8, define eight explicit IDs and use that exact roster/lane tuple throughout ENV/curriculum/POP/descriptor. For an intentionally smaller test population, explicitly author/validate the actual selected training population size or consistently initialize the real manager for that actual population; do not leave an eight-row curriculum paired silently with two ENV rows. This is fixture consistency, not permission to change production defaults.

## Actual BrainConfig and faithful payload

`townlet.config.brain_config.BrainConfig(**payload)` and `.model_validate(payload)` construct validated Pydantic objects. `load_brain_config(Path(pack))` safe-loads pack/brain.yaml and calls BrainConfig(**data); missing file raises FileNotFoundError; Pydantic ValidationError is formatted as ValueError. All declared brain submodels forbid extras and nonfinite numeric values. BrainConfig fields are all required: version,description,architecture,optimizer,loss,q_learning,replay. **Brain contains no authored observation_dim/action_dim/population fields.** Actual network geometry comes separately from ENV/TokenSpec/actual action width.

Literal actual pack brain payload, suitable as data for the genuine validator (description is the actual YAML string):

```python
{
    "version": "1.0",
    "description": "token-set smoke pack — the live token_set exerciser over the compiled TokenSpec (token-obs unit 3, hamlet-fa6bb6da4a)",
    "architecture": {"type": "token_set", "token_set": {
        "token_embed_dim": 16, "q_head_hidden_dim": 64,
        "aggregator": {"type": "mean"},
    }},
    "optimizer": {"type": "adam", "learning_rate": 0.0001,
        "weight_decay": 0.0, "schedule": {"type": "constant"},
        "adam_beta1": 0.9, "adam_beta2": 0.999, "adam_eps": 1e-8},
    "loss": {"type": "smooth_l1"},
    "q_learning": {"gamma": 0.99, "target_update_frequency": 1000,
        "use_double_dqn": True},
    "replay": {"capacity": 100000, "prioritized": False},
}
```

Prefer actual `compiled.brain` over duplicating this data. `apply_training_overrides(brain, training)` is a genuine public function in this inspected source (530-568), returning typed copied nested models without mutating originals. It maps exactly training.q_learning.gamma/target_update_frequency/use_double_dqn to brain.q_learning, training.q_learning.learning_rate to optimizer.learning_rate, and training.replay_buffer.capacity to replay.capacity. Thus `apply_training_overrides(compiled.brain, selected.training)` gives a source-backed effective brain route for this selected pack, with target frequency500 and double DQN False; LR.0001/gamma.99/capacity100000 remain as above. The comments distinguish selected base brain from overridden brain hash. Do not assume an unverified `effective.brain` accessor.

Other constructor invariants useful when deliberately authoring a small *real* brain: token embedding and Q-head hidden dimensions positive; token aggregator mean forbids num_heads, attention requires positive num_heads dividing embed width. Omitted token_encoder resolves linear at its declared owner. Replay capacity positive; prioritized False forbids PER-only fields; prioritized True requires alpha,beta,annealing. Optimizer Adam/AdamW requires all betas/eps; positive LR; nonnegative decay; constant schedule needs only type. smooth_l1 forbids huber_delta; huber requires positive delta. Q gamma in[0,1], target frequency positive. Architecture requires the selected config; this validator does not actually reject extra nonselected architecture subblocks despite the docstring's stronger prose. Recurrent one-layer LSTM requires dropout0. No fabricated brain SimpleNamespace is needed.

## Current real curriculum

The compiled/curriculum public contracts and actual factory58 establish:

```python
from townlet.curriculum.factory import build_curriculum

effective = compiled.effective_run
assert effective.options.curriculum is not None
curriculum = build_curriculum(
    effective.training,
    curriculum_options=effective.options.curriculum,
    static_policy=effective.static_policy,
    device=device,
)
curriculum.initialize_population(effective.training.population.size)
```

Returns a genuine uninitialized manager; caller initializes actual N once. Both commit/difficulty modes must be resolved even under static. Required modes: completion and stage_band|rate_limited. Actual static factory passes commit_mode,difficulty_level,reward_mode,list(active_meters),depletion_multiplier to StaticCurriculum. Actual adversarial factory passes completion/difficulty modes and all configured adaptation/min/max/survival thresholds/entropy gate/stage dwell/device. No horizon/configure_from_training adapter exists.

Public direct resolution alternative is `resolve_bac_options(training.bac_options, training=training)` then `resolve_static_baseline_policy(declared_meter_names=tuple(m.name for m in selected.bars.meters))`; use resolved.options.curriculum and the genuine resolved static policy. Static baseline constants are policy_id static-baseline-v1,difficulty.5,reward shaped,depletion1 and exact selected bars tuple. Reward/meter application mechanics remain unqualified metadata. This is actual curriculum construction, not a fake curriculum.

## Selected policy, descriptor and real runtime construction

The parent author already owns RP1279 and therefore its actual current resolver. None of these five bodies declares the EffectiveRunConfig exploration/replay property names: **unknown here**, so do not invent `effective.exploration_policy`/`effective.replay_options` or fabricate FieldRole records. A fully documented existing genuine policy producer is `policy(compiled, family, scope, mode)` in wave33 T18d-RUNTIME-FIXTURE-API, importable from tests.test_townlet.regressions.bac.test_pw_scope_conversion. It returns an actual resolved policy for all five families, shared/per_world and paced_fifo/occupancy_fifo. This helper's *policy return* is independent of Rig's geometry; using it does not authorize the Rig's synthetic service helper. Parent may use its owned RP resolver directly for explicit family/scope/service declarations. Resolve replay through the parent's actual owned public replay/config contract, not a made-up property.

Descriptor source entry (world_curiosity_state.py269-310):

```python
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor

descriptor = WorldCuriosityDescriptor.from_policy(
    selected_policy,
    world_ids=ids,                    # actual ENV lane order/membership
    observation_dim=actual_D,         # actual ENV/compiled TokenSpec width
    action_dim=actual_A,              # actual ENV/compiled action width
    training_seed=seed,               # same explicit ENV seed
)
```

No N parameter: N=len(world_ids). This derives provider_parameter_hash and private seeds from genuine resolved policy; no synthetic parameter hash/role construction. Full direct frozen-dataclass fields, all required, are schema_version,scope,provider_kind,provider_parameter_hash,observation_dim,action_dim,world_ids,seed_policy,service_clock_unit,origin,guarantee,training_seed,seeds. Shared tuple is legacy_shared_v1/vector_tick/shared_population_state; private is world_id_derived_v1/world_eligible_admission/world_id_owned_state and origin authored. Scope origin may otherwise authored|bac-options-v1. schema_version exact int1; D exact int>=0, A exact int>=1, seed exact int>=0; canonical lowercase64-hex parameter hash. Private IDs nonempty unique strings; all IDs owned as tuple. Shared seeds must be empty; private seeds exactly ID-keyed with model_init,target,predictor,service. Each private seed is derived from canonical sorted compact ensure_ascii JSON over schema world-curiosity-seed-v1, training_seed,exact world_id,provider_kind,component, taking first16 SHA hex characters and masking to63bits. Population/lane order/clocks/model values are excluded.

`to_dict` serializes world_ids/canonical_world_ids as lists plus ordered world_binding_hash, all direct fields and nested seed dictionaries. `from_dict` requires the exact full field set and checks canonical IDs/binding/hash/derived seeds. canonical_world_ids is sorted unique tuple; binding hash covers ordered IDs separately from policy identity. `seed_for(world_id,component)` only supports private scope.

Actual runtime public contract (wave34) supplies eight required keywords to `build_exploration` in townlet.config.exploration_policy: policy,descriptor,device,validate_accepted_episode,issuer_factory,report_allocation,validate_committed_batch,validate_parent_cadence. Bind `env.validate_accepted_episode` directly. `issuer_factory(owner)` receives **actual BANK**; return `WorldReceiptIssuer(owner=owner)` and retain that callback owner for ENV curiosity registration. Facade is a separate exploration owner. Actual callback implementations remain parent-owned work; a no-op validator cannot be called authentic parent cadence. All five selected families/scopes remain supported.

Public backend-factory contract: make_backend(policy, *, world_id,obs_dim,action_dim,device,rng,descriptor) and make_policy_selector(policy). Shared requires world_id/rng/descriptor=None. Private requires exact ID, actual descriptor, actual WorldRNGState; CPU device inventory(). WorldRNGState.create(*,descriptor,world_id,cuda_devices) and OwnedWorldBackend.construct(*,rng,factory) exist in this inspected source. Pass the callback candidate_rng into make_backend. Runtime/BANK ordinarily performs this construction; tests need not replace its provider. Factory Count/trainables require D>0; none allows0. No actual runtime execution is claimed.

## Immutable token fields and portable identity data

world_roster.py48-98 establishes:

- WorldRosterDeclaration(world_ids) frozen dataclass normalizes nonempty unique string tuple/list to tuple. from_dict requires exactly schema/world_ids with schema world-roster-v1 and serialized list. to_dict returns `{schema: "world-roster-v1", world_ids: list(...)}`. Semantic identity hashes sorted membership; manifest digest hashes canonical declaration bytes plus newline.
- WorldEpisodeReservation is frozen, identity-equal (`eq=False`) with world_ids,world_episode_seqs,batch_episode,_owner,_generation,_release. WorldAcceptedEpisode is frozen, identity-equal with world_ids,world_episode_seqs,batch_episode,_owner,_generation. These dataclasses do not themselves authenticate constructor inputs. Do not construct a purported accepted token; actual ENV reset receipt `.accepted` is the only valid current token.
- Real reset WorldRecord `.observation` returns owned data; `.accepted` preserves the original capability identity. WorldRecord's payload copying preserves issued record/token capabilities, clones tensors and copies mutable containers. `WorldOwnerReceipt.owner` exposes owner identity. None of _owner/_generation/_release belongs in portable data.

The exact *existing portable accepted-history record* in roster.py and public native contract is:

```python
{
    "batch_episode": accepted.batch_episode,          # exact nonnegative int
    "world_ids": list(accepted.world_ids),           # lane-ordered strings
    "world_episode_seqs": list(accepted.world_episode_seqs), # positive ints
}
```

Current world snapshot accepted_bindings requires these exact three keys and serialized lists. Last closure uses those same fields plus completion_content/participated_world_ids. The current checkpoint contract calls accepted value identity batch_episode/world_ids/world_episode_seqs. This is data, never a deserialized authority; native restore cannot recreate accepted token by constructing WorldAcceptedEpisode. The actual ENV validator accepts only identical current issued token, including while phases separately forbid work; copied/foreign/stale/manufactured objects refuse.

**Exact remaining carrier distinction:** neither these five bodies nor supplied parent brief defines a currently implemented POP `vector_step_progress.accepted_identity` serializer (the parent progress API is proposed). The three-key/list representation above is the existing portable data shape available for adopting in that owning T18e implementation. Calling it an already-existing POP API would be false. The BANK internal accepted_identity sequence-container representation is not specified exactly by the read public prose; it must not be guessed or used as authority. If the parent deliberately chooses this existing world-history shape for new progress, that is an explicit current implementation contract choice, not a missing fact that requires user permission.

## Existing versus owning implementation work

Existing: genuine current compilation, compiled/config/curriculum constructors above; real ENV roster/reservation/reset/token validation and cooperative registered-owner lifecycle; current runtime/factory/BANK component APIs; actual networks/replay via genuine POP.for_training as already owned by parent author.

Missing production implementation per parent-owned source/report, not fabricated APIs and not permission stalls: reservation-aware POP reset/accepted-token ownership; POP activation/empty receipts; runtime telemetry/current reset; POP prepare/claim/nonreentry/phase handoff; actual parent cadence validation and role wiring; seven-unit persisted ledger/progress; coherent current whole-parent native preparation/publication and external T26/HC/runner consumers. Implement those in the frozen parent/ENV/native owning steps under their approved contracts. No request to redesign, reduce capabilities or obtain routine go-ahead follows from these omissions.

An existing test-local boundary driver may explicitly control bootstrap/activation/completion only with actual registered component owner identities. It must name its cooperative external boundary role and cannot attest absent native/all-child/T26 work. Registering the driver as every component owner, using its synthetic width3/action2 service path, fabricating accepted token, fake __new__ POP, stand-in replay/curriculum or replacing composer does not demonstrate genuine parent integration. Genuine current ENV/POP/network/replay fixture construction is now supported by the factual carriers above; missing intended methods should produce causal RED at their real owning seam. Whole native/T26 E2E remains separately owed.
