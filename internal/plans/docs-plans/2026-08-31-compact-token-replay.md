# Compact Token Replay Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the 4,090-float full-payload transition ABI with one compiled, compact token serialization whose current L1 width is 115 floats, while reconstructing the unchanged fixed per-type projection schema only at the token-network boundary.

**Architecture:** `TokenSpec` remains the single observation artifact. It owns a required substrate `position_rank`, required compact transport version, compact row layouts, and immutable per-type context tables. Environment publishers emit only compact dynamic rows; replay, flat, dueling, RND, and the current block-recurrent reader consume those rows directly. A network-owned `TokenInputAssembler` expands one type immediately before `TokenSetQNetwork` projects it; no production API reconstructs a complete fixed observation tensor. This is a hard artifact cut: no legacy serializer, migration, fallback, alias, or dual ABI remains.

**Tech Stack:** Python 3.13 or newer, frozen dataclasses, PyTorch tensors/modules, msgpack compiled artifacts, pytest, Ruff, Black, mypy, Filigree.

**Prerequisites:**

- Work only on `project-recovery-3`; preserve unrelated work and verify the branch before every commit.
- M1 `hamlet-6a4a6596bd` and M2 `hamlet-1e335e0363` are terminal.
- M3 `hamlet-1b1caf552a` is `in_progress` and assigned to `codex`.
- REQUIRED SUB-SKILL: Use superpowers:test-driven-development.
- The repository is pre-release with zero users: old caches/checkpoints must fail, not migrate.

---

## Frozen engineering rulings

1. `TokenSpec.total_dims` and `TokenSpec.row_layout()` describe the sole compact environment/replay serialization. The internal fixed projection shape is named `fixed_total_dims` and `fixed_row_layout()`; it is never an environment or replay ABI.
2. Current L1 is exactly 115 floats. The PDR's 118 target is current L1 plus one three-lane scalar `variable_element`; the acceptance cap remains 120.
3. `variable_element` coordinates, rank, `value_width_used`, and descriptor are immutable compiled context. Its compact row is always `presence,value_0,value_1`, independent of tensor rank.
4. Effect slots are scope-budget lanes, not declaration-bound lanes. A compact effect row therefore carries `context_index` in addition to live state. This is validated finite, integral, exactly representable in float32, and in range before gathering; it is ignored for absent rows and never enters the fixed projected payload. Compilation refuses a catalog whose highest index is not exactly representable in float32.
5. Delete `SlotBinding.static_signature`. Each `TokenTypeSchema` owns positional `slot_context_payloads` for non-effect slots; identity remains solely in `SlotBinding.filler_ref`. The effect type instead owns named `effect_catalog_contexts` in catalog order, selected by `context_index`. Their different selection semantics are explicit, not hidden behind one overloaded table.
6. Keep `token_type_schema_hash` over the unchanged fixed projected feature vocabulary. Redefine `layout_hash` over compact transport version, compact lane order, rank, capacities, binding order, and effect catalog references/order. `observation_schema_hash` adds immutable slot/catalog context contents.
7. Keep `token-1.1`: the fixed transfer schema is unchanged. Add required `TokenSpec.transport_version = "compact-1"` and validate it exactly; no missing-value inference. Bump every artifact that could contain full transition rows.
8. Static context registered in a network is `persistent=False`; it must not be copied into model checkpoints or contaminate cross-universe weight transfer.

## Task 1: Commit the RED contract and reviewed plan

**Files:**

- Create: `tests/test_townlet/unit/universe/test_compact_token_layout.py`
- Modify: `tests/test_townlet/unit/training/test_token_checkpoint_gates.py`
- Create: `docs/plans/2026-08-31-compact-token-replay.md`
- Create: `docs/plans/2026-08-31-compact-token-replay.review.json`

**Step 1: Verify the focused contract is RED for the intended missing behavior**

Run:

```bash
uv run pytest \
  tests/test_townlet/unit/universe/test_compact_token_layout.py \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py::TestCompactReplayArtifactCut \
  -q
```

Expected: nine or more failures naming the missing required `position_rank`, missing compact layout/context table, and checkpoint version 4 instead of 5. No failure may be an import, collection, or fixture error.

**Step 2: Verify the tests themselves are clean**

Run:

```bash
uv run ruff check \
  tests/test_townlet/unit/universe/test_compact_token_layout.py \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py
uv run black --check \
  tests/test_townlet/unit/universe/test_compact_token_layout.py \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py
git diff --check
```

Expected: all three commands exit 0.

**Step 3: Commit only the RED contract and plan**

```bash
test "$(git branch --show-current)" = "project-recovery-3"
git add \
  docs/plans/2026-08-31-compact-token-replay.md \
  tests/test_townlet/unit/universe/test_compact_token_layout.py \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py
git add -f docs/plans/2026-08-31-compact-token-replay.review.json
git commit -m "test(tokens): pin compact replay artifact cut"
```

**Definition of Done:**

- [ ] Compact L1 115 / synthetic 118 / byte caps are pinned.
- [ ] Ranked variables and world-specific effects are pinned through the network-owned per-type assembler.
- [ ] `TokenSpec.total_dims` is pinned as compact and fixed reconstruction is separately named.
- [ ] The checkpoint v5 refusal happens before state access.
- [ ] Only the four named paths are committed.

## Task 2: Make `TokenSpec` the compact compiled authority

**Files:**

- Modify: `src/townlet/universe/dto/token_spec.py`
- Modify: `src/townlet/universe/compilers/observation.py`
- Modify: `src/townlet/universe/token_hashes.py`
- Modify: `src/townlet/universe/compiled.py`
- Modify: `src/townlet/universe/compilers/metadata.py`
- Modify: `tests/test_townlet/unit/universe/test_token_spec.py`
- Modify: `tests/test_townlet/unit/universe/test_token_emission.py`
- Modify: `tests/test_townlet/unit/universe/test_compiled_token_coherence.py`
- Modify: `tests/test_townlet/unit/universe/test_compiled_universe.py`
- Modify: `tests/test_townlet/unit/universe/test_compiler_cache.py`
- Modify: `tests/test_townlet/unit/training/test_token_checkpoint_gates.py`
- Modify: `tests/test_townlet/unit/universe/test_compact_token_layout.py`

**Step 1: Add failing artifact/hash/cache tests**

Pin these exact contracts:

```python
assert spec.position_rank == 2
assert spec.total_dims == 115
assert spec.fixed_total_dims == 4090
assert compute_token_type_schema_hash(grid2d) == compute_token_type_schema_hash(grid3d)
assert compute_token_layout_hash(grid2d) != compute_token_layout_hash(grid3d)
with pytest.raises(ValueError, match="schema version"):
    CompiledUniverse.from_dict(old_125_payload)
```

Also assert that `SlotBinding.__dataclass_fields__` contains no `static_signature`; non-effect `slot_context_payloads` carry no identity field; only effect catalog entries carry a `context_ref`. Assert `TokenSpec.transport_version` is required and has no default.

Add these named parameterized tests to `test_compiled_universe.py`:

- `test_compiled_token_artifact_rejects_unknown_and_legacy_keys`;
- `test_compiled_token_artifact_rejects_invalid_rank_and_transport_version`;
- `test_compiled_token_artifact_rejects_invalid_context_tables`;
- `test_schema_version_refuses_before_invalid_token_payload`.

They cover every malformed key/rank/context case listed in Step 4 and both direct-dict and real-MessagePack load paths.

**Step 2: Verify those tests fail before implementation**

Run only the artifact-owned node IDs; assembler parity stays RED until Task 3:

```bash
uv run pytest \
  tests/test_townlet/unit/universe/test_compact_token_layout.py::test_immutable_context_is_schema_owned_without_duplicating_non_effect_identity \
  tests/test_townlet/unit/universe/test_compact_token_layout.py::test_current_l1_dynamic_census_is_exactly_115_and_below_the_120_cap \
  tests/test_townlet/unit/universe/test_compact_token_layout.py::test_one_rank_zero_variable_preserves_the_118_target_shape \
  tests/test_townlet/unit/universe/test_compact_token_layout.py::test_compact_l1_rows_exclude_descriptors_and_fixed_rank_padding \
  tests/test_townlet/unit/universe/test_token_spec.py \
  tests/test_townlet/unit/universe/test_token_emission.py \
  tests/test_townlet/unit/universe/test_compiled_token_coherence.py \
  tests/test_townlet/unit/universe/test_compiled_universe.py \
  tests/test_townlet/unit/universe/test_compiler_cache.py \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py::TestAttachStampsTokenHashes \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py::TestTokenNetGate \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py::TestFlatNetLayoutGate \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py::TestLoadByTypeKey \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py::TestCrossUniverseLoadResets \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py::TestReviewRound1Pins \
  -q
```

Expected: failures identify the old full layout, old signature field, equal cross-rank layout hashes, and schema `1.25`.

**Step 3: Implement the immutable context and compact layouts**

The core data shape is:

```python
@dataclass(frozen=True)
class TokenContext:
    context_ref: str
    fixed_payload: tuple[float, ...]


@dataclass(frozen=True)
class TokenSpec:
    types: tuple[TokenTypeSchema, ...]
    position_rank: int
    transport_version: str
    encoding_version: str = ENCODING_VERSION

    @property
    def total_dims(self) -> int:
        return sum(token_type.capacity * token_type.compact_row_width for token_type in self.types)

    @property
    def fixed_total_dims(self) -> int:
        return sum(token_type.capacity * token_type.fixed_row_width for token_type in self.types)

    def compact_layout(self) -> CompactTokenLayout:
        return CompactTokenLayout.from_spec(self)
```

`CompactTokenLayout` contains only compact offsets, row widths, dynamic feature names, and fixed scatter indices. It exposes no complete fixed-tensor reconstruction method.

Define and export `TOKEN_TRANSPORT_VERSION = "compact-1"`. `TokenTypeSchema` must carry the unchanged fixed `payload_features`, positional `slot_context_payloads` for non-effect types, and `effect_catalog_contexts` only for the effect type. Context payloads canonicalize to float32 and validate exact fixed width, finiteness, and `[-1,1]` bounds. Derive compact features from one closed mapping plus `position_rank`; do not serialize a second authored schema. Move `element_coordinate_block` from `environment/token_publishers.py` into `token_spec.py` so variable context is compiled from declaration shape and element index. Update `test_compact_token_layout.py` to import it from that canonical owner; leave no re-export in `token_publishers.py`.

Build full fixed-payload context rows once:

- `self`, `agent`, `item`, `affordance`: normalized `position_rank` plus declared static fields;
- `meter`: signature plus `value_width_used`;
- `variable_element`: element coordinates/rank, `value_width_used`, and descriptor;
- `effect`: one named catalog row per declaration in catalog order, not one declaration per runtime slot. Refuse more than `2**24` catalog entries so every `context_index` is an exact float32 integer.

The artifact layer stops here. Full fixed rows are assembled only by the network component in Task 3.

**Step 4: Redefine identity and persistence without aliases**

- Set `COMPILED_SCHEMA_VERSION = "1.26"`.
- Serialize required `position_rank`, required `transport_version`, positional context payloads, and effect catalog refs/payloads.
- Deserialization requires the exact new keys. Do not read `static_signature` or infer a missing rank.
- Validate exact key sets at TokenSpec, type, binding, slot-context, and effect-context levels. Reject unknown legacy `static_signature`; boolean/non-integer/out-of-range ranks; missing or wrong transport versions; slot-context count mismatches; malformed payload widths; non-finite/out-of-bounds payloads; and duplicate or empty effect context refs before constructing `TokenSpec`.
- `canonical_token_type_schema()` remains fixed-schema-only.
- `canonical_token_layout()` includes `transport_version`, compact feature order, compact `total_dims`, `position_rank`, bindings, and effect catalog refs/order. Non-effect filler refs are hashed once through slot bindings.
- `canonical_observation_schema()` adds context payloads.

Update every `TokenSpec`/`SlotBinding` constructor in `test_token_checkpoint_gates.py` to the new required artifact shape during this task; the checkpoint v5 assertions remain RED until Task 4.

**Step 5: Run the artifact slice GREEN**

Run the command from Step 2.

Expected: every selected artifact/hash fixture test passes; the excluded two v5 assertions remain intentionally RED until Task 4. Current L1 reports compact 115 and fixed 4090.

For cache refusal ordering, feed both `CompiledUniverse.from_dict()` and a real MessagePack `load_from_cache()` a schema-1.25 payload whose nested token content is deliberately invalid. The schema-version error must win before nested token interpretation.

**Definition of Done:**

- [ ] One compiled artifact owns rank, compact layout, and static context.
- [ ] Variable coordinates are absent from compact rows.
- [ ] Effect context order is explicit and hashed.
- [ ] Token transfer hash is stable across Grid2D/Grid3D/aspatial.
- [ ] Old 1.25 caches refuse before token deserialization.
- [ ] No `static_signature` or full-transition serializer remains.

## Task 3: Land a vertical compact tracer, then cut every live reader

**Files:**

- Modify: `src/townlet/environment/token_publishers.py`
- Modify: `src/townlet/environment/observation_encoder.py`
- Modify: `src/townlet/environment/vectorized_env.py`
- Modify: `src/townlet/agent/networks.py`
- Create: `src/townlet/agent/token_input.py`
- Modify: `src/townlet/agent/network_factory.py`
- Modify: `src/townlet/agent/token_diagnostics.py`
- Modify: `src/townlet/exploration/rnd.py`
- Modify: `tests/test_townlet/unit/environment/test_token_publishers.py`
- Modify: `tests/test_townlet/unit/agent/test_token_set_qnetwork.py`
- Modify: `tests/test_townlet/unit/agent/test_network_factory.py`
- Modify: `tests/test_townlet/unit/agent/test_networks.py`
- Modify: `tests/test_townlet/unit/agent/test_token_diagnostics.py`
- Modify: `tests/test_townlet/integration/test_token_transfer_contract.py`
- Modify: `tests/test_townlet/integration/test_substrate_observation_seam.py`
- Modify: `tests/test_townlet/unit/substrate/test_observation_shape_contract.py`
- Modify: `tests/test_townlet/unit/universe/test_token_numeric_contract.py`
- Modify: `tests/test_townlet/unit/universe/test_compact_token_layout.py`
- Modify: `tests/test_townlet/integration/test_meter_bounds_runtime.py`
- Modify: `tests/test_townlet/regressions/test_affordance_token_identity.py`
- Modify: `tests/test_townlet/integration/test_compile_cache_level_identity.py`
- Modify: `tests/test_townlet/integration/test_reference_model_pack.py`
- Modify: `tests/test_townlet/integration/test_effects_smoke.py`
- Modify: `tests/test_townlet/integration/test_token_set_runtime.py`
- Modify: `tests/test_townlet/unit/environment/test_vectorized_env.py`
- Modify: `src/townlet/universe/__main__.py`
- Create: `tests/test_townlet/integration/test_compact_token_runtime.py`

**Step 1: Add a failing vertical tracer before broad conversion**

Create `tests/test_townlet/integration/test_compact_token_runtime.py::test_l1_compact_vertical_trace`. It must execute this chain for one L1 tick: compile -> env reset/step -> compact observation width 115 -> replay push/sample -> flat forward -> one token type expanded/projected by `TokenInputAssembler`.

Run:

```bash
uv run pytest tests/test_townlet/integration/test_compact_token_runtime.py::test_l1_compact_vertical_trace -q
```

Expected before implementation: failure at the old 4,090-wide environment output. Expected after the tracer lands: pass before broadening coverage to all token types.

**Step 2: Add failing end-to-end compact publisher/reader tests**

Cover all seven token types, including:

```python
compact = encoder.encode(batch_size=2, ctx=context)
affordance_layout = layout.get_type("affordance")
dynamic_rows = compact[:, affordance_layout.start : affordance_layout.end].view(
    2,
    affordance_layout.capacity,
    affordance_layout.compact_row_width,
)
rows = assembler.expand_type("affordance", dynamic_rows)
assert torch.equal(rows, expected_fixed_affordance_rows)
assert compact.shape == (2, spec.total_dims)
```

Freeze this sole assembler signature:

```python
def expand_type(self, type_name: str, dynamic_rows: torch.Tensor) -> torch.Tensor:
    """[B, capacity, compact_row_width] -> [B, capacity, fixed_row_width]."""
```

The network, not the assembler, slices and views the full compact observation.

For effects, one runtime slot must reconstruct two different catalog definitions in two worlds. Parameterize present selectors over fractional, negative, out-of-range, NaN, positive/negative infinity, and float32-inexact values; each must raise before gather. Repeat every value with `presence == 0` and require exact-zero rows with no exception or indexing. Cover a mixed present/absent batch. A present effect against an empty catalog must raise.

For `TokenSetQNetwork`, compare `_embed_tokens()` against projection of the per-type assembled fixed rows and assert its static buffers are absent from `state_dict()`. Test code may concatenate per-type outputs into a parity oracle; production code may not expose or allocate one full fixed observation tensor.

**Step 3: Verify RED**

Run:

```bash
uv run pytest \
  tests/test_townlet/unit/environment/test_token_publishers.py \
  tests/test_townlet/unit/agent/test_token_set_qnetwork.py \
  tests/test_townlet/integration/test_token_transfer_contract.py \
  tests/test_townlet/integration/test_substrate_observation_seam.py \
  -q
```

Expected: shape/scatter/projection failures show that publishers and token networks still read full rows.

**Step 4: Rewrite publishers in place**

`TokenObservationEncoder.encode()` allocates exactly `[batch, spec.total_dims]` and views each compact type block. Publishers write only lanes named by the compact layout:

- delete meter/affordance/variable static writes;
- delete fixed-rank padding writes;
- effect writes `context_index` plus live fields;
- variable publishers write presence plus normalized value lanes only;
- preserve current visibility and dynamic-slot overflow behavior.

There must not be a `FullTokenObservationEncoder`, `encode_full`, compression pass, or adapter that first builds the 4,090-float tensor.

**Step 5: Attach context only at the token-network boundary**

Implement `TokenInputAssembler` in `src/townlet/agent/token_input.py`. For one named type it views compact rows, starts from positional slot context or effect catalog context, scatters dynamic lanes, validates effect selectors, gates the whole fixed row by presence, and returns only `[batch, capacity, fixed_row_width]`, where `fixed_row_width == 1 + len(payload_features)`. `TokenSetQNetwork` owns this component, registers immutable tensors with `persistent=False`, immediately projects the returned type rows, and releases them before the next type. Presence remains output-side masking after projection.

Flat, dueling, RND, and current recurrent readers receive `spec.total_dims` directly. `NetworkFactory.token_block_slices()` walks compact row widths. Delete `RNDExploration.get_novelty_map()`'s retired 64-grid positional assumptions or rewrite it solely from the current compact spec; do not leave a hard-coded compatibility interpretation.

During this task, update `test_compact_token_layout.py` to import `TokenInputAssembler` only from `townlet.agent.token_input`; do not re-export it from `networks.py`.

**Step 6: Run the vertical tracer and live slice GREEN**

Run the command from Step 3, the vertical tracer command from Step 1, then:

```bash
uv run pytest tests/test_townlet/unit/universe/test_compact_token_layout.py -q
uv run pytest \
  tests/test_townlet/unit/agent \
  tests/test_townlet/unit/environment/test_token_publishers.py \
  tests/test_townlet/unit/environment/test_vectorized_env_level_metadata.py \
  tests/test_townlet/integration/test_token_set_runtime.py \
  -q
```

Expected: all selected tests pass; no model state dict contains compiled context.

**Definition of Done:**

- [ ] Environment output is compact on first allocation.
- [ ] Every token type has byte-exact fixed reconstruction parity.
- [ ] Visibility/presence cannot leak static context.
- [ ] Token projection widths and transfer keys are unchanged.
- [ ] Flat/dueling/current recurrent/RND have no full-row interpretation.
- [ ] No full-payload runtime tensor is built outside the token boundary.
- [ ] Production has no complete fixed-observation reconstruction callable; only per-type network assembly.

## Task 4: Make the artifact cut loud through replay and checkpoints

**Files:**

- Modify: `src/townlet/training/replay_buffer.py`
- Modify: `src/townlet/training/prioritized_replay_buffer.py`
- Modify: `src/townlet/training/sequential_replay_buffer.py`
- Modify: `src/townlet/population/vectorized.py`
- Modify: `src/townlet/training/checkpoint_utils.py`
- Modify: `tests/test_townlet/unit/training/test_replay_buffers.py`
- Modify: `tests/test_townlet/unit/training/test_prioritized_replay_buffer.py`
- Modify: `tests/test_townlet/unit/training/test_sequential_replay_buffer.py`
- Modify: `tests/test_townlet/unit/population/test_vectorized_population.py`
- Modify: `tests/test_townlet/integration/test_checkpointing.py`
- Modify: `tests/test_townlet/integration/test_live_inference_checkpoint_identity.py`
- Modify: `tests/test_townlet/integration/test_content_hash_checkpoint_guard.py`
- Modify: `tests/test_townlet/integration/test_reward_component_flow.py`
- Modify: `tests/test_townlet/unit/population/test_recurrent_training.py`
- Modify: `tests/test_townlet/integration/test_recurrent_bptt_runtime.py`
- Modify: `tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py`

**Step 1: Add failing exact-version and memory tests**

Pin these versions:

```python
assert CHECKPOINT_FORMAT_VERSION == 5
assert POPULATION_CHECKPOINT_FORMAT_VERSION == 4
assert replay.serialize()["format_version"] == 4
assert per.serialize()["format_version"] == 4
assert sequential.serialize()["format_version"] == 5
```

At capacity 100,000 and L1 width 115, assert the standard and PER observation pair tensors are explicitly `torch.float32`, have the exact shapes, and allocate exactly `92_000_000` bytes by both `numel() * element_size()` and paired tensor storage. Assert sequential episode observations use width 115. Feed every immediately previous version and assert refusal before any tensor/network/optimizer mutation.

**Step 2: Verify RED**

Run:

```bash
uv run pytest \
  tests/test_townlet/unit/training/test_replay_buffers.py \
  tests/test_townlet/unit/training/test_prioritized_replay_buffer.py \
  tests/test_townlet/unit/training/test_sequential_replay_buffer.py \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py \
  tests/test_townlet/unit/population/test_vectorized_population.py \
  tests/test_townlet/integration/test_checkpointing.py \
  -q
```

Expected: exact format-version assertions fail on 3/3/4/3/4 and old nested replay can still reach later state today.

**Step 3: Bump and validate exact formats**

- Replay `3 -> 4`.
- PER `3 -> 4`.
- Sequential replay `4 -> 5`.
- Population `3 -> 4`.
- Outer checkpoint `4 -> 5`.

Keep the current exact-version style. Validate the outer version, population version, nested replay kind/version, and current `obs_dim == token_spec.total_dims` before applying any network, optimizer, exploration, or replay state. Do not add migrations or old-key readers.

For each invalid population/nested replay kind/version/width case, snapshot the online network, target network, optimizer, scheduler, counters, replay, and exploration state. After refusal, assert each snapshot is byte-identical. Errors name the found value, exact expected value, and instruction to regenerate.

**Step 4: Run checkpoint/replay GREEN**

Run the command from Step 2, then:

```bash
uv run pytest \
  tests/test_townlet/integration/test_live_inference_checkpoint_identity.py \
  tests/test_townlet/integration/test_content_hash_checkpoint_guard.py \
  tests/test_townlet/integration/test_reward_component_flow.py \
  tests/test_townlet/unit/population/test_recurrent_training.py \
  tests/test_townlet/integration/test_recurrent_bptt_runtime.py \
  tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py \
  -q
```

Expected: all selected tests pass and every old artifact fails at its first applicable version gate.

**Definition of Done:**

- [ ] Standard, PER, and sequential replay store compact observations only.
- [ ] Actual L1 pair allocation is 92,000,000 bytes.
- [ ] Previous cache/checkpoint/replay versions all fail loudly.
- [ ] Population validates nested state before mutation.
- [ ] No migration, compatibility reader, or legacy key remains.

## Task 5: Prove the complete engineering acceptance surface

**Files:**

- Create: `tests/test_townlet/integration/test_compact_token_acceptance.py`
- Create: `tests/test_townlet/unit/universe/test_no_full_token_observation_abi.py`
- Create: `scripts/benchmark_compact_token_observation.py`
- Do not add a wall-clock assertion to the default correctness gate; record the measured performance command and result in product metrics.

**Step 1: Run the cross-substrate and architecture matrix**

Create these parameterized tests in `test_compact_token_acceptance.py`:

- `test_substrate_matrix`: `configs/default_curriculum` / `L1_full_observability`, `configs/differential/div003_cubic_partial` / `L2_partial_observability`, and `configs/aspatial_test` / `L0`; for each, compile, artifact round-trip, reset/step, compact/fixed widths, hashes, visibility/presence, exact per-type assembly parity, outer checkpoint round-trip, and old checkpoint refusal. Grid2D/Grid3D/aspatial share `token_type_schema_hash`; their rank-specific `layout_hash` values differ.
- `test_batch_256_architecture_matrix`: feedforward, dueling, token-set mean, token-set attention, and RND each execute forward, scalar loss, backward, optimizer step, and at least one changed parameter at batch 256.
- `test_batch_256_recurrent_bptt`: execute sequence length 4 as `[256,4,compact_dim]`, validity masks with at least one terminal boundary, hidden threading, `next_observations[:, -1, :]` bootstrap, backward, optimizer step, and at least one changed recurrent parameter.
- `test_replay_matrix`: standard, PER, and sequential replay each push/store, sample, serialize, exact-current reload, shape/dtype equality, and immediately-previous-version refusal.
- `test_multiworld_effect_context`: two worlds sharing one effect slot select different catalog definitions, including the present/absent selector matrix from Task 3.

Run:

```bash
uv run pytest tests/test_townlet/integration/test_compact_token_acceptance.py -q
```

Expected:

- one fixed token type-schema hash across substrate ranks;
- rank-specific compact layout hashes and widths;
- exact reconstruction parity;
- a real forward and optimizer step at batch 256 for every current architecture;
- for recurrent, a real `[256, sequence_length, compact_dim]` BPTT/update with masks, hidden threading, and boundary bootstrap, not 256 independent one-step forwards.

**Step 2: Build and smoke the reproducible encoding harness**

Implement `scripts/benchmark_compact_token_observation.py` with required CLI parameters `--config`, `--level`, `--agents`, `--seed`, `--warmup`, `--iterations`, and `--output`. It must:

- force CPU and `torch.set_num_threads(1)`;
- call `townlet.determinism.seed_all(args.seed)` before compilation/environment construction;
- compile with `use_cache=False`, build four worlds, reset once, and use one preallocated WAIT-action tensor;
- create the output parent with `Path(args.output).parent.mkdir(parents=True, exist_ok=True)` before writing JSON;
- run 20 untimed warm-up WAIT steps, resetting immediately when any world is done;
- measure 200 `_get_observations()` calls and 200 `env.step()` calls with `time.perf_counter_ns()`, resetting terminal worlds outside timed sections;
- report median nanoseconds per call for each operation and `encoding_ratio = median_observation_ns / median_step_ns`;
- emit JSON with Git commit, dirty flag, Python/Torch versions, CPU/platform, config, level, agents, seed, thread count, warm-up/iteration counts, numerator, denominator, and ratio.

Smoke the harness while implementation is still uncommitted:

```bash
uv run python scripts/benchmark_compact_token_observation.py \
  --config configs/default_curriculum \
  --level L1_full_observability \
  --agents 4 --seed 1337 --warmup 2 --iterations 2 \
  --output runs/benchmarks/m3-compact-encoding-smoke.json
```

Expected: valid JSON with the required provenance/measurement keys. This smoke is not acceptance evidence. The two 200-iteration acceptance runs occur from the clean pushed implementation SHA in Task 6.

**Step 3: Prove the complete fixed-observation ABI is absent**

`test_no_full_token_observation_abi.py` must:

- AST/rg-scan production references to `fixed_total_dims` and `fixed_row_layout` against an explicit allow-list limited to their artifact definitions and CLI reporting. `agent/token_input.py` is not allow-listed: per-type assembly needs only `fixed_row_width`;
- assert compiled-universe, environment, encoder, replay, population, and network objects expose no whole-observation `reconstruct`/`expand` callable;
- monkeypatch the tensor allocation functions used by the vertical tracer, execute compile -> reset/step -> replay -> flat forward -> token forward, and assert no allocation has trailing dimension `spec.fixed_total_dims`; per-type `[batch,capacity,fixed_row_width]` allocations are allowed.

Run:

```bash
uv run pytest tests/test_townlet/unit/universe/test_no_full_token_observation_abi.py -q
```

Expected: pass, with no production whole-observation expansion surface or 4,090-wide runtime allocation.

**Step 4: Run all project gates**

```bash
uv run ruff check
uv run black --check .
uv run mypy src
uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
uv run python scripts/validate_compiler_cli.py
uv run pytest
git diff --check
```

Expected: all commands exit 0; pytest has no failures. If the full suite exposes an in-scope defect, fix it now rather than file an observation.

**Step 5: Search for forbidden residue**

```bash
rg -n "static_signature|encode_full|full_payload|legacy.*token|migrate.*token|compat.*token" src tests docs/product
```

Expected: no executable legacy ABI, migration, fallback, or compatibility result. Historical PDR prose may name the deleted design only when clearly marked historical/superseded.

**Definition of Done:**

- [ ] L1 width/bytes, batch 256, and all substrates are evidenced; the acceptance harness is smoke-verified.
- [ ] All architecture readers execute the compact ABI.
- [ ] Full suite and static gates pass.
- [ ] Forbidden-residue search is adjudicated line by line.

## Task 6: Product checkpoint, tracker closure, commit, and push

**Files:**

- Create: `docs/product/decisions/0136-compact-token-transport-preserves-dynamic-effect-identity.md`
- Modify: `docs/product/current-state.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/product/metrics.md`

**Step 1: Commit and push only the verified implementation paths**

```bash
test "$(git branch --show-current)" = "project-recovery-3"
git status --short
git add \
  scripts/benchmark_compact_token_observation.py \
  src/townlet/agent/network_factory.py \
  src/townlet/agent/networks.py \
  src/townlet/agent/token_diagnostics.py \
  src/townlet/agent/token_input.py \
  src/townlet/environment/observation_encoder.py \
  src/townlet/environment/token_publishers.py \
  src/townlet/environment/vectorized_env.py \
  src/townlet/exploration/rnd.py \
  src/townlet/population/vectorized.py \
  src/townlet/training/checkpoint_utils.py \
  src/townlet/training/prioritized_replay_buffer.py \
  src/townlet/training/replay_buffer.py \
  src/townlet/training/sequential_replay_buffer.py \
  src/townlet/universe/__main__.py \
  src/townlet/universe/compiled.py \
  src/townlet/universe/compilers/metadata.py \
  src/townlet/universe/compilers/observation.py \
  src/townlet/universe/dto/token_spec.py \
  src/townlet/universe/token_hashes.py \
  tests/test_townlet/integration/test_checkpointing.py \
  tests/test_townlet/integration/test_compile_cache_level_identity.py \
  tests/test_townlet/integration/test_compact_token_acceptance.py \
  tests/test_townlet/integration/test_compact_token_runtime.py \
  tests/test_townlet/integration/test_content_hash_checkpoint_guard.py \
  tests/test_townlet/integration/test_effects_smoke.py \
  tests/test_townlet/integration/test_live_inference_checkpoint_identity.py \
  tests/test_townlet/integration/test_meter_bounds_runtime.py \
  tests/test_townlet/integration/test_reference_model_pack.py \
  tests/test_townlet/integration/test_reward_component_flow.py \
  tests/test_townlet/integration/test_recurrent_bptt_runtime.py \
  tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py \
  tests/test_townlet/integration/test_token_set_runtime.py \
  tests/test_townlet/integration/test_substrate_observation_seam.py \
  tests/test_townlet/integration/test_token_transfer_contract.py \
  tests/test_townlet/regressions/test_affordance_token_identity.py \
  tests/test_townlet/unit/agent/test_token_diagnostics.py \
  tests/test_townlet/unit/agent/test_network_factory.py \
  tests/test_townlet/unit/agent/test_networks.py \
  tests/test_townlet/unit/agent/test_token_set_qnetwork.py \
  tests/test_townlet/unit/universe/test_no_full_token_observation_abi.py \
  tests/test_townlet/unit/environment/test_token_publishers.py \
  tests/test_townlet/unit/environment/test_vectorized_env.py \
  tests/test_townlet/unit/environment/test_vectorized_env_level_metadata.py \
  tests/test_townlet/unit/population/test_vectorized_population.py \
  tests/test_townlet/unit/population/test_recurrent_training.py \
  tests/test_townlet/unit/substrate/test_observation_shape_contract.py \
  tests/test_townlet/unit/training/test_prioritized_replay_buffer.py \
  tests/test_townlet/unit/training/test_replay_buffers.py \
  tests/test_townlet/unit/training/test_sequential_replay_buffer.py \
  tests/test_townlet/unit/training/test_token_checkpoint_gates.py \
  tests/test_townlet/unit/universe/test_compact_token_layout.py \
  tests/test_townlet/unit/universe/test_compiled_token_coherence.py \
  tests/test_townlet/unit/universe/test_compiled_universe.py \
  tests/test_townlet/unit/universe/test_compiler_cache.py \
  tests/test_townlet/unit/universe/test_token_emission.py \
  tests/test_townlet/unit/universe/test_token_numeric_contract.py \
  tests/test_townlet/unit/universe/test_token_spec.py
git commit -m "fix(tokens): cut replay to compact dynamic state"
git push origin project-recovery-3
```

Record the exact pushed implementation hash; the product checkpoint and tracker evidence cite it.

Verify the benchmark will run against an exact clean remote commit:

```bash
M3_IMPL_SHA=$(git rev-parse HEAD)
test -z "$(git status --porcelain)"
test "${M3_IMPL_SHA}" = "$(git rev-parse origin/project-recovery-3)"
```

**Step 2: Measure encoding twice at the exact clean implementation SHA**

Run in two fresh processes. The `runs/` outputs are ignored, so the second process still observes a clean worktree at the same SHA:

```bash
uv run python scripts/benchmark_compact_token_observation.py \
  --config configs/default_curriculum \
  --level L1_full_observability \
  --agents 4 --seed 1337 --warmup 20 --iterations 200 \
  --output runs/benchmarks/m3-compact-encoding-1.json
uv run python scripts/benchmark_compact_token_observation.py \
  --config configs/default_curriculum \
  --level L1_full_observability \
  --agents 4 --seed 1337 --warmup 20 --iterations 200 \
  --output runs/benchmarks/m3-compact-encoding-2.json
```

For both JSON payloads, assert `commit == M3_IMPL_SHA`, `dirty == false`, `level == "L1_full_observability"`, `iterations == 200`, and `encoding_ratio < 0.25`. If either run fails, do not average it away: change the implementation, rerun the affected gates, create and push a new implementation commit, verify clean local/remote SHA equality, and repeat both fresh-process benchmarks.

**Step 3: Record the representation clarification and refresh product state**

Create PDR-0136 only now, after both clean-SHA benchmark runs. It must state:

- current L1 is 115, while 118 remains the one-scalar target;
- variable coordinates are compiled immutable element context;
- effect `context_index` is required transport metadata because slot identity varies by world;
- `TokenSpec.total_dims` is the compact ABI and fixed expansion is network-internal;
- the fixed transfer schema/hash remains unchanged;
- all previous artifacts are deliberately unsupported.

Rewrite `current-state.md` to make M3 complete and M4 next. Refresh roadmap and metrics with exact width, actual pair bytes, test counts, batch result, encoding ratios, artifact versions, commit, and remaining risk. Embed both complete benchmark JSON payloads verbatim in `docs/product/metrics.md` so the evidence remains committed even though `runs/` is ignored. Record `max(run1.encoding_ratio, run2.encoding_ratio)` as the accepted reading. Do not claim M4's 79.19 IQM regression work has run.

Commit and push the product checkpoint separately:

```bash
test "$(git branch --show-current)" = "project-recovery-3"
git add \
  docs/product/decisions/0136-compact-token-transport-preserves-dynamic-effect-identity.md \
  docs/product/current-state.md \
  docs/product/roadmap.md \
  docs/product/metrics.md
git commit -m "docs(product): accept compact token replay milestone"
git push origin project-recovery-3
```

Record the exact pushed product-checkpoint hash.

**Step 4: Add Filigree evidence and close M3**

```bash
M3_IMPL_SHA=$(git rev-parse HEAD^)
M3_PRODUCT_SHA=$(git rev-parse HEAD)
filigree --actor codex add-comment --expected-assignee codex hamlet-1b1caf552a \
  "M3 accepted. implementation=${M3_IMPL_SHA}; product-checkpoint=${M3_PRODUCT_SHA}. L1 compact width=115, observation-pair bytes=92000000, cap<=120; Grid2D/Grid3D/aspatial, batch-256 architecture/recurrent BPTT, replay/checkpoint refusal, full project gates, and two fresh-process encoding runs passed. Exact commands, test counts, ratios, and benchmark JSON are recorded in docs/product/metrics.md at ${M3_PRODUCT_SHA}."
filigree --actor codex close --expected-assignee codex \
  --commit "project-recovery-3@${M3_IMPL_SHA}" hamlet-1b1caf552a
```

The evidence names both exact remote hashes and points to the committed exact commands/results. If the CLI syntax has drifted, inspect `filigree add-comment --help` / `filigree close --help`; do not guess. Confirm the issue is terminal before starting M4.

**Step 5: Start M4 only after the checkpoint is remote**

```bash
filigree --actor codex start-work hamlet-25fc3fb955
```

Expected: M3 terminal, remote contains both commits, worktree clean, M4 in its working status.

**Definition of Done:**

- [ ] M3 acceptance evidence is exact and tracker-visible.
- [ ] Product state names M4 as next without claiming it complete.
- [ ] Representation clarification is captured in PDR-0136.
- [ ] Implementation and product checkpoint commits are pushed.
- [ ] Worktree is clean and M4 is atomically started.

## Recovery and rollback posture

This is an intentional one-way artifact cut. Runtime rollback, migration, and dual readers are prohibited. Before the final push, development rollback is ordinary Git revert. After all planned commits exist, revert newest-first: product checkpoint, implementation, then RED contract/plan; regenerate local caches afterward. Do not leave new tests or product state against reverted code. After acceptance, old checkpoints are not product data because the project has zero users and no release. Any failure to preserve visibility, transfer, or the byte cap stops M3 and selects one different ABI rather than retaining both.
