# PDR-0135 — Affordance and effect identity is executable behaviour

Date: 2026-08-31   Status: **accepted** (engineering reconciliation within the standing grant)
Author: Codex (standing product owner)
Related: `PDR-0131`, `PDR-0132`, `PDR-0134`, `hamlet-1e335e0363`

## Context

Restoring meter identity exposed a larger engineering defect in the same compiled boundary. An
affordance token identified a small subset of its authored writes while omitting duration,
opening hours, costs, lifecycle stage, write source and most spawned-effect behaviour. Distinct
executable behaviours could therefore be identical to the network.

The authoring surface also described behaviour the runtime did not execute. `dual` did not run an
instant and a multi-tick interaction: it followed the multi-tick branch while active and the
instant branch otherwise. Effect definitions declared scope and intensity, but the executor
hard-coded agent scope and definition intensity was unused. The manager did not tick and despawn
every declared scope consistently.

There is no scientific-audience requirement to defend a convenient abstraction. The engineering
requirement is stricter and simpler: every admitted declaration must select one reachable runtime
behaviour, and every behaviour distinction that matters at execution must survive compilation
into the model-visible identity.

## The call

Interaction type is exactly `instant | multi_tick`:

- `instant` has no duration and may execute immediate `costs` and `on_start` writes;
- `multi_tick` requires a positive duration and may execute `costs_per_tick`, `per_tick` and
  `on_completion` writes; and
- fields belonging to the other member, and lifecycle buckets with no executable route, are
  rejected rather than stored inertly.

`dual` is deleted from DTOs, configs, examples, runtime branches and ordinary tests. It has no
alias, warning, migration reader or replacement spelling.

Each compiled affordance slot carries the executable identity of its declaration: interaction
type, duration applicability and value, the exact 24-hour availability mask, lifecycle stage,
write source, target class, command form, bounded magnitude/sign, target-meter identity, costs and
per-tick costs. The fixed summary capacity is five entries: a census of all 251 affordances in the
34 positive packs found a global maximum of five, reached by `BID_HIGH` and `BID_LOW` in
`trial_o_bidding`. Declarations above five fail and are never truncated or aliased.

Spawned effects carry the resolved definition identity needed to distinguish execution: supported
target, command intensity, resolved duration, declared scope, reapply policy and observability.
Missing definitions, cycles, nested spawning and targets the affordance runtime cannot execute are
compile errors. This is deliberate capability contraction, not a partially implemented promise.

Costs, direct meter deltas and spawn intensities are canonicalized to their exact float32 runtime
value. Finite float64 values that overflow float32 or authored nonzero values that become zero are
rejected before execution. Effect reapply-by-merge validates the float32 result before mutating the
live instance, so overflow cannot partly apply a lifecycle transition.

Effect definition scope is runtime authority. The executor attaches to that scope, and the manager
ticks, expires and runs despawn behaviour across global, agent, item and affordance stores.
Definition-level intensity is deleted because it never affected execution. Spawn-command intensity
is required, becomes live instance state, and is emitted in the dynamic effect-token payload.
`observable` is required on every effect definition because visibility is behaviour, not a hidden
default.

## Compatibility ruling

This is a pre-release product with zero users and zero downloads. Keeping `dual`, dead definition
intensity, inert lifecycle fields, fallback target parsing or old compiled artifacts would create
technical debt without preserving a user. Old declarations and artifacts fail loudly. Current
packs and references are rewritten at the cut.

## Acceptance

1. Every admitted interaction field reaches its named runtime lifecycle point, and every
   unreachable or member-inapplicable field is refused by the DTO.
2. Changing duration, hours, stage, source, target, form, cost, target meter or supported spawned
   effect metadata changes the compiled affordance signature.
3. More than the fixed effect-summary capacity, non-finite magnitudes, missing/cyclic/nested
   effect references and unsupported targets fail at compilation; no truncation or fallback
   exists.
4. Declared effect scope selects the executed store, all four stores tick and despawn, and live
   spawn intensity reaches the effect token.
5. Compiled-artifact loading reconstructs and verifies these identities rather than trusting
   self-consistent stored hashes.
6. Every current valid pack compiles, focused runtime/compiler tests pass, no-compatibility scans
   are clean, and the full engineering gates pass before milestone 2 closes.

## Consequences

The current full L1 token serialization is 4,090 floats after the five-entry cut and the
exposed-initializer correction: 3,272,000,000 bytes, or 3,120.4 MiB, per 100,000 float32 observation
pairs. Its `variable_element` count is zero because expression-backed exposure is refused until
milestone 3 static context can encode executable initializer identity; the time variable remains
live but unexposed. The remaining width tells the truth about static behaviour. That is acceptable
under `PDR-0131`: milestone 3 removes immutable context from replay rather than weakening identity
to hit a raw-width number. The compact live-state budget remains the relevant historical 9.43x
decision boundary.

Adding a lifecycle stage, spawn target or effect scope is now an end-to-end product change. It must
be executable, represented, hashed, reconstructed and tested in the same checkpoint; extending a
DTO alone is not delivery.
