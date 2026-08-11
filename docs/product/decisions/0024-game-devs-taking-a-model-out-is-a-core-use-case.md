# PDR-0024 — Game devs prototyping and taking a trained model out is a core use case; `vision.md`'s audience needs amending

Date: 2026-08-12   Status: **proposed** — the `vision.md` amendment requires owner sign-off. The *recording* of the use case is accepted.
Author: Claude (standing product owner)
Owner statement: *"a core usecase is game devs rapidly throwing a prototype together here, getting a model and an interface contract and take the model to their own game code trained on a simplified version of the same scenario."*
Related: PDR-0006 (strangler / provenance spine), PDR-0008 (provenance breaches), PDR-0017 (token observations), PDR-0007 (options not yet enabled)
Prior art in repo: `docs/tasks/TASK-008-MODEL-ABSTRACTION-AND-EXPORT.md` — **Status: Planned**, created 2025-11-05, never built

## Context

`vision.md`'s *Who it serves* names four audiences: the sole researcher/builder (primary), other
RL researchers (secondary), the **aspirational novice author** (the standard the substrate is
judged by), and students/instructors (downstream).

The novice author is close to the owner's use case but stops one step short. `vision.md` has
them *"express it as a universe and watch agents attack it"* — **the journey ends inside
HAMLET.** The owner's game dev finishes somewhere else: they leave with a **model** and an
**interface contract**, and integrate both into their own engine.

That handoff step appears nowhere in `vision.md`.

## Why this is a strategy-level addition, not a detail

It changes what "done" means for the product. Today, done is *a running gym you authored*. Under
this use case, done is *a portable trained artifact plus a contract stable enough to code
against in a different codebase.*

Three things follow immediately.

**1. It re-values the provenance spine as the product surface.** The "interface contract" is not
a new artifact to invent — it is `observation_schema_hash` + `action_schema_hash` + the field
UUIDs and action vocabulary they cover. WS-1 has been treating those as *internal correctness*.
Under this use case they are **what the customer leaves with**. That materially raises the value
of work already committed and in flight, and it is the strongest argument yet for finishing the
provenance stream properly rather than declaring it green early (`PDR-0021`).

**2. The export path is designed and unbuilt.** `TASK-008` specifies exactly this — a standalone
`HamletModel`, an inference checkpoint format, ONNX export, *"portable checkpoints (~10MB vs
~50MB)"* — and has sat at **Planned** since 2025-11-05. `grep` finds no export entry point in
`src/townlet/` beyond video export. So this use case is **not served at all today**: a trained
model cannot leave without dragging `VectorizedPopulation`, curriculum and exploration with it.

Note also that `TASK-008` declares *"Breaking Changes: No (backward compatible with v2 training
checkpoints)"* — written before `PDR-0012`, and an antipattern under the zero-backcompat rule.
The task needs re-specifying, not just scheduling.

**3. It sharpens `PDR-0017`.** A contract a game dev codes against is easier to satisfy the less
it hardcodes about one universe. A fixed 124-dim vector with a fixed 14-affordance vocabulary is
a *brittle* contract to carry into a different game; a token/set observation is a portable one.
`PDR-0017` argued the token direction on strangler grounds. This use case gives it a second,
independent justification — and the two agree.

**What this use case does NOT change.** *"Trained on a simplified version of the same scenario"*
is transfer learning, and the substrate was already built for it: constant `obs_dim` across grid
sizes, a global action vocabulary shared by every level, checkpoint transfer as a stated design
goal. That part of the design anticipated this user correctly.

## The call

**Two parts, deliberately separated.**

**Accepted (within grant):** the use case is recorded here, and the consequences above are now
inputs to sequencing. Specifically — the provenance stream is finished properly rather than
declared green (`PDR-0021` already so decided, and this strengthens it), and `TASK-008` is filed
as a tracked, re-specified gap rather than left as a 2025 planning document.

**PROPOSED — needs owner sign-off:** amend `vision.md`'s *Who it serves* to name this audience,
and extend the novice-author entry so the journey includes the handoff. `vision.md` is ENDORSED
and is **not** edited by this PDR.

Suggested shape, for the owner to accept, alter or reject:

> **The prototyping game developer** — someone with an existing game who wants an agent for a
> mechanic in it. They author a *simplified* version of their scenario, train against it, and
> leave with a **model and an interface contract** they can code against in their own engine.
> HAMLET is the harness, not the destination. Every barrier between "it trains here" and "it
> runs in my game" is a defect against this user.

## Rationale for escalating rather than deciding

The authority boundary puts vision and strategy on the owner's side of a one-way door, and this
is squarely that: it adds an audience whose success criterion (*the model runs in my engine*) is
not currently measured by anything in `metrics.md`. The north-star measures **authoring** cost.
It does not measure **export** cost, and under this use case a product could score perfectly on
the north-star while being useless to a game dev — they could author it beautifully and still
not get it out.

Whether that means a second north-star input, or whether export is subordinate to authoring,
is exactly the kind of call I should not make unilaterally.

## Reversal trigger

Reopen (or reject the proposal) if **any** of the following:

- **The owner judges this a variant of the novice author** rather than a distinct audience. Then
  no `vision.md` change is needed and the export gap is simply a roadmap item.
- **`TASK-008`'s export path turns out to be blocked by the rebuild.** If the model abstraction
  needs the strangler's later stages, sequencing it early is wasted work and it should follow the
  oracle freeze.
- **No measurable export barrier survives contact with a real attempt.** If someone extracts a
  model and integrates it without hitting a wall, the gap is smaller than the missing entry point
  suggests, and this drops in priority accordingly.
