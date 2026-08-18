# Current State — HAMLET / Townlet        Checkpoint: 2026-08-18 · thirty-first checkpoint (`PDR-0084`: Trial M, the third of nine, is RUN — PASS, both predictions falsified, north-star 3 of 3 with the AGGREGATE pre-registration formally falsified)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight,
no horizon change, untouched this session. Exits when the **pinned oracle can be RETIRED**
(`PDR-0058`).

| # | condition | status 2026-08-18 (`origin/main` = `4222a917`, branch = `790dcb7e`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open — DIV-001/002 `tag-stamped` (checkpoint-boundary, own rebuilds pending); DIV-003/004/005 `retired`; DIV-006 `built` |
| 2 | harness verdict vocabulary re-earned (`PDR-0056`) | **MET** (`PDR-0074`), narrowed by DIV-006 to the four profile-variable cells |
| 3 | `Gates green` on a suite that hides nothing (`PDR-0059`) | **MET on `main`** — nightly 2-for-2 GREEN (verified again this session, runs `32003077539`, `32107696959`) |

**2. Measure the authoring claim — the INSTRUMENT IS IN USE** (`PDR-0077`) · tracker
`hamlet-5fa1f7bfc0` (`in_progress`) · spec PRD-0001 · metric: north-star **Zero-Python authoring
rate (world)**, standing bar ≥8 of 9 by 2026-10-06. **Third reading: 3 of 3 trials run, split
0 ABSENT / 0 INERT / 0 BLOCKED — all three PASS, and the aggregate pre-registration ("1,
possibly 2, pass") is formally FALSIFIED** (`PDR-0084`). Remaining: 6 trials at one per session
(B, D, E, J, K, O — four are multi-agent), then 2 blind re-runs (criterion 3) before any
reading publishes.

## What this session did

- **RESUME/ORIENT**: workspace loaded, tracker and GitHub state reconciled, grant re-confirmed
  **unchanged** (stamp stays 2026-08-16 per the standing rule; no `vision.md` touch). No
  material drift; local `main` ref is stale at `07b26ed5` (cosmetic — `origin/main` is right).
- **DECIDE**: owner chose "Run trial three." The executor selected **M (combo actions)** from
  the seven remaining — action-structure axis untouched, second live ABSENT/INERT test,
  single-agent one-session fit (`PDR-0084`).
- **DISPATCH/ACCEPT — `PDR-0084`**: Trial M executed per the ACTIVE protocol at pin `a519f312`.
  **Headline PASS on all five pre-committed facets, both legs** — sequential unlocking (A
  enables B enables C) authors as event-trace meters + whole-effect `if` gates, zero
  `src/townlet/` diff, chain composes to depth 3, traces observable including mid-chain.
  **Both predictions falsified**: M's own (PARTIAL/INERT), and the aggregate at 3 passes of 3.
  Record `docs/product/trials/0001/M-20260818.md`; pack `configs/trial_m_combo/`; suite
  3281/16/0 before commit; commit `790dcb7e`, pushed.
- **By-catch filed, not fixed** (protocol §8): `hamlet-f1dec55b9d` — the custom-action YAML
  surface cannot express effects or preconditions (`CustomActionConfig` is
  name/description/enabled-flag with `extra="forbid"`; runtime `reads`/`writes` reachable from
  no YAML). ABSENT, routed WS-4, label `prd-0001-trial`. This makes the ledger's "custom
  actions are structural no-ops" concrete through a mechanic someone actually wants.

## Reversal triggers — state as of this session

- `PDR-0081` triggers: **armed, none fired** — 0 budget-limited records in 3 trials; no blind
  re-run yet; the BLOCKED line has not been stressed.
- `PDR-0068` trigger (bank the merge before the next unit): **not lit** — 18 commits ahead of
  `origin/main` against a ~30 threshold; the span includes two `src/townlet/` units and the
  oracle move, so the next merge owes `PDR-0039` gate 2 in full.
- `PDR-0058` trigger 2 (register only grows): not touched.
- Pack-disposition clock (`PDR-0082`–`PDR-0084`): **three packs** — `configs/trial_l_cooldown/`,
  `configs/trial_f_durability/`, `configs/trial_m_combo/` — must each be promoted to a fixture
  or deleted by **2026-10-06** or PRD-0001 criterion 7 rejects the bet. The clock now carries
  real weight; a fixture-promotion session would clear it.

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated this session.** No vision/grant change, no release, no deprecation, no
  pricing, no data deletion, no external party. `vision.md` untouched.
- **Dependabot on `main`**: PRs `#33` (torch 2.11→2.13) and `#34` (pytest 8.4.2→9.0.3) still
  open (verified this session); any merge to `main` is yours.
- **`CLAUDE.md:65` still cites the deleted `REVIEW-2026-08-15…` file** (tenth sighting; a
  deferred decision, proposed as a bet 08-17 and not chosen).
- Next merge to `main` owes `PDR-0039` gate 2 (README re-verification by method) over 18
  commits including two src units and the oracle move.
- Cosmetic: filigree CLI needs `--actor claude` on updates; the comment command is
  `add-comment`. Local `main` ref is stale (harmless; `git fetch` updates `origin/main` only).

## Open questions

- **Prediction calibration, resolved against the aggregate**: 3 run, 2 falsified + 1 confirmed,
  aggregate falsified. The corpus's priors (built from the authorability ledger) were
  systematically pessimistic about single-agent mechanics — every falsification has the
  `PDR-0082` shape (first-reached surface incapable or awkward; a second declared surface
  expresses the idea). **The real test is ahead**: four of the six remaining trials (D, E, J,
  O) are multi-agent, where the predicted-FAIL reasons are structural (cross-agent transfer,
  heterogeneity, clearing phases), not surface-choice.
- **Blind re-runs** (criterion 3: 2 of 9 by 2026-10-06, chosen by the comparer, fresh session
  at the first run's pinned commit, executor barred from `docs/product/trials/`): three records
  now on file. The standing agent has read the records, so a blind executor must be a
  dispatched fresh agent. Worth scheduling before the backlog grows.
- Unchanged: `exposed_to` hidden default in the three profile validators (unfiled);
  `recurrent_vision_window_side` raises on a non-square window (unfiled); `hamlet-1ad6383186`
  (item layout), `hamlet-7cd887c9e5` (reference pack does not compile), `hamlet-266a0a41f0`
  (triage), `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Run trial four** — pick from B, D, E, J, K, O (protocol
`docs/product/prds/0001-trial-protocol.md`, §3 preflight first: P1 corpus hash, a mismatch
voids the trial); a multi-agent idea (D, E, J, O) would test the corpus's structural
predictions rather than its surface-choice ones — **or dispatch a blind re-run of L, F, or M**
(criterion 3; needs a fresh-context executor barred from the trial records) — **or clear the
pack-disposition clock** (promote the three trial packs to fixtures; one session, discharges
the 2026-10-06 risk early). One trial is one session's work; the WS-4 queue (`exposed_to`
default, `hamlet-1ad6383186`, `hamlet-7cd887c9e5`, `hamlet-d45331a367`, `hamlet-6b24c0bd83`,
`hamlet-fba3d5aa3c`, now `hamlet-f1dec55b9d`) continues alongside in strangler sessions. Work
continues on `project-recovery-2`.
