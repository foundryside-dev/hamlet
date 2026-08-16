# Current State — HAMLET / Townlet        Checkpoint: 2026-08-17 · twenty-fourth checkpoint (amended the same session: THE SECOND MERGE LANDED, `PDR-0073`)

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`, owner-ruled) — not
when anything merges. Merging is a publication step *inside* the bet.

The three exit conditions, read rather than asserted:

| # | condition | status 2026-08-17 (`main` = `4222a917`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open (DIV-001..005; DIV-003/004/005 `built`, DIV-001/002 `tag-stamped`) — no DIV-006 |
| 2 | harness verdict vocabulary re-earned or successor recorded (`PDR-0056`) | open — 16/16 `DIVERGED_AS_REGISTERED`, 0 `AGREE`, by construction until DIV-004/005 close |
| 3 | `Gates green` read on a suite that hides nothing (`PDR-0059`) | **MET ON `main`** as of `4222a917` (`PDR-0065`, `PDR-0073`) — confirm on the first post-merge nightly (`PDR-0072` trigger 2 if red) |

**THE SECOND MERGE LANDED: `main` = `4222a917`** (PR #35, merge commit of `07b26ed5` + `f023b9e7`,
29 commits; `PDR-0073`). Executed by the agent on the owner's explicit in-session instruction — the
`PDR-0046` boundary is unchanged, not a precedent. `project-recovery-2` is 0 ahead / 0 behind;
`main`'s README is byte-identical to the branch's; `main` no longer carries the `slow` marker.

## What this checkpoint did

- **Sequencing decided at the resume (`PDR-0071`, owner-chosen): merge first, unit 3 after.**
  `PDR-0068`'s trigger lit on both prongs — 27 commits ahead, and README decay *measured* at
  ORIENT (two claims falsified by the last two units).
- **Gate 2 EXECUTED for the second merge (`PDR-0072`, `905acd96`, stamped at `54132aaf`).** Four
  ground-truth verifiers executed every README claim (compiles + hash comparison, byte-diff of
  the quoted YAML, every CLI command, a harness cell, a two-episode training run, `npm test`,
  60 CI runs + 91 nightly runs from the API); **twenty-one claims stale or misleading in 27
  commits**, then the adversarial pass caught **ten more** in the revised draft — all fixed, not
  re-described. Same rule applied to three in-code texts the sweep named (`harness.py`
  docstring, `full-tests.yml` comment, `ORACLE.md` harness row). Pushed (`PDR-0046`); CI on the
  push: **Lint ✅ Config Validation ✅, Tests in progress at checkpoint** (`31968042996`).
- **New durable rule (`PDR-0072`):** a claim about `main` in a file that will *become* `main`'s
  README must be written to be true after the merge — pin it to the stamp or state the
  transition. The mirror of `PDR-0065`'s reading note.
- Filed `hamlet-0d750af814` (run-directory layout branches on the literal path segment `runs`)
  and `hamlet-df91baa2bb` (stray unread `drive_as_code.yaml` fixture + legacy loader). WS-7
  lease heartbeated. Grant re-confirmed **unchanged**; no `vision.md` touch, stamp left at
  2026-08-16 per the standing rule.

## Reversal triggers — read this session

- **`PDR-0068` trigger: FIRED on both prongs** and answered by `PDR-0071` (merge first).
- **`PDR-0072` trigger 1: did not fire** — the only commit between the sweep (`905acd96`) and
  the merge was the `docs/product/` checkpoint. **Trigger 2 now live** on the first post-merge
  nightly.
- **`PDR-0058` trigger 2**: unfired, armed at register growth #1 (unit 3 will fire it).
- **`PDR-0043` trigger 2**: stays discharged — the nightly is `active`, verified this sweep.
- **`PDR-0025`** (presentation reaching the engine): mechanically watched by test, unchanged.

## Blocked on the owner (the merge) · flagged, not blocking

- **DONE — the merge landed at `4222a917`** (`PDR-0073`; both gates re-read green at the tip
  first: `f023b9e7` Tests 3239/24/0-deselected). Newly recorded fact: `main` is governed by
  ruleset 9453164 — PR required, non-fast-forward, required checks `lint`+`unit` on the PR's own
  runs, auto-merge disabled — which is why every merge here is a PR merge commit. **The first
  post-merge nightly (`Full Test Suite`, 06:00 UTC) is the reading that closes the `main`-is-red
  thread** (expected green; if still red on the three named files, `PDR-0072` trigger 2 fires).
- GitHub reported **4 Dependabot vulnerabilities on the default branch (2 moderate, 2 low)** at
  push time — surfaced, not acted on; triage is a candidate for next session if you want it.
- **`CLAUDE.md:65` still cites the deleted `REVIEW-2026-08-15…` file** (owner's file; DTO list
  also lacks `presentation_config.py`). Third flag.
- **Nothing escalated.** No vision/grant change, no release beyond the merge you already own,
  no deprecation-with-users, no pricing, no data deletion, no external party.

## Open questions

- After the merge, **unit 3 is `hamlet-f0ed709ecf`** (split `obs_vfs` into per-variable fields
  with declared `semantic_type`; kills the last `obs_vfs` name branch). It touches compiled
  observation fields → needs DIV-006 → fires `PDR-0058` trigger 2 → the **re-tag question**
  (re-freeze the oracle past the normalization programme so `AGREE` becomes reachable again,
  `PDR-0056`) becomes unavoidable. Open the next session with that decision, not the cut.
- Cheap follow-ons: `hamlet-102db4c2e0` (`AffordanceGraph.vue` dead), `hamlet-0d750af814`,
  `hamlet-df91baa2bb`.
- Unchanged: `tests/README.md` staleness → WS-5; no schema doc for `variables[].semantic_type` /
  `interaction_type` (WS-5, comment 157); no schema-doc index lists `presentation.md`; no shipped
  pack declares `multi_tick` (`PDR-0061` armed); `hamlet-266a0a41f0` in triage; `cues` inert.

## Next session starts here

**Read the first post-merge nightly** (`gh run list --workflow full-tests.yml --limit 1`, the run
after 2026-08-16T06:33Z) and record `Gates green` on `main` from it — green closes the thread
`PDR-0059` opened; red fires `PDR-0072` trigger 2. Then open the **re-tag question** (`PDR-0056`)
and take unit 3 (`hamlet-f0ed709ecf`) with its DIV-006 entry. Work continues on
`project-recovery-2` (now level with `main`) unless the owner wants a fresh branch name — the CI
trigger glob covers `project-recovery*` either way.
