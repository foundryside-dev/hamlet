# Current State — HAMLET / Townlet        Checkpoint: 2026-08-17 · twenty-fifth (short — usage limit; `PDR-0074`, `PDR-0075`)

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`), exit = the pinned oracle can be
RETIRED (`PDR-0058`). Unchanged, in flight.

| # | condition | status 2026-08-17 |
|---|---|---|
| 1 | every register entry terminal | DIV-001/002 `tag-stamped` at the NEW tag; DIV-003/004/005 **`retired`**; **DIV-006 `tag-stamped`, not yet `built`** |
| 2 | verdict vocabulary re-earned | **MET at `72144e7c`** — 20/20 `AGREE`, zero suppressions (`PDR-0074`, run `20260817-072714`); narrowed again by DIV-006 on 4 cells only |
| 3 | `Gates green` on a suite hiding nothing | met on `main` (`4222a917`, per-push Tests green); first post-merge nightly still owed (fires 06:00 UTC 08-17) |

## What this session did

- Resumed; grant re-confirmed unchanged (stamp left at 2026-08-16). Branch rebased onto `main` and force-pushed with lease.
- **`PDR-0074` — the oracle moved forward:** `oracle-2026-08-17` → `4222a917` (tag pushed). Register re-stamped, fixtures re-frozen, matrix 20 cells (+ `items_smoke`, `effects_smoke`), acceptance 20/20 AGREE CPU+CUDA. `hamlet-7e5e15d993` closed at `72144e7c`. Filed `hamlet-7cd887c9e5` (`model_pack` doesn't compile).
- **`PDR-0075` — unit 3 cut (`hamlet-f0ed709ecf`), committed this checkpoint:** `obs_vfs` block → one field per exposed global/agent profile variable (declared `semantic_type`, REQUIRED) + one `obs_item_slots` feature; runtime reads every field by declared scope, `obs_vfs` name branch deleted; `COMPILED_SCHEMA_VERSION` 1.16; 8 packs + schema doc updated. Full suite 3260/16/0, ruff/black/mypy/config-validation green. Item-layout question filed `hamlet-1ad6383186`. **DIV-006 register entry is `tag-stamped`; the matrix adjudication run has NOT been executed yet.**

## Next session starts here

1. **Run the matrix** (`uv run python -m townlet.oracle.harness --cuda`): expect 16 `AGREE` + 4 `DIVERGED_AS_REGISTERED (DIV-006)` with exactly `observation_schema_hash, variable_schema_hash, vfs_hash` moved (measured pre/post already: env hash unchanged). Then set DIV-006 `built` in `docs/oracle/known-divergences.md`, close `hamlet-f0ed709ecf`, commit. If any other cell moves → `PDR-0075` trigger 3: stop and diagnose.
2. Read the first post-merge nightly (`gh run list --workflow full-tests.yml --limit 1`) → closes the `PDR-0059` thread or fires `PDR-0072` trigger 2.
3. Owed at checkpoint (not done this session): `roadmap.md` / `metrics.md` readings for `PDR-0074`/`0075` (Config-surface coverage: profile variables can now declare their group; Declared-but-inert: none added; exit condition 2 met-then-narrowed). Dependabot PRs #33/#34 and `CLAUDE.md:65` stale citation still flagged for the owner. Nothing escalated.
