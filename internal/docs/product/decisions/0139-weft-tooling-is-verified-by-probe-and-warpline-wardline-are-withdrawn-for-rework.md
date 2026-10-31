# PDR-0139 — Weft tooling is verified by probe, not by doctor; warpline and wardline are withdrawn for rework

Date: 2026-09-02   Status: **accepted** (owner-directed: *"make all those 3"*; wardline/warpline
uninstall stated by the owner in the same message)
Author: Claude (standing product owner)
Related: `PDR-0038`, `PDR-0127`, `PDR-0138`, `project-recovery-3@b2a10f3e`, `@9318d86f`

## Context

At the 2026-09-02 resume the owner asked for filigree and loomweave to be brought "up to
speed/spec". Both tools' own doctors passed on every check but one cosmetic line each, and both
were at their newest published versions (loomweave 1.6.0 and plugins, PyPI 2026-08-30; filigree
3.1.0 built from the owner's dev checkout at its HEAD). Yet the seam between them was dead:
`loomweave.yaml` carried loomweave's baked-in default filigree URL on port 8766, filigree's own
default is 8377, and this machine pins the server to 8749. Nothing listened on 8766, so every
loomweave→filigree call (issue lookups on entities, finding bridging) had been failing silently
since the file was created on 2026-08-15. Neither doctor checks whether anything answers at the
configured URL.

Three further findings from the same pass:

1. An orphaned pre-`.weft` `.filigree/` directory (install version 14, log ending 2026-08-15)
   sat beside the live `.weft/filigree/` (install version 29), identical config, no database.
2. `.claude/settings.json` ran a warpline `session-context` hook every session start, the
   post-commit git hook called warpline, and `CLAUDE.md`/`AGENTS.md` carried installer-generated
   Warpline instruction blocks — with no warpline or wardline binary installed. The owner stated
   in-session that both were uninstalled deliberately and *"are going back for reworking"*.
3. Loomweave doctor reported stale git-sync hooks, missing three-way integration bindings and
   85 index rows for files deleted at the M4 cut (`9d4e942f`).

This is the same shape `PDR-0127` recorded for CI: a green instrument that was not measuring the
thing that mattered.

## Options considered

1. **Trust the doctors and stop.** Rejected: both said healthy while the federation link was dead.
2. **Fix the port, leave the dead warpline wiring in place until the tools return.** Rejected: a
   hook against a missing binary fails on every session start, and instruction blocks telling
   agents to prefer `mcp__warpline__*` tools that do not exist are exactly the declared-but-inert
   defect the product refuses elsewhere.
3. **Fix the seam, remove the dead wiring, keep what re-adoption needs, verify by probe.** Chosen.

## The call

- `loomweave.yaml` points at `http://127.0.0.1:8749` (`b2a10f3e`). Verified: `/api/health`
  answers 200 with the federation token. The running serve process reads it on next start.
- Both doctors' `--fix` paths applied: filigree context regenerated, loomweave hooks and bindings
  repaired, stale rows purged, index re-analysed and fresh at HEAD.
- The Warpline instruction blocks are removed from `CLAUDE.md` and `AGENTS.md` (`9318d86f`). The
  warpline SessionStart hook (ignored file) and the warpline-managed post-commit git hook are
  removed locally.
- `.filigree/` is deleted. **This is a data deletion under the grant and was approved by the
  owner explicitly in-session before it ran**; it held no evidence, no database, and nothing not
  duplicated in `.weft/filigree/`.
- **Retained on purpose**, per `PDR-0038`: the `wardline-gate` and `warpline-workflow` skill packs,
  `weft.toml`, and the `.wardline/` gitignore line. They are what re-adoption will need; the
  roadmap's Later bet *"Adopt wardline as a hygiene activity"* is unchanged in horizon — its
  precondition is now "the reworked tools return", not "declare trust boundaries".
- Three commits pushed to `origin/project-recovery-3` at `9318d86f`, including the owner's own
  `dc92e8ba` (regenerated loomweave skill docs). Push is within the grant (`PDR-0099`) and was
  also owner-approved.

## Consequences

- **Tool health at resume is a probe, not a doctor.** From this checkpoint, "filigree and
  loomweave are healthy" means: both doctors clean **and** `project_status_get` reports the
  filigree `resolved_url` answering `/api/health` 200 with the federation token **and**
  `staleness == fresh`. A doctor line alone does not count.
- Two upstream defects belong to the owner's other repos, not to hamlet's tracker: filigree's
  generated instruction block says data lives in `.filigree/` while the tool runs from
  `.weft/filigree/`; loomweave's shared `ephemeral.port` file is deleted when any one of several
  concurrent serve processes exits, so the read-API resolves to none while others still run.
- The filigree build is from branch `feat/weft-suppression-conformance` at `2052e7a`, nine
  commits ahead of and two behind `origin/main` (the June RED-1 closure-gate fix). Noted, not
  acted on: it is a filigree-repo decision.

## Reversal trigger

- If the loomweave→filigree probe fails at any `/own-product` resume (non-200 on `/api/health`
  at the configured URL, or `staleness != fresh` after one incremental analyze), this ruling
  reopens as a Gates-green guardrail breach and the seam is treated as broken until proven.
- When warpline or wardline is reinstalled, their installers regenerate the instruction blocks and
  hooks; nothing removed here is to be hand-restored. If the owner decides the reworked tools are
  **not** coming back, the retained skill packs and `weft.toml` go too, under a successor PDR
  that supersedes the retention half of `PDR-0038`.
