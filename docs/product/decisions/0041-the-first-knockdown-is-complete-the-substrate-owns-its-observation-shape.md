# PDR-0041 — The first knockdown is complete: the substrate owns its observation shape

Date: 2026-08-15   Status: **accepted** (within grant — ACCEPT of dispatched work against
`PDR-0035`'s unit definition, `PDR-0036`'s register scope, and `PDR-0037`'s order; no new
bet, no scope change beyond the recorded design edges below)
Author: Claude (standing product owner)
Related: `PDR-0035` (the unit this executes), `PDR-0036` (DIV-003's authorization),
`PDR-0037` (the order — steps 2–4 of which this completes), `PDR-0040` (the matcher these
cells were adjudicated by), `PDR-0019` (the selection criterion the cut answers),
`PDR-0006` (the strangler this is the first proof of)
Tracker: `hamlet-e3af412673` (WS-7 content 5 — all four steps DONE) · Commit: `b7574132`

## What was accepted

The **strangler method has now run end-to-end once**: register the divergence before
cutting (`PDR-0037` step 2), bind it to declared matrix cells that land red honestly
(step 3), cut the seam, and watch the harness flip exactly those cells to
`DIVERGED_AS_REGISTERED` while every standing cell stays byte-exact AGREE (step 4). This
was the whole point of not taking the one-line repair (`PDR-0035`): the first knockdown
proves the method, not just the fix.

The cut itself: a **five-member observation-shape contract on `SpatialSubstrate`**
(`supports_partial_vision`, `get_grid_encoding_dim`, `get_position_feature_dim`,
`get_vision_radius`, `get_partial_window_dim`), implemented by all six substrate families
and parity-pinned per substrate against **its own encoders' actual output widths**
(`test_observation_shape_contract.py`, 36 tests). `compilers/observation.py` and
`compilers/metadata.py` now build the substrate instance through the same factory door the
runtime uses and ask it — every `substrate.type` string switch is deleted. The runtime env
asks the same contract (`_configure_partial_observability`), so declared and produced dims
cannot drift by construction. WS-6's run-sheet check confirmed this is what unfinished
plan phase 9 prescribed ("Refactor observation builder → substrate-agnostic").

**Acceptance evidence:** full 16-cell matrix vs `oracle-2026-08-13`, exit 0, twice — CPU
(run `20260815-055108`) and CPU+CUDA (run `20260815-055207`); 10 standing cells AGREE
(byte-exact traces: preserved behaviour preserved), all 6 DIV-003 cells
`DIVERGED_AS_REGISTERED` naming their entry. pytest **3130/0** (+45: the contract, seam,
and matrix tests); ruff/black/mypy clean. Five-mutant battery in a detached worktree, loud
probe first, **all killed** — including reintroductions of each original defect (scaled
hardcode, 2-D window on 3-D grid, square masking, compiler-side dim derivation, dropped
radius floor). DIV-003's oracle behaviour was re-executed at `0e875d7a` through the
harness's own driver (injection probe-verified) *before* the entry was written — the
register's no-unchecked-copying rule, followed.

## Design edges recorded, so they are not relitigated

- **The window min-clamp is deleted** (`min(2r+1, grid_size)`, compiler and env). The
  encoders never clamped, so any config where the clamp engaged declared one width and
  produced another — the same declared-vs-produced drift as DIV-003, latent because no
  shipped pack reached it. Declared now always equals `encode_partial_observation`'s
  output; a window may overhang the grid (out-of-bounds cells empty). The test that pinned
  the clamp could only exist because it never called `reset()`; it now does.
- **Vision radius derives from the longest axis** (`max(width, height[, depth])`),
  reducing exactly to the historical `grid_size/2` formula on squares — standing traces
  unaffected; non-square partial vision gets defined semantics instead of a guard.
- **`type: grid3d` is deleted from the stratum schema** (zero-BC). It never had a factory
  branch — it could only compile toward a guaranteed crash — and the working 3-D path is
  `type: grid` + `topology: cubic`. Deliberately **outside DIV-003**: both sides crash on
  it, so there is no trace-visible divergence to register. Pre-release with zero users;
  inside the grant.
- **`ActionMaskBuilder` masks per axis** from the substrate's own extents. The old single
  `grid_size` masked the y axis with the x extent — correct only on squares; the fix is
  pinned by a test whose expectations derive from the env's own movement deltas.
- **`metadata.grid_size` is honest**: the square display size, `None` for non-square and
  non-grid substrates (the old code silently wrote `width`, discarding height).
  `metadata.position_dim` now comes from the instance (continuous substrates report their
  real dimensionality instead of 0); no consumer of either was found that depends on the
  old values.

## The instrument findings (the battery corrected itself)

1. **A mutation probe must be able to see its mutant.** M5 (dropped radius floor)
  "survived" the first battery because the probe input `vision_range=0.01` cannot
  distinguish it — `ceil` of any positive value is already ≥ 1; only `0.0` separates the
  behaviours. The test was fixed to probe `0.0` and the mutant re-killed. Standing rule,
  joining `PDR-0040`'s family: *an equivalent-looking survivor indicts the probe input
  before it indicts the code — pick inputs where the mutant's behaviour actually differs.*
2. **The stale-cache rule earned its keep again**: the first post-cut test run read
  `.compiled` msgpack caches written during the pre-cut harness run and reported the OLD
  dims. Purge `configs/**/*.msgpack` before measurements — now proven against the
  knockdown itself.

## Reversal triggers

- **Reopen this acceptance** if any standing cell stops AGREEing against
  `oracle-2026-08-13` and the divergence is attributable to `b7574132` — the cut claimed
  behaviour preservation for everything outside DIV-003, and a later-found trace
  divergence falsifies that claim.
- **The no-clamp decision**: if a window-overhang configuration surfaces runtime breakage,
  the fix is at the substrate (its contract answer and its encoder move together) — never
  a reintroduced compiler-side clamp, which is the declared-vs-produced drift this
  knockdown exists to end.
- **The grid3d deletion**: reversed only by building the type for real — a factory branch,
  contract implementations, matrix cells, and (pre-cut) a DIV-004 entry. Restoring the
  bare literal is the dead-surface antipattern, not a reversal.
- `PDR-0037` trigger 3 (fold the suppression path back out if two consecutive knockdowns
  register no trace-visible divergence) — **knockdown 1 registered one; the counter resets
  to zero.**
