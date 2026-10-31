# PDR-0100 — "Public release" means publishing a product — declaring 1.0 — not code being visible on the internet

Date: 2026-08-20   Status: **accepted** (owner-defined; this is the owner stating what their own escalation term means)
Author: Claude (standing product owner)

Amends the *interpretation* of: the authority grant's escalation list in `vision.md`.
Undercuts the stated rationale of: `PDR-0099` (see below — the call stands, the reason does not).
Related: `PDR-0046`, `PDR-0058` (both use "the merge to `main` is the boundary"), `PDR-0039`
(the merge gates), `PDR-0013` (the tech-debt anti-goal, already scoped *"until 1.0 is declared"*)
Artifacts: `docs/product/vision.md` — grant specifics note rewritten; amendment log entry
2026-08-20 (second)

## Context

The authority grant escalates *"public release or announcement"*. `vision.md` glossed that clause
with a parenthetical the standing agent had written at bootstrap: *"(the GitHub repo is public at
`github.com/foundryside-dev/hamlet`)"* — asserting that because the repo is public, code reaching
it is a release event.

That inference was never the owner's. Asked to widen the grant to cover pushing, the owner
volunteered the correction unprompted, twice:

> *"I call publication declaring 1.0 - not makinmg content availabile on the internet"*
>
> *"publication => publishing a product and right now we don't have a coherent product offering,
> just code"*

## Options

1. Record it as a footnote and leave the parenthetical.
2. Correct the grant note outright, and state that the previous reading was the agent's error.

## Call

**Option 2.** Publication = **publishing a product**: a coherent product offering someone can
adopt, which for this project means **declaring 1.0**. Code being visible on the internet is not
publication. The repo's public status, pushing branches, and merging to `main` are **not** release
events under this grant. *Announcement* remains a separate limb that still escalates on its own —
it covers **telling people** (blog, social, forum, aggregator), which is outward communication, not
code readability.

## Rationale

The correction is made in the grant's own text rather than annotated beneath it because the wrong
reading was **load-bearing on behaviour, not just wording**. It is the reason `PDR-0099` — written
an hour before this — read the push widening at its narrowest: that PDR argued *"the repo is
PUBLIC, so a push to `main` is a publication step, and publication is on the escalation list by
name."* Under the owner's definition that sentence is simply false. A wrong gloss that changes how
cautious an autonomous agent is must be corrected where the agent reads it.

The definition also **coheres with vision language that already exists**: the tech-debt anti-goal
is scoped *"until 1.0 is declared"* (`PDR-0013`), so putting the release clause on the same
milestone makes the vision turn on one threshold rather than two. That is a sign the owner's
definition is the settled one and the agent's was the improvised one.

**What this PDR does NOT do.** It does not widen the autonomous list. The owner defined a term;
they did not say the merge to `main` is autonomous. Those are different claims, and treating a
definitional clarification as a scope grant would repeat exactly the error `PDR-0099` was written
to avoid — letting a sentence carry weight it was never asked to bear. `PDR-0099`'s **call**
(push scope = `project-recovery*`) therefore stands for now; only its **rationale** is void, and
the merge boundary is re-offered to the owner as an open question rather than resolved here.

Terminology note for future readers: `PDR-0058` uses "publication step" to describe merging —
*"merging is a publication step that may happen any number of times inside the bet"*. That is a
different sense of the word from the escalation clause's, and under this PDR it is a misleading
one. Read `PDR-0058` as meaning **banking** work to `main`, not releasing a product.

## Reversal trigger

This definition is re-offered at the next grant re-confirmation, together with `PDR-0099`'s clause,
because both were settled in one rapid exchange rather than at a considered review. It reopens if:

1. **A coherent product offering appears before 1.0** — a published package, an installable
   artifact, a hosted demo, documentation addressed to adopters. At that point "no product offering
   yet" stops being true and the release clause re-arms *before* the 1.0 milestone, not at it.
2. **An act that is not a "release" nonetheless reaches external parties** — e.g. the repo is
   submitted to an aggregator, indexed prominently, or picked up and discussed. The *announcement*
   limb governs there, and this PDR must not be cited to wave it through.
