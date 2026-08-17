# Current State — HAMLET / Townlet        Checkpoint: 2026-08-17 · twenty-fifth checkpoint (`PDR-0074` the oracle moved forward; `PDR-0075` unit 3 landed, DIV-006 built)

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`).

| # | condition | status 2026-08-17 (`main` = `4222a917`, branch = `8c5fa2c8`+) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open — DIV-001/002 `tag-stamped` at `oracle-2026-08-17` (checkpoint-boundary, own rebuilds pending); DIV-003/004/005 **`retired`**; DIV-006 `built` |
| 2 | harness verdict vocabulary re-earned (`PDR-0056`) | **MET at `72144e7c`** — 20/20 `AGREE`, zero suppressions (`PDR-0074`, run `20260817-072714`); now narrowed by DIV-006 to the four profile-variable cells only (run `20260817-091351`: 16 `AGREE` + 4 `DIVERGED_AS_REGISTERED`, exactly three DERIVED hashes moved) |
| 3 | `Gates green` on a suite that hides nothing (`PDR-0059`) | **MET on `main` at `4222a917`** — the Full Test Suite workflow (bare `uv run pytest`, the nightly's own job) is green for the first time: run `31981122221`, owner-dispatched 00:08 UTC 08-17, **3239 / 24 / 0**. `PDR-0072` trigger 2 did not fire. The scheduled 06:00 UTC run should read the same tree; a red there is a new fact, not the owed one |

## What this session did

- **RESUME/ORIENT**: workspace loaded, tracker reconciled (no drift), grant re-confirmed **unchanged**
  (stamp left at 2026-08-16 per the standing rule). Owner sequenced: *re-tag question, then unit 3*.
- **Branch rebased onto `main`** (`4222a917` is an ancestor), force-pushed with lease, tree identical.
- **`PDR-0074` — the oracle moved forward to `oracle-2026-08-17` → `4222a917`** (`72144e7c`, tag pushed):
  the hash-only suppression was at its ceiling and no matrix cell could see unit 3 (no matrix pack declared
  a profile variable). Evidence re-earned at the commit (CI run ids; determinism CPU+CUDA re-run);
  DIV-001/002 re-stamped, DIV-003/004/005 retired; fixtures re-frozen; matrix 20 cells (+ `items_smoke`,
  `effects_smoke`); **acceptance 20/20 `AGREE`**. `hamlet-7e5e15d993` closed.
- **`PDR-0075` — unit 3 landed** (`8c5fa2c8`; `hamlet-f0ed709ecf` closed): the `obs_vfs` block → one field per
  exposed global/agent profile variable with a **required declared `semantic_type`** + one `obs_item_slots`
  feature; the runtime reads every field by declared scope; the name branch is deleted;
  `COMPILED_SCHEMA_VERSION` 1.16; 8 packs + `docs/config-schemas/vfs-profiles.md` updated. Full suite
  **3260/16/0**. **DIV-006 `built`** — matrix run `20260817-091351` (owner-executed) matched the prediction row
  for row. Design fork on item layout recorded and filed (`hamlet-1ad6383186`), not folded.
- Filed `hamlet-7cd887c9e5` (`configs/reference/model_pack` does not compile — `spawn_effect` schema rot).
- One CI red on the push to `8c5fa2c8`: the repo's `no_defaults_lint` gate caught a ternary-as-default in the
  new sync step; fixed in this checkpoint's commit — all three workflows green on `c69bd2ff`. Lesson kept: run
  all five Lint-workflow checks locally, not four.
- **After the checkpoint commit the owner ran the Full Test Suite on `main` by hand rather than wait for the
  schedule** (run `31981122221`, 3239 / 24 / 0) — exit condition 3 closes; the `PDR-0059` thread is done.

## Reversal triggers — read this session

- `PDR-0074` triggers 1 (determinism at the tag) and 2 (any non-AGREE at the new tag): **did not fire**.
- `PDR-0075` triggers (movers ≠ prediction; a non-profile cell leaves AGREE): **did not fire**.
- `PDR-0058` trigger 2 (register only grows): **reset** — three entries went terminal this checkpoint.
- `PDR-0072` trigger 2 (first post-merge full-suite run red on the three named files): **did not fire** —
  run `31981122221` green. `PDR-0043` trigger 2: discharged.

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated.** No vision/grant change, no release, no deprecation-with-users, no pricing, no data
  deletion, no external party.
- **Dependabot on `main`**: PRs `#33` (torch 2.11→2.13, low, an oracle-behaviour risk to the JIT kernels)
  and `#34` (pytest 8.4.2→9.0.3, moderate); setuptools <83 (moderate) had a failed update run. Not acted
  on; any merge to `main` is yours. Triage is a candidate next unit if you want it.
- **`CLAUDE.md:65` still cites the deleted `REVIEW-2026-08-15…` file**; the DTO list lacks
  `presentation_config.py`. Fourth flag.
- Next merge to `main` will owe `PDR-0039` gate 2 (README re-verification by method) again — 3+ commits ahead.

## Open questions

- Sibling primitive name-syncs (`obs_grid_encoding`, `obs_local_window`, `obs_position`, `obs_velocity`,
  meters, `obs_affordance_*`, `obs_effects`, `obs_temporal`, now `obs_item_slots`) — the general fix is a
  typed feature discriminator on the compiled field; a candidate next unit in WS-4's queue.
- `exposed_to` defaults to `["agent"]` when empty in the three profile validators (hidden default) — noted
  in `PDR-0075`, unfiled.
- Unchanged: `tests/README.md` staleness → WS-5; no schema-doc index lists `presentation.md`; no shipped
  pack declares `multi_tick` (`PDR-0061` armed); `hamlet-266a0a41f0` in triage; `cues` inert.

## Next session starts here

**Glance at the scheduled nightly** (`gh run list --workflow full-tests.yml --limit 1`, the 06:00 UTC 08-17
run) — it should match the owner-dispatched green on the same tree; a red is a new fact to explain, not the
`PDR-0059` thread reopening. Then pick the next WS-4 unit on `PDR-0019`'s criterion (*where does the runtime still know what the game is?*): the sibling
primitive name-syncs are the same shape unit 3 just killed. Dependabot triage is the owner's call.
Work continues on `project-recovery-2` (ahead of `main` by this session's commits).
