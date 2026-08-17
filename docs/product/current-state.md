# Current State — HAMLET / Townlet        Checkpoint: 2026-08-17 · twenty-seventh checkpoint (`PDR-0077`–`PDR-0080`: the north-star has a denominator for the first time — corpus frozen at 15, trial set N=9 drawn not chosen)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight,
no horizon change. Exits when the **pinned oracle can be RETIRED** (`PDR-0058`).

| # | condition | status 2026-08-17 (`main` = `4222a917`, branch = `62b5424d`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open — DIV-001/002 `tag-stamped` at `oracle-2026-08-17` (checkpoint-boundary, own rebuilds pending); DIV-003/004/005 `retired`; DIV-006 `built` |
| 2 | harness verdict vocabulary re-earned (`PDR-0056`) | **MET** (`PDR-0074`), narrowed by DIV-006 to the four profile-variable cells |
| 3 | `Gates green` on a suite that hides nothing (`PDR-0059`) | **MET on `main`** (run `31981122221`, 3239/24/0). Branch tip `62b5424d` green on all three (`31986232849`/`…853`/`…870`) |

**2. Measure the authoring claim — the INSTRUMENT** (`PDR-0077`, promoted Next → Now this session,
owner-chosen). Runs *alongside* bet 1, not instead of it. · tracker `hamlet-5fa1f7bfc0` · spec
**PRD-0001** (`ready-for-planning`) · metric: north-star **Zero-Python authoring rate (world)**.

## What this session did

- **RESUME/ORIENT**: workspace loaded, tracker reconciled (**zero drift** — every in-flight ID
  matched the brief), grant re-confirmed **unchanged** (stamp left at 2026-08-16 per the standing
  rule; no `vision.md` touch). Owner chose the session's bet from four options.
- **`PDR-0077` — the bet, and PRD-0001 written.** The north-star had never been readable: Trial 001
  scored a whole idea (`1 of 1`), Trial 002 scored halves (`3 of 4`), no scoring unit was ever
  defined. Twenty-six checkpoints of WS-4 units against an *input* metric while the outcome metric
  sat unread — named as the build trap and treated as the reason to take this bet first.
- **`PDR-0078` — ≥80% governs the metric, not the bet.** My own PRD conflated *does the instrument
  work* with *does the substrate score well*, which would have rewarded picking an easy corpus.
  Amended **before any trial ran** — the only legitimate window.
- **`PDR-0079` — a miss is not one thing** (owner steer: *"it's just a gap"*). Every non-PASS
  verdict classifies **ABSENT** / **INERT** / **BLOCKED**; escalation retargets off the raw rate
  onto the INERT count.
- **`PDR-0080` — corpus FROZEN at 15, trial set DRAWN not chosen.** SHA256 `48840cc3…8de935d9`.
  N=9 = **B, D, E, F, J, K, L, M, O**; held in pool A, C, G, H, I, P. Stratified over seven axis
  buckets, seeded by the corpus's own content hash. **Criterion 1 met a week early.**

## Reversal triggers — read this session

- `PDR-0072` trigger 2 (first *scheduled* post-merge nightly on `main`): **still pending** — at
  this checkpoint the 06:00Z 08-17 run had not fired; the last scheduled run is `31931718941`
  (08-16, failure, **pre-merge and expected**). The 00:08Z owner-dispatched run discharged the
  *tree*, not the scheduled confirmation.
- `PDR-0068` trigger (bank the merge before the next unit): **not lit** — 7 commits ahead of `main`
  against a ~30 threshold, and `Documentation truth` has not moved twice consecutively.
- `PDR-0058` trigger 2 (register only grows): **not touched**.

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated.** No vision/grant change, no release, no deprecation, no pricing, no data
  deletion, no external party. `vision.md` untouched.
- **Dependabot on `main`**: PRs `#33` (torch 2.11→2.13) and `#34` (pytest 8.4.2→9.0.3) still open;
  any merge to `main` is yours.
- **`CLAUDE.md:63-65` still cites the deleted `REVIEW-2026-08-15…` file** (verified absent this
  session); the DTO list lacks `presentation_config.py` (verified present). **Sixth flag** — it was
  proposed as a bet this session and not chosen, so it is now a decision deferred, not an oversight.
- Next merge to `main` owes `PDR-0039` gate 2 (README re-verification by method).

## Open questions

- **The instrument's next step is the protocol** — PRD-0001's top item, handed to
  `/axiom-planning`. The corpus is frozen but the written trial protocol does not exist yet, and
  criterion 3 (2 of 9 re-run blind, reproducing their verdicts) cannot be attempted without it.
- **Predicted first reading is ~1 of 9** against a standing bar of 8. Expect that to look alarming
  and to be mostly ABSENT — a build list. The number that actually matters is the **INERT** count;
  agent prediction 1–2 (L, possibly M), escalation threshold 3.
- Unchanged: `exposed_to` hidden default in the three profile validators (unfiled);
  `recurrent_vision_window_side` raises on a non-square window (unfiled); `hamlet-1ad6383186` (item
  layout), `hamlet-7cd887c9e5` (reference pack does not compile), `hamlet-266a0a41f0` (triage),
  `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**One reading first**: the scheduled nightly on `main` (`gh run list --workflow full-tests.yml
--limit 1`) — the 06:00Z 08-17 run should match the owner-dispatched green on the same tree; a red
is a new fact to explain and fires `PDR-0072` trigger 2. Then **write the trial protocol** — it is
PRD-0001's top item and it gates every trial; the first trial cannot run without it, and no trial
may run against an edited corpus (criterion 1 voids it). After that, trials run one per session
alongside the WS-4 queue; **L is the highest-information first trial** — it is the one predicted to
land INERT rather than ABSENT, against the already-known zero-writer fields of `hamlet-dc8f887cd5`.
Work continues on `project-recovery-2`.
