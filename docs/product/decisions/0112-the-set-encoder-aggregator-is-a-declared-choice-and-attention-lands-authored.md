# PDR-0112 — The set-encoder aggregator is a DECLARED choice, and attention lands authored in config

Date: 2026-08-22   Status: **accepted** (within grant; the design fork was put to the owner
in-session and they chose the recommended branch)
Author: Claude (standing product owner)
Owner sign-off: the unit itself was pre-authorized (`PDR-0109`: "the aggregator upgrade is
schedulable directly") and the owner directed "proceed with phase B" at this session's
resume; the declared-vs-replace design fork was answered explicitly ("Declared choice").
Related: `PDR-0109` (pre-authorization + the reversal trigger this checks), `PDR-0027`
(the level-override mechanism this dogfoods), `PDR-0017` (cost basis), `PDR-0108` (scope),
`PDR-0045` (declare-don't-hardcode)
Tracker: `hamlet-fa6bb6da4a` (comment 215) · Commit: `ba2766e6`

## Context

`PDR-0109` scheduled Phase B unit 1 as "aggregator upgrade (mean-pool → self-attention)".
That wording admits two readings: replace the aggregator inside the engine, or make the
aggregator an authorable choice. The first is less code; the second is what this product
says it is — behaviour that varies must come from a declared parameter, never an engine
fact (`PDR-0045`), and BAC's whole premise is that the mind is config.

## The call

**The aggregator is declared.** `SetEncoderConfig` gains a **required** `aggregator` block
(No-Defaults — the existing pack broke loudly and was updated):

- `{type: mean}` — the proven masked mean-pool (DeepSets), now declared instead of implied;
- `{type: attention, num_heads: N}` — self-attention over the embedded token rows (empty
  rows excluded via key-padding mask), then the same masked mean-pool. `token_embed_dim`
  must divide by `num_heads` at parse; all-empty token sets stay finite on both paths.
  Permutation invariance — the set property `PDR-0109`'s proof pinned — holds on both
  aggregators and is asserted by test.

The attention option is **authored in a committed pack** per `PDR-0007`'s definition of
done: `configs/test/set_encoder_smoke` gains level `L1_attention`, whose **level-override
`brain.yaml`** declares attention — the first real use of the `PDR-0027` override mechanism
carrying a genuinely different mind, with `brain_forked` asserted true.

## Acceptance evidence (ACCEPT ran against this)

Built TDD, each layer watched red before green. 10 new unit tests (config validation,
network behaviour, factory threading), 3 pack tests, 3 integration proofs
(config-in/behaviour-out: the declaration changes the built module; declared `num_heads`
respected; gradients reach the attention weights). 607 affected unit tests + 7 integration
green; `mypy` clean; `python -m townlet.universe validate --primary-level L1_attention`
passes.

**`PDR-0109`'s first reversal trigger did NOT fire**: attention required no new plumbing —
the same slice → embed → mask → pool path, one module inserted between embed and pool. The
"aggregator upgrade, not a new build" cost basis held.

## Consequences

- The remaining `hamlet-fa6bb6da4a` scope is Phase B unit 2 onward: **token representation
  of the full observation** (the migration proper and its design document), then
  relational/message exposure as tokens (discharges `PDR-0107`), then dynamic variables
  (`hamlet-424adcb84f`).
- Mind-authoring (BAC) Layer 2 widens again: architecture per level (`PDR-0027`), the token
  path proven (`PDR-0109`), and now the aggregation strategy — all authorable. The BAC
  count stays 1 of 3 (Layers 1/3 unbuilt).

## Reversal trigger

Reopen if:

- **training** (not just forward/backward) fails on the attention path — inherits
  `PDR-0109`'s second trigger onto the new aggregator;
- the full-observation token design (unit 2) needs an aggregation shape this block cannot
  express — then the `aggregator` schema is re-shaped by a superseding PDR, not patched
  silently;
- a shipped pack is found declaring `attention` whose behaviour is indistinguishable from
  `mean` at equal weights — that would mean the declaration went inert, the failure mode
  this project treats as debt.
