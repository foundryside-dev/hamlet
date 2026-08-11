# PDR-0017 — The token/transformer observation direction is recorded, not started; the first step is proving `set_encoder` works

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)
Owner sign-off: not required (within grant — sequencing work against existing strategy). The **direction** is the owner's: *"move to embedded transformers to 'solve' our obs problem"*, clarified immediately as *"more of an orthogonal comment … we should have put a pin in that a long time ago"* — i.e. raised to be captured, not to redirect the session.
Related: PDR-0016 (bounds + normalization), PDR-0007 (options not yet enabled), PDR-0006 (strangler), PDR-0009 (per-level architecture gap)
Tracker: `hamlet-fa6bb6da4a`, blocked by `hamlet-0d0115383e`

## Context

While reviewing task 3a's blast radius the owner observed that the fixed 124-dim observation
vector is itself the problem, and proposed embedded transformers. Investigating before
answering turned up a fact that changes what the proposal costs.

**The token encoder already exists.** `SetEncoderQNetwork` (`agent/networks.py:443`) embeds a
fixed-capacity token set and pools it permutation-invariantly — DeepSets, i.e. a transformer
with mean-pooling where self-attention would go. It is authorable today:
`brain_config.py:368` accepts `set_encoder`, with a `SetEncoderConfig` and a validator.

So a transformer is an **aggregator upgrade**, not a new build. But:

| architecture | implemented | packs using it |
|---|---|---|
| `feedforward` | yes | 18 |
| `dueling` | yes | 2 |
| `recurrent` | yes | **0** |
| `set_encoder` | yes | **0** |

**Two of four brain architectures are implemented, authorable, documented — and driven by
nothing.** The same disease as the config surface, one layer up.

## Options considered

1. **Act on it now**, inside WS-1. Rejected: it is rebuild-scale work, and `PDR-0007`'s second
   reversal trigger explicitly watches for capability work starving the recovery. The owner
   also disclaimed the urgency directly.
2. **Record it as a direction and start with the transformer.** Rejected for the reason below.
3. **Record it, and make the first step proving `set_encoder` actually works** — taken.

## The call

**Option 3.** Filed as `hamlet-fa6bb6da4a`, sequenced after the oracle freeze and after the
HLD-versus-implementation divergence map, with `hamlet-0d0115383e` (per-level `architecture`
is not overridable) recorded as a hard blocker — without it no pack can author the experiment
at all.

**The first unit is not the transformer.** It is a config-in/behaviour-out test that authors
`architecture.type: set_encoder` and asserts the tokens reach the network and change its
output.

## Rationale

Attaching attention to `set_encoder` without first proving `set_encoder` runs would repeat, at
the architecture layer, the exact mistake this recovery exists to fix. Six declarative features
shipped inert; `clamp_and_validate` is a declared-but-empty phase; the entire VFS normalization
ABI has zero production callers. An unexercised code path in this codebase is not
presumptively working — the base rate says otherwise.

Two things are also worth separating, because "solve our obs problem" bundles them:

- **Structure** — a token encoder genuinely kills the fixed 14-affordance vocabulary and the
  fixed 124-dim vector. The observation *shape* stops being a hardcoded fact about one
  universe. This is real strangling and is the strongest argument for the direction.
- **Scale** — it does *not* fix magnitude. A `money` token at 22.5 beside an `energy` token at
  0.5 is still badly scaled, and there is no LayerNorm anywhere in the shipped brain. Scale
  belongs to the declared normalization surface, which `PDR-0016` wires now.

Recording that split is the point of this PDR: without it, a future session reads "transformers
solve the obs problem", ships tokens, and is surprised when magnitudes still misbehave.

## Consequences

- **Nothing is built now.** WS-1 is unaffected; the freeze is not delayed.
- **`PDR-0016`'s normalization half is not made redundant by this.** If anything the reverse:
  normalization is needed under either observation architecture, so wiring it now is not work
  thrown away when tokens land.
- **`hamlet-0d0115383e` gains a second consumer** and its priority argument strengthens — it
  already blocked the documented MLP→LSTM curriculum progression, and now blocks this too.
- **Tasks 6 and 7 are reframed, not devalued.** They fix the recurrent path's gradient flow and
  window-boundary bootstrap, and no shipped pack is recurrent. They are worth landing before
  the freeze so the oracle does not encode a broken component — but they are "don't freeze
  this broken", not "fix training".

## Reversal trigger

Reopen if **any** of the following:

- **`set_encoder` turns out to work** and a pack exercises it successfully. The first unit then
  collapses to a formality and the transformer step can be scheduled directly.
- **`set_encoder` turns out to be inert or broken.** Then the question is no longer "add
  attention" but "is the token path worth repairing or replacing", which is a design fork that
  escalates to the owner rather than being answered inside WS-4.
- **The divergence map concludes the target observation is NOT token-based.** The HLD is the
  design authority and has not yet been read on this question; if it specifies something else,
  this PDR is superseded by that finding rather than by preference.
