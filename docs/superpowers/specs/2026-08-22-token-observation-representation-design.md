# Token Observation Representation — Design

> **Binding amendment — 2026-08-31, `PDR-0131`:** replay stores a compact dynamic flat
> serialization only (presence, live values, actual-rank coordinates). Immutable per-slot
> descriptors live once in compiled context. Token-native feedforward/recurrent networks attach
> that context before per-type projection; universe-bound flat/dueling networks consume the compact
> dynamic view. Fixed-rank expansion occurs at the network boundary, preserving the per-type
> transfer schema. Delete the old full-payload transition ABI; do not support both. This amendment
> supersedes contrary transport and unit-sequencing text below.

**Status:** Design approved in-session by the owner, 2026-08-22, section by section; revised
same day after a four-lens design review (round 1), and revised again after a four-lens
VFS-pairing review (round 2) — both synthesized under "Review amendments". **The second
revision is APPROVED by the owner (2026-08-22), with one binding rider: the no-tech-debt
policy (`PDR-0012`/`PDR-0013`) applies across the board.** Concretely: every review finding
— in this design and in the 13 filed VFS tickets — carries a **named discharge vehicle**
(the migration unit that wires-or-deletes it, or explicit standalone scheduling); nothing
surfaced here is carried as parked debt. Each unit's implementation plan inherits this: a
unit that touches a surface with a filed defect discharges it, never codes around it. The
trial-pack recommendation in unit 5 is adopted (⚖ resolved). Next step: writing-plans for
unit 1.
**Unit:** Phase B unit 2 of the token-observation pivot — "the migration proper and the big
design document" (`PDR-0109`, `PDR-0112`).
**Tracker:** `hamlet-fa6bb6da4a` (this unit) · `hamlet-c586d520b2` (deferred approach A) ·
`hamlet-424adcb84f` (dynamic variables, follows) · `hamlet-83a043a9b9` (agent_private —
referenced boundary, NOT absorbed).
**Related PDRs:** `PDR-0016` (structure vs scale), `PDR-0017`/`PDR-0044` (direction +
authority), `PDR-0045` (never branch on a name), `PDR-0076` (feature vocabulary), `PDR-0107`
(relational exposure waits for tokens), `PDR-0108` (scope), `PDR-0109` (set_encoder proof),
`PDR-0112` (declared aggregator).

## What this supersedes

The fixed-width superset+mask observation ABI: an `ObservationSpec` of index-ranged fields
over a `[B, total_dims]` tensor, with a per-level activity mask holding inactive dims at
zero, a fixed 14-affordance vocabulary, and engine-published raster blocks
(`grid_encoding`, `local_window`, `temporal`, `affordance_at_position`). That design bought
cross-level weight transfer by fixing the vector's width; it hardcoded one universe's
vocabulary into every universe's tensor. Tokens invert the deal: **structure becomes
per-universe content; what is fixed is the type system.**

Tokens fix observation *structure*, not magnitude. Scale stays with the declared
normalization surface (`PDR-0016`). This document must not be read as "the obs problem is
solved" in the scale sense.

## Owner rulings this design is built on (2026-08-22, in-session)

1. **Transfer contract: cross-universe by token type.** A checkpoint transfers wherever
   token *types* match, across different vocabularies (affordance sets, meter rosters,
   grid sizes, substrate dimensionalities).
2. **Token identity: declared payload.** A token's features are its canonically-featurized
   declared, behavior-bearing parameters plus live state. No name, no vocabulary index,
   anywhere in a payload. `PDR-0045` extended into the network.
3. **Non-token architectures: flat view derived from tokens.** The TokenSpec is the one
   source of truth; a canonical serialization doubles as the flat vector for vector
   networks, which stay universe-bound. (Refined in Section 4: the recurrent CNN cannot
   ride the flat view — and the recurrent path is driven by zero shipped packs today.)
4. **Spatial state: per-entity tokens.** The raster dies; the world is entity tokens
   carrying positions; POMDP is a visibility filter. The grid encoding was a view of entity
   positions all along — this is the `PDR-0044` trigger-3 adjudication, decided with the
   owner rather than escalated later. (Section 1 and reversal trigger 2 record the known
   residual: walls/obstacles/zone boundaries are non-entity spatial structure with no token
   form yet.)
5. **Realization: approach C** — token rows serialized into the flat tensor in canonical
   TokenSpec order. Approach A (typed dict-of-streams transport) is captured, not lost:
   `hamlet-c586d520b2`, P4, extractable later *behind* the TokenSpec.
6. **No hardcoded temporality.** There is no `world` token type. The engine publishes one
   primitive — the tick — as an engine-written VFS variable; day/night, seasons, and phase
   are *authored* via VFS expressions and observed as ordinary variable tokens. The
   `temporal` block was Townlet Town content frozen into the engine; it un-freezes.
   **Round-2 correction:** this ruling stands, but the machinery it rides on is a BUILD,
   not a dependency check — see Section 6 unit 2, rescoped.

## Review amendments

### Round 1 (design solo — systems / solution-architecture / PyTorch / DRL)

Five convergent defects, fixed in the first revision: (1) capacity derivation unspecified
for runtime-dynamic types (now a per-type table + loud overflow); (2) the oracle harness
cannot express the DIV-008 stream split (unit 1 is now four harness changes); (3)
RND/intrinsic exploration unaddressed (Section 3b); (4) the payload-bucketing mechanism
named a field that does not exist (replaced with recursive payload-signature identity);
(5) reversal trigger 1 had no possible baseline — zero packs drive `recurrent` (trigger
restated numerically against a frozen pre-cut L2 baseline). Plus: quantified padding
envelope, checkpoint gates replaced not supplemented, ModuleDict/roster policy,
training-dynamical diagnostics, per-type learned embeddings, the shipped-pack inert-guard,
and the Section 6 implementation constraints.

### Round 2 (VFS pairing — same four lenses, plus a VFS-standalone mandate)

The second round paired this design against the VFS code as it exists. Verdict: the
token-side contract held; the VFS-side contract did not meet it in these places, all fixed
in this revision:

1. **`variable_element` tokens had no variable identity** (DRL blocker, mathematical):
   coords+value payloads make co-scoped scalars *provably* indistinguishable under any
   permutation-invariant aggregator, and unit 5's own "authored sin/cos variables" would
   have fired reversal trigger 4 at migration. Fixed: the **variable-descriptor block**,
   the **2-wide value sub-block**, and the **compile-time indistinguishability check**
   (Section 1).
2. **"Scale stays declared" was false on the flagship path**: `vfs_profiles.yaml`
   variables have no normalization field at all (structural root of
   `hamlet-bf42ac60b5`), and the design's named normalization source
   (`VariableDef.normalization`) is consumed nowhere at runtime. Fixed: normalization
   authority ruled, a third admitted authoring surface (required `normalization` on
   exposed profile variables), and boundedness certification (Section 2).
3. **`vfs_hash` and the mirror**: redefining `observation_schema_hash` silently redefines
   `vfs_hash` (a four-term composition the oracle matrix reads), and "TokenSpec replaces
   ObservationSpec" killed the VFS `ObservationField` mirror's only producer without
   saying what replaces it. Fixed: both ruled in Section 5.
4. **Item state cannot come from the scope-driven publisher** — item scope is rejected by
   the registry at three layers; item state lives in the separate `item_vfs` arena.
   Fixed: two fill paths for `variable_element`, stated (Section 3).
5. **Five of nine VFS scopes had no landing spot**, six are structurally unconstructible
   in the current field DTO, and `exposed_to` fails OPEN to `["agent"]` in the required
   authoring file. Fixed: the nine-row scope table with compile-time refusals (Section 2),
   explicit exposure at the cut, and the DTO consequence named in unit 3.
6. **Ruling 6's machinery does not exist**: agent-profile expression evaluation has zero
   call sites; global-profile evaluation is mark-gated and inert on the shipped default
   (`hamlet-df3a96bbac`); no `tick` VFS variable exists; two parallel temporal
   bookkeepings (`global_tick`, `time_of_day`) need reconciling; and the evaluator runs
   *before* the tick increments while the temporal block reads *after* (a one-tick phase
   shift the differential would flag). Fixed: unit 2 rescoped as a build (Section 6).
7. **Trigger 3 fires on day one for `trial_b_blind_organism`** (verified by two lenses
   independently: ≈10× from 249 variable elements alone; ≈25× with its 250-item pool).
   ⚖ owner call — see Section 6 unit 5.

VFS-standalone findings from the widened mandate are filed as tracker issues — and, per
the owner's no-tech-debt rider, **filed with a named discharge vehicle each, never
parked**:

| Ticket | Finding | Discharge vehicle |
|---|---|---|
| `hamlet-b8ad2ffcd6` | exposed profile variables ship raw (no normalization surface) | **unit 3** — Normalization authority (required at exposure) |
| `hamlet-d97b4d6b4a` | `exposed_to` fails open to `["agent"]` | **unit 3** — explicit exposure at the cut |
| `hamlet-d970ef83f0` | `set_engine_value` shape bypass | **unit 3** — named prerequisite (capacity/coordinate derivation) |
| `hamlet-88578e629e` | effects DTOs lack `extra="forbid"` + behavioral defaults | **unit 3** — prerequisite of `max_active_effects` |
| `hamlet-81942565ff` | `VFSObservationSpec` live fallbacks (`max_items_per_agent=3` in-engine) | **unit 3/6** — dies with the mirror; capacity table replaces the fallback |
| `hamlet-0ddc83e377` | VTC/evaluator write-backs silently drop unknown ids | **unit 3** — made loud as part of the cut (publisher-variable renames make it live) |
| `hamlet-6a6e104523` | `rank_scaled` ranks across independent worlds / constant-zero | **unit 3** — same surface as the boundedness/kind rules; restricted or refused there |
| `hamlet-bc0a5deeff` | item-profile expressions never evaluate (3rd inertness instance) | **unit 2** — the evaluation scope decision covers all three profile kinds: evaluate or refuse-at-compile, never silently inert |
| `hamlet-0ba58fd9dc` | `ScopedVariableRegistry` + `dynamic_needs.py` production-dead | **unit 6** — deletion sweep (added to its list explicitly) |
| `hamlet-c7084169f7` | per-step VFS clone traffic (5× full-state/step) | **unit 3/4** — the trigger-3 step-time baseline is clone-audited before that trigger is read |
| `hamlet-702ae15f82` | stale zone-scope conclusion in trial_k record + extents preflight gap | record half: **pack-disposition/record-keeping queue** (measure-bet residual scope); preflight two-liner rides **unit 3** |
| `hamlet-5f99e89865` | `environment.yaml` lifetime hardcoded to tick (counters silently reset) | **WS-4 queue** — authoring-surface work, routed per the standing rule; not this migration's scope |
| `hamlet-955900540e` | hygiene batch (vocab mismatch, misleading errors, docstring, host-syncs, one_hot guard, masked_value) | standalone, schedulable now — cheap fixes, several in files unit 3 rewrites anyway |

Existing tickets `hamlet-83a043a9b9` (agent_private) and `hamlet-bf42ac60b5` (raw values in
observation) received mechanism-evidence comments; their observation-path halves are
discharged by the Section 2 scope table's publisher filter and the normalization authority
respectively, and the tickets close when those land.

---

## 1. The token type system

A closed set of token types replaces the ten-member `ObservationFeature` vocabulary as what
the runtime and networks dispatch on. Same discipline as
`src/townlet/universe/dto/observation_feature.py`: one definition; a new type is a new
member plus a new publisher, never a name to match.

| Token type | Cardinality per compiled universe | Replaces (old feature) |
|---|---|---|
| `self` | 1 | `position`, `velocity` |
| `meter` | one per declared meter | `meter` |
| `affordance` | one per placed affordance instance | `grid_encoding`, `local_window`, `affordance_at_position` |
| `agent` | one per other agent **sharing the world** (0 in independent-env packs) | (raster's agent channel) |
| `item` | one per world/carried item instance | `item_slots` (instance/position half) |
| `effect` | one per active observable effect | `effects` |
| `variable_element` | one per element of each exposed variable (incl. item-profile state) | `variable`, `item_slots` (state half), `temporal` (via authored variables) |
| *reserved names:* `relation`, `message`, `group` | — | `PDR-0107`'s exposure; later units |

Seven live types plus three reserved names. The reserved names mark intent only — they are
**not** settled shapes. `relation` is dyadic (two entity references) and will likely not
fit the one-filler-per-slot binding model; treat reversal trigger 2 as *likely*, not merely
possible, for it. Nothing in this unit builds them.

### Invariants

- **Payload width is fixed per token type, across all universes.** Entity variation goes
  into token *count*, never payload width. A 30-affordance universe has 30 affordance
  tokens, not a wider row.
- **The max position rank is an engine constant: `MAX_POSITION_RANK = 8`.** Position
  payloads pad to it, with a rank feature. Covers every shipped and test substrate (2-D,
  3-D, 6-D, 7-D). A pack declaring a substrate of rank > 8 is **refused loudly at compile
  time**. This is a real capability contraction for GridND's documented 4–100D range —
  named as the trade it is: the cut *closes* gridnd's POMDP gap (Section 3) and *opens*
  this narrower one. Raising the constant breaks all checkpoints (the vocab-content hash
  catches it) and is done by superseding PDR.
- **Tensor-shaped variables tokenize per element.** Payload = normalized element
  coordinates (padded to `MAX_POSITION_RANK`, rank feature) + the value sub-block +
  the descriptor block (both below). Scalars are the rank-0 case.
- **The `variable_element` payload carries a variable-descriptor block** (round 2, DRL
  blocker). Coords+value alone make co-scoped variables provably indistinguishable under
  permutation-invariant pooling — `{world_temp: 0.3, season_clock: 0.7}` and its swap pool
  identically for every possible weight setting. The descriptor block is fixed-width,
  name-free, and built from the variable's *declaration*: scope one-hot (9), declared
  `semantic_type` one-hot (6), normalization signature (kind one-hot 9 + canonical
  parameter vector, absent-marked), dtype flag (3), lifetime one-hot (3), normalized
  declared initial value, log-scaled element count, and the owner/slot coordinate where
  applicable. Exact widths in unit 3's table; sketch ≈ +30 features. Ruling 2 is
  unchanged: identity is still declared payload — the block just stops dropping the
  declaration.
- **The value sub-block is 2 wide (`VALUE_BLOCK_WIDTH = 2`), with a width-used feature.**
  Round 2 found the declared normalization vocabulary contains *width-changing* kinds
  (`cyclical_sin_cos` 1→2, `one_hot` 1→C), which cannot fit a 1-wide value slot without
  breaking the fixed-width invariant — the exact source/observed-width conflation the
  compiler already carries a scar comment about. Rule: scalar-width kinds use lane 0;
  `cyclical_sin_cos` lands sin and cos **in one token** (lanes 0–1) — which is also what
  makes authored temporality whole (one `day_phase` variable, one token, phase pairing
  preserved by construction); `one_hot` is **refused at compile time on tokenized
  variables** (the categorical fact is carried as normalized index + the categories count
  in the descriptor block; a future widening is a superseding PDR).
- **Boundedness is certified at exposure.** A value feature entering a token must come
  from a bounded normalization kind (or a range kind with `clip: true`). Exposing a
  variable under `none`, `zscore`, unclipped `minmax`, or bare `masked_value` is a
  compile-time refusal naming the rule. (LayerNorm does not save unbounded values — it
  saturates them into unreadability while RND treats them as perpetual novelty, the
  `PDR-0016` odometer shape. Quiet failure twice over; hence loud refusal.)
- **Compile-time indistinguishability check.** Two exposed variables whose static payload
  signatures (descriptor block + coordinate space) are identical are a **compile error**
  naming both declarations and demanding a distinguishing declared parameter. This
  converts the silent-aliasing failure into a loud authoring error, and is what keeps
  reversal trigger 4 an edge case instead of a scheduled event.
- **Identity = declared payload, applied recursively.** An affordance token's payload:
  `interaction_type` one-hot; absolute position AND position-relative-to-self (egocentric —
  "standing on it" = relative zero, which is what deletes `affordance_at_position`); and a
  fixed-size **effect summary** of k = 4 entries, each `(delta magnitude, sign, target
  signature)` where the target signature is the target meter's own declared-parameter
  features — identity-by-payload applied to the reference as well as the referent. Fewer
  than k effects: absent-marked; more: the k largest by normalized magnitude, count
  carried as a feature.
- **Two payload-identical entities at the same position are genuinely the same** to the
  agent — correct for *instances of one declaration* (a true world symmetry; DRL round 1
  endorsed). Round 2's finding was that *variables* are not instances of one declaration,
  which is what the descriptor block now encodes. Reversal trigger 4 remains the exit for
  the residual case.
- **Presence is explicit** — leads every row; mask-source only for token networks
  (stripped before the per-type projection; the flat view sees it). Mask derivation is
  `presence > 0.5`; `key_padding_mask` stays bool.
- **Scale stays declared** (`PDR-0016`) — with the round-2 correction that the authority
  is now real: see Section 2, "Normalization authority".
- **Known non-entity residual, pre-registered for trigger 2:** walls, impassable cells,
  zone boundaries. No shipped pack has them; the moment one does (L4 multi-zone), trigger
  2 fires on spatial structure itself. Note: dense occupancy tensors authored as VFS
  variables (trial_b's 243-cell organism) are this residual arriving in authored-variable
  form — the raster re-entering by the side door. The reopening move is a
  spatial-structure payload or learned position encoding, never a raster revival.

## 2. TokenSpec — the compiled artifact

`TokenSpec` **replaces** `ObservationSpec` as the compiler's product. Per compiled universe:

- **Type roster** — which types this universe instantiates, engine-fixed canonical order.
- **Per type: payload schema** — feature names, order, normalization refs. An engine
  constant per type, embedded so the artifact is self-describing.
- **Per type: compiled capacity and slot bindings** — N deterministic slots, each bound at
  compile time to its filler. Binding order is declaration order, stable, and hashed.
- **Per type: the token census** (round 2) — slot counts published in the artifact and in
  `inspect` output. Compiling `{type: mean}` against a census where any single type
  exceeds **64 tokens** emits a loud compile-time advisory naming the counts and the
  regime guidance — the Section 4 advisory turned into an instrument, this repo's pattern.

### Scope → token-type table (round 2; the contract, with refusals)

| `VariableScope` | Landing under this design |
|---|---|
| `global` | `variable_element` (registry publisher) |
| `agent` | `variable_element` (registry publisher) |
| `agent_private` | **excluded from observation by the publisher — filtered before slot binding, pinned by test.** The `hamlet-83a043a9b9` boundary is enforced here by mechanism, not assumption: scope-driven enumeration (`list_agent`) includes agent_private and the raw accessors do no reader check, so the filter is the publisher's, explicitly. |
| `item` (profile state) | `variable_element` via the **item-arena publisher** (Section 3) with owner/slot coordinate |
| `affordance` | **exposure refused at compile time in this unit**, with the landing pre-named: `variable_element` with an affordance-index owner coordinate — the only reading compatible with the fixed-width invariant (folding into the `affordance` token's payload would make that width per-universe). Lands when its authoring surface exists. |
| `pair` | exposure refused at compile time; reserved (`relation`) |
| `group` | exposure refused at compile time; reserved (`group`) |
| `zone` | exposure refused at compile time; pre-named as the natural first move if trigger 2 reopens on zone structure |
| `message` | exposure refused at compile time; reserved (`message`) |

"Refused at compile time" means a variable of that scope declaring exposure fails the
compile loudly, naming this table — never a silently absent token. Unexposed declarations
(e.g. `L5_multi_agent`'s `trust`/`occupied_by`, both `observable: false`) compile
unchanged. **DTO consequence, named for unit 3:** the current observation-field DTO types
scope as a three-member Literal, so the publisher plumbing needs a widened or new DTO —
that work is in unit 3's plan, not discovered there.

### Exposure is explicit at the cut (round 2)

`exposed_to` currently **fails open to `["agent"]`** in all three `vfs_profiles.yaml`
blocks — a No-Defaults violation on the field that now sizes the observation. At the cut
the default-injection validators are deleted: an empty `exposed_to` means **unexposed**,
and every exposure is authored. Capacity, the worked width table, and trigger 3's
arithmetic are computed only after this lands — otherwise the trigger fires on an artifact
of a default.

### Normalization authority (round 2)

One rule: **the normalization that feeds a token value is declared on the variable being
exposed, and it is required at exposure.** Concretely: exposed `vfs_profiles.yaml`
variables gain a **required `normalization` field** — the third admitted new authoring
surface (they currently have none at all, which is the structural root of
`hamlet-bf42ac60b5`: today every exposed profile variable ships raw). `environment.yaml`
variables keep their already-required spec. The two inert/indirect paths die with the cut:
`VariableDef.normalization` (consumed by nothing at runtime) and the name-keyed
`environment.yaml` lookup that profile fields ride today. Unexposed variables need no
normalization. Refusal shapes: see Section 1's boundedness and width rules.

### Capacity derivation (per type — all declared, one honest exception)

| Type | Capacity | Source |
|---|---|---|
| `self` | 1 | — |
| `meter` | count of declared meters | `bars.yaml` |
| `affordance` | count of placed affordance instances | `affordances.yaml` |
| `agent` | declared agents-per-world − 1 | see below |
| `item` | `max_items_in_world + max_items_per_agent × agents_per_world` | `items.yaml` (required fields). Note this is a deliberate widening: world items become observable entities under the visibility filter — today `max_items_in_world` plays no part in observation sizing. |
| `effect` | Σ of a **per-scope declared budget** — `max_active_effects: {global: N, agent: N, item: N, affordance: N}` in `effects.yaml`, required if any effects are declared; each scope's count multiplied by its denominator (world / agents / item capacity / affordance instances) | declared, No-Defaults. Prerequisite: the effects DTOs gain `ConfigDict(extra="forbid")` — they are currently the only DTOs in the area without it, so a typo'd budget field would be silently ignored. |
| `variable_element` | Σ element counts of **explicitly** exposed variables (registry scopes + item-profile state) | VFS declarations, post explicit-exposure |

**The `agent` exception, stated honestly:** "how many agents share one world" is a runtime
constructor argument today — `default_curriculum`'s population of 8 is 8 *independent*
worlds, so its `agent` capacity is **0** and the type is structurally absent there.
Capacity derives from a declared shared-world agent count; where no declaration exists,
capacity is 0. Candidate homes, shortlisted for unit 3 (not decided here): the
`training.yaml` population block (already compiled per level) vs `stratum.yaml` (couples
topology to population — probably wrong). If a new field is needed, that is admitted
authoring surface #4.

**Overflow is loud.** A publisher asked to place more live instances than compiled
capacity **raises at publish time**, naming the type, capacity, and source. Silent
truncation is a lying observation. `VectorizedHamletEnv` construction refuses a
`num_agents` that contradicts compiled capacity. Prerequisite (round 2): the
`set_engine_value` shape bypass — which today lets a global scalar legally hold `[B]` —
is closed in unit 3, or compile-time capacities and coordinate buffers are fiction.

### Serialization = the flat view

Rows concatenate in canonical type-then-slot order, presence leading each row:

```
total_dims = Σ_type  N_type × (1 + payload_width_type)
```

One layout, two readings: reshape-by-spec (token tensor) or read-as-is (flat vector). Said
plainly: **the flat view is a supported second, universe-bound ABI this project intends to
carry**, guarded by the layout-hash gate. Its transfer contract (layout equality) is weaker
than the token contract (type schemas); today's pack census (31 of 32 brains
feedforward/dueling) means most packs use the weaker one until they opt in.

**Worked instance (ESTIMATE — exact table owed by unit 3, computed only after explicit
exposure lands):** `default_curriculum` L1 roster: 1 self + 8 meters + 14 affordances +
0 agents + 0 items + 0 effects + a small authored-variable set (the compiled L1 spec today
has **zero** variable fields — the prior "~10" was wrong; post-cut it gains at least the
authored temporal variables). With sketch widths (self ≈ 18, meter ≈ 8, affordance ≈ 34,
variable_element ≈ 45 with the descriptor block), serialization lands ≈ **650–750 dims,
roughly 5–6× today's ~120**, dominated by affordance position padding and the descriptor
block. Stated up front because trigger 3 watches it.

**What dies:** the activity mask **and its whole mechanism** — `curriculum_active` on both
DTOs, `ObservationActivity`, the allocated-vs-active framing CLAUDE.md teaches (its docs
move at landing), and the mask's RND constructor contract (Section 3b); the raster and
window encoders; the temporal block; the VFS `ObservationField` mirror and
`vfs/observation_builder.py`'s `VFSObservationSpec` (see Section 5 — the mirror's fate is
ruled, not implied); the two inert normalization paths above. `observation_schema_hash` is
redefined over the TokenSpec. `COMPILED_SCHEMA_VERSION` bumps; stale `.compiled` artifacts
refuse loudly — and the `.compiled` payload schema itself changes (the serializer
round-trips `VFSObservationSpec` today with required fields; that block is replaced, named
in unit 3's plan).

**What authors declare:** exposure (`exposed_to`, now explicit), normalization (now
required at exposure), semantic types as today — plus the admitted additions:
`max_active_effects` (per-scope), the shared-world agent count (when multi-agent packs
need it), and required `normalization` on exposed profile variables. The first revision's
"nothing new to declare" was false in three places, now four; all are stated. Tokenization
is derived from scope and shape; capacities are compiler-derived per the table;
`vision_range` keeps its meaning.

## 3. Runtime encoding and the visibility filter

- **One publisher per token type — with `variable_element` filled by two publishers**
  (round 2): the **registry publisher** for global/agent scopes, and the **item-arena
  publisher** for item-profile state. Item state is not scope-addressed registry storage —
  it is rejected there at three layers and lives in the consolidated `item_vfs`
  `[max_items, max_vars]` arena with a compiled index map. That arena+map is also the
  in-tree template for how the registry publisher should be built: today's global/agent
  fill is a per-variable Python loop with a clone per read (round 2 answered the open
  verify-item: **not batched, in any sense**), so unit 3 builds either a per-scope arena
  (item_vfs-style) or a compiled index-map with per-variable `.view()` writes — an
  explicit choice in the plan, not an adaptation of `build_vfs_observation`.
- **Publishers dispatch on type** — the `PDR-0076` discipline. Access control: the
  registry's guarded reader is *not* what the observation path uses today (the raw
  accessors check nothing), so the publisher's `agent_private` filter (Section 2 table) is
  the enforcement point, pinned by test.
- **Presence ownership:** compile-time-static entities publish presence 1;
  runtime-dynamic entities toggle. Dynamic slot assignment is unique-slot writes only.
- **Visibility filter:** spatial token types pass through substrate-provided
  `visible(self_pos, entity_pos, vision_range)` under the declared metric and boundary
  mode (wrap-aware). Out of range ⇒ presence 0, payload zeroed. Full observability =
  pass-all. POMDP levels are the same TokenSpec with a radius; GridND gains partial
  observability (≤ rank 8 — the Section 1 trade).
- **Egocentric features** computed at publish time: `entity_pos − self_pos`, normalized
  per declared encoding mode, shortest-path under wrap.
- **Read point:** publishers run at the existing end-of-step observation point — the one
  well-defined sync point after all VTC/effects/evaluator writes of the tick (verified
  sound in round 2; the ordering is inherited, the implementation is not).

## 3b. Intrinsic exploration across the cut (RND)

- **The consumer:** `RNDNetwork` registers the activity mask as a static buffer multiplied
  into every novelty forward. The mask dies; that constructor contract dies with it —
  deleted, not defaulted. RND consumes the flat serialization directly.
- **The named risk:** presence flips are large discontinuous jumps; RND novelty becomes
  partly a visibility-churn detector, and pacing the visibility boundary is a predictable
  intrinsic-reward pump feeding the annealing gate (the `PDR-0016` shape, measured once
  already in this repo).
- **The decision:** instrument, don't redesign: (a) the cut's adjudication includes a
  **measured** intrinsic-reward distribution comparison on identical states pre/post cut;
  (b) training diagnostics add per-step intrinsic reward vs presence-flip count; (c) if
  boundary-farming appears, it is preserve-and-document material — an interesting failure
  is only valuable if the instrument to see it exists first.
- **Native token consumption for intrinsic modules** is a named follow-on.

## 4. Network consumption and the flat view

**Token-native network** (successor to `SetEncoderQNetwork`):

1. Per-type projection encoders — `Linear(W_t → token_embed_dim)` in an **`nn.ModuleDict`
   keyed by token type name** (a list indexed by roster position re-binds weights silently
   on roster differences);
2. a **learned per-type embedding added post-projection** (type-keyed, transfers; closed
   roster, fixed-size);
3. all tokens pooled into **one set**;
4. the `PDR-0112` aggregator block verbatim — `{type: mean}` | `{type: attention,
   num_heads: N}`, declared, required;
5. Q-head.

**Why one mixed set:** the design's own cross-type bindings — effect-summary → meter
signature, and (round 2) item-instance ↔ item-state conjunctions — are attention patterns
*across* types; per-type pooling would hardcode that types never attend to each other.
The dilution cost is real and handled by the census advisory, the regime advisory, and the
PMA escape hatch.

**Aggregator regime advisory** (also goes in `docs/config-schemas/brain.md`): `mean` suits
small rosters of behaviorally-distinct entities under full observability. `attention` is
the expected choice for large/homogeneous/variable-count sets, for POMDP, **and for packs
with item state** (round 2: "the item in slot 0 is the fast-decaying tool AND its
durability is low" spans two tokens and is not sum-decomposable — it needs the attention
hop, exactly like the effect-summary binding). `mean` + LSTM is the weakest configuration
in the design space. A **`{type: pma}`** member (learned-seed cross-attention pooling,
O(N), permutation-invariant, capacity-independent) is the pre-named first upgrade; the
census advisory names when. Both remain declarable; "mean degrades with scale" is
legitimate teaching material.

**Masking mechanics (load-bearing):** an absent token's zero row embeds to LayerNorm's
bias, not zero — output-side masking guarantees exact-zero contribution and exact-zero
gradient, per aggregator type, pinned by test. The all-empty unmask guard survives.

**`brain.yaml` surface:** `architecture.type: token_set`, declaring `token_embed_dim`, the
aggregator block, and Q-head sizes. The roster is compiled, never authored. No-defaults.

**The recurrent path:** the flat view keeps vector networks alive (`feedforward`,
`dueling`); `RecurrentSpatialQNetwork` cannot ride it (its CNN consumes the dead raster) —
and zero shipped packs drive it (census: 26 feedforward, 5 dueling, 1 set_encoder, 0
recurrent; L2/L3 run feedforward today). It joins `StructuredQNetwork` and
`SetEncoderQNetwork` on the verify-then-delete list. **Recurrence is still built
token-native** (encoders → aggregator → LSTM → Q-head) because POMDP needs memory in
principle; unit 4's justification is forward-looking, its baseline discipline is trigger
1. This also justifies unit 3's atomicity: the recurrent path being dark strands no pack.

**Provenance and load:** `brain_hash` unchanged. The checkpoint gates `observation_dim`
equality and `observation_field_uuids` are **REPLACED**: token nets compare on the
TokenSpec **type-schema hash** (hashing payload-schema *contents* — closed-vocabulary
members, `MAX_POSITION_RANK`, `VALUE_BLOCK_WIDTH` — so a vocab bump produces the banner,
not a shape error); flat nets compare on the **layout hash**. `observation_field_uuids`
dies with its producer. Roster mismatch at cross-universe load is loud: load the
intersection of type keys, report both directions, refuse on payload-schema mismatch.
Cross-universe loads reset optimizer state, re-copy the target network, and reset RND
state. Per-type encoders and the aggregator transfer as *feature extractors*; the Q-head
transfers only *mechanically* — its values encode the source universe's rewards and must
be relearned.

## 5. Transfer, provenance, and the oracle

- **Hashes — ruled, not deferred** (round 2): `observation_schema_hash` is redefined over
  the TokenSpec type-schema + slot-binding content and moves on every pack, once.
  **`vfs_hash` keeps its name and meaning: the TokenSpec-derived `observation_schema_hash`
  occupies slot 2 of the same four-term composition** — so `vfs_hash` also moves on every
  pack at the cut, as a consequence, and the oracle matrix columns that read both are
  re-baselined by the DIV-008 entry. **The VFS `ObservationField` mirror and
  `VFSObservationSpec` die**: the mirror was always derived *from* `ObservationSpec` (the
  hash was computed one hop downstream), and with TokenSpec hashed directly there is
  nothing left for it to mirror. `vfs/observation_builder.py`'s spec/mirror halves are
  deleted; its normalization kernels (`apply_normalization`) survive and move to the
  publisher path. The enumeration of engine-minted publisher variables and any further
  hash movement stays in unit 3's plan — that part is inventory; the identity decisions
  above are not, which is why they are here.
- **The oracle cut needs the harness unit 1 builds.** The adjudication criterion: **tokens
  change what agents see, never what the world does.** Register entry DIV-008, written
  BEFORE the cut, splits the streams: observation streams diverge, registered per-stream;
  world dynamics under **scripted** actions — state evolution, rewards, terminals — must
  stay byte-exact. (Honest rationale: the current driver draws actions from the global
  RNG, so the hazard is RNG-stream coupling, not a "live policy"; scripted actions remove
  it.) The scripted mode lives inside the self-contained driver rule and is verified
  all-AGREE on current code first, including the RNG-call-order spot-check.
- **Transfer is a tested contract:** two disjoint-vocabulary universes; train-step a token
  net on one; weights load by type (ModuleDict keys) and forward cleanly. This test fails
  against the current checkpoint gates; their replacement is part of the same unit.
  Zero-shot *competence* is a research observation, never an acceptance criterion. One
  recorded, non-gating experiment: transferred-encoders-fresh-Q-head vs from-scratch
  sample efficiency.
- **Docs:** "ask the compiled artifact, never quote a width" survives (`total_dims` =
  serialization width; the allocated-vs-active distinction dies with the mask). CLAUDE.md,
  `docs/config-schemas/`, README all move at landing, gate-2 standard.

## 6. Migration sequencing and test strategy

Implementation units, in dependency order — each lands green, each gets its own plan:

1. **Harness adjudicability** — four changes: (a) scripted-action trace mode inside the
   self-contained driver; (b) a stream-scoped registered-divergence shape beside the
   hash-only one; (c) non-short-circuiting per-stream adjudication; (d) a shape-preflight
   exemption for streams under a registered divergence. Verified all-AGREE on current
   code, plus the RNG-call-order spot-check.
2. **Authored temporality made real — a BUILD, not a dependency check** (rescoped, round
   2): (a) `tick` as an always-on, engine-written VFS global, independent of
   `enable_temporal_mechanics`, with its **write point pinned in the tick order** so
   authored phase and observation see the same value (the evaluator currently runs before
   the tick increments — left unpinned, authored temporality lags one tick and DIV-008
   flags it); (b) global-profile expression evaluation working on the shipped default —
   `hamlet-df3a96bbac`'s empty-mark-set path fixed; (c) `global_tick`/`time_of_day`
   reconciled into the one pipeline; (d) scope decision recorded for agent-profile
   evaluation (`hamlet-5d74335111` — zero call sites exist; not strictly needed for
   temporality, same subsystem, unit 2's plan says build-now or defer-explicitly).
3. **Baselines, then register DIV-008, then the cut as one atomic knockdown.** Baselines
   first: current shipped L2 (feedforward over superset+mask), ≥ 5 seeds, frozen curves —
   unrepeatable after the raster dies. Then the cut: TokenSpec replaces ObservationSpec,
   publishers replace sync steps (storage decision made: per-scope arena or index-map —
   see Section 3), the widened scope DTO, explicit `exposed_to`, required normalization at
   exposure, the `set_engine_value` shape-bypass closed, checkpoint gates replaced,
   `.compiled` payload schema updated, token-native net + flat view. No green half-state
   exists (justified: the recurrent path is dark). Adjudicated per Section 5.
4. **Token-recurrent variant** — POMDP levels to tokens+LSTM; window machinery deleted;
   gridnd partial vision arrives. DoD includes the trigger-1 comparison (both aggregators)
   against the unit-3 frozen baseline, before unit 6 deletes anything.
5. **Pack migration** — every shipped pack recompiles; `set_encoder_smoke` re-authored;
   **L3 temporality becomes ONE authored `day_phase` variable with `cyclical_sin_cos`
   normalization → one token with the paired value block — never two scalar variables**
   (round 2: the two-scalar form re-imports the aliasing and ships a learnability
   regression). Acceptance keeps the inert-guard — every live token type N > 0 in at least
   one committed pack that compiles AND runs in the suite — **extended to scopes**: every
   scope row in Section 2's table demonstrably behaves as the table says (lands, or
   refuses loudly). **Trial-pack interaction (owner-adopted 2026-08-22):**
   `trial_b_blind_organism` breaches trigger 3 immediately if exposed/migrated (≈10–25× —
   round 2, two lenses). Ruling: the retired corpus's trial packs resolve on their
   existing 2026-10-06 disposition clock *before* this unit; the inert-guard is satisfied
   by purpose-built or promoted packs, and trigger 3 is evaluated only on packs that
   survive disposition. A retired-corpus artifact does not force-promote approach A.
6. **Deletion sweep** — activity mask + `curriculum_active` + `ObservationActivity` (and
   RND's dead constructor contract), raster/window encoders, temporal block, the VFS
   mirror + `VFSObservationSpec`, the two inert normalization paths, `StructuredQNetwork`,
   `SetEncoderQNetwork`, `RecurrentSpatialQNetwork`, and the production-dead
   `ScopedVariableRegistry` + `vfs/dynamic_needs.py` (`hamlet-0ba58fd9dc`); docs and
   README at gate-2 standard.
   **Prerequisite: the token-table inspector exists** (dump one step's token set per
   agent, presence and payload labeled) — the raster was also the debugging view.

Follow-ons outside this unit: relational/message tokens (discharges `PDR-0107`), dynamic
variables (`hamlet-424adcb84f` — note for its brief: `exposed_to` has a second,
scope-agnostic reader under `dynamic_variable_mode` that disagrees with observation about
which scopes count), native token intrinsics (Section 3b).

**Test strategy.** TDD throughout.

*Structural:*
- Per token type, a **wiring test**: declare → that token row moves. Per scope, a
  **table test**: each Section 2 scope row lands or refuses exactly as stated.
- Permutation invariance re-pinned on the **mixed-type** set.
- Presence tests: legitimately-zero ≠ absent; **exact-zero contribution and exact-zero
  gradient** for absent tokens, per aggregator type.
- **Indistinguishability check test**: two identical-signature exposures refuse at
  compile; adding any distinguishing declared parameter compiles.
- Width rules: `cyclical_sin_cos` variable compiles to one token with both lanes;
  `one_hot` exposure refuses; unbounded-kind exposure refuses.
- Visibility-filter tests per substrate and boundary mode; wrap-aware egocentric features.
- The transfer-contract test, including roster-mismatch loudness.
- Flat-view forward passes + layout-hash gates.
- Scripted-action differential: dynamics byte-exact across the cut.
- Overflow raises at capacity + 1; `set_engine_value` shape drift raises.
- Replay aliasing: store two consecutive ticks, assert they differ.

*Training-dynamical diagnostics (recorded during training; the structural suite passes
green while training quietly degrades without these):*
- Per-type encoder gradient norms and update magnitudes (dead rare-type encoders).
- Cold-token injection: bounded Q-perturbation on a never-seen token toggling present.
- TD-error distribution conditioned on presence-flip count between s and s′.
- Pooled-embedding norm and online-vs-target cosine drift.
- Intrinsic reward vs presence-flip count (Section 3b).
- Mean-vs-attention **learning** probe on a navigation task (also services `PDR-0112`'s
  inert-declaration trigger).
- **Flat-vs-token A/B on the same pack** sweeping exposed payload-identical scalars — the
  flat view retains slot identity, so this directly measures any residual identity loss
  and falsifies (or vindicates) the descriptor block. (Round 2's free instrument.)
- **Slot-swap Q-sensitivity + linear decode probes** for item-state binding (swap two
  slots' contents in a probe state; decode "durability of slot k" and "profile of slot k"
  individually and jointly from the pooled embedding) — wired into trial_f-style pack
  acceptance in unit 5.

**Implementation constraints (carried so every unit plan inherits them):** publisher write
targets use `.view()` (raises on copy), never `.reshape()`; stored observations are
`.clone()`d or per-tick allocated; the token-recurrent forward folds `[B, S, ·]` →
`[B·S, ·]` through encoders+aggregator and runs **one** `nn.LSTM` call over the sequence;
attention uses explicit QKV + `F.scaled_dot_product_attention` with the math backend
pinned where byte-exact training replay matters; masks are bool; no LayerNorm/Linear over
concatenated set width anywhere in the token path; the packed single-GEMM encoder form is
permitted later only if the checkpoint format stays per-type; registry publisher fills are
batched per scope via the arena/index-map (never per-variable Python loops); item-arena
reads never hold cross-tick views.

## Reversal triggers (into the landing PDR)

1. **POMDP learnability regression:** token-feedforward and token-recurrent (both
   aggregators) on L2 fail to reach **≥ 80% of the unit-3 frozen baseline's final greedy
   survival within the same env-step budget** (seed-level IQM, non-overlapping CIs).
   Fires → reopen the spatial representation (spatial-structure payload or learned
   position encoding, not a raster revival).
2. **A surface emerges with no natural token form** — `PDR-0044` trigger 3 stays armed.
   Pre-registered candidates: walls/obstacle/zone structure (including dense occupancy
   tensors in authored-variable form), and the dyadic `relation` shape.
3. **Capacity/padding cost bites, with numbers:** a shipped pack's serialization exceeds
   **8× its pre-cut allocated width** (evaluated post-disposition, post-explicit-exposure
   — see unit 5), or observation encoding exceeds **25% of `env.step` wall time**
   (measured against a step baseline that is itself clone-audited — round 2 found the
   current step path clone-bound, which would flatter this percentage), or
   recurrent-attention training memory forces `batch_size` below the declared value.
   Fires → promote `hamlet-c586d520b2` (approach A) and/or land `{type: pma}`.
4. **Two entities the agent must distinguish are payload-identical** in a real authored
   pack — with the descriptor block and the indistinguishability check in place this is
   now a genuine edge case, not a scheduled event. Fires → hybrid (payload + learned tag)
   identity, its own PDR (owner ruling — trigger 2's reserved exit from ruling 2).

## Verify-at-implementation (not design questions)

- Whether any production caller depends on `StructuredQNetwork`, `SetEncoderQNetwork`, or
  `RecurrentSpatialQNetwork` (expected: none — config census found zero).
- Where the shared-world agent count is declared (shortlist in Section 2).
- Whether `vtc.py` consumes `ObservationSpec`, the activity mask, or field uuids anywhere
  (round 2's one unread giant — a single grep settles it and gates the deletion list's
  completeness; if it does, the "tokens never change what the world does" criterion needs
  re-examination there first).
- Whether temporal *mechanics* beyond observation exist that ruling 6's observation change
  must leave untouched.
- The exact per-type payload widths `W_t` and the real `total_dims` table (post
  explicit-exposure), including descriptor-block widths.
- Whether persistent-lifetime tick counters can exceed float32-exact integer range
  (2²⁴) over long runs — cast policy note for the publisher.
