# PDR-0006 — Recovery strategy is a strangler rewrite behind the compiled-universe contract, with the frozen system as oracle

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: yes (owner chose the strategy directly)
Supersedes: the "REPAIR in place" execution model implied by PDR-0004; PDR-0004's *dispositions* and evidence stand
Amends: PDR-0005 (its plan-archaeology claim is downgraded — see §Correction)
Related: PDR-0002, PDR-0003, metrics.md (Trial 001), assessments/2026-08-11-maturity-assessment.md

## Context

`PDR-0004` adopted REPAIR for all eight subsystems. The owner challenged that conclusion on solid
grounds: at 45,274 LOC, a full rebuild is *"a few days of hard burn from a far more capable model
than we had at the time."*

Two admissions reshaped the question.

**First, the assessment's instrument was biased.** The workflow instructed verification agents to
*"REFUTE this disposition… Default to REFUTING unless the evidence is overwhelming"* and warned
assessors that REBUILD/DELETE *"will be adversarially challenged."* That is a one-way ratchet
toward REPAIR. The unanimity reported in `PDR-0004` is partly an artifact of prompt design, and
was cited there as if it were purely evidential. The dimension-score variance and the 81 named
keep-worthy items remain real; the *unanimity* should not have been offered as independent
corroboration.

**Second, the specification is as spotty as the code.** The owner: *"the spec has the same
spottiness as the code just on a smaller scale."* This defeats the recovery plan `PDR-0005` leaned
on. Code gaps and spec gaps are **correlated, not independent** — they share a cause, so the run
sheets are silent exactly where the code is missing. Plan-archaeology finds accidental drops and
deliberate cuts (both leave a written trace); it is structurally blind to *never-specified-at-all*,
and that blindness is indistinguishable from "nothing missing here." `TASK-009` validated the
method only on the case where the spec existed.

That left an apparent impasse: repair-in-place inherits a shape built for a 32k context window,
while rebuild discards the only *complete* artifact (the code) in favour of an incomplete one
(the spec).

## Options considered

1. **REPAIR in place, per PDR-0004** — pro: no work lost; incremental. Con: inherits the structure
   that a since-expired constraint produced; wires the declarative/runtime join piecemeal across 8
   subsystems when the join is a single architectural problem.
2. **Full greenfield rebuild** — pro: 45k LOC is genuinely small now; the thesis is far clearer
   than when the code was written. Con: with a spotty spec you are inventing, not reconstructing;
   ~81 items of discovered knowledge (bug fixes carrying comments explaining the real bug, the
   strict-float regex, the closure-factory avoiding late-binding, the all-actions-invalid row
   guard) get silently re-bought at full price.
3. **Strangler rewrite behind the compiled-universe contract** — freeze the current system as an
   oracle, then knock down and rebuild one subsystem at a time against it, keeping the provenance
   spine and re-earning the rest through a differential harness.

## The call

**Option 3**, chosen by the owner: *"effectively a strangle rewrite rather than refactor — freeze
everything and then knockdown rebuild a subsystem."*

The seam is the **compiled-universe contract**: a frozen, content-addressed `CompiledUniverse` in,
tensors out. `metrics.md` Trial 001 demonstrated that surface is real and exercisable — a 6-D
universe compiled, reset, and stepped with zero `src/townlet/` changes.

### Why this beats both alternatives

**The oracle dissolves the specification bottleneck for preserved behaviour.** This is the
decisive property. For everything being kept, you do not need a written spec — the frozen system
*is* the spec, consulted mechanically. Specification effort collapses onto genuinely **new**
surface (the authorability ledger, BAC Layers 1 and 3), which is a far smaller and more tractable
artifact than a whole-system spec. The spottiness problem is not solved; it is **routed around**.

**It defuses the strongest objection to rebuilding.** The concern that hard-won fixes get silently
re-bought is answered structurally rather than by vigilance: if a rebuilt subsystem reintroduces
the late-binding closure bug or drops the all-actions-invalid guard, the differential harness
fires. Discovered knowledge is protected by a mechanism instead of by whoever remembers it.

**It preserves the best asset while replacing the weakest.** The assessment named the compiled-
universe pipeline with real provenance as the single biggest asset — an 8-stage compiler emitting a
frozen msgpack artifact keyed on config hash + compiler version + git SHA + library versions, with
schema-version checks on load. That spine is kept and becomes the strangler's load-bearing
structure. The declarative/runtime *join* — the actual defect — is what gets rebuilt.

**It makes the rebuild/repair question per-subsystem and empirical** rather than a single
up-front bet, and it is reversible at every step: a knockdown that goes badly is abandoned against
a still-frozen oracle.

## Preconditions (these gate the strategy, and one may invalidate it)

1. **Determinism — VERIFIED SATISFIABLE, but not currently exposed (tested 2026-08-11).**
   The strategy stands. Two runs of `configs/default_curriculum` over the same compiled universe
   with the same action sequence produce **bit-identical 40-step trace hashes** — *provided* torch,
   `random`, and `numpy` are all seeded. Recompiling per run is not a confound (verified
   deterministic). CPU only; GPU float nondeterminism and the `vtc_kernels.py` TorchScript-JIT
   dependency remain untested.

   **But there is no single seeding door.** Seeding only torch diverges. `vectorized_env.py:1441`
   calls `random.shuffle` off the global Python RNG, and `grep` over `src/` and `scripts/` finds
   **no seeding entry point at all** — one local generator in `effects/executor.py:322` is the sole
   hit. Filed as `hamlet-834108b55a`. This is a product defect independent of the strategy: the
   provenance spine hashes the experiment's *input* seven ways but cannot reproduce its
   *execution*, which undercuts the HLD's governance claims of tick-level proof and checkpoint
   replay. Fixing it is the first task of WS-7 and cheap.
2. **The oracle must be correct before it is frozen.** `WS-1`'s defects — the compile cache not
   keyed on `primary_level`, and the recurrent path training memoryless — must be fixed first, or
   explicitly entered in a **known-divergences register** as behaviour the rebuild is *expected*
   to differ on. Freezing a bug makes it a requirement.
2b. **The knockdown unit is a *design-space* unit, not necessarily a dependency subsystem.**
   The owner: *"we can expand that within the design space too — 'we freeze everything but the
   terrain generator and build it out properly', then do the same for the compiler."* This is a
   better framing than the assessment's SG1–SG8 partition, which was drawn for *analysis* (who
   owns which files) rather than for *replacement* (what can be rebuilt as a coherent whole).
   A knockdown unit is any slice with a definable contract at its edge — the terrain/substrate
   generator, the observation encoder, the reward pipeline, the action-write path — regardless of
   whether it maps to one package.

   **This pattern already has a proven precedent in this codebase.** The owner ran exactly this
   operation on the compiler a few weeks ago as a side task
   (`docs/plans/2026-05-15-compiler-cleanup-modernization.md`, with a `.review.json`). That is
   evidence the approach works *here*, not merely in principle, and the assessment independently
   scored the compiler as the project's single biggest asset — consistent with it having already
   received the treatment. **Mine that plan for the knockdown playbook** rather than inventing one:
   it is the closest thing to a worked example of the strategy this project has.

3. **Seams must exist at subsystem boundaries.** A strangler needs swappable units. Components are
   currently env-owned and circular-deps-wired in place. **`hamlet-030f2ce0aa` (EnvFactory) is
   therefore promoted from P3 to a strategic precondition** — it is the seam-cutting work. This
   reverses its earlier framing in `roadmap.md`, which set it aside as serving changeability rather
   than authorability; under a strangler, changeability *is* the enabling constraint.
4. **A freeze protocol.** Tag the oracle reference; no feature work on frozen subsystems; all
   intended behavioural differences recorded in the known-divergences register rather than
   discovered by a failing diff.

## Consequences for the work streams

- **WS-3 changes character and grows in value** — from hand-written config-in/behaviour-out
  assertions to a **differential harness**. Stronger, and largely self-writing: it need not know
  the right answer, only that old and new agree. It becomes the central artifact of the program.
- **WS-1 is promoted** — it now gates the freeze rather than merely preceding the harness.
- **WS-6 is demoted and re-scoped** — no longer "recover the specification" (it cannot), but a
  narrower two-part job: find the accidental drops still worth wanting, and inventory what exists
  so nothing good vanishes silently. The oracle now carries the preservation burden.
- **WS-2 (deletion) is largely subsumed** — under knockdown, dead code is not deleted so much as
  not rebuilt. The salvage-on-paper requirement stands.
- **WS-4 becomes the spec-writing work**, confined to genuinely new surface.
- **WS-5 trails everything**, unchanged in kind.
- **A new stream is implied — WS-7: freeze and oracle infrastructure.** Determinism verification,
  oracle tagging, differential harness scaffolding, known-divergences register, seam cutting.
  It gates every knockdown.

## Correction to PDR-0005

`PDR-0005`'s cause-based triage table and its **wire-not-delete** default stand. Its claim that the
run sheets constitute *"much of the specification the assessment found missing"* **overclaims** and
is corrected here: the plans share the code's gap structure and are silent on never-specified
surface. Their remaining value is narrower — finding accidental drops, and dating artifacts by
tooling stratum.

## Reversal trigger

Reopen this PDR if **any** of the following:

- **Determinism cannot be established** well enough for old/new comparison to be trustworthy.
  This is the precondition most likely to fail, and it invalidates the strategy rather than
  delaying it — fall back to full greenfield against a written spec, accepting the re-buy cost.
- The first knockdown costs materially more than repairing that subsystem would have. One data
  point is enough to re-evaluate; the strategy's whole claim is that knockdown is cheaper than
  untangling.
- Seam-cutting (`hamlet-030f2ce0aa`) proves harder than the knockdowns it enables — the coupling
  would then be the real problem, and the honest move is a whole-runtime rebuild rather than
  subsystem-at-a-time.
- The known-divergences register grows large enough that the oracle no longer constrains much.
  At that point the rebuild is greenfield in all but name and should be called that.
