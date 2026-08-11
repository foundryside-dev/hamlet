# PDR-0018 — The config packs are test infrastructure, never an authored curriculum; two escalations are corrected and a larger one is raised

Date: 2026-08-12   Status: accepted (with one **proposed** item requiring owner sign-off — see §Escalation raised)
Author: Claude (standing product owner)
Owner sign-off: the **correction** is the owner's, stated directly: *"don't assume the packs were 'particularly tuned', we were still landing large blocks of core systems, nothing was final at all, it was test infrastructure not calibration."*
Related: PDR-0015 (bounds scope; its reversal trigger), PDR-0016 (bounds + normalization), PDR-0006 (strangler/oracle), PDR-0009 (per-level architecture gap)
Corrects: two of the three escalations raised at the 2026-08-11 checkpoint (`074471c0`)

## Context

The 2026-08-11 checkpoint escalated three questions. Two rested on a premise the owner has now
denied: that the curriculum packs were *tuned*, and that task 3's measured 35–58% drop in
completing interactions therefore threatened a calibrated artifact.

The premise was mine, not the owner's, and it was never checked. Checking it turns out to be
one `diff` away.

## What the configs actually say (measured 2026-08-12)

Levels live under `configs/default_curriculum/levels/`. Across `L0_0_minimal`,
`L0_5_dual_resource`, `L1_full_observability`, `L2_partial_observability`, `L3_temporal_mechanics`:

- **`bars.yaml`, `affordances.yaml` and `drive.yaml` are byte-identical in all five.**
- **Grid size is 8×8 for every level**, set once in pack-level `stratum.yaml`, with no per-level
  override path. The documented 3×3 and 7×7 grids do not exist.
- **`L0_5_dual_resource/training.yaml` and `L1_full_observability/training.yaml` are identical
  except `output_subdir`.** The two levels are the same experiment under two names.
- **`L0_0` vs `L0_5` `curriculum.yaml` differ only in comments.** The settings —
  `active_vision: global`, `vision_range: 0.5`, `active_temporal: false`, `day_length: null` —
  are the same.
- Only **L2** (`active_vision: partial`) and **L3** (`active_temporal: true`, `day_length: 24`)
  differ in any universe-defining way.

**Five documented curriculum levels are three distinct universes**, and the differences between
the first three are training hyperparameters, not universe definition. That is exactly the shape
of test infrastructure: one universe, several harness configurations. The owner's account is
corroborated, and is stronger than stated — the packs are not merely uncalibrated, they are
largely undifferentiated.

## The call

**Accept the correction and re-derive the three escalations from it.**

### 1. "Who re-authors the packs?" — no longer blocked-on-owner; filed as downstream work

Reframed, not withdrawn. The owner removed the *premise* (that tuning existed to protect); the
*question* survives in a better form, because the measurement above shows there is no authored
curriculum to re-author — there is one to **author, for the first time**.

That is a build task, not a repair decision, and it is downstream of the engine being honest
about its own config. It stops gating WS-1 and stops sitting in `current-state.md` awaiting a
reply. Filed to WS-4 so the next session does not read "resolved" and drop it.

**Consequence for task 3a**: the fear that reviving the money economy would damage a tuned
curriculum is void. 3a proceeds without that hesitation.

### 2. "The Low Energy Delirium teaching claim is now unverified" — misattributed; corrected

I reported `30c433e3` as having broken this claim. **That was wrong, and the error was mine.**
The claim was never true of the shipped configs. It requires `L0_0_minimal` to declare a
`multiplicative` extrinsic and `L0_5_dual_resource` to declare
`constant_base_with_shaped_bonus`; in fact **both declare `constant_base_with_shaped_bonus`,
from byte-identical files**, and no shipped level declares a `multiplicative` extrinsic at all.

This is a documentation-truth defect of long standing, not a regression introduced this month.

### 3. "When do we stop adding to WS-1 and freeze?" — unchanged, but the argument moves toward freezing sooner

The correction removes the largest reason to slow down. There is no calibrated behaviour at risk,
so behaviour-shift measurements should not be treated as regression gates. Still the owner's call.

## Escalation raised (this is the larger one — **proposed**, awaiting sign-off)

`vision.md:94` describes Low Energy Delirium as *"the flagship demonstrator of the substrate: the
proof that the thing works."* `vision.md:192` makes preserving such artefacts a stated principle.

**The flagship demonstrator is not implemented in any shipped config.** `vision.md` is ENDORSED
and is not touched here — that is the authority boundary. But this is strictly bigger than the
escalation it replaces, and it is recorded as a question for the owner rather than resolved.

Trading a soft escalation for a hard one is the honest outcome of this correction. It should not
be presented as net de-escalation.

## Rationale

Two things are worth separating, because the correction makes it easy to overshoot.

**"Test infrastructure, not calibration" does not make the 3a measurements pointless.** They are
not a regression gate — nothing was calibrated, so nothing regressed. They remain the way we
learn what the engine does when a declared surface is wired, which is the whole method of this
recovery. The measurement keeps its evidentiary value and loses only its veto.

**The failure mode this exposes is my own.** I inferred "tuned" from the existence of five
named levels with distinct documented purposes, and escalated on that inference without running
the diff that would have refuted it in one command. This is the same lesson recorded three times
already — *grep finds the shape of a call, not the set of places a value is produced* — in a new
costume: **a name is not evidence of the thing it names.** Five directories named for five
pedagogical stages contained three universes. Before escalating on a property of an artifact,
verify the artifact has it.

## Consequences

- **`PDR-0015`'s reversal trigger stands unchanged.** It already reads *"the economy was never
  actually tested at its declared values"* — the correction strengthens its rationale rather
  than tripping it.
- **`PDR-0016`'s CLAUDE.md commitment was not honoured, and is honoured now.** That PDR listed
  correcting CLAUDE.md's false claims as part of task 3a's work; `30c433e3` and `9a6de69e`
  did not touch the file. An acceptance gap in my own prior unit, closed in this commit — four
  sites corrected, three of them newly proven false here.
- **The five shipped levels are a thin coverage set for WS-3's differential harness.** Three
  distinct universes will not exercise much of the design space. This does **not** reopen
  `PDR-0006` — the compiled-universe contract remains the seam — but it is an input to WS-3's
  scoping, recorded as an open question rather than designed here.
- **Documentation truth moved again** — three further CLAUDE.md claims proven false
  (the L0_0 grid/affordance count, the delirium contrast, five-differentiated-levels).

## Reversal trigger

Reopen if **any** of the following:

- **The owner intends the packs as the curriculum** rather than as harness configuration. Then
  authoring is not downstream work but a gap in the current product, and its priority changes.
- **A level-differentiating mechanism turns out to exist and be unused** — e.g. per-level
  `stratum.yaml` overrides are supported but unauthored. Then this is one more inert declared
  surface (`PDR-0007`) and belongs in WS-1's ledger, not WS-4's backlog.
- **The oracle freeze is scoped to pack behaviour rather than the compiled-universe contract.**
  Freezing three universes as the reference would encode scaffolding as requirement, which is
  the failure `PDR-0006`'s precondition 2 exists to prevent.
