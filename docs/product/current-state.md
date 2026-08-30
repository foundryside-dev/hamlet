# Current State — HAMLET / Townlet        Checkpoint: 2026-08-31 · forty-eighth checkpoint (`PDR-0131`: **ownership reconciled; 9.43× re-ruled as a replay-layout problem; grant confirmed unchanged**)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — the Now bet.
- `main` remains `9efadd3c` after the fourth merge; work continues on `project-recovery-3` at
  `22ebbb32` before this checkpoint.
- **WS-7 is closed** (`hamlet-e3af412673`). Its enabling stream delivered determinism, the pinned
  oracle, differential harness, divergence register and first seam cut. The only open child was
  standalone P3 CLI hardening (`hamlet-1073af4d4e`); it is preserved under the recovery milestone.
- The critical path is now WS-6 → WS-2 → WS-3 → WS-4. Bet exit remains unmet: WS-3/WS-4 are open
  and the oracle has not been retired.

**2. Token-observation engineering** (`PDR-0108`/`PDR-0114`/`PDR-0131`) ·
`hamlet-fa6bb6da4a`.
- Unit 3 is complete. `PDR-0126` is superseded: the 9.43× result is not debt to carry into pack
  migration; it is a representation-layout defect to fix before unit 4.
- Current L1 replay cost at 100,000 transitions: 863.6 MiB for observation pairs versus 91.6 MiB
  before the cut. About 810 of 1,132 floats are immutable descriptors repeated every tick and 204
  are rank padding. The current census needs 118 floats of compact live state.
- The accepted design stores static token context once in the compiled artifact, stores only
  compact dynamic state in replay, and reconstructs the fixed transfer schema at the network
  boundary. The old full-payload transition ABI is deleted; no compatibility path is carried.
- `hamlet-6a4a6596bd` and `hamlet-1e335e0363` now explicitly block the token task. After both:
  compact ABI → unit 4 engineering acceptance → unit 5 all-pack migration.

**3. Documentation truth** (`PDR-0125`) — recovery labelling is complete; source-generated
rewrite remains gated on WS-4. Do not start `hamlet-7a52a63e0b` merely because it appears ready.

**4. Measure the authoring claim** — retired as record (`PDR-0111`). Instrument redesign remains
parked. The pack-disposition clock remains 2026-10-06.

## What this checkpoint did

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

1. Fix `hamlet-6a4a6596bd` (delete the inert observation-mode/encoding surface).
2. Fix or deliberately delete `hamlet-1e335e0363`'s inert meter `range_type` path.
3. Start `hamlet-fa6bb6da4a`: write the implementation plan for static compiled context plus the
   compact dynamic replay ABI, including deletion of the old path and the named acceptance tests.
4. Run unit 4 only after that ABI lands; migrate packs in unit 5 after unit 4 passes.
