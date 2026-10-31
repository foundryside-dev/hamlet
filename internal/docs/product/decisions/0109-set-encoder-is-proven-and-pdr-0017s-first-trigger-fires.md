# PDR-0109 — `set_encoder` is proven config-in/behaviour-out, and PDR-0017's first trigger fires

Date: 2026-08-22   Status: **accepted** (within grant — adjudicates a pre-registered outcome
gate against measured evidence; the escalation branch did not fire)
Author: Claude (standing product owner)
Owner sign-off: not required — PDR-0017 pre-committed both branches; this records which one
the evidence took. The direction executed here is the owner's (`PDR-0044`, `PDR-0108`).
Related: `PDR-0017` (the sequencing this discharges), `PDR-0044` (authority), `PDR-0027`
(brain override, landed this session), `PDR-0107` (relational exposure waiting on this path),
`PDR-0108` (the scope decision)
Tracker: `hamlet-fa6bb6da4a` (first unit complete; migration proper is the remaining scope),
`hamlet-0d0115383e` (closed this session)

## Context

PDR-0017 ruled that the first unit of the token-observation direction is not the transformer
— it is a config-in/behaviour-out test proving `architecture.type: set_encoder` runs at all,
because an unexercised code path in this codebase is not presumptively working (six
declarative features shipped inert as the base rate). It pre-committed two outcomes: works →
"the first unit collapses to a formality and the transformer step can be scheduled directly"
(trigger 1); broken → a repair-or-replace design fork that escalates to the owner
(trigger 2).

The unit ran today (Phase A plan, tasks 3–4), on the first pack ever to drive the path:
`configs/test/set_encoder_smoke`, whose agent-profile `tensor2d [4,3]` variable compiles to
the 12-dim token field the network slices.

## The evidence

`tests/test_townlet/integration/test_set_encoder_runtime.py`, green on first run, four
assertions with teeth:

1. **Built from config**: the compiled pack produces a `SetEncoderQNetwork` with the declared
   token geometry, its slice matching the compiled observation field.
2. **Tokens reach the network and change its output**: a registry write to `need_tokens`
   flows through the observation and moves the Q-values.
3. **The slice is a SET, not a flat vector**: permuting token rows leaves Q-values identical
   (mean-pool permutation invariance) — the property a flat feedforward consumer could not
   show.
4. **Gradients reach the token encoder** — the path trains, not merely evaluates.

Two real defects were flushed out on the way, neither in the token path itself: the profile
compiler crashed on `initial_value_mode` (a DTO-blessed init source it never implemented —
fixed), and a stale never-loaded `levels/*/brain.yaml` stub in `items_smoke` (deleted,
registered as DIV-007).

## The call

**PDR-0017 trigger 1 fires.** The token path is real. Consequently:

- `hamlet-fa6bb6da4a`'s remaining scope is the migration proper, and its next unit — the
  **aggregator upgrade** (mean-pool → self-attention) — is schedulable directly, per
  PDR-0017's own wording.
- Phase B of the pivot proceeds under `PDR-0108`: aggregator upgrade → token representation
  of the full observation → relational/message exposure as tokens (which will discharge
  `PDR-0107` via its third trigger) → dynamic variables (`hamlet-424adcb84f`).
- The escalation branch (`PDR-0017` trigger 2, `PDR-0044` trigger 2) is dead — nothing to
  escalate.

## Consequences

- The MLP→LSTM curriculum progression is now *expressible* in config (PDR-0027's metric
  path): a level can carry its own complete `brain.yaml`. Authoring a recurrent pack remains
  future content work.
- Filed at execution per the Phase A plan: `SetEncoderConfig.token_field_name` resolves only
  at network-build time, not compile time — the PDR-0052 shape (underspecification should be
  a compile error). Tracked in filigree.
- The Phase A plan is fully executed; its checkboxes stand as the record.

## Reversal trigger

Reopen if **any** of the following:

- **The aggregator upgrade shows the DeepSets proof did not generalize** — attention needs
  materially different plumbing than mean-pool replacement. Then PDR-0017's cost basis ("an
  aggregator upgrade, not a new build") was wrong and the migration is re-scoped.
- **Training (not just forward/backward) fails on the token path** — the proof exercised
  build/forward/gradient, not a full training run. A training-loop defect specific to
  `set_encoder` reopens the "is the path whole?" question at the loop, not the network.
- **The full-observation token design cannot express a compiled block** (e.g. the grid
  encoding has no natural token form) — already `PDR-0044`'s third trigger; it fires on the
  design work, not on this proof.
