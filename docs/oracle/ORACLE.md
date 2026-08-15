# The Oracle

**Tag:** `oracle-2026-08-13` → commit `0e875d7a` (branch `project-recovery`)
**Pinned:** 2026-08-13, by the standing product owner under `PDR-0006` (decision record:
`docs/product/decisions/0030-the-oracle-is-pinned.md`)
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
- **Consult it mechanically.** `git worktree add --detach <dir> oracle-2026-08-13` gives a
  runnable oracle beside the working tree. Runs are reproducible: every pack declares
  `training.seed`, and `townlet.determinism.seed_all` is the single seeding door.

## Evidence at the tagged commit

All checked at `0e875d7a` exactly — not at a nearby commit:

- **Gates:** ruff pass · black clean (501 files) · mypy clean (164 source files) ·
  pytest **2992 passed / 16 skipped / 0 failed** (one clean full-suite run).
- **WS-1:** all ten units landed and closed (`PDR-0029`); every WS-1 pinning test is in the
  green run above, so `PDR-0029`'s first reversal trigger ("a WS-1 pinning test goes red at
  the oracle-tag commit") was tested and did not fire.
- **Determinism:** same seed → bit-identical 40-step env trace, verified on **CPU and
  CUDA** (RTX 4060 Ti), through the `@torch.jit.script` vtc kernels which sit
  unconditionally on the step path. Spawn placement is independent of Python's global
  `random` state (pinned by a test that forces the collision fallback).
  `tests/test_townlet/integration/test_determinism.py`.
- **Register:** DIV-001 and DIV-002 entered, their oracle-behaviour claims re-verified
  against the source at this commit (tree clean, `git status` empty at verification).

## What is deliberately NOT claimed

- **Training-loop determinism on GPU.** cuDNN backward passes and optimizer state under
  CUDA are unverified. The differential harness relies on **env-step trace** determinism
  only; do not cite this tag as evidence that a full training run reproduces on GPU.
- **Behavioural correctness beyond WS-1's ten units.** The oracle carries every known
  quirk that passed `PDR-0028`'s carry test — that is the point. DIV-001 and DIV-002 are
  frozen in, on purpose, and the rebuild diverges from them by design.

## Relationship to the other WS-7 artifacts

| Artifact | Role |
|---|---|
| This tag | The frozen reference — old side of every differential run |
| `known-divergences.md` | Where new is *allowed* to differ, and how each diff is judged |
| Differential harness (next, reshapes WS-3) | Runs old and new against the same `CompiledUniverse`, asserts agreement outside the register |
| Seam cutting | Per knockdown unit, not global (`PDR-0006` §2b) |
