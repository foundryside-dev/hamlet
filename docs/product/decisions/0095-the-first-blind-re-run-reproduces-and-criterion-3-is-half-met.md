# PDR-0095 — The first blind re-run reproduces O's PASS, §7's reject branch does not fire, and criterion 3 is HALF met — the discriminating re-run has not run

Date: 2026-08-20   Status: **accepted** (within the grant: dispatch delivery, accept against criteria)
Author: Claude (standing product owner)

Related: `PDR-0089` (the re-run pair is O + B), `PDR-0081` (protocol active), `PDR-0086`
(Appendix A, construct preamble), `PDR-0096` (the amendments this run produced)
Artifacts: `docs/product/trials/0001/O-blind-20260820.md` (blind record),
`docs/product/trials/0001/O-comparison-20260820.md` (adjudication + standing-agent addendum §9),
pin `a3318624`, packs `configs/trial_o_bidding_blind/`

## Context

PRD-0001 criterion 3 requires **2 of the 9 trials re-run blind**, reproducing their verdicts, or
the instrument is not accepted and **no north-star reading publishes**. `PDR-0089` chose the pair
(O + B) but neither had run. The owner chose the blind re-run over trial seven at this resume.

## Options

1. Run trial seven (D, E or J) — moves the numerator, leaves publication blocked.
2. Run a blind re-run — moves publication, and de-risks three further trials whose readings could
   be rejected wholesale if the instrument fails criterion 3.

## Call

**Option 2, idea O**, executed by a fresh agent in a `git worktree` at the first run's pin
`a3318624`, then adjudicated by a **second** fresh agent because A.8 bars the original executor
and the standing agent executed run 1.

**Result: blind PASS, run 1 PASS, 6 mapped facet pairs, 6 agreed, 0 differed. §7's reject branch
does NOT fire. The instrument is ACCEPTED on criterion 3 for idea O.**

## Rationale, and the honest limit on it

A blinding hazard was real and the protocol caught it without intervention: today's Appendix A
would have leaked the verdict outright (A.8 names O as a candidate second-surface-dependent PASS;
A.4 cites *"Trial O's auction effect… survive reset"*), but Appendix A's own scope rule already
ruled that a re-run of a completed trial executes under the protocol text as of its pin — which
predates the appendix. No redaction by the standing agent was needed, and none was made.

**The comparison refuses to bank the win, and the refusal is adopted here.** Agreement between two
all-PASS records is cheap: with zero failing facets the classification comparison §7 specifies is
vacuous by construction, and §7's discriminating power was never exercised on this idea. The "no"
rests instead on two results that could have gone otherwise: two non-communicating executors
**converging on the same load-bearing surface** (`for_each: all_agents` + global VFS scratch +
running max, reached second, found only by reading source), and **exact agreement on the
ABSENT/INERT classification** of both gaps both runs found.

**Criterion 3 is therefore HALF met, and is recorded that way** (comparison §9.5, `metrics.md`).
1 of 2. **Idea B is the discriminating re-run** — a FAIL carrying BLOCKED facets, so it is the
first re-run that will actually exercise the classification comparison the reject branch turns on.

The four differences §7 does not name are recorded, not waved: facet cardinality (6 vs 8), evidence
depth (run 1 never exercised the tie case), base pack, and surface path on 4 of 6 mapped pairs.

Guardrails: full suite **3281 passed / 16 skipped / 0 failed, exit 0** with the blind pack in the
tree; pack `validate` exit 0; blind worktree removed and pruned.

## Reversal trigger

**No north-star reading publishes until idea B's blind re-run has run and agreed.** If B's re-run
disagrees on any verdict or classification, §7's reject branch fires, the instrument is not
accepted, and this PDR's "accepted for idea O" does not survive it — one agreeing cheap comparison
does not outvote one disagreeing discriminating comparison. Additionally: if a later reader finds
that the O comparison's mapping was wrong (a run-1 facet without a counterpart, contra its §2.1),
reopen the adjudication.
