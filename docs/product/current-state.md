# Current State — HAMLET / Townlet        Checkpoint: 2026-09-02 (later) · M4 and unit 5 accepted, token umbrella closed (`PDR-0144`)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) remains the Now bet.

- `main` remains at the fourth recovery merge (`9efadd3c`). Active branch `project-recovery-3`,
  tip `a07b889b` plus this checkpoint, pushed.
- WS-7 closed; WS-3/WS-4 open; oracle still required. Critical path unchanged: WS-6
  `hamlet-5e39fcccb0` → WS-2 `hamlet-337b9e80fb` → WS-3 `hamlet-1f89714685` → WS-4
  `hamlet-15050f280a`. Docs rewrite `hamlet-7a52a63e0b` stays gated on WS-4 (`PDR-0125`).

**2. Token-observation engineering — COMPLETE.** `hamlet-fa6bb6da4a` closed with all five
milestones terminal (`PDR-0133`–`0136`, `0141`, `0144`). This session accepted M4 (four cells
pass the 79.1947 floor at the frozen budget) and unit 5 (every pack runs under one
discovery-driven test; every live token type and scope exercised from a committed pack; L3 is one
authored `day_phase` token; `observation_mode` and nine retired trial packs deleted). No horizon
change: the next unit is the top of Next — the declaration-store compiler unit (`PDR-0117`) or the
epistemic-access unit (`PDR-0120`) — and is a DECIDE for the next session, not preauthorised.

**3. Two P1 engine defects outside any unit:** `hamlet-d6fc84d147` (env step counter increments
for dead agents; feeds rewards/curriculum under the oracle, needs its own differential run,
`PDR-0140`) and `hamlet-4b931faaf4` (held/exclusive items invisible to the whole `item` token
type; `layout_hash`-moving fix, `PDR-0144`). Both triage.

**4. Documentation truth** (`PDR-0125`): schema docs realigned this session; `CLAUDE.md:116`
false claim still an observation (`hamlet-obs-5f1ea6c254`, expires 2026-09-15); new observation
`hamlet-obs-b959ce55c0` (dead-weight durability rows).

**5. Weft tooling** (`PDR-0139`): held at resume (doctors clean, probe 200, index fresh). The
loomweave index is now stale by 12 commits — re-analyse at next resume.

## What this checkpoint did

- Owner directed *"lets finish M4"* and preauthorised the roll into M5. Grant re-confirmed
  unchanged.
- M4: resumed both recurrent cells on the pinned `9d4e942f` worktree, evaluated, repaired the
  evidence path test-first (`PDR-0140`), accepted (`PDR-0141`), evidence versioned under
  `docs/product/baselines/2026-09-m4-token-regression/`.
- Unit 5: ruled the trial-pack disposition (`PDR-0142`) and unit scope (`PDR-0143`); executed a
  five-task plan by subagent-driven development (fresh implementer + task review per task, whole-
  branch review, one fix wave); accepted (`PDR-0144`). Eleven code commits `5973f79b`…`a07b889b`.
- Closed `hamlet-25fc3fb955`, `hamlet-55b2826a02`, `hamlet-fa6bb6da4a`, `hamlet-5a87550adb`;
  filed `hamlet-d6fc84d147`, `hamlet-4b931faaf4`, one observation.

## Standing gates

1. `PDR-0127` gate set last executed on `a07b889b`: all static gates green; pytest 3,846 passed /
   11 skipped (run as two foreground tiers — the host killed two background runs).
2. Dependabot #33 (torch) and #34 (pytest) remain open since 2026-08-15.
3. No release, tag, announcement, 1.0 declaration or external coordination is authorized here.

## Open questions / blocked on owner

- **Nothing escalated.** Every action (pushes, tracker closes, deletions of retired packs
  already ruled by `PDR-0082`–`0085`/PRD-0001 §9, the `.filigree/`-style cleanups) is inside the
  grant. Primary experimental evidence untouched.
- **Merge to `main`:** autonomous under `PDR-0101` but owes the `PDR-0039` gate-2 README
  re-verification by method. Not done this session; the branch is 13 commits ahead of `main`.

## Decision checks

- `PDR-0132`: each milestone accepted and checkpointed before its successor — held for M4→M5.
- `PDR-0143` / `PDR-0144` reversal triggers armed: L2 four-cell floor on any post-unit-5 commit;
  a shared-world declaration surface makes agent tokens live.
- `PDR-0139`: tool health rule held at resume.

## Next session starts here

1. `/own-product`: re-analyse the loomweave index; confirm the grant.
2. DECIDE the next unit from Next: declaration-store compiler unit (`PDR-0117`; two inputs from
   this session — `period`/`day_length` duplication, `filler_ref` string contract) versus
   epistemic-access unit (`PDR-0120`). Or the merge to `main` with gate 2 first.
3. Triage `hamlet-4b931faaf4` and `hamlet-d6fc84d147` — both are engine changes under the oracle
   and need a register entry before landing.
