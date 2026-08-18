# Current State — HAMLET / Townlet        Checkpoint: 2026-08-18 · twenty-eighth checkpoint (`PDR-0081`: the trial protocol is ACTIVE — the instrument is whole, and the first trial can run)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight,
no horizon change. Exits when the **pinned oracle can be RETIRED** (`PDR-0058`).

| # | condition | status 2026-08-18 (`main` = `4222a917`, branch = `99b69540`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open — DIV-001/002 `tag-stamped` (checkpoint-boundary, own rebuilds pending); DIV-003/004/005 `retired`; DIV-006 `built` |
| 2 | harness verdict vocabulary re-earned (`PDR-0056`) | **MET** (`PDR-0074`), narrowed by DIV-006 to the four profile-variable cells |
| 3 | `Gates green` on a suite that hides nothing (`PDR-0059`) | **MET on `main` and now schedule-confirmed** — the first scheduled post-merge nightly is GREEN (run `32003077539`, 06:47Z 08-17); `PDR-0072` trigger 2 discharged without firing |

**2. Measure the authoring claim — the INSTRUMENT** (`PDR-0077`) · tracker `hamlet-5fa1f7bfc0`
(claimed, `in_progress`) · spec **PRD-0001** · metric: north-star **Zero-Python authoring rate
(world)**, standing bar ≥8 of 9 by 2026-10-06. **The instrument is now WHOLE**: corpus frozen
(`PDR-0080`) + protocol ACTIVE (`PDR-0081`, `docs/product/prds/0001-trial-protocol.md`, record
template `docs/product/trials/0001/TEMPLATE.md`). What remains is its **use**: nine trials at one
per working session, then 2 blind re-runs (criterion 3) before any reading publishes.

## What this session did

- **RESUME/ORIENT**: workspace loaded, tracker reconciled (zero substantive drift), grant
  re-confirmed **unchanged** (stamp stays 2026-08-16 per the standing rule; no `vision.md`
  touch). Corpus hash re-verified byte-identical. The brief's named first reading resolved
  **green**: the scheduled nightly on `main` succeeded, so `PDR-0072` trigger 2 is discharged.
- **DECIDE**: owner chose proposal 1 — write the trial protocol (PRD-0001's top item).
- **DISPATCH/ACCEPT — `PDR-0081`**: protocol written via `/axiom-planning`
  (plan: `docs/plans/2026-08-18-trial-protocol.md`), four design calls recorded (pinned-commit
  blind re-runs; leg (a) counts untracked files; one-session budget with stopping rule; BLOCKED
  = the idea refused, not the pack), verified by executing every documented command against the
  live tree at `2c1275d6` before the Status flipped ACTIVE. Commits `7cd19f17`→`99b69540`, pushed.
- **Housekeeping**: prior checkpoint commit pushed; tracker description reconciled to the amended
  N=9 shape (it had still carried the pre-amendment 5-idea text).

## Reversal triggers — state as of this session

- `PDR-0072` trigger 2: **discharged without firing** (scheduled nightly green, above).
- `PDR-0068` trigger (bank the merge before the next unit): **not lit** — 5 commits ahead of
  `main`, all docs/workspace-only, against a ~30 threshold.
- `PDR-0081` triggers now **armed**: blind-run disagreement (kills the instrument's acceptance);
  two budget-limited records in the first three trials (budget mis-sized); an ambiguous
  BLOCKED-vs-pack-mistake call (taxonomy returns to design).
- `PDR-0058` trigger 2 (register only grows): **not touched**.

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated this session.** No vision/grant change, no release, no deprecation, no
  pricing, no data deletion, no external party. `vision.md` untouched.
- **Dependabot on `main`**: PRs `#33` (torch 2.11→2.13) and `#34` (pytest 8.4.2→9.0.3) still
  open; any merge to `main` is yours.
- **`CLAUDE.md:63-65` still cites the deleted `REVIEW-2026-08-15…` file** (re-verified absent
  this session; seventh sighting). A deferred decision, not an oversight — it was proposed as a
  bet on 08-17 and not chosen.
- Next merge to `main` owes `PDR-0039` gate 2 (README re-verification by method).
- Cosmetic: filigree CLI warns `ACTOR_MISMATCH claimed='claude' verified='john'` on updates —
  audit-trail noise, updates land.

## Open questions

- **Trial L's facet enumeration is the first act of the first trial** — per protocol §4 it is
  pre-committed before authoring, and it will test the protocol as much as the substrate.
  Prediction on record: L lands **INERT** against `hamlet-dc8f887cd5`'s zero-writer fields;
  aggregate 1–2 of 9 pass, INERT count 1–2 (threshold 3).
- Unchanged: `exposed_to` hidden default in the three profile validators (unfiled);
  `recurrent_vision_window_side` raises on a non-square window (unfiled); `hamlet-1ad6383186`
  (item layout), `hamlet-7cd887c9e5` (reference pack does not compile), `hamlet-266a0a41f0`
  (triage), `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Run Trial L** (cooldown management — the highest-information draw). Protocol:
`docs/product/prds/0001-trial-protocol.md`, start at §3 preflight (P1 corpus hash first — a
mismatch voids the trial). One trial is one session's work; the WS-4 queue
(`exposed_to` default, `hamlet-1ad6383186`, `hamlet-7cd887c9e5`) continues alongside in strangler
sessions. Work continues on `project-recovery-2`.
