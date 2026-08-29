# PDR-0114 — The full-observation token design is APPROVED, with the no-tech-debt rider and the trial-pack disposition ruling

Date: 2026-08-22   Status: **accepted** (every fork below was put to the owner in-session
and answered explicitly; the final revision was approved with "yes, remember our project
has a no techdebt policy so that applies across the board")
Author: Claude (standing product owner)
Related: `PDR-0108` (tokenisation in scope), `PDR-0109`/`PDR-0112` (Phase B units this
design is unit 2 of), `PDR-0044` (compiled-block escalation triggers), `PDR-0107`
(relational exposure waits for tokens), `PDR-0045` (declare-don't-hardcode),
`PDR-0012`/`PDR-0013` (the no-tech-debt policy the rider applies)
Tracker: `hamlet-fa6bb6da4a` · Spec: `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` (Status: APPROVED, committed `c73f729a`)

## Context

Phase B unit 2 — "the migration proper and the big design document": how the fixed-width
superset+mask observation ABI becomes a token representation. Designed interactively with
the owner, then hardened through two four-lens subagent review rounds (systems / solution
architecture / PyTorch / DRL; round 2 paired the design against VFS-as-built and widened
to VFS-standalone findings on the owner's instruction).

## The owner's rulings (each answered explicitly in-session)

1. **Transfer contract: cross-universe by token type.** Checkpoints transfer where token
   types match; per-type encoders are the transferable unit.
2. **Token identity: declared payload.** A token is what its declared parameters say —
   recursive payload-signature identity, with a compile-time indistinguishability check.
3. **Non-token architectures ride a flat view derived from tokens** (serialization of the
   token rows in canonical TokenSpec order), not a parallel pipeline.
4. **Spatial: per-entity tokens.** The raster dies; POMDP becomes a visibility filter.
   This resolves `PDR-0044` trigger 3 for the raster/grid block (it dissolves into entity
   tokens); the trigger stays armed for walls/zone structure and the dyadic relation shape.
5. **Realization: approach C** (token rows serialized into the flat tensor), with
   approach A (typed dict-of-streams transport) captured as `hamlet-c586d520b2` (P4),
   extractable later behind the TokenSpec — "C but capture A as a P4 task".
6. **No hardcoded temporality.** No `world` token type; the engine publishes ONE primitive
   (the tick) as an engine-written VFS variable; day/night/phase are authored expressions.
   Round 2 found this machinery did not exist and rescoped migration unit 2 as a BUILD.

## The no-tech-debt rider (owner-directed)

Every finding from both review rounds — including the 13 VFS-standalone tickets round 2
filed — carries a **named discharge vehicle** (a migration unit, WS-4, or standalone
scheduling); nothing is parked as debt. The vehicle table is in the spec's header and the
round-2 section.

## The trial-pack disposition ruling (owner-adopted)

`trial_b_blind_organism` breaches reversal trigger 3 immediately if migrated (≈10–25×,
two lenses independently). Ruling: the retired corpus's trial packs resolve on their
existing **2026-10-06 disposition clock before migration unit 5**; the inert-guard is
satisfied by purpose-built or promoted packs; trigger 3 is evaluated only on packs that
survive disposition. A retired-corpus artifact does not force-promote approach A.

## Reversal triggers (armed; restated from the spec §"Reversal triggers")

1. **POMDP learnability:** token-feedforward AND token-recurrent (both aggregators) fail
   to reach ≥ 80% of the unit-3 frozen L2 baseline's final greedy survival within the same
   env-step budget (seed-level IQM, non-overlapping CIs) → reopen the spatial
   representation (payload or learned position encoding, not a raster revival).
2. **A surface emerges with no natural token form** (`PDR-0044` trigger 3 stays armed;
   pre-registered candidates: walls/obstacle/zone structure, dyadic relations).
3. **Capacity/padding bites with numbers:** a shipped pack's serialization exceeds 8× its
   pre-cut allocated width (post-disposition, post-explicit-exposure), or observation
   encoding exceeds 25% of clone-audited `env.step` wall time, or recurrent-attention
   memory forces `batch_size` below declared.
4. **Payload-identical entities prove indistinguishable in practice** despite the
   descriptor block (the flat-vs-token A/B in §6 is the instrument).
