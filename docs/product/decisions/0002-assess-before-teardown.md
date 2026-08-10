# PDR-0002 — Recovery is the Now bet, and a maturity assessment gates it

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: yes (owner directed the recovery framing and the assessment-first sequence in-session)
Supersedes: —   Related: PDR-0001, roadmap.md (Now), metrics.md (Subsystem maturity established)

## Context

PDR-0001 set the Now bet as "make the architecture truthful and pinned," inferred from the active
architecture-gap milestone. Within the same session the owner supplied the real context, which is
broader: they had just come out of a six-month hard crunch on an unrelated work project, during
which Townlet received only "occasional time from older models." The result is a codebase that is
**buggy, underspecified or unfinished in places, with documentation that is messy, missing and
inconsistent**. Their stated first step: *"teardown, rebuild and recover"* — but qualified
immediately and importantly: *"we aren't throwing out everything, there's some great engineering
and ideas here, but first step is a maturity assessment both at a macro level and then at the
subsystem level."*

The owner also recalibrated severity unprompted: shown 60 open markdown bug notes, they judged it
*better* than expected against a 400k-line day-job baseline. So this is a recovery, not a rescue.

## Options considered

1. **Proceed with the architecture-gap milestone as-is** — pro: already scoped, three tasks ready,
   real work. Con: it was scoped on 2026-05-16 against a source tree that has moved, it covers
   only part of the problem, and it presumes dispositions nobody has established. Writing truthful
   docs for a subsystem that should be respec'd or deleted is wasted work.
2. **Start teardown directly on the known-bad areas** — pro: fastest visible progress. Con: this
   is precisely what the owner ruled out. Without an assessment, "known-bad" means "unfamiliar,"
   and the good engineering they explicitly want kept is what gets destroyed first, because
   undocumented good code and genuinely bad code look identical from the outside.
3. **Gate all recovery work on a macro + subsystem maturity assessment** — pro: matches the
   owner's instruction exactly; produces a per-subsystem disposition so teardown is targeted;
   protects good work by naming it before anything is cut. Con: delays visible repair; costs a
   large fan-out of analysis before a line changes.

## The call

Option 3. The Now bet is **teardown, rebuild, recover**, and it is **gated on a maturity
assessment** — macro first, then subsystem-level, per the owner's stated sequence. No repair,
rewrite, or deletion is dispatched until the assessment produces an evidence-backed disposition
(KEEP / REPAIR / RESPEC / REBUILD / DELETE) for that subsystem.

The assessment was dispatched this session as workflow run `wf_4ca82820-274` against the eight
subsystems from the 2026-05-16 catalog, structured as: three macro lenses (declared-vs-live audit,
bug-corpus freshness verification, spec/doc truth) → eight per-subsystem assessments scored on six
maturity dimensions → **adversarial verification of every REBUILD or DELETE call** → synthesis
into a disposition table, an authorability ledger, and a work-stream shape.

Two design choices in that assessment are load-bearing and are recorded here as decisions, not
implementation detail:

- **Drastic dispositions must survive an adversarial pass.** Any REBUILD or DELETE is challenged
  by a second agent instructed to refute it and to default to the cheaper disposition (REPAIR /
  RESPEC) unless the evidence is overwhelming, and to enumerate salvage regardless. This is the
  mechanism that operationalises "we aren't throwing out everything."
- **`declared-but-inert config` is treated as the top-severity defect class.** For a product whose
  thesis is *substrate as code*, a YAML field that validates, is documented, and does nothing is
  worse than a missing feature: the author cannot detect it, and it silently falsifies the
  promise. Four suspected instances exist in stale bug notes of unverified freshness; the
  assessment verifies each against source rather than trusting the note.

The architecture-gap milestone `hamlet-7a932c4e40` is **not cancelled** — it is demoted to a
subordinate workstream that the assessment may re-scope. Its guardrail-tests child
(`hamlet-c8c316ba03`) is exempted from the gate, because regression protection is worth having
*during* recovery whatever the dispositions turn out to be.

## Rationale

Option 3 beat option 1 because the milestone's scope is an artifact of a three-month-old snapshot
and encodes assumptions the assessment exists to test. It beat option 2 on the owner's explicit
constraint, but also on product grounds: the asset at risk here is not code volume, it is the
*good ideas* embedded in code nobody has a spec for. An assessment that names what is good is
cheaper than rediscovering it after deletion, and git history is a poor substitute for a decision
someone can read.

The cost — analysis before repair — is real but bounded, and it buys the thing recovery programs
usually lack: a defensible answer to "why did you rewrite that?" for every subsystem touched.

## Reversal trigger

Reopen this PDR if **any** of the following:

- The assessment returns dispositions for fewer than 6 of 8 subsystems, or its confidence is too
  low to act on. The gate has then failed to pay for itself and recovery should proceed on the
  architecture-gap milestone's existing scope instead.
- The assessment finds **zero** declared-but-inert surfaces and **zero** authorability gaps. That
  would mean the substrate thesis is in better shape than believed, and the Now bet should move
  from recovery to measuring the authoring claim (`roadmap.md` → Next) directly.
- Recovery work is still gated on assessment at the **second** checkpoint from now — meaning the
  gate has become a stall rather than a filter.
- The owner directs otherwise. This bet exists because they framed it; their reframing supersedes
  it without further justification.
