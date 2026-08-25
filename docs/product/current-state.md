# Current State — HAMLET / Townlet        Checkpoint: 2026-08-25 · forty-fourth checkpoint (`PDR-0122`–`PDR-0123`: **the baseline is frozen and the cut is mid-Phase-2** — Tasks 5–8 landed alongside with zero hash movement; the first width reading is over the cap on paper and its measurement was brought forward; the VFS doc loop converged)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). The compiler
cleanup LANDED (merge `312d0fe0` behind the `PDR-0121` gate — the branch turned out to be
cut from main's tip, re-based `--onto` and fully re-gated; hashes clean). DIV-011 is live
in the register (the two new token hashes, additive, retires at DIV-008/re-tag).

**2. Token-observation encoding** (`PDR-0108`/`PDR-0114`) · tracker `hamlet-fa6bb6da4a`.
**PHASE 2 IS MID-FLIGHT, Tasks 5–8 COMPLETE, all ALONGSIDE** (zero hash movement at every
task boundary; matrix exit 0 both modes throughout; suite 3,584):
- Task 2 DONE: baseline frozen at `docs/product/baselines/2026-08-l2-preraster/record.md`
  — IQM **98.99**, trigger-1 threshold **79.19** at equal env-steps (`PDR-0122`). Freeze
  lifted.
- Task 5 (compile hardening 5a–5f), Task 6 (TokenSpec artifact, `token_spec.py`), Task 7
  (compiler emission + `token_type_schema_hash`/`layout_hash` + DIV-011), Task 8
  (publishers, per-scope arenas, substrate `visible()`/`egocentric_delta()` contract) all
  landed + reviewed + re-reviewed. **Task 8's review verdict is the one thing still
  outstanding** (fable reviewer in flight at checkpoint time — findings may add a fix
  round).
- **Width reading (`PDR-0123`)**: L1 TokenSpec = 1080 dims = 9.0× pre-cut 120, over
  trigger 3's 8× line on paper. Cap NOT moved, constants NOT tuned; **Task 11 must
  re-measure on the compiled post-cut artifact and treat ≥8× as trigger FIRED then.**
  Levers to drill with data: meter-signature variance, position-padding policy, K.
- Standing Task-10 dispositions (recorded in the ledger): effect-budget advisory →
  refusal + required `max_active_effects`; explicit-exposure refusals; DIV-011 retirement
  into DIV-008; `effects_smoke` day_count + effect-budget advisories; meter-value
  normalization ruling re-examined at adjudication; schema_hashes layering inversion.
- Plan conflict RULED: Task 7's drafted severing edits moved to Task 10 (spec §6.3
  "no green half-state" governs). Delta-check gate ran for Tasks 6/7/8; Task 9 next.

**3. Measure the authoring claim** — retired as record (`PDR-0111`), unchanged.
Instrument redesign still awaits owner promotion; 2026-10-06 pack-disposition clock.

## What this checkpoint did

- Recorded `PDR-0122` (baseline accepted at realized episodes; truncation documented, not
  re-run) and `PDR-0123` (width cap kept, measurement brought forward to Task 11).
- Metrics: baseline IQM 98.99 + threshold 79.19 published; the 9.0× width reading
  recorded as not-a-firing with its forward evaluation point.
- Owner-directed this session: the 3-pass Fable doc loop on `docs/architecture/VFS.md`
  (converged: 12→2→0 substantive corrections; commits `5236f117`/`a6c74632`/`53947a09`)
  + the dead-path sweep (39 repointed, `2546382d`).
- Defects filed: `hamlet-cebe51077a` (P1 — phase names are a closed set; VFS.md's design
  examples unauthorable; runtime raise should be compile), `hamlet-784884e550`
  (order-dependent LSTM flake), `hamlet-5a87550adb` (model_pack items.yaml spawn_effect).
  Closed: `hamlet-af929afa06` (compiler cleanup). Discharged into Task 5: `hamlet-88578e629e`,
  `hamlet-d970ef83f0`, `hamlet-0ddc83e377`, `hamlet-702ae15f82`, `hamlet-6a6e104523` (ruling).

## Standing gates & in-flight state (read before acting)

1. **Task 8 review verdict** → possible fix round → completion → push → Task 9
   delta-check (against Tasks 5–8's landed diffs) → dispatch.
2. **Task 10 is the swap** (severs old wiring; carries the deferred edits list above);
   Task 11 adjudicates (DIV-008 binding by measurement, the width re-measurement
   `PDR-0123`, fixture-refusal/oracle-move-forward decision, docs at gate-2 standard).
3. Baseline record NEVER changes (`PDR-0122`); a re-measurement is a successor record.

## Reversal triggers — state

- `PDR-0114` trigger 1 ARMED with a real denominator: ≥79.19 IQM at equal env-steps.
- `PDR-0114` trigger 3: **measured 9.0× at design time — evaluation brought forward to
  Task 11 (`PDR-0123`); fires there if the compiled post-cut artifact reads ≥8×.**
- `PDR-0121` gate: executed clean; branch landed.
- Pack-disposition clock **2026-10-06** unchanged.

## Blocked on / flagged for the owner

1. **Un-archive `docs/config-schemas/`?** The dead-path sweep found the current docs
   delegate to it as their reference tier (UAC.md cites it 14×) — recommendation is to
   un-archive + truth-pass it, but that reverses your "zzz. archive" recut, so it waits
   on you. (Same, smaller: `docs/guides/dac-migration.md`.)
2. Instrument redesign — promote or park (unchanged).
3. WS-7 (`hamlet-e3af412673`, P0) — park or schedule (unchanged).
4. `hamlet-83c8e3b50e` — CI silent on `main`'s third merge; deciding test = next merge.
5. Dependabot #33/#34 + 4 vulnerability alerts on `main` (unchanged).

## Open questions

- `hamlet-cebe51077a`: open the phase vocabulary to declared names (declarative surface —
  the CLAUDE.md-shaped fix) vs close the doc examples to canonical names; either way the
  post-completion-bonus runtime raise should become a compile refusal.
- VFS doc maintenance: pass 3's recommendation — re-run the doc loop when
  `registry.py`/`vtc.py`/`vectorized_env.py` churn (Tasks 9–10 will), not on a calendar.
- Owner stops of running agents (twice this session) resolved fine both times — resumed
  or controller-finished; SendMessage relay remains the cheaper steering path.

## Next session starts here

**If Task 8's review landed**: run its verdict (fix round or completion + push), then
Task 9 delta-check + dispatch. **Then Task 10 (swap) and Task 11 (adjudication — DIV-008
binding, width re-measurement, oracle decision).** The ledger
(`.superpowers/sdd/2026-08-24-token-obs-unit3-baselines-div008-cut/progress.md`) carries
every ruling; trust it over recollection. Branch `project-recovery-2`; everything through
Task 7 + all docs pushed; Task 8's four commits local at checkpoint time.
