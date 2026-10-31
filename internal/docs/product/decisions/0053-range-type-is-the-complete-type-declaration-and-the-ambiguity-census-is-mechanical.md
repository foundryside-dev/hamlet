# PDR-0053 — `range_type` becomes the complete type declaration, and the ambiguity hunt is a mechanical census rather than a reading

Date: 2026-08-15   Status: **accepted** (owner-made ruling on the fork; the census method and its
first results are within grant — a measurement, no code behaviour changed)
Author: Claude (standing product owner)
Owner sign-off: **yes**, on both halves:

> *"a - the system likely has more ambiguities, this strangulation exercise is our chance to
> clean them all up"*

Resolves: `PDR-0052`'s open fork, in favour of **(a)**
Related: `PDR-0045` (name-blind), `PDR-0047` (closed vocabularies), `PDR-0052` (completeness),
`PDR-0049` (a defect counts only if it executes), `PDR-0051` (Trial 002), `PDR-0019` (the
knockdown criterion), `PDR-0006` (strangler)
Tracker: `hamlet-2090c9f16d` (P0 — oracle inputs, gates the stream), `hamlet-3d3039f340`,
`hamlet-365e996511`, `hamlet-2fe1c34ebb`, plus issues filed by this PDR
Artifact: `scripts/audit_declaration_census.py` — the census is a script, re-runnable, not a
one-off sweep

## Part 1 — the fork is settled: (a)

`range_type` becomes the **complete type declaration** for a meter: a closed, *parameterized*
vocabulary where each member fully determines its own required parameters, and omitting them is
the compile error `PDR-0052` mandates. Not a new required field beside `range_type`.

The reasoning is recorded in `PDR-0052` and stands: the owner said *"if a **type** is
underspecified"* — the unit declared is the type — and option (b) would have walked into
`PDR-0047`'s own second reversal trigger, with ~100 of 108 meters writing an identical
`kind: minmax` whose parameters are already implied by declared bounds. It also folds
`hamlet-365e996511` in rather than leaving `range_type` inert beside its replacement.

## Part 2 — "the system likely has more ambiguities" is a measurable claim, so measure it

The owner's second clause is the larger instruction, and the trap is obvious from this session's
own history: `PDR-0049` had to strike two of two grep-found defects because neither executed, and
deflate a metric that *"had inflated itself by exactly the mechanism it exists to catch."* A hand
enumeration of "ambiguities" would repeat that at scale.

**So the census is mechanical.** For each closed-vocabulary declaration, change one value to
another *legal member of its own vocabulary*, recompile, and record which of the five provenance
hashes move. Nothing else changes, so any difference is attributable to that declaration alone.

Two design rules make it evidence rather than a count:

1. **Buckets are assigned in the script, before any result is seen.** A declaration is either
   `structural` (it claims to describe something the compiled artifact should encode) or
   `control` (it legitimately affects runtime or presentation only). Assigning buckets after
   seeing results is precisely how a static sweep launders itself into a measurement.
2. **Controls test the prober, not the tree.** A control that moves a hash means the prober's own
   reasoning is wrong. Both controls (`labels.preset`, `population.size`) moved nothing, as
   predicted — so the instrument is calibrated, and the six `structural` fields that *did* move
   hashes show it is not trivially reporting silence.

**"Moves no hash" is not "inert", and conflating them would be this session's mistake a third
time.** Every candidate therefore gets a second leg: does the declaration change *behaviour*?
That distinction produced the most important finding below.

## The first census — 13 probes on `default_curriculum:L1_full_observability`

| declaration | bucket | hashes moved | verdict |
|---|---|---|---|
| `grid.observation_encoding` | structural | observation, vfs, variable | ✅ encoded |
| `grid.diagonals` | structural | action, vfs | ✅ encoded |
| `observation_mode.mode` | structural | observation, vfs, variable | ✅ encoded |
| `temporal_support` | structural | observation, vfs, variable | ✅ encoded |
| `variables[].scope` | structural | vfs, variable | ✅ encoded |
| `curriculum.active_vision` | structural | observation, vfs | ✅ encoded |
| `vision_support` | control | *rejected* | ✅ gates validity by design (`VISION_INCOMPATIBLE`) |
| `labels.preset` | control | none | ✅ control as predicted |
| `population.size` | control | none | ✅ control as predicted |
| **`grid.boundary`** | structural | **none** | ⚠️ **live behaviour, absent from provenance** |
| **`grid.distance_metric`** | structural | **none** | ⚠️ **live behaviour, absent from provenance** |
| **`meters[].range_type`** | structural | **none** | ⚠️ **inert** (`PDR-0051`) |
| **`variables[].normalization.method`** | structural | **none** | ⚠️ **vocabulary collision + a member that lies** |

> ⚠️ **FINDING A IS WITHDRAWN — it was FALSE, and the census method that produced it is
> downgraded. Corrected 2026-08-15, same day, before any work started; original text kept below
> per the `PDR-0020` practice so the error stays legible.**
>
> **`boundary` and `distance_metric` ARE hashed** — both move `stratum_hash`. The headline claim
> ("a torus and a walled box are checkpoint-interchangeable") is wrong; provenance guards that
> transfer correctly today. `hamlet-7b126ad3fa` is closed **not_a_bug**.
>
> **The cause was the instrument.** The census compared five hand-picked hash fields;
> `CompiledUniverse` has **sixteen**. `stratum_hash` was not in the list, so a declaration hashed
> only there read as hashed nowhere. `driver.py` had this right all along
> (`collect_provenance_hashes` reflects over every `*_hash` field) — the script did not.
>
> **And widening it exposed that the method was weak, not merely mis-parameterised.** With all 16
> compared, the *controls* move hashes too, because there are two families and this PDR conflated
> them:
> - **RAW** (`stratum_hash`, `environment_hash`, `actions_hash`, `training_hash`, …) —
>   `_compute_pydantic_hash` over a whole config file, so **every** declared value in that file
>   moves it by construction. Proves provenance, never comprehension.
> - **DERIVED** (`observation_schema`, `action_schema`, `vfs`, `variable_schema`,
>   `transition_graph`) — what the compiler actually built.
>
> Under that split, `boundary`/`distance_metric` move a raw hash and no derived hash — which is
> **correct**: they change dynamics, and no derived schema describes dynamics. The "structural"
> bucket assignment for them was simply wrong.
>
> **This PDR's own second reversal trigger has therefore fired** — *"reverse the census method if
> the structural/control bucketing turns out to be the real judgement call"*. It did.
> `audit_declaration_census.py` no longer emits verdicts; it prints a **map split by hash family**
> and stops, because *"should this declaration reach a derived artifact?"* is a judgement about
> intent that no perturbation can settle.
>
> **Unaffected:** Finding B (`hamlet-1dba1910c0`) was measured on compiled `NormalizationSpec`
> equality and on `apply_normalization`'s behaviour, **not on hashes**, and stands.
> `range_type` also stands — it moves `environment_hash`, reaches no derived artifact, and Trial
> 002 measured its behavioural inertness directly.
>
> **The lesson, and it is the third time this session:** `PDR-0049` said a red found by reading is
> not a defect until it executes. This adds the sharper case — **a red found by a tool is not a
> defect until the tool is validated against something you already know the answer for.** The
> controls existed and were the right idea; they were just too weak to catch a truncated hash list.

### Finding A — two declarations change the world and enter no hash

`boundary: clamp → wrap` and `distance_metric: manhattan → euclidean` move **none** of the five
hashes. Leg 2 says they are **not inert** — both work:

- **boundary**: on an 8×8 grid, an agent at `(0,3)` under `clamp` reaches
  `{(0,2),(0,3),(0,4),(1,2),(1,3),(1,4)}` in one step; under `wrap` it also reaches
  `{(7,2),(7,3),(7,4)}`. Toroidal topology, working.
- **distance_metric**: `compute_distance((0,0),(3,4))` returns `7` under manhattan and `5.0`
  under euclidean.

**So this is a worse defect than inertness, not a lesser one.** Two packs describing genuinely
different worlds — a torus and a walled box — compile to **byte-identical provenance hashes**. A
checkpoint trained on the torus loads cleanly into the box with nothing to detect it. Provenance
hashes exist to make exactly that impossible. This is a new shape the taxonomy did not have, and
it was only visible because the census separates "moves a hash" from "changes behaviour".

### Finding B — `clip` and `normalize` are the same thing, and `clip` does not clip

`normalization.method` has four declared members (`clip`, `normalize`, `standardize`, `none`).
Measured:

- `none` is **rejected** at compile time (correctly, under No-Defaults).
- `clip` and `normalize` compile to **byte-identical** `NormalizationSpec(kind='minmax',
  min=0.0, max=1.0)`. Two names, one behaviour — an author choosing between them believes they
  are choosing something.
- And `minmax` is `(v - min) / (max - min)` — **pure rescaling, no clamping.** Declaring
  `method: clip, range: [0.0, 1.0]` and feeding `[-5.0, 0.0, 0.5, 1.0, 7.0]` returns
  `[-5.0, 0.0, 0.5, 1.0, 7.0]` — unchanged, unclipped, out of range.

**A vocabulary member that does not do what its name says is the sharpest form of the ambiguity
the owner is asking to clean up** — worse than an inert field, because the author's intent was
expressible, was expressed, and was silently discarded in favour of a different operation. It is
also `PDR-0045`'s lesson arriving from the opposite direction: there, the *compiler* read meaning
into a name; here, the *author* reasonably reads meaning into a name and the compiler ignores it.

## The taxonomy, derived from measured instances only

Six shapes, each with at least one confirmed in-tree instance:

| # | shape | confirmed instance |
|---|---|---|
| 1 | **Inert declaration** — accepted, drives nothing | `range_type` (`PDR-0051`) |
| 2 | **Live but unhashed** — changes behaviour, absent from provenance | `boundary`, `distance_metric` (this PDR) |
| 3 | **Vocabulary collision** — two members, one behaviour | `clip` ≡ `normalize` |
| 4 | **A member that lies** — behaviour contradicts the name | `clip` does not clip |
| 5 | **Silent discard** — declaration accepted then dropped | `variables_reference.yaml` normalization (`PDR-0051`) |
| 6 | **Unreachable vocabulary** — implemented, not selectable | 8 of 10 normalisation kinds (`hamlet-3d3039f340`) |

Plus two already recorded and owned elsewhere: **hidden default** (`default="custom"`,
`hamlet-2fe1c34ebb`) and **compiler emits outside the declared set** (`"effects"`, same issue).

## Coverage — stated honestly

This census probed **13 declarations in one pack at one level**. It does **not** cover: items,
effects, drive/DAC, brain, cascade and modulation graphs, the non-grid substrates, or any
`Literal` that is a discriminated-union tag (perturbing those selects a different model rather
than a different value, so they need a different probe). `scripts/audit_declaration_census.py`
exists so extending coverage is adding rows to a list, not repeating an investigation.

**No total is quoted on purpose.** "N ambiguities" is the number `PDR-0049` had to deflate; the
deliverable is the per-field table with its bucket, its verdict, and what was not probed.

## Consequences

1. **The (a) ruling closes `hamlet-3d3039f340`'s design gate** and subsumes `hamlet-365e996511`.
2. **Finding A is filed** — `boundary` and `distance_metric` must enter the provenance hashes.
   Note this is hash-moving in the strict `PDR-0037` sense and interacts with the oracle-input
   gap (`hamlet-2090c9f16d`), which still gates everything.
3. **Finding B is filed** — the `normalization.method` vocabulary must be reduced to distinct
   members whose behaviour matches their names, under `PDR-0047` rule 1. This is a live
   correctness bug for any author who declared `clip` expecting clamping.
4. **The census script is in-tree** (`scripts/audit_declaration_census.py`) and re-runnable. It
   is a candidate CI gate once the fields are fixed: a structural declaration that stops moving
   its hash is a regression, and this catches it mechanically.
5. **The strangler now has a mechanical unit-finder.** `PDR-0019` asks *"where does the runtime
   still know what the game is?"*; this census answers the adjacent and equally useful question
   *"where does the compiler not know what the author said?"* — and answers it with a script
   rather than an opinion.

## Reversal trigger

- **Reverse (a)** if a meter legitimately needs two independent type facts that cannot be folded
  into one parameterized `range_type` member without inventing a member per combination — the
  combinatorial blow-up is the signal that (b) was right after all.
- **Reverse the census method** if the structural/control bucketing turns out to be the real
  judgement call — i.e. if reviewers routinely disagree about which bucket a field belongs in.
  Then the census is measuring the bucketer, not the tree, and the fix is probing behaviour
  directly rather than hashes.
- **Re-open finding A's classification** if `boundary`/`distance_metric` turn out to be
  deliberately excluded from provenance for a reason recorded somewhere I did not find. The
  measurement stands either way; only the verdict would change.
- **Do not let the census become a count.** If a future session reports a total instead of a
  table, that is the `PDR-0049` failure recurring and the number should be discarded.
