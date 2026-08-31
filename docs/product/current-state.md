# Current State — HAMLET / Townlet        Checkpoint: 2026-08-31 · milestone-2 accepted (`PDR-0134`/`PDR-0135`: **declared token behaviour is executable identity**)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — the Now bet.
- `main` remains `9efadd3c` after the fourth merge; work continues on `project-recovery-3` at
  `b7fc3951` before this checkpoint.
- **WS-7 is closed** (`hamlet-e3af412673`). Its enabling stream delivered determinism, the pinned
  oracle, differential harness, divergence register and first seam cut. The only open child was
  standalone P3 CLI hardening (`hamlet-1073af4d4e`); it is preserved under the recovery milestone.
- The critical path is now WS-6 → WS-2 → WS-3 → WS-4. Bet exit remains unmet: WS-3/WS-4 are open
  and the oracle has not been retired.

**2. Token-observation engineering** (`PDR-0108`/`PDR-0114`/`PDR-0131`/`PDR-0132`/`PDR-0133`/`PDR-0134`/`PDR-0135`) ·
`hamlet-fa6bb6da4a`.
- Unit 3 is complete. `PDR-0126` is superseded: the 9.43× result is not debt to carry into pack
  migration; it is a representation-layout defect to fix before unit 4.
- The former 1,580-float / 1,205.4-MiB line was an intermediate meter-only reading. Exact
  five-entry executable affordance/effect identity and the exposed-initializer correction make the
  current full L1 serialization 4,090 floats: 3,272,000,000 bytes, or 3,120.4 MiB, per 100,000
  float32 observation pairs. The current `variable_element` count is zero because expression-backed
  exposure is refused until milestone 3 static context can encode executable initializer identity;
  the time variable remains live but unexposed. Milestone 3 owns the compact dynamic-state
  measurement. The historical 1,132-float reading remains evidence for the replay-layout defect.
- The accepted design reuses static token context already carried by the compiled artifact, stores
  only compact dynamic state in replay, and reconstructs the fixed transfer schema at the network
  boundary. Milestone 3 will delete the current full-payload transition ABI; it will carry no
  compatibility path.
- The work now runs as five independently accepted milestones: bounded positions
  (`hamlet-6a4a6596bd`), meter `range_type` wiring (`hamlet-1e335e0363`), compact replay
  (`hamlet-1b1caf552a`), Unit 4 regression (`hamlet-25fc3fb955`), then Unit 5 migration
  (`hamlet-55b2826a02`). The umbrella closes only after the final child is terminal.
- **Milestone 1 is complete:** `observation_encoding` is deleted from the current API and one
  bounded contract is canonical: positions `[0,1]`, egocentric deltas `[-1,1]`.
  `div003_scaled` is replaced by the real `boundary_wrap` differential cell.
- **Milestone 2 is engineering-accepted** (`hamlet-1e335e0363`, `PDR-0134`, `PDR-0135`): meter
  `range_type` is now an exact bounded two-lane surface — `minmax` with `clip: true`,
  `log_scaled` with `clip: true`, `cyclical_sin_cos`, or `binary`. `none`, `zscore`, `one_hot`,
  `rank_scaled` and `masked_value` are deleted from the meter vocabulary with no alias, translation
  or fallback.
- All 39 current config declarations (38 pack `environment.yaml` files plus the complete reference)
  use the current contract. Frozen oracle fixtures retain their old
  declarations only as inputs to the historical executable; they are not supported current packs.
  The compiled artifact is schema 1.25 with token encoding `token-1.1`.
- Each level's compiled `TokenSpec` now carries meter static signatures and recursive affordance
  and spawned-effect identity. `dual`, dead definition intensity, inert lifecycle fields and
  catalog-overridable scope/duration are deleted; effect scope is executable authority. The
  environment, encoder, population and token network consume the selected level's spec; there is
  no fallback to the compiled primary-level alias. Artifact loading reconstructs compiler-owned
  token bindings instead of trusting stored hashes.
- Acceptance is current and complete: the default suite passes **3,675 tests with 11 skips and
  84% coverage**; Ruff, Black (565 files), mypy (175 source files), no-defaults, compiler-pack
  validation and `git diff --check` are green. The three compiler negative fixtures refuse exactly
  as designed. The prior 181/158/24 results predate `PDR-0135` and are retained only as history.
  Milestone 3 starts only after this accepted checkpoint is committed and the tracker dependency is
  discharged.

**3. Documentation truth** (`PDR-0125`) — recovery labelling is complete; source-generated
rewrite remains gated on WS-4. Do not start `hamlet-7a52a63e0b` merely because it appears ready.

**4. Measure the authoring claim** — retired as record (`PDR-0111`). Instrument redesign remains
parked. The pack-disposition clock remains 2026-10-06.

## What this checkpoint did

- `PDR-0134` reconciles the old nine-kind, variable-width meter promise with the fixed two-lane
  token ABI. It admits exactly four bounded transformations and deletes the five shapes that are
  unbounded, variable-width or batch-relative rather than translating them silently.
- The runtime now applies the meter's declared transformation to its live token value. Each level's
  compiled meter signature carries the same normalization identity, and recursive affordance target
  signatures inherit it, so changing `range_type` changes both emitted dynamics and network-visible
  identity. The selected environment and token network consume that level's `TokenSpec` directly;
  they never fall back to the primary-level alias.
- `PDR-0135` contracts interaction type to exact `instant | multi_tick`, makes affordance and
  spawned-effect identity match executable lifecycle behaviour, and makes effect definition scope
  and duration the sole runtime authority.
- Non-finite or non-representable token inputs fail at validation or compilation rather than
  entering a float32 tensor silently.
- All 39 current config declarations were updated to the contracted surface. Frozen oracle fixtures
  remain unchanged only to preserve historical differential evidence.
- The compiled schema moves to 1.25 and the encoding remains `token-1.1`.
- **Acceptance evidence:** default suite 3,675 passed / 11 skipped / 84% coverage; Ruff, Black,
  mypy, no-defaults, compiler-pack validation and diff integrity all green. The checkpoint is ready
  for commit, tracker closure and compact-replay handoff.

## Standing gates & in-flight state

1. Local product-source gate remains CI-equivalent: `ruff check .`, `black --check .`, mypy,
   `no_defaults_lint.py`, compiler-pack validation and the full default suite before this source
   push (`PDR-0127`). All are green for the milestone-2 checkpoint.
2. Dependabot #33 (torch) is a separate oracle-moving unit, not dependency housekeeping.
3. The documentation rewrite remains gated on source generation and WS-4.
4. `boundary_wrap` now exercises a real axis. `items_smoke` remains demoted as evidence; the §5
   finding remains CPU-only.

## Decision checks

- `PDR-0132`: if a milestone invalidates the next one's assumptions, stop at the checkpoint and
  write the replacement call before continuing; never skip or combine milestones.
- `PDR-0133`: a future position representation is one replacement ABI with measured constraints;
  it does not revive the deleted selector or create a dual path.
- `PDR-0134`: a new meter normalization must remain bounded, fit two value lanes and be independent
  of other worlds; otherwise it requires a superseding representation PDR.
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

1. Commit and push the accepted milestone-2 checkpoint, record its exact evidence on
   `hamlet-1e335e0363`, and make that issue terminal.
2. Atomically start `hamlet-1b1caf552a`, reuse the compiled static context, and implement the
   compact 118-float replay ABI plus network-edge reconstruction.
3. Continue through `hamlet-25fc3fb955` → `hamlet-55b2826a02`, accepting
   and committing a product checkpoint at each boundary under `PDR-0132`.
