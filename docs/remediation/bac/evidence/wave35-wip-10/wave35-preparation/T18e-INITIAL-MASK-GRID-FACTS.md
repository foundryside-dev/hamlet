# Initial participation: named grid action-mask geometry facts

Read-only source qualification, 2026-11-11. Coordinator supplied worktree /workspace/hamlet and HEAD d4426803; no git identity query was run. AGENTS.md was read. Scope is only factory-selected builtin grid `is_on_position(positions, affordance_pos)` for approved required-C pre-first-step participation. Existing builder call is a supplied/public fact, not another inspected body. The older observation geometry proof names different methods and was not substituted for this graph.

Only this designated ignored prose capsule was written. No source/test/tracked-document edits, imports, simulator/runtime probes, tests, compilation, reflection, alias exploration, git/index/branch/worktree/checkout actions, source copies or new agents. Repository tracker/index workflows were not invoked because this finite task forbids those actions. Two supplied preparation capsules and AGENTS.md were consulted as prose. Exactly five distinct whole implementation bodies, total 1970 lines, were read; SHA256 and line counts were obtained BEFORE any body. A combined output was truncated, so the same already-charged bodies were rendered again individually to see all lines. No sixth body or dependency expansion occurred.

## Source custody

| Complete body under src/townlet/substrate | Lines | SHA256 before body |
|---|---:|---|
|base.py|365|36f6bdddac815689993fe7cc94780bd69b3f229e07d623bf65936cc3460d7931|
|factory.py|145|f537479e40e068da399b800d5574bec1f10cfd076e6f18953f3f6c731347a366|
|grid2d.py|473|d17bcd2870be1168ce27aa23f153fdf1b97134e0d6e0b124135557dce696475b|
|grid3d.py|489|9ad6173a3259ddbd41fddd221052575b2b9b967e8150196d6c137f157e4cd714|
|gridnd.py|498|bba779335e80d78e14c6beadc3d407ab3bfd5a1d0b021c06f5ff4ac6d4323631|
|Total|1970|five whole bodies|

Prose provenance: T18e-INITIAL-PARTICIPATION-MASK-OWNER-FACTS.md and T18e-GRID-READ-PURITY.md in this directory explain the named-method gap. Their statements about ENV/builder/observation are attributed boundaries; ENV and builder were not opened here.

## Factory selection and supported premises

factory.py46–71 selects Grid2DSubstrate for `type='grid', grid.topology='square'`, forwarding width,height,boundary,distance_metric,topology,diagonals. Cubic selects Grid3DSubstrate, additionally requiring/forwarding depth. Lines120–128 select GridNDSubstrate for `type='gridnd'`, forwarding dimension_sizes,boundary,distance_metric,topology. Factory device is not installed in these instances or used to migrate mask inputs. Continuous/continuousnd/aspatial branches exist but are outside this grid-only verdict.

2D58–72 and 3D63–76 check positive axis sizes, boundary in clamp/wrap/bounce/sticky and metric in manhattan/euclidean/chebyshev, then store ordinary mutable fields. ND59–94 requires 4..100 positive-sized axes, checks the same boundary/metric choices and retains dimension_sizes by reference; construction can warn at >=10 axes. These are constructor facts, not mask-call writes. Position dimensions are 2 (2D74–77), 3 (3D40), len(dimension_sizes) (ND96–99); declared position dtype is torch.long (2D79–82,3D41,ND101–104).

The result contract below assumes actual ordinary builtin instances, unchanged methods/configuration, stable ordinary dense input tensors of shape [N,D] and target [D], supported finite grid coordinates and compatible same device/dtypes (ordinary grid representation torch.long). No concurrent input/config mutation or custom Tensor dispatch is covered. Constructor validation is not an input-shape validator. Finite values alone do not establish valid shape/device or arithmetic range.

## Actual complete named call graph

| Selected builtin | Entry | Actually called project helper | Formula |
|---|---|---|---|
|Grid2D|grid2d.py453–461|own compute_distance140–160|distance == 0|
|Grid3D|grid3d.py318–320|none|(positions == target_position).all(dim=-1)|
|GridND|gridnd.py426–436|none|(agent_positions == target_position).all(dim=-1)|

Base268–286 declares [N,D] agents, [D] target and bool[N] result; its abstract method does not execute under these concrete entries. **No project helper beyond the five authorized bodies is essential.** ActionConfig imports and unrelated factory imports are not called by this graph. The base pairwise/metric/shape helpers used by observation visibility are not called by these mask entries.

For 2D, compute_distance147–148 checks target rank and unsqueezes a one-dimensional target to [1,2]. This is local variable rebinding to a view, not a target write. It then reads only self.distance_metric:

- manhattan150–152: abs(positions-target).sum(dim=-1).
- euclidean154–156: sqrt(((positions-target)**2).sum(dim=-1)).
- chebyshev158–160: abs(positions-target).max(dim=-1)[0].

The entry compares that new distance tensor to literal zero. No configurable interaction radius, tolerance, threshold, vision fraction or radius helper is consulted. No float32 conversion or normalization is performed. Subtraction, abs/square, reductions, sqrt and equality have normal Torch dtype/promotion/backend behavior. Integer subtraction/square/abs/sum can overflow for sufficiently large valid integer coordinates; this source alone does not certify ideal mathematical exact-cell semantics for arbitrarily large dimensions/coordinates. In particular the 2D euclidean route squares in input arithmetic before sqrt. Finite floating alternatives can also underflow/overflow/round. These numerical limits do not add mutation or RNG and do not affect the literal returned bool dtype/shape on successful valid calls. The exact formula, rather than an unconditional mathematical exact-match claim, is authoritative.

3D/ND entries compare each corresponding coordinate directly and reduce the boolean equality tensor over the last dimension; they do not call compute_distance. Their stored distance_metric, boundary, topology, diagonals, axis sizes and dimension_sizes are not read by the entry. Under valid [N,D]/[D] inputs, true means all coordinate equalities were true in that row. ND's dimension list alias therefore does not directly affect a call at fixed input tensors, though a mutated configuration could change what the owner considers valid D.

For all three entries, successful [N,D] with target [D] yields newly computed torch.bool[N], including N=0, on the common operand device. There is no use of a stored/factory device, explicit `.to(device=...)`, CPU materialization, `.item()`, host list conversion, input output alias return or cached mask. A mismatched-device target is not relocated; normal backend errors apply. Torch comparison/reduction and 2D arithmetic allocate/intermediately compute results; neither source assigns through positions/target views. The output does not promise any particular object identity across calls.

There is no shape/rank/width, bounds, finiteness or device validation at these concrete entries. Normal broadcasting can accept some shapes outside the documented contract and produce other shapes; backend errors can reject others. Do not claim bool[N] for arbitrary malformed inputs, nor claim every malformed input is refused. An invalid post-construction 2D metric falls through compute_distance with no explicit final raise; constructor support plus fixed configuration excludes that case.

## Mutable dependencies, nonmutation and bounded verdict

Only 2D distance_metric is read from self in this runtime graph. Its mutable value must remain one supported fixed string. Changing metric can change arithmetic behavior at non-grid/numerically extreme values; no immunity to concurrent or injected mutation is claimed. Width/height/depth, boundary, topology, diagonals and ND dimension_sizes are not used by these entries. In particular wrap does not select toroidal distance here; clamp/bounce/sticky/wrap yield the same entry formulas at identical input coordinates and (for 2D) metric. Movement, initialization, neighbor enumeration, normalization, visible and egocentric methods are unreachable from this graph.

No inspected instruction assigns self/config/input fields, writes in-place to inputs, installs lazy/cache state, invokes a callback, reads time/done/activity/registry/item/VFS state or consumes RNG. `torch.randint` exists in initialization methods but is not called by is_on_position. 2D's target unsqueeze may alias target storage but is read-only; the graph contains no write through that view.

**Qualified by source:** each factory-selected builtin grid is_on_position is a deterministic, nonmutating, RNG-free read at the fixed builtin configuration and stable finite valid inputs stated above. Repeated successful calls have the same formula-derived boolean values, shape and device without read-count dependence. This is a source-level dependency/purity finding, not executed test evidence, cross-device numerical equality, general GPU determinism or an unrestricted ideal-arithmetic correctness theorem. No unresolved external project owner question remains for this named grid call graph.

This supplies only the grid-is_on_position prerequisite identified by the public mask-owner capsule. It does not qualify continuous/aspatial substrates, base mask ownership, action metadata, item/custom handlers, temporal gate callbacks, mask-builder purity as a whole, ENV reset-state freshness/guards, executable participation atomicity, required-C closure, T18e completion or global acceptance. All owning action-mask calculation/allocation and validation remain subject to the parent design's prepublication cut; no source change is proposed or authorized here.
