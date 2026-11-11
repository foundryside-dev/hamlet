# T18e existing replay batch API facts

Read-only extraction for the parent regression. No source/test/index/tracked-document changes, imports, runtime probes, compilation, or tests. Tests unrun. Only the three assigned source bodies were inspected (1,162 unique source lines); repository AGENTS.md was read for instructions. No fourth source body, POP/helper/test bodies, or history was consulted.

## Frozen source evidence

Metadata was collected before source reads. SHA-256 and line counts:

| Source | Lines | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `src/townlet/training/replay_buffer.py` | 677 | 33669 | `d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8` |
| `src/townlet/training/replay_contract.py` | 222 | 10583 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| `src/townlet/training/state.py` | 263 | 9678 | `a6f22b0b26ca6422e6a0710f9268386e8d2b7162e1a5e9a43a2decdea4c9d3e3` |

## Exact public return and accessors

`ReplayBuffer.sample_batch(self, request: ReplayRequest) -> UniformReplayBatch` is the exact signature (`replay_buffer.py:356`). It calls readiness and raises ValueError if unavailable, samples indices, and returns the DTO at lines 357–398. `UniformReplayBatch` subclasses `ReplayBatch` (48–58).

All following names are direct dataclass attributes, not getter methods:

| Sample attribute | Uniform sample shape/dtype | Meaning |
| --- | --- | --- |
| `rewards` | `[B]`, float32 | Stored authoritative total; there is no batch `total` attribute |
| `rewards_extrinsic` | `None` or `[B]`, float32 | Independent extrinsic component |
| `rewards_intrinsic` | `None` or `[B]`, float32 | Independent intrinsic component |
| `rewards_shaping` | `None` or `[B]`, float32 | Independent shaping component |
| `rewards_extrinsic_present` | `[B]`, bool | Per-row extrinsic presence |
| `rewards_intrinsic_present` | `[B]`, bool | Per-row intrinsic presence |
| `rewards_shaping_present` | `[B]`, bool | Per-row shaping presence |
| `observations`, `next_observations` | `[B,D]`, float32 | Current and actual stored successor observations |
| `actions` | `[B]`, int64 | Stored selected action |
| `dones`, `legality_recorded`, `loss_mask` | `[B]`, bool | Terminal status, captured successor legality, selected loss rows |
| `next_action_masks` | `[B,A]`, bool; A > 0 | Stored successor action sets |
| `lengths` | `[B]`, int64, all one | One transition per unit |
| `unit_ids` | `[B]`, int64 | Selected live storage indices |
| `weights` | `[B]`, float64, all one | Unit weights |
| `sampling` | `SamplingReceipt` | Owned proposal evidence |

`B=request.batch_size`. All tensor attributes share the observations device. Base fields/validation are `replay_contract.py:127–222`; uniform shape/presence validation is `replay_buffer.py:48–75`; actual population of attributes is 373–398. Real observations/rewards/components must be finite. Nonterminal successor masks require at least one legal action; terminal masks may be empty (`replay_contract.py:33–43`). A uniform sample has all loss masks true, all lengths one, and all real legality flags true.

## Actual optional semantics and ownership

For each component, sampling tests only the selected rows' presence flags. If none is present, the returned component is `None`; if any is present, the returned component is a full `[B]` tensor with zero placeholders for missing rows (`replay_buffer.py:373–380`, 48–75). Thus all-false presence can produce `None` even when other unsampled buffer rows contain that component. True plus numeric zero is a recorded zero; false means missing, independent of placeholder value. Presence never recomposes total or changes loss.

Push stores `RewardTensor.total` directly as `rewards`, and each optional component separately; missing components receive zero storage placeholders with false presence flags (271–287). Producer tensors are detached, moved, and cloned on insertion (285–287). `ReplayBatch` clones every tensor field and copies its sampling receipt (contract:218–222), and UniformReplayBatch clones flags again (buffer:75). Frozen fields prevent rebinding, but consumers can still mutate their owned tensors and must not mutate them during learner use (contract:1–7).

`RewardTensor` uses `total`, `extrinsic`, `intrinsic`, `shaping`, `is_composed` slots (`state.py:38–84`). Constructor components default to None; `from_dac` preserves the provided total and optional components and sets `is_composed=True` (86–110). Neither constructor composes rewards nor clones/validates tensors. Replay insertion never uses `is_composed` to recalculate total.

## Provenance and genuine post-capture comparison

`unit_ids` equals the sampled indices, and `sampling.indices` contains their CPU NumPy int64 copy in the same order (buffer:362–395). Receipt arrays are copied and made nonwriteable (contract:88–124). Receipt fields are exactly `indices`, `weights`, `population_size`, `conditional_draw_probabilities`, `mode`, `objective_unit`, `weight_rule`. Uniform values are population `self.size`, probabilities `1/(self.size-arange(B))`, requested mode, `transition`, `unit_weights` (buffer:363–372).

These IDs identify live storage slots for that snapshot, not durable transition identities across overwrites. No additional persistent provenance accessor exists on these DTOs. Serialization returns chronological rows and can reorder a wrapped ring (423–450), so do not assume its row offsets equal live `unit_ids` after wrapping.

After the parent's genuine canonical capture inserts actual transitions into its real ReplayBuffer, a genuine `sample_batch(request)` exposes both captured total and components in one aligned sample. Compare `batch.rewards` directly with the independently retained expected composed totals for the selected captured rows; compare each non-None `batch.rewards_*` independently with its expected captured component and assert its corresponding presence flags. Do not derive expected total by adding returned components. Resolve random sample order using the receipt/live-slot correspondence for that captured snapshot or the parent's existing explicit row identity. When a component is expected wholly absent in the sampled rows, assert None plus all-false presence; for present zero, assert the tensor value zero plus true presence. This uses the actual sampler and stored canonical capture without a fake buffer or recomposition. Exact parent row identity, capture geometry, values, and fixture setup are outside these three sources and are supplied by the parent.

## Existing insertion requirements

`push_recorded(self, observations: torch.Tensor, actions: torch.Tensor, rewards: RewardTensor, next_observations: torch.Tensor, dones: torch.Tensor, next_action_masks: torch.Tensor) -> None` accepts independent optional components (buffer:234–247). Both insertion routes validate observations/next observations float32 `[B,D]`, actions int64 `[B]`, total float32 `[B]`, dones bool `[B]`; every supplied component must be finite float32 `[B]` (174–214). It does not require any component to be supplied and does not demand total equal their sum. `push_recorded` requires actual bool successor masks `[B,A]`, consistent width, legal nonterminal successors, and action vocabulary membership (234–268). Plain `push` is the unconstrained adapter and can declare all actions legal after action width exists (216–232); it is not a substitute for genuine constrained capture.

No additional producer-specific component requirement, actual capture contents, durable transition identifier, or parent fixture behavior can be established from the assigned three sources. No new API or behavior is proposed here.
