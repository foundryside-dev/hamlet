# Current State — HAMLET / Townlet        Checkpoint: 2026-08-29 · forty-sixth checkpoint (`PDR-0126`–`PDR-0129`: **trigger 3 RULED, the Lint gate RESTORED after 47 dark pushes, gate 2 DISCHARGED, and the fourth merge is owner-directed and in flight**)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — the Now bet.
- **THE FOURTH MERGE LANDED: `main` = `9efadd3c` (PR #37, 2026-08-29)**, 143 commits / 921
  files / 38 PDRs from `project-recovery-2`, merge commit as the three before (`PDR-0129`).
  Gate 1 met (`PDR-0127`, all three green at `1065dbf0`); gate 2 discharged (`PDR-0128`).
  The Protect Main ruleset (2025-11) required a content-empty merge of `main` into the branch
  first (`1b4020aa`) and the `lint`/`unit` PR checks — both passed.
- **`hamlet-83c8e3b50e` is CLOSED by observation**: `main`'s tip got per-push Lint / Config
  Validation / Tests within ~60 s of landing. The third merge's silence was transient.
- **Work continues on `project-recovery-3`**, cut from `9efadd3c` and pushed.
- Bet exit (`PDR-0058`) unchanged and not met: oracle not retired, WS-3/WS-4 open.

**2. Token-observation encoding** (`PDR-0108`/`PDR-0114`) · `hamlet-fa6bb6da4a`. Unit 3 complete
(`PDR-0124`). **Trigger 3 is RULED — option 4 (`PDR-0126`)**: cap and constants stay, 9.43×
carried as debt into unit 5, re-measured there. **Unit 4/5 sequencing is no longer gated.**
Nine post-cut defects open in `triage` (ids in `PDR-0124`; `hamlet-6a4a6596bd` and
`hamlet-1e335e0363` are the two cheap ones and go first on the next branch).

**3. Documentation truth** (`PDR-0125`) — recovery labelled, rewrite gated on WS-4. The README
is re-verified as of this morning; `docs/product/` is consistent with it as of this checkpoint.

**4. Measure the authoring claim** — retired as record (`PDR-0111`); its ticket
`hamlet-5fa1f7bfc0` is now **closed**. Pack-disposition clock **2026-10-06** survives in
`roadmap.md`.

## What this checkpoint did

- `PDR-0126` — trigger 3 ruled (owner): option 4, debt into unit 5. `PDR-0124` status → RESOLVED.
- `PDR-0127` — Lint had been red 47 pushes (`7dc6f66c` → `8b733f3e`) under two "green"
  checkpoints; restored at `237b0c38` (Black) + `b915139e` (no-defaults: three real defaults
  made required, fifteen structural whitelisted with reasons). **New rule:** `Gates green` is
  written only from every workflow's conclusion at the tip SHA.
- `PDR-0128` — gate 2 for the fourth merge: 33 stale claims + 16 omissions in 143 commits; six
  defects in the draft's own corrections caught adversarially; stamped `1065dbf0` (`6fb148fd`).
- `PDR-0129` — merge now (fruit moves behind it; torch bump stays out), next branch is
  **`project-recovery-3`**, not a release branch.
- Metrics: `Gates green` and `Documentation truth` readings dated 2026-08-29; the trigger-3
  block reads *fired → escalated → ruled*.
- Tracker: `hamlet-5fa1f7bfc0` closed; comments on `hamlet-fa6bb6da4a` (276) and
  `hamlet-83c8e3b50e` (277). Working tree clean apart from this checkpoint.

## Standing gates & in-flight state (read before acting)

1. **Read `main`'s post-merge gates**: the per-push runs at `9efadd3c` (queued at landing —
   read their conclusions) and the first nightly (`PDR-0128` trigger).
2. **Local gate = CI gate**: `ruff check .`, `black --check src tests`,
   `no_defaults_lint.py` — all three before any push of product source (`PDR-0127`).
3. **Never take the torch bump (#33) as a dependency chore** — it can move the oracle
   (`PDR-0074` precedent). It is a WS-7 unit with its own PDR.
4. The doc rewrite stays blocked on `hamlet-ad2773718a` (prereq 2 = WS-4). Two matrix cells
   (`div003_scaled`, `items_smoke`) stay demoted as evidence; §5 finding is CPU-only.

## Reversal triggers — state

- `PDR-0126` armed: unit-5 re-measurement ≥ 8× calls the debt (options 1–3 reopen).
- `PDR-0127` armed: a >3-push red streak under a "green" checkpoint → the rule failed; make it
  mechanical.
- `PDR-0128`/`PDR-0129` armed on `main`'s first post-merge nightly and per-push CI.
- `PDR-0114` trigger 1 (≥ 79.19 IQM at equal env-steps) still unread — unit 4's measurement.
- Pack-disposition clock **2026-10-06** unchanged.

## Blocked on / flagged for the owner

1. **`vision.md` `Last reviewed` stamp** reads 2026-08-22; you re-confirmed the grant unchanged
   on 2026-08-29 but no stamp touch was offered, so per the 2026-08-15 rule the debt is carried.
   Approve the stamp correction at the next resume and it moves (the `PDR-0038` pattern).
2. Instrument redesign — promote or park (unchanged). WS-7 (`hamlet-e3af412673`, P0) — park or
   schedule (unchanged). Dependabot #33 (torch) — see gate 3 above; #34 (pytest) goes with the
   fruit.

## Open questions

- `hamlet-1e335e0363` (`range_type` inert post-cut): wire or retire — the framework's signature
  defect in miniature, and the first real call on the next branch.
- `hamlet-88578e629e`'s live `observable: bool = True` half stays open.
- Gate-2 cost scales with commits-since-stamp (18 in 43; 33 in 143). Merging more often is the
  cheaper discipline; nothing in the grant prevents it.

## Next session starts here

**Read `main`'s per-push conclusions at `9efadd3c` and the first nightly**, then on `project-recovery-3`: `hamlet-6a4a6596bd`
(delete the inert `observation_mode`/`observation_encoding`), `hamlet-1e335e0363` (rule on
`range_type`), Dependabot #34, then unit 4 (the `PDR-0114` trigger-1 probes) or WS-4 per the
owner's steer — the width cap no longer gates either.
