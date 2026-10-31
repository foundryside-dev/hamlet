# PDR-0046 — The agent may push `project-recovery`; reversibility is the test, and the merge to `main` becomes the boundary it does not cover

Date: 2026-08-15   Status: **accepted** (owner-made — this changes an agent authority boundary,
which is not within the grant to grant itself)
Author: Claude (standing product owner)
Owner sign-off: **yes**, stated as a correction to my framing. I recorded the session's push as a
one-time exception to a standing "the owner pushes" practice; the owner replied: *"I think a
better answer is 'I don't really care who pushes because with git you can generally roll back and
forward easily anyway'."*
Amends: `PDR-0039` — falsifies its clause *"the agent pushes nothing"*, and with it the premise of
its accidental-publication argument. Its two merge gates and the README expiry rule **stand
unchanged**, and gain force from this.
Related: `PDR-0043` (CI restoration; the push this session fired its acceptance evidence),
`PDR-0038` (grant re-confirmation), `PDR-0012` (no tech debt until 1.0)
Tracker: `hamlet-2100105c9a` (closed by the runs this push fired)

## Context

Every prior checkpoint recorded, as observed practice, that **the owner pushes the branch
themselves**. `PDR-0039` used that as a load-bearing premise: because the agent pushes nothing, a
newly-written public claim would reach the world on the owner's *next reflexive push*, with nobody
having decided to publish it — so the publish decision had to be taken explicitly.

This session the owner directed a push (*"please commit all your updates including your checkpoint
and sync to remote"*). I recorded that as a **one-time exception** and told the next session to
keep assuming the owner pushes. The owner corrected the framing: the practice was never a control,
and treating it as one was my inference, not their rule.

## The call

**The agent may commit and push `project-recovery` without asking.** No per-push approval.

**The owner's reason is the important half, because it is a *test*, not a permission:** with git
you can roll back and forward easily. A pushed commit on a working branch is `git revert` or
`git reset` away, the branch is not the default branch, and nothing downstream consumes it. The
cost of a bad push is bounded and the remedy is mechanical.

**So the rule generalises to: gate on reversibility, not on the verb.** "Push" was never the
category that mattered. What matters is whether an action can be undone by another action of the
same kind.

**Where the test comes out the other way — unchanged, and now the whole of the boundary:**

1. **The merge to `main` still gates on `PDR-0039`'s two conditions.** `foundryside-dev/hamlet` is
   **PUBLIC** (verified 2026-08-15). Merging to the default branch publishes; a reader who has
   already read something is not reachable by a later push. `git revert` restores the *file*, not
   the *fact that it was published*. Gate 2 (README re-verification by method) is the only gate
   still standing, and it is not a formality.
2. **Genuinely outward-facing actions still stop for the owner** — releases, issues or PRs on the
   public repo, anything that leaves the machine toward a third party. Same reasoning: undo does
   not reach a reader.

## Rationale

My "one-time exception" framing was wrong in a way worth recording, because it is a failure mode I
have now hit twice in one session. **I read an observed regularity as a rule, and then read a
deviation from it as an exception requiring justification.** The owner had never said "only I
push"; they had simply been the one pushing. Elevating that to a control, and then to a control
with an exception, invented a constraint and put ceremony around it.

This is the same error as `PDR-0044`, one turn earlier and in the opposite direction: there I read
a *deferral of timing* as a *withdrawal of authority*; here I read a *habit* as a *policy*. Both
are the same mis-inference — **treating a description of what happened as a prescription about
what is permitted** — and both cost real work: a directive recorded as tentative in one case,
an invented approval gate in the other.

The corrected principle is also better engineering. "Who performs the action" is a weak control:
it is easy to satisfy and easy to satisfy *vacuously* (the owner pushing an agent's unreviewed
commit is not review). "Is this reversible, and by what" is a real one, because it names the
actual risk and points at the actual boundary. It also explains why the merge gate is strict while
the push gate is not, which the old framing could not — under "the agent pushes nothing", branch
pushes and the merge sat in the same undifferentiated bucket.

Worth stating plainly, because this PDR *reduces* a constraint: the reduction is narrow. It moves
exactly one thing — pushing a non-default working branch of a repo whose default branch is
protected by two named gates. It does not touch the merge, publication, third parties, or anything
`PDR-0039` decided.

## Consequences

- **`current-state.md`'s "Owner state" is rewritten** from "the owner pushes the branch themselves"
  to the retired practice plus the two limits. The next session should not re-derive a push gate.
- **`PDR-0039`'s clause 2 is factually superseded**; its *conclusion* is untouched. The README
  still ships as written, its claims still expire at the merge, and both merge gates still hold.
  Note the accidental-publication risk it identified is **not** eliminated by this PDR — it is
  relocated: the danger is no longer "the owner pushes without deciding" but "the agent pushes
  without deciding", which is the same risk with a different actor. The mitigation is unchanged
  and is the merge gate, not the push gate.
- **This session's push is retroactively ordinary**, not an exception, and it produced the
  evidence that closed merge gate 1: the first CI runs in the branch's history, all green.
- **No standing approval is created for anything else.** Releases, PRs, issues, and the merge are
  where they were.

## Reversal trigger

Reopen if **any** of the following:

- **A push turns out not to be cheaply reversible in practice** — e.g. something starts consuming
  `project-recovery` (a CI publish step, a downstream fork, a reader treating it as a release).
  The premise is reversibility; if a consumer appears, the premise is gone.
- **`main` stops being the only publication boundary** — if `project-recovery` is ever made the
  default branch, or the repo's visibility changes, this PDR must be re-read before it is relied
  on. The public/private status of the repo is load-bearing here, not incidental.
- **The owner wants pre-push review for a class of change** (e.g. anything touching `configs/` or
  `src/`). That is a narrower gate than the one just retired and would supersede this cleanly.
