# PDR-0027 — `brain.yaml` becomes level-overridable, and a lineage fork must be legible before you load it

Date: 2026-08-13   Status: **accepted**
Author: Claude (standing product owner)
Owner statement: *"Overridable is the obvious answer, but at the same time that creates other
complexity - if you override a brain your experiment isn't compatible with others of the same
lineage anymore, which is fine but we need a way to make that obvious - I shoulnd't be
downloading/loading an experiment and then finding out its not what I thought it was."*
Resolves: the design fork inside `PDR-0009`
Related: `PDR-0017` (token observations — first consumer), `PDR-0018` (curriculum authoring —
second consumer), `PDR-0024` (the interface contract — what a consumer leaves with)
Tracker: `hamlet-0d0115383e` (re-scoped by this)

## Context

`PDR-0009` established that per-level `architecture` selection is unauthorable — no pack can
express the documented MLP→LSTM curriculum progression — and left a design fork open: add a
per-level `architecture` override field, or make `brain.yaml` level-overridable the way
`training.yaml` already is. The fork accumulated three consumers before being decided.

## The call

**Two halves, both owner-stated, and the second is the interesting one.**

**1. `brain.yaml` becomes level-overridable the way `training.yaml` is.** The general door,
not a one-field special case — consistent with `PDR-0007` (universality as the default: build
the general mechanism, let packs opt in). A level that says nothing inherits the pack brain
unchanged.

**2. Overriding a brain forks the lineage, and the fork must be legible at load time — not
discovered at runtime.** The owner accepts the incompatibility itself (*"which is fine"*); what
is not acceptable is the silent version: downloading or loading an experiment and finding out
mid-use that it is not what you thought. This is a **new acceptance criterion**, not a caveat:

> An experiment artifact whose effective brain diverges from its pack baseline must carry that
> fact visibly, and every loader must surface it **before** the artifact is used.

## What "legible" means here (direction, not prescription)

The detection half already exists: WS-1 task 4 (`31c17111`) made `brain_hash` cover the
**effective** config at the primary level, so a per-level override *will* move the hash — the
provenance spine notices the fork by construction. The gap this PDR names is **presentation of
that fact to a human**: a hash mismatch deep in a load path is detection; "this experiment's
brain diverges from lineage X at level Y" surfaced at load/download time is legibility. The
implementer decides the mechanism (stamped metadata field, manifest line, loader banner);
the criterion is that no one learns about a fork by observing wrong behaviour.

Note the convergence with `PDR-0024`: the interface contract is *what the customer leaves
with*, and lineage identity is part of that contract. A game dev or simulation builder pulling
a trained model needs "what exactly is this?" answerable from the artifact alone.

## Sequencing (unchanged from `PDR-0009`)

After WS-1(b)/(c). Enabling recurrent authoring while the recurrent training path trains
memoryless (WS-1(b)) would ship an option whose observable behaviour is wrong — the worst kind
of authorable surface.

## Consequences

- **`hamlet-0d0115383e` is re-scoped** to two deliverables: (1) level-overridable `brain.yaml`
  via the same merge path `training.yaml` uses; (2) the lineage-legibility criterion above,
  testable as "load a forked experiment, see the fork stated."
- **`hamlet-fa6bb6da4a`** (token observations) remains blocked by it, unchanged.
- **The Mind-authoring metric row** (`metrics.md`) gets its path: Layer 2 goes from
  "pack-scope only" toward per-level, measured by whether the documented MLP→LSTM progression
  becomes expressible in config.
- **A latent tension is on record**: `vision.md` lists checkpoint transfer across universes as
  part of the preset grammar's value. Per-level brain forks are the first deliberate,
  first-class way to *break* transfer within a pack. The resolution is exactly the legibility
  criterion — transfer-compatibility becomes a stated property of an artifact rather than an
  assumed one.

## Reversal trigger

Reopen if **any** of the following:

- **Authors fork lineage accidentally in practice** — the marker exists but people still load
  forked experiments unknowingly. Then the legibility *mechanism* failed its criterion and
  needs redesign; the override itself is not the defect.
- **The general merge path proves unable to express the progression** (e.g. architecture
  changes need structure the override merge cannot carry) and a dedicated per-level
  `architecture` field turns out to be needed after all — the fork reopens with evidence.
- **Effective-`brain_hash` turns out not to move under some override** — then detection itself
  is broken (a `brain_hash` false negative, the exact class task 4 fixed), and that is a WS-1
  shaped provenance defect, not a feature gap; it routes per `PDR-0028`.
