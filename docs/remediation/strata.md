# Strata — gap analysis and remediation plan

Scope: `src/townlet/substrate/` (base, grid2d, grid3d, gridnd, continuous, continuousnd,
aspatial, factory), `config/stratum_config.py`, and the environment's consumers:
`action_mask_builder.py`, `action_executor.py`, `action_labels.py`,
`substrate_action_validator.py`, `compilers/actions.py`, the spatial lanes of
`token_publishers.py`, and position setup, movement deltas and affordance placement in
`vectorized_env.py`.
Evidence: `review-2026-10-24/findings_strata.md`, scripts `review-2026-10-24/strata/s1-s13`.

## What the subsystem promises

README and STRATA.md: square and cubic grids, GridND, continuous 1D to ND, aspatial; boundary
modes clamp, wrap, bounce, sticky; manhattan, euclidean, chebyshev distance; a composed action
space with a canonical ordering; normalized positions in `[0,1]` and egocentric deltas in
`[-1,1]` with one per-axis denominator; POMDP visibility by substrate metric with toroidal
shortest paths under wrap. Trial 001 is cited as a witness that survival rules moved to a 6-D
grid by configuration alone.

## What it does

The geometry is right. The reviewer refuted its own hypotheses on the radius formula, wrap
shortest-path at even and odd spans, the shared normalization denominator, 1-wide axes, every
boundary × metric combination in every family, bounce and sticky signs, rectangular grids end to
end, aspatial tolerance of every position path, and the schema hash across 2-D, 3-D, 4-D,
continuous and aspatial packs.

The gaps are in the layer between the substrate and the policy. The action mask does not know
the boundary mode exists, so a policy can never cross a wrap seam. Continuous2D applies
`movement_delta` twice. Affordance randomization is silently downgraded when a grid is crowded.
Items cannot be placed on anything but a 2-D or 3-D grid. Family-specific vocabularies disagree
on whether `WAIT` is a substrate action, whether walls are masked, and whether
`action_discretization` means anything.

## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_strata.md`
(F-numbers) and filigree ids.

| id | sev | gap | source |
|---|---|---|---|
| S1 | P1 | Action mask ignores `boundary`; wrap and bounce unreachable by any masked policy | F1 |
| S2 | P1 | Continuous2D applies `movement_delta` twice | F2 |
| S3 | P1 | Over-capacity grid silently disables randomization; affordances at origin until reset; random-deployment packs crash on reset | F3 |
| S4 | P1 | Items never spawn off Grid2D/Grid3D; every placement path is rank 2 | F4, hamlet-6c49488b22 |
| S5 | P2 | Fixed affordance positions never bounds-checked at compile | F5 |
| S6 | P2 | Custom `WAIT` with writes silently dropped on GridND/ContinuousND | F6 |
| S7 | P2 | `action_discretization` required everywhere, consumed only by Continuous2D | F7 |
| S8 | P2 | Velocity lane unbounded (−7 on wrap, world units on continuous) | F8 |
| S9 | P2 | `vision_support: none` unusable; `active_vision: local` residual | F9 |
| S10 | P2 | `[-2]/[-1]` ordering contract false after composition; STRATA.md §5 says code relies on it | F10 |
| S11 | P2 | Engine branches on `velocity_x/y/z/magnitude` variable names | F11 |
| S12 | P3 | `SubstrateActionValidator` tautological; dead `hex` branch | F12 |
| S13 | P3 | No boundary masking at all on GridND/continuous | F13 |
| S14 | P3 | `math`/`cardinal` labels wrong sign; dead label helpers | F14 |
| S15 | P3 | Grid2D bounce lacks clamp; zero-legal-action rows possible; rank limits in constructors | F15, F16, F19 |
| S16 | P3 | Residue: dead `_encode_*`, `get_valid_neighbors`, meter-cost literals, `_layout`, blanket whitelist | F17, F18 |

## Remediation plan

### WP1 — Boundary-aware masking (S1, S13, S15)

Replace the duck-typed block in `action_mask_builder.py` with a substrate method:
`substrate.blocked_moves(positions, movement_deltas) -> bool[N, A]`. Grid families implement it
from their boundary mode (clamp blocks, wrap and bounce never block, sticky blocks once stuck);
GridND and continuous implement the same contract so the family inconsistency closes with the
bug. Add the Grid2D bounce clamp. Add an "at least one legal action" guarantee: when the mask
would be all-false, unmask `WAIT` if declared, else `INTERACT`.

Verification: `s2_wrap_mask.py` becomes a test: on `configs/differential/boundary_wrap` the
corner agent has every move legal and `apply_movement` lands on the far edge; on clamp the same
moves are masked. `s11_masks_labels.py` GridND case: a clamp bump is masked. Size: M.
**This unblocks the `boundary_wrap` oracle cell, which has never measured wrap.**

### WP2 — Single scaling in Continuous2D (S2, S7)

`_generate_discretized_actions` emits unit direction vectors like 1D and 3D; `apply_movement`
remains the only place `movement_delta` applies. Then decide `action_discretization`: either
every continuous family honours it (1D with two directions is degenerate; 3D and ND would need a
direction-sphere scheme) or the field is admitted only when `dimensions == 2`. The plan recommends
the conditional field; pass it to ContinuousND only if ND gets a scheme.

Verification: `s1_continuous2d_double_scale.py` expects 0.5. `configs/test/action_space/continuous1d`
refuses `action_discretization` at parse. Size: S.

### WP3 — Refuse over-capacity instead of downgrading (S3, S5)

`randomize_affordance_positions` stops flipping the flag. Capacity (`agents + affordances >
cells`) is a config fact: refuse it in cross-validate when `randomize_affordances: true`, with the
numbers in the message. `__init__` calls `_apply_configured_affordance_positions()` when
randomization is off, so positions are never the origin by accident. Run the bounds check that
`validate_affordance_positions` already does over `deployment.positions` at cross-validate.

Verification: `s3_capacity_fallback.py` refuses at construction with a capacity message;
`s3b_capacity_random.py` never raises "requires explicit position"; `s8_fixed_oob.py` refuses at
compile. Size: S.

### WP4 — Rank-generic item placement (S4)

Shared with the items plan (its WP3), owned here for the position typing. `fixed_positions` and
script positions become `list[list[int | float]]` validated against `substrate.position_dim` at
cross-validate. `reset()` asks the substrate for its extents (`dimension_sizes`, `bounds`, or
"none" for aspatial) instead of `hasattr(width)`. `find_spawn_location`, `grid` placement and
`random` placement iterate `position_dim` axes. Aspatial: items have no position; either refuse
`items_appearance` on aspatial or give items a positionless mode. Delete the dead axial
`{"q","r"}` branch.

Verification: `s9_items_nd.py` spawns the coat on gridnd and cubic; a 4-D `fixed_positions` entry
parses; a 2-D entry on a 3-D substrate refuses at compile. Size: M.

### WP5 — One `WAIT` vocabulary (S6, S10)

`WAIT` is passive, not spatial. No substrate emits it; it is a custom action in every pack, and a
custom action colliding with a substrate movement name is a refusal (the `reserved_names` path
two lines below already does this). Rewrite the ordering contract in `base.py` and STRATA.md §5 to
what is true: movement block, then `INTERACT`, within the substrate-sourced prefix; custom and
item actions follow; nothing indexes by position. Aspatial's `[INTERACT]` matches.

Verification: `s6_custom_wait_dropped.py` on gridnd keeps the custom `WAIT` and its writes;
`s5_action_order.py` shows no family emitting `WAIT`. Size: S.

### WP6 — Bounded velocity and declared velocity variables (S8, S11)

Velocity becomes `substrate.egocentric_delta(old, new)`: shortest path under wrap, same
denominator as positions, bounded in `[-1,1]`. The magic names in `action_executor.py` go: if an
authored pack wants velocity as a variable, that is a declared engine-write binding (a
`semantic_type: velocity` or an explicit `engine_writes:` list on the declaration), not an id the
engine recognises. Until a pack needs it, delete the branch.

Verification: `s4_velocity.py` wrap case publishes `[-1/7, 0]` scaled, not −7;
`s4b_velocity_continuous.py` publishes a normalized value. Size: S.

### WP7 — Vocabulary hygiene (S9, S12, S14)

Delete `vision_support: none` and the `local` branch. Delete `SubstrateActionValidator` or make it
validate the compiled action metadata against `inherit` and the declared custom actions. Fix the
`math`/`cardinal` sign labels (or flip the Grid2D `UP` delta so `MOVE_Y_POSITIVE` is up, which is
a differential-visible change and needs a divergence entry). Delete `FORWARD`/`BACKWARD`,
`action_labels.get_labels`, `_filter_labels_for_substrate`, `get_label`, `get_action_count`.

Verification: `s7_vision_none.py` refuses at parse; `s11_masks_labels.py` label table matches
delta signs. Size: S.

### WP8 — Residue (S16)

Delete `_encode_scaled`/`_encode_absolute` from all five substrates, `get_valid_neighbors` and
`supports_enumerable_positions`/`coordinate_semantics`/`action_space_size` if still uncalled
after WP1, the meter-cost literals in `continuous.py`, and `token_publishers._layout`. Move
constructor rank limits into the DTOs. Replace the `substrate/**:*` whitelist line with per-line
entries or nothing. Size: S.

## Docs to correct in the same changes

- `docs/architecture/STRATA.md` §5: the ordering contract (WP5) and the validator description
  (WP7).
- `docs/manual/pomdp_compatibility_matrix.md`: `vision_support` values (WP7).
- `CLAUDE.md` "Action Space": already says "never quote a count"; add "WAIT is never a substrate
  action" (WP5). The `token_type_schema_hash` literal there is stale (`8ad2b59b502a905b` today);
  delete the literal rather than update it.
