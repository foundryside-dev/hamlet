# PDR-0021 — The two provenance gaps task 4 uncovered are filed, not folded into WS-1

Date: 2026-08-12   Status: accepted
Author: Claude (standing product owner)
Owner sign-off: not required (within grant — scoping work against existing strategy). Directly serves the owner's standing question *"when do we stop adding to WS-1 and freeze?"*
Related: PDR-0014 (reversal trigger 2 — batch growth delaying the freeze), PDR-0008 (provenance breaches), PDR-0012 (no tech debt), PDR-0006 (oracle freeze)
Tracker: `hamlet-2dde1015fe`, `hamlet-df2b972c49` (both filed, neither in WS-1)

## Context

Reconnaissance and verification around task 4 turned up two further provenance defects of
exactly the class WS-1 exists to close:

1. **The dead-hash set is NINE, not four** (`hamlet-2dde1015fe`). Beyond the four per-level
   content hashes task 4 wired, five pack-level hashes — `experiment`, `stratum`, `environment`,
   `actions`, `items` — are computed, stored, serialized, round-tripped through the cache and
   **compared by nobody**. Identical shape to the defect just fixed.
2. **Two further checkpoint stamp/compare paths** (`hamlet-df2b972c49`, P1) that neither task 4
   nor task 5 touches: `VectorizedPopulation.get_checkpoint_state`/`load`, and
   `DemoRunner._validate_checkpoint_compatibility` — which unpickles a checkpoint *before any
   universe exists*, behind a broad `except`.

Under `PDR-0012` (strict no-tech-debt until 1.0) both are in scope for the program. The question
is whether they are in scope for **this batch**.

## Options considered

1. **Fold both into WS-1.** They are cheap now that the pattern exists, the context is loaded,
   and `PDR-0012` says debt is not deferred. This is what the last two reviews did, and it is
   how WS-1 went 7 → 10 units.
2. **File both, sequence after the freeze** — taken.
3. **File the nine-hash one, fold the checkpoint-paths one** (it is P1 and bears on whether the
   breach can be called closed). Rejected — see below.

## The call

**Option 2. Both are filed and neither enters WS-1.**

`PDR-0014`'s reversal trigger 2 — *"the bounds wiring materially delays the oracle freeze"* — was
already recorded as **approaching**. WS-1 has grown 7 → 10 across two reviews, every addition
individually justified and none optional under `PDR-0012`. That is precisely how a batch drifts
without anyone deciding to let it. The discipline that keeps `PDR-0012` from becoming unbounded
scope is that "fix everything" and "fix everything **now**" are different claims.

Option 3 was tempting because `hamlet-df2b972c49` is P1. It is rejected because its own first
unit is *enumeration, not repair* — find every site that reads or writes a checkpoint — and
enumeration is exactly the work that should not be rushed into a batch that is trying to close.

## Rationale

The load-bearing consequence is about **honesty, not scope**: closing WS-1 task 5 closes
provenance breach 3 of 3, and it would be natural to then call the Provenance-integrity guardrail
green. **It will not be green.** Two known gaps will remain open, both filed, both of the same
class. The guardrail row in `metrics.md` says so explicitly so that a future session cannot read
"3 of 3 breaches closed" as "provenance is sound".

That is the trade this PDR makes: the freeze is not delayed, and the scoreboard tells the truth
about what the freeze is capturing.

There is a real cost, and it should be stated rather than glossed: the oracle will be frozen
with five dead hashes and two unguarded checkpoint paths **in** it. Under `PDR-0006` precondition
2 that is acceptable only because they are entered in the known-divergences register rather than
discovered later by a failing diff — freezing a bug you have written down is a different act
from freezing one you have not.

## Consequences

- **WS-1 stays at 10 units.** Task 5 is the last provenance unit in the batch.
- **Both issues must be entered in the known-divergences register** when WS-7 builds it. This is
  the condition that makes the trade legitimate; without it, this PDR is just deferral.
- **`metrics.md`'s Provenance-integrity row records that 3-of-3 ≠ green**, with both tracker IDs.
- **`hamlet-df2b972c49`'s first unit is enumeration**, deliberately: grepping for callers of the
  two known helpers finds the call shape, not the set of places a checkpoint is read — the
  recurring lesson now recorded five times.

## Reversal trigger

Reopen if **any** of the following:

- **Task 5 turns out to need one of them anyway.** If routing the serving path through the shared
  guard requires the population checkpoint path to be correct first, the dependency is real and
  `hamlet-df2b972c49` joins the batch rather than following it.
- **The known-divergences register does not get built before the freeze.** Then the freeze
  captures undocumented defects, `PDR-0006` precondition 2 is violated, and these two must be
  fixed rather than deferred.
- **A third gap of the same class appears.** Two is a deferral; three is evidence that the
  provenance surface was never scoped, and the honest response is a dedicated stream rather than
  a growing list of filed-and-waiting issues.
