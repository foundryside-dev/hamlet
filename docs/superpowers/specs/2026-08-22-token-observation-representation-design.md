# Token Observation Representation — Design

**Status:** Design approved in-session by the owner, 2026-08-22, section by section; under
multi-lens review (systems / solution-architecture / PyTorch / DRL) before implementation
planning.
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
   networks, which stay universe-bound. (Corrected in Section 4: the recurrent CNN cannot
   ride the flat view — recurrence is rebuilt token-native.)
4. **Spatial state: per-entity tokens.** The raster dies; the world is entity tokens
   carrying positions; POMDP is a visibility filter. The grid encoding was a view of entity
   positions all along — this is the `PDR-0044` trigger-3 adjudication, decided with the
   owner rather than escalated later: the block has a natural token form because it
   dissolves into entities.
5. **Realization: approach C** — token rows serialized into the flat tensor in canonical
   TokenSpec order. Approach A (typed dict-of-streams transport) is captured, not lost:
   `hamlet-c586d520b2`, P4, extractable later *behind* the TokenSpec.
6. **No hardcoded temporality.** There is no `world` token type. The engine publishes one
   primitive — the tick — as an engine-written VFS variable; day/night, seasons, and phase
   are *authored* via VFS expressions (e.g. `sin(2π·tick/day_length)`) and observed as
   ordinary variable tokens. The `temporal` block was Townlet Town content frozen into the
   engine; it un-freezes.

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
| `agent` | one per other agent | (raster's agent channel) |
| `item` | one per world/carried item instance | `item_slots` (position/slot half) |
| `effect` | one per active observable effect | `effects` |
| `variable_element` | one per element of each exposed variable | `variable`, `item_slots` (state half), `temporal` (via authored variables) |
| *reserved:* `relation`, `message`, `group` | — | `PDR-0107`'s exposure; later units |

Seven live types plus three reserved; the reserved types are named now so the type system
does not need reshaping when relational/message exposure lands.

### Invariants

- **Payload width is fixed per token type, across all universes.** This is what makes the
  transfer contract literal: per-type network weights are shape-stable everywhere. Entity
  variation goes into token *count*, never payload width. A 30-affordance universe has 30
  affordance tokens, not a wider row.
- **Tensor-shaped variables tokenize per element.** Payload = normalized element
  coordinates (padded to a fixed max rank, with a rank feature) + the value. Scalars are
  the rank-0 case. Item state = `variable_element` tokens carrying an owner/slot
  coordinate. (Authored row-as-token layouts — heterogeneous declared columns — are NOT
  expressible in this unit; they are the dynamic-variables follow-on's territory,
  `hamlet-424adcb84f`.)
- **Identity = declared payload.** Example, affordance token: costs and effect deltas
  bucketed by the target meter's declared `semantic_type`; `interaction_type` one-hot from
  its closed vocabulary; plus live state — absolute position AND position relative to self
  (egocentric). "Standing on it" = relative position zero, which is what deletes
  `affordance_at_position` as a block. Two behaviorally-identical affordances at different
  positions differ by position; at the same position they are genuinely the same to the
  agent, and that is correct under ruling 2.
- **Presence is explicit.** Every token row leads with a presence feature (1/0). This
  retires the all-zeros-means-empty heuristic from the unit-1 set encoder, which cannot
  represent a legitimately all-zero token.
- **Scale stays declared** (`PDR-0016`): every value feature passes through its
  variable's/meter's declared normalization before entering the token.
- **Position payloads are padded to a fixed max rank** (with a rank feature), so `grid`,
  `gridnd`, `continuous`, and `aspatial` substrates emit the same token shapes. The max
  rank is an engine constant of the type system (set generously; revisit only by
  superseding this design).

## 2. TokenSpec — the compiled artifact

`TokenSpec` **replaces** `ObservationSpec` as the compiler's product. Per compiled universe:

- **Type roster** — which types this universe instantiates, in engine-fixed canonical
  order.
- **Per type: payload schema** — feature names, order, normalization refs. An engine
  constant per type (the fixed-width invariant), embedded so the artifact is
  self-describing — never so universes can vary it.
- **Per type: compiled capacity and slot bindings** — N deterministic slots, each bound at
  compile time to its filler (affordance instance → slot, meter → slot, variable element →
  slot). Binding order is declaration order, stable, and hashed.

**Serialization = the flat view.** Rows concatenate in canonical type-then-slot order,
presence leading each row:

```
total_dims = Σ_type  N_type × (1 + payload_width_type)
```

One layout, two readings: reshape-by-spec (token tensor) or read-as-is (flat vector).

**What dies:** the activity mask (per-level variation is presence/capacity, not zeroed
dims); the raster and window encoders; the temporal block. `observation_schema_hash` is
redefined over the TokenSpec. `COMPILED_SCHEMA_VERSION` bumps; stale `.compiled` artifacts
refuse loudly.

**What authors declare — nothing new.** Exposure (`exposed_to`), normalization, and
semantic types are the existing surfaces; tokenization is derived from scope and shape.
Capacities are compiler-derived, never authored. `vision_range` keeps its meaning as the
visibility filter's radius.

**Honest limit on the flat view:** width is exact per compiled level. Flat-vector
architectures transfer only where serialization layouts match (loader compares layout
hashes loudly). The shipped pack's levels share declarations so widths coincide in
practice, but the *contract* lives with token-consuming networks only.

## 3. Runtime encoding and the visibility filter

- **One publisher per token type**, dispatching on type — the `PDR-0076` discipline carried
  over. Engine publishers fill `self`/`meter`/`affordance`/`agent`/`item`/`effect`; the
  registry fills `variable_element` by declared scope, access control enforced as today.
  Each publisher is one vectorized op over its type's slot range in `[B, total_dims]`.
- **Presence ownership:** compile-time-static entities (meters, variable elements, self)
  publish presence 1. Runtime-dynamic entities (other agents, active effects, items)
  toggle presence as they exist.
- **Visibility filter:** spatial token types pass through a substrate-provided predicate
  `visible(self_pos, entity_pos, vision_range)` under the pack's declared distance metric
  and boundary mode (wrap-aware on toroidal). Out of range ⇒ presence 0, payload zeroed.
  Full observability = pass-all. POMDP levels are the same TokenSpec with a radius — and
  because the filter is metric-based, not window-based, **GridND gains partial
  observability**, closing the "window too large for N≥4" limitation in kind.
- **Egocentric features** are computed at publish time: `entity_pos − self_pos`,
  normalized per the declared encoding mode, shortest-path under wrap.
- **Boundary honestly drawn:** per-agent visibility of other agents' internal state
  (`agent_private`, `hamlet-83a043a9b9` — open, P1) is neither solved nor widened here.
  `agent` tokens carry only position and public kinematics until relation tokens land.

## 4. Network consumption and the flat view

**Token-native network** (successor to `SetEncoderQNetwork`):

1. Per-type projection encoders — `Linear(payload_width_type → token_embed_dim)`, one per
   roster type;
2. all tokens pooled into **one set** in the common embedding space;
3. the `PDR-0112` aggregator block verbatim — `{type: mean}` | `{type: attention,
   num_heads: N}`, declared, required;
4. Q-head.

Masking runs off the explicit presence column. **What transfers is exactly the type-keyed
weights** — per-type encoders, aggregator, Q-head — none capacity-dependent. The remaining
transfer gate is the action vocabulary, checked loudly at load as today.

**`brain.yaml` surface:** `architecture.type: token_set`, declaring `token_embed_dim`, the
aggregator block, and Q-head sizes. The type roster is never authored — it is compiled.
No-defaults throughout.

**Correction found during design:** the flat view keeps *vector* networks alive
(`feedforward`, `dueling` — unchanged, `obs_dim` = serialization width), but
`RecurrentSpatialQNetwork` cannot ride it: its CNN consumes the raster, which no longer
exists. **Recurrence is rebuilt token-native** — per-type encoders → aggregator → LSTM →
Q-head. The CNN's spatial prior is genuinely lost with the raster; this is a named
reversal trigger (below), and the reopening move would be a spatial-structure payload or
learned position encoding, never a raster revival.

**Deletions:** `StructuredQNetwork` (subsumed by per-type encoders; driven by zero packs —
verify at implementation) and `SetEncoderQNetwork` (superseded; `set_encoder_smoke`
re-authored as `variable_element` tokens under `token_set`).

**Provenance:** `brain_hash` mechanics unchanged. Checkpoints additionally stamp the
TokenSpec layout hash — token-net checkpoints compare on type schemas, flat-net checkpoints
require layout equality, both stated at load (the `PDR-0027` banner pattern; a checkpoint
missing the stamp raises, zero-backcompat).

## 5. Transfer, provenance, and the oracle

- **Hashes:** `observation_schema_hash` moves on every pack, once, at the cut.
  `variable_schema_hash`/`vfs_hash` move where engine-minted publisher variables change.
  `drive_hash` untouched.
- **The oracle cut needs a sharper comparison than "bytes match."** The adjudication
  criterion in one sentence: **tokens change what agents see, never what the world does.**
  Register entry DIV-008, written BEFORE the cut, splits the streams:
  - *Expected to diverge, registered:* observation streams on every cell, and everything
    downstream of a live policy.
  - *Required byte-exact AGREE:* world dynamics under **scripted** action sequences —
    state evolution, rewards, terminal conditions with actions forced.
  If the harness cannot drive scripted-action traces today, building that mode is a
  **prerequisite of the cut**: without it the matrix just reads "diverged," which
  certifies nothing.
- **Transfer is a tested contract:** compile two universes with disjoint vocabularies
  (different affordance sets, meter rosters, grid sizes), train-step a token net on one,
  load its weights into a net built for the other — must load by type and forward cleanly.
  The stronger claim — zero-shot *competence* on never-seen entities — is a research
  observation to record, **never** an acceptance criterion.
- **Docs:** "ask the compiled artifact, never quote a width" survives (`total_dims` =
  serialization width). CLAUDE.md observation sections, `docs/config-schemas/`, README
  claims all move at landing, at gate-2 standard.

## 6. Migration sequencing and test strategy

Implementation units, in dependency order — each lands green, each gets its own
implementation plan under this design:

1. **Scripted-action harness mode** — forced-action traces in the differential harness,
   verified all-AGREE on *current* code first. Prerequisite of adjudicability.
2. **The tick primitive** — engine-written `tick` VFS variable, referenceable from VFS
   expressions (ruling 6's dependency; coordinate with `hamlet-a737e444c0`, whose fix
   family overlaps).
3. **Register DIV-008, then the cut as one atomic knockdown:** TokenSpec replaces
   ObservationSpec, publishers replace sync steps, token-native net + flat view land
   together. No green half-state exists. Adjudicated per Section 5.
4. **Token-recurrent variant** — POMDP levels to tokens+LSTM; window machinery deleted;
   gridnd partial vision arrives.
5. **Pack migration** — `set_encoder_smoke` re-authored; L3 temporality becomes authored
   sin/cos variables; every shipped pack recompiles.
6. **Deletion sweep** — activity mask, raster/window encoders, temporal block,
   `StructuredQNetwork`, `SetEncoderQNetwork`; docs and README.

Follow-ons already scheduled outside this unit: relational/message tokens (discharges
`PDR-0107`), dynamic variables (`hamlet-424adcb84f`).

**Test strategy.** TDD throughout.

- Per token type, a **wiring test**: declare → that token row moves (the WS-3 mandate
  applied to each publisher).
- Permutation invariance re-pinned on the **mixed-type** set (extends `PDR-0112`'s tests).
- Presence tests distinguishing legitimately-zero from absent.
- Visibility-filter tests per substrate and boundary mode; wrap-aware egocentric features.
- The transfer-contract test (Section 5).
- Flat-view forward passes + layout-hash gates.
- Scripted-action differential: dynamics byte-exact across the cut.

## Reversal triggers (into the landing PDR)

1. **POMDP training materially degrades without the CNN spatial prior** — reopen the
   spatial representation; the move is a spatial-structure payload or learned position
   encoding, not a raster revival.
2. **A surface emerges with no natural token form** — `PDR-0044` trigger 3 stays armed for
   the reserved types (relation/message/group) and anything unforeseen.
3. **Padding/capacity waste bites** (large multi-agent counts, dynamic item populations,
   profiling evidence) — promote `hamlet-c586d520b2` (approach A: typed streams behind the
   TokenSpec).
4. **Two entities the agent must distinguish are payload-identical** in a real authored
   pack — reopens ruling 2 toward the hybrid (payload + learned tag) identity option,
   recorded as its own PDR.

## Verify-at-implementation (not design questions)

- Whether any production caller depends on `StructuredQNetwork` (expected: none).
- Whether VFS expressions can already reference an engine tick variable, or whether unit 2
  builds it (`hamlet-a737e444c0` adjacency).
- The exact set of engine-minted variables the publishers replace, and which hashes move
  beyond `observation_schema_hash`.
- The max position rank constant (chosen generously; document the number and the rule for
  changing it).
- Whether temporal *mechanics* (beyond observation) exist in the engine that ruling 6's
  observation change must leave untouched — this design touches observation only.
