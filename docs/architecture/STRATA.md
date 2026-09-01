# Strata — the space subsystem

Document date: 2026-08-24
Status: **Current** (reviewed 2026-08-24) — part of the six-document HLD set (PDR-0118).

Strata declares **space**: what kind of it exists, how it connects, what happens at its edges,
how far apart two things are, and how position enters the observation tensor. It is the smallest
of the three compiled subsystems and the one with the sharpest boundary — everything here is a
property of *where things can be*, never of what they are or what they do.

Where this document and an archived one disagree, this one wins; where it and `README.md`
disagree, README wins; where either disagrees with `src/townlet/`, the source wins.

---

## 1. Strata's place in the trio

| subsystem | question | authored in | doc |
| --- | --- | --- | --- |
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

**Examples: read the shipped packs, not a template.** There is no `configs/templates/`
directory — that path is dead.

| pack | shows |
| --- | --- |
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
| --- | --- | --- | --- |
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
| --- | --- | --- |
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
`docs/config-schemas/enabled_actions.md` (archived 2026-08-24; content may be
stale).

Compile-time alignment between the two halves is checked by `SubstrateActionValidator`
(`src/townlet/environment/substrate_action_validator.py`), surfaced as
`SUBSTRATE_ACTION_INCOMPATIBLE` / `SUBSTRATE_ACTION_WARNING_AS_ERROR`. It validates aspatial and
square/cubic grids; continuous and gridnd currently impose no discrete action requirements.

---

## 6. The observation seam

Spatial observation is a token-publisher concern, not an observation-width API. The compiler
builds one `TokenSpec`; at runtime publishers ask the substrate two questions:

- `visible(self_pos, entity_pos, vision_range)` returns the `[observer, entity]` presence mask.
- `egocentric_delta(self_pos, entity_pos)` returns normalized entity-minus-observer offsets.

No substrate emits a grid raster or local window, and no network derives an input width from a
substrate. The compiled token roster, capacities and payload schemas determine the serialization.

### 6.2 Canonical bounded position encoding

There is one position contract across every spatial family. Absolute coordinates are normalized
to `[0, 1]` per axis; egocentric deltas use the same denominator and land in `[-1, 1]`. Grid axes
divide by `max(size - 1, 1)` and continuous axes divide by their declared extent. The deleted
`observation_encoding` selector is rejected as an extra config field; raw-coordinate and
extent-appending alternatives do not exist.

### 6.3 Width and visibility

`TokenSpec.total_dims` is the flat serialization width. It is the sum of each token type's
compiled capacity times its compact row width. Full and partial visibility use the same spec and
the same width: partial visibility clears presence and payload for out-of-range spatial tokens.

Cross-universe token transfer is governed by `token_type_schema_hash`, not equal flat widths.
Flat `feedforward` and `dueling` readers remain positional and therefore use `layout_hash`.

> **No dimension literals.** Ask the compiled artifact for `token_spec.total_dims`,
> `token_spec.census`, and `token_spec.row_layout()`.

---

## 7. POMDP support

`stratum.vision_support` must admit the level's `active_vision`; incompatible declarations fail
with `VISION_INCOMPATIBLE`. Once admitted, the token visibility contract covers every substrate:

| substrate | `visible()` radius | `egocentric_delta()` |
| --- | --- | --- |
| Grid2D, Grid3D, GridND | `max(1, ceil(vision_range * longest_axis / 2))` cells | divide by `max(axis_size - 1, 1)` |
| Continuous, ContinuousND | `vision_range * longest_extent / 2` world units | divide by axis extent |
| Aspatial | all entities visible | width-zero deltas |

The declared distance metric combines per-axis deltas. `wrap` uses the toroidal shortest path;
clamp, bounce and sticky use ordinary in-bounds deltas. `vision_range: null` at the runtime seam
means global visibility. A partial level passes its required normalized `vision_range` instead.

---

## 8. Future direction: hybrid / dimension-declarative substrates (proposed 2026-08-24 — not designed, not built)

**Everything in this section is proposal. Nothing here is implemented, scheduled, or designed
beyond the sketch below.** Tracker: `hamlet-157deba962` (status: proposed).

The owner proposes a **hybrid substrate**: N-dimensional space that is continuous in some
dimensions and discrete in others. Motivating example — a building: continuous `x, y` within a
floor, a discrete floor index as the third dimension.

Today's taxonomy cannot express that: `SubstrateConfig.type` is a closed enum (`grid` / `gridnd`
/ `continuous` / `continuousnd` / `aspatial`) in which every spatial dimension of a substrate is
the same kind. The generalization the proposal implies is a **per-dimension declaration model**
— each dimension declares its kind (`discrete` | `continuous`), extent or range, and boundary
mode — under which the current types become special cases (a grid is all-discrete, a continuous
space all-continuous, aspatial zero dimensions). That is consistent with the
declare-don't-hardcode ethos and the spirit of PDR-0117: the *shape* of space becomes a
declaration, not a menu entry.

The multi-floor mechanic needs **no new topology concept** — it composes from existing
declarative primitives. The developer masks the regular move-up / move-down substrate actions on
the discrete floor dimension, and an **elevator affordance** writes the floor coordinate — one
interaction per destination floor, like elevator buttons (`teleport_to` already exists in the
action schema). Hybrid substrates would compose with action masking and position-writing
affordances rather than requiring a graph-topology concept.

Open design questions, noted rather than resolved: per-dimension boundary modes (e.g. `wrap` on
an angular dimension beside `clamp` on a linear one); how a distance metric composes across
mixed dimension kinds; action-space composition (discrete ±1 movement actions for discrete
dimensions alongside discretized continuous displacement for continuous ones, under §5's
ordering contract); and POMDP distance/visibility semantics across mixed dimensions.

---

## 9. Where to read next

- `docs/config-schemas/` — authoring schemas; **schemas lived there, not here** —
  but that location was archived 2026-08-24 (commit `c4e8bd58`) and nothing has replaced it, so
  cite it knowing it is no longer maintained. Action surface:
  `docs/config-schemas/enabled_actions.md`.
- `HLD.md` — the trio, the compiler-and-provenance contract, honest status.
- `UAC.md` — everything Strata is *not*: variables, items, effects, affordances, rewards.
- `COMPILER.md` — the seven-stage pipeline and the error codes cited above.
- `archive/substrate-system.md` — history: the WebSocket substrate-metadata contract consumed by
  the frontend, and the topology-extension sketch. Its §WebSocket Metadata Contract JSON blocks
  were re-checked against the current builder on 2026-08-24 and **match field-for-field**:
  `live_inference._build_substrate_metadata` (`src/townlet/demo/live_inference.py:191-250`)
  emits `type` (class name lowercased, minus "Substrate") + `position_dim` always; grids add
  `topology`, `width`/`height` (+`depth` for Grid3D; `dimension_sizes` for GridND), `boundary`,
  `distance_metric`; continuous substrates add `bounds`, `boundary`, `movement_delta`,
  `interaction_radius`, `distance_metric` and no `topology`; aspatial adds nothing. Everything
  *else* in the archived doc: cite for history, never as evidence of what is implemented.
- `scripts/validate_substrate_runtime.py` — smoke-tests packs end to end.
