# PDR-0029 — WS-1 is accepted complete against the plan's definition of done, and closed

Date: 2026-08-13   Status: **accepted** (within grant — accept against criteria)
Author: Claude (standing product owner)
Related: `PDR-0006` (the strangler this stream enables), `PDR-0008` (WS-1 verified by
execution and reordered), `PDR-0028` (the scope freeze this close vindicates)
Tracker: `hamlet-67ffbd282a` (WS-1, closed at `project-recovery@e8ad4985`),
`hamlet-88acec4bb5` (sibling 3b, closed same commit), `hamlet-e3af412673` (WS-7, unblocked)

## Context

WS-1 was the P0 gate on the entire strangler programme: ten units closing the defects that
would otherwise be frozen into the oracle as requirements. Nine had landed by the sixth
checkpoint. This session landed the tenth-but-one (sibling 3b — dead agents stop transacting)
and ran task 8, the batch close, whose gate is the plan's §4 definition of done: one gate
after task 8, not per-unit failure counts.

## Options

1. **Accept and close now** — the DoD is met mechanically: all four gates green
   (black 497 unchanged / ruff pass / mypy 163 files clean / pytest **2981 passed, 16
   skipped, 0 failed**), every unit red/green-verified with mutation checks, smoke record
   taken, tree hygiene clean (no msgpack artifacts, no `.pt`).
2. **Hold WS-1 open until the register-routed residuals land** — `hamlet-2dde1015fe`,
   `hamlet-df2b972c49`, and the unwritten hash-boundary tests (`hamlet-c8c316ba03`) are
   real gaps adjacent to WS-1's subject matter.

## The call

**Option 1 — accepted and closed.** Option 2 would quietly reverse `PDR-0028`: those
residuals were *deliberately routed around* WS-1 precisely so its scope could stop
receding. Holding the stream open for work the fence excluded would make the fence
meaningless and the freeze date recede again.

## Rationale

- Acceptance is against pre-stated criteria (§4/§0.1(f)), all of them checkable and all
  checked this session — not against a feeling of doneness.
- The one gate-time surprise (two `test_utilities_validation.py` tests stepping a CUDA env
  with CPU action tensors) was root-caused to a latent test defect newly exposed by the
  fix, repaired to the file's own existing pattern, and amended in so the tree stays green
  at every commit. Landing record: WS-1 comments #125–#127 (#127 corrects #126's
  normalization-mode claim — a correction is not self-verifying).
- Closing WS-1 unblocks WS-7, whose first artifact **must** be the known-divergences
  register (`PDR-0028`'s second reversal trigger fires on routing-to-nowhere).

## Reversal trigger

Reopen WS-1 (or file a successor unit under its admission bar) if:

- **Any WS-1 pinning test goes red at the oracle-tag commit** — the freeze would then be
  about to canonize a behaviour WS-1 claimed to have fixed; or
- **WS-7's determinism/differential work shows one of the ten units' fixes is wrong in
  substance** (not merely divergent-by-intent, which belongs in the register); or
- The `Gates green` guardrail regresses to red on a WS-1-touched surface before the freeze.
