# Current State — HAMLET / Townlet        Checkpoint: 2026-08-18 · twenty-ninth checkpoint (`PDR-0082`: Trial L, the first of nine, is RUN — PASS, prediction falsified, the north-star has its first reading)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight,
no horizon change. Exits when the **pinned oracle can be RETIRED** (`PDR-0058`).

| # | condition | status 2026-08-18 (`main` = `4222a917`, branch = `484976d3`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open — DIV-001/002 `tag-stamped` (checkpoint-boundary, own rebuilds pending); DIV-003/004/005 `retired`; DIV-006 `built` |
| 2 | harness verdict vocabulary re-earned (`PDR-0056`) | **MET** (`PDR-0074`), narrowed by DIV-006 to the four profile-variable cells |
| 3 | `Gates green` on a suite that hides nothing (`PDR-0059`) | **MET on `main`, schedule-confirmed** (first scheduled nightly GREEN 08-17; `PDR-0072` trigger 2 discharged) — but note `main` does not carry units 3/4 (below) |

**2. Measure the authoring claim — the INSTRUMENT IS IN USE** (`PDR-0077`) · tracker
`hamlet-5fa1f7bfc0` (`in_progress`) · spec PRD-0001 · metric: north-star **Zero-Python authoring
rate (world)**, standing bar ≥8 of 9 by 2026-10-06. **First reading exists: 1 of 1 trials run,
split 0 ABSENT / 0 INERT / 0 BLOCKED** (`PDR-0082`). Remaining: 8 trials at one per session, then
2 blind re-runs (criterion 3) before any reading publishes.

## What this session did

- **RESUME/ORIENT**: workspace loaded, tracker reconciled, grant re-confirmed **unchanged**
  (stamp stays 2026-08-16 per the standing rule; no `vision.md` touch). **One drift item found
  and corrected here**: the prior brief said "5 commits ahead of `main`, all docs/workspace-only"
  — measured reality was 13 (now 14) including **two `src/townlet/` strangler units (unit 3
  `8c5fa2c8`, unit 4 `ebd16fce`) and the oracle move (`72144e7c`)**, +628/−305 under
  `src/townlet/`. `main`'s green nightly does not cover those units; branch CI does.
- **DECIDE**: owner chose "Run Trial L" (option 1 of the resume brief's proposals).
- **DISPATCH/ACCEPT — `PDR-0082`**: Trial L executed per the ACTIVE protocol at pin `fb8c6148`.
  **Headline PASS on all four pre-committed facets, both legs** — cooldown management authors
  zero-Python (timers as meters via declared negative passive drain, `if`-gated interactions,
  reset-on-use, observation at compiled offsets 31/32). **The pre-registered prediction
  (PARTIAL/INERT) is FALSIFIED and stated.** Record `docs/product/trials/0001/L-20260818.md`;
  pack `configs/trial_l_cooldown/`; suite 3281/16/0 before commit; commit `484976d3`, pushed.
- **By-catch filed, not fixed** (protocol §8): `hamlet-d45331a367` (`recovery.natural` required
  in every pack, consumed by zero runtime sites — live INERT) and `hamlet-6b24c0bd83`
  (`CapabilityConfig` incl. a purpose-built `CooldownCapability` reachable from no YAML — dead
  vocabulary). Both routed WS-4, label `prd-0001-trial`.

## Reversal triggers — state as of this session

- `PDR-0081` triggers: **armed, none fired** — 0 budget-limited records in 1 trial; no blind
  re-run yet; the one loud error (stale copied `.compiled` cache) was unambiguously a pack
  mistake, so the BLOCKED-vs-pack-mistake line was not stressed.
- `PDR-0068` trigger (bank the merge before the next unit): **not lit** — 14 commits ahead of
  `main` against a ~30 threshold, but see the drift correction above: the "docs-only"
  characterization was false, and the next merge owes `PDR-0039` gate 2 over that full span.
- `PDR-0058` trigger 2 (register only grows): not touched.
- Pack-disposition clock (`PDR-0082`): `configs/trial_l_cooldown/` must be promoted to a fixture
  or deleted by **2026-10-06** or PRD-0001 criterion 7 rejects the bet.

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated this session.** No vision/grant change, no release, no deprecation, no
  pricing, no data deletion, no external party. `vision.md` untouched.
- **Dependabot on `main`**: PRs `#33` (torch 2.11→2.13) and `#34` (pytest 8.4.2→9.0.3) still
  open; any merge to `main` is yours.
- **`CLAUDE.md:63-65` still cites the deleted `REVIEW-2026-08-15…` file** (eighth sighting; a
  deferred decision, not an oversight — proposed as a bet 08-17 and not chosen).
- Next merge to `main` owes `PDR-0039` gate 2 (README re-verification by method) over 14 commits
  including two src units and the oracle move.
- Cosmetic: filigree CLI needs `--actor claude` on updates to `claude`-assigned issues.

## Open questions

- **Prediction calibration**: Trial L falsified its own prediction *optimistically for the
  substrate* — the predictions were made against the first surface an author would reach, not
  the space of declared surfaces. The aggregate prediction (1–2 of 9 pass) is already 1-for-1
  against itself; the remaining eight will test it properly.
- Unchanged: `exposed_to` hidden default in the three profile validators (unfiled);
  `recurrent_vision_window_side` raises on a non-square window (unfiled); `hamlet-1ad6383186`
  (item layout), `hamlet-7cd887c9e5` (reference pack does not compile), `hamlet-266a0a41f0`
  (triage), `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Run trial two** — pick from B, D, E, F, J, K, M, O (protocol
`docs/product/prds/0001-trial-protocol.md`, §3 preflight first: P1 corpus hash, a mismatch voids
the trial). One trial is one session's work; the WS-4 queue (`exposed_to` default,
`hamlet-1ad6383186`, `hamlet-7cd887c9e5`, and now `hamlet-d45331a367` / `hamlet-6b24c0bd83`)
continues alongside in strangler sessions. Work continues on `project-recovery-2`.
