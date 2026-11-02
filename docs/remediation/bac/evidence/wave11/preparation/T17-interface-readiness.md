# T17 interface readiness — read only; implementation remains blocked

Inspection: 2026-11-02 UTC in existing `/workspace/hamlet`. Authority is the existing `T17-task-brief.md`; this receipt does not amend P4, the original plan, or programme governance. T16 is not qualified in the supplied authority, so neither T17 source/test authoring nor runtime work is cleared. The only authored artifact is this ignored receipt. No project imports, collection, pytest, compiler, linter, probes, additional source inspection, source/test/tracked-document edits, index/commit/push, branch/worktree/checkout/copy/deletion, `.oracle` work, or subdelegation occurred. All 14 existing checkouts were left in place.

## Bounded source census

All four present named sources were read whole. The fifth named source does not exist (`stat` returned ENOENT); no replacement test/helper/probe was opened. Counts are physical newline counts from `wc -l`; SHA256 values came from `sha256sum` independently of the reads.

| Alias | Exact source | Access for eventual T17 | Actual lines | Projected lines | SHA256 |
| --- | --- | --- | ---: | ---: | --- |
| NET | `src/townlet/agent/networks.py` | modify | 474 | 750 | `bff39c4b46820c3bc812bfa7ebdf5f8832cf4b1f94bb6038eb1c5d56dd9ae9e1` |
| NF | `src/townlet/agent/network_factory.py` | modify | 171 | 250 | `976ff4f761c65981ce0f35812379abbdef940e81bed21e8f2715c2df02efb6fd` |
| BC | `src/townlet/config/brain_config.py` | read only | 568 | 750 | `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079` |
| OP | `src/townlet/config/bac_options.py` | read only | 294 | 600 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| test | `tests/test_townlet/regressions/bac/test_token_binding.py` | create test after clearance | absent | 350 | absent |
| Total | Five complete named sources; four currently present | bounded | 1507 | 2700 | — |

Current 1507 plus the future 350-line test allocation is 1857. The 843-line difference from projected 2700 is not authorization for another file. NET/NF account for 645 current lines against 1000 projected (355 growth); BC/OP account for 862 current read-only lines against 1350 projected. Their unused projection does not permit edits to them. No sixth implementation/helper/probe/test/source is available in this task.

## Existing APIs and observable source contracts

These are the current signatures, not proposed constructor keyword spellings:

```text
NET:222 TokenSetEncoder(token_spec, token_embed_dim, aggregator_type, num_heads)
NET:367 TokenSetQNetwork(token_spec, action_dim, token_embed_dim,
                       q_head_hidden_dim, aggregator_type, num_heads)
NET:411 RecurrentTokenQNetwork(token_spec, action_dim, token_embed_dim,
                             q_head_hidden_dim, aggregator_type, num_heads,
                             lstm_hidden_size, lstm_num_layers, lstm_dropout)
NF:134 NetworkFactory.build_token_set(config: TokenSetConfig,
                                     action_dim: int, token_spec: TokenSpec)
          -> TokenSetQNetwork
NF:73  NetworkFactory.build_recurrent(config: RecurrentConfig,
                                     action_dim: int, token_spec: TokenSpec)
          -> RecurrentTokenQNetwork
```

Both factory methods pass token schema, action/embedding/head dimensions, `config.aggregator.type`, and `config.aggregator.num_heads`. The recurrent method additionally passes `config.lstm.hidden_size`, `.num_layers`, and `.dropout`. Neither reads `config.token_encoder`, calls `resolve_token_encoder`, nor passes an encoder mode or hidden width. Both network wrappers create the same `TokenSetEncoder` with the four existing arguments. No present constructor accepts P4's mode/width.

NET's inspected schema consumption is exact: `token_spec.types` supplies `type_name`, `capacity`, and `payload_width`; `token_spec.compact_layout().get_type(type_name)` supplies `compact_row_width`, `start`, and `end`; `token_spec.total_dims` is `obs_dim`. Only positive-capacity types receive layouts, encoder parameters, and type embeddings. An entirely zero-capacity roster raises `ValueError`, independently of an all-absent observation of a valid live roster.

NET:303 `_embed_tokens(obs)` requires rank 2 with width `obs_dim`. Each type slice is viewed as `[batch, capacity, compact_row_width]`; `input_assembler.expand_type(type_name, dynamic_rows)` reconstructs fixed rows. Presence is `rows[:, :, 0] > 0.5`; all remaining assembled descriptor/live fields jointly enter that type's current `nn.Linear(payload_width, token_embed_dim)`, followed by its learned type embedding. Type-name keys, not roster indices, own parameters. The assembler is constructed from the supplied/target `TokenSpec` at NET:267. Its implementation was not inspected.

NET:326 `pooled_embedding(obs) -> Tensor[batch, token_embed_dim]` and NET:359 encoder `forward(obs)` use the same result. Mean has no attention modules or heads. Attention retains explicit Q/K/V/output projections and `scaled_dot_product_attention` under the MATH backend, masks absent keys, and unmasks keys for an all-empty batch row to keep attention finite. Both finish by multiplying encoded outputs by boolean presence, summing, and dividing by present count clamped to one. Preserve that masking location after either row encoder; static assembly, type embeddings, and post-encoder biases cannot bypass it.

NET:401 token Q-network `pooled_embedding(obs)` delegates to its encoder; NET:404 `forward(obs)` returns `[batch, action_dim]` via its Q-head. The head is `Linear -> LayerNorm -> ReLU -> Linear`, at sequential indices 0, 1, 2, and 3. Exact-zero empty pooled output does not imply zero Q output: head biases remain allowed.

NET:456 recurrent `initial_hidden(batch_size, device) -> (h, c)` creates zeros shaped `[lstm.num_layers, batch_size, lstm.hidden_size]`. NET:460 `forward(observations, hidden) -> (q_values, new_hidden)` requires `[batch, sequence, obs_dim]`, encodes flattened frames once, reshapes to `[batch, sequence, token_embed_dim]`, calls one batch-first LSTM with the caller's explicit `(h, c)`, and applies the same head structure at every step. Q shape is `[batch, sequence, action_dim]`; hidden/cell threading and zero-start semantics must remain intact. There is no implicit hidden initialization in `forward`.

## P4 already supplied versus the actual G01 gap

OP:23 already defines strict/frozen `TokenEncoderOptions` with `mode: Literal['linear','interaction_mlp']` and `hidden_width: positive int | None`. Linear rejects any non-None width; interaction MLP requires an explicit positive width. OP:38 `resolve_token_encoder(options: TokenEncoderOptions | None) -> tuple[TokenEncoderOptions, str]` returns `(TokenEncoderOptions(mode='linear'), 'bac-options-v1: omitted token_encoder retains linear')` for omission and `(options, 'authored')` otherwise. The immutable options and validation are present; they need no T17 edit.

BC:147 `TokenSetConfig.token_encoder` and BC:172 `RecurrentConfig.token_encoder` already accept the optional options object. Embedding/head dimensions and aggregation remain required; attention geometry is validated independently. Thus authored `interaction_mlp` can enter either DTO today, while the inspected factory ignores it and constructs linear encoders. This is the specific unresolved runtime routing/representation gap. No current test in the fifth slot supplies red or green evidence.

For present same-type rows, the implemented affine row feature is `W_c c_i + W_v v_i + b + e_type`. Mean sees descriptor and live-value sums separately. Reassigning the same two values among fixed descriptor identities preserves the mean in exact arithmetic, so a nonlinear head after pooling cannot recover the binding. This is G01, the accepted revised-design gap; it does not contradict the old implementation recipe or invalidate historical linear-mean studies. Mean and attention, linear mode, token-set and recurrent families remain selectable.

Accepted P4 supplies the addition: per-type `Linear -> ReLU -> Linear` over the assembled joint descriptor/live row before pooling, using an explicit hidden width. Each interaction encoder must be `nn.Sequential` with Linear modules at indices 0 and 2. It is not permission to move interaction after pooling, replace mean, remove attention, or remove historical controls. No additional design decision is introduced by this receipt.

## State and static-context boundary

The state names below are inferred directly from inspected module registration and ordinary `nn.Module` naming, not from a runtime `state_dict()` probe:

| Current component | Linear mode state names to preserve |
| --- | --- |
| Bare `TokenSetEncoder` row encoder | `encoders.<type>.weight`, `encoders.<type>.bias` |
| Bare encoder learned type vector | `type_embeddings.<type>` |
| Attention-only encoder projections | `q_proj.{weight,bias}`, `k_proj.{weight,bias}`, `v_proj.{weight,bias}`, `out_proj.{weight,bias}` |
| Either Q-network's shared encoder | The above with `encoder.` prefix |
| Either Q-head | `q_head.0.{weight,bias}`, `q_head.1.{weight,bias}`, `q_head.3.{weight,bias}` |
| Recurrent memory | `lstm.weight_ih_l<layer>`, `lstm.weight_hh_l<layer>`, `lstm.bias_ih_l<layer>`, `lstm.bias_hh_l<layer>` |

P4's interaction Sequential gives mode-distinct `encoder.encoders.<type>.0.{weight,bias}` and `.2.{weight,bias}` in either wrapper; indices and hidden-width-dependent shapes must remain unambiguous to later transfer consumers. Linear must retain its old direct Linear registration/state shape and exact computation/initialization behavior rather than gain a Sequential wrapper or extra persistent mode state.

The supplied B02 report says assembler context buffers were `persistent=False`, no `_token_context_` entries appeared in checkpoint state, and loading identical weights into a network constructed with permuted target context retained the target's context. This is supplier prose at B02's pinned historical SHA, not a fresh inspection of `token_input.py`. P4 requires the same target-owned/nonpersistent context in both modes. The current NET assembly call is compatible with that ownership, but does not independently prove the assembler implementation or loader behavior today.

BC:506 `compute_brain_hash(config)` still hashes JSON from `config.model_dump()` with sorted keys; the explicit encoder declaration is in the object being hashed. Preserve this API/meaning. Effective-run/execution identity, compiled serialization, checkpoint loader/refusal/transfer routing and their source files were not inspected. No claim about their present correctness follows from module-key inference; source-verified supplier handoffs are required where the future bounded test touches them.

## Exact fixture DATA/API handoffs still needed

The only external evidence read was `/workspace/bac-review-2026-11-01/B02.md` as prose. Its linked sources, scratch script, pack, logs, JSON, and other reports were not opened. It provides abbreviated declaration expressions, not complete valid YAML or executable current APIs. These are concrete inputs missing from the bounded T17 test-authoring handoff, not authorization to open a sixth source:

| Needed handoff | Exact content required inside the existing boundary |
| --- | --- |
| Full authored complementary-variable DATA | Complete valid base-pack/reference and override YAML bytes, all required declaration fields, exposed global scalar declarations with distinct initial values `0.125`/`0.875`, identical bounded `[0,1]` normalization, and `where(tick % 2 == 0, 0.25, 0.75)` / its complement. Freeze every relevant meter depletion/recovery rate as in B02 so other observed fields do not change. Supply current source/version provenance; the abbreviated report snippet is insufficient. Keep future fixture generation in the one allowed test rather than create a sixth helper/source file. |
| Compiler/environment API prose | Source-verified import paths, callable names and full signatures for normal uncached compilation, two-world construction, reset, legal WAIT action construction and one step; exact return tuples/objects, observation tensor extraction, token spec and action-count extraction, required settings, and cleanup. No state injection. B02 reports historic `[2,147]` observations and changed columns 142/145; neither dimension nor offsets may be assumed current without schema-derived confirmation. |
| Descriptor and transport coordinates | Exact current fixed assembled variable-row descriptor/live-field names and indices, compact presence/value offsets, capacity/row starts, descriptor values after normalization, plus the public immutable TokenSpec/context construction API. This is needed to select joint-row weights and to identify the two live rows without hard-coding B02 offsets. NET exposes shape consumption, not those constructors or field identities. |
| Semantic permutation DATA/API | Source-verified immutable way to create the target compiled spec with each semantic compact row and its positional context permuted together, while retaining compatible learned-weight layout. Supply exact context payload/constructor fields and mapping. Compact rows alone permuted against fixed contexts constitute a value reassignment witness, not semantic invariance. Do not mutate private assembler buffers as a substitute for the compiled-context contract. |
| Constructive and selected-weight DATA | Exact encoder tensors selecting a verified descriptor coordinate and live value; all unrelated input coefficients zero. The two-row normalized witness uses `c in {0,1}` and `ReLU(v+c-1)`: assignments `(c,v)=(0,.25),(1,.75)` yield pooled `.375`; reassignment yields `.125`. Supply the explicit descriptor transformation when actual authored contexts are `.125`/`.875`. Whole authored packs have additional present rows, so their mixed-set denominator need not be two. Supply deterministic full encoder/type-vector/Q-head tensors, selected action index and expected nonzero Q distinction for that authored case, respecting the existing head's LayerNorm. Random weights/seed difference alone cannot establish expressivity. |
| Resolved encoder/API handoff | Existing exact portable fields are `token_encoder.mode` and `.hidden_width`; omission resolver/provenance is above. Factory and both wrappers must receive the resolved selection. The brief does not fix spellings/order of added network constructor parameters; the current source has none. Supply the implementer's agreed exact keyword names when test authoring is cleared, without guessing an existing API or adding a constructor-local behavioral default. |
| State/identity consumer prose if exercised | Current source-verified API and expected refusal/omission behavior for same-mode weights, cross-mode incompatibility and target-owned context, and the execution-identity metadata interface. No loader, assembler, effective-run, compiler or extra test source may be opened under T17 to infer these contracts. |

## Bounded evidence and later acceptance checks

No runtime command was run for this receipt. The available executed evidence is historical B02 prose pinned to `4aa5363b5de54d9a112977c32c2975f37627197f`: 194 focused tests passed; its authored complementary-variable case had mean pooled delta `1.4901161193847656e-08` and Q delta `5.960464477539063e-08` (roundoff), while attention had respective nonzero deltas `7.450580596923828e-06` and `1.0609626770019531e-05`. Those numbers are not new T17 execution or an interaction-MLP result.

B02 also reports exact-zero absent-type encoder/type-vector gradients, finite exact-zero empty pooled values/encoder gradients for mean and attention, semantic row-plus-context permutation Q equality within `5.960464477539063e-08`, one-call sequence equivalence and recurrent-weight gradient paths, and nonpersistent static context. These are retained working controls with stated historical scope, not requalified present results. CPU-only network evidence does not establish replay/learner orchestration, CUDA, long-run learning or checkpoint atomicity.

The existing T17 brief already fixes the single-test-file acceptance evidence; no new programme is proposed here:

| Named future test | Required bounded evidence once T16 is qualified and the root owner clears work |
| --- | --- |
| `test_mean_can_bind_descriptor_value` | First new-mode red against current NF/NET; deterministic two-row `.375` versus `.125` prepool interaction witness; full authored complementary-variable pack yields a selected nonzero Q distinction. Include both network-family factory paths and retain both aggregator choices within the named file's scope. |
| `test_linear_mean_is_preserved` | Explicit and omitted-resolved linear use old state keys/shapes and identical selected-weight behavior, with the truthful value-reassignment alias retained. Floating-point reduction roundoff must not be misreported as represented binding. Do not assert random weights must distinguish. |
| `test_semantic_permutation_absence_and_memory` | Semantic rows and context travel together; Q/pooled equality within `1e-6`. Poisoned absent rows and valid all-empty observations have finite exact-zero pooled contribution and relevant row-encoder gradients (including both MLP Linear layers) exactly zero; absent-type vector gradients remain zero. Keep nonzero head bias allowable. Use zero-start hidden state, compare full sequence with threaded per-frame calls, and keep current-frame alias/binding separate from information available through distinguishing history. |

After those tests exist and red is genuine, the brief requires green plus existing compact/context/empty/permutation/network suites and frame-versus-history separation. Their sources were not read and none were executed now. Full-suite or programme qualification is owned by root and is not conferred by this receipt.

## Disposition

Readiness inspection is finite: current schema support is present; NF routing and NET nonlinear per-row encoding/state identity are still missing; exact missing authored DATA/API inputs are enumerated above. T17 is not implemented, tested, qualified, or cleared. T16's unqualified dependency and the active-writer source/runtime barrier remain. This worker becomes stationary after handing back this receipt.

## Addendum — supplied fixture closure and concrete additive API choice

2026-11-02 UTC, root-requested read-only follow-up while G2 remains frozen. Consumed whole as source-verified prose only: `T17-fixture-api-handoff.md`, SHA256 `7595dd625f196f22433c9db32a29ce19c2ba164f2a7f437f8234f2916ab707ab`, and `T17-env-public-api.md`, SHA256 `41cb275e96e52f6e771889ba92138c4819c1bd02082903d6829b64267ec48e74`. No implementation, DATA, helper, probe, or test links in either handoff were followed. Their TS/TI/UC/EF/ENV facts are supplier evidence, not extra source inspections by this worker. This addendum supplies the routine API choice root requested within accepted P4; it opens no design/plan/review cycle and grants no authoring/runtime clearance.

The supplied full replacement YAML documents, immutable TokenSpec/context constructors and feature coordinates, semantic permutation recipe, authoritative compiler and ENV calls, WAIT record/mask lookup, and complete constructive encoder/head tensor specifications close the corresponding missing-handoff rows above. In particular: use selected `L0_test`, normal uncached compile and two-world ENV reset plus one legal WAIT; clone returned observations, derive pulse slots from bindings and coordinates from feature names, and assert actual dtype/device/presence/non-pulse stability. The authored descriptor values are `.125/.875`; their joint feature is implemented by the supplied `ReLU(3v+4d-3.5)/3` tensors. The full-pack pool uses actual common present count N, and its selected token-set Q-head uses a fixed reference coordinate through LayerNorm. The isolated two-row `.375/.125` witness remains distinct from that full-pack result. Supplied deterministic recurrent evidence is the shared encoder witness plus zero-start/threaded-sequence controls, not an asserted identity LSTM or random recurrent Q separation. No external cleanup API is supplied or needed beyond fixture-local object lifetime.

### Exact new public construction surface

Retain all three existing direct `__init__` signatures listed above, including their positional argument behavior and fixed linear meaning. Add the classmethod name **`from_resolved_encoder`** on all three classes. Every argument of the new classmethods is keyword-only and required, including an explicit `None` width for linear. Exact signatures selected for implementation are:

```text
TokenSetEncoder.from_resolved_encoder(
    *, token_spec: TokenSpec, token_embed_dim: int,
    aggregator_type: str, num_heads: int | None,
    token_encoder_mode: Literal['linear', 'interaction_mlp'],
    token_encoder_hidden_width: int | None,
) -> TokenSetEncoder

TokenSetQNetwork.from_resolved_encoder(
    *, token_spec: TokenSpec, action_dim: int, token_embed_dim: int,
    q_head_hidden_dim: int, aggregator_type: str, num_heads: int | None,
    token_encoder_mode: Literal['linear', 'interaction_mlp'],
    token_encoder_hidden_width: int | None,
) -> TokenSetQNetwork

RecurrentTokenQNetwork.from_resolved_encoder(
    *, token_spec: TokenSpec, action_dim: int, token_embed_dim: int,
    q_head_hidden_dim: int, aggregator_type: str, num_heads: int | None,
    lstm_hidden_size: int, lstm_num_layers: int, lstm_dropout: float,
    token_encoder_mode: Literal['linear', 'interaction_mlp'],
    token_encoder_hidden_width: int | None,
) -> RecurrentTokenQNetwork
```

The exact added keywords are **`token_encoder_mode`** and **`token_encoder_hidden_width`**. Neither has a default or accepts an unresolved omission marker for mode. `token_encoder_hidden_width=None` is an explicit valid value only when mode is linear; interaction requires a positive explicit integer. Reject an invalid explicit pair using OP's validated semantics, without selecting another mode or filling a width. The new classmethod is the explicit resolved-selection API. Calling the existing direct constructor continues selecting its already-published linear API; that retained fixed meaning is not a fallback for an omitted new option.

Keep `NetworkFactory.build_token_set(config, action_dim, token_spec)` and `.build_recurrent(config, action_dim, token_spec)` signatures unchanged. Each obtains `selected, origin = resolve_token_encoder(config.token_encoder)` from the existing authoritative OP resolver, then calls the matching wrapper's `from_resolved_encoder` with all current dimension/aggregator/LSTM arguments unchanged and these exact additions:

```text
token_encoder_mode=selected.mode
token_encoder_hidden_width=selected.hidden_width
```

The wrappers forward exactly those two required keywords to `TokenSetEncoder.from_resolved_encoder`. NF must use this route for both explicit and omitted authored declarations, so no wrapper/encoder interprets `None` as a policy choice. OP's versioned resolver owns omission semantics; authored/effective-run provenance remains its existing owner's responsibility. A neural module does not silently invent or redefine execution identity/provenance. Both aggregation choices and recurrent/forward/hidden APIs remain unchanged.

### Common initialization and identity constraints

Give each of the three classes one private **`_initialize`** method shared by its unchanged `__init__` and its new classmethod. It receives that class's complete existing constructor values plus required keyword-only `token_encoder_mode` and `token_encoder_hidden_width`. The existing constructor delegates with the literal established selection `token_encoder_mode='linear', token_encoder_hidden_width=None`; the new classmethod allocates the instance with `cls.__new__(cls)` and invokes `_initialize` directly with its explicit pair. The common initializer calls `nn.Module` initialization exactly once. Do not construct a throwaway linear network and replace its encoder, call a normal constructor then reinitialize, or allocate trial layers before the chosen path: those approaches consume extra RNG and alter initialization.

For the linear branch preserve the current module creation and registration order, the same direct per-type `nn.Linear` objects in the same live type order, zero type-vector initialization, and unchanged optional attention/Q-head/LSTM construction order. The encoder common initializer retains target `TokenSpec` assembly before row projections as today. Wrapper common initializers retain encoder-before-head, or encoder-before-LSTM-before-head, as today. Validation and nonpersistent scalar attributes must not consume RNG. Thus the old direct path and explicit resolved-linear path can start from the same RNG state and produce identical keys, shapes, parameter bytes and forward behavior; a Sequential wrapper around linear is excluded.

The interaction branch creates only the accepted per-type `nn.Sequential(Linear(payload_width, hidden_width), ReLU(), Linear(hidden_width, token_embed_dim))` before the existing type-vector/aggregation path. Keep type-name parameter ownership and output-side masking. If exposed on the modules, `token_encoder_mode` and `token_encoder_hidden_width` are ordinary nonpersistent Python attributes, not extra checkpoint tensors. Existing linear keys stay byte-for-byte spelled as above; the interaction keys differ through Linear indices 0/2 and their hidden-width shapes. This is mode-aware module-state identity, without a claim that an excluded checkpoint consumer has been changed or verified.

Every construction path creates `TokenInputAssembler` from its own supplied target spec. Supplier TI evidence establishes all `_token_context_`, `_dynamic_lanes_`, and `_fixed_lanes_` buffers are nonpersistent. New same-mode weight loads into a semantic-permutation target therefore preserve that target's context; do not copy the source assembler or private buffers. The original empty/absent mask, attention guard and recurrent zero-start/full-sequence contract remain load-bearing. The selected API adds capability without removing or degrading any existing selectable family.

### Finite test reservation within the same five files

The original 350-line reservation is too tight to commit to all supplied controls in readable form: the two complete replacement DATA documents alone contain **71 and 49 YAML lines**, before authored mode selection, normal fixture materialization/API assertions, immutable semantic permutation, deterministic two-row/full-pack tensors, linear state/initialization controls, both MLP-layer absence gradients, all-empty attention, and recurrent frame/history comparisons. It could be compressed by generating equivalent DATA from the canonical base, but this receipt does not trade away a control or require dense code to force that projection.

Recommend an **800-physical-line test reservation**, with all fixture functions/DATA remaining inside `test_token_binding.py`, no sixth source/helper/test. A bounded allocation is 120 full replacement YAML lines, 100 authored compiler/ENV fixture and assertions, 90 immutable toy/permutation construction, 70 deterministic weight setup, 65 constructive/authored witness assertions, 65 linear/state/initialization controls, 90 semantic-permutation/context assertions, 85 absence/empty/gradient controls, 80 recurrent sequence/frame/history controls, and 35 imports/parameterization/spacing: total 800. These are reservations, not a claim authored tests already exist. Share setup within this one file; keep the three accepted named tests and parameterize applicable encoder/pooling/family controls rather than create additional test files. A full authored pack need not be duplicated per parameter combination.

Reallocate confirmed unused read-only projections to that test instead of expanding the source set:

| Named source | Original projection | Recommended finite reservation | Access unchanged |
| --- | ---: | ---: | --- |
| NET | 750 | 750 | eventual modify |
| NF | 250 | 250 | eventual modify |
| BC | 750 | 568 | read only; actual counted size |
| OP | 600 | 294 | read only; actual counted size |
| test | 350 | 800 | eventual create test |
| Total | 2700 | **2662** | same five files |

The 450-line test increase fits within the 488 lines of unused BC/OP projections; 38 original projected lines remain unallocated. The proposal stays below both the original 2700-line projection and the overall 5000-line ceiling, without borrowing a sixth source or authorizing BC/OP edits. Root owns adopting this finite reservation when implementation clears. Excluded checkpoint/transfer/refusal/execution-identity consumers remain outside these tests unless their separate source-verified prose is supplied; ordinary same-mode module-state/context behavior is already supplied.

Disposition after addendum: concrete keyword/API choice and finite budget recommendation are ready for the existing T17 owner. No source/test implementation, runtime acceptance or G2 clearance occurred. T17 authoring still waits for T16 qualification and root clearance; worker returns stationary.
