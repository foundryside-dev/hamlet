# PDR-0121 — The compiler has two eras and a declaration-store target; cleanup buys 1+2 executed in a worktree behind a hash-identical bar

Date: 2026-08-24   Status: **accepted** (assessment + target shape within grant; the
cleanup execution was owner-directed in-session — "can you task a fable agent to do 1
and 2 now (we'll yolo it)")
Author: Claude (standing product owner)
Related: `PDR-0117` (the declaration-store unit this aligns with), `PDR-0118` (the
COMPILER.md doc this feeds)
Assessment record:
`docs/architecture/archive/REVIEW-2026-08-24-compiler-architecture-assessment.md`
Tracker: `hamlet-af929afa06` (cleanup task; comment 248 records results + landing gate)

## Context

The owner characterized the compiler: "carefully architected and badly implemented, and
then it was better implemented but poorly architected." A Fable assessment verified
both halves and localized them: the 2025-11 architecture was careful and stillborn
(orchestrator/sub-compiler graph/SourceMap/CuesCompiler never wired); the 2026 trunk is
well-implemented at the leaves (fail-loud, real provenance, ~5k test lines) but
unarchitected at the orchestration layer (self-disagreeing stage numbering, discarded
typed bundles, triplicated validations, fragmented error taxonomy, ghost diagnostics
citing `drive_as_code.yaml`). Biggest debt = the triple declaration-surface config
model — the same defect the VFS audit found from the authoring side.

## The calls

1. **Target shape adopted as intent**: a declaration-store compiler — discovery/merge
   front end with per-declaration file:line provenance, one symbol table, typed
   declaration-family compilers, mechanical emission; the Strata/UAC/BAC trio mirrored
   in the artifact and hash tree, NOT as three monolithic sub-compilers. PDR-0117 and
   the variable-surface unification are one unit, after the token cut.
2. **Explicitly not worth building**: the three-tier orchestrator, the sub-compiler
   graph engine, incremental compilation.
3. **Buys 1+2 executed now, owner-directed**, in an ISOLATED WORKTREE so the L2
   baseline freeze (no src edits until all seeds trained AND evaled) holds on the main
   tree. Yolo-limiter: compiled hashes byte-identical across all five levels (verified:
   90-line before/after diff empty), suite 2650 green, mypy clean, matrix exit 0 both
   modes. Landed on the branch: ~500 lines of dead seams deleted, stage enum,
   error-code registry (ghost diagnostics fixed), SourceMap wired for file:line
   diagnostics. Parked for the declaration-store unit: real DAC modifier-source check,
   real economics metadata, SourceMap coverage for remaining raise-site families.
4. **Landing gate**: after the final baseline eval — rebase onto tip, re-run the full
   gate set on the rebased branch, then merge to `project-recovery-2`.

## Reversal trigger

If the post-rebase gate re-run shows any hash movement or matrix divergence, the branch
does NOT land; the offending commit is dropped or reworked and the parked-items list
grows — the baseline record's validity is never traded for cleanup.
