# The Oracle

**Tag:** `oracle-2026-08-17` → commit `4222a917` (the tip of `main` after PR #35)
**Moved forward:** 2026-08-17, by the standing product owner under `PDR-0074` (decision
record: `docs/product/decisions/0074-the-oracle-moves-forward-before-unit-3-because-the-matrix-is-blind-to-it.md`)
**History:** `oracle-2026-08-13` → `0e875d7a` (pinned 2026-08-13, `PDR-0030`; retained as a
tag and as `.oracle/oracle-2026-08-13` — no longer the harness's default reference)
**Stream:** WS-7 (`hamlet-e3af412673`)

## What this is

The strangler rewrite (`PDR-0006`) freezes the current system as an **oracle** and rebuilds
one design-space unit at a time against it. **The tagged tree is the specification for
preserved behaviour.** Spec-writing collapses onto genuinely new surface only; for everything
else, the question "what should this do?" is answered by running the oracle, not by reading
or writing prose.

Rules:

- **The oracle never mutates.** Nothing is ever committed "to the oracle". If a
  disqualifying defect is discovered in the tagged tree — one that fails `PDR-0028`'s carry
  test (freezing it would freeze artifact corruption, not a known quirk) — the oracle moves
  **forward** to a new tag after the fix lands, and the register is re-stamped. The old tag
  stays as history.
- **A diff against the oracle is a defect in the rebuild unless the register says
  otherwise.** Expected differences live in `known-divergences.md`, recorded at plan time,
  each with an adjudication rule.
- **Consult it mechanically.** `git worktree add --detach <dir> oracle-2026-08-17` gives a
  runnable oracle beside the working tree (the harness does this itself at
  `.oracle/<tag>`). Runs are reproducible: every pack declares
  `training.seed`, and `townlet.determinism.seed_all` is the single seeding door.

## Evidence at the tagged commit

All checked at `4222a917` exactly — not at a nearby commit (the working tree that produced
these readings differed from `4222a917` only under `docs/product/`, verified by
`git diff --stat 4222a917 HEAD -- . ':!docs/product'` returning empty):

- **Gates:** CI on the push to `main` at `4222a917` — `Tests` run `31971043702`
  (**3239 passed / 24 skipped / 0 failed**, nothing deselected — the default `uv run pytest`
  is the whole suite since the `slow` marker was removed, `PDR-0062`), `Lint` run
  `31971043734` (ruff, black, mypy), `Config Validation` run `31971043687`. The PR's own
  `lint` / `unit` / `validate-config-packs` runs passed too (`PDR-0073`).
- **Determinism:** same seed → bit-identical env trace, re-verified locally at this tree on
  **CPU and CUDA** (RTX 4060 Ti) through the `@torch.jit.script` vtc kernels —
  `tests/test_townlet/integration/test_determinism.py`: 5 passed, 0 skipped (the two
  `@requires_cuda` tests ran). Spawn placement is independent of Python's global `random`
  state (pinned by a test that forces the collision fallback).
- **Register:** DIV-001 and DIV-002 re-verified against the source at this commit and
  re-stamped `tag-stamped`; DIV-003, DIV-004 and DIV-005 `retired` — the tree at `4222a917`
  carries their rebuilt behaviour, so old and new no longer differ on those surfaces.
- **Matrix at the tag:** 20 cells (ten default_curriculum, six differential, four
  profile-variable), every fixture under `oracle_fixtures/` a byte copy of its live pack,
  **no cell declaring any divergence** — acceptance run `20260817-072714`: **20/20 `AGREE`
  on CPU and CUDA, exit 0**, `oracle_ref` `oracle-2026-08-17`, new side `ef54dfab`.

### Evidence at the previous tag (`0e875d7a`, `oracle-2026-08-13`) — retained

- **Gates:** ruff pass · black clean (501 files) · mypy clean (164 source files) ·
  pytest **2992 passed / 16 skipped / 0 failed** (one clean full-suite run).
- **WS-1:** all ten units landed and closed (`PDR-0029`); every WS-1 pinning test is in the
  green run above, so `PDR-0029`'s first reversal trigger ("a WS-1 pinning test goes red at
  the oracle-tag commit") was tested and did not fire.
- **Determinism:** same seed → bit-identical 40-step env trace, verified on **CPU and
  CUDA** (RTX 4060 Ti), through the `@torch.jit.script` vtc kernels which sit
  unconditionally on the step path.
- **Register:** DIV-001 and DIV-002 entered, their oracle-behaviour claims re-verified
  against the source at this commit (tree clean, `git status` empty at verification).

## What is deliberately NOT claimed

- **Training-loop determinism on GPU.** cuDNN backward passes and optimizer state under
  CUDA are unverified. The differential harness relies on **env-step trace** determinism
  only; do not cite this tag as evidence that a full training run reproduces on GPU.
- **Behavioural correctness beyond WS-1's ten units.** The oracle carries every known
  quirk that passed `PDR-0028`'s carry test — that is the point. DIV-001 and DIV-002 are
  frozen in, on purpose, and the rebuild diverges from them by design.
- **A direct diff against pre-normalization-programme behaviour.** That preservation was
  adjudicated cut by cut against `0e875d7a` (DIV-003/004/005, byte-identical streams on
  CPU and CUDA) and is inherited transitively by this tag; the old tag and its worktree
  remain for a by-hand re-run if that inheritance is ever questioned (`PDR-0074`).

## Relationship to the other WS-7 artifacts

| Artifact | Role |
|---|---|
| This tag | The frozen reference — old side of every differential run |
| `known-divergences.md` | Where new is *allowed* to differ, and how each diff is judged |
| Differential harness (`src/townlet/oracle/`, built — `PDR-0032`; it does **not** subsume WS-3, `PDR-0034`) | Runs old and new on the same logical pack, level and seed — each side a (code root, pack root) pair — and asserts agreement outside the register: exit 0 only when every cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED |
| Seam cutting | Per knockdown unit, not global (`PDR-0006` §2b) |
