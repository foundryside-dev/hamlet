# Initial participation: continuous/aspatial action-mask geometry facts

Finite read-only source qualification, 2026-11-11, for the approved BAC required-C preparation question at coordinator-supplied HEAD `d4426803` (identity not queried). Repository AGENTS.md was read. Only this designated ignored prose capsule was written. No source/test/runtime/import/probe/reflection/compile/lint/git/index/branch/worktree/checkout/source-copy/new-agent action was performed. This answers the actual factory-selected continuous/aspatial `is_on_position` dependency of affordance mask rows, not whole-C qualification or integration acceptance.

## Attributed documentary inputs

Read `T18e-INITIAL-PARTICIPATION-MASK-OWNER-FACTS.md`, SHA256 `5559dec45a7864e49aae9aa9a39ed24457cfcf95fe63759d069d5504fd187ea4`, and `T18e-CONTINUOUS-READ-PURITY.md`, SHA256 `0ee0569f80646b84bd03620c6819ae5ccf1e2028c1c1e3245528781f32b5e854`. Their ENV/builder and historical observation-read findings are attributed prose, not implementation bodies opened here. In particular the owner capsule supplies the actual builder call `substrate.is_on_position(positions, affordance_pos)`, temporal-open handling, and final `action_masks[dones] = False`. Historical token visibility/normalization qualification does not itself certify this distinct proximity call.

## Exact source inventory

SHA256 and whole-file line count were obtained before any implementation body was opened. Exactly these five distinct complete bodies were read, totaling 1843 lines. An aggregate tool response truncated its display; the already-counted continuous, factory, and continuousnd bodies were subsequently read individually to obtain their complete display. No sixth body, helper expansion, source copy, or excerpt substitution was used.

| Source relative to `/workspace/hamlet` | Whole lines | SHA256 |
|---|---:|---|
| `src/townlet/substrate/base.py` | 365 | `36f6bdddac815689993fe7cc94780bd69b3f229e07d623bf65936cc3460d7931` |
| `src/townlet/substrate/factory.py` | 145 | `f537479e40e068da399b800d5574bec1f10cfd076e6f18953f3f6c731347a366` |
| `src/townlet/substrate/continuous.py` | 735 | `d5bd3818d5e208bef26ed3c47ae28cecb7f9631b630900f568d3c53b1bf19578` |
| `src/townlet/substrate/continuousnd.py` | 458 | `57fe724555f4c2786f27de8cd6b6e58482291cc8fb6bc5bf01e7e3c1586f3f86` |
| `src/townlet/substrate/aspatial.py` | 140 | `f6040932c30a6a0c5edd0272c89456eace04d4317514213885ea847477521315` |

## Factory-selected implementation and exact call graph

`SubstrateFactory.build` selects Continuous1D/2D/3D for `config.type == 'continuous'` and `config.continuous.dimensions` 1/2/3. Each subclass inherits both `is_on_position` and `compute_distance` from `ContinuousSubstrate`; none overrides them. Factory forwards the configured `interaction_radius` and `distance_metric`, as well as bounds/boundary/movement/action discretization. `continuousnd` selects `ContinuousNDSubstrate` using `config.continuous` bounds/radius/metric; its dimension is bounds length (constructor admits 4 through 100). `aspatial` selects `AspatialSubstrate()` with no spatial config. Factory's device parameter does not set instance tensor device.

The complete named graph is:

- Continuous1D/2D/3D: inherited `ContinuousSubstrate.is_on_position` -> same-class `compute_distance` -> ordinary Torch arithmetic/reductions -> distance comparison.
- ContinuousND: `ContinuousNDSubstrate.is_on_position` -> same-class `compute_distance` -> ordinary Torch arithmetic/reductions -> distance comparison. Its only extra operation is a local `target_position.unsqueeze(0)` when the target is rank one; this rebinds a local variable and does not write target storage.
- Aspatial: `AspatialSubstrate.is_on_position` -> `agent_positions.shape[0]`, `.device`, and `torch.ones`.

No project helper outside the five-body inventory is essential to this graph. Base defines the abstract `[N,D]`, target `[D]`, bool `[N]` interface, but the concrete methods do not call base validators, `pairwise_axis_deltas`, `combine_metric`, token visibility/delta methods, or any external project callback. `ActionConfig`, config DTO validation, constructor `model_dump`, default-action caches, movement, and initialization are not executed by these mask proximity reads.

## Threshold, broadcasting, and result contract

For both spatial continuous families, let `delta = agent_positions - target_position`, with D coordinates. Distance is exactly one configured metric:

- Euclidean: `sqrt(sum(delta ** 2, dim=-1))`.
- Manhattan: `abs(delta).sum(dim=-1)`.
- Chebyshev: `abs(delta).max(dim=-1)[0]`.

`is_on_position` returns `distance <= self.interaction_radius`. Equality at the threshold is included; the radius is neither rounded nor scaled by bounds, movement delta, or vision range. **Boundary mode, including wrap, does not alter this distance.** There is no toroidal seam adjustment in this graph. This documents current semantics without proposing a geometry change.

For supported ordinary tensors `agent_positions [N,D]` and one affordance target `[D]` on the same device, subtraction broadcasts the target across N rows, reduction removes only D, and comparison creates a fresh bool `[N]` result on the arithmetic device (the input positions device). `[1,D]` also broadcasts; `[N,D]` gives rowwise targets under ordinary broadcasting. These incidental additional shapes are not required by the one-affordance builder contract. Arbitrary other ranks/shapes are not validated here and can broadcast to another shape or fail; no universal bool `[N]` promise follows for malformed inputs. ND's explicit rank-one unsqueeze makes the supported single-target case `[1,D]` before subtraction. D is positive in both spatial families, so supported Chebyshev reduction has a nonempty coordinate dimension.

Aspatial's supported positions are `[N,0]`, with zero-width target `[0]`. It ignores target entirely and allocates fresh `torch.ones(N, dtype=torch.bool, device=agent_positions.device)`: all rows true, including an empty bool `[0]` batch when N is zero. It performs no target shape/device/finiteness validation; that does not certify malformed input support. No input tensor or preexisting output storage is returned as a result alias in any of the three implementations.

## Bounded purity verdict and mutable dependencies

CONFIRMED by source: at fixed supported builtin configuration and finite valid position/affordance tensors with supported ordinary same-device arithmetic, these factory-selected `is_on_position` implementations are deterministic, nonmutating, RNG-free reads. The spatial graph reads only its two supplied tensors, `self.distance_metric`, and `self.interaction_radius`; Aspatial reads only the positions batch count/device. There is no random draw, state/attribute/cache assignment, in-place input write, physical movement, wall-clock/hour/VFS/history/episode/done read, or registry/item/ENV callback. Tensor arithmetic, local unsqueeze, reductions, comparisons, and allocation form the Torch library boundary.

Spatial metric/radius attributes are ordinary mutable instance fields. Supported constructor configuration validates the three metric names and positive radius; constructor bounds/movement checks and construction-time warnings are not part of this read. External mutation or concurrent writes can change results, and the methods enforce no lock or snapshot. Bounds lists may be mutable, but neither bounds nor boundary nor movement_delta nor dimensions nor action discretization is read by the proximity graph itself. Actual tensor coordinate width is consequently an owner input invariant, not a concrete-method validation guarantee.

No explicit finite validation or dtype conversion occurs here. Ordinary supported floating tensor arithmetic must be used; finite values alone do not preclude intermediate overflow or establish an arbitrary dtype's meaningful metric arithmetic. No arbitrary Tensor subclass/custom config object, injected method/subclass, mutation racing the call, mixed-device support, CPU/GPU byte identity, or universal Torch backend determinism claim is made. This is static source evidence; no runtime/test witness was executed.

## Consequence for one prepublication legal-mask capture

For these selected builtin substrate paths, the actual affordance proximity calls may be completed during one genuine full legal-mask build before status publication without introducing hidden substrate physics writes, RNG consumption, or lazy cache changes. At the same retained positions/targets/metric/radius, repeating just these calls produces the same logical rows. The owner capsule's existing builder final done-row clearing permits deriving an independently owned candidate mask from a genuinely captured all-active mask by clearing retired rows, provided its full unchanged-dependency and ownership premises hold. Nothing here calls for a second builder invocation after publication or an action selection to obtain legality.

This closes only the continuous/aspatial `is_on_position` source-purity owner question. Full-build purity still needs the independent owners identified in the attributed mask capsule: fresh/nonaliased action-space base-mask ownership and accessor purity; actual item `world_of_agent`/`items_at` and custom-mask writes/callback/RNG facts; temporal gate read purity; plus ENV guard/freshness discipline for mutable state. Grid proximity belongs to its separate owner. No additional essential external body remains for the named continuous/aspatial proximity graph; the listed full-builder duties are separate dependencies, not a reason to open a sixth body here. All real build/callback execution, cloning, validation and allocations must finish before publication under the owner's operation guard. Full-C acceptance, implementation, integrated mask equality, and postpublication recoverability remain outside this capsule.
