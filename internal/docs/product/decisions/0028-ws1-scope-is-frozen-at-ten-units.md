# PDR-0028 — WS-1's scope is frozen at ten units; new findings route to the register or to WS-4

Date: 2026-08-13   Status: **accepted** (within grant — prioritization; proposed to the owner in
the 2026-08-13 resume brief with a stated silence-adopts protocol, and the owner's reply raised
no objection)
Author: Claude (standing product owner)
Related: `PDR-0014` (whose reversal trigger 2 this pre-empts), `PDR-0018` (removed the main
reason for slowness), `PDR-0021` (the precedent this generalizes)
Tracker: `hamlet-67ffbd282a` (WS-1), `hamlet-e3af412673` (WS-7, owner of the register)

## Context

WS-1 has grown from 7 to 10 units across two reviews. Every addition was individually justified
and none was optional under `PDR-0012` — and that is exactly the problem: a stream where every
addition is defensible has no internal stopping rule. `PDR-0014`'s reversal trigger 2 (*"the
bounds wiring materially delays the oracle freeze"*) was recorded as approaching. Meanwhile
`PDR-0018` established there is no calibrated behaviour at risk (the packs were never tuned),
which removed the largest argument for going slowly, and `PDR-0021` already routed two findings
*around* WS-1 rather than into it.

## The call

**WS-1 is its current ten units. Nothing new enters.** From task 5 onward, findings route by
kind:

- **Provenance-shaped** (a silent stamp/compare/acceptance path) → WS-7's known-divergences
  register, as a precondition of the freeze — the oracle carries the divergence rather than
  WS-1 fixing it first. (`hamlet-2dde1015fe` and `hamlet-df2b972c49` are already there in
  intent; `PDR-0022`'s deletion condition depends on the first.)
- **Authoring-surface-shaped** (declared-but-inert, unauthorable, hardcoded-domain) → WS-4.
- **Anything else** → ordinary triage. Not into WS-1.

This converts `PDR-0021`'s one-off ruling into the standing fence it was implicitly arguing
for.

## The exception clause (deliberately narrow)

A finding may enter WS-1 only if **all three** hold:

1. It **silently corrupts artifacts today** — WS-1's own admission bar;
2. It **cannot be recorded as a divergence** for the oracle to carry (i.e. freezing it would
   freeze corruption itself, not a known quirk);
3. It **mechanically blocks** a remaining WS-1 unit (5, b, c, 3b, or close).

Two of three is a filed issue, not a WS-1 unit.

## Consequences

- **The freeze date stops receding.** WS-1's remaining work is enumerable: task 5, b, c,
  sibling 3b, close. `PDR-0014` trigger 2 is answered before it trips instead of after.
- **The register becomes load-bearing earlier** — routing provenance findings there only works
  if WS-7 stands the register up as one of its first artifacts, not its last. Noted on
  `hamlet-e3af412673`.
- **Discovery pressure doesn't vanish, it lands somewhere honest**: the inert-surface guardrail
  keeps counting (rate of discovery still exceeds rate of repair), and WS-4 inherits the
  backlog it was always going to own.

## Reversal trigger

Reopen if:

- **A finding meets all three exception clauses and the fence still feels wrong to apply** —
  then the fence's bar is miscalibrated, and it should be re-argued rather than quietly
  breached.
- **The register is not stood up by the time the first routed finding needs it** — routing to
  a register that doesn't exist is filing to /dev/null, and the fence would then be causing
  silent loss, the one thing this whole stream exists to prevent.
