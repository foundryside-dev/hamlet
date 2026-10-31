# PDR-0009 — Per-level `architecture` is an authorability gap (WS-4), not a WS-1 correctness defect

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: n/a (within grant — classification and backlog placement)
Related: PDR-0007 (options not yet enabled + definition-of-done), PDR-0008, metrics.md (Config-surface coverage, Mind-authoring surface), tracker `hamlet-0d0115383e` under WS-4 `hamlet-15050f280a`

## Context

The WS-1 completeness critic established, by execution, that the shipped `L2_partial_observability`
is a POMDP trained by a **memoryless feedforward MLP** — and that no config pack can change this:

- Zero recurrent packs exist. Of 21 `brain.yaml` files, 18 are `feedforward`, 2 `dueling`, 1
  `feedforward`; `grep -rn recurrent configs/` returns one hit, in a reference *document*.
- `L2_partial_observability/curriculum.yaml:9` is `active_vision: partial`, and that level
  directory contains no `brain.yaml`.
- `apply_training_overrides` merges exactly five fields — `q_learning.{gamma,
  target_update_frequency, use_double_dqn}`, `optimizer.learning_rate`, `replay.capacity`.
  **`architecture` is not among them.** Architecture is pack-scoped only.

So a single curriculum pack **structurally cannot** express the L0-MLP → L2-LSTM progression that
`CLAUDE.md` documents. This arrived inside a WS-1 sweep, so the placement question was live: is it
a fourth correctness defect, or something else?

## Options considered

1. **File it as a WS-1 correctness defect** — pro: it was found there, and it is adjacent to (b)
   and (c). Con: nothing is *incorrect*. Every component behaves as written; the capability was
   never wired. Filing it in WS-1 would also make it a freeze blocker, which it is not.
2. **File it as a WS-5 documentation-truth item** — pro: `CLAUDE.md` is demonstrably false about
   L2/L3. Con: this treats the *doc* as the defect and would "fix" it by writing down the
   limitation — converting an unbuilt option into a permanent decision, which is exactly what
   `PDR-0005` and `PDR-0007` forbid.
3. **File it as a WS-4 authorability gap, with the doc half routed to WS-5** — the option taken.

## The call

**Option 3.** This is a declared-but-unreachable **authoring surface** — `PDR-0007`'s exact
category, *an option not yet enabled* — and it belongs in WS-4 (`hamlet-15050f280a`), the stream
that closes the "you must write Python" gaps. The documentation half routes to WS-5.

It is sequenced **after** WS-1(b) and (c): enabling recurrent authoring before the recurrent
training path is fixed would ship a config option whose observable behaviour is wrong, which is
the precise failure `PDR-0007`'s definition-of-done exists to prevent.

`PDR-0007`'s definition-of-done applies in full: the option is not done when `architecture` joins
the override list. It is done when a pack authors it at a non-default value, it drives observable
runtime behaviour, and a config-in/behaviour-out test (WS-3) pins it.

## Rationale

Option 3 beat option 1 because "correctness" and "authorability" have different acceptance tests
and different freeze semantics. WS-1 is gated by *the oracle must be correct before it is frozen*;
this item is gated by *the option must be wired and tested before it is exposed*. Conflating them
would either make WS-1 unclosable or let this ship as a schema field with no runtime — the exact
mechanism that produced the ~40 inert surfaces.

Option 2 was the tempting one and is the more dangerous, because it looks like honesty. Writing
"L2 uses a feedforward network" into the docs would be true, cheap, and would convert an unfinished
plan step into a decision nobody made — `PDR-0005`'s core error, at the level of a headline
capability.

There is a sharper reason this is a *product* finding rather than a bug. The vision's promise is
that **both halves of an experiment — the world and the mind — are declarative**. Trial 001 proved
the world half by re-substrating Sims into six dimensions with zero Python. This is the mirror
result on the mind half: the most basic cognitive choice in the shipped curriculum — does this
agent have memory? — is not authorable per level at all. `metrics.md` recorded the Mind-authoring
surface as *1 of 3, Layer 2 is live*. The correct reading is now **Layer 2 is live at pack scope
only**, which is narrower than "live" implied.

## Consequences

- **`metrics.md` Config-surface coverage** does not improve; it is *revealed narrower*. The
  curriculum/cognition surface was assumed authorable per level and is not.
- **WS-1(b) and (c) get their reachability answer.** They are unreachable today *because of this*.
  Fixing this is what makes them matter, and it is why they must precede it.
- **An open design fork is recorded, not resolved:** is per-level `architecture` override the right
  shape, or should `brain.yaml` be level-overridable the way `training.yaml` is? The second is more
  coherent with the grammar — and `PDR-0007`'s limiting principle is coherence, not effort — but it
  is a larger change. Decide before implementing.

## Reversal trigger

Reopen this PDR if **any** of the following:

- **A recurrent pack is authored and trains correctly without touching `apply_training_overrides`** —
  i.e. a per-pack recurrent universe turns out to serve the curriculum need. The gap would then be
  narrower than stated and this drops in priority.
- Making `brain.yaml` level-overridable requires a **runtime special case** — a branch on level
  name or a path around the compiled contract. Under `PDR-0007`'s limiting principle that is
  presumptively *no*, and it escalates to the owner as a question about the expressible problem
  space rather than being resolved in WS-4.
- The inert-surface count in `metrics.md` **rises** after this lands. That is `PDR-0007`'s own
  reversal trigger and it fires here first, because this is the first option enabled under it.
