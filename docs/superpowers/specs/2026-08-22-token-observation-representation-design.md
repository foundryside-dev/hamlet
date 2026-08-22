# Token Observation Representation — Design

**Status:** Design approved in-session by the owner, 2026-08-22, section by section; **revised
same day after a four-lens review** (systems / solution-architecture / PyTorch / DRL — findings
synthesized below under "Review amendments"). Awaiting owner review of the revised document
before implementation planning.
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
   owner rather than escalated later: the block has a natural token form because it
   dissolves into entities. (Section 1 and reversal trigger 2 record the known residual:
   walls/obstacles/zone boundaries are non-entity spatial structure with no token form yet.)
5. **Realization: approach C** — token rows serialized into the flat tensor in canonical
   TokenSpec order. Approach A (typed dict-of-streams transport) is captured, not lost:
   `hamlet-c586d520b2`, P4, extractable later *behind* the TokenSpec.
6. **No hardcoded temporality.** There is no `world` token type. The engine publishes one
   primitive — the tick — as an engine-written VFS variable; day/night, seasons, and phase
   are *authored* via VFS expressions (e.g. `sin(2π·tick/day_length)`) and observed as
   ordinary variable tokens. The `temporal` block was Townlet Town content frozen into the
   engine; it un-freezes.

## Review amendments (2026-08-22, four-lens review)

The first draft went to four independent reviewers: systems (second-order effects),
solution architecture (failure modes), PyTorch (mechanics), DRL (learnability). Verdict:
sound core, **not implementable as first written**. Five convergent defects, all fixed in
this revision:

1. **Capacity derivation was unspecified for runtime-dynamic types** and underivable for
   `agent` tokens (PyTorch blocker; SA high). Fixed: Section 2 now carries a per-type
   derivation table and a loud overflow rule.
2. **The oracle harness cannot express the DIV-008 stream split as it exists** — one
   registered shape, short-circuit on first mismatching stream (always frame-zero `obs`
   after a width change), shape preflight ahead of comparison (SA critical, code-verified
   in `src/townlet/oracle/trace_io.py`). Fixed: Section 6 unit 1 is now four harness
   changes, not one.
3. **RND/intrinsic exploration was unaddressed** — three of four lenses hit it
   independently: `RNDNetwork` consumes the activity mask this design kills
   (`exploration/rnd.py:75-106`), and presence-flip geometry makes token observations a
   novelty pump at the visibility boundary (the `PDR-0016` odometer shape). Fixed: new
   Section 3b.
4. **The declared-payload bucketing mechanism named a field that does not exist** —
   `MeterConfig` has no `semantic_type`, and the VFS one reserves a single value for all
   meters (systems blocker). Fixed: Section 1's effect-entry mechanism no longer references
   meter `semantic_type`; it uses recursive payload-signature identity.
5. **Reversal trigger 1 had no possible baseline** — zero shipped packs drive `recurrent`;
   L2/L3 run feedforward today (SA high; reframes the DRL blocker). Fixed: trigger 1
   restated against a baseline that will actually be taken, and the recurrent path's
   dark-ness is now stated where it justifies unit 3's atomicity.

Also folded in: quantified padding envelope and max-rank constant (SA high), checkpoint
gates *replaced* not supplemented (SA high), `ModuleDict`/roster policy/vocab-content
hashing (PyTorch), training-dynamical diagnostics and pooling-regime advisory (DRL),
per-type learned embeddings (DRL), the shipped-pack exercise requirement (systems), and a
set of implementation constraints in Section 6. Full review reports are in the session
record; findings not absorbed here were judged implementation-plan material, not design.

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
| `item` | one per world/carried item instance | `item_slots` (position/slot half) |
| `effect` | one per active observable effect | `effects` |
| `variable_element` | one per element of each exposed variable | `variable`, `item_slots` (state half), `temporal` (via authored variables) |
| *reserved names:* `relation`, `message`, `group` | — | `PDR-0107`'s exposure; later units |

Seven live types plus three reserved names. The reserved names mark intent only — they are
**not** settled shapes. `relation` in particular is dyadic (two entity references) and will
likely not fit the one-filler-per-slot binding model below; treat reversal trigger 2 as
*likely*, not merely possible, for it (systems review). Nothing in this unit builds them.

### Invariants

- **Payload width is fixed per token type, across all universes.** This is what makes the
  transfer contract literal: per-type network weights are shape-stable everywhere. Entity
  variation goes into token *count*, never payload width. A 30-affordance universe has 30
  affordance tokens, not a wider row.
- **The max position rank is an engine constant: `MAX_POSITION_RANK = 8`.** Position
  payloads are padded to it, with a rank feature. It covers every shipped and test
  substrate (2-D, 3-D, 6-D, 7-D). A pack declaring a substrate of rank > 8 is **refused
  loudly at compile time** — a documented limitation, like gridnd-POMDP used to be.
  Raising the constant changes every spatial payload width and breaks all checkpoints
  (by design — the vocab-content hash in Section 5 catches it); it is done by a
  superseding PDR, never quietly.
- **Tensor-shaped variables tokenize per element.** Payload = normalized element
  coordinates (padded to `MAX_POSITION_RANK`, rank feature) + the value. Scalars are the
  rank-0 case. Item state = `variable_element` tokens carrying an owner/slot coordinate.
  (Authored row-as-token layouts — heterogeneous declared columns — are NOT expressible in
  this unit; they are the dynamic-variables follow-on's territory, `hamlet-424adcb84f`.)
- **Identity = declared payload, applied recursively.** An affordance token's payload is
  its canonically-featurized declaration plus live state: `interaction_type` one-hot from
  its closed vocabulary; absolute position AND position-relative-to-self (egocentric —
  "standing on it" = relative zero, which is what deletes `affordance_at_position` as a
  block); and a fixed-size **effect summary** of k = 4 entries, each
  `(delta magnitude, sign, target signature)` for its k largest declared meter effects,
  where the **target signature is the target meter's own declared-parameter features**
  (its normalized bounds/decay descriptors — the same features the meter's own token
  carries). Identity-by-payload applied to the *reference* as well as the referent: the
  network can bind "this affordance raises the fast-decaying resource" to the meter token
  carrying that signature, with no name and no index anywhere. This REPLACES the first
  draft's "bucketed by the target meter's declared `semantic_type`", which named a
  granularity that does not exist (`MeterConfig` has no such field; the VFS `semantic_type`
  reserves one value for all meters). Fewer than k effects: entries absent-marked. More
  than k: the k largest by normalized magnitude, and the count carried as a feature.
- **Two payload-identical entities at the same position are genuinely the same** to the
  agent, and that is correct: if no declared parameter distinguishes them, no optimal
  policy can either (endorsed by the DRL review, F9). Reversal trigger 4 is the
  pre-registered exit if a real pack finds the counterexample.
- **Presence is explicit.** Every token row leads with a presence feature (1/0). This
  retires the all-zeros-means-empty heuristic from the unit-1 set encoder, which cannot
  represent a legitimately all-zero token. **Presence is mask-source only for token
  networks**: it is serialized in the row (the flat view sees it) but stripped before the
  per-type projection — payload width `W_t` excludes it. Mask derivation is
  `presence > 0.5`, never float truthiness; `key_padding_mask` stays bool.
- **Scale stays declared** (`PDR-0016`): every value feature passes through its
  variable's/meter's declared normalization before entering the token.
- **Known non-entity residual, pre-registered for trigger 2:** a raster also encodes
  *non-entities* — walls, impassable cells, zone boundaries. No shipped pack has them; the
  moment one does (L4 multi-zone), "where can I walk" has no token to live in and trigger
  2 fires on spatial structure itself. The reopening move is a spatial-structure payload
  or learned position encoding, never a raster revival. Recorded now so it is recognized
  on arrival, not rediscovered.

## 2. TokenSpec — the compiled artifact

`TokenSpec` **replaces** `ObservationSpec` as the compiler's product. Per compiled universe:

- **Type roster** — which types this universe instantiates, in engine-fixed canonical
  order.
- **Per type: payload schema** — feature names, order, normalization refs. An engine
  constant per type (the fixed-width invariant), embedded so the artifact is
  self-describing — never so universes can vary it.
- **Per type: compiled capacity and slot bindings** — N deterministic slots, each bound at
  compile time to its filler. Binding order is declaration order, stable, and hashed.

### Capacity derivation (per type, all from declared config — with one honest exception)

| Type | Capacity | Source |
|---|---|---|
| `self` | 1 | — |
| `meter` | count of declared meters | `bars.yaml` |
| `affordance` | count of placed affordance instances | `affordances.yaml` |
| `agent` | declared agents-per-world − 1 | see below |
| `item` | `max_items_in_world + max_items_per_agent × agents_per_world` | `items.yaml` (fields exist, required) |
| `effect` | `max_active_effects` — a **new required field** in `effects.yaml` | declared, No-Defaults |
| `variable_element` | Σ element counts of exposed variables | VFS declarations |

**The `agent` case is the honest exception the first draft hid** (PyTorch blocker, SA
high): today "how many agents share one world" is a runtime constructor argument, not
compiled config — `default_curriculum`'s population of 8 is 8 *independent* single-agent
worlds, so its `agent` capacity is **0** and the type is structurally absent there. The
rule: `agent` capacity derives from a **declared shared-world agent count** in pack config;
where no such declaration exists (all current single-world-per-agent packs), capacity is 0.
Locating or creating that declaration is a named item in unit 3's plan; if it requires a
new config field, that is admitted as new authoring surface — the first draft's "nothing
new to declare" was false in exactly two places (this and `max_active_effects`), and both
are now stated rather than smuggled.

**Overflow is loud.** A publisher asked to place more live instances than compiled
capacity **raises at publish time**, naming the type, the capacity, and its source. Silent
truncation would be a lying observation — the exact defect class this project treats as
debt. `VectorizedHamletEnv` construction refuses a `num_agents` that contradicts the
compiled capacity, same pattern.

### Serialization = the flat view

Rows concatenate in canonical type-then-slot order, presence leading each row:

```
total_dims = Σ_type  N_type × (1 + payload_width_type)
```

One layout, two readings: reshape-by-spec (token tensor) or read-as-is (flat vector). Said
plainly (SA M1): **the flat view is a supported second, universe-bound ABI this project
intends to carry**, guarded by the layout-hash gate — not a costless shadow of the first.
Its transfer contract (layout equality) is weaker than the token contract (type schemas),
and today's pack census (31 of 32 brains are `feedforward`/`dueling`) means most packs use
the weaker one until they opt in.

**Worked instance (ESTIMATE — exact table owed by unit 3's plan):** `default_curriculum`
L1 roster: 1 self + 8 meters + 14 affordances + 0 agents + 0 items + 0 effects + ~10
variable elements. With sketch widths (self ≈ 18, meter ≈ 8, affordance ≈ 34 — dominated
by the two rank-8 position blocks — variable_element ≈ 12), serialization lands ≈ **600
dims, roughly 5× today's ~120 allocated**, with the affordance position padding the
dominant term. This is stated up front because it is the number reversal trigger 3
watches; hiding it in implementation would be the risk-theatre the review called.

**What dies:** the activity mask (per-level variation is presence/capacity, not zeroed
dims — and its RND consumer is handled in Section 3b, not forgotten); the raster and
window encoders; the temporal block. `observation_schema_hash` is redefined over the
TokenSpec. `COMPILED_SCHEMA_VERSION` bumps; stale `.compiled` artifacts refuse loudly.

**What authors declare:** exposure (`exposed_to`), normalization, and semantic types as
today, plus the two admitted additions above (`max_active_effects`; the shared-world agent
count when multi-agent packs need it). Tokenization is derived from scope and shape;
capacities are compiler-derived per the table; `vision_range` keeps its meaning as the
visibility filter's radius.

## 3. Runtime encoding and the visibility filter

- **One publisher per token type**, dispatching on type — the `PDR-0076` discipline carried
  over. Engine publishers fill `self`/`meter`/`affordance`/`agent`/`item`/`effect`; the
  registry fills `variable_element` by declared scope, access control enforced as today,
  **batched per scope, never per-variable Python loops** (PyTorch F12). Each publisher is
  one vectorized op over its type's slot range in `[B, total_dims]`.
- **Presence ownership:** compile-time-static entities (meters, variable elements, self)
  publish presence 1. Runtime-dynamic entities (other agents, active effects, items)
  toggle presence as they exist. Dynamic slot assignment is unique-slot writes only —
  never scatter with possibly-duplicate indices (CUDA nondeterminism, PyTorch F10).
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

## 3b. Intrinsic exploration across the cut (RND)

Added at review — three of four lenses found this independently, and the project has one
measured prior incident of exactly this shape (`PDR-0016`: RND novelty 0.013 → 11,820 from
one observation-distribution change).

- **The consumer:** `RNDNetwork` (`src/townlet/exploration/rnd.py:75-106`) registers the
  activity mask as a static per-dimension buffer multiplied into every novelty forward.
  The mask dies; therefore **that constructor contract dies with it** — deleted, not
  defaulted to all-True. RND consumes the flat serialization directly.
- **The named risk:** presence flips are large discontinuous jumps in observation space.
  Under the visibility filter, RND novelty becomes partly a *visibility-churn detector*,
  and pacing the visibility boundary is a predictable intrinsic-reward pump. It also feeds
  the intrinsic-annealing gate (threshold 100.0, survival > 50).
- **The decision:** this design does not redesign intrinsic motivation. It instruments the
  change instead: (a) the cut's adjudication includes a **measured** intrinsic-reward
  distribution comparison on identical states pre/post cut — an expected divergence that
  is measured, never merely registered; (b) training diagnostics add per-step intrinsic
  reward vs presence-flip count, so visibility-boundary farming is *observable*; (c) if it
  then appears in training, it is preserve-and-document material in this project's spirit
  — an interesting failure is only valuable if the instrument to see it exists first.
- **Native token consumption for intrinsic modules** (per-token novelty vs pooled-embedding
  novelty) is a named follow-on question, not this unit's scope.

## 4. Network consumption and the flat view

**Token-native network** (successor to `SetEncoderQNetwork`):

1. Per-type projection encoders — `Linear(W_t → token_embed_dim)`, one per roster type,
   held in an **`nn.ModuleDict` keyed by token type name**, never a list indexed by roster
   position — with a list, roster differences re-bind weights to the wrong types and the
   load *succeeds silently* (PyTorch F6);
2. a **learned per-type embedding added post-projection** (type-keyed, so it transfers;
   closed roster, so it is fixed-size). Type identity must not depend on encoders
   happening to learn disjoint subspaces (DRL F2);
3. all tokens pooled into **one set** in the common embedding space;
4. the `PDR-0112` aggregator block verbatim — `{type: mean}` | `{type: attention,
   num_heads: N}`, declared, required;
5. Q-head.

**Why one mixed set rather than per-type pooling:** per-type pooling concatenated over the
roster would be immune to cross-type count dilution but hardcodes the assumption that
types never need to attend to each other — and the effect-summary → meter-signature
binding in Section 1 is exactly a cross-type attention pattern. Single-set is chosen *for*
that binding; the dilution cost is real and handled by the advisory below and by the PMA
escape hatch. (This paragraph exists because the review found the choice undefended.)

**Aggregator regime advisory (goes in `docs/config-schemas/brain.md` too):** `mean` suits
small rosters of behaviorally-distinct entities under full observability; it dilutes as
entity count and similarity grow — precisely the universes the transfer contract targets —
and `mean` + LSTM is the weakest configuration in the design space for POMDP.
`attention` is the expected choice for large/homogeneous/variable-count sets and POMDP.
This is authoring guidance, not a hidden default: both remain declarable, and "mean
degrades with scale" is legitimate teaching material. A **`{type: pma}`** member (learned-
seed cross-attention pooling, O(N), permutation-invariant, capacity-independent) is the
pre-named first upgrade if mean underperforms and attention's O(N²) bites — it extends the
`PDR-0112` block without reshaping anything.

**Masking mechanics (load-bearing, pinned here):** an absent token's zero row embeds to
LayerNorm's bias, **not** zero — output-side masking is what guarantees absent tokens
contribute exactly zero to the pool and receive exactly zero gradient, per aggregator
type. The all-empty unmask guard survives (a universe of only dynamic types is
expressible). Both are pinned by the test list in Section 6.

**`brain.yaml` surface:** `architecture.type: token_set`, declaring `token_embed_dim`, the
aggregator block, and Q-head sizes. The type roster is never authored — it is compiled.
No-defaults throughout.

**The recurrent path, corrected twice:** the flat view keeps *vector* networks alive
(`feedforward`, `dueling` — unchanged, `obs_dim` = serialization width), but
`RecurrentSpatialQNetwork` cannot ride it: its CNN consumes the raster, which no longer
exists. The review then established the sharper fact: **zero shipped packs drive
`recurrent` — L2/L3 run feedforward today** (config census: 26 feedforward, 5 dueling,
1 set_encoder, 0 recurrent). So the CNN prior being "lost" is the loss of an unexercised
path, and `RecurrentSpatialQNetwork` joins `StructuredQNetwork` on the
verify-then-delete list rather than being rebuilt like-for-like. **Recurrence is still
built token-native** (per-type encoders → aggregator → LSTM → Q-head) because POMDP needs
memory in principle — but unit 4's justification is forward-looking, not preservation, and
its baseline discipline is restated in trigger 1. This also supplies unit 3's missing
atomicity justification (SA M2): the recurrent path being dark across the unit-3/unit-4
boundary strands no shipped pack.

**Deletions:** `StructuredQNetwork` (subsumed by per-type encoders) and
`SetEncoderQNetwork` (superseded; `set_encoder_smoke` re-authored as `variable_element`
tokens under `token_set`). Both zero-pack-driven; verified at implementation.

**Provenance and load:** `brain_hash` mechanics unchanged. The existing checkpoint gates
`observation_dim` equality and `observation_field_uuids`
(`training/checkpoint_utils.py:71,78-84`) are **REPLACED, not supplemented** (SA H1 —
"additionally stamp" was the wrong verb under zero-backcompat): token-net checkpoints
compare on the TokenSpec **type-schema hash** — which hashes the payload-schema *contents*
including the closed-vocabulary members and `MAX_POSITION_RANK`, so a vocab bump produces
the banner, not a shape error (PyTorch F6.4) — and flat-net checkpoints compare on the
**layout hash**. `observation_field_uuids` dies with its producer. Roster mismatch at a
cross-universe load is **loud**: load the intersection of type keys, report both
directions (types dropped, types fresh-initialized), refuse on any payload-schema
mismatch. Cross-universe loads also **reset optimizer state, re-copy the target network
from the loaded online net, and reset RND predictor/normalizer state** (DRL F6) — decided
here, not ad hoc in the loader. And one epistemic sentence the docs must carry: per-type
encoders and the aggregator transfer as *feature extractors*; the Q-head transfers only
*mechanically* — its values encode the source universe's rewards and dynamics and must be
relearned. "What transfers" and "what is expected to help" are different claims.

## 5. Transfer, provenance, and the oracle

- **Hashes:** `observation_schema_hash` moves on every pack, once, at the cut. The
  **exact set of engine-minted publisher variables, and every hash that moves beyond
  `observation_schema_hash`, is enumerated in unit 3's plan before the cut** — promoted
  from "verify at implementation" because Section 5's own provenance claims depend on it
  (SA M4). `drive_hash` untouched.
- **The oracle cut needs a sharper comparison than "bytes match" — and the harness cannot
  currently express it** (SA C1, code-verified). `compare_traces` has one registered shape
  (hash-only), returns on the first mismatching stream — always frame-zero `obs` once
  `total_dims` moves, via a shape preflight that fires before byte comparison — and
  `DIVERGED_AS_REGISTERED` is reachable only when every stream matches. The adjudication
  criterion stands — **tokens change what agents see, never what the world does** — and
  unit 1 now builds the harness that can state it (four changes, Section 6). Register
  entry DIV-008, written BEFORE the cut, splits the streams:
  - *Expected to diverge, registered per-stream:* observation streams on every cell.
  - *Required byte-exact AGREE:* world dynamics under **scripted** action sequences —
    state evolution, rewards, terminal conditions with actions forced. (The honest
    rationale: the current driver draws actions from the global RNG, so there is no "live
    policy" in any trace — the real hazard is RNG-stream coupling: if the token path
    consumes global RNG differently, action sequences shift and dynamics diverge for a
    non-defect reason. Scripted actions remove that coupling.)
  - The scripted mode must live inside the **self-contained driver** rule
    (`oracle/driver.py` executes by file path in both interpreters, pinned by test) and
    is verified all-AGREE on current code before the cut — including a spot-check that
    current seeded-random traces are RNG-call-order stable (systems review).
- **Transfer is a tested contract:** compile two universes with disjoint vocabularies
  (different affordance sets, meter rosters, grid sizes), train-step a token net on one,
  load its weights into a net built for the other — must load by type (ModuleDict keys)
  and forward cleanly. **This test fails against the current checkpoint gates; their
  replacement (Section 4) is part of the same unit.** The stronger claim — zero-shot
  *competence* on never-seen entities — is a research observation to record, **never** an
  acceptance criterion. One recorded, non-gating experiment gives the headline empirical
  content: transferred-encoders-fresh-Q-head vs from-scratch sample efficiency on the
  target universe.
- **Docs:** "ask the compiled artifact, never quote a width" survives (`total_dims` =
  serialization width). CLAUDE.md observation sections, `docs/config-schemas/`, README
  claims all move at landing, at gate-2 standard.

## 6. Migration sequencing and test strategy

Implementation units, in dependency order — each lands green, each gets its own
implementation plan under this design:

1. **Harness adjudicability** — four changes, not one: (a) scripted-action trace mode
   inside the self-contained driver; (b) a stream-scoped registered-divergence shape
   (`RegisteredStreamDivergence`) beside the hash-only one; (c) non-short-circuiting
   per-stream adjudication so a registered `obs` divergence cannot mask the
   `rewards`/`dones` verdict; (d) a shape-preflight exemption for streams under a
   registered divergence. Verified all-AGREE on current code, plus the RNG-call-order
   spot-check.
2. **The tick primitive** — engine-written `tick` VFS variable, referenceable from VFS
   expressions (ruling 6's dependency; coordinate with `hamlet-a737e444c0`).
3. **Baselines, then register DIV-008, then the cut as one atomic knockdown.**
   *Baselines first:* the current shipped L2 configuration (feedforward over
   superset+mask with local window), ≥ 5 seeds, greedy-eval learning curves (survival,
   return vs env steps) committed as a frozen reference artifact beside DIV-008 — the
   raster dies at this unit, so the baseline is unrepeatable after it (DRL F1).
   *Then the cut:* TokenSpec replaces ObservationSpec, publishers replace sync steps,
   token-native net + flat view land together, checkpoint gates replaced. No green
   half-state exists (justified: the recurrent path is dark — zero packs). Adjudicated
   per Section 5.
4. **Token-recurrent variant** — POMDP levels to tokens+LSTM; window machinery deleted;
   gridnd partial vision arrives. **Definition of done includes the trigger-1
   comparison:** token-feedforward and token-recurrent (both aggregators) on L2 against
   the unit-3 frozen baseline, before unit 6 deletes anything.
5. **Pack migration** — `set_encoder_smoke` re-authored; L3 temporality becomes authored
   sin/cos variables; every shipped pack recompiles. **Acceptance includes the
   inert-guard: every live token type has N > 0 instances in at least one committed pack
   that compiles AND runs in the suite** — recompiling is not exercising, and `agent`/
   `item`/`effect` are all structurally empty in `default_curriculum` today (systems
   review). Where that requires populating or promoting a pack, that work is this unit's.
6. **Deletion sweep** — activity mask (and RND's dead constructor contract), raster/window
   encoders, temporal block, `StructuredQNetwork`, `SetEncoderQNetwork`,
   `RecurrentSpatialQNetwork`; docs and README. **Prerequisite: a token-table inspector
   exists** (dump one step's token set per agent, presence and payload labeled) — the
   raster was also the debugging view, and the first post-cut behavioral mystery must not
   be the moment that is discovered (DRL F8).

Follow-ons already scheduled outside this unit: relational/message tokens (discharges
`PDR-0107`), dynamic variables (`hamlet-424adcb84f`), native token consumption for
intrinsic modules (Section 3b).

**Test strategy.** TDD throughout.

*Structural:*
- Per token type, a **wiring test**: declare → that token row moves (the WS-3 mandate
  applied to each publisher).
- Permutation invariance re-pinned on the **mixed-type** set.
- Presence tests distinguishing legitimately-zero from absent, and the **exact-zero
  guarantee**: an absent token contributes exactly 0 to the pooled vector and receives
  exactly 0 gradient, per aggregator type (LayerNorm-of-zero is nonzero; the output mask
  is load-bearing — PyTorch F13).
- Visibility-filter tests per substrate and boundary mode; wrap-aware egocentric features.
- The transfer-contract test (Section 5), including roster-mismatch loudness.
- Flat-view forward passes + layout-hash gates.
- Scripted-action differential: dynamics byte-exact across the cut.
- Overflow: publisher raises loudly at capacity + 1.
- Replay aliasing: store two consecutive ticks, assert they differ (preallocated-buffer
  hazard — PyTorch F2.2).

*Training-dynamical diagnostics (recorded during training runs; the structural suite
passes green while training quietly degrades without these — DRL F4):*
- Per-type encoder gradient norms and update magnitudes (dead rare-type encoders).
- Cold-token injection: bounded Q-perturbation when a never-seen-in-training token
  toggles present.
- TD-error distribution conditioned on presence-flip count between s and s′
  (count-normalization discontinuity).
- Pooled-embedding norm and online-vs-target cosine drift (representation drift under
  pooling symmetry).
- Intrinsic reward vs presence-flip count (Section 3b).
- One **learning** probe comparing mean vs attention on a navigation task — also services
  `PDR-0112`'s "declaration went inert" trigger.

**Implementation constraints (from the PyTorch review; carried here so every unit plan
inherits them):** publisher write targets use `.view()` (raises on copy), never
`.reshape()`; stored observations are `.clone()`d or per-tick allocated; the token-
recurrent forward folds `[B, S, ·]` → `[B·S, ·]` through encoders+aggregator and runs
**one** `nn.LSTM` call over the sequence (the per-timestep Python loop is rollout-only);
attention uses explicit QKV + `F.scaled_dot_product_attention` with the math backend
pinned where byte-exact training replay matters; masks are bool; no LayerNorm/Linear over
concatenated set width anywhere in the token path (it would silently break the transfer
contract); the packed single-GEMM encoder form is permitted later only if the checkpoint
format stays per-type.

## Reversal triggers (into the landing PDR)

1. **POMDP learnability regression — now measurable:** token-feedforward and
   token-recurrent (both aggregators) on L2 fail to reach **≥ 80% of the unit-3 frozen
   baseline's final greedy survival within the same env-step budget** (seed-level IQM,
   non-overlapping CIs to claim regression). Fires → reopen the spatial representation
   (spatial-structure payload or learned position encoding, not a raster revival). The
   80% figure is the landing PDR's to re-argue; a trigger without a number cannot fire.
2. **A surface emerges with no natural token form** — `PDR-0044` trigger 3 stays armed.
   Pre-registered first candidates: walls/obstacle/zone structure (Section 1), and the
   dyadic `relation` shape (Section 1's reserved-names caveat).
3. **Capacity/padding cost bites, with numbers:** a shipped pack's serialization exceeds
   **8× its pre-cut allocated width**, or observation encoding exceeds **25% of
   `env.step` wall time**, or recurrent-attention training memory forces `batch_size`
   below the pack's declared value. Fires → promote `hamlet-c586d520b2` (approach A:
   typed streams behind the TokenSpec), and/or land `{type: pma}`.
4. **Two entities the agent must distinguish are payload-identical** in a real authored
   pack — reopens ruling 2 toward the hybrid (payload + learned tag) identity option,
   recorded as its own PDR.

## Verify-at-implementation (not design questions)

- Whether any production caller depends on `StructuredQNetwork` or
  `RecurrentSpatialQNetwork` (expected: none — config census found zero packs driving
  either).
- Whether VFS expressions can already reference an engine tick variable, or whether unit 2
  builds it (`hamlet-a737e444c0` adjacency).
- Where the shared-world agent count should be declared (unit 3 names the field or
  confirms capacity-0 everywhere).
- Whether the `variable_element` registry fill path is already batched per scope.
- Whether temporal *mechanics* (beyond observation) exist in the engine that ruling 6's
  observation change must leave untouched — this design touches observation only.
- The exact per-type payload widths `W_t` (the Section 2 worked instance is an estimate;
  the unit-3 plan carries the exact table and the real `total_dims`).
