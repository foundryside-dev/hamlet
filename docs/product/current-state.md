# Current State — HAMLET / Townlet        Checkpoint: 2026-08-16 (latest) · twenty-first checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`, owner-ruled) — not
when anything merges. Merging is a publication step *inside* the bet.

The three exit conditions, read rather than asserted:

| # | condition | status 2026-08-16 (`a725bf66`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open (DIV-001..004; DIV-004 `built`) |
| 2 | harness verdict vocabulary re-earned or successor recorded (`PDR-0056`) | open — matrix 16/16 `DIVERGED_AS_REGISTERED`, 0 `AGREE`, by construction until DIV-004 closes |
| 3 | `Gates green` read on a suite that hides nothing (`PDR-0059`) | **MET ON THE BRANCH** — nothing deselected, marker gone (`PDR-0065`) |

Work continues on **`project-recovery-2`**, now **21 commits ahead** of `main` (20 + this
checkpoint). `main` is at `07b26ed5` and still carries all 33 formerly-hidden tests behind the
marker; its nightly reported 31 failed again this morning (run `31931718941`) — expected, cleared
by the next merge. Merge gate 2 (`PDR-0039` README re-sweep at the merge commit) is owed by all 21.

## What this checkpoint did

- **Reframed and closed the harness issue (`PDR-0065`).** ORIENT read the oracle context that
  `PDR-0063` had deferred to: **DIV-004 had already chosen *register*** (fixture stays at the old
  schema for the programme), and the **matrix had certified the meter cut** at `2535a306`. The
  defect was two harness *self-tests* — `run_cell` named the old side by code root alone and
  hardcoded its pack root; a self-comparison has no oracle side. Fix: `run_cell(old_pack_root)`
  **required**, `pack_drift` over the two roots actually read. TDD (four tests RED on the missing
  kwarg → GREEN); hypothesis probed before any change. `hamlet-6f98e38a36` closed.
- **Discharged `PDR-0062`'s trigger in the same commit** (`a725bf66`): `-m "not slow"` out of
  `addopts`; the marker declaration deleted from `pyproject.toml` *and* a duplicate registration
  in `conftest.py` citing a `--runslow` that never existed; `full-tests.yml` runs bare
  `uv run pytest`; both test READMEs' marker sentences corrected. `hamlet-a0832f9004` **closed on
  its held acceptance**: default suite **3193 passed, 16 skipped, 0 failed, nothing deselected**.
- **Took a post-fix harness reading through `main()`'s new plumbing**: run `20260816-184228`,
  CPU+CUDA, 16/16 `DIVERGED_AS_REGISTERED`, exit 0 — identical to `20260815-213851`.
- **Grant re-confirmed unchanged** by the owner at the resume; owner ruled *take the harness issue
  now as repair* and approved the unit through to checkpoint. Pushed `a725bf66` under `PDR-0046`.
- Corrected two of this workspace's own false claims found at ORIENT (below).

## Drift found at ORIENT and corrected here (do not inherit)

- **The last brief predicted the nightly would show "RED (2 failures)". It showed 31.** The nightly
  reads the *default branch*, which is 20+ commits stale; the 2 harness failures were branch-only.
  Same shape as `PDR-0058` — a claim about `main` written from the branch — one checkpoint after
  `PDR-0058` named it. Rule now in `metrics.md` → Reading notes.
- The commit-count line said 17 ahead; it was 19 (two post-checkpoint product commits).
- `PDR-0063`'s headline — *"the harness cannot currently certify anything"* — was an
  overstatement; superseded **in part** by `PDR-0065`, body untouched.

## Blocked on nothing. Flagged for the owner (not blocking, but you should know)

- **`vision.md`'s authority grant reads `Last reviewed: 2026-08-15`; you re-confirmed it unchanged
  on 2026-08-16.** Not touched: the 2026-08-15 amendment established that the stamp is corrected
  only *at an approved touch*, and this session's approvals did not include a `vision.md` edit.
  Offer stands for the next resume — a factual stamp correction, `PDR-0038`'s pattern.
- **`full-tests.yml` is now identical in command to `tests.yml`** (`hamlet-44ef388ecc`, P3).
  `PDR-0043` trigger 2 restored the nightly deliberately and it earned its keep once; whether a
  scheduled re-run of an unchanged `main` still buys anything is a PDR-sized call left open on
  purpose (`PDR-0065` trigger 2). Not urgent.
- **Nothing escalated.** No vision/grant, release, deprecation-with-users, pricing, data-deletion,
  or external-party action this session; the push is inside `PDR-0046`.

## Open questions

- **Exit condition 3 is met on the branch and no further than that.** The merge that makes it true
  on `main` owes `PDR-0039`'s re-sweep on 21 commits — the README decayed ten claims in one day the
  last time this was measured. That sweep is the next merge's price, not this session's.
- **`tests/README.md` / `tests/test_townlet/README.md` are known-false beyond the marker** (a
  `slow/` directory and smoke configs that do not exist; 2026-05-16 counts; the 19% coverage
  artefact). Named and routed to WS-5 `hamlet-7a52a63e0b` (comment 156), not fixed.
- Unchanged from last checkpoint: no shipped pack declares a `multi_tick` affordance or wrapping
  schedule (`PDR-0061` trigger armed); an agent cannot observe its own interaction progress
  (`hamlet-266a0a41f0`).

## Next session starts here

The authoring-surface queue, displaced for two sessions by the hidden-failure work, is clear again:
**`hamlet-2fe1c34ebb`** (P1, `semantic_type` has three disagreeing vocabularies and no authority,
`default="custom"` against no-defaults) with **`hamlet-45b35cfee5`** (P2, `interaction_type` — same
shape) taken **in one pass**; **`hamlet-0dd4ac24d9`** (P1, presentation hardcoded by variable name)
behind them. All three move *Declared-but-inert* and *Config-surface coverage*.

If instead the preference is to bank exit condition 3 on `main`, the unit is the merge: run
`PDR-0039`'s README re-sweep by method at the merge commit, then merge — an owner action
(`PDR-0046`: publication is not undone by pushing again).
