# T18e real configuration and fixture API capsule

Read-only extraction, 2026-11-10; original T18e acceptance remains unchanged. This capsule is the only written artifact. No implementation, imports, runtime probes, tests, source copies, git operations, branches, worktrees, or helper introspection occurred. AGENTS.md, the named brief, T18e-original-task.md, and T18e-COMPOSER-READINESS-REPORT.md were read. Owner zero-backwards-compatibility rules supersede the original task's observation-only compatibility sentence: update obsolete callers directly; no adapters or fallback modes.

## Exact source inventory

Whole-file charges, even where reading was split into display chunks:

| Source | Actual | Ceiling | SHA-256 |
| --- | ---: | ---: | --- |
| tests/test_townlet/unit/environment/test_dac_engine.py | 3108 | 3150 | 3f55c7d95fa82f2293cdb999f7270f06888f04cabda00deb054c51a84c12a312 |
| src/townlet/config/drive_as_code.py | 605 | 650 | 870e44fbc55f4bc7a221e7272cebea893ff95bfe37f23c6e4e01c4e80595150c |
| tests/test_townlet/unit/vfs/test_vtc_reward_components.py | 93 | 100 | 46d9aaabe484e7d6a815a3292c8daa766436dde9dc93aed9a1550ea50e2f75c7 |
| src/townlet/vfs/registry.py | 897 | 900 | 8e9da37fb2df6308b7e0a65ec5898437e5151159a8377948607e8e58bc35d884 |
| tests/test_townlet/unit/environment/test_reward_calculator.py | 82 | 100 | 4af786337e3d719d6e3c9668c6fbf4811c9255906886f1cd164055d6202e83e0 |
| Total | 4785 | 4900 | Exactly five source files |

DAC/VTC/RWC production facts below come exclusively from the supplied composer readiness report. Their production sources, ENV, RP, schema, other tests, helpers, and compiled-universe sources were not opened. Destination is the ignored path designated by the brief; ignore state was not independently queried because git operations were prohibited.

## Real constructors and minimum coherent inputs

All following configuration classes are directly importable from `townlet.config.drive_as_code`; these are Pydantic models, not substitute config objects. All have `extra="forbid"`. Required top-level fields are `extrinsic: ExtrinsicStrategyConfig` and `intrinsic: IntrinsicStrategyConfig`. Other declared top-level fields are `version="1.0"`, `modifiers={}`, `shaping=[]`, and `composition=CompositionConfig()`. Explicit values below avoid relying on incidental defaults in the eventual test.

| Control | Accepted construction data | Effect / prerequisite |
| --- | --- | --- |
| Drive base | `IntrinsicStrategyConfig(strategy="rnd", base_weight=0.25, apply_modifiers=["double"])` | Base is independently authored, constrained to [0,1]. Strategy accepts rnd/icm/count_based/adaptive_rnd/none; a strategy label alone does not construct or prove a runtime provider. |
| Authored modifier | `ModifierConfig(bar="energy", ranges=[RangeConfig(name="all", min=0.0, max=1.0, multiplier=2.0)])`, under key `"double"` | Exactly one of bar/variable; ranges must cover [0,1] without gaps/overlaps. Multiplier 2 is allowed. Top-level validator requires each referenced modifier to exist. |
| Extrinsic 1 | `ExtrinsicStrategyConfig(type="constant_base_with_shaped_bonus", base_reward=1.0, bars=[], bar_bonuses=[], variable_bonuses=[], apply_modifiers=[])` | No VFS variable or contextual bonus; modifier does not accidentally scale extrinsic. Tests establish constant-base strategy and additive bonuses. |
| Shaping .1 | `EfficiencyBonusConfig(type="efficiency_bonus", weight=0.1, bar="energy", threshold=0.7)` as sole shaping entry | Test `TestShapingBonuses.test_efficiency_bonus` establishes >= threshold. Energy .8 satisfies it with margin. No position/action/time context needed. |
| Composition | `CompositionConfig(normalize=False, clip=None, log_components=True, log_modifiers=True)` | Makes requested arithmetic unambiguous; see clamp distinction below. |
| Real registry | `townlet.vfs.registry.VariableRegistry(variables=[], num_agents=2, device=device, items_per_world=0, item_profiles=None, num_affordances=0)` | Valid constructor path in inspected registry: no definitions to validate, empty global/agent arenas, no item storage. Bar-only configuration requires no VFS variable declarations, library registration, item profile, or schema helper. |
| Bar ordering | `{"energy": 0}` | Actual meter column mapping, independent of VFS variable storage. |
| Real backend | `townlet.environment.dac_engine.DACEngine(dac_config=cfg, vfs_registry=registry, device=device, num_agents=2, bar_index_map={"energy": 0})` | Constructor signature supplied by readiness report, also exercised directly in DAC tests; it compiles actual config modifiers/extrinsic/shaping. |
| Real wrapper | `townlet.vfs.vtc.VTCRewardProgram()` | Fieldless frozen dataclass per supplied report; no reward-rule compiler/factory registration required. VTC test independently instantiates this constructor. |

Assemble `DriveAsCodeConfig(version="1.0", modifiers={"double": modifier}, extrinsic=extrinsic, intrinsic=intrinsic, shaping=[shaping], composition=composition)` using the table's real models. These are concise construction expressions, not an implemented test or copied implementation. No new configuration runtime-scale field is warranted: the runtime factor must enter the explicit producer/composer contract once settled.

Minimum data geometry for one live and one terminal row, all on `torch.device("cpu")`:

| Argument | Shape / dtype | Example data |
| --- | --- | --- |
| step_counts | [2], torch.long | [1,1] |
| dones | [2], torch.bool | [False,True] |
| meters | [2,1], torch.float32 | [[.8],[.8]] |
| intrinsic_raw | [2], torch.float32 | [2,2] |
| reward_context | mapping | {} for these bar-only shaping controls |
| runtime_intrinsic_scale | Future explicit ABI; not currently declared | Desired value .5; scalar versus tensor and ownership must come from qualified runtime contract |

Current public invocation is `program.apply(reward_backend=engine, step_counts=step_counts, dones=dones, meters=meters, intrinsic_raw=intrinsic_raw, reward_context={})`. The report establishes its keyword-only signature and return `(total, intrinsic_weights, components)` with all tensor outputs shaped like dones. A single live row [1]/[1,1] is sufficient for arithmetic alone; two rows distinguish the mask while keeping the same meters/raw.

Do not place .5 into intrinsic_raw or base_weight to make current output look correct. Current DAC lacks runtime_intrinsic_scale; passing it through generic reward_context only forwards an ignored-for-intrinsic shaping kwarg. Current source-derived live result is intrinsic 1 and total 2.1. Desired explicit-runtime result is `2 * .5 * .25 * 2 = .5`, then `1 + .5 + .1 = 1.6`, before separate retirement. This capsule does not invent the future scale signature. Once supplied, change runtime scale independently of fresh real configs with base .25 versus .5; at runtime .5 the latter would give intrinsic 1/total 2.1. Runtime 0 with base .25 gives intrinsic 0/total 1.1; runtime 1 gives intrinsic 1/total 2.1. These are mathematical expectations, not test results.

## Terminal, clipping, and retirement are distinct

The readiness report establishes current done masking of extrinsic, effective intrinsic, and shaping. For the two-row example current total is [2.1,0]; future scale-.5 expected total is [1.6,0]. `intrinsic_weights` currently means only authored modifier product, hence [2,2], including terminal rows; it excludes base, runtime scale, and masking. `components["intrinsic_raw"]` currently means raw times drive base before modifier and terminal mask, hence [.5,.5]. It is not the provider's raw [2,2]. Tests `test_components_includes_intrinsic_raw`, `test_calculate_rewards_composition`, and `test_dead_agents_receive_zero_rewards` corroborate these distinctions. The future owner must specify any changed diagnostic semantics explicitly, without silently reinterpreting them.

Composition schema declares `normalize` (described as tanh) and `clip` (dictionary with min/max); that schema is not evidence those features execute. The supplied production report describes direct component summation and does not establish a total clamp/normalization implementation. The inspected DAC tests contain no total composition clip/normalize verification. Use normalize=False/clip=None here and retain an explicit missing fact for any claimed enabled clamp behavior. The approach-reward test separately documents a distance bonus clamped to zero outside max_distance; that is shaping-local behavior and is not a total-reward clamp. It is not used in the minimal setup.

No retirement behavior or bonus appears in these tests or config/registry construction, and the supplied report establishes no retirement in VTC/DAC/RWC. Do not interpret a dones row as proof of ENV retirement handling, equate retirement with raw diagnostic masking, or absorb a retirement bonus into the 1.6 composer expectation. Actual retirement timing, bonus, and post-retirement return/replay comparison remain ENV-owner evidence.

## Ownership and registration facts

The config models are not declared frozen; nested lists/dicts are mutable. Construct fresh validated configs and fresh backend instances for independent factor cases: mutating an existing model after DAC compilation does not prove what compiled closures captured. The supplied report establishes VTC's fieldless dataclass is frozen, but input tensors/context remain mutable references; VTC forwards input tensor objects and returns backend objects unchanged. DAC clones raw before drive weighting. No claim is made that tensors become immutable merely because a containing object is frozen.

`VariableRegistry.__init__(variables: list[VariableDef], num_agents: int, device: torch.device, items_per_world: int=0, item_profiles: dict[str, Any] | None=None, num_affordances: int=0)` is source-backed. Ordinary variables are declared at construction, not registered by a later public add-variable call. `get(variable_id: str, reader: str) -> torch.Tensor` returns a clone; `set(variable_id: str, value: torch.Tensor, writer: str) -> None` checks exact shape/dtype and permission, then copies into arena-backed storage or clones standalone storage. `set_engine_value(variable_id: str, value: torch.Tensor) -> None` retains shape/dtype/permission checks. `variables` exposes the actual definitions dict, not an immutable copy. Static access policy is snapshotted into a frozen dataclass of tuples; arena dataclass freezing does not freeze its tensor/index. Global/agent rows are independent worlds, num_worlds=num_agents.

Existing tests use `from townlet.vfs.schema import VariableDef` and declarations with id/scope/type/default/lifetime/readable_by/writable_by. The schema body and imported access validator were not inspected, so those older call sites do not certify a complete current VariableDef constructor (notably exposed_to). The empty real registry avoids this unresolved prerequisite altogether. If future ENV fixture needs declarations, obtain qualified current schema facts instead of copying old omissions or inventing compatibility.

No library registration API or genuine compiled-universe factory is present in the five inspected sources. The only pytest fixtures in DAC tests are `bar_index_map_single()` and `bar_index_map_dual()`, producing energy:0 and energy:0/health:1. There is no real ENV fixture to export from these files. No private helper is represented as a stable public factory.

## Genuine future ENV construction and evidence still required

The VTC test's local Backend returns fixed components; the RWC test's local Env, DACBackend, and VTCRewardProgram are doubles. They establish wrapper/delegation expectations only. Reusing those local classes would violate genuine ENV acceptance. Directly reuse the real model and registry constructors above for primitive composer proof, then obtain an independently qualified real compiled-universe/environment fixture for actual ENV step execution. Old tests omit the new context/scale because those APIs were absent; update callers with the new contract, never preserve their omission via fallback.

From the supplied readiness report, actual RWC currently stores returned weights in `env.intrinsic_weights`, stores the same components dict in `env._last_reward_components`, and returns the exact VTC/backend total. Those are the available canonical capture anchors. A later observer may capture these real outputs without replacing DAC or recomposing totals. Detached owned snapshots are necessary when retaining tensor evidence across later mutable steps; capture actual raw/runtime factor at the bound provider invocation separately from the historically base-weighted intrinsic_raw diagnostic.

Finite remaining prerequisites:

1. Qualified actual ENV/compiled-universe constructor import, signature, required fixture registration and config injection route. None of these five files supplies it; no sixth helper read or introspection was taken.
2. Settled runtime/provider result and transition-context ABI: full versus eligible row ordering, scale shape/device/ownership, context ownership, all five selected choices, and stats update policy. The config's allowed strategy labels alone are not runtime evidence.
3. Actual accepted-step placement proving distinct predecessor/successor, observation-provider successor reward phase, ICM true s,a,s', and predecessor RND predictor admission; eligible rows update stats once, including zero-scale cases.
4. Actual ENV terminal/retirement ordering, retirement bonus, final canonical return tuple and replay/sink API. Compare real component outputs and exact appropriate before/after-retirement totals; do not certify replay from the RWC local-double test.
5. Enabled total clamp/normalization semantics if claimed outside the explicit disabled configuration here; no production clamp evidence was supplied.

Ready: real minimum cfg, independently authored base/modifier/extrinsic/shaping controls, empty real registry, actual wrapper/backend call geometry, current diagnostic/mask meanings, and legacy-fixture limitations. Missing: future runtime-scale ABI and genuine ENV/compiled fixture/replay/retirement proof. Primitive component-boundary success cannot close original T18e end-to-end acceptance. All five families, zero-scale behavior, phase identity, stats-once, POP diagnostic isolation, canonical replay, red/green/review/commit, and global BAC gates remain owed.
