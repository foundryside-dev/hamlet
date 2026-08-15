# PDR-0013 — Promote no-tech-debt into `vision.md` as an anti-goal (vision change, owner-approved)

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)
Owner sign-off: **yes** — *"yes, put it into the vision - its absolutely load bearing, I don't want to have 20 or 30 data migration pathways in our code base before we even have a single user"*
Answers the escalation raised in: PDR-0012   Related: PDR-0007, vision.md (Anti-goals; Amendment log)

## Context

`PDR-0012` recorded the owner's strict no-tech-debt policy and deliberately stopped short of one
thing: anti-goals live in `vision.md`, and `vision.md` is ENDORSED, so editing it is a **vision
change** that escalates under the authority grant. The PDR bound the policy regardless; the vision
edit was left as an open question in `current-state.md`.

The owner answered it directly and supplied the rationale that decides it: *"I don't want to have
20 or 30 data migration pathways in our code base before we even have a single user."*

## Options considered

1. **Leave it as a PDR only** — pro: PDRs already bind, and `vision.md` stays smaller. Con: the
   owner called it *load bearing*, and load-bearing refusals belong where refusals are read.
   `vision.md`'s anti-goals are what a new session (or a new contributor) reads to learn what this
   project will not become; a policy discoverable only by reading thirteen decision records is
   discoverable in theory and not in practice.
2. **Replace the existing "Backwards compatible" anti-goal with the broader one** — pro: no
   apparent duplication; the owner's own example (migration pathways) sits squarely inside the
   older anti-goal. Con: it would **lose specificity**. The backwards-compat anti-goal enumerates
   concrete forbidden patterns (fallbacks, deprecation warnings, "support both") that a general
   debt refusal does not spell out, and those enumerations are what make it enforceable in review.
3. **Add it as a distinct anti-goal that explicitly generalises the existing one** — the option taken.

## The call

**Option 3.** A new anti-goal, *"A carrier of technical debt — at all, until 1.0 is declared"*, is
added to `vision.md` immediately after the backwards-compatibility anti-goal, quoting the owner and
stating explicitly that it **generalises** rather than replaces it. An amendment log is added to
`vision.md`'s status block so this and every future vision change carries visible provenance.

Nothing else in `vision.md` changed. **The authority grant is untouched.**

## Rationale

Option 3 beat option 2 on a distinction worth preserving: backwards compatibility is the *specific*
debt this project is most prone to and the one the owner named, but it is an instance, not the
category. Collapsing them would mean the next non-compat debt — a failing gate, an inert config
field, a computed-but-unconsumed hash — has no anti-goal to be caught by, which is precisely how
the current ~40 inert surfaces and the three-months-red gates accumulated. Keeping both, with the
relationship stated, means a reviewer can cite whichever is closer to the case in front of them.

The owner's rationale also sharpens *why* debt is the right thing to refuse at the vision level
rather than the process level. Migration pathways are not individually unreasonable — each one is
defensible at the moment it is written, which is exactly what makes them accumulate. A refusal that
has to be re-argued per instance loses; a refusal stated as identity does not. That is what an
anti-goal is for.

The amendment log is added because `vision.md` is now a document that has been changed after
endorsement, and "ENDORSED, 2026-08-11" alone would no longer tell a future reader *what* was
endorsed versus what was added later. Without it the endorsement's scope silently drifts — the same
class of failure as an edited PDR.

## Consequences

- **`vision.md` now carries the refusal**, so it is loaded by every `RESUME` before any decision is
  made, rather than depending on a session reading `decisions/`.
- **Future vision changes have a recorded shape**: escalate → owner approves → PDR → amendment-log
  entry. This is the first one; it sets the pattern.
- **`PDR-0012`'s open escalation is closed.** `current-state.md` is updated accordingly.
- No change to the substance of the policy, its edges, or its reversal triggers — those remain
  `PDR-0012`'s, and this PDR does not supersede it.

## Reversal trigger

Reopen this PDR if **either**:

- **`PDR-0012` is itself reversed or materially narrowed** (e.g. at 1.0, per its own trigger). The
  anti-goal would then be stating a policy that no longer holds, and `vision.md` must be amended in
  the same act rather than left to drift — that amendment is itself a vision change and escalates.
- **The two anti-goals are observed being confused in practice** — i.e. reviewers cite the general
  debt refusal where the specific backwards-compatibility enumeration applies, or vice versa,
  suggesting the split costs more clarity than it buys. Merging them would then be worth
  reconsidering, with the enumerations preserved.
