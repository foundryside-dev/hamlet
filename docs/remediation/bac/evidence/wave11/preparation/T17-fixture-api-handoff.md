# T17 fixture DATA and public API handoff — bounded supplier

2026-11-02 UTC; existing `/workspace/hamlet`; observed HEAD `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`. This supplies the finite missing-handoff table in `T17-interface-readiness.md` under the existing `T17-task-brief.md` and accepted P4. It is static source/DATA evidence and constructive arithmetic, not an implementation, a new design decision, a test result, or clearance to execute T17. T16 source/runtime barriers remain. Root is the sole integration owner.

## Source and attribution boundary

Exactly five authorized complete sources were read; physical line counts were independently measured with `wc -l`, bytes with `sha256sum`. Long source output was read in contiguous ranges where display truncation required it. No sixth ENV/NET/NF/helper/test source was opened.

| Alias | Complete source | Lines | SHA256 |
| --- | --- | ---: | --- |
| B02 | `/tmp/bac-B02/probe_networks.py` | 200 | `6934dca836cbb111de5399f2ef97600c949df0e339519affcfcddadc28c35bd9` |
| TS | `src/townlet/universe/dto/token_spec.py` | 2093 | `bec4f86e89819dfd030e787fe39632edf99d8f09b555237ffacc5be8f6ab3068` |
| TI | `src/townlet/agent/token_input.py` | 116 | `2aaab1b6d524ec5371e1e3503c936c1359d2a241826315afdd088cfbb6d44ba3` |
| EF | `src/townlet/environment/env_factory.py` | 81 | `ab9489d854fba3b644439b19a964190e78302a78132646132921c2ece7f0d232` |
| UC | `src/townlet/universe/compiler.py` | 976 | `521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92` |
| Total | Five complete sources | **3466** | — |

B02 is historical scratch source, **read but never executed**. It pins its original repository to `/tmp/hamlet-bac-4aa5363b` and its report's historical SHA is `4aa5363b5de54d9a112977c32c2975f37627197f`. Its import assertions, seed, deletions/copies, direct constructors, hard-coded action 5/action dimension 7, historical widths/offsets, state/gradient assertions and JSON output are not newly executed evidence. Its pack edits and semantic permutation recipe can be checked against the current authorized TS/TI/UC sources and supplied YAML DATA. None of its copy/deletion/probe operations was repeated.

The following existing wave09 receipts were consumed **as prose**, not by opening their linked sources. Their SHA256 values were measured for attribution:

| Prose receipt | SHA256 | Scope used here |
| --- | --- | --- |
| `T15-constructor-factory-bridge.md` | `ffe98bb8fa69aef0c1f338d4816375530e69499956999bb2351ace574e81b789` | The bridge's direct constructor forwarding; independently confirmed in this task's authorized EF. |
| `T15-constructor-fixture-suppliers.md` | `0ce1d3732ba2ff231495dbecbe8f2f73c04da18cf5f2bb850bb71fb5a2793f19` | ENV keyword-only construction/classmethod route and retained selected-level training carrier at its recorded source hash. |
| `T15-action-metadata-api.md` | `ddf95569a750c0e04110a9f28e143c426884763c0d22198529dcf565f688c9be` | `env.action_dim`, `env.level.runtime_action_space.actions`, record `.name/.id/.type/.delta`; display labels are not authored action names. |

Those ENV receipts name source SHA256 `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d`, 1714 lines, at their stated historical HEADs. This supplier has not independently inspected ENV. Root's separately bounded current ENV supplier completed `wave11-preparation/T17-env-public-api.md`, SHA256 **`41cb275e96e52f6e771889ba92138c4819c1bd02082903d6829b64267ec48e74`**. It was consumed whole as prose; it verifies the same 1714-line ENV hash at current observed HEAD `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`. Current ENV facts below are attributed to that supplier, not charged as a sixth source read by this worker.

## Complete authored pack reference and exact DATA edits

Use the existing canonical base pack `configs/test/token_set_smoke`, select **`L0_test` explicitly**, preserve its entire declared hierarchy, and replace only `variables.yaml` and `levels/L0_test/bars.yaml` with the full contents below. This is a reference plus two full replacement documents, not a partial two-variable pack. Do not replace the canonical pack in place; any later fixture materialization belongs inside the one allowed T17 test after root clears authoring/runtime. This supplier created no pack, checkout, source copy or helper.

All nineteen canonical YAML DATA files were read. Measured hashes show the original `/tmp/bac-B02/authored_identity_pair` matches the current canonical base byte-for-byte for the seventeen files other than those two replacements. This connects the historical witness DATA to today's canonical base without trusting a copied-pack name.

| Relative DATA path | Canonical SHA256; also B02's unless separately stated |
| --- | --- |
| `actions.yaml` | `7363114f30b2794659da1ec49aef65b5800c0addf5be659997c5e103d4180653` |
| `brain.yaml` | `9629e1b27c3bb8931cec870a53ae760760e2cdf90158cb5862ce1a3ad5928979` |
| `effects.yaml` | `2b9f559e318f638d2d96a8c5d5efd45a8bd9f22b739b6625053e0c2d8e737fa9` |
| `environment.yaml` | `7c9d3d95b02cbb4198c9f7450a4bd88bda3e759f0ebbaec5a3c9fa5bc9abcfaf` |
| `experiment.yaml` | `9ad9a5d0aa0b4dff49cccb154e0a3758beb8f32f77d6e432b58c4d7ac6600c1b` |
| `items.yaml` | `5121217232857b0e3551f484dcaa32a82d0e104e3e74a3316ac8183b9beb818e` |
| `stratum.yaml` | `d78508ca7d6b3a72966a766829e75e9deefff9300f21bfd4e801a7769dcb26d2` |
| `variables.yaml` | base `c28cfabdad385064388e3bbfbc4f24b2826629896194b1302985d384ca22b3eb`; B02 replacement `c275b6d1b8fe4ec669c0765eb8e70ae3ca4c1660f1705403701dfd3d86a945b9` |
| `levels/L0_test/affordances.yaml` | `70fb72d3ca1663682c35f6c447af53d9ea00020dc157a39e3a449ea4cb70f488` |
| `levels/L0_test/bars.yaml` | base `c050412a304078501fe2f1ff2da41cf5bdee632aa1ef500948c04b90a9d8814b`; B02 replacement `47305acc4ef79422363825ceca9bfa76d511d02f8b2064ebd03cf63f1eab643e` |
| `levels/L0_test/curriculum.yaml` | `3cc1e1583939f8d1fd4b6be265250ec174fea6ceb24712150892b7d64599b987` |
| `levels/L0_test/drive.yaml` | `b4ec89fb5e214e40e7f6c8c1f9d60301dc6bac92062ccad89fa20cf6b445f937` |
| `levels/L0_test/training.yaml` | `613e1e2cae003e379f8f19ee8bf1b19e62e737460877aebef539f41a32e7c073` |
| `levels/L1_attention/affordances.yaml` | `70fb72d3ca1663682c35f6c447af53d9ea00020dc157a39e3a449ea4cb70f488` |
| `levels/L1_attention/bars.yaml` | `c050412a304078501fe2f1ff2da41cf5bdee632aa1ef500948c04b90a9d8814b` |
| `levels/L1_attention/brain.yaml` | `60e014d4d9883c4acb098d9695863417527a09f2f79c98a9271e0b5798173c3e` |
| `levels/L1_attention/curriculum.yaml` | `3cc1e1583939f8d1fd4b6be265250ec174fea6ceb24712150892b7d64599b987` |
| `levels/L1_attention/drive.yaml` | `b4ec89fb5e214e40e7f6c8c1f9d60301dc6bac92062ccad89fa20cf6b445f937` |
| `levels/L1_attention/training.yaml` | `613e1e2cae003e379f8f19ee8bf1b19e62e737460877aebef539f41a32e7c073` |

Full `variables.yaml` replacement, with the original declarations retained (formatting is compacted here; the preceding hash identifies original B02 bytes):

```yaml
variables:
  version: '1.0'
  item_profiles: []
  declarations:
  - id: deficit_energy
    readable_by: [engine, agent]
    writable_by: [engine]
    scope: agent
    type: scalar
    lifetime: tick
    semantic_type: custom
    exposed_to: [agent]
    initial_value: 0.0
    normalization: {kind: minmax, min: 0.0, max: 1.0, clip: true}
    description: How far below target energy (0.0 = at/above target)
  - id: time_since_last_eat
    readable_by: [engine, agent]
    writable_by: [engine]
    scope: agent
    type: scalar
    lifetime: tick
    semantic_type: custom
    exposed_to: [agent]
    initial_value: 0.0
    normalization: {kind: minmax, min: 0.0, max: 100.0, clip: true}
    description: Timesteps since last EAT action
  - id: need_tokens
    readable_by: [engine, agent]
    writable_by: [engine]
    scope: agent
    type: tensor2d
    lifetime: episode
    semantic_type: custom
    exposed_to: [agent]
    initial_value_mode: zeros
    shape: [4, 3]
    normalization: {kind: minmax, min: 0.0, max: 1.0, clip: true}
    description: 'Flattened variable-element token rows: 4 tokens x 3 features.'
  - id: position
    readable_by: [engine, agent]
    writable_by: [engine]
    scope: agent
    type: vecNf
    lifetime: tick
    semantic_type: custom
    exposed_to: []
    initial_value: [0.0, 0.0]
    description: Normalized agent position (2D) in [0, 1]^2 range
    dims: 2
  - id: pulse_left
    scope: global
    type: scalar
    lifetime: episode
    semantic_type: custom
    readable_by: [engine, agent]
    writable_by: [engine]
    exposed_to: [agent]
    initial_value: 0.125
    expression: 'where(tick % 2 == 0, 0.25, 0.75)'
    normalization: {kind: minmax, min: 0.0, max: 1.0, clip: true}
  - id: pulse_right
    scope: global
    type: scalar
    lifetime: episode
    semantic_type: custom
    readable_by: [engine, agent]
    writable_by: [engine]
    exposed_to: [agent]
    initial_value: 0.875
    expression: 'where(tick % 2 == 0, 0.75, 0.25)'
    normalization: {kind: minmax, min: 0.0, max: 1.0, clip: true}
```

Full `levels/L0_test/bars.yaml` replacement:

```yaml
bars:
  version: '1.0'
  meters:
  - name: energy
    initial: 1.0
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 1.0, lethal_min: true, lethal_max: false}
  - name: health
    initial: 1.0
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 1.0, lethal_min: true, lethal_max: false}
  - name: satiation
    initial: 1.0
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 1.0, lethal_min: false, lethal_max: false}
  - name: hygiene
    initial: 1.0
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 1.0, lethal_min: false, lethal_max: false}
  - name: money
    initial: 0.0
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 999999.0, lethal_min: false, lethal_max: false}
  - name: fitness
    initial: 0.5
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 1.0, lethal_min: false, lethal_max: false}
  - name: mood
    initial: 1.0
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 1.0, lethal_min: false, lethal_max: false}
  - name: social
    initial: 1.0
    depletion: {passive: 0.0, move: 0.0, interact: 0.0}
    recovery: {natural: 0.0}
    bounds: {min: 0.0, max: 1.0, lethal_min: false, lethal_max: false}
  cascades:
  - {source: satiation, target: health, threshold: 0.3, strength: 0.004}
  - {source: satiation, target: energy, threshold: 0.3, strength: 0.006}
  - {source: mood, target: energy, threshold: 0.2, strength: 0.001}
  - {source: hygiene, target: mood, threshold: 0.4, strength: 0.003}
  - {source: hygiene, target: social, threshold: 0.4, strength: 0.0}
```

This freezes passive, move and interact depletion **and** natural recovery for every L0 meter, including health's otherwise nonzero recovery. Cascades are retained exactly as in B02: their starting satiation/mood/hygiene values are all 1, above the declared thresholds. B02's historical check found only the pulse value columns changed after WAIT; the future current-source test must assert that stability rather than infer an uninspected executor's WAIT behavior from its name. L0 retains `active_vision: global`, `active_temporal: false`, `day_length: null`; stratum retains `temporal_support: enabled`. `tick` expressions do not justify turning on unrelated temporal dynamics. Training's full required carrier, population size 8, explicit enabled-affordance list, lifespan 1000, randomization setting and other modes remain present. Two constructor batch worlds use `num_agents=2`; this is not a shared-world count or an instruction to change training population.

B02's only modified level is L0. L1's unfrozen bars remain part of the canonical hierarchy and are not the selected environment for this witness. Attention control can use the same L0 observation/spec with its aggregator selected independently; selecting L1 instead would require freezing its relevant meter rates too and would be a distinct fixture edit. No such unneeded edit was made here.

For authored new-mode selection, preserve the full base brain document and add this exact mapping at `architecture.token_set.token_encoder`:

```yaml
token_encoder:
  mode: interaction_mlp
  hidden_width: 1
```

Its base dimensions are `token_embed_dim: 16`, `q_head_hidden_dim: 64`, aggregator `{type: mean}`. A positive width 1 is sufficient for the construction below. Explicit linear uses `{mode: linear}` and no width; the omitted field resolves to linear under the accepted resolver. The existing readiness receipt, consumed as source-verified prose, already proves `TokenSetConfig.token_encoder` and `RecurrentConfig.token_encoder`, `TokenEncoderOptions`, and `resolve_token_encoder`; this supplier did not reopen BC/OP/NF/NET. These are portable authored fields, **not claims about already-existing network constructor keyword names**. T17's implementation owner must add and report exact resolved mode/width parameters to both factories/wrappers under P4. No constructor-local default or guessed new current API is supplied here.

## Current immutable TokenSpec and coordinate API

Import from **`townlet.universe.dto.token_spec`**. TS defines all these as frozen dataclasses; constructor fields are public, with no omitted required context tables:

```text
SlotBinding(slot_index: int, filler_kind: Literal['static','dynamic'],
            filler_ref: str, scope: VariableScope | None)
TokenContext(context_ref: str, fixed_payload: tuple[float, ...])
TokenTypeSchema(type_name: str, payload_features: tuple[str, ...], capacity: int,
                slot_bindings: tuple[SlotBinding, ...],
                slot_context_payloads: tuple[tuple[float, ...], ...],
                effect_catalog_contexts: tuple[TokenContext, ...])
build_token_type(type_name: str, slot_bindings: Sequence[SlotBinding], *,
                 slot_context_payloads: Sequence[Sequence[float]],
                 effect_catalog_contexts: Sequence[TokenContext]) -> TokenTypeSchema
TokenSpec(types: tuple[TokenTypeSchema, ...], position_rank: int,
          transport_version: str, encoding_version: str = ENCODING_VERSION)
```

Current constants are `TOKEN_TRANSPORT_VERSION='compact-1'`, `ENCODING_VERSION='token-1.1'`, `VALUE_BLOCK_WIDTH=2`; roster order is `self,meter,affordance,agent,item,effect,variable_element`. TokenSpec may contain a roster-ordered subset. It rejects duplicate/out-of-order types, wrong transport/encoding versions and invalid rank. TokenTypeSchema requires the exact `PAYLOAD_SCHEMAS[type_name]`, dense binding indices, capacity/binding/context agreement, static variable bindings with non-null scope, and finite float32-representable fixed payloads within [-1,1]. `SlotBinding` accepts a scope value such as `'global'` and canonicalizes it to `VariableScope`; the type annotation is not a requirement to open/import that enum's source.

Non-effect context is **positional payload tuples**, one full payload per slot, excluding presence. Its `effect_catalog_contexts` must be `()`. Effects instead require `slot_context_payloads=()` and named `TokenContext` catalog rows. A `TokenContext` alone is not a variable positional-context wrapper. The public construction/replacement boundary is these dataclasses (`dataclasses.replace` reruns validation), not mutation of an assembler's private buffers.

`spec.get_type(name)` returns a schema or None. `schema.payload_width=len(schema.payload_features)`; `fixed_row_width=1+payload_width`; `schema.census=len(slot_bindings)`. `spec.total_dims` is compact observation width; `spec.fixed_total_dims` is a different, derived network-boundary width. `spec.census` gives per-type counts. `spec.row_layout()` returns `(type_name,slot_index,start,end)` tuples in **compact** transport order; `spec.fixed_row_layout()` provides corresponding fixed-row offsets and must not index environment tensors.

`spec.compact_layout()` returns `CompactTokenLayout(types, dynamic_total_dims)`. Its `.get_type(name)` returns `CompactTokenTypeLayout` or None, with exact fields:

```text
type_name, start, end, capacity, compact_row_width, fixed_row_width,
dynamic_features: tuple[str, ...],
fixed_scatter_indices: tuple[int | None, ...]
```

For variables, `dynamic_features=('presence','value_0','value_1')`, `compact_row_width=3`, scatter lanes `(0, 1+payload.index('value_0'), 1+payload.index('value_1'))`. For slot `s`, compact start is `layout.start + s*layout.compact_row_width`; the live scalar is at start + `layout.dynamic_features.index('value_0')` (currently +1). Derive the pulse slots from `schema.slot_bindings` by exact `filler_ref`, then bind by the stored `slot_index`; do not assume historical slot numbers or flatten-column 142/145. Assert both bindings/presences and derive tensor width from `spec.total_dims`.

The complete variable payload is `position_features('position', with_rank=True) + ('value_0','value_1','value_width_used') + DESCRIPTOR_BLOCK_FEATURES`. Let `M=MAX_POSITION_RANK`, `P=schema.payload_width`; these exact indices require no uninspected enum widths:

| Field | Payload/Linear-input index (presence removed) | Assembled fixed-row index | Compact variable-row index |
| --- | --- | --- | --- |
| presence | excluded | 0 | 0 |
| `position_0 ... position_(M-1)` | `0 ... M-1` | `1 ... M` | none |
| `position_rank` | M | M+1 | none |
| `value_0` | M+1, also `payload_features.index('value_0')` | M+2 | 1 |
| `value_1` | M+2 | M+3 | 2 |
| `value_width_used` | M+3 | M+4 | none |
| descriptor start | M+4 | M+5 | none |
| `declared_initial` | **P-4**, also `.index('declared_initial')` | P-3 | none |
| `log_element_count` | P-3 | P-2 | none |
| `owner_slot` | P-2 | P-1 | none |
| `owner_slot_applicable` | P-1 | P | none |

These are exact coordinate formulas rather than inferred numeric values for external enum lengths. The public feature tuples expose every remaining descriptor coordinate: `scope_<scope>`, `semantic_<semantic_type>`, `norm_kind_<kind>`, `norm_param_min/max/clip/scale`, `norm_param_absent`, `dtype_float/int/bool`, `lifetime_<lifetime>`, followed by the four tail fields. Select by the feature name; do not hard-code an unverified payload width.

TS's `normalize_declared_scalar(value, normalization, *, element_index, element_count)` applies clipped minmax `(value-min)/(max-min)` to the declared default. Thus pulse descriptors have **d_left=.125, d_right=.875 exactly**, not 0/1 and not saturated d/(1+d). Their shared normalization parameter descriptor is `(0,.5,1,0,1)` for `(min,max,clip,scale,absent)`: parameter bounds are saturated, while the declared-initial feature is normalized. Both have scalar position/rank coordinates 0; `value_width_used=.5`; one-hot `scope_global`, `semantic_custom`, `norm_kind_minmax`, `dtype_float`, `lifetime_episode`; `log_element_count=float32(log(2)/(1+log(2)))`; owner fields0. Their live compact lane1 is .25/.75 or its complement, lane2 is0. Other exposed base declarations have declared-initial0; `need_tokens` contributes 12 variable rows, not four tokens inferred from its old description. `position` is unexposed. The authored pair therefore gives 16 variable rows under the TS declaration rules, with pulses after the two base scalars and twelve elements; runtime lookup remains by filler reference.

## Target-owned assembly and semantic permutation

Current TI source verifies `TokenInputAssembler(token_spec)` and `expand_type(type_name: str, dynamic_rows: Tensor) -> Tensor`, requiring floating `[batch,capacity,compact_row_width]` and returning `[batch,capacity,fixed_row_width]`. It registers the supplied spec's contexts as `_token_context_<type_index>`, scatter indices as `_dynamic_lanes_<type_index>`/`_fixed_lanes_<type_index>`, **all `persistent=False`**. For variables it copies positional context, scatters compact presence/value lanes into fixed rows and returns exact-zero rows when compact presence is zero. The assembler predicate is `!=0`; NET's presence predicate is `>0.5` according to the existing readiness receipt, so fixtures use canonical binary 0/1 presence.

The module registers its own target context at construction and no trainable parameter in TI. Ordinary learned `state_dict()` loading cannot replace these nonpersistent context/scatter buffers. This directly verifies the ownership boundary TI controls today; it does not claim an excluded checkpoint loader's refusal or transfer policy. Device/dtype conversion in assembly uses current input device/dtype without publishing static context to replay.

Exact immutable semantic permutation, checked against current TS and TI, is the historical B02 recipe expressed with derived widths:

```text
schema = spec.get_type('variable_element')
layout = spec.compact_layout().get_type('variable_element')
order = tuple(reversed(range(schema.capacity)))   # new slot -> old slot
target_schema = replace(
    schema,
    slot_bindings=tuple(replace(schema.slot_bindings[old], slot_index=new)
                        for new, old in enumerate(order)),
    slot_context_payloads=tuple(schema.slot_context_payloads[old] for old in order),
)
target_spec = replace(spec, types=tuple(
    target_schema if t.type_name == 'variable_element' else t for t in spec.types
))
rows = observation[:, layout.start:layout.end].reshape(
    observation.shape[0], schema.capacity, layout.compact_row_width
)
target_observation = observation.clone()
target_observation[:, layout.start:layout.end] = rows[:, order, :].reshape(
    observation.shape[0], layout.end-layout.start
)
```

Here `replace` is `dataclasses.replace`. The input spec and input tensor remain untouched. Bindings retain each old row's filler reference/scope/kind while receiving a new dense slot index; its whole positional context and entire compact row travel together. Same type names, widths, capacities and learned parameter shapes remain compatible. Construct a **new target network using `target_spec`**, then load the source network's learned state using the normal same-mode module API supplied in the readiness receipt/B02 usage. Do not assign private assembler buffers or load a source context into the target. For the future test, compare source and target pooled/Q results at tolerance1e-6 and verify no `_token_context_`, `_dynamic_lanes_` or `_fixed_lanes_` state keys. Nonzero context tables remain different in the two targets. Permuting only compact rows against fixed context is precisely a value reassignment witness and has the opposite intended result.

This constructs the immutable **compiled TokenSpec** consumed by the target network. It does not pretend that `CompiledUniverse`/its level DTO has an inspected public mutation or replacement API. No environment state or level metadata is injected.

## Deterministic witness tensors, including the full authored Q distinction

These are complete tensor DATA specifications for the accepted P4 Sequential (`Linear` indices0 and2), to be applied only after the implementation owner supplies the real new-mode constructor/factory parameters. They are not code added to the repository and were not executed. `E=16`, MLP hidden width1, Q-head width `H=64` match the supplied authored dimensions. A tensor described as zero is zero in **every** element; no seed/random coefficient is left as evidence.

### Two-row accepted .375/.125 witness

Use a pure network fixture with one `variable_element` schema, capacity2, static bindings `(0,'static','witness_low','global')` and `(1,'static','witness_high','global')`, no effect contexts, and `TokenSpec(types=(schema,),position_rank=0,transport_version=TOKEN_TRANSPORT_VERSION)`. Use `PAYLOAD_SCHEMAS['variable_element']`, not an invented short payload. Each complete fixed payload is all zero except `value_width_used=.5`, `scope_global=1`, `semantic_custom=1`, `norm_kind_minmax=1`, `norm_param_max=.5`, `norm_param_clip=1`, `norm_param_absent=1`, `dtype_float=1`, `lifetime_episode=1`, `log_element_count=float32(log(2)/(1+log(2)))`, and `declared_initial=c` with c0/c1 respectively. This describes valid scalar declared-default0/1 contexts using the public frozen constructors; payload lane `value_0` remains0 in context because compact transport supplies it. All listed coordinates are selected by feature name.

Take binary-present compact observations `[1,.25,0, 1,.75,0]` and `[1,.75,0, 1,.25,0]`. Set all type vectors and all encoder parameters0. Then set only first Linear `W[0,i_value_0]=1`, `W[0,i_declared_initial]=1`, `b[0]=-1`; second Linear `W[0,0]=1`. Its other E-1 output rows and all second biases remain0. The row feature is exactly `f(c,v)=ReLU(v+c-1)`. Row0 contributes0; row1 contributes .75/.25. Mean over two present rows produces exactly `(.375,0,...,0)` versus `(.125,0,...,0)` in exact arithmetic; these dyadic values also avoid reduction-roundoff ambiguity in the toy fixture. A joint row+context permutation preserves either result.

This isolated tensor fixture is the accepted mathematical witness. The full authored environment below is separate and uses ordinary reset/WAIT observations without state injection.

### Full authored pack, including extra present rows

Set every type vector0, every unrelated type's first/second Linear weights and biases0, and every variable MLP coefficient0 except:

| Tensor | Exact nonzero entries |
| --- | --- |
| `encoder.encoders.variable_element.0.weight` | `[0,i_value_0]=3`, `[0,i_declared_initial]=4` |
| `.0.bias` | `[0]=-3.5` |
| `.2.weight` | `[0,0]=float32(1/3)` |
| `.2.bias` | none |

Indices here are **payload/Linear-input** indices, excluding presence. Every live unrelated payload coordinate coefficient is zero. Other variable rows have d0 and bounded v≤1, so `3v+4d-3.5≤-.5` and contribute0. The pulse with d.125 has `3v-3≤-.75`, also0. The pulse with d.875 has preactivation3v, then outputv. This is the same feature as

`ReLU(v+c-1)`, where **`c=(d-.125)/.75=(4d-.5)/3`**,

implemented as `ReLU(3v+4d-3.5)/3` so first-layer coefficients/bias and cancellation are binary-exact. For the authored .25/.75 values, first activation .75/2.25 and multiplication by float32(1/3) round to .25/.75. No other descriptor, type bias or absent padding supplies the distinction.

For each actual environment observation compute

`N = sum_over_types sum_over_slots (compact_presence > .5)`

using each derived compact layout. Require both pulse presences1, the same positive N in the two compared frames, equal presence masks and unchanged non-pulse compact fields. Read actual pulse lane values and identify the `.75` versus `.25` pulse_right frames by those values rather than relying on expression-evaluation timing. In exact arithmetic, pooled output is `p_high=(.75/N,0,...,0)` versus `p_low=(.25/N,0,...,0)`. Additional present self/meter/affordance/base-variable rows have **zero numerator but still count in N**. Never compare this full-set result to .375/.125 unless the actual N is2.

The supplied declaration rules predict self1, meter8, affordance14, agent/item/effect0 and variable16, compact width `5+24+70+48=147` at rank2. If all those declared live rows are present under the supplied full-vision L0 settings, N39 and pooled values are `.75/39` and `.25/39`. These are conditional checks derivable from the returned schema/presence, not permission to hard-code B02's dimension147, N39 or columns142/145. Present-row counts and publisher stability are runtime assertions left for the cleared test.

For the token-set Q-head `Linear -> LayerNorm -> ReLU -> Linear` described in the existing NET readiness receipt, specify **all** Q-head tensors deterministically:

| Tensor | Complete DATA specification |
| --- | --- |
| `q_head.0.weight` `[64,16]` | all0, except `[0,0]=N` (the common observed integer count) |
| `q_head.0.bias` `[64]` | all0, except `[1]=1` |
| `q_head.1.weight` `[64]` | all1 |
| `q_head.1.bias` `[64]` | all0 |
| `q_head.3.weight` `[action_dim,64]` | all0, except `[a,0]=1` |
| `q_head.3.bias` `[action_dim]` | all0 |

Choose `a` as the current compiled WAIT record's `.id`, after checking `0≤a<env.action_dim`. No fixed a5/action_dim7 is required. Multiplication by N turns pooled coordinate0 into `s=.75` or `.25` up to normal floating-point rounding, while hidden coordinate1 remains the fixed reference1. Let epsilon be the **actual `q_head[1].eps`**, rather than guessing a currently unquoted LayerNorm default. The exact selected output is

`Q_a(s) = ReLU((s-(s+1)/64) / sqrt((s*s+1)/64 - ((s+1)/64)^2 + epsilon))`.

For s∈{.25,.75}, the numerator is positive; the function strictly increases for any finite epsilon≥0. Equivalently its pre-ReLU normalized coordinate is `((63s-1)/sqrt(63s*s-2s+63+4096epsilon))`, whose derivative numerator is `63^2-1+63*4096epsilon>0`. Thus **Q_a(.75)>Q_a(.25)**, with every other Q action exactly0 under the specified tensors. If epsilon were1e-5 the corresponding values would be approximately4.70 and1.81, but the formula using the actual module epsilon is the test oracle; this supplier did not inspect/runtime-evaluate the external LayerNorm implementation. The fixed reference coordinate is essential: a hidden vector proportional only to s could become indistinguishable through scale normalization. This construction does not rely on random weights or a seed delta.

The same row-encoder pooled witness applies to the recurrent wrapper's shared encoder before memory. Its zero-start/full-sequence-versus-threaded-frame comparison remains the existing acceptance obligation. The above **selected Q tensors specify the token-set head input**, not an invented identity LSTM; unconfigured recurrent Q cannot inherit this exact analytic formula because memory transforms p. The current readiness receipt supplies its public `initial_hidden`/forward API. T17 can assert the constructive pooled distinction in both factory families, the selected full-pack Q distinction with the deterministic token-set tensors, and separately preserve threaded recurrent equivalence. No random recurrent Q difference is asserted as an expressivity proof.

### Preserved linear control, masking and scope

For a linear same-type encoder, swapping pulse .25/.75 values leaves the sums of every descriptor coordinate and live-value coordinate unchanged, provided presence/other rows are unchanged. Any fixed affine row parameters, common learned type vector and head therefore preserve the exact-arithmetic mean alias. For a deterministic control, zero all vectors/parameters and set just variable `W[0,i_value_0]=1`, `W[0,i_declared_initial]=1`; use the same deterministic head if a nontrivial output is useful. The pulse numerator is `.25+.75+.125+.875=2` in both frames. Explicit/omitted-resolved linear must retain the old direct `.weight/.bias` state shape and computation, not acquire Sequential keys. Full-pack floating reduction differences are checked at appropriate tolerance and cannot be represented binding.

TI verifies absent compact rows become exact-zero assembled rows even with poisoned absent dynamic lanes. P4/readiness requires masking **after** either row encoder and type embedding. Under binary absence, test finite exact-zero empty pooled values and zero gradients for all relevant first/second MLP Linear parameters and absent-only type vectors. A Q-head bias may remain nonzero: empty pooled0 does not imply Q0. Attention stays selectable; the explicit numbers above establish mean expressivity only and do not silently replace attention with a different architecture. Existing attention/sequence/state controls remain in the single named T17 test scope. No present runtime result is claimed.

## Compiler/environment/WAIT handoff and exact remaining facts

Directly source-verified current compiler import and signatures:

```text
from townlet.universe.compiler import UniverseCompiler
UniverseCompiler()  # __init__(self) -> None
UniverseCompiler.compile(self, experiment_dir: Path,
                         primary_level: str | None = None,
                         use_cache: bool = True) -> CompiledUniverse
```

Use `compiler.compile(pack_path, primary_level='L0_test', use_cache=False)` explicitly. Although its signature permits None, compile immediately rejects omitted/None primary level. It resolves the path, discovers/parses the full pack, compiles every declared level, and constructs `CompiledUniverse(all_levels=...)`. `_compile_level` passes `token_spec`, `training`, `runtime_action_space`, `action_metadata`, hashes and other carriers into `CompiledUniverse.LevelMetadata`. Thus `universe.all_levels['L0_test'].token_spec` is the source-observed compiled-product route (also used in historical B02), not a synthetic token schema substituted into an environment. Cache False skips both the cache-read branch and the cache-write branch. No compiler was instantiated or run for this receipt; excluded parser/DTO/observation compiler implementations were not opened.

The current authorized EF bridge is:

```text
from townlet.environment.env_factory import from_universe
from_universe(env_cls: type[VectorizedHamletEnv], universe: CompiledUniverse, *,
              level_name: str, num_agents: int,
              device: torch.device | str) -> VectorizedHamletEnv
```

It requires an explicit non-None level, converts a string device to `torch.device`, and returns `env_cls(universe=universe,level_name=level_name,num_agents=num_agents,device=torch_device)` with no wrapper or state injection. The T15 ENV prose supplied the constructor/classmethod route. The current ENV supplier now confirms its complete public signatures below. This preserves the full selected level's training carrier and required explicit controls.

The T15 action API prose supplies `env.action_dim` and `env.level.runtime_action_space.actions`; the current ENV receipt reconfirms them. Select exactly one action record with `.name=='WAIT'` and take its actual `.id`; DATA declares WAIT enabled by default and training additionally enables REST. Never use a display label lookup or assume `.action_ids['WAIT']`/fixed ID. Current UC directly constructs/passes the runtime-action carrier but the downstream mask/executor implementation is outside these five sources.

The complete **current ENV API**, from the separately source-verified prose receipt, is:

```text
from townlet.environment.vectorized_env import VectorizedHamletEnv
VectorizedHamletEnv.__init__(
    self, *, universe: CompiledUniverse, level_name: str,
    num_agents: int, device: torch.device | str)
@classmethod
VectorizedHamletEnv.from_universe(
    cls, universe: CompiledUniverse, *, level_name: str,
    num_agents: int, device: torch.device | str) -> VectorizedHamletEnv
VectorizedHamletEnv.reset(self) -> torch.Tensor
VectorizedHamletEnv.get_action_masks(self) -> torch.Tensor
VectorizedHamletEnv.step(
    self, actions: torch.Tensor, depletion_multiplier: float = 1.0
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]
```

The ordinary call is `VectorizedHamletEnv.from_universe(universe,level_name='L0_test',num_agents=2,device='cpu')`; neither construction route implicitly resets. `num_agents=2` denotes two independent single-agent worlds. Current public extraction is **`env.token_spec`** (the selected level's spec), **`env.observation_dim=env.token_spec.total_dims`**, **`env.action_dim`**, and **`env.device`**. Prefer `env.token_spec` for both network-family factories; do not use a primary-level alias when the actual selected environment differs. This complements current UC's direct `universe.all_levels['L0_test'].token_spec` construction route.

`obs0=env.reset()` returns a **bare Tensor**, documented `[env.num_agents,env.observation_dim]`, with no info tuple/container. Reset sets global tick0, publishes it, and evaluates compiled VFS profiles **before returning**. A subsequent ordinary `step(actions)` increments/publishes tick1 and evaluates profiles before returning its observation. Thus reset plus **one** normal WAIT step is the supplied k0/k1 pair; a second WAIT step is unnecessary to create the complementary assignment. The external evaluator's exact `where` arithmetic remains a boundary, while current ENV proves the evaluation schedule; DATA and the future value assertions supply the rest. Literal `.125/.875` initial values are descriptor facts and are not expected as live values in the already-evaluated reset observation.

`masks=env.get_action_masks()` returns documented bool `[env.num_agents,env.action_dim]`, **True means valid**. Require `masks[:,wait_id]` true in both lanes before calling the chosen step. Construct `actions=torch.full((env.num_agents,),wait_id,dtype=torch.long,device=env.device)`. ENV passes this Tensor unchanged to its imported executor; it does not itself validate input rank/dtype/device or prove WAIT's no-op/write behavior. The caller's explicit shape/dtype/device, actual public mask check, authored WAIT declaration and next-observation stability assertions avoid inventing those helper contracts.

The exact step extraction is `obs1,rewards,dones,info=env.step(actions)`: observation Tensor `[2,env.observation_dim]`; reward Tensor documented `[2]`; combined done bool Tensor `[2]`; dict info. Step returns `self.dones` without clone and performs **no automatic episode reset**. Require both dones false for this finite comparison. ENV constructs/clones `info['successor_action_masks']` after successor observation/status/hour commit; it is the documented bool mask for the returned frame. Its other exact info keys are `active_on_entry`, `newly_terminal`, `newly_retired`, `step_counts`, `positions`, `successful_interactions`, `reward_components`, `intrinsic_weight`, and `effect_spawn_refusals`. The first five of those are clones; interactions/reward components/intrinsic weight are direct helper/member objects; effect spawn refusals is a tuple. No Gymnasium five-tuple or terminated/truncated split is present.

The ENV reader explicitly cannot prove the imported observation encoder's allocation ownership or actual output dtype/device, although its annotation/documented shape and direct return are inspected. Retain **`obs0=env.reset().clone()`**, then **`obs1=obs1.clone()`** after step (and clone dones if retaining it across further environment calls), so fixture comparisons do not depend on uninspected storage reuse. Assert actual floating observation dtype, expected CPU device and width before network input; TI independently enforces a floating compact input. No extra helper inspection is needed to make owned snapshots.

Current ENV source has **no `close`, `__enter__`, `__exit__`, `__del__`, or public disposal function**. There is no verified project cleanup call or context-manager protocol to invoke; let ordinary fixture-local Python lifetime own the object. This does not claim imported helpers have no resources or promise immediate torch allocator release. Full selected training is retained; visible constructor dependencies include explicit non-null enabled-affordances, valid compiled labels/experiment name/meter bounds, and day_length if temporal mechanics are active. The canonical pack retains these required carriers, with actual lifespan1000; future nonterminal assertion handles any authored terminal behavior.

These ENV facts close the missing public reset/step/mask/token-spec/action-count/cleanup handoff at the separately inspected source hash. Remaining helper limits are explicit: actual observation allocation/dtype/device, evaluator arithmetic, full action-ID validation and executor behavior were not inspected by either bounded supplier. They are resolved by the local observation/value/mask/stability assertions when runtime is cleared, not by assuming hidden APIs or injecting state.

Other missing facts are confined to the original table: T17 owner must provide exact added constructor/factory mode/width keyword spellings when implemented; excluded checkpoint/transfer/refusal and execution-identity consumer APIs require source-verified prose only **if the bounded test exercises those consumers**. This handoff establishes ordinary nonpersistent assembler context, not those broader consumer policies. Existing accepted P4 fixes the representation and state distinction; no new design/review loop is requested.

## Custody and disposition

Only this ignored receipt was authored. `.git/info/exclude:7` reports `/.superpowers/` for the destination. DATA was read from the original B02 directory and canonical base; no DATA files were changed or generated. No project imports, execution/probes, pytest/collection/compiler/linter, source/test/tracked-document/index/tracker edits, commit/push, branch/worktree/project checkout/copy/deletion, `.oracle` action or subdelegation was performed. The existing fourteen checkouts were left in place. Postwrite readback, five fresh unchanged source hashes/counts, destination ignore check and ENV-prose hash confirm custody only, not test qualification. T17 remains unimplemented/unqualified until root clears the existing dependency and runtime gates. This supplier returns stationary after the finite handoff.

## Scalar binding-name clarification — tests-only handoff, 2026-11-02

For the supplied exposed **registry/global scalar** declarations, the binding rule yields exact `SlotBinding.filler_ref` strings **`'pulse_left'`** and **`'pulse_right'`**: bare authored IDs, with no `global.` qualifier and no `[0]` suffix. Current TS:1622,1648–1658 carries each registry `var_def.id` unchanged into `ExposedVariable.id` (the registry path supplies no item profile or owner slot). TS:1737–1744 selects `filler_ref=exposed.id` for a one-element variable without an owner; indexing is the separate multi-element/owner branch. Scope is stored in `SlotBinding.scope`, not prepended to its reference. Item-profile qualification at TS:1678–1687 belongs to a different path. B02:41–49 authors these exact global scalar IDs and B02:60–62 explicitly looks up `row_by_ref['pulse_left']` and `row_by_ref['pulse_right']`, consistent with that current rule.

Exact semantic lookup uses the **variable-element type plus filler reference**, then the binding's actual stored slot index; no declaration-order offset or qualified-name fallback is needed:

```text
schema = spec.get_type('variable_element')
assert schema is not None
compact_rows = {(type_name, slot): (start, end)
                for type_name, slot, start, end in spec.row_layout()}
for name in ('pulse_left', 'pulse_right'):
    matches = [b for b in schema.slot_bindings if b.filler_ref == name]
    assert len(matches) == 1
    binding = matches[0]
    start, end = compact_rows[('variable_element', binding.slot_index)]
```

This statically verifies the scalar registry **binding rule** and the exact historical fixture lookup. No fresh compiled artifact was produced: the excluded `build_runtime_variables`/`variable_element_shape` implementations were not inspected, so independently re-proving their lowering of the authored YAML into the scalar registry inputs is outside these five sources. The cleared test should require the two exact literal matches above and report the actual roster if compilation supplies different inputs; do not invent a qualifier, suffix or compatibility fallback. All five source hashes remain those recorded above. This append changes only this ignored handoff; its original 416-line prefix is preserved. No runtime or production edit accompanies this clarification.
