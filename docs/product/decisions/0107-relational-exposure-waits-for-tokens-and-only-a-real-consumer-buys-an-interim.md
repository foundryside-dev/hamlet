# PDR-0107 — Relational and message observation exposure waits for token observations; only a real consumer buys the narrow aggregate interim

Date: 2026-08-22   Status: **accepted** (within grant — sequencing against the standing
token-observation direction; internal repo documentation, git-reversible)
Author: Claude (standing product owner)
Owner sign-off: not required. The direction this sequences against is the owner's
(`PDR-0044`: token observations authoritative since 2026-08-11); this PDR decides *order*,
not *whether*.
Related: `PDR-0017` / `PDR-0044` (token direction and its provenance), `PDR-0012` / `PDR-0013`
(no tech debt until 1.0), `PDR-0018` (the packs are test infrastructure, not a curriculum),
`PDR-0090` (substrate frozen for the corpus)
Tracker: `hamlet-fa8ed299c5` (this decision), `hamlet-fa6bb6da4a` (token path, gains a
consumer), `hamlet-424adcb84f` (dynamic variables, re-pointed), `hamlet-0d0115383e`
(transitive blocker of the token path)

## Context

Pair, group, and message variables have full registry storage, unit tests, and — since
2026-08-22 — a working social-residue authoring surface that mutates pair state during
`env.step`. None of it can be observed. Two gates hold, both deliberate:

- `ObservationCompiler._exposed_profile_scopes` admits only `global` and `agent` profiles to
  per-variable observation fields (`src/townlet/universe/compilers/observation.py:498`).
- `ObservationEncoder._build_observation_field_from_vfs` raises for any other scope, with an
  error naming the rule: other scopes are observed through a compiler feature, never as a bare
  field (`src/townlet/environment/observation_encoder.py:94`).

The L5 (other-agent relationships, occupancy) and L6 (messages) curriculum intents depend on
some form of exposure. `hamlet-fa8ed299c5` requires the choice to be recorded as a PDR before
any build starts.

## Options

1. **Build fixed-width relational blocks now** inside the superset+mask ABI — e.g. flattened
   `[num_agents]` trust rows per agent. Fastest to L5 observability; known-throwaway under
   the token direction.
2. **Wait: relational and message state is first exposed as token observations**, as part of
   the `hamlet-fa6bb6da4a` migration. No throwaway; L5/L6 observability blocks on that work.
3. **Build a narrow aggregate interim now** — derived agent-scope features only
   (nearest-agent distance, occupancy summaries), following the item-slots
   compiler-feature precedent. Survives the migration as a feature; builds machinery nothing
   currently drives.

## The call

**Option 2 — wait.** Relational and message observation exposure is deferred to the
token-observation representation. The narrow aggregate interim (option 3) is not built now,
but it is the pre-decided fallback: if a concrete consumer needs relational observability
before the token path's first unit passes, build the interim **scoped to what that consumer
actually reads**, never the general fixed-width mechanism.

`hamlet-fa8ed299c5` closes as "wait, blocked on token-obs migration". No implementation
ticket spawns. `hamlet-424adcb84f` (dynamic variables) is re-pointed from this decision to
`hamlet-fa6bb6da4a`, which its own text anticipates — variable-token observations are the
natural representation for dynamic needs.

## Rationale

Every line of evidence gathered for this decision points the same way:

1. **Option 1 is manufactured tech debt.** The token direction is owner-authoritative
   (`PDR-0044`), which makes fixed-width relational blocks a *known* dead end at authoring
   time — not debt discovered later, debt built on purpose. `PDR-0012`/`PDR-0013` forbid
   exactly this.
2. **Nothing pulls today.** Both packs that declare pair-scope variables
   (`configs/L5_multi_agent`, `configs/trial_o_bidding_blind`) mark them
   `observable: false`. No shipped pack declares social-residue rules (vfs.md §21.1 item 7).
   The packs are test infrastructure, not a curriculum (`PDR-0018`); L5/L6 are "Future" in
   CLAUDE.md. "Fastest to L5" optimizes for a pull that does not exist.
3. **Nothing could land anyway.** The substrate is frozen for the corpus duration
   (`PDR-0090`). The earliest any exposure work could merge is after the nine and the blind
   re-runs — which is also roughly when the token path's first unit becomes schedulable.
4. **Option 3 now would be the house disease.** This codebase's base-rate failure is the
   declared-but-inert feature: six declarative features shipped inert; `set_encoder` and
   `recurrent` are authorable and driven by zero packs. Aggregate relational features that no
   pack observes would be one more. The interim is worth building only against a named
   consumer, at which point its scope is that consumer's reads, not a speculative surface.

The honest cost of waiting: the token path is **unproven**. `set_encoder` has never been
exercised by any pack, `hamlet-fa6bb6da4a` is open and blocked by `hamlet-0d0115383e`. This
decision therefore adds weight to sequencing that chain soon after the corpus — relational
exposure is now its fourth consumer (after the MLP→LSTM progression, the `set_encoder` proof,
and dynamic variables) — and the reversal triggers below bound how long "wait" can silently
stretch.

## Consequences

- **Nothing is built now.** The corpus measurement is undisturbed; the two observation gates
  stay closed and their error messages stay honest.
- **`hamlet-fa6bb6da4a` gains its fourth consumer** and should be sequenced early in
  post-corpus work; its blocker `hamlet-0d0115383e` inherits the same pressure.
- **`hamlet-424adcb84f` (dynamic variables) re-points to the token path**, per its own
  sequencing note. It stops being blocked by a decision and starts being blocked by the work
  the decision chose.
- **Group-scope social rules stay gated** (vfs.md §21.1 item 7) — their observation half now
  has a named owner (the token migration) instead of an open question.
- **The encoder's scope error message remains the contract**: pair/group/message state is
  observed through a compiled feature or a token, never as a bare fixed-width field. Any
  future PR adding a third admitted scope to `_exposed_profile_scopes` should be read as
  reopening this PDR.

## Reversal trigger

Reopen if **any** of the following:

- **A concrete consumer needs relational or message observability before the `set_encoder`
  proof passes** — a trial in the corpus's successor, an owner ask, a demo commitment. Then
  build option 3, scoped to that consumer's actual reads (e.g. only nearest-agent distance),
  and record the scope in the reopening PDR. Option 1 remains forbidden while the token
  direction stands.
- **`set_encoder` proves inert or broken and the owner redirects away from tokens**
  (`PDR-0017`'s second trigger, escalated and answered). If the replacement direction is
  fixed-width, option 1 stops being throwaway and becomes the path — this PDR's premise
  dissolves.
- **The token migration lands.** This PDR then closes naturally: relational exposure becomes
  a unit of that work, and the wait it recorded is over.
