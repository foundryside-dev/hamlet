# PDR-0063 — the differential harness's self-comparison disagrees, so it currently certifies nothing

Date: 2026-08-16   Status: **superseded in part** by `PDR-0065` (same day)
Author: Claude (standing product owner)

> **What stands:** the finding — both self-tests fail, the hidden count was 33 not 31, and the
> deliberate non-action was correct for the session that filed it. **What is superseded:** the
> framing. The fork this PDR posed — *re-freeze vs register* — had already been decided by
> `DIV-004` (register; fixture stays at the old schema) the day before, and the headline *"cannot
> currently certify anything"* overstated it: the **matrix** certified the meter cut at `2535a306`;
> the **self-tests** were the defect — `run_cell` named the old side by code root alone. Both
> reversal triggers below are discharged: the issue closed at the first checkpoint after filing.
> Body below untouched.
Owner sign-off: **not required to file this, but the fix is a strangler specification call and is
flagged to the owner in this checkpoint's summary.**

Related: `PDR-0062` (the marker removal this blocks), `PDR-0040` (the harness's exit contract),
`PDR-0037` (the harness's unreadable red), `PDR-0043` (a gate restored is not a gate verified)
Tracker: `hamlet-6f98e38a36` (P1, filed this session)
Evidence: `test_differential_harness.py` → **2 failed in 0.15s** at `2ba1f530`

## Context

Settling `PDR-0062` meant enumerating everything the `slow` marker hides. Three files were known.
There is a **fourth**: `tests/test_townlet/integration/test_differential_harness.py`, marked slow at
line 18, deselected by the same default `addopts`, and never counted in the 31.

**The true hidden-failure count when `hamlet-a0832f9004` was filed was 33, not 31.** That issue
enumerated the failures from a CI log listing three files and reasoned about the marker mechanism
correctly, but never asked the complementary question: *what else does that marker cover?*

## The finding

Both tests fail, in 0.15 seconds:

- `test_self_comparison_agrees`
- `test_driver_failure_is_a_loud_side_error`

The first is the serious one. It runs the harness with `old_src` and `new_src` **both pointed at
`src`** and expects the verdict `AGREE`. It does not agree:

```
{'delta': {'differing': ['environment.yaml']},
 'fix': 'Either re-freeze the fixture (the change was not a schema divergence)
         or register it in known-divergences.md',
 'frozen_root': '/home/john/hamlet/oracle_fixtures',
 'pack': 'configs/default_curriculum'}
```

**A differential harness whose self-comparison disagrees cannot certify anything.** It is the
instrument the whole strangler rewrite is measured with: `docs/oracle/ORACLE.md` holds that *"a diff
against the oracle is a defect in the rebuild unless the register says otherwise"*, and that
sentence is only load-bearing if the instrument returns AGREE when there is nothing to disagree
about. Any "no divergence" reading taken through this harness while it is in this state is worth
nothing.

The second failure is a verdict-vocabulary mismatch — expected `OLD_SIDE_ERROR`, got
`HARNESS_ERROR` — which is `PDR-0040`'s exit contract drifting from the tests that pin it.

## The call

**File it; do not fix it in this unit.** Two reasons, and the second is the real one:

1. **Scope.** This session was chartered on two named issues. This is a third, in a different
   subsystem (WS-7, `hamlet-e3af412673`, already in progress).
2. **The fix is a fork between two materially different decisions, and it is not mine to take
   casually.** The harness itself says so: *re-freeze the fixture, or register the divergence*.
   Re-freezing silently redefines what the oracle attests; registering asserts the difference is
   accepted behaviour. The pinned oracle exists precisely to stop that choice being made in
   passing, by whoever is nearby. It needs someone holding the oracle context.

What this unit did instead: measure it, file it with the verdict text, and record it as the thing
blocking `PDR-0062`'s second half.

## Rationale

The tempting move was to re-freeze the fixture — it is one command, it turns the suite fully green,
and the harness's own message lists it first. That is exactly the move the strangler discipline
forbids without a decision, and doing it to tidy a checkpoint would be the purest form of
`PDR-0010`'s corrosion: **making the instrument agree with the code instead of finding out why it
does not.**

## Reversal trigger

**If `hamlet-6f98e38a36` is still open at the second checkpoint from now**, the harness has been
unable to certify for three sessions and the strangler's core claim — "diff against the oracle" — is
running on an unverified instrument. At that point it stops being a filed bug and becomes the Now
bet's blocking item, ahead of authoring-surface work.

**If any session records a "harness green" or "no divergence" reading before this closes**, that
reading is void and this PDR is the reason.
