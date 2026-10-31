# PDR-0015 — Second review: the bounds scope was an undercount, the architecture half re-sequences to WS-4, and the dependency spec is brought back to reality

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)
Owner sign-off: **yes, on the bounds fork** — *"Source the existing sites now, file the phase for WS-4"*, followed by *"the original 'game engine' needs to be strangled out by the engine engine"* and *"VFS and the other dynamic engine parts are the guiding star here, not 'health = 0,100"*. Dependency cleanup requested directly: *"please take a second to bring all our dependencies up to a current spec"*.
Related: PDR-0014 (amended here, not superseded), PDR-0006 (oracle freeze), PDR-0007 (options not yet enabled), PDR-0012 (no tech debt), metrics.md (Config-surface coverage)
Plan: `docs/zzz. archive/plans/2026-08-11-ws1-fix-set.md` §0.1 · tracker `hamlet-67ffbd282a`, `hamlet-f46e2b381a`, `hamlet-88acec4bb5`

## Context

`PDR-0014` resolved three blockers and directed that the plan be re-reviewed once its
amendments landed. It was, by five lenses with adversarial verification. Verdict:
**APPROVED_WITH_AMENDMENTS** — nine surviving blockers, all mechanically applicable edits,
no open design decision.

The review confirmed `PDR-0014`'s direction and **corrected its arithmetic**.

## The call

**1. `PDR-0014` B3's site list was an undercount, and the omitted site is the only one that
binds.** There are **seven** hardcoded `(0.0, 1.0)` sites in **two** mechanisms — four
runtime meter clamps and three compile-time clamp specs fed to the VTC kernels — of which
six are meter bounds. Measured on L1: `money := 22.5`, one step → `1.0`; widen only
`vfs/vtc.py:2384` (passive depletion) → `22.5`; wire only B3's four sites → **still `1.0`**.
`apply_instant_interaction` has *zero production callers* until task 3 lands, and the live
path `apply_interaction` has no clamp at all. Implementing `PDR-0014` literally would have
certified bounds "wired" while `bounds.max: 999999.0` stayed contradicted every tick.

**2. `PDR-0014`'s acceptance test does not compile.** `MeterConfig.validate_initial_in_bounds`
rejects `initial: 1.0` against `bounds.max: 0.5`, and the correct post-`step` literal is
`0.490000`, not `0.5` — the ceiling minus the passive tick that runs after the interaction.
Restated in task 3a.

**3. The architecture half re-sequences to WS-4, per `PDR-0014`'s own reversal trigger 2.**
The HLD says clamp ranges are *"instance-specific"* (`09-affordance-semantics.md:388`, naming
`machinery_stress` as the counterexample bar) and the VFS docs say VTC owns clamps via a
scheduled `clamp_and_validate` phase. That phase appears **exactly once in the codebase** —
as a string in `DEFAULT_TRANSITION_PHASES`. It is declared and empty. WS-1 does the debt half
(source the existing sites from `bars.*.bounds`); `hamlet-f46e2b381a` owns the architecture
half. Owner chose this split explicitly to avoid delaying the oracle freeze.

**4. The declared dependency spec is brought back to reality.** Thirteen runtime
dependencies had zero references anywhere in the repo, including `tensorflow` — declared
**twice** — which dragged a duplicate `nvidia-cudnn-cu12` stack alongside torch's `cu13`.
Floors were fiction (`ruff>=0.0.280` against 0.15.12 running; `mypy>=1.4.0` against 2.1.0).
Both are now honest. The two deliberate caps (`torch<2.12` for the triton 3.7.0 segfault,
`pytest<9`) are **kept and annotated**, not lifted blind.

## Rationale

The bounds correction matters beyond its own scope because of *how* it was wrong. `PDR-0014`
counted with `grep torch.clamp(` and therefore could not see the compile-time tuple literals
that actually govern the meter. A fix built on that count would have shipped green tests, a
commit message claiming bounds were wired, and a runtime where the shipped economy stayed
dead. That is the precise failure mode `PDR-0007` exists to prevent — a declarative surface
certified as working while the runtime contradicts it — reproduced *inside the fix for it*.
The lesson is recorded because it will recur: **count enforcement points by what the value
meets at runtime, not by the shape of the call that sets it.**

The dependency work turned out to be load-bearing rather than hygiene. The duplicate CUDA
stack was not merely bloat: removing it and repairing `nvidia-cudnn-cu13` **restored CUDA on
this machine**, which had been failing with `nvrtc: failed to open libnvrtc-builtins.so.13.0`
and was recorded in `current-state.md` as blocking GPU determinism verification. It also
retires a caveat the review itself had written — that 37 tests need `CUDA_VISIBLE_DEVICES=""`
to pass. That is now false.

`tensorflow` also illustrates the owner's framing directly. It was not a dependency anyone
chose and kept; it was one nobody noticed, satisfying nothing, costing 349 MB and a broken
GPU. Under `PDR-0012` an unused dependency is debt in exactly the same way an unread config
field is.

## Consequences

- **WS-1 grows from seven units to nine**: task 3a (bounds wiring) and sibling 3b
  (dead agents stop transacting), both specified in the plan's §0.1.
- **`transition_graph_hash` and `vfs_hash` move for every pack** when 3a lands, because
  `clamp` is part of `_canonical_transition_rule`. Zero cost under `PDR-0011`. **No
  re-stamping, no compatibility branch.**
- **The shipped L1 economy comes alive.** WORK's `+22.5` persists; six of seven money
  affordances move from permanently unaffordable to affordable; `money` enters the
  observation vector unnormalized, which is a real training-signal change and must be stated
  rather than papered over. CLAUDE.md's *"Job payment = $22.5, sustainable with proper
  cycles"* becomes true for the first time.
- **Dev setup now requires two extras.** `mypy src/townlet` type-checks
  `src/townlet/recording/`, whose imports were reaching the environment only transitively
  through `mlflow`. Documented in CLAUDE.md.
- **The plan's source-of-record citations resolve.** They pointed at a `scratchpad/`
  directory that has never existed in the repo; the files are committed under
  `docs/plans/2026-08-11-ws1-pinning-test-sources/`.

## Reversal trigger

Reopen if **any** of the following:

- **Wiring `bars.*.bounds` requires branching on a bar name.** Unchanged from `PDR-0014`:
  presumptively *no*, and it escalates as a grammar question. The specified shape — two
  vectorized `[meter_count]` tensors — does not trip this.
- **The revived money economy destabilises the curriculum.** Six affordances becoming
  affordable is a large behaviour change immediately before the freeze. If L1 training
  collapses, the *fix* is not to re-cap money; it is to re-author the pack, because the
  economy was never actually tested at its declared values. Escalates as a curriculum
  question.
- **Lifting a dependency cap is attempted without a full-suite run.** Both caps are
  annotated with what must be verified first. `torch<2.12` in particular guards a segfault
  that only reproduces under pytest's native-extension load order, so a bare
  `python -c "import torch"` is **not** evidence.
