# PDR-0003 — Townlet Town is the first-class tech demo, and the demo is bound by two obligations

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: yes (owner stated the correction directly in-session)
Supersedes: —   Related: PDR-0001 (its reversal trigger fired; PDR-0001 otherwise stands), vision.md, metrics.md, roadmap.md (Next)

## Context

`PDR-0001` recorded, tagged `[assumption]`, that the pedagogical Sims mission had been **demoted**
from mission to use case, and named that assumption in its own reversal trigger as the most
consequential thing it might have got wrong. The owner corrected it directly:

> *"it's not demoted so much as 'we promoted the world around it' — it's gone from being 'the
> product' to being 'the first-class tech demo of the product'."*

and then specified what the demo is *for*:

> *"it demonstrates 'this is a powerful example of what you can make, but you can also make
> anything else you can think of'."*

The distinction matters because "demoted" and "promoted to first-class tech demo" imply opposite
treatment during a recovery program. Demoted invites neglect — let it rot, it's legacy. First-class
demonstrator carries quality obligations that survive teardown.

## Options considered

1. **Leave PDR-0001's "demoted" framing and just soften the wording** — pro: minimal churn.
   Con: the framing drives behaviour. A recovery program that reads "pedagogy demoted" will
   deprioritise the demo's maturity, which is precisely backwards.
2. **Record the correction as a status change only** (demoted → first-class) — pro: accurate,
   cheap. Con: leaves "first-class tech demo" as a label with no enforceable content, so it decays
   into a compliment. Nothing about the codebase would have to change to satisfy it.
3. **Record the correction *and* derive the obligations the role implies** — pro: turns a framing
   into a testable constraint; makes the demo a running proof of the product claim. Con: creates
   new obligations mid-recovery and may surface uncomfortable gaps.

## The call

Option 3. Townlet Town — the survival universe, its curriculum levels, and its "interesting
failures" — is the **first-class tech demo of the substrate**: maintained to demonstrator
standard, not legacy, and not something recovery may let rot.

The demo's specification is the owner's two-part claim, and the two halves are recorded as pulling
*against* each other, because that tension is the real design constraint: **power** (impressive
enough to want) versus **generality** (not special-cased, proving the substrate isn't built around
it). The standard failure is buying power by destroying generality.

Two obligations are therefore adopted, both serving the generality claim:

- **A — the dogfooding rule.** Townlet Town must be authored through the same door as any user:
  config in, standard compiler, **no privileged Python path a novice author would not have**. Each
  violation is an authorability gap of the most diagnostic kind — one the project has already
  proven it cannot live without. Tracked as the **Demo dogfooding — privileged-Python count**
  input metric, target 0.
- **B — generality needs a second witness.** One universe cannot demonstrate "anything else you
  can think of"; it can only fail to contradict it. At least one **deliberately dissimilar**
  universe — no shared domain vocabulary with Townlet Town, ideally not survival-shaped — is
  required. Whether `aspatial_test` / `L5_multi_agent` / `simple` / `reference` are real witnesses
  or thin fixtures is referred to the maturity assessment.

Obligation A is also adopted as the **best available proxy for the north-star** until the N-idea
authoring corpus exists, because unlike that corpus it is measurable today against code that
already exists.

`PDR-0001` is **not** superseded. Its call — bootstrap from observed state, record the pivot as
stated, tag every inference — stands and worked exactly as designed: the tag it placed on this
claim is what caused the owner to correct it within the same session. Only the specific
characterisation is amended, by this record.

## Rationale

Option 3 beat option 2 because a role without obligations is not a decision, it is a label — and
labels do not survive a recovery program. The dogfooding rule is what converts "first-class tech
demo" from a compliment into something that can fail a check. It also happens to solve a real
measurement problem: the north-star was seeded `UNMEASURED` with no path to a reading until
someone builds an N-idea corpus, and obligation A yields an honest partial reading immediately.

Recording the power/generality tension explicitly, rather than the two claims as a flat pair, is
deliberate. The pair reads as harmless marketing; the tension names the specific way this product
is most likely to fool itself — a spectacular demo that quietly required engine changes nobody
counted.

## Reversal trigger

Reopen this PDR if **any** of the following:

- The maturity assessment finds the privileged-Python count is **large** (say, more than a handful
  of load-bearing paths). The dogfooding rule would then be aspirational rather than a live
  constraint, and the honest move is to state that the substrate does not yet author its own demo
  — rather than keep a target of 0 that has never been met.
- No deliberately-dissimilar universe can be authored **without** engine changes. That falsifies
  the generality claim directly and forces the vision's "anything else you can think of" down to
  a bounded, stated grammar — a vision change, and therefore an owner escalation.
- The owner indicates the demo's quality obligations are competing destructively with substrate
  work during recovery. The role is worth having, but not at the cost of the thing it demonstrates.
