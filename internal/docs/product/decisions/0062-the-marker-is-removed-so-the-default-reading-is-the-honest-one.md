# PDR-0062 — the `slow` marker is removed from the three files, so the default gate reading is the honest one

Date: 2026-08-16   Status: **accepted** (autonomous within the grant)
Author: Claude (standing product owner)
Owner sign-off: not required — a test-selection change on a recovery branch, reversible in one line.

Related: `PDR-0059` (the gate hides 31 failures behind a marker), `PDR-0043` (a gate restored is
not a gate verified), `PDR-0010` (recorded green while three of four were red)
Tracker: `hamlet-a0832f9004` (closed), `hamlet-6f98e38a36` (filed, blocks the remaining half)
Evidence: full default suite at `e62a5e4a` — 3189 passed, 16 skipped, **2 deselected**, 0 failed

## Context

`PDR-0059` deliberately sequenced this last: *"decide whether `-m 'not slow'` belongs in default
`addopts` — belongs to whichever unit closes `hamlet-551be983a8`."* The reason for deferring it was
to keep the repair measurable; the risk of deferring it was that the invisibility defect — the
actual reason the issue existed — would survive the issue that was filed to kill it.

The mechanism, restated: `pyproject.toml` carries `-m "not slow"` in the **default** `addopts`, and
three integration files carried `pytestmark = pytest.mark.slow`. Every gate reading, local and CI's
`tests.yml`, was therefore blind to them. The deselect count printed in every reading for weeks and
was read as *tests that are slow*, never as *tests that are red*.

## The measurement

The word "slow" was never checked against a clock. It is false:

| | tests | wall clock |
|---|---|---|
| the three files, all passing | 31 | **34.8s** |
| `test_differential_harness.py` | 2 | 0.15s (fails fast) |

31 integration tests in 35 seconds is not a slow suite. The marker was not describing runtime; it
was, in effect, a suppression.

## The call

**Remove `pytestmark = pytest.mark.slow` from the three repaired files.** The default suite now
runs them. Each file carries a comment saying why the marker is absent, so it does not get
helpfully restored.

**Keep `-m "not slow"` in `addopts` for now**, and say exactly what it still hides: two tests, in
one file, with a filed P1 (`hamlet-6f98e38a36`). Deselection with a named disposition is a
different object from deselection with none — that is the rule `metrics.md` adopted last session
and this is its first application.

Result: deselected falls **33 → 2**, and the arithmetic is exact — 3157 + 31 previously-hidden + 1
new contract test = **3189**.

## Rationale

The obvious move was to delete `-m "not slow"` outright and be done. That was rejected on
measurement, not principle: the differential harness's two tests **fail**, so deleting the entry
would leave the default suite red on a defect that belongs to WS-7 and needs oracle context to
resolve. Trading a hidden red for a permanently red gate teaches everyone to ignore the gate, which
is `PDR-0010`'s corrosion arriving by a different road.

Removing the marker from the three files gets the substance of the fix — 31 tests move from
invisible to gated — without that cost. The residual is one file, one issue, one line to delete
when it closes.

**What this does not claim.** `Gates green` is now green over a suite that still excludes two known
failures. Per this row's own rule, that exclusion is stated with its disposition rather than banked.

## Reversal trigger

**When `hamlet-6f98e38a36` closes, `-m "not slow"` comes out of `addopts` in the same commit.** If
that issue is still open at the next checkpoint, this PDR is the record that the gate is
*deliberately* narrower than the suite, and the next session must re-state the exclusion rather
than inherit it silently.

**If any file acquires `pytest.mark.slow` again without a wall-clock measurement in its commit
message**, this decision has failed and the marker should be deleted from the project outright.
