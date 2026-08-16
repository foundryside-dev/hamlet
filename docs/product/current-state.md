# Current State — HAMLET / Townlet        Checkpoint: 2026-08-17 · twenty-fourth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`, owner-ruled) — not
when anything merges. Merging is a publication step *inside* the bet.

The three exit conditions, read rather than asserted:

| # | condition | status 2026-08-17 (`905acd96`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open (DIV-001..005; DIV-003/004/005 `built`, DIV-001/002 `tag-stamped`) — no DIV-006 |
| 2 | harness verdict vocabulary re-earned or successor recorded (`PDR-0056`) | open — 16/16 `DIVERGED_AS_REGISTERED`, 0 `AGREE`, by construction until DIV-004/005 close |
| 3 | `Gates green` read on a suite that hides nothing (`PDR-0059`) | **MET ON THE BRANCH** (`PDR-0065`); `main` still carries all 33 behind the marker until the merge below |

`project-recovery-2` is **28 commits ahead** of `main` (`07b26ed5`) at `905acd96`, 29 once this
checkpoint commits. **The branch is MERGE-READY and the merge is the owner's next action.**

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
- **`PDR-0072` trigger 1 armed:** any commit touching `src/`, `configs/`, `frontend/`, `.github/`,
  `scripts/` or `tests/` before the owner merges re-owes the sweep. This checkpoint commit is
  `docs/product/` only.
- **`PDR-0058` trigger 2**: unfired, armed at register growth #1 (unit 3 will fire it).
- **`PDR-0043` trigger 2**: stays discharged — the nightly is `active`, verified this sweep.
- **`PDR-0025`** (presentation reaching the engine): mechanically watched by test, unchanged.

## Blocked on the owner (the merge) · flagged, not blocking

- **The merge to `main` is yours (`PDR-0046`).** Both gates stand for `905acd96`: gate 2 executed
  (`PDR-0072`); gate 1 read on the push — confirm the Tests run `31968042996` finished green
  before merging (Lint/Config Validation already are). Suggested: `gh pr create --base main
  --head project-recovery-2` (PR #33) and merge as before; nothing else on the checklist —
  the nightly is already `active` and its file is now the same invocation as the per-push
  Tests job, so **the first nightly after the merge is the reading that closes the
  `main`-is-red thread** (expected green; if still red on the three named files, `PDR-0072`
  trigger 2 fires).
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

**Read `main`.** If the owner merged: confirm the merge commit, read the first post-merge nightly
(`gh run list --workflow full-tests.yml --limit 1`), and record `Gates green` on `main` for the
first time since the marker went — then open the re-tag question and take unit 3. If the owner
has not merged: nothing has changed — the branch is merge-ready at `905acd96` and `PDR-0072`
trigger 1 governs any commit that lands first.
