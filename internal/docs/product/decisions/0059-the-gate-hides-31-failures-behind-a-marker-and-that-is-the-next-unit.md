# PDR-0059 — the gate hides 31 failures behind a marker, and closing that is the next unit

Date: 2026-08-15   Status: **accepted** (prioritization, autonomous within the grant)
Author: Claude (standing product owner)
Owner sign-off: not required — *"prioritize the backlog"* is in the autonomous list. The finding
was surfaced to the owner in the same session's ORIENT brief before this call was made.

Related: `PDR-0010` (a gate recorded green while red — the original pattern), `PDR-0043` (a gate
restored is not a gate verified), `PDR-0049` (a red found by reading is not a defect until it
executes), `PDR-0012`/`PDR-0013` (strict no-tech-debt until 1.0)
Tracker: `hamlet-a0832f9004` (filed this session, P1)
Evidence: GitHub Actions run `31869712709`, branch `main`, 2026-08-15 06:32Z

## Context

The nightly Full Test Suite was restored on `main` at the merge, discharging `PDR-0043` reversal
trigger 2. **Its first scheduled run failed: `31 failed, 3120 passed, 24 skipped`.**

All 31 failures sit in three files — `test_temporal_mechanics.py` (15), `test_training_loop.py`
(8), `test_recurrent_networks.py` (8) — and all three are `pytest.mark.slow`. `pyproject.toml`
carries `-m "not slow"` in the **default** `addopts`, so:

- the local four/six gates run `uv run pytest` and deselect them,
- CI's `tests.yml` runs bare `uv run pytest` and deselects them,
- only `full-tests.yml` (`-m "slow or not slow"`) runs them.

That deselection is the *"35 deselected"* that has appeared verbatim in `Gates green` readings in
`metrics.md` for weeks. Nobody was hiding anything; the number was printed every single time. It
was read as a category of tests that were slow, and never as a category of tests that were red.

The cause profile is uniform in kind: `VectorizedPopulation.__init__()` missing 4–5 required
positional arguments (11 failures), affordance-not-deployed assertions against the test config
(10), a `FileNotFoundError` on a `configs/default_curriculum/…` path (3), *"ObservationSpec-driven
slicing is required in v2.1; legacy positional layout is no longer supported"* (2), a missing
`next_observations` key (1). That reads as tests left behind by the very changes this recovery has
been making — but **that is a reading of error text, not an execution.** `PDR-0049` applies with
its polarity reversed for once: the red is unquestionably real (it executed, in CI, on the default
branch), while the comfortable diagnosis *"just stale tests"* is the unverified half.

## Why this outranks the queued authoring work

`current-state.md` sequenced `hamlet-2fe1c34ebb` (`semantic_type`) next, and it is a good unit —
same shape as the surface just closed, same ruling, worked example ready. It is being displaced by
one position, not dropped.

1. **`vision.md`'s tech-debt anti-goal names this first.** Its list of what counts as debt opens
   with **failing gates**, and it forecloses the deferral explicitly: *broken-but-unreached is
   still broken*. There is no "it's only test code" exemption in this product, by owner statement.
2. **It is red on the public default branch.** `main` is public. The nightly will now fail every
   night until this is closed, which re-arms precisely the corrosion `PDR-0043` deleted the cron
   to avoid — except the previous red stream was against a stale `main` nobody was working on, and
   this one is against the live one.
3. **`test_training_loop.py` is the training loop.** This product's entire claim is *author a
   universe and train agents against it*. Eight integration tests over that path have been failing
   unseen.
4. **It corrupts the instrument the strangler is steered by.** Every `Gates green` reading since
   the marker landed is qualified. `PDR-0058`'s restated exit condition requires an unhidden
   suite, so this blocks the exit as now written.

## The call

`hamlet-a0832f9004` is the next unit, ahead of `hamlet-2fe1c34ebb`. Its scope, in order:

1. **Run the three files locally and diagnose by execution**, not by error text — which failures
   are stale tests, which (if any) are live product defects. This ordering is `PDR-0049`'s rule
   and the pre-cut-census lesson from `PDR-0057`: point the instrument at the code before
   committing to the shape of the fix.
2. **Repair or delete per zero-backcompat.** A test pinning an API that no longer exists is
   deleted, not adapted — `git history preserves it`. A test pinning behaviour that *should* still
   hold is repaired and stays.
3. **Then decide the marker's fate** — whether `-m "not slow"` belongs in default `addopts` at
   all. Stated as step 3 deliberately: fixing the deselection before fixing the tests would turn
   every local gate red and make the repair unmeasurable.

## Consequences

1. `hamlet-2fe1c34ebb` moves to second. Nothing else in the queue reorders.
2. `metrics.md`'s `Gates green` row is re-stated so that a reading which excludes tests must say
   what it excluded and why — a count with no disposition attached is how this happened.
3. The `PDR-0010` pattern gains its sixth recorded instance, and its first where the gate was
   genuinely being run, genuinely green, and genuinely incomplete at the same time. The prior five
   were gates that were not run, not read, or unfalsifiable. This one was all three of run, read,
   and honest — and still wrong, because the *scope* of the command was never audited.

## Reversal trigger

- **If step 1 finds these are predominantly live product defects rather than stale tests**, this
  stops being hygiene and becomes a correctness bet: it escalates to the owner with the defect
  list before any test is deleted, because deleting a test that is correctly failing is how a real
  defect gets buried.
- **If the repair cannot be completed without touching production APIs that the strangler is about
  to knock down anyway**, stop and re-sequence behind that knockdown — repairing a test against an
  API scheduled for deletion is work performed twice.
- **If a `Gates green` reading is ever taken again from a command that excludes tests without
  saying so**, this PDR failed at the thing it was for, and the fix moves from documentation
  discipline to mechanism (a gate script that refuses to report green with a nonzero deselect
  count).
