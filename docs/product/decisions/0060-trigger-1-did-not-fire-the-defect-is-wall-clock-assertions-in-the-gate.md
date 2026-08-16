# PDR-0060 — `PDR-0043` trigger 1 did not fire; the defect is wall-clock assertions inside the gate

Date: 2026-08-15   Status: **accepted** (adjudication, autonomous within the grant)
Author: Claude (standing product owner)
Owner sign-off: not required — this adjudicates whether a recorded reversal trigger fired, against
its own written condition. The reading is reported to the owner in this checkpoint's summary
because it touches the claim `metrics.md` makes about triggers.

Related: `PDR-0043` (CI restoration and its three triggers), `PDR-0059` (the other gate finding
this session), `PDR-0057` (the ~21% `env.step` cost, watch-do-not-act)
Tracker: `hamlet-f9090ec3e8` (rescoped this session, title changed to name the class)
Evidence: run `31870278368` FAILED at `bf0f2fe4`; run `31863730920` PASSED at `07b26ed5`

## Context

CI's Tests job went **red on `project-recovery-2`** at `bf0f2fe4`, on
`test_scripted_vtc_threshold_kernel_within_hardcoded_baseline_tolerance`. That test carries **no
`slow` marker**, so unlike `PDR-0059`'s 31 it runs inside the local gate set as well as CI.

`PDR-0043` reversal trigger 1 reads:

> **The first CI run on the branch fails for a cause the local gate set covers.** Then the
> "local four ⊂ CI set, difference now closed" claim is false again and this PDR's acceptance
> evidence was insufficient — reopen `hamlet-2100105c9a`, and the local-verification protocol
> (not just the fix) is what gets re-examined.

On the surface this matches: a CI failure, for a cause the local set covers. `metrics.md` also
carries the line *"No metric has fired a PDR reversal trigger yet"*, so getting this right matters
beyond the one issue.

## The reading

**The trigger did not fire, and the reason is what the trigger was protecting.** It protects one
specific claim: *the local gate set is a faithful subset of CI's, and the difference is closed* —
i.e. that CI cannot fail for a cause local gates never look at. That claim is not falsified here.
The local set **does** run this test. Local was not blind to it.

What failed instead is a weaker assumption nobody wrote down: that a green local run of a covered
test predicts a green CI run of the same test. It does not, because the test is nondeterministic:

    baseline_time = _measure(hardcoded_baseline, iterations=75)
    scripted_time = _measure(scripted_vtc,       iterations=75)
    assert scripted_time <= baseline_time * SCRIPTED_KERNEL_TOLERANCE   # 1.50

Two `time.perf_counter()` wall-clock measurements over 75 iterations, ratio-asserted, under
always-on `--cov=townlet --cov-branch`. It passed at `07b26ed5` and failed at `bf0f2fe4` on code
with no bearing on either kernel. This is CPU contention on a shared runner, measured through
coverage instrumentation that dominates the quantity under test.

That is the **same construction** as `test_vfs_overhead_under_limit`, filed 2026-08-15 as
`hamlet-f9090ec3e8`, which asserts a 5% wall-clock ratio between two envs under the same
instrumentation. Two instances, one shape.

## The call

1. **`PDR-0043` trigger 1 is adjudicated NOT FIRED.** `hamlet-2100105c9a` stays closed; the
   local-verification protocol is not reopened. The local/CI set-difference claim stands.
2. **`hamlet-f9090ec3e8` is rescoped from a test to a class** — *wall-clock ratio assertions
   inside the CI gate* — and retitled accordingly, with the second instance recorded on it. A
   fix that repairs one and leaves the other would close the issue and not the defect.
3. **`metrics.md`'s "no trigger has fired yet" line is kept, with this adjudication cited.** An
   unqualified "no" would be indistinguishable from nobody having checked.

The distinction is worth the words because the wrong call is expensive in both directions. Calling
it fired would reopen a correctly-closed issue and re-litigate a verification protocol that
worked. Calling it *nothing* would let a gate that reddens at random keep reddening — and a gate
that reddens at random is how a verified gate becomes a waved-through one, which is `PDR-0043`'s
own sentence.

## Consequences

1. Two known nondeterministic assertions sit inside the gate that `PDR-0058`'s exit condition now
   depends on. They are P2, not P1: unlike `PDR-0059`'s 31, they fail *loudly and visibly* rather
   than silently, which is the strictly better failure mode.
2. The fix direction is recorded, not chosen: move both out of the gating suite (the benchmark
   suite already exists and self-skips when `pytest-benchmark` is absent), or replace the
   wall-clock ratio with something deterministic. Deciding is the unit's job, not this PDR's.
3. `PDR-0057`'s watch-do-not-act on the ~21% `env.step` regression is **unaffected and still
   correct** — but note the interaction: a real performance regression and a flaky performance
   gate now coexist, and the flaky gate is what would make a real one unreadable.

## Reversal trigger

- **Reverse if CI reddens for a cause the local set covers and the test is deterministic.** Then
  the set-difference claim really is false, trigger 1 fires as written, and `hamlet-2100105c9a`
  reopens.
- **Reverse the "P2, fails loudly" reading if either test is ever waved through** — if a red run
  on one of them is dismissed as flaky without being executed and confirmed as flaky. At that
  point the loud failure has become a silent one by habit, and it graduates to P1.
