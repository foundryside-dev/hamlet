# Current State — HAMLET / Townlet        Checkpoint: 2026-09-02 · weft tooling verified, M4 still paused (`PDR-0139`)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) remains the Now bet.

- `main` remains at the fourth recovery merge (`9efadd3c`). Active branch is `project-recovery-3`,
  pushed at `9318d86f`; three commits since the `PDR-0138` checkpoint, none touching product
  source.
- WS-7 is closed. The bet has not exited: WS-3/WS-4 remain open and the oracle is still required.
- The critical path remains WS-6 `hamlet-5e39fcccb0` → WS-2 `hamlet-337b9e80fb` → WS-3
  `hamlet-1f89714685` → WS-4 `hamlet-15050f280a`, all open. The documentation rewrite
  (`hamlet-7a52a63e0b`) shows Ready but stays gated on WS-4 (`PDR-0125`).

**2. Token-observation engineering** (`PDR-0108`, `PDR-0114`, `PDR-0131`–`PDR-0138`) ·
`hamlet-fa6bb6da4a`.

- Milestones 1–3 complete/accepted; see `PDR-0133`, `PDR-0134`/`0135`, `PDR-0136`.
- **Milestone 4 is paused, not accepted (`PDR-0138`).** `hamlet-25fc3fb955` is `in_progress`.
  Feedforward/mean 98.9925 and feedforward/attention 99.0 pass the 79.1947 floor at full budget.
  Recurrent/mean is restart-safe at `checkpoint_ep01763.pt` (1,181,395 transitions);
  recurrent/attention at `checkpoint_ep01722.pt` (1,204,116). **Verified 2026-09-02:** both
  checkpoints on disk with sha256 sidecars, no later checkpoint, all four `meta.json` pin
  `git_sha 9d4e942f` with `resume: false`, GPUs idle. Nothing has been resumed.
- Three M4 evidence defects remain in scope: the terminal curve-import failure, legacy curves that
  overstate all-agent transitions, and early-stop database status `completed` on an incomplete
  budget. `hamlet-55b2826a02` (Unit 5) stays blocked behind M4.

**3. Documentation truth** (`PDR-0125`) — recovery labelling complete; source-derived rewrite
gated on WS-4. One newly confirmed false claim, `CLAUDE.md:116` ("no workflow has ever run on
`project-recovery`"), is filed as a filigree observation, not fixed.

**4. Authoring-trial measurement** retained as record (`PDR-0111`). Pack-disposition clock
2026-10-06.

**5. Weft tooling** (`PDR-0139`, new standing rule): filigree and loomweave health means doctor
clean **and** the loomweave→filigree probe answers 200 **and** the index is fresh. Warpline and
wardline are uninstalled by the owner for rework; their instruction blocks and hooks are removed,
their skill packs and `weft.toml` retained per `PDR-0038`.

## What this checkpoint did

- Ran `/own-product` RESUME → ORIENT: no product drift against tracker or git; grant surfaced.
- Found and fixed the dead loomweave→filigree federation link (port 8766 → 8749, `b2a10f3e`);
  applied both doctors' fixes; re-analysed the index to HEAD.
- Removed the warpline instruction blocks and hooks (`9318d86f`), deleted the orphaned
  `.filigree/` directory with explicit owner approval, pushed the branch. Recorded as `PDR-0139`.
- Took dated readings for Gates green, M4 evidence integrity and Documentation truth.

## Standing gates

1. Product-source pushes use Ruff, Black, mypy, no-defaults, compiler-pack validation, the default
   suite and diff integrity (`PDR-0127`). Last executed for `9d4e942f`; not re-run for the three
   non-source commits since.
2. Dependabot #33 (torch) and #34 (pytest) remain open since 2026-08-15; #33 is a separate
   oracle-moving unit.
3. `boundary_wrap` exercises a real axis; `items_smoke` remains demoted as evidence.
4. No release, tag, announcement, 1.0 declaration or external coordination is authorized here.

## Open questions / blocked on owner

- **Authority grant:** surfaced at this resume; the owner did not explicitly re-confirm it in
  this session (the session's answers were task instructions). `Last reviewed` stays 2026-08-31,
  inside the monthly cadence. Re-surface at the next resume.
- **Retained wardline/warpline skill packs and `weft.toml`:** kept per `PDR-0038` on the owner's
  "going back for reworking". If the rework is abandoned, they go under a successor PDR.
- **Filigree build provenance:** installed 3.1.0 is the owner's dev branch at `2052e7a`, two
  commits behind `origin/main` (RED-1 closure gate). Filigree-repo decision, not hamlet's.

## Decision checks

- `PDR-0132`: accept and record every milestone before starting its successor — holds.
- `PDR-0137`: all four cells must reach raw greedy mean 79.19 on seed 45 at full budget.
- `PDR-0138`: resume recurrent cells on the exact `9d4e942f` snapshot; never from a later commit.
- `PDR-0139`: tool health = doctor clean + probe 200 + index fresh; on failure treat the seam as
  broken until proven.

## Next session starts here

1. Check out the exact `9d4e942f` snapshot (worktree or detached) and resume the two recurrent
   cells with their original commands plus `--resume`. Do not resume from `9318d86f` or any later
   commit; the run metadata pins the training source.
2. Evaluate each terminal recurrent checkpoint once under the frozen 100-episode seed-12345
   protocol, then validate all four raw 800-agent arrays against the 79.1947 floor.
3. Return to the branch tip, repair the curve import, truthful transition artifact and early-stop
   status as M4 scope, and run their focused plus relevant full gates.
4. Write the final M4 evidence record, reconcile and close `hamlet-25fc3fb955`, commit and push the
   acceptance checkpoint, then — and only then — start `hamlet-55b2826a02`.
