# PDR-0033 — A verification tool is not trusted until its own verdict contract survives adversarial review

Date: 2026-08-13   Status: **accepted** (within grant — accept against criteria; this records
both the acceptance of WS-7 content 3 and the standing practice the acceptance taught)
Author: Claude (standing product owner)
Related: `PDR-0032` (the harness accepted here), `PDR-0010` (the Gates-green lesson this
rhymes with), `PDR-0012` (no tech debt until 1.0)
Tracker: `hamlet-e3af412673` comment 132 · Filed from this review:
`hamlet-f894ade20a` (P1), `hamlet-1ec950ee60` (P3)

## Context

The differential harness was built TDD, reviewed per task, and passed a whole-branch review.
Acceptance criteria were met: full CPU matrix all-AGREE against the oracle, a mutation-verified
DIVERGE, four gates green. By the project's normal bar it was done.

A subsequent review wave — five reviewers with deliberately different lenses, one of them
briefed specifically to hunt *wrong verdicts* rather than bugs — then found **two defects that
would each have produced a false AGREE**, i.e. the harness certifying a broken rebuild as
correct:

1. **Shape blindness.** Agreement was decided by `old.tobytes() == new.tobytes()`, which
   serializes the buffer without the shape. Verified directly: `np.zeros((4,))` and
   `np.zeros((4,1))` compare equal. No provenance hash covers tensor rank, and `RunParams`
   constrains only the step and agent counts. A rebuild returning rewards as `[n,1]` instead
   of `[n]` — an ordinary refactor — would have AGREEd across the entire matrix.
2. **Unverified injection.** Nothing asserted that setting `PYTHONPATH` actually changed which
   `townlet` got imported. Had injection silently failed, both sides would have run
   working-tree code, every cell would trivially AGREE, and the whole programme's evidence
   would have been worthless — including every future knockdown judged by it.

Three further Important defects were found in the same wave (absent-vs-`None` hash keys, a
byte-count mismatch raising instead of diverging, and no per-cell containment so one exception
destroyed the report for cells already computed).

## Options

1. **Accept at the original bar** — criteria were met; treat the review wave as optional
   polish.
2. **Accept only after the adversarial pass, and make that pass standing practice for
   verification tooling.**
3. Defer acceptance pending a formal verification of the comparison logic.

## The call

**Option 2.** Both criticals sat in code that had already passed a per-task review *and* a
whole-branch review. What surfaced them was not more review but a *differently aimed* one:
a reviewer told that a false AGREE is the worst possible defect and asked to hunt it
specifically. Option 1 would have banked a green harness whose green was partly unearned —
the precise shape of `PDR-0010`'s Gates-green failure, where the cost was never the defects
but the months of false confidence. Option 3 is disproportionate for a local developer tool.

**Standing practice adopted:** any tool whose output is a *verdict about correctness* —
the differential harness, the register's adjudication, future knockdown gates — gets one
review pass whose explicit brief is "find the case where this reports success wrongly,"
before its verdicts are cited as evidence. Normal code review does not substitute; both
criticals survived it.

## Evidence at acceptance

`d54ad7df`, tree clean. Full suite **3035 passed / 16 skipped / 0 failed** (781s); ruff, black,
mypy clean. Full CPU matrix all-AGREE with CUDA cells reported `SKIPPED("cuda not requested")`
rather than silently absent (run `20260813-191816`); mutation-verified red — `+0.001` on the
DAC total reward → `DIVERGE` on `rewards` at step 0, `max_abs_diff` 0.001, exit 1 (run
`20260813-191900`), reverted clean; CUDA spot-check both AGREE (run `20260813-191915`). All
acceptance runs serialized after an earlier concurrent pair produced race artifacts.

**`PDR-0030`'s third reversal trigger is hereby tested and did NOT fire**: the harness
reproduces the oracle's traces from the recorded seeds on *both* devices. The oracle pin is
now validated by the instrument it was pinned for.

## Reversal trigger

- **If a knockdown is later found to have been judged by a false AGREE** — a defect reaching
  a rebuild that the harness reported as agreeing — this practice failed and the harness needs
  a stronger correctness argument than review (property tests over the comparison contract, or
  a formal one).
- **If the adversarial pass returns nothing on two consecutive verification-tool changes**,
  it has become ceremony; fold it back into normal review rather than performing it.
