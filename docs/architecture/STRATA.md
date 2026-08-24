# Strata — the space subsystem

Document date: 2026-08-24
Status: **Current** — first draft of the six-document HLD (PDR-0118, owner-amended to six);
pending review pass.

Strata declares **space**: what kind of it exists, how it connects, what happens at its edges,
how far apart two things are, and how position enters the observation tensor. It is the smallest
of the three compiled subsystems and the one with the sharpest boundary — everything here is a
property of *where things can be*, never of what they are or what they do.

Where this document and an archived one disagree, this one wins; where it and `README.md`
disagree, README wins; where either disagrees with `src/townlet/`, the source wins.

---

## 1. Strata's place in the trio

| subsystem | question | authored in | doc |
|---|---|---|---|
| **Strata** | *Where can things be?* — space itself | `stratum.yaml` | this document |
| **UAC** — Universe as Code | *What exists, and how does it change?* | the rest of the pack | `UAC.md` |
| **BAC** — Brain as Code | *How do agents think?* | `brain.yaml` | `BAC.md` |

Historically (UAC v2.5, 2025-11) "Universe as Code" meant *strata + world config* as one blob.
Strata is promoted out because space is a different kind of declaration from world rules,
compiled against a different DTO, and consumed by different compiler stages — the action
compiler and the observation compiler both ask the substrate directly, before any world rule is
resolved.

Strata is also the subsystem that most cleanly demonstrates the product thesis. Changing a
universe from an 8×8 grid to a 7-dimensional hypercube, or to no space at all, is a `stratum.yaml`
edit. No environment subclass, no observation plumbing, no action enumeration.

---

## 2. What `stratum.yaml` declares

The DTO is `StratumConfig` → `StratumConfigRoot` in `src/townlet/config/stratum_config.py`
(**not** `townlet.substrate.config` — that module does not exist, and several archived documents
cite it). Every field is required; `ConfigDict(extra="forbid")` throughout, per the No-Defaults
Principle.

`StratumConfigRoot` carries five declarations:

- `version` — config schema version.
- `substrate` — the `SubstrateConfig` block (§3–§4).
- `vision_support` — `global | partial | both | none`. What vision modes this space *can*
  serve. Cross-validated against each level's `curriculum.active_vision`
  (`universe/validation/semantics.py:118-139`, error code `VISION_INCOMPATIBLE`).
- `temporal_support` — `enabled | disabled`. Gates multi-tick affordances
  (`MULTI_TICK_REQUIRES_TEMPORAL`).
- `observation_mode` — `full_auto | max_compact | full_manual` (§6.4).

**Examples: read the shipped packs, not a template.** There is no `configs/templates/`
directory — that path is dead.

| pack | shows |
|---|---|
| `configs/default_curriculum/stratum.yaml` | the reference grid: `square`, 8×8, `clamp`, `manhattan`, `relative`, `diagonals: true`, `vision_support: both` |
| `configs/test/action_space/grid2d/stratum.yaml` | grid action-space contribution in isolation |
| `configs/test/action_space/aspatial/stratum.yaml` | the no-space case |
| `configs/test/action_space/continuous1d/stratum.yaml` | continuous with `action_discretization` |
| `configs/test/gridnd_4d_pack/stratum.yaml` | an N-dimensional grid |

⚠ Do not lift the YAML blocks in `archive/substrate-system.md`. Its *concepts* are accurate, but
it predates the `substrate.yaml` → `stratum.yaml` rename and omits the now-required `diagonals`
field; its examples would not validate today.

### 2.1 Scope: one space per pack

`stratum.yaml` is read **only** from the pack root — `RawConfigsV21.from_experiment_dir`'s
`shared_specs` list (`src/townlet/universe/raw_configs_v21.py:114-119`) resolves it against
`experiment_dir`, and nothing anywhere resolves a level-scoped path. Every level of a pack
therefore shares one space: `configs/default_curriculum` is 8×8 for all five of its levels.

Note the *mechanism*, because it differs from the sibling prohibitions. `vfs_profiles.yaml` and
`effects.yaml` are in preflight's `forbidden_level_files` and a level copy is refused loudly
(`SCOPING_FORBIDDEN_LEVEL_FILE`). `stratum.yaml` is **not** in that list: a file dropped into a
level directory is not refused, it is simply never read. The constraint holds by construction
rather than by a gate. (Earlier drafts marked this TODO-VERIFY; it is now verified.)

---

## 3. Substrate families

`SubstrateConfig.type` is a closed literal — `grid` | `gridnd` | `continuous` | `continuousnd` |
`aspatial` — with exactly one matching sub-block required and more than one refused
(`stratum_config.py:179-203`).

| type | sub-block | implementation | position |
|---|---|---|---|
| `grid` | `GridConfig` | `Grid2DSubstrate` (`topology: square`) / `Grid3DSubstrate` (`topology: cubic`) | discrete, `torch.long` |
| `gridnd` | `GridNDConfig` | `GridNDSubstrate` | discrete, `torch.long` |
| `continuous` | `ContinuousConfig` | `Continuous1D/2D/3DSubstrate` by `dimensions` | float, `torch.float32` |
| `continuousnd` | `ContinuousConfig` | `ContinuousNDSubstrate` | float, `torch.float32` |
| `aspatial` | `AspatialConfig` (empty marker) | `AspatialSubstrate` | none, `position_dim == 0` |

**There is no `grid3d` type.** The literal was deleted because it never had a
`SubstrateFactory` branch — it could only compile toward a guaranteed factory crash. The working
3-D path is `type: grid` with `topology: cubic`, which additionally requires `depth`
(and `topology: square` must *omit* it). The comment recording this sits at
`stratum_config.py:166-170`.

Dispatch is `SubstrateFactory.build` (`src/townlet/substrate/factory.py`) — a single flat
`if/elif` from config to concrete class. Substrates are device-agnostic: the `device` argument is
reserved, and tensors are created on the device passed to each method call.

All implementations satisfy `SpatialSubstrate` (`src/townlet/substrate/base.py`), whose abstract
surface is the whole of what the rest of the engine may know about space: `position_dim`,
`position_dtype`, `get_default_actions`, `initialize_positions`, `apply_movement`,
`compute_distance`, `encode_observation`, `get_valid_neighbors`, `is_on_position`,
`get_all_positions`, `get_capacity`, and the five-member observation-shape contract of §6.

---

## 4. Topology, boundaries, distance

**Topology** is the connectivity pattern — how a cell reaches its neighbours.

| topology | connectivity | declared by |
|---|---|---|
| `square` | 4-connected 2D Cartesian grid (±X, ±Y) | `GridConfig.topology` |
| `cubic` | 6-connected 3D Cartesian grid (±X, ±Y, ±Z) | `GridConfig.topology` |
| `hypercube` | 2N-connected N-dimensional grid, dimension-agnostic | `GridNDConfig.topology` (only legal value, stated explicitly to avoid a hidden default) |

Continuous substrates have **no** discrete topology — positions are floats, not cells — and
aspatial substrates have no spatial structure at all. In both cases the topology field is absent
from runtime metadata rather than set to a placeholder.

**Boundary modes**, on every spatial family (`Literal["clamp", "wrap", "bounce", "sticky"]`):
hard walls, toroidal wrap, elastic bounce, sticky edges. Handling is per-substrate inside
`apply_movement`.

**Distance metrics** (`Literal["manhattan", "euclidean", "chebyshev"]`): L1, L2, L∞. For grid
substrates `manhattan` is the metric that matches 4-/6-/2N-connected movement. All three are
legal on continuous substrates too, and the field is required there as everywhere — the literal
merely happens to list `euclidean` first (`stratum_config.py:130`). There is no default.

Extending the topology vocabulary is a four-step change (config literal → factory branch →
substrate class → frontend renderer); `archive/substrate-system.md` §Future Extensions sketches
it. One artefact of an abandoned attempt: `substrate_action_validator.py:51` branches on
`topology == "hex"`, which `GridConfig`'s `Literal["square", "cubic"]` makes unreachable. That is
why older documents mention hex grids.

---

## 5. The action seam: substrate actions + custom actions

**The action space is composed, not per-substrate-constant.** The substrate contributes the
movement half; `actions.yaml` contributes custom actions; the pack's compiled action metadata is
the only authority on the result.

The durable part is the **canonical ordering contract**
(`src/townlet/substrate/base.py:80-103`), which every substrate must satisfy:

1. movement actions (substrate-specific),
2. `INTERACT` at `[-2]`,
3. `WAIT` at `[-1]`.

Downstream systems identify meta-actions by position, so `actions[:-2]` is always movement.
Aspatial is the special case: no movement actions at all, `[INTERACT, WAIT]` only
(`aspatial.py:159-165`).

**The movement set is a function of substrate type *plus declared parameters*.** `GridConfig`
requires `diagonals: bool`, threaded through the factory to `Grid2DSubstrate(enable_diagonals=)`
/ `Grid3DSubstrate(...)`, and `get_default_actions` emits `UP_LEFT` / `UP_RIGHT` / `DOWN_LEFT` /
`DOWN_RIGHT` only when it is true (`grid2d.py:160`, the diagonal block gated at `grid2d.py:224`).
Continuous substrates synthesize their movement set from `action_discretization`
(`num_directions` 8–32 × `num_magnitudes` 3–7, both required). GridND emits `DIM0_NEG`/`DIM0_POS`
… per dimension.

⚠ **No action-count literals in this document**, for the same reason as dimension literals.
CLAUDE.md's table ("Grid2D 8, Grid3D 10, GridND(7D) 16, Aspatial 4") **disagrees with the
source**: `base.py`'s own docstring enumerates Grid2D as eight movement actions plus `INTERACT`
and `WAIT`, and that is itself conditional on `diagonals`. Ask the compiled artifact. Schema:
`docs/config-schemas/enabled_actions.md`.

Compile-time alignment between the two halves is checked by `SubstrateActionValidator`
(`src/townlet/environment/substrate_action_validator.py`), surfaced as
`SUBSTRATE_ACTION_INCOMPATIBLE` / `SUBSTRATE_ACTION_WARNING_AS_ERROR`. It validates aspatial and
square/cubic grids; continuous and gridnd currently impose no discrete action requirements.

---

## 6. The observation seam

The observation compiler (`src/townlet/universe/compilers/observation.py`) never derives a
spatial width itself — it **asks the substrate instance**, through the five-member contract
documented at `base.py:195-255`. Deriving these numbers anywhere else is the defect class behind
`DIV-003` in `docs/oracle/known-divergences.md`.

### 6.1 The three spatial fields

| field | width from | emitted when |
|---|---|---|
| `obs_grid_encoding` | `get_grid_encoding_dim()` | `vision_support` in `{both, global}` and the substrate has a grid |
| `obs_local_window` | `get_partial_window_dim(get_vision_radius(vision_range))` | `vision_support` in `{both, partial}` and `supports_partial_vision` |
| `obs_position` | `get_position_feature_dim()` | non-zero position features |

`get_grid_encoding_dim()` is **one slot per cell** — `width * height` for Grid2D,
`width * height * depth` for Grid3D. GridND has no occupancy grid, so its published grid encoding
*is* its coordinate encoding; continuous and aspatial return 0 and no such field is declared.

### 6.2 Position encoding modes

`observation_encoding` (`relative` | `scaled` | `absolute`), required on every spatial family:

- **`relative`** — normalized [0,1] coordinates. Best for transfer learning, and what POMDP
  position context always uses (`normalize_positions` returns relative regardless of mode).
- **`scaled`** — normalized coordinates **plus the extents**, so the value range conveys grid size.
- **`absolute`** — raw unnormalized coordinates, for physical simulation.

⚠ **`scaled` is wider than the other two.** CLAUDE.md's "all encoding modes produce identical
obs_dim (2 dims for position)" is **false against the source**: `grid2d.py:480-493` returns
relative → 2, scaled → **4** (x, y, width, height), absolute → 2; `grid3d.py:496-509` returns
3 / **6** / 3. Relative and absolute agree; scaled widens the position block because it packs the
extents into it. Continuous and GridND route `obs_position` through their whole coordinate
encoding.

### 6.3 What "constant width" actually claims

**Allocated observation width is constant across the levels of one pack**, because every level
shares one `stratum.yaml` (§2.1) — that is the mechanism behind cross-level checkpoint transfer,
together with the global action vocabulary. It is **not** constant across grid sizes: one slot
per cell means a larger grid allocates a wider `obs_grid_encoding` field.

POMDP does not shrink the tensor. Both `obs_grid_encoding` and `obs_local_window` are allocated
when `vision_support: both`; the level's `active_vision` sets `curriculum_active` on each, and
the inactive block is held at zero rather than removed.

> **No dimension literals.** "Observation dim" is two quantities — *allocated*
> (`observation_spec.total_dims`) and *active* (`sum(observation_activity.active_mask)`) — and
> conflating them is what corrupted every dimension table in the old corpus. Never write either
> number in a document; ask the compiled artifact. See `HLD.md` §5.3 for the snippet.

### 6.4 `observation_mode` interacts with allocation

`_apply_observation_mode` (`observation.py:883-901`) filters the field list *before* widths are
summed:

- `full_auto` — every field is kept. This is what preserves the superset-plus-mask property.
- `max_compact` — keeps only fields with `curriculum_active`, i.e. **drops** the inactive blocks
  rather than zeroing them. That genuinely narrows the tensor, and therefore trades away the
  cross-level transfer property of §6.3.
- `full_manual` — an explicit `include_fields` list; unknown names and empty results raise.

`configs/default_curriculum` declares `full_auto`.

---

## 7. POMDP support

Three independent gates, and conflating them is a common error:

1. **Substrate capability** — `supports_partial_vision`. True in `grid2d.py:473` and
   `grid3d.py:489`; **False** in `gridnd.py:379`, `continuous.py:334`, `continuousnd.py:328`,
   `aspatial.py:78`, where `get_vision_radius` / `get_partial_window_dim` raise `ValueError`.
   Requesting `active_vision: partial` on an unsupported substrate raises at compile
   (`observation.py:202-206`).
2. **Window size** — for supported substrates, `vision_range` is a **normalized fraction** of the
   longest axis (`get_vision_radius` = `max(1, ceil(vision_range * span / 2))`), and validation
   refuses when the implied window is too large. From
   `tests/test_townlet/unit/environment/test_pomdp_validation.py`: Grid3D accepts `0.5` on an 8³
   grid (window 5) and rejects `0.75` (window 7 → "requires 343 cells"); GridND 4D is rejected
   outright (`Partial observability .* gridnd`). Read the test for the live matrix.
3. **Declared support** — `stratum.vision_support` must admit the level's `active_vision`
   (`VISION_INCOMPATIBLE`, §2).

⚠ CLAUDE.md's support matrix is wrong on two counts against the source: it lists **Aspatial as
supported ("special case")** — `aspatial.py:78` returns False — and it phrases the Grid3D
constraint as "vision_range ≤ 2", which predates the normalized-fraction encoding. Its
continuous-substrate exclusion is correct, and is now source-verified rather than TODO.

---

## 8. Where to read next

- `docs/config-schemas/` — authoring schemas; **schemas live there, not here**. Action surface:
  `enabled_actions.md`.
- `HLD.md` — the trio, the compiler-and-provenance contract, honest status.
- `UAC.md` — everything Strata is *not*: variables, items, effects, affordances, rewards.
- `COMPILER.md` — the seven-stage pipeline and the error codes cited above.
- `archive/substrate-system.md` — history: the WebSocket substrate-metadata contract consumed by
  the frontend (`live_inference._build_substrate_metadata`), and the topology-extension sketch.
  Cite for history, never as evidence of what is implemented.
- `scripts/validate_substrate_runtime.py` — smoke-tests packs end to end.

**TODO-VERIFY**: the archived WebSocket metadata contract (§Topology Metadata JSON blocks) has
not been re-checked against the current `live_inference` builder in this pass; the *shape* is
plausible but the field list may have drifted.
