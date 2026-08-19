# PDR-0101 — The merge to `main` is autonomous; `PDR-0039` gate 2 survives as a quality gate the agent executes rather than an escalation it waits on

Date: 2026-08-20   Status: **accepted** (owner-ruled: *"Autonomous — run gate 2 and merge now"*)
Author: Claude (standing product owner)

Follows from: `PDR-0100` (publication = declaring 1.0)
Amends: the authority grant in `vision.md` — second scope change of the day
Related: `PDR-0046` and `PDR-0058` (both say "the merge to `main` is the boundary" — that
sentence is now superseded), `PDR-0039` (the gates), `PDR-0068` (merge banking trigger),
`PDR-0099` (the push widening this completes)

## Context

The merge to `main` has been described as *the boundary* since `PDR-0046`, and every merge to date
(PR #32 at `07b26ed5`, PR #35 at `4222a917`) was executed by the owner. `PDR-0100` then removed the
reason the agent treated it as escalating: merging is not a publication event, because publication
means putting out a product offering and this project has none — *"just code"*.

That left the boundary standing on **unstated grounds**. A gate whose reason has evaporated but
which still fires is worse than either alternative: it produces flagging that neither party can
justify, and it invites the agent to quietly reinterpret it later. So it was put to the owner
plainly — autonomous, autonomous-with-agent-timing, or still your gate for some other reason.

`PDR-0068`'s banking trigger was lit at the time of asking (37+ commits ahead vs a ~30 threshold).

## Options

1. **Autonomous — run gate 2 and merge now.**
2. Autonomous, agent picks timing.
3. Keep it as the owner's gate, on a non-publication ground to be recorded.

## Call

**Option 1, the owner's ruling.** Merging `project-recovery*` into `main` is now autonomous. The
grant's autonomous list gains it; *"the merge to `main` is the boundary"* is superseded wherever it
appears.

**`PDR-0039` gate 2 is unchanged in substance and changed in kind.** It remains owed at **every**
merge, unconditionally, executed **by method** — ground-truth sweep, draft from verified facts
only, adversarial pass — never a re-read. What changed is that it is now a **quality gate the
agent executes** rather than an escalation the agent waits on. The distinction matters: a gate the
agent owns is a gate the agent can quietly weaken, so the method is restated in the grant itself
rather than left in this PDR alone.

## Rationale

Once `PDR-0100` landed, keeping the merge gated would have meant one of two bad things: the agent
enforcing a boundary whose stated reason it knew to be void, or the agent inventing a replacement
reason on the owner's behalf. Both are worse than asking. The owner answered without hedging and
paired the answer with an instruction to act, which is a considered ruling rather than the
indifferent consent `PDR-0099` had to read narrowly.

**What did not move.** Escalation still binds: declaring **1.0** or publishing a product offering,
**announcement** (telling people — blog, social, forum, aggregator), **tags and releases**,
**vision/strategy/grant changes**, and **data deletion** (which here includes `runs/`, checkpoints,
and recorded episodes as experimental evidence). The merge left the list; nothing else did.

Note the asymmetry this creates and accept it deliberately: the agent may now put code on the
default branch of a public repository without asking, but may not *tell anyone* it did. That is
the correct shape given `PDR-0100` — the owner's boundary is around the product being offered and
around outward communication, not around code being readable.

## Reversal trigger

1. **A gate-2 execution that finds nothing** is the signal to distrust the gate, not to celebrate.
   The two prior runs found 21+10 and a substantial set; a clean sweep across 30+ commits means the
   method was applied as a re-read, which `PDR-0039` explicitly forbids. Re-run it with a fresh
   adversarial agent before merging.
2. **A merge that lands a red gate on `main`** — CI failing on the default branch after an
   agent-executed merge — reopens this PDR immediately, because the owner's exposure is precisely
   what the boundary used to cover.
3. **`PDR-0100` reversing** (a coherent product offering appears before 1.0) takes this with it:
   if merging starts to feed something adopters consume, the merge re-arms as a release step.
4. Re-offered at the next grant re-confirmation alongside `PDR-0099` and `PDR-0100`, because three
   grant changes were settled in one rapid exchange.
