# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 (later) · fifteenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). The first knockdown
is COMPLETE and accepted (`PDR-0041`, `b7574132`). **This session executed merge gate 1: CI
restoration (`PDR-0043`, `cb865af4`)** — inputs fixed first, three workflows now watch this
branch, the measured gate set widened 4→6 and all six are green locally. `hamlet-2100105c9a`
sits in **verifying**: it closes on the **first green CI run**, which fires on the owner's
push. A gate restored is not a gate verified.

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-15)

- **Grant standing, unchanged** (re-confirmed 2026-08-14). **The owner pushes the branch
  themselves** — and the next push now also fires the first CI run in this branch's history.
- Ahead of `origin/project-recovery` by **4 commits** after this checkpoint: `cb865af4` (CI
  restoration), `3191cd90` (**owner-committed mid-session**: CLAUDE.md rewritten again after
  `PDR-0042`'s trim + `docs/architecture/REVIEW-2026-08-15-architecture-docs-and-hld.md`, a
  14-agent docs review — feeds WS-5 `hamlet-7a52a63e0b`; read it before docs work),
  `d77e0610` (worktree-gitlink cleanup), and this checkpoint's commit.
- Bookkeeping still owed to `vision.md` (never edited silently): grant block reads
  `Last reviewed: 2026-08-11`; owner re-confirmed 2026-08-14. Fix at next approved touch.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **`hamlet-2100105c9a`** (P1, **verifying**, claude) — CI restoration. Close on the first
  green run of Lint + Tests + Config Validation on `project-recovery` (after owner push):
  `gh run list --branch project-recovery`. Optional full matrix afterward:
  `gh workflow enable 203224930 && gh workflow run full-tests.yml --ref project-recovery`.
- **`hamlet-c4ce5515cc`** (P2, new) — adjudicate the PROVISIONAL no-defaults whitelist
  entries (`vtc.py` raw-mapping parse defaults; `metadata.py` hasattr-guarded cost). Carries
  a `PDR-0019` sighting: `vtc.py` hardcodes social-residue telemetry labels — the compiler
  still knows what the game is.
- **WS-7** `hamlet-e3af412673` (P0, in progress, claude — claim expires 2026-08-16 17:29 UTC,
  NOT refreshed this session; re-claim if lapsed). Open DECIDE unchanged: close now
  (infrastructure proven) or keep as the standing knockdown home. Nothing blocks on it.
- **WS-3** `hamlet-1f89714685` still gates WS-4 `hamlet-15050f280a` (`PDR-0034`). **WS-6**,
  **WS-0** ready, untouched. Tooling P3s: `hamlet-312f75963b`, `hamlet-5e2032b166`.

## Two gates on the merge to `main` (`PDR-0039`)

1. **CI restoration — EXECUTED, verifying** (above). The merge checklist inherits `PDR-0043`
   trigger 2: restore the nightly cron at merge (or PDR its death) — the deferral must not
   decay into silent capability loss.
2. **README re-verification by the same method, not a re-read** — unchanged.

## What this checkpoint did

- **Recorded `PDR-0043`** (CI restored fix-inputs-first; nightly waits for the merge): two
  drifted packs repaired not excluded; the previously-unknown second failing gate
  (`no_defaults_lint`, 93 violations, all post-2025-11-28 code) adjudicated with the
  provisional-register pattern; acceptance = first green run, not the ship.
- **Metrics**: `Gates green` widened 4→6 (all green locally, row not done until CI runs);
  `Pre-release hygiene` — 12 stale whitelist entries pruned, ten expended mutation/probe
  worktrees deleted (221MB, diffs salvaged), ten accidentally-tracked gitlinks removed and
  `.claude/worktrees/` gitignored. **No reversal trigger fired.**
- Tracker reconciled: `hamlet-2100105c9a` → verifying (root_cause + fix_verification set);
  `hamlet-c4ce5515cc` filed. Nothing escalated; nothing outward-facing executed (workflow
  enable/disable is repo CI config, owner-directed, one-command reversible).

## Next session, start here

1. **After the owner pushes:** verify the three runs green, then close `hamlet-2100105c9a`
   naming the run IDs and `close_commit`. If any run is red for a cause the local set covers,
   `PDR-0043` trigger 1 has fired — reopen and re-examine the verification protocol itself.
2. **The standing DECIDE** (unchanged from last checkpoint): next knockdown unit on
   `PDR-0019`'s criterion — the vtc.py social-residue sighting is a fresh candidate — and
   WS-7 close-or-keep in the same DECIDE. Playbook fixed: `PDR-0037`+`PDR-0041`.

**Harness gate contract** (carry): `uv run python -m townlet.oracle.harness` — exit 0 iff
every cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its register entry; empty and
all-SKIPPED runs fail. NOT safe to run concurrently with itself in one checkout. DIV-003
cells stay suppressed until the oracle moves forward.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before measurements; verify red by
mutation in a detached worktree; a green test is not evidence — mutate first; enumerate
producers, not call shapes; a correction is not self-verifying; ask what a green tool cannot
see and what its red cannot distinguish; a verifier is not self-verifying — probe the
instrument first; a brief that argues with itself trains distrust (`PDR-0042`). **New
(`PDR-0043`):** *a gate restored is not a gate verified — close on the first green run, not
the ship*; *the scheduler reads the default branch's file — a branch-side cron edit changes
nothing until merge*; *a verification ledger can itself declare dead surface — prune the
whitelist like code*.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0029`, `PDR-0030`,
`PDR-0031`, `PDR-0032`, `PDR-0034`–`PDR-0042` (per their stated triggers), `PDR-0043` (the
nightly deferral and the provisional-whitelist pattern — reverse only via its three triggers).
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-14, unchanged; changing it escalates.
