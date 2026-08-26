# Current State — HAMLET / Townlet        Checkpoint: 2026-08-26 · forty-fifth checkpoint (`PDR-0124`, `PDR-0125`: **unit 3 LANDED — the observation ABI is a compiled TokenSpec and spec §5 held on all ten cells — with reversal trigger 3 FIRED and escalated to the owner**)

## The bets right now

**1. Token-observation encoding** (`PDR-0108`/`PDR-0114`) · tracker `hamlet-fa6bb6da4a`.
**UNIT 3 IS COMPLETE.** Tasks 1–11 all landed, reviewed, and pushed.
- The cut: `TokenSpec` is the observation ABI; the fixed-width superset with a per-level
  activity mask is gone, along with the raster/window encoders and the engine temporal block.
- **Spec §5 HELD on 10 of 10 cells, both modes** — `actions`/`dones`/`rewards` byte-exact,
  only `obs` diverges. Matrix exit 0 (`20260826-172349` / `20260826-172441`); suite 3278/0.
- DIV-008 **bound** to a measured 5-field set; DIV-006 + DIV-011 retire into it; DIV-010
  stands. `scripted_actions` stays False.
- **⚠ Trigger 3 FIRED: 1132 dims = 9.43× vs an 8× cap. ESCALATED (`PDR-0124`) — the owner's
  call, four costed options. No lever taken, cap not edited.**
- Nine defects land OPEN and RECORDED (`hamlet-6a4a6596bd`, `-559cc74246`, `-4538ba909f`,
  `-aba6171ff7`, `-81bf807963`, `-d76684f549`, `-1e335e0363`, `-2aca57c0f0`, `-5a87550adb`);
  one BLOCKED and was fixed first (`hamlet-02684be106`, L3 declaratively observable again).

**2. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Steady; the
compiler cleanup landed earlier this session (`PDR-0121`) and its stage enum incidentally
satisfied WS-5's first prerequisite.

**3. Documentation truth** (`PDR-0125`, owner-authorised). 53 files recovered from the
archive with 51 dated staleness banners; the corpus REWRITE is gated on WS-4.

**4. Measure the authoring claim** — retired as record (`PDR-0111`), unchanged.

## What this checkpoint did

- Recorded `PDR-0124` (the cut adjudicated; unit lands; trigger 3 escalated) and `PDR-0125`
  (the archive was sorted by appearance — recovery is labelling, the rewrite is gated).
- Metrics: the §5 verdict, the 9.43× reading, the two demoted matrix cells, and the
  documentation-truth numbers, all dated.
- Tracker: 11 tickets filed this session, 3 commented, discharge closures on
  `hamlet-fa6bb6da4a`'s unit-3 vehicles.

## Standing gates & in-flight state (read before acting)

1. **The trigger-3 decision gates unit 4/5 sequencing.** Nothing downstream should assume a
   width answer until the owner rules.
2. **The doc rewrite stays blocked** on `hamlet-ad2773718a` (generate from consuming code
   paths, not Pydantic models). Prereq 1 satisfied by `PDR-0121`; prereq 2 needs WS-4.
   Labelling-only work is not blocked and is done.
3. **Two matrix cells are demoted as evidence** — `div003_scaled` and `items_smoke` pass
   while no longer measuring their own axes. Never cite them for those axes.
4. The §5 finding is **CPU-only**; all CUDA cells SKIPPED.

## Reversal triggers — state

- **`PDR-0114` trigger 3: FIRED at 9.43×, escalated, unresolved.** The live one.
- `PDR-0114` trigger 1 armed with its denominator (≥79.19 IQM at equal env-steps) — not yet
  read post-cut; that is a unit-4/5 measurement.
- `PDR-0125` armed (if WS-4 lands and docs still cannot generate from consuming paths, the
  doc strategy reopens).
- Pack-disposition clock **2026-10-06** unchanged.

## Blocked on / flagged for the owner

1. **THE WIDTH CAP (`PDR-0124`)** — four options: move the cap with reasoning written down;
   take K=3 (8.15×, zero headroom, needs a loud advisory); reopen spec §1's fixed-width
   invariant and trade cross-substrate transfer for 210 dims; or carry 9.43× as debt into
   unit 5 where the census moves anyway. **This is a real trade — width vs transfer
   generality vs content headroom — and it is yours.**
2. **Prioritising WS-4** would unblock the doc rewrite and is on the critical path as "the
   actual product work". Competes with unit 4/5 for the next slot — worth your steer.
3. Instrument redesign — promote or park (unchanged).
4. WS-7 (`hamlet-e3af412673`, P0) — park or schedule (unchanged).
5. `hamlet-83c8e3b50e` — CI silent on `main`'s third merge; deciding test = next merge.
6. Dependabot #33/#34 + 4 vulnerability alerts on `main` (unchanged).

## Open questions

- `hamlet-1e335e0363` (meter `range_type` parses, validates, reaches nothing) is the defect
  I would look at next — it is the framework's signature failure in miniature.
- `hamlet-88578e629e`'s `observable: bool = True` was found **live, not inert** while
  verifying a closure; that half stays open.
- The pack-freeze guard is armed on zero cells while DIV-008 is open (DIV-004's cost
  restated); the enumerated drift table is a weaker substitute.

## Next session starts here

**The owner's trigger-3 ruling**, then unit 4 (the probe experiments `PDR-0114` trigger 1
needs) or WS-4, per their steer. Branch `project-recovery-2`, everything pushed and green.
The SDD ledger
(`.superpowers/sdd/2026-08-24-token-obs-unit3-baselines-div008-cut/progress.md`) carries
every ruling made across the whole unit; trust it over recollection.
