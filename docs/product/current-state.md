# Current State — HAMLET / Townlet        Checkpoint: 2026-08-31 · milestone 3 accepted (`PDR-0136`)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) remains the Now bet.

- `main` remains at the fourth recovery merge; current work is pushed on
  `project-recovery-3@d554fb7f`.
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
- Compiled artifact `1.26`, projected schema `token-1.1`, transport `compact-1`, outer checkpoint
  `5`, population `4`, standard/PER `4`, sequential `5`. All are exact one-way cuts.
- The dead public `set_encoder` architecture and old-brain-hash preservation serializer are
  deleted. `token_set` is the sole set architecture.
- Clean-SHA encoding ratios are `0.1618647585026199` and `0.16272129673268468`; accepted maximum
  `0.16272129673268468 < 0.25`.
- Default acceptance: **3,824 passed, 11 skipped, 84% coverage**; Ruff, Black (568 files), mypy
  (176 source files), no-defaults (176 files), compiler-pack validation and diff integrity green.

The checkpointed sequence is unchanged:

1. bounded positions — complete;
2. meter normalization — closed;
3. compact replay/static context — accepted, tracker closure being recorded;
4. token-native recurrent engineering regression — next (`hamlet-25fc3fb955`); and
5. shipped-pack migration — after milestone 4 (`hamlet-55b2826a02`).

**3. Documentation truth** (`PDR-0125`) — recovery labelling is complete; the source-derived
rewrite remains gated on WS-4. Do not start `hamlet-7a52a63e0b` merely because it is ready.

**4. Authoring-trial measurement** is retained as record (`PDR-0111`). Instrument redesign stays
parked; the pack-disposition clock remains 2026-10-06.

## What this checkpoint did

- Moved immutable compiler context out of transitions without weakening fixed model identity.
- Kept effect selection dynamic where scope-budget slots can differ by world.
- Made environment output compact on first allocation and bounded replay to 92 MB at L1.
- Made checkpoint/replay refusal atomic and exact across five artifact boundaries.
- Proved current readers, replay variants, substrate ranks and rank-zero publishers against the
  compact ABI.
- Deleted the non-buildable `set_encoder` surface and the explicit old-hash compatibility shim.
- Established a reproducible, provenance-bearing encoding benchmark at the clean pushed SHA.

## Standing gates

1. Product-source pushes use Ruff, Black, mypy, no-defaults, compiler-pack validation, the default
   suite and diff integrity (`PDR-0127`). They are green for `d554fb7f`.
2. Dependabot #33 (torch) remains a separate oracle-moving unit.
3. `boundary_wrap` exercises a real axis; `items_smoke` remains demoted as evidence.
4. No release, tag, announcement, 1.0 declaration or external coordination is authorized here.

## Decision checks

- `PDR-0131`: if compact state cannot preserve visibility/transfer inside the byte budget, choose
  one replacement ABI; never retain two. Milestone 3 met this check.
- `PDR-0132`: accept and record every milestone before starting its successor.
- `PDR-0134`: a new meter normalization must remain bounded, fixed-width and world-independent.
- `PDR-0114` trigger 1 is now milestone 4's engineering check: token feedforward and the
  token-native recurrent variant must each reach 79.19 IQM at equal environment steps.

## Next session starts here

1. Close `hamlet-1b1caf552a` with the implementation/product SHAs and exact evidence.
2. Atomically start `hamlet-25fc3fb955`.
3. Build the token-native recurrent variant and run the 79.19 IQM equal-step regression. Do not
   treat milestone 3's current-reader BPTT check as that result.
4. Checkpoint milestone 4 before beginning shipped-pack migration.
