# T18e factory grid builtin-read purity

Finite read-only source qualification, 2026-11-10, against coordinator-supplied frozen fullsuite30a802a9 (`30a802a996fe8bf7cd63e53d211fa8b2cd028f77`); commit identity was not queried. The public T18e-SUCCESSOR-EQUALITY-API.md and T18e-PHASE-CLOCK-RECONCILIATION.md are requirements, not additional inspected implementation. Repository AGENTS.md was read. This designated ignored capsule is the only write. No code/test/index/tracked-document writes, imports, simulator execution, runtime probes, compilation, tests, git operations, branches/worktrees/checkouts, source copies or subagents occurred.

## Inventory and ruling

Metadata preceded implementation bodies. Exactly five whole source charges, 1970 <= 5000 lines, all under `src/townlet/substrate/`. No sixth implementation/helper/test body was read.

| Source | Lines | SHA256 |
|---|---:|---|
| base.py |365|36f6bdddac815689993fe7cc94780bd69b3f229e07d623bf65936cc3460d7931|
| factory.py |145|f537479e40e068da399b800d5574bec1f10cfd076e6f18953f3f6c731347a366|
| grid2d.py |473|d17bcd2870be1168ce27aa23f153fdf1b97134e0d6e0b124135557dce696475b|
| grid3d.py |489|9ad6173a3259ddbd41fddd221052575b2b9b967e8150196d6c137f157e4cd714|
| gridnd.py |498|bba779335e80d78e14c6beadc3d407ab3bfd5a1d0b021c06f5ff4ac6d4323631|

**Qualified by source:** factory-selected builtin Grid2DSubstrate, Grid3DSubstrate and GridNDSubstrate `position_dim`, `normalize_positions`, `egocentric_delta` and `visible`, including every actually called project helper, are deterministic nonmutating reads at fixed ordinary builtin configuration and finite supported tensor inputs on the same device. They read no RNG, wall/episode time, done/activity state, ENV, scheduler, registry or item manager. No read caches or lazy state are installed. No unresolved project-helper body remains in this grid read graph.

This closes the grid portion of the named builtin-read source prerequisite. It does not close other substrate branches, item/schema/registry helpers, callback nonmutation, executable full-batch equality, T18e, or global acceptance. It establishes source behavior, not results of unrun tests, cross-device equality, GPU determinism or raw-byte identity.

## Exact factory and geometry mapping

Factory.build23–71 maps `config.type == 'grid'` plus `config.grid.topology == 'square'` to Grid2DSubstrate, forwarding width, height, boundary, distance_metric, topology and diagonals. `topology == 'cubic'` selects Grid3DSubstrate with the same fields plus depth. Thus `type='grid'` does not itself fix dimensionality to two. Factory120–128 maps `type='gridnd'` to GridNDSubstrate, forwarding `config.gridnd.dimension_sizes`, boundary, distance_metric and topology. Factory's `device` is not used by these constructors; operation input devices determine output placement. The continuous, continuousnd and aspatial branches belong to the separate owner.

| Selected builtin | Dimensions / geometric capacity | Read configuration |
|---|---|---|
| Grid2D | constant position_dim2 (74–77); positive width,height; get_capacity467–469 is width*height | axis sizes [width,height], boundary, distance_metric |
| Grid3D | class position_dim3 (40); positive width,height,depth; get_capacity455–457 is their product | axis sizes [width,height,depth], boundary, distance_metric |
| GridND | len(dimension_sizes) (96–99), constructor requires 4..100 axes, each size>0; get_capacity481–495 multiplies sizes | dimension_sizes, boundary, distance_metric |

All positions use grid integer coordinates (`torch.long` declarations: 2D79–82, 3D41, ND101–104); read arithmetic converts to float32. Unit axes are allowed. Each axis normalization divisor is max(size-1,1), so no division by zero for size1. In-bounds unit-axis coordinates normalize to zero. Topology and diagonal settings affect selection/action configuration but are not consumed by these four read operations. Constructors check positive sizes, permitted boundary and metric (2D58–72, 3D63–76, ND59–94); topology is stored without an additional constructor membership check. The factory supplies square/cubic for those selected branches; ND simply forwards its topology. Constructor signatures/annotations are not a substitute for the unopened DTO's validation rules.

The separate notion of **positive token capacity** comes from the public equality capsule: ENC36–116 installs publishers only for positive compiled capacity. Its publisher mapping is authoritative documentary evidence here: self PUB417–449 uses position_dim/normalization; affordance PUB528–598 uses normalization/delta/visibility; agent PUB601–654 and item PUB657–715 use spatial geometry/visibility when their slots are supplied. ENV's ordinary agent slots are None per that capsule; no claim of a live agent-token witness follows from positive agent capacity alone. Effect, meter and registry variable-element publishers do not add a grid read dependency in the public audit. Require positive compiled capacities and populated slots for self/affordance/item geometry witnesses, and positive meter/effect/variable-element capacities for the complete existing equality gate. Geometric get_capacity is not a token-capacity selector. Exact DTO/compiler construction of a full ENV fixture is outside this five-source qualification; no new config key is asserted.

## Complete called read graph

| Member | 2D | 3D | ND | Behavior |
|---|---|---|---|---|
| position_dim |74–77|40|96–99| constant2/3 or list length; no write |
| normalize_positions |416–429|435–444|340–349| calls own _encode_relative with fresh empty dict |
| _encode_relative |308–329|322–344|303–313| allocates fresh float32 [N,D] zeros on positions.device, fills only fresh columns with positions.float()/max(size-1,1) |
| _token_vision_radius |382–385|397–400|358–360| max(1,ceil(vision_range*max(axis_sizes)/2)); ordinary math.ceil/int/max |
| _token_axis_sizes |389–390|404–405|355–356| creates fresh float32 sizes tensor on requested device |
| visible |392–401|407–416|362–371| validates shapes; None returns fresh all-True bool [N,M]; otherwise computes declared-metric distance <= radius |
| egocentric_delta |403–414|418–433|373–384| validates shapes; computes signed pairwise delta and divides by fresh per-axis divisors |

The common helpers are fully inside base.py:

- require_position_batch51–54 checks rank2 and exact trailing width D; require_entity_batch57–69 accepts shared [M,D] or per-observer [N,M,D] with matching N,D, returns M. Only metadata is read.
- pairwise_axis_deltas12–35 casts entity/observer tensors to float32, unsqueezes shared entities, subtracts observer positions to allocate [N,M,D]. For wrap, sizes are cast to float32 on delta device and `remainder(delta+extent/2,extent)-extent/2` selects shortest signed displacement. Exactly half an even extent maps to negative half. Casts/unsqueeze may alias inputs but no aliased tensor is written.
- combine_metric38–48 reduces absolute deltas with sum for manhattan, sqrt(sum(square)) for euclidean, max for chebyshev (zero-width special case sums). Only results/local tensors are produced.

Only wrap changes distance/deltas. Clamp/bounce/sticky have identical read formulas at equal current positions; their movement algorithms are not called. Full visibility validates shapes then returns ones before radius, metric or pairwise arithmetic. Normalization does not call movement, initialize_positions, compute_distance, action constructors or the older scaled/absolute encoding helpers. ActionConfig imports introduce no runtime read helper call on this graph. No project helper outside these five bodies is essential.

In-place assignments in _encode_relative write fresh zeros only. Input tensors, self fields, config and RNG are not assigned. Repeated valid calls therefore produce equal mathematical values, shapes/dtypes/devices without depending on earlier read count. Output identity is not promised; numerical helper outputs are newly computed. Finite inputs/config, same fixed builtin instance, stable input contents and no concurrent mutation are required just as in the accepted equality proof.

## Current refusals and limits

Factory47/121 assert the selected subconfig is not None. Cubic without depth raises ValueError59–60; unrecognized grid topology70–71 and unknown substrate type144–145 raise ValueError. Positive-grid-dimension, unknown boundary and metric violations raise ValueError in the constructors at the lines above. ND fewer than4 or more than100 axes raises ValueError61–67; ND>=10 warns before later size/boundary/metric checks (70–76). These construction warnings/writes to object fields are not observations at fixed constructed state.

visible/egocentric_delta explicitly raise ValueError from base51–69 for malformed observer/entity shape, including mismatched per-observer batch. This also applies to visible(None). They do not validate value bounds, finiteness, device agreement or vision fraction domain. Finite negative vision fractions saturate radius to1; NaN reaches math.ceil and raises ValueError; infinite radius arithmetic reaches ceil with OverflowError for infinity under ordinary Python behavior. Backend dtype/device/allocation errors remain ordinary Torch errors. No exception mutation path was found in these helpers.

normalize_positions has **no exact rank/width validator**. Too few columns/nonindexable shapes can raise indexing/backend errors; surplus columns may be ignored. No global assertion that every malformed input fails, or that arbitrary input values normalize into [0,1], is warranted. Similarly delta [-1,1] assumes in-bounds grid positions; reads do not clamp invalid positions. None visibility can succeed without inspecting numeric positions or metric.

ND91 retains dimension_sizes by reference, and its property reads current length: configuration ownership/immutability is not enforced by this class. Mutation between calls could alter dimensions, divisors, radius and capacity. That is an actual alias boundary requiring the already-stated fixed-state/no-config-mutation premise, not a stateful read or an observed intervening writer. 2D/3D scalar fields and class attributes are likewise mutable Python state. No purity certification covers arbitrary injected subclasses, replaced methods, custom tensor/config types, autograd hook behavior or concurrent callers mutating inputs.

Refuted within this grid graph: hidden hour/done/pending-work dependence; read-time RNG consumption; initialization randomness being implicitly called on normalization/visibility; topology/diagonal flags changing these read values at otherwise identical geometry; need for another unopened project helper to qualify these reads. Random torch.randint initialization exists at 2D84–92, 3D87–96, ND123–135 but is unreachable from the four inspected read members. This is not a claim the complete substrate lifecycle is RNG-free.

## Finite actual equality witnesses for later authorized execution

None executed. These are factory field/value selections and concrete in-bounds input witnesses, not invented complete DTO documents or an independently built encoder. The fixture owner must compile their actual current DTO and retain actual ENV/RWC encodes. Use CPU, N>=2, positive compiled geometry capacities and nonempty item/affordance slots as above; include shared and per-observer entity layouts. Compare repeated helper values plus actual reward-boundary and final returned full token tensors with torch.equal and matching shape/dtype/device, while snapshotting simulator/config/input/RNG state. Preserve independently allocated encoder output checks from the public requirement.

1. Square: type grid; grid topology square; width8,height6; diagonals both authored settings. Cubic: type grid; grid topology cubic; width8,height6,depth4; diagonals both settings. ND: type gridnd; dimension_sizes [8,6,4,1], topology hypercube. For each of these three selections run the finite cross-product of boundary {clamp,wrap,bounce,sticky}, metric {manhattan,euclidean,chebyshev}, vision {None,0.25}: 72 geometry cases (plus the square/cubic diagonal companion runs). This covers every read formula branch, not every imaginable configuration.
2. Observer row zero; entity A has first coordinate7 and other coordinates0, entity B first coordinate4 and others0. For longest extent8, vision0.25 gives radius1. A is visible only under wrap (distance1 rather than7 for every metric); its x delta is -1/7 under wrap versus1 otherwise. B's wrap tie is -4/7 versus +4/7, checking sign rather than visibility alone. Normalize A x=1. In cubic/ND add axis-specific entities [0,5,0,...] and [0,0,3,...] to discriminate width/height/depth denominators and toroidal extents.
3. In each class at clamp, vision0.25, entity [1,1,0,...] has distance2/sqrt(2)/1 under manhattan/euclidean/chebyshev: hidden/hidden/visible. With vision0.5 radius2, entity [2,1,0,...] is hidden/hidden/visible; entity [1,1,1] in 3D/ND at radius2 is hidden/visible/visible. These detect metric conflation instead of merely exercising equal output cases.
4. Unit-axis companions square [1,6], cubic [1,6,4], ND [1,6,4,1] retain positive geometric capacity6/24/24 and zero valid unit coordinates; assert finite zero normalized/delta lanes. ND dimension companions of four, ten and100 axes with positive sizes and at least one nonunit axis exercise variable width and >=10 constructor warning without enumeration. Validation controls use actual malformed rank/width/per-observer N and nonpositive sizes, not a replaced helper.
5. On the actual populated ENV witnesses retain the public retirement, authored termination, coincidence, subsequent inactive step, real hour rollover/exposed tick and temporal expression, active observable effect plus genuinely removed pending agent work, carried/hidden items and partial/full vision controls. This grid audit adds no new temporal/done inputs and supplies no unequal successor counterexample. Preserve five provider families/both scopes and the callback nonmutation requirement from the accepted public design; their implementations are not inspected here.

No further grid source boundary is needed. Other builtin branches and item/schema/registry/callback owner reports remain separate finite prerequisites already named in the public documents. Executable witnesses and original acceptance remain open.
