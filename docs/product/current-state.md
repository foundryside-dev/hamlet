# Current State — HAMLET / Townlet        Checkpoint: 2026-08-17 · twenty-third checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`, owner-ruled) — not
when anything merges. Merging is a publication step *inside* the bet.

The three exit conditions, read rather than asserted:

| # | condition | status 2026-08-17 (`fb791193`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open (DIV-001..005; DIV-003/004/005 `built`, DIV-001/002 `tag-stamped`) — **no DIV-006 this session** |
| 2 | harness verdict vocabulary re-earned or successor recorded (`PDR-0056`) | open — matrix 16/16 `DIVERGED_AS_REGISTERED` (run `20260817-002157`), 0 `AGREE`, by construction until DIV-004/005 close |
| 3 | `Gates green` read on a suite that hides nothing (`PDR-0059`) | **MET ON THE BRANCH** (`PDR-0065`), re-read green at `fb791193`: 3247 / 16 / 0, nothing deselected; **plus a frontend gate that did not exist before: `npm test` 37/37** |

Work continues on **`project-recovery-2`**, now **27 commits ahead** of `main` (`07b26ed5`) once
this checkpoint commits: 24 at resume + `a5cca764` + `fb791193` + this. **`PDR-0068`'s trigger
(bank the merge before the next queue unit if commits ahead pass ~30) is three commits away** —
one more unit will cross it. `main` still carries all 33 formerly-hidden tests behind the marker.

## What this checkpoint did

- **Unit 2 of the authoring queue LANDED (`PDR-0069`, `PDR-0070`, `fb791193`).**
  `hamlet-0dd4ac24d9` closed with verification. Presentation is **declared** (new optional
  pack-root `presentation.yaml`, `PresentationConfig` DTO, loader in `demo/presentation.py`),
  **honest by default** (the server forwards each meter's declared bounds / lethality / cascade
  edges on `connected`; the frontend renders bar = fraction of declared range, plain value, no
  `%`/`$`, critical = within 20% of a lethal bound), **never inferred** (server-side
  `AFFORDANCE_ICON_MAP` deleted; every live name-branch in `frontend/src` — tiers, relationship
  map, colours, mood/social semantics, icon tables, per-name CSS tokens, the `value×100%` death
  certificate — gone). Home chosen by the owner: **observer-only, never compiled** — proven by
  test that no behavioural hash moves, so **no register entry** and `PDR-0058` trigger 2 stays
  armed at growth #1, unfired.
- **Prerequisite taken inside the unit (`PDR-0070`): `hamlet-d892e161c0` closed** —
  `frontend/package.json` had never existed; `npm install`, `vite build`, and now `npm test`
  run. The frontend has a gate for the first time.
- **Verified by execution, not schema:** full suite 3247/16/0 (+27 = the new tests); ruff /
  black / mypy / `no_defaults_lint` clean; matrix 16/16 exit 0; a live server on a *fresh*
  checkpoint (the 2026-08-14 ones are correctly rejected on `vfs_hash`) sent the real
  `connected` frame: `presentation=None`, eight meters in compiled order, money `max 999999.0`.
- Filed `hamlet-102db4c2e0` (`AffordanceGraph.vue` is dead — fed by a message nothing emits;
  delete or rebuild from the compiled graph). Docs: `docs/config-schemas/presentation.md` new;
  `frontend/CLAUDE.md` customization rewritten.
- Grant re-confirmed **unchanged** at the resume; no `vision.md` touch, no stamp owed.

## Reversal triggers — read this session

- **`PDR-0058` trigger 2**: did **not** fire — the register did not grow (`PDR-0069` kept
  presentation out of the compiled artifact by construction). Stays **armed at growth #1**.
- **`PDR-0068` trigger** (~30 commits ahead, or a second consecutive README decay): **26 → 27
  after this commit; not fired, but next in line.** README decay was not measured this session.
- **`PDR-0025` trigger** (presentation reaching the engine): now *mechanically* watched —
  `test_the_compiler_never_reads_presentation` goes red if it ever does.
- **`PDR-0047` trigger 2** (every pack writes the same value): unchanged, armed, protocol stands.

## Blocked on nothing. Flagged for the owner (not blocking, but you should know)

- **`CLAUDE.md:65` still cites the deleted `REVIEW-2026-08-15…` file** (your instructions file,
  not touched). Its DTO list also lacks `presentation_config.py` — incomplete, not false.
- **Two commits + this checkpoint are unpushed at the moment of writing.** Pushing
  `project-recovery-2` is inside `PDR-0046` and will be done right after this commit; note that
  the branch also carries your own `0da08142`, which goes up with it.
- **Nothing escalated.** No vision/grant change, no release, no deprecation-with-users, no
  pricing, no data deletion (the scratch checkpoint used for the live check lives in the session
  scratchpad, not `runs/`), no external party.

## Open questions

- **Merge before unit 3?** `PDR-0068` says bank exit condition 3 on `main` (README re-sweep by
  method per `PDR-0039`, then the owner merges) once commits ahead pass ~30. At 27 the honest
  recommendation for the next session is to **run the re-sweep and merge first**, then take
  `hamlet-f0ed709ecf`.
- `tests/README.md` / `tests/test_townlet/README.md` known-false beyond the marker (WS-5,
  comment 156); no schema doc for `variables[].semantic_type` / `interaction_type` (WS-5,
  comment 157). New this session: no schema doc *index* lists `presentation.md` (there is none
  to list it in).
- Unchanged: no shipped pack declares a `multi_tick` affordance or wrapping schedule
  (`PDR-0061` trigger armed); an agent cannot observe its own interaction progress
  (`hamlet-266a0a41f0`); the `cues` surface remains inert.

## Next session starts here

**Read `PDR-0068`'s trigger against the commit count first.** If the owner still prefers the
queue, unit 3 is **`hamlet-f0ed709ecf`** (split `obs_vfs` into per-variable fields with a
declared `semantic_type`; kills the last `obs_vfs` name branch) — that one *does* touch compiled
observation fields, so it needs a register entry (DIV-006), which **fires `PDR-0058` trigger 2**
and makes the re-tag question unavoidable. Either way the next session opens with a sequencing
call, not a cut: merge-then-unit-3-with-re-tag, or unit-3-with-re-tag-then-merge.
