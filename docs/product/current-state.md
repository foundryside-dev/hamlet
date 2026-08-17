# Current State — HAMLET / Townlet        Checkpoint: 2026-08-17 · twenty-sixth checkpoint (`PDR-0076` unit 4 landed: the compiled field says who fills it; no observation-field name branch survives)

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`).

| # | condition | status 2026-08-17 (`main` = `4222a917`, branch = `ebd16fce`+) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open — DIV-001/002 `tag-stamped` at `oracle-2026-08-17` (checkpoint-boundary, own rebuilds pending); DIV-003/004/005 `retired`; DIV-006 `built` |
| 2 | harness verdict vocabulary re-earned (`PDR-0056`) | **MET** (`PDR-0074`), narrowed by DIV-006 to the four profile-variable cells — re-read at unit 4, run `20260817-111409`: 16 `AGREE` + 4 `DIVERGED_AS_REGISTERED`, the same three hashes at the same values as at unit 3; unit 4 moved nothing |
| 3 | `Gates green` on a suite that hides nothing (`PDR-0059`) | **MET on `main`** (run `31981122221`, 3239/24/0). Branch at unit 4: suite 3281/16/0 locally; CI on `ebd16fce`: **all three green** (`31984884149` / `31984884176` / `31984884156`). The scheduled 06:00 UTC nightly on `main` had **not yet fired** at this checkpoint |

## What this session did

- **RESUME/ORIENT**: workspace loaded, tracker reconciled (no drift), grant re-confirmed **unchanged**
  (stamp left at 2026-08-16 per the standing rule). Found `5e5a60e8` (the previous checkpoint's
  follow-up commit) unpushed — pushed under `PDR-0046`. Owner chose the session's unit from four
  options: **WS-4 unit 4, the name-sync discriminator**.
- **`PDR-0076` — unit 4 landed** (`ebd16fce`; `hamlet-39e1fe3c6d` filed, claimed, closed): one closed
  vocabulary `townlet.universe.dto.observation_feature`; `ObservationField.feature` required
  (`meter` fields carry `feature_ref`); the encoder's nine name-keyed sync steps → one loop + one
  publisher table; `RecurrentSpatialQNetwork` slices by feature; one `recurrent_vision_window_side`
  helper for both demo sites; `build_vfs_variables` decides by feature, not name sets;
  `meter_name_from_observation_field` and the dead `obs_affordances` alias deleted;
  `COMPILED_SCHEMA_VERSION` 1.17. **Placement: DTO only, not the hash-bearing mirror** — measured
  invisible to the harness (20 cells, CPU + CUDA, exit 0), so **no register entry** (`PDR-0069`
  precedent). 21 new tests; suite 3281/16/0; all five Lint checks + Config Validation green locally.
- Docs brought current: `vfs.md` §4.3, `vfs-current-implementation.md` (also caught up to `PDR-0075`).

## Reversal triggers — read this session

- `PDR-0076` triggers (any of the sixteen leaves `AGREE`; the four DIV-006 cells move any hash
  other than the three registered): **did not fire** — measured exactly as predicted.
- `PDR-0058` trigger 2 (register only grows): **not touched** — the register did not grow.
- `PDR-0072` trigger 2: discharged last checkpoint; the first *scheduled* post-merge nightly is
  still owed a look (below).

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated.** No vision/grant change, no release, no deprecation-with-users, no pricing, no
  data deletion, no external party.
- **Dependabot on `main`**: PRs `#33` (torch 2.11→2.13) and `#34` (pytest 8.4.2→9.0.3) still open;
  any merge to `main` is yours. Offered a risk read; not chosen this session.
- **`CLAUDE.md:63-65` still cites the deleted `REVIEW-2026-08-15…` file**; the DTO list lacks
  `presentation_config.py`. Fifth flag.
- Next merge to `main` owes `PDR-0039` gate 2 (README re-verification by method) — 6 commits ahead.

## Open questions

- `exposed_to` defaults to `["agent"]` when empty in the three profile validators (hidden default) —
  noted in `PDR-0075`, still unfiled; a small WS-4 unit.
- `recurrent_vision_window_side` raises on a non-square window (a cubic partial-vision pack with the
  recurrent architecture) — the *network's* 2D assumption, noted in `PDR-0076`, unfiled.
- Unchanged: `hamlet-1ad6383186` (item layout), `hamlet-7cd887c9e5` (reference pack does not compile,
  triage), `hamlet-266a0a41f0` (triage), `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Two readings first**: (1) the scheduled nightly on `main` (`gh run list --workflow full-tests.yml
--limit 1`, the 06:00 UTC 08-17 run) — should match the owner-dispatched green on the same tree; a
red is a new fact to explain; (2) nothing else owed on the branch — CI on `ebd16fce` is green.
Then the next WS-4 unit on `PDR-0019`'s criterion (*where does the runtime still know what the game
is?*): the `exposed_to` hidden default is the cheapest honest one; `hamlet-7cd887c9e5` moves failure
loudness. Dependabot triage remains the owner's call. Work continues on `project-recovery-2`.
