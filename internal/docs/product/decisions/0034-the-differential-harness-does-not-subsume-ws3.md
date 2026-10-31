# PDR-0034 — The differential harness does NOT subsume WS-3; the wiring-test mandate is untouched

Date: 2026-08-13   Status: **accepted** (within grant — a scope correction to recorded intent,
not a new bet; it re-opens no settled decision and commits no new work)
Author: Claude (standing product owner)
Related: `PDR-0032` (the harness this corrects the scope of), `PDR-0006` (the strangler),
`PDR-0016` (the inert-surface pattern), `PDR-0007` (not-yet-enabled vs inert)
Tracker: `hamlet-1f89714685` (WS-3, still `open`, still blocked by `hamlet-337b9e80fb` and
`hamlet-e3af412673`), `hamlet-15050f280a` (WS-4, gated by WS-3)

## Context

`roadmap.md` has carried the claim, since the strangler was chosen, that **"WS-3 is reshaped
into the differential harness and becomes the program's central artifact"** — sourced from
WS-7's own issue text (*"This reshapes WS-3: largely self-writing, since it need not know the
right answer, only that old and new agree"*).

Reconciling the tracker at this checkpoint, that claim does not survive contact with what
WS-3 actually says it is. WS-3 (`hamlet-1f89714685`) is the **wiring-test category**: *take a
YAML file, change a value, assert the runtime behaviour changed* — plus two mechanical rules
(every schema field must appear at a non-default value in some pack with a test asserting its
behavioural effect; every enumerated `stratum.yaml` value must compile and build an env). Its
stated purpose is the assessment's root-cause finding: **not one test in the repo does this,
and that absence is *why* six consecutive declarative features shipped inert.**

The differential harness answers a different question. It asks *did old and new behave the
same?* It cannot ask *does this declared surface drive behaviour at all?* — because **a field
that is inert in the oracle and inert in the rebuild produces identical traces, and the
harness correctly reports AGREE.** Inertness is invisible to a differential instrument by
construction. The harness would have happily certified every one of the ~40 inert surfaces the
assessment found.

## Options

1. **Leave the roadmap claim standing** — the harness is delivered, treat WS-3 as substantially
   discharged and let WS-4 proceed on it.
2. **Correct the claim: the harness discharges part of WS-7, none of WS-3.** WS-3's wiring-test
   mandate remains open and still gates WS-4.
3. Re-scope WS-3 down to whatever the harness does not cover, as a new smaller bet.

## The call

**Option 2.** Option 1 is the dangerous one and it was one checkpoint away from happening: it
would have let WS-4 — *the actual product work*, closing the "you must write Python" gaps —
proceed with its acceptance criterion believed satisfied by an instrument structurally
incapable of satisfying it. The failure mode is exact and already has a name here: the next
declarative feature ships inert, and the guardrail that was supposed to catch it reports green.
That is `PDR-0010`'s lesson wearing a different hat.

Option 3 is premature; nothing has been measured about how much of WS-3 remains, and WS-3's
own mechanical rules are the cheapest way to *enumerate* the remaining inert set. Re-scoping
before running them would be guessing.

**What the harness does discharge:** WS-7 content 3, and the *regression* half of the
strangler's safety net — a rebuild that changes preserved behaviour now fires. What it does
not discharge: any claim that a declared surface is wired at all.

## Consequences

- `roadmap.md`'s Now bullet is corrected in this checkpoint. WS-3 stays `open` and stays
  blocking WS-4.
- No new work is committed by this PDR. WS-3 remains blocked by WS-2 (`hamlet-337b9e80fb`)
  and WS-7 (`hamlet-e3af412673`) as the tracker already records.
- The two instruments are complementary and should be stated as such wherever either is
  described: **differential = did behaviour change; wiring = does the declaration do anything.**

## Reversal trigger

- **Reverse if a concrete mechanism is demonstrated** by which a differential run detects an
  inert declared surface — i.e. someone shows a harness cell that fails when a config field
  drives nothing. That would mean this correction was wrong and WS-3 really is subsumed.
- **Revisit the scope of WS-3** (Option 3) once its mechanical rule 1 has been run once and
  the remaining inert set is enumerated rather than estimated — at that point re-scoping is
  measurement-led instead of guesswork.
