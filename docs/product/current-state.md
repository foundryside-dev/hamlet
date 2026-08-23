# Current State — HAMLET / Townlet        Checkpoint: 2026-08-23 · forty-second checkpoint (`PDR-0113`–`PDR-0116`: **the token design is APPROVED, migration units 1–2 are BANKED**, the oracle register is caught up, and three VFS-inertness bugs are dead)

## The bets right now — two live, one substantially complete

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). In flight and
**materially advanced this session**: the register grew DIV-009 (six-commit drift measured
per-commit, adjudicated, bound) and DIV-010 (unit-2 provenance), cells compose multiple
hash declarations, DIV-008 is visibly reserved for the token cut, and the matrix is
**exit 0 in BOTH plain and scripted modes with all streams byte-identical**
(runs `20260823-043109` / `20260823-043209`). Exit condition unchanged (`PDR-0058`).

**2. Measure the authoring claim** (`PDR-0077`) — SUBSTANTIALLY COMPLETE, retired as
record (`PDR-0111`). Untouched. Remaining: record-keeping + the **2026-10-06
pack-disposition clock** (now ALSO a gate before token migration unit 5, per `PDR-0114`'s
trial-pack ruling). Instrument redesign still awaits owner promotion.

**3. Token-observation encoding** (`PDR-0108`) · tracker `hamlet-fa6bb6da4a`.
**The design is APPROVED (`PDR-0114`)** — six owner rulings, two four-lens review rounds,
no-tech-debt rider, spec at `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md`.
**Migration unit 1 (harness adjudicability) accepted** (`PDR-0115`, `9e7197e6..1960dee6`):
trace v4 actions stream, driver `--actions`, `RegisteredStreamDivergence`, per-stream
adjudication. **Unit 2 (authored temporality) banked** (`PDR-0116`, `3b72c4c4..30f94f93`):
engine `tick` VFS variable (pre-increment semantics, pinned write), exposure-derived
evaluation marks (expressions evaluate on shipped defaults at last), agent profiles BUILD
/ item profiles REFUSE, `time_of_day` derived, statics-are-storage enforced at three
layers. **Next: unit 3 — freeze L2 baselines (≥5 seeds), register DIV-008, then the token
cut as one atomic knockdown.** Unit-3 carry-forwards are on the tracker (comment 242).

## What this checkpoint did

- Recorded the design approval + owner rulings + no-tech-debt rider + trial-pack ruling
  as `PDR-0114`; the vision-stamp provenance as `PDR-0113`.
- Recorded unit-1 acceptance with the drift adjudication and discharge as `PDR-0115`, and
  unit-2's landing (including the spec-delegated build/refuse scope decision and the DIV-009
  catch-up executing that discharge) as `PDR-0116`.
- Tracker reconciled live during execution: closed `hamlet-5cc071f4b6` (drift catch-up),
  `hamlet-df3a96bbac`, `hamlet-5d74335111`, `hamlet-bc0a5deeff` (the three expression-
  inertness bugs); opened `hamlet-f7631a4672` (P4 unit-1 cosmetics), `hamlet-5628884d7d`
  (P2 pre-existing test flakiness, controlled at `11dee204`), `hamlet-c586d520b2` (P4
  approach A capture); 13 VFS round-2 findings filed earlier in-session, each with a
  discharge vehicle.

## Reversal triggers — state

- `PDR-0114` (new): **armed** — the spec's four (≥80% of frozen L2 baseline; a surface
  with no natural token form; 8×width / 25% step-time / batch-size caps;
  payload-identical entities despite the descriptor block).
- `PDR-0115` (new): **discharged unfired** — drift measured to three pre-unit movers.
- `PDR-0116` (new): **armed** — constant-expression/item-expression demand reopens the
  refuse rulings; unit-5 authoring pain reopens the tick write-point pin; an EAGER debug
  dependency reopens the statics ruling as a declared flag.
- `PDR-0109` training-loop trigger: still armed (unit 4 checks it). `PDR-0107`: armed,
  serviced by the migration. Pack-disposition clock: **2026-10-06**, now double-load-bearing
  (`PDR-0111` record-keeping + `PDR-0114` gate before unit 5).

## Blocked on / flagged for the owner (unchanged this session, still open)

1. **Instrument redesign as a future bet** — promote or park (north-star reads `UNREAD`).
2. **WS-7 (`hamlet-e3af412673`, P0)** — park or schedule; untouched since ~2026-08-17.
3. **`hamlet-83c8e3b50e` (P1)** — CI silent on `main`'s third merge; deciding test is the
   next merge (project-recovery-2 is now ~34 commits ahead). No workflow changes before it.
4. Dependabot `#33`/`#34` + **4 vulnerability alerts** on `main`.

Nothing NEW escalated this session — all pushes to `project-recovery-2` within grant; the
vision stamp fix was owner-directed (`PDR-0113`); no releases, deprecations, or external
touches.

## Open questions

- The 2026-08-21 VFS gap analysis (129 cells) still untriaged into WS-4 — several of its
  worst rows just closed via unit 2; a re-triage may be much cheaper now.
- `SetEncoderConfig.token_field_name` resolves only at network-build time (PDR-0052 shape).
- Persistent-lifetime globals (`hamlet-0268336cd1`) — the tick's float32 note points here.

## Next session starts here

**Token migration unit 3 — baselines, then DIV-008, then the cut** (`hamlet-fa6bb6da4a`,
spec §6 unit 3): freeze the shipped-L2 feedforward baseline (≥5 seeds, unrepeatable after
the raster dies), register DIV-008 binding stream+hash under one ref, then TokenSpec
replaces ObservationSpec as one atomic knockdown. Unit-3 carry-forwards: tracker comment
242 (six one-liners) + `PDR-0116`'s notes. The brief for its plan should re-read spec §§1–5
in full — unit 3 is the largest and most irreversible unit of the migration.

Work continues on `project-recovery-2` (tip `30f94f93`, pushed).
