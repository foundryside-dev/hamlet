# Current State — HAMLET / Townlet        Checkpoint: 2026-08-31 · forty-ninth checkpoint (`PDR-0132`: **five token milestones armed; bounded-position repair is next**)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — the Now bet.
- `main` remains `9efadd3c` after the fourth merge; work continues on `project-recovery-3` at
  `22ebbb32` before this checkpoint.
- **WS-7 is closed** (`hamlet-e3af412673`). Its enabling stream delivered determinism, the pinned
  oracle, differential harness, divergence register and first seam cut. The only open child was
  standalone P3 CLI hardening (`hamlet-1073af4d4e`); it is preserved under the recovery milestone.
- The critical path is now WS-6 → WS-2 → WS-3 → WS-4. Bet exit remains unmet: WS-3/WS-4 are open
  and the oracle has not been retired.

**2. Token-observation engineering** (`PDR-0108`/`PDR-0114`/`PDR-0131`/`PDR-0132`) ·
`hamlet-fa6bb6da4a`.
- Unit 3 is complete. `PDR-0126` is superseded: the 9.43× result is not debt to carry into pack
  migration; it is a representation-layout defect to fix before unit 4.
- Current L1 replay cost at 100,000 transitions: 863.6 MiB for observation pairs versus 91.6 MiB
  before the cut. About 810 of 1,132 floats are immutable descriptors repeated every tick and 204
  are rank padding. The current census needs 118 floats of compact live state.
- The accepted design stores static token context once in the compiled artifact, stores only
  compact dynamic state in replay, and reconstructs the fixed transfer schema at the network
  boundary. The old full-payload transition ABI is deleted; no compatibility path is carried.
- The work now runs as five independently accepted milestones: bounded positions
  (`hamlet-6a4a6596bd`), meter `range_type` wiring (`hamlet-1e335e0363`), compact replay
  (`hamlet-1b1caf552a`), Unit 4 regression (`hamlet-25fc3fb955`), then Unit 5 migration
  (`hamlet-55b2826a02`). The umbrella closes only after the final child is terminal.
- **Current milestone:** delete the inert `observation_encoding` surface and establish one
  canonical bounded position encoding. `div003_scaled` must stop presenting a vacuous matrix
  cell as evidence.

**3. Documentation truth** (`PDR-0125`) — recovery labelling is complete; source-generated
rewrite remains gated on WS-4. Do not start `hamlet-7a52a63e0b` merely because it appears ready.

**4. Measure the authoring claim** — retired as record (`PDR-0111`). Instrument redesign remains
parked. The pack-disposition clock remains 2026-10-06.

## What this checkpoint did

- `PDR-0132` turned `PDR-0131`'s prose sequence into a durable five-milestone product plan with
  an evidence, tracker, product-document and Git checkpoint at every boundary.
- Filigree now has distinct compact-ABI, Unit 4 and Unit 5 children. Compact replay waits on both
  semantic repairs, Unit 4 waits on compact replay, Unit 5 waits on Unit 4, and the umbrella waits
  on Unit 5. This preserves the downstream block without pretending the umbrella is executable.
- `PDR-0131` replaced the raw 8× acceptance proxy with byte-level engineering constraints:
  dynamic replay ≤120 floats, a 100k observation pair ≤96,000,000 float32 bytes, batch 256 still
  viable, encoding below 25% of `env.step`, and cross-substrate schema/visibility parity.
- The default curriculum was inspected at current HEAD: `token_spec.total_dims = 1132`, with
  census self 1×18, meter 8×12, affordance 14×66, item 2×21 and variable_element 1×52.
- Filigree reconciliation:
  - closed stale P0 WS-7 and reparented its P3 hardening child;
  - rewrote the stale token umbrella to the compact-state engineering scope;
  - released its expired `claude-fable` claim back to `open`;
  - added the two semantic observation defects as explicit blockers.
- The owner confirmed the standing authority grant unchanged. `vision.md` now carries the
  2026-08-31 review stamp; the autonomous and escalation lists did not move.

## Standing gates & in-flight state

1. Local product-source gate remains CI-equivalent: `ruff check .`, `black --check src tests`,
   and `no_defaults_lint.py` before any source push (`PDR-0127`).
2. Dependabot #33 (torch) is a separate oracle-moving unit, not dependency housekeeping.
3. The documentation rewrite remains gated on source generation and WS-4.
4. `div003_scaled` and `items_smoke` remain demoted as evidence; the §5 finding remains CPU-only.

## Decision checks

- `PDR-0132`: if a milestone invalidates the next one's assumptions, stop at the checkpoint and
  write the replacement call before continuing; never skip or combine milestones.
- `PDR-0131`: if compact-flat state cannot preserve visibility and transfer while meeting the
  byte budget, stop and choose one different token ABI; never retain both.
- `PDR-0127`: a >3-push red streak under a green checkpoint means the reading rule failed and
  must become mechanical.
- `PDR-0114` trigger 1 is now an engineering regression check: token feedforward and recurrent
  must each reach 79.19 IQM at equal environment steps in unit 4.
- Pack-disposition clock: **2026-10-06**.

## Blocked on / flagged for the owner

Nothing from this reconciliation. The grant is confirmed and stamped; the 9.43× decision is
resolved within strategy. Still owner-bound if promoted: instrument redesign, declaring 1.0,
announcement, tags/releases, vision/strategy/grant changes, data deletion or external parties.

## Next session starts here

1. Start `hamlet-6a4a6596bd` atomically with its bug workflow advanced to fixing; delete the inert
   observation-mode/encoding surface and pin the canonical bounded position semantics.
2. Checkpoint milestone 1, then wire `hamlet-1e335e0363`'s meter `range_type` into token values.
3. Continue through `hamlet-1b1caf552a` → `hamlet-25fc3fb955` → `hamlet-55b2826a02`, accepting
   and committing a product checkpoint at each boundary under `PDR-0132`.
