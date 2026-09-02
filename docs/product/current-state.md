# Current State — HAMLET / Townlet        Checkpoint: 2026-09-02 (fifth merge) · `main` at `ea3648db`, next unit chosen (`PDR-0145`, `PDR-0146`)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) remains the Now bet.

- **The fifth merge is on `main` at `ea3648db`** (PR #38, 36 commits, 610 files, `PDR-0129`–`0146`).
  Active branch **`project-recovery-4`**, cut from the merge commit and pushed; at this checkpoint it
  carries only the workspace commit. `main`'s per-push CI fired within a minute and all three workflows
  completed green (Lint ✅ Config Validation ✅ Tests ✅). Later commits on `-4`: `a55b5a3f`
  (project settings tracked, `gh pr merge` allowed, CLAUDE.md merge rule) and `a8b66984`
  (concurrent: `loomweave.yaml` untracked, ADR-063).
- WS-7 closed; WS-3/WS-4 open; oracle still required. Critical path unchanged: WS-6
  `hamlet-5e39fcccb0` → WS-2 `hamlet-337b9e80fb` → WS-3 `hamlet-1f89714685` → WS-4
  `hamlet-15050f280a`. Docs rewrite `hamlet-7a52a63e0b` stays gated on WS-4 (`PDR-0125`).
- **Next unit, owner-chosen at this resume: the declaration-store compiler unit (`PDR-0117`).**
  The unit is committed; its **scope ruling is not** — that is the next session's first DECIDE.
  Banked inputs: `period: 24`/`day_length: 24` duplication (`PDR-0143`); `filler_ref` string
  contract → typed `scope` on `SlotBinding` (`PDR-0144`); `items_smoke` stray files no loader reads
  (`hamlet-obs-982755441c`, expires 2026-09-16); the symbol-table half `hamlet-33e520cebd`; the
  SourceMap parks `hamlet-af929afa06`. Explicitly NOT in it: orchestrator tiers, sub-compiler graph
  engine, incremental compilation.

**2. Token-observation engineering — COMPLETE and merged** (`hamlet-fa6bb6da4a` closed, `PDR-0144`).

**3. Fifteen P1 bugs in `triage`, none inside a unit.** The two from the milestone work:
`hamlet-d6fc84d147` (step counter for dead agents; behaviour change under the oracle, needs a
register entry, `PDR-0140`) and `hamlet-4b931faaf4` (held items invisible to the `item` token type;
`layout_hash`-moving). The other thirteen are mostly WS-4 authorability gaps from the trials and
the VFS audit; several (`hamlet-fc78bb49d3`, `hamlet-83a043a9b9`, `hamlet-33e520cebd`) belong to
the epistemic-access or declaration-store units rather than to standalone fixes.

**4. Documentation truth** (`PDR-0125`): README re-verified by method and stamped at `1eb347f7`
(`PDR-0145`); CLAUDE.md's false CI caveat and dead `CuesCompiler` line corrected;
`hamlet-obs-5f1ea6c254` dismissed as resolved. One observation pending besides the stray-files one:
`hamlet-obs-b959ce55c0` (dead-weight durability rows, expires 2026-09-16).

**5. Weft tooling** (`PDR-0139`): loomweave re-analysed at the fifty-first checkpoint; now behind by
the merge and workspace commits — re-analyse at resume. Wardline still uninstalled.

## What this checkpoint did

- Owner confirmed the grant and approved the review-stamp move to 2026-09-02; chose *merge, then
  declaration-store* over opening a unit first.
- Executed `PDR-0039` gate 2 by method — sweep, draft, adversarial pass as three agents: 29 stale
  claims, 22 omissions, nine defects in the draft's own corrections (`PDR-0145`). Stamped at
  `1eb347f7`, committed `4e23b3ea`.
- Opened and merged PR #38 (`ea3648db`) after all six checks passed; cut `project-recovery-4`
  (`PDR-0146`). The harness classifier blocked the merge twice; the owner granted it via
  `/permissions`. `PDR-0101` trigger 2 (silent `main`) did not fire.
- Tracker: dismissed `hamlet-obs-5f1ea6c254`, filed `hamlet-obs-982755441c`. No issues closed
  or opened.

## Standing gates

1. `PDR-0127` gate set: read on `1eb347f7` (all green) and PR #38 (all six green). Local pytest
   was not re-run this session (docs-only commits since the 3,846-pass reading at `a07b889b`).
2. Dependabot #33 (torch) and #34 (pytest) remain open since 2026-08-15.
3. No release, tag, announcement, 1.0 declaration or external coordination is authorized here.

## Open questions / blocked on owner

- **Nothing escalated.** The merge, pushes, README/CLAUDE.md edits, observation filing and the
  approved stamp correction are all inside the grant.
- **Mechanism note:** the grant's autonomous merge is gated by the harness classifier in practice.
  A standing Bash permission for `gh pr merge` would make it autonomous in mechanism too; the
  owner's call, not the agent's (`PDR-0146` trigger 3).

## Decision checks

- `PDR-0143`/`0144` reversal trigger (L2 four-cell floor on a post-unit-5 commit) is **armed and
  unread** — no harness run since unit 5. Not failed; not passed.
- `PDR-0145`/`0146`: if `main`'s Tests at `ea3648db` or the first nightly is red, gate 2's CI
  reading must be re-derived at merge commits.
- `PDR-0145` trigger 3: a second "fix at next touch" observation surviving a touch converts
  file-triggered observations into filed issues.

## Next session starts here

1. `/own-product`: re-analyse loomweave; confirm the grant. (`main` at `ea3648db` is fully
   green — nothing to read there.)
2. **DECIDE the scope of the declaration-store compiler unit (`PDR-0117`)** — the unit is chosen,
   the cut is not. Start from `PDR-0117`'s five calls, `PDR-0121`'s assessment, and the three
   banked inputs above; decide whether the variable-surface unification lands in the same cut or
   the next. Then `/write-prd` → plan → dispatch.
3. Triage `hamlet-4b931faaf4` and `hamlet-d6fc84d147` into the divergence register before either
   unit lands an engine change.
