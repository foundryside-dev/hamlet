# PDR-0007 — Universality and configurability are the default; "should we implement it" is usually "yes, and expose it as config"

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: yes (owner stated the principle directly)
Related: PDR-0005 (generalises its wire-not-delete default), PDR-0006, metrics.md (Config-surface coverage), roadmap.md

## Context

`PDR-0005` established **wire, not delete** as the default for inert config surfaces, justified
narrowly: deleting an accidental drop converts an accident into a permanent decision. The owner
then generalised it into a standing product principle:

> *"as a guiding principle consider that we generally want to aim for universality and
> configurability — if it comes down to 'should we implement' the answer is often 'yes, and expose
> it as a config option' — partial observation in nd space isn't a design decision, it's an option
> we haven't enabled yet."*

The worked example is precise. Trial 001 (the 6-D Sims universe) hit exactly one wall: gridnd
rejects partial vision. Three framings of that wall were available — a *limitation to document*, a
*design decision to respect*, or **an option not yet enabled**. Only the third is correct here, and
`TASK-009-ND-POMDP` (*Status: Planned, Completed: [Not started]*) proves it: the capability was
specified and simply never built.

## Options considered

1. **Keep wire-not-delete as a narrow archaeology rule** (PDR-0005 as written) — pro: tightly
   evidenced, low risk of scope explosion. Con: it only fires where a written trace exists, so it
   is silent on never-specified surface — which is where most of the "should we implement this?"
   questions actually arise.
2. **Adopt universality-and-configurability as a general default** — pro: matches the product
   thesis directly; a substrate whose promise is *"you can also make anything else you can think
   of"* cannot answer most capability questions with "no". Con: unbounded "yes to everything" is
   how a project never ships, and — critically — it is *how this codebase got into its current
   state*.
3. **Adopt the default, paired with a mandatory wiring obligation** — the same bias toward yes,
   with the cost of "yes" stated honestly.

## The call

**Option 3.** Universality and configurability are the default. When the question is *should we
implement this*, the answer is usually **yes, and expose it as a config option**. Capability gaps
are presumed to be **options not yet enabled** rather than decisions taken, unless a decision is
on the record.

This generalises `PDR-0005`'s wire-not-delete from an archaeological inference to a product
principle. It also reclassifies the ~40 declared-but-inert fields: most are not mistakes, they are
**options nobody got to**. That is a materially different — and more optimistic — reading of the
codebase than the maturity assessment's framing, and it is consistent with pattern P4 (inertness
tracks recency, not quality).

### The obligation that makes it safe

**If you expose it, you wire it and you test it. Exposure without wiring is not a smaller version
of the feature — it is a lie.**

This must be stated because *universality applied without the wiring discipline is the exact
mechanism that produced the current mess.* Someone reasoned "we should support N-dimensional
grids / arbitrary effect scopes / configurable recurrent encoders" — correctly, per this
principle — declared the schema, and then ran out of time before wiring the runtime. The result is
~40 fields that validate, are documented, and do nothing, in a product where the author has no way
to detect the difference. The principle is right; unpaired, it is the disease.

So the rule has two halves and they ship together:

1. **Bias to yes** — implement it and expose it as config.
2. **Definition of done** — the option is authored in a config pack at a non-default value, driven
   through to observable runtime behaviour, and pinned by a config-in/behaviour-out test (WS-3).
   Until all three hold, the option does not exist and its schema field must not ship.

### The limiting principle

The constraint on "yes" is **coherence of the grammar**, not appetite or effort. An option that
composes with the existing vocabulary should be exposed. An option that requires a special case in
the runtime — a branch on a domain name, an escape hatch past the compiled contract — is a
different question and is presumptively **no**, because it breaks the property that makes the
substrate universal in the first place. The existing invariant test asserting `vectorized_env.py`
contains no domain tokens is the concrete form of this limit.

Effort is not a reason to refuse; incoherence is.

## Rationale

Option 3 beat option 1 because the narrow rule cannot reach the cases that matter most — the ones
with no written trace, which the owner's own example (`ND-POMDP`) shows are routinely
capability-gaps rather than decisions.

It beat option 2 because an unqualified bias-to-yes has already been run as an experiment on this
codebase, and the result is in `metrics.md`: ~40 inert surfaces and a Config-surface coverage of
~2 of 7. Adding the definition-of-done is what converts the principle from the thing that caused
the problem into the thing that fixes it. Under a strangler strategy (`PDR-0006`) this is
affordable, because the differential harness makes "wired and tested" mechanically checkable rather
than a matter of diligence.

## Consequences

- **WS-2 (deletion) narrows again.** Items listed for deletion should be re-read as candidates for
  *enabling*. Genuinely dead code (`ActionSpaceBuilder` loading a file that no longer exists) still
  goes; unbuilt options do not.
- **WS-4 grows and is reframed** — from "close the gaps" to "enable the options", with
  `TASK-009 ND-POMDP` as the exemplar.
- **The target spec should be written for the widest coherent grammar**, not the current one.
- **`metrics.md` Config-surface coverage becomes the principle's scoreboard** (~2 of 7 → 7 of 7).

## Reversal trigger

Reopen this PDR if **any** of the following:

- The inert-surface count **rises** after this principle is adopted. That means the definition-of-
  done is not being enforced and the principle has reverted to its harmful form. This is the
  specific failure to watch and it is measurable in `metrics.md`.
- Enabling options is consistently starving the recovery of capacity — universality is worth less
  than a substrate that works, and the sequencing call would then belong to
  `/axiom-program-management`.
- An option is found that is coherent, wanted, and genuinely cannot be expressed without a runtime
  special case. That would mean the grammar itself is inadequate, which is a vision-level question
  about the expressible problem space and escalates to the owner.
