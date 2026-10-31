# PDR-0089 — The blind re-run pair is O + B: the instrument is tested on both the accept and the reject branch

Date: 2026-08-19   Status: **accepted** (the pick is the owner's, per Appendix A.8)
Author: Claude (standing product owner)

Related: `PDR-0081` (protocol §7, blind re-runs), `PDR-0086` (Appendix A.8 — the owner
selects, not the standing agent), `PDR-0085` (Trial O), `PDR-0087` (Trial B)
Tracker: `hamlet-5fa1f7bfc0`
Artifacts: PRD-0001 criterion 3; records `docs/product/trials/0001/O-20260818.md` (pin
`a3318624`), `B-20260819.md` (pin `1ef1d950`)

## Context

PRD-0001 criterion 3 requires **two blind re-runs** before any north-star reading publishes.
Appendix A.8 reserves the pick to the **owner**, not the standing agent, and requires at
least one second-surface-dependent PASS from {L, M, O}. The pick had been outstanding since
trial three — five sessions — while trials kept raising the numerator. **No trial advances
publication; only the re-runs do.** It was surfaced at this resume as the single item on the
2026-10-06 critical path that only the owner could unblock.

## Options

1. **O + B** — the richest PASS and the only FAIL.
2. **L + O** — two PASSes, cheaper, reject branch untested.
3. **M + B** — lighter than O+B, still tests the reject branch.
4. **L + M** — cheapest; two short single-agent PASSes.

## The call

**Option 1 — O + B.** O satisfies A.8's {L, M, O} requirement; B supplies the FAIL.

## Rationale

A protocol that only reproduces PASSes is weak evidence for criterion 3. Reproducibility of a
**FAIL** is the harder and more informative test: it asks whether a second executor, given only
the corpus entry and the protocol, independently concludes that the substrate *cannot* express
the idea — rather than concluding they simply failed to find the surface. That distinction is
the exact ambiguity the whole instrument exists to resolve, and B (the first and only FAIL) is
the only trial that can test it.

O is the richest PASS available — six pre-committed facets, both legs, and the trial whose
verdict turned on a second surface found by source archaeology, which is precisely the
search-dependence A.8 wants the comparison to record.

Cost is real: O+B is the most expensive pair. It was chosen anyway because criterion 3's reject
branch fires on **any** verdict or classification disagreement, so the pair should be the one
most likely to surface a genuine disagreement if one exists.

## Standing obligations this creates

- Each re-run executes at **its own first run's pinned commit** (O at `a3318624`, B at
  `1ef1d950`) via `git worktree`, so criterion 3 tests protocol reproducibility, not substrate
  drift. This is reinforced by `PDR-0090`, which freezes the substrate for the corpus anyway.
- Per A.12/A.8, both re-runs use the protocol text **as of their own first run's pin** — O
  therefore runs *without* Appendix A; B runs *with* it.
- The blind executor must not open `docs/product/trials/` or any prior verdict.
- The comparer is the owner or an owner-appointed fresh agent, **never the original executor**.
- **If O is chosen the comparer is pre-briefed that the first run's facet 4 never exercised the
  tie case** (A.8). That pre-brief is now owed and is recorded in `current-state.md`.
- The comparison records the **surface path**, not only the verdict: same headline via a
  different surface is a search-dependence finding even when the verdicts agree.

## Reversal trigger

If either re-run disagrees with its original on **headline verdict or any facet
classification**, PRD-0001 criterion 3's reject branch fires: the protocol is underspecified,
**the instrument is NOT accepted, and no north-star reading publishes** — regardless of how
many trials have been run. The recorded diagnosis (protocol ambiguity vs. search variance)
informs what is rebuilt, not whether the branch fires.
