# Current State — HAMLET / Townlet        Checkpoint: 2026-08-31 · fiftieth checkpoint (`PDR-0133`: **one bounded position contract; milestone 1 complete**)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — the Now bet.
- `main` remains `9efadd3c` after the fourth merge; work continues on `project-recovery-3` at
  `90815496` before this checkpoint.
- **WS-7 is closed** (`hamlet-e3af412673`). Its enabling stream delivered determinism, the pinned
  oracle, differential harness, divergence register and first seam cut. The only open child was
  standalone P3 CLI hardening (`hamlet-1073af4d4e`); it is preserved under the recovery milestone.
- The critical path is now WS-6 → WS-2 → WS-3 → WS-4. Bet exit remains unmet: WS-3/WS-4 are open
  and the oracle has not been retired.

**2. Token-observation engineering** (`PDR-0108`/`PDR-0114`/`PDR-0131`/`PDR-0132`/`PDR-0133`) ·
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
- **Milestone 1 is complete:** `observation_encoding` is deleted from the current API and one
  bounded contract is canonical: positions `[0,1]`, egocentric deltas `[-1,1]`.
  `div003_scaled` is replaced by the real `boundary_wrap` differential cell.
- **Current milestone:** restore each meter's declared `range_type` transformation into its token
  live value (`hamlet-1e335e0363`). The declaration is wired, not deleted.

**3. Documentation truth** (`PDR-0125`) — recovery labelling is complete; source-generated
rewrite remains gated on WS-4. Do not start `hamlet-7a52a63e0b` merely because it appears ready.

**4. Measure the authoring claim** — retired as record (`PDR-0111`). Instrument redesign remains
parked. The pack-disposition clock remains 2026-10-06.

## What this checkpoint did

- `PDR-0133` deleted the inert selector rather than carrying an alias, fallback, constructor
  overload or config migration. Old current configs now fail loudly as extra-field input.
- Every spatial substrate now publishes absolute positions in `[0,1]` and egocentric deltas in
  `[-1,1]`; the hidden raw-delta branch is gone.
- The vacuous `div003_scaled` cell became `boundary_wrap`. Its frozen-oracle counterpart remains
  an input to the pinned old executable, not an accepted current config surface.
- Red-first regression produced 12 failures before the cut and 12 passes after it. Focused
  evidence is 427 passed / 6 skipped plus 45 oracle/seam passes. The full default suite is
  3,307 passed / 11 skipped at 84% coverage; pack validation, Ruff, Black, mypy, no-defaults and
  `git diff --check` are green.
- The active runtime, scripts, shipped configs and ordinary tests contain zero references to the
  deleted key. The implementation removes 1,104 lines while adding 121, including the rejection
  and boundedness regression.

## Standing gates & in-flight state

1. Local product-source gate remains CI-equivalent: `ruff check .`, `black --check src tests`,
   and `no_defaults_lint.py` before any source push (`PDR-0127`).
2. Dependabot #33 (torch) is a separate oracle-moving unit, not dependency housekeeping.
3. The documentation rewrite remains gated on source generation and WS-4.
4. `boundary_wrap` now exercises a real axis. `items_smoke` remains demoted as evidence; the §5
   finding remains CPU-only.

## Decision checks

- `PDR-0132`: if a milestone invalidates the next one's assumptions, stop at the checkpoint and
  write the replacement call before continuing; never skip or combine milestones.
- `PDR-0133`: a future position representation is one replacement ABI with measured constraints;
  it does not revive the deleted selector or create a dual path.
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

1. Close `hamlet-6a4a6596bd` with the milestone-1 commit, then start `hamlet-1e335e0363`
   atomically and restore declared meter `range_type` semantics into token values.
2. Checkpoint milestone 2, then implement static compiled context plus the compact 118-float
   replay ABI in `hamlet-1b1caf552a`.
3. Continue through `hamlet-25fc3fb955` → `hamlet-55b2826a02`, accepting
   and committing a product checkpoint at each boundary under `PDR-0132`.
