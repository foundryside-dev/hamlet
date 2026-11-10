# Current compiled policy developer contract

This source-verified contract describes the bounded compiled-policy transport qualified at R2 candidate treee18e85776f16b507040c1671310b17595fb26b21 and unchanged in root R3 tree92d2c815. Root reports51 owned passes in100.8851s wall, independent26passes/25deselected in103.912s with custody PASS and unchanged hashes, and all six global guards PASS including mypy0/compilerCLI147.287s. These are received root/reviewer results, not this document author's executions. No integrated BAC release is declared.

At that R2 compiled-policy review, the five counted source/test files were compiler.py976,compiled.py1651,test_effective_run.py323,test_curriculum_compiled_roster.py365,metadata.py165READONLY, total3480/ceiling4700. Root reports all five source hashes identical between R2 and R3; R3 changes only a separately owned stale token-gate test fixture. This document uses those sources and accepted T21/manager producer receipts without extra implementation reads. Only this ignored prose file is authored; no source/test/runtime/import/Git/index actions.

## Real authored compilation and factory handoff

The actual public compiler signature is:

```python
UniverseCompiler.compile(
    experiment_dir: Path,
    primary_level: str | None = None,
    use_cache: bool = True,
) -> CompiledUniverse
```

An explicit actual authored primary_level is required; omission raises ValueError. A real smoke-pack route, assuming repository cwd, is:

```python
from pathlib import Path

import torch

from townlet.curriculum.factory import build_curriculum
from townlet.universe.compiler import UniverseCompiler

compiled = UniverseCompiler().compile(
    Path("configs/test/token_set_smoke"),
    primary_level="L0_test",
    use_cache=False,
)
effective = compiled.effective_run
selected = compiled.get_level(compiled.metadata.primary_level)
declared_meter_names = tuple(meter.name for meter in selected.bars.meters)
assert effective.static_policy.active_meters == declared_meter_names
assert effective.options.curriculum is not None
curriculum = build_curriculum(
    effective.training,
    curriculum_options=effective.options.curriculum,
    static_policy=effective.static_policy,
    device=torch.device("cpu"),
)
curriculum.initialize_population(effective.training.population.size)
```

The factory/initialize signatures and policy constants are accepted T21/manager producer contracts, exercised by the received compiled tests. Factory returns an uninitialized manager, takes required resolved modes/policy/device, and has no horizon argument or configure_from_training adapter. Current options omissions resolve completion/stage_band; legacy_step refuses. Named immutable static policy is static-baseline-v1, difficulty0.5,reward shaped,depletion1.0,exact declared tuple. Pure resolve_bac_options remains roster-free; the separate OP baseline resolver owns that declaration. Compiled uses the accepted EF resolver's required declared_meter_names input with selected bars order, never re-resolves options in the factory.

CompiledUniverse.get_level(level_name) returns actual LevelMetadata. to_level delegates to it. metadata_for_level projects a level's summary; it does not switch compiled.effective_run to another level. Compile with the desired explicit primary_level to obtain its effective view rather than combining another level's projection with the existing run.

## Two legitimate meter orders

Per-level bars declaration order owns the actual static-policy tuple and compiler meter_declarations. Global environment declaration order owns public meter_metadata columns and their indices. MetadataCompiler explicitly enumerates environment.environment.meters and looks up initial values by bars name. These orders may legitimately differ; changing bars order must not silently reorder global metadata columns or be rejected solely for that difference.

Before deriving/publishing the effective view, CompiledUniverse validates:

- Environment names and each level's bars names are unique nonblank strings.
- Per-level meter_declarations exactly match ordered bars names.
- Each bars vocabulary has exact membership equality with the environment vocabulary: no missing, extra or duplicate names.
- Per-level meter_metadata names exactly match environment declaration order, with corresponding0..N-1 indices.
- Selected public summary meter_names,meter_count,meter_name_to_index match the selected meter_metadata view.

It returns the selected bars tuple to EF without sorting, substituting global order, injecting standard names or manufacturing absent roster values. Arbitrary names are supported. A coherent empty vocabulary is accepted by the new validator; received integrated compile witnesses cover authored permutation/arbitrary names rather than claiming a new empty-pack compilation proof.

## Current native APIs and expected-view binding

The only current native compiled schema is **1.42**, written under exact payload key `compiled_schema_version`. Effective payload key `effective_run` is required and contains required `static_policy` mapping. This carries accepted effective-run-v2 semantics; curriculum manager checkpoint state independently remains native version2.

Actual compiled transport APIs:

```python
compiled.to_dict() -> dict[str, Any]
CompiledUniverse.from_dict(payload: Mapping[str, Any]) -> CompiledUniverse
compiled.clone() -> CompiledUniverse
compiled.save_to_cache(path: Path) -> None
CompiledUniverse.load_from_cache(path: Path) -> CompiledUniverse
```

Native persistence uses MessagePack. from_dict/load_from_cache validate exact compiled version before interpreting nested products. Parent from_dict locally requires effective_run and static_policy mappings before child decoding, so missing/wrong-shape current declarations produce ValueError without fallback or synthesized policy. Accepted EF decoding explicitly reconstructs portable meter lists as typed tuples and validates its full current declaration/payload.

Child self-consistency and an execution hash alone are insufficient to bind a view to the actual compiled outer candidate. Compiled independently resolves expected actual brain/training/drive/selected-bars inputs with captured origins and compares the entire canonical transported EF payload through existing validate_payload. A fully rehashed foreign-roster view therefore refuses; this also holds under adversarial selection where inactive static-policy roster is excluded from selected execution hash.

from_dict validates existing token/policy coherence, then compares expected actual EF before installing/returning that checked run. clone deep-copies actual outer products through existing serializers, reconstructs EF and compares expected cloned inputs before installation. to_dict validates against actual current inputs before exporting; save_to_cache obtains the validated export before packing/writing. Failed forged export does not overwrite preexisting target bytes. Validation does not mutate original serialized input/source view. Local candidate construction may initialize its own derived view before comparison, but a failed candidate is never returned as accepted.

## Historical data and mutable authored caches

Direct native loaders reject1.40,1.41 and every other old/unknown/missing version. There is no known1.40 derive branch, old field-list alias or pre-scope adapter in the current accepted transport. No historical state conversion/import programme follows from this contract. Original artifact bytes,data,manifests,digests and history remain preserved; the real15-artifact manifest loop and original pre-optimizer sequence digest are retained as direct read-only refusal/byte checks. Current recurrent runtime success is established through fresh actual authored compilation/native transport.

Compiler mutable-cache recovery is a separate supported capability. The actual cache path is config_dir/.compiled/universe-{primary_level}.msgpack; it does not embed schema or source digest. Provenance includes current package-source bytes, config content/path and dependency versions. Successfully loaded caches still undergo existing freshness/path/level checks. Old/corrupt/unusable cache loads can remain misses and rebuild from explicit current authored source; generated mutable cache entries may then be replaced at their existing path. This is fresh compilation, not an old-state decoder. Do not run authored compilation/save against protected historical fixture paths. Received cache tests use temporary authored data copies, while original historical artifacts use only direct read-only loaders/digests.

## Ownership, presets and identity meaning

Current dictionary/native/clone/cache transport preserves capture origins and complete effective payload. Exported data and returned model copies cannot mutate the owned effective view. Full canonical EF comparison retains inactive raw numeric NaN preset semantics; ordinary Python dictionary equality is not substituted for that canonical check. Native manager-state test assertions recursively compare every scalar/container/tensor, including exact tensor dtype/device/layout/shape/content; no readings are dropped or approximated.

Existing complete selected brain replacement,five training overrides,seeded network-weight behavior,provider selection/capacity precedence,replay choices,typed/unknown inactive presets and authored-versus-selected identity distinctions remain substantive. Compiled authored_brain_hash,authored_identity,execution_hash delegate to effective_run; historical brain_hash/pack_brain_hash/per-level training hash recipes are preserved. EFv2 binds full selected static declaration as policy context, so actual static roster names/order affect selected execution hash. Under adversarial, inactive static baseline remains transported but does not enter that selected projection. Full expected-view comparison is therefore required in either strategy.

Static reward_mode/active_meters roles remain unqualified application metadata. Their exact decisions/transport prove this configuration/factory contract, not environment reward switching,meter gating,all-lane physics or real runtime world identity. Test completion world IDs are declared fixture identities only. No claim of external artifact authentication follows from internal expected-candidate comparison.

## Continuing qualification

Root’s exact R3 candidate passes all153 broader compiler/direct-owner cases and the239 existing curriculum/factory regressions. The shared token-reader fixture was updated to current required arguments without changing its optimizer,target,RND or annealing assertions; both affected cases also passed independent Astra execution. Compiled production/source hashes are unchanged from the reviewed R2 candidate that passed51 owned cases,26 independent adversarial cases and all six global guards; the sole R3 difference is that fixture, with its own formatting/lint checks and source-equivalence receipt.

Pipeline/world lifecycle,all-lane mechanics,unfiltered full suite,complete real native/learning/restart/E2E and final BAC gates remain open. These results establish bounded compiled policy transport and caller compatibility, not whole-program qualification. Planned delivery continues after the durable checkpoint.

## Current world constructor transport
A later bounded constructor packet at R1tree6f46f449 extends CompiledUniverse.create_environment with required world_roster,training_seed,lane_world_ids alongside its existing required num_agents,level_name,device. It forwards through VectorizedHamletEnv.from_universe and env_factory.from_universe into the actual env_cls, preserving the exact declaration/seed/binding and device normalization. There is no inferred identity/default/old-signature path or automatic reset/bootstrap. Current compiled.py is1663lines SHA256d8e2734b0845c7d23ac79180a724b216d7c881e079352356f108cb294d2b7384; current native1.42/cache/policy serialization is unchanged. The joint193 (88constructor+54identity+51compiled) and independentAstra88 pass; globalmypy retains7oracle/POPreseterrors. See CURRENT-WORLD-CONSTRUCTOR-TRANSPORT.md for the source-verified signatures and remaining integration limits.
