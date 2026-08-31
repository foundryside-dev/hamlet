# Current State — HAMLET / Townlet        Checkpoint: 2026-09-01 · milestone 4 paused (`PDR-0138`)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) remains the Now bet.

- `main` remains at the fourth recovery merge; M4 implementation is pushed on
  `project-recovery-3@9d4e942f`.
- WS-7 is closed. The bet has not exited: WS-3/WS-4 remain open and the oracle is still required.
- The critical path remains WS-6 → WS-2 → WS-3 → WS-4. The documentation rewrite remains gated
  on source generation and WS-4.

**2. Token-observation engineering** (`PDR-0108`, `PDR-0114`, `PDR-0131`–`PDR-0136`) ·
`hamlet-fa6bb6da4a`.

- Milestone 1 is complete: `observation_encoding` is deleted; positions use `[0,1]`, egocentric
  deltas `[-1,1]`, and `boundary_wrap` replaces the vacuous scaled oracle cell.
- Milestone 2 is closed: meter `range_type` reaches live values and compiled identity through the
  exact bounded two-lane vocabulary ruled by `PDR-0134`; affordance/effect identity matches
  executable behaviour under `PDR-0135`.
- **Milestone 3 is accepted at `d554fb7f` under `PDR-0136`.** `TokenSpec.total_dims` is the compact
  environment/replay ABI. Fixed context is attached one token type at a time inside the token
  network; no complete fixed-observation runtime surface or compatibility reader remains.
- The current substrate census is Grid2D `115 / 4,090`, Grid3D `149 / 4,090`, and aspatial
  `19 / 394` (compact / fixed). Rank zero is truly positionless. All ranks share the projected
  type-schema hash and carry distinct compact layout hashes.
- A 100,000-transition L1 observation pair is exactly **92,000,000 bytes**. The earlier 118-float
  figure is the one-scalar target, not the current census.
- Batch 256 is executed for feedforward, dueling, token-set mean/attention and RND. The current
  recurrent reader executes four-step BPTT at batch 256 and changes LSTM parameters. Standard,
  prioritized and sequential replay each round-trip and reject their previous format.
- M4 replaces raster/window recurrence with one token encoder shared by feedforward and recurrent
  networks. Recurrent training makes one `[B,S,D]` network call and threads explicit LSTM state;
  no raster reader, fallback or compatibility path remains. Outer checkpoint `6` and population
  checkpoint `5` are exact one-way cuts.
- The dead public `set_encoder` architecture and old-brain-hash preservation serializer are
  deleted. `token_set` is the sole set architecture.
- Clean-SHA encoding ratios are `0.1618647585026199` and `0.16272129673268468`; accepted maximum
  `0.16272129673268468 < 0.25`.
- M4 implementation gate at `9d4e942f`: **3,822 passed, 11 skipped**; Ruff, Black (570 files),
  mypy (176 source files), no-defaults (176 files), compiler-pack validation and diff integrity
  green.
- **M4 is paused, not accepted (`PDR-0138`).** Feedforward/mean completed 2,278,634 transitions
  (shortfall 6) and scored 98.9925 raw greedy mean; feedforward/attention completed 2,278,639
  (shortfall 1) and scored 99.0. Both use 800 raw agent outcomes and pass the fixed 79.1947 floor.
- Recurrent/mean is restart-safe at episode 1,763 and 1,181,395 transitions; recurrent/attention
  at episode 1,722 and 1,204,116 transitions. Neither is budget-complete or evaluated. No
  qualification process remains active.
- Three M4 evidence defects remain in scope: the terminal curve-import failure, legacy curves that
  overstate all-agent transitions, and early-stop database status that says `completed` despite an
  incomplete budget. The metadata and checkpoint counters remain internally consistent.

The checkpointed sequence is unchanged:

1. bounded positions — complete;
2. meter normalization — closed;
3. compact replay/static context — accepted and closed;
4. token-native recurrent engineering regression — paused at a restart-safe evidence boundary,
   still in progress (`hamlet-25fc3fb955`); and
5. shipped-pack migration — after milestone 4 (`hamlet-55b2826a02`).

**3. Documentation truth** (`PDR-0125`) — recovery labelling is complete; the source-derived
rewrite remains gated on WS-4. Do not start `hamlet-7a52a63e0b` merely because it is ready.

**4. Authoring-trial measurement** is retained as record (`PDR-0111`). Instrument redesign stays
parked; the pack-disposition clock remains 2026-10-06.

## What this checkpoint did

- Froze and pushed the token-native recurrent implementation and source-bound four-cell harness at
  `9d4e942f` after the complete source gate passed.
- Completed and accepted two feedforward cells as partial M4 evidence without claiming the
  milestone: raw greedy means 98.9925 and 99.0.
- Stopped both recurrent cells through the normal checkpoint path and recorded their exact resume
  positions rather than discarding or relabelling partial work.
- Kept M4 and Unit 5 open after discovering three evidence-path defects; none was moved to an
  observation or future cleanup item.

## Standing gates

1. Product-source pushes use Ruff, Black, mypy, no-defaults, compiler-pack validation, the default
   suite and diff integrity (`PDR-0127`). They are green for `9d4e942f`.
2. Dependabot #33 (torch) remains a separate oracle-moving unit.
3. `boundary_wrap` exercises a real axis; `items_smoke` remains demoted as evidence.
4. No release, tag, announcement, 1.0 declaration or external coordination is authorized here.

## Decision checks

- `PDR-0131`: if compact state cannot preserve visibility/transfer inside the byte budget, choose
  one replacement ABI; never retain two. Milestone 3 met this check.
- `PDR-0132`: accept and record every milestone before starting its successor.
- `PDR-0134`: a new meter normalization must remain bounded, fixed-width and world-independent.
- `PDR-0137` makes trigger 1 an explicit engineering check: all four
  feedforward/recurrent × mean/attention cells must reach raw greedy mean survival 79.19 on
  deterministic seed 45 at its full frozen transition budget. No confidence claim is made.

## Next session starts here

1. Execute the exact `9d4e942f` snapshot and resume the two recurrent cells with their original
   commands plus `--resume`; do not resume from the later product-checkpoint commit.
2. Evaluate each terminal recurrent checkpoint once under the frozen 100-episode seed-12345
   protocol, then validate all four raw 800-agent arrays and the 79.1947 floor.
3. Return to the branch tip, repair the curve import, truthful transition artifact and early-stop
   status as M4 scope, and run their focused plus relevant full gates.
4. Write the final M4 evidence record, reconcile and close `hamlet-25fc3fb955`, commit and push the
   acceptance checkpoint, then—and only then—start `hamlet-55b2826a02`.
