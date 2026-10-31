# PDR-0035 — The first knockdown unit is the substrate→observation-dim SEAM, and it subsumes WS-4's line-227 item

Date: 2026-08-14   Status: **accepted** (within grant — prioritize / dispatch; a scope call
inside the committed Now bet, not a new bet. Same shape as `PDR-0034`.)
Author: Claude (standing product owner)
Related: `PDR-0006` (the strangler), `PDR-0019` (the selection criterion this satisfies),
`PDR-0032` (the harness that judges the knockdown), `PDR-0034` (the precedent: a scope claim
corrected before it did damage)
Tracker: `hamlet-e3af412673` (WS-7 content 5), `hamlet-15050f280a` (WS-4 — scope narrowed by
this PDR)

## Context

WS-7 content 5 is *seam cutting, per knockdown unit*. Cutting a seam requires knowing where
the unit boundary falls. Terrain/substrate has been the nominated first knockdown since the
stream was written, on the strength of one line in the maturity assessment: *"three of the
four crashes collapse to one change."* The nomination had never been checked against source,
and the boundary had never been drawn.

Drawing it is not bookkeeping. The boundary decides whether the nomination's justification
survives at all.

## Options

1. **Unit = the `substrate/` package.** Rebuild the substrate implementations and their ABC.
2. **Unit = the substrate→observation-dim seam** — the contract by which the compiler learns
   a substrate's observation shape, spanning `substrate/` and the compiler pass that consumes
   it.
3. **Unit = the one-line repair** at `universe/compilers/observation.py`, treated as a
   knockdown.

## The call

**Option 2.**

Verified at `58ace08f`, reading `src/townlet/universe/compilers/observation.py`:

- `:64-76` derives `grid_cells` by switching on `substrate.type` string literals
  (`grid`/`grid3d`, then `gridnd`).
- `:135-145` derives `position_dim`/`velocity_dim` by switching on the same strings again —
  four more branches, including `position_dim = 3 if substrate.grid.topology == "cubic" else 2`,
  the compiler hardcoding what a topology means.
- `:146-155` — `continuous`/`continuousnd` **already do it correctly**: build the substrate
  instance via `SubstrateFactory` and ask `get_observation_dim()` and `.position_dim`, with a
  comment stating the rule outright — *"compiler observation dimensions must come from the
  runtime substrate implementation."*

So the correct pattern is present **in the same function**, applied to two of five substrate
types, and the other three are string-switched. This is `PDR-0019`'s selection criterion
verbatim — *strangle wherever the runtime still knows what the game is* — and it is a
stronger reason to pick this unit than the crash count was.

**Option 1 is the dangerous one.** The crashes are caused by the *compiler*, not by
`substrate/` (the assessment's own words: *"`substrate/` has the right ABC"*). A knockdown
scoped to the package would leave every crash intact and the nomination's stated justification
unmet — while looking like progress. Option 3 inverts the strangler: a one-line repair does
not need an oracle, a harness, or a register, and dressing it as a knockdown would burn the
programme's first knockdown on something that proves nothing about the method.

## Consequences

- **WS-4's line-227 item is subsumed.** The assessment
  (`docs/product/assessments/2026-08-11-maturity-assessment.md:227`) files *"delegate substrate
  observation dims to the substrate instance in `compilers/observation.py:64-150` (fixes three
  of four substrate crashes in one change)"* under WS-4, gated behind WS-3. Under this boundary
  it is inside the first knockdown instead. WS-4 is narrowed accordingly; it does **not** wait
  on WS-3 for this item, because the knockdown carries its own instrument (the harness) rather
  than borrowing WS-3's.
- This narrows WS-4 by exactly one item and **changes nothing else about WS-3's mandate**.
  `PDR-0034` stands: the harness does not subsume WS-3, and WS-3 still gates the rest of WS-4.
- The fourth substrate crash (`type: grid3d` has no factory branch — `factory.py:152`) is
  inside the same seam and is carried by the knockdown, not left behind.

## Reversal trigger

- **Reverse the boundary** if cutting the seam shows the compiler-side change cannot be made
  without also rebuilding substrate internals that are out of the unit — i.e. the seam is not
  actually a seam. At that point the unit is genuinely `substrate/`-plus-compiler and the
  knockdown is larger than scoped; re-scope explicitly rather than letting it grow.
- **Revisit the subsumption** if WS-4 begins before this knockdown completes. Two streams
  holding one item is the failure `PDR-0034` caught; if WS-4 starts first, the item goes back
  to WS-4 and this knockdown narrows to the remaining seam.
