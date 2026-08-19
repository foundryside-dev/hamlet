# PDR-0079 — a miss is not one thing: every non-PASS verdict classifies ABSENT / INERT / BLOCKED, and escalation retargets onto the INERT count

Date: 2026-08-17   Status: **accepted** (owner steer — *"it's not necessarily a huge problem if
there's a gap, it's just a gap"* — implemented autonomously within grant)
Author: Claude (standing product owner)
Owner sign-off: **yes**, on the framing; the taxonomy and the retarget are the agent's

Related: `PDR-0007` (the "not yet enabled" distinction this operationalises), `PDR-0012`/`PDR-0013`
(the anti-goal names what is wired *wrong*, explicitly not what is merely absent), `PDR-0051`
(Trial 002 found `range_type` declared-accepted-inert — the type specimen), `PDR-0078` (the
escalation clause this retargets)
Tracker: `hamlet-5fa1f7bfc0`, and `hamlet-dc8f887cd5` (four declared observation fields with zero
writers — the predicted first INERT hit)

## Context — binary FAIL hid the only distinction that matters

The owner's steer was a framing correction, and the scoring did not reflect it. A binary FAIL
scored these identically:

- **no declarative surface exists** — nobody has built it. `vision.md`'s anti-goal is explicit
  that debt is what is wired *wrong*, **not** what is merely absent; `PDR-0007` calls this "not
  yet enabled".
- **a surface exists, validates, and does nothing** — the substrate tells an author *yes* and
  means *no*. This **is** debt, and it is the worst failure mode a declarative product has.

Same score, opposite meanings, opposite routes.

## Call

Every non-PASS verdict classifies:

- **ABSENT** — no declarative surface. Routes to WS-4 as a feature. Not debt.
- **INERT** — leg (a) passes, leg (b) fails: declared, accepted, unobservable. Debt; routes as a
  defect.
- **BLOCKED** — declarable in principle, fails loudly. The loudness is the good news;
  `Failure loudness` is its metric.

Every reading reports the split alongside the rate. And the escalation clause **retargets off the
raw rate onto the INERT count**: 3 or more INERT ideas escalates to the owner as a question about
`vision.md`'s central claim. A low rate whose misses are ABSENT does **not** escalate.

## Rationale

A reading of 3 of 9 whose misses are ABSENT describes a young substrate with a finite build list.
The same 3 of 9 whose misses are INERT describes a substrate that lies to authors. The bare
fraction cannot tell them apart, and escalating on the fraction would have escalated the wrong one.

This also corrects the agent's own framing: a predicted 1–2 of 9 was being read as bad news when
most of those misses are ABSENT — for a pre-1.0 substrate mid-strangler that is a roadmap.

## Reversal trigger

- **If a verdict cannot be classified** into the three buckets in two or more trials, the taxonomy
  is wrong and returns to design.
- **If INERT reaches 3 or more**, the agent's pre-registered prediction (1–2) has failed and the
  vision question goes to the owner — the agent does not write that conclusion.
- **If ABSENT findings routed to WS-4 are not acted on within two checkpoints**, the taxonomy has
  become a way of filing gaps rather than fixing them, and "just a gap" has quietly become debt.
