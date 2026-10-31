# PDR-0108 — Tokenisation moves into scope, owner-directed, so the VFS refresh can finish

Date: 2026-08-22   Status: **accepted** (owner-stated direction, recorded verbatim in intent:
*"we're bringing the tokenisation into scope so that we can finish the vfs refresh"*)
Author: Claude (standing product owner)
Owner sign-off: the direction **is** the owner's, given directly this session.
Related: `PDR-0017`/`PDR-0044` (the direction and its authority), `PDR-0107` (relational
exposure waits on exactly this work), `PDR-0027` (brain level-override, the blocker's
resolution), `PDR-0090` (the corpus substrate freeze this supersedes for this stream)
Tracker: `hamlet-0d0115383e` → `hamlet-fa6bb6da4a` (the chain now in scope),
`hamlet-424adcb84f` (downstream), plan
`docs/superpowers/plans/2026-08-22-token-observation-pivot-phase-a.md`

## Context

`PDR-0044` settled *whether* (token observations, owner-authoritative since 2026-08-11) but
deferred *when* to "post-corpus". The VFS refresh (the 2026-08-21 vfs.md source audit's
"VFS to green" stream) has been landing since 2026-08-21 and its tail — relational
observation exposure, message wiring, dynamic variables — was deferred onto the token path
by `PDR-0107` yesterday. The owner now sets the timing: tokenisation is in scope **now**,
precisely so that tail can close.

Per the `PDR-0044` standing practice (record authority and timing separately): the authority
was never in question; this PDR records the timing decision and who made it — the owner.

## The call

1. **The token-observation chain moves Later → Now** on the roadmap, inside the strangler
   bet's work: `hamlet-0d0115383e` (brain level-override + lineage legibility), then
   `hamlet-fa6bb6da4a` starting with the `set_encoder` proof, per the Phase A plan.
2. **The Phase A plan's execution gate is lifted by this direction.** The gate deferred to
   `PDR-0090`'s corpus freeze; the owner directing substrate work now supersedes it for this
   stream — consistent with the VFS-refresh commits already landing on `src/townlet/` since
   2026-08-21. Trial readings remain protected by their own mechanism regardless: every
   trial and blind re-run executes at a **pinned commit**, not at HEAD.
3. **`PDR-0107` is not reversed — it is being serviced.** Its call was "relational/message
   exposure waits for tokens"; the tokens are now being built. Its third reversal trigger
   ("the token migration lands") is the intended exit.

## Consequences

- The Phase A plan executes now: claim `hamlet-0d0115383e`, run tasks 1–5, adjudicate the
  `set_encoder` proof outcome. A design-level proof failure still **escalates** to the owner
  (`PDR-0017` trigger 2) — being in scope does not pre-decide repair-vs-replace.
- Phase B (aggregator upgrade, full token representation, relational/message exposure,
  dynamic variables) becomes schedulable on the proof's outcome — that is what "finish the
  VFS refresh" means concretely: vfs.md §21.1's remaining items 1/5/6 all land via this path.
- The roadmap's Later bullet for token observations moves to Now under the strangler bet,
  stamped with this PDR. Its "captured rather than started" framing (pre-`PDR-0044`) dies
  with the move.

## Reversal trigger

Reopen if **any** of the following:

- **The owner re-defers or redirects.** This PDR records the owner's timing; only the owner
  moves it again.
- **The `set_encoder` proof fails at design level** — the `PDR-0017` trigger 2 escalation
  fires and the answer changes the representation. The scope decision survives (the VFS
  refresh still needs *some* exposure path) but the work content is re-planned from the
  owner's ruling.
- **The corpus resumes live trials against HEAD** (rather than pins) while this stream is
  mid-flight — then the `PDR-0090` tension is real again and sequencing goes back to the
  owner.
