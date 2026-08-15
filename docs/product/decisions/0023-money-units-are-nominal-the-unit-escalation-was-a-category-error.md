# PDR-0023 — Money units are nominal; the "what unit is money in?" escalation was a category error

Date: 2026-08-12   Status: accepted
Author: Claude (standing product owner)
Owner sign-off: **yes** — resolved directly: *"it doesn't matter what the unit is, this is ML/RL remember — they're 'money units'."* And, immediately after: *"we shouldn't 'moneyfy' these for users, they need to understand that a dollar isn't a dollar, it's a normalised variable like everything else."*
Amends: `PDR-0020` — resolves its escalation. Its two accepted calls (vfs.md as design authority; the money-scale fix routes through `range_type`) **stand unchanged**.
Tracker: `hamlet-365e996511` (unblocked by this), `hamlet-0dd4ac24d9` (do-not-moneyfy), `hamlet-e979f2ba37`

## Context

`PDR-0020` escalated a question to the owner: *is `money` denominated in dollars or in fractions
where `1.0 ≈ $100`?* It rested on a real contradiction — `docs/architecture/vfs.md:739` and
`frontend/src/utils/formatting.js:26` assume the fraction convention, the shipped configs
denominate in whole units (EAT 5.0, DOCTOR 20.0, WORK +22.5).

The owner dissolved it rather than answering it. **There is no unit.** This is a
reinforcement-learning environment: the agent observes a number and learns a policy from it.
`money` is denominated in *money units*, and no fact of the matter makes 22.5 "really" $22.50
or "really" $2250.

## The call

**The escalation is withdrawn, not answered.** No owner decision is pending on it.

What survives the correction, and what does not:

| question | status |
|---|---|
| What real-world unit is `money`? | **Void.** Not a question this system has. |
| Is `range_type: unbounded` inert? | **Stands** — a real defect (`PDR-0020`), one `grep` hit in all of `src/`. |
| Does money's observed magnitude harm learning? | **Stands** — the only version of "the money problem" that was ever real. |
| Are costs and payouts self-consistent? | **Yes, and that is all consistency means here** — the economy is internally coherent in money units. |
| Does `vfs.md:739` contradict the configs? | **No.** It records a convention, not a constraint. Nothing depends on it. |

## Rationale

The correction is worth recording because of *how* I got it wrong, not just that I did.

I treated a numeric feature as if it carried real-world semantics needing reconciliation — an
economy with dollars, where "$2250 for a shift" is absurd and therefore evidence of a bug. But
the agent has no concept of a dollar. It has a scalar, its scale relative to other scalars, and
a gradient. **Asking what unit it is in is asking the game a question that only the engine can
answer, and the engine's answer is "it is a number."**

That is [[game-engine-vs-engine-engine]] in a new costume, and this time *I* was the one thinking
in game terms. The recurring lesson has been about code that hardcodes domain facts; this is the
same error made by a reader rather than by the runtime.

**The genuine problem was never semantic, and the correction sharpens it.** Money at `2.25e-05`
beside features at `5e-01` is bad because **the network cannot resolve it**, not because $22.50
"should" look like something. Stripping the semantics away leaves a purely mechanical question —
how does a declared *unbounded* variable get scaled for a network? — which is exactly what
`PDR-0020`'s accepted call already routes to `range_type` and the log-scaled family.

**One option the correction re-opens.** With units nominal, re-scaling the pack — declaring
`money.bounds.max` in the low hundreds and scaling costs/payouts to match — costs *nothing
semantically*; it is a free choice, not a falsification of an economy. It does not replace the
`range_type` fix (an unbounded variable should not be minmax'd against any fixed ceiling —
that is what "unbounded" means), but it is a legitimate curriculum-authoring option to hold
alongside it rather than an alternative I had ruled out.

## Consequences

- **One escalation retired.** Three remain open for the owner: the `vision.md` flagship
  demonstrator, WS-1 freeze timing, and `config_hash_warning` (`PDR-0022`).
- **`hamlet-365e996511` is UNBLOCKED.** Its dependency on `hamlet-e979f2ba37` (author the
  curriculum) existed *only* because choosing a ceiling looked like a balance decision that
  needed the economy settled first. With units nominal, honouring `range_type` is pure VFS-layer
  wiring and can proceed independently. The dependency edge is removed.
- **`frontend/formatting.js` is RAISED, not downgraded — and my "cosmetic" reading of it was
  wrong.** The owner's second point is the load-bearing one: *do not "moneyfy" it for users.*
  Dressing a normalised variable as currency teaches students a false model of what the
  environment is, and pedagogy is this product's north star. `formatMeterValue` is defective on
  three counts, in increasing order of importance:

  1. **It is factually wrong post-WS-1(e).** It comments *"Money is 0-1 normalized"* — true only
     because of the hardcoded clamp that task 3a removed. Money now holds real magnitudes, so a
     22.5 balance renders as **"$2250"**, and `getMeterPercentage` (which does *not* special-case
     money) pegs the bar at **100%**. Both are simply broken.
  2. **It hardcodes a domain fact in the presentation layer.** `if (name === 'money')` is the
     frontend knowing what the game is — the same defect as
     `torch.clamp(meters, 0.0, 1.0)`, one layer out. A meter should render by its declared type,
     not by a name the code recognises.
  3. **It is pedagogically harmful**, which is the reason that decides it. This project already
     holds exactly this principle for space — CLAUDE.md, on `AspatialView`: *"Aspatial universes
     have no position concept — rendering a fake grid would be pedagogically harmful."* A fake
     dollar is the same error as a fake grid. Students should see money as a variable with a
     declared range, indistinguishable in kind from `energy`.

  Filed as `hamlet-0dd4ac24d9`. The fix is to **delete the special case**, not to correct the
  multiplier.
- **`vfs.md:739` needs no correction as a constraint** — it documents a convention nothing
  enforces. But its phrasing (*"`1.0` approximates `$100`"*) is the same moneyfication one layer
  up, and it is what led me to escalate a non-question. Worth a note when VFS is next edited.

## Reversal trigger

Reopen if **any** of the following:

- **Something outside the agent starts depending on the unit** — a pedagogical claim ("students
  see a realistic wage"), a scenario authored against real-world prices, or telemetry compared
  against an external benchmark. Then the denomination becomes load-bearing and needs deciding.
- **Two packs adopt incompatible money conventions** and a checkpoint or comparison crosses
  between them. Nominal units are fine per-universe; they are not fine if something silently
  compares across universes.
- **A pedagogical argument is made FOR moneyfication** — e.g. that a currency framing is what
  makes the Sims conceit land for students, and the trade is worth it. That is a real argument
  and it is the owner's to make; this PDR records that they made the opposite one.
