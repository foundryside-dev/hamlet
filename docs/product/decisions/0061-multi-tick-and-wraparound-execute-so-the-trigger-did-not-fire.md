# PDR-0061 — `multi_tick` and wraparound hours execute; `PDR-0059`'s escalation trigger did not fire

Date: 2026-08-16   Status: **accepted** (adjudication + delivery, autonomous within the grant)
Author: Claude (standing product owner)
Owner sign-off: not required — this adjudicates a recorded escalation trigger against its own
written condition, and reports the reading rather than acting outside it.

Related: `PDR-0059` (the gate hides 31 failures; this trigger), `PDR-0045` (never branch on a
variable's name), `PDR-0049` (the comfortable diagnosis is the unverified half)
Tracker: `hamlet-551be983a8` (closed), `hamlet-a0832f9004` (closed)
Evidence: commit `e62a5e4a`; live runtime probes recorded below

## Context

`PDR-0059` split 10 temporal tests out of the 31 hidden failures because they needed a config the
shipped pack does not contain: an affordance that is `multi_tick`, and one whose schedule crosses
midnight. It attached an escalation trigger to that split:

> **The real prize.** This is the first execution of `multi_tick` and wraparound hours anywhere in
> the tree. If they work, coverage is restored AND two declared surfaces are verified live. **If
> they do not work, that is a live product defect** and it escalates to the owner with a repro.

That fork had to be settled by execution before a single test was written, because the two
branches lead to completely different work: repair, or escalate.

## The reading

**Both surfaces execute. The trigger did not fire.**

Measured on a re-parameterized copy of the shipped L3 pack, driving a real `VectorizedHamletEnv`:

| surface | result |
|---|---|
| wraparound (`start: 18, end: 28`) | OPEN at 20:00, **OPEN at 02:00 across midnight**, CLOSED at 05:00, CLOSED at 12:00 |
| `multi_tick` (`duration_ticks: 4`) | progress `0→1→2→3→0`, resetting exactly at the declared duration |
| `costs_per_tick` | charged **every tick** — 500 → 495 → 490 → 485 → 480 |
| `per_tick` effects | fire (the meter holds flat against decay instead of falling) |

The 02:00 reading is the one that matters: the non-wrapping branch reports CLOSED there, so that
single observation distinguishes the two code paths at `world/expression/functions.py:741`.

**The tests were red because the pack lacked the parameters, not because the engine lacked the
capability.** That is the opposite polarity to `PDR-0049`'s warning, and it was only established by
running the thing — the issue's own write-up had asserted the capabilities were "implemented" on
the strength of a schema literal and a source line, which is exactly the evidence standard
`CLAUDE.md` says never to trust.

### The near-miss worth recording

The first probe showed `interaction_progress` pinned at 0 for six steps and would have read as a
clean confirmation of a live product defect. It was not. `can_afford` was returning False because
the probe set every meter to 1.0 and the affordance costs `money: 5.0` — the agent had $1 and
needed $5. **The engine was correct and the instrument was wrong.** Instrumenting each gate on the
path (`has_multi_tick_affordances` → `contains_affordance` → `_is_affordance_open` →
`is_on_position` → `can_afford`) is what separated them; a fifth of a step further and this
checkpoint would have escalated a working engine to the owner as broken.

This is the second time in two sessions that a measurement, not a diagnosis, stopped a false
escalation — the first being the `masks[0, 4]` INTERACT index.

## The call

1. **Repair, do not escalate.** The 10 tests are repaired against a purpose-authored pack.
2. **The test pack re-parameterizes; it never extends.** A 15th affordance is rejected by the
   compiler with `AFFORDANCE_VOCAB_MISMATCH`, cross-validated against `environment.yaml`. This is a
   genuinely good finding: the "fixed affordance vocabulary for transfer learning" property that
   `CLAUDE.md` documents is **mechanically enforced**, not merely written down.
3. **Assertions derive from declared constants, and are verified red by mutation.** Three mutants,
   each killing exactly the test that claims the mutated behaviour:
   - wrapping branch `|` → `&` → only `test_wraparound_hours_cross_midnight`, at the 02:00 line
   - `duration_ticks` ignored → 8 multi-tick tests
   - `costs_per_tick` moved to the completion tick → only `test_money_charged_per_tick`
4. **A hardcoded index into a compiled vocabulary is a `PDR-0045` name-branch wearing a number.**
   The repaired tests resolve INTERACT, meter columns, and even an "empty" grid cell from the
   compiled artifact. The last of these was a real flake: `[3, 3]` is empty or not depending on
   where deployment put things that run.

## Rationale

The alternative — point the tests at a shipped always-open instant affordance — was explicitly
rejected in `PDR-0059` and remains rejected. It produces a green `test_wraparound_hours` that
exercises zero wraparound logic. **A vacuous green is strictly worse than a red**, because a red is
visibly work-to-do and a vacuous green is indistinguishable from coverage. That is the same failure
class as the marker deselection this whole thread began with.

## Reversal trigger

**If any shipped pack ever declares a `multi_tick` affordance or a wrapping schedule, this test
pack stops being the coverage of record and must be re-pointed at the real one.** A test pack that
is the *only* exerciser of a surface is a stopgap for an unauthored demo, not a destination — the
framework's claim is that packs express this, and no shipped pack yet does.

Secondary: **if `interaction_type` becomes required with a single vocabulary** (`hamlet-45b35cfee5`),
the fixture's parameter-setting must be re-read, because it currently relies on the hidden
`or "instant"` default for the 11 affordances it does not touch.
