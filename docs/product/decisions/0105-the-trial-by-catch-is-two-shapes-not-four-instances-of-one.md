# PDR-0105 — The trial by-catch is TWO shapes, not four instances of one — and shape 1 has a mechanical, greppable signature

Date: 2026-08-20   Status: **accepted** (autonomous — prioritizing and routing the backlog is
inside the grant; nothing was fixed)
Author: Claude (standing product owner)

Answers: the standing open question carried in `current-state.md` since the thirty-fifth
checkpoint — *"Are the four 'declared capability, unthreaded execution path' tickets one unit?"*
Discharges: `PDR-0079` trigger 3 (ABSENT/unactioned by-catch overdue for a WS-4 triage session)
Related: `PDR-0005` (the *wire, not delete* triage default), `PDR-0007` (absent ≠ debt),
`hamlet-15050f280a` (WS-4)

## Context

`PDR-0079` trigger 3 had been reading "19+ ABSENT/unactioned by-catch across six trials and two
audits" and describing a WS-4 triage session as *overdue* and *the largest unscheduled item*, for
several consecutive checkpoints. A fired reversal trigger carried across sessions without
converting to work is drift in its own right, so the owner made it this session's top bet.

Alongside it sat an unanswered question: were `hamlet-1b9af9088c` (spawn_item),
`hamlet-a737e444c0` (effects blind to position/time), `hamlet-3381043d2e` (action `writes`) and
`hamlet-f2a37a8c8a` (item vars via `registry.get()`) **one unit**?

Triage was done by **reading `src/townlet/` at `035d5932`**, not by re-reading the tickets. That
distinction is the whole reason the answer changed.

## Options

1. Treat the four as one unit, as the question proposed.
2. Treat all 24 by-catch tickets as independent bugs and route them by priority.
3. **Derive the shapes from source, then route by shape.**

## Decision

**Option 3.** The answer is **no — they are two shapes, and the first has more members than four.**

### Shape 1 — a hardcoded literal where compiled config should flow

The consumer **exists and works**; the producer hands it a constant instead. Verified sites:

| site | literal | ticket |
|---|---|---|
| `universe/compilers/actions.py:205` | `writes=()` | `hamlet-3381043d2e` |
| `effects/executor.py:231` | `scope=EffectScope.AGENT` | `hamlet-4cd664a955` |
| `effects/executor.py:42` | `temporal={}`, `affordances={}` | `hamlet-a737e444c0` |
| `vfs/registry.py:107-110` | `num_groups`/`num_zones`/`num_message_slots` `= 0`, **no caller anywhere passes them** | `hamlet-9e1ae3b7a2`, `hamlet-02bd5a3eaa` |
| spawn_item | `agent_positions` never passed by any production pipeline | `hamlet-1b9af9088c` |

**Five tickets across six sites — and `hamlet-f2a37a8c8a`, one of the original four, is not among
them.**

**The diagnostic signature is mechanical: the hardcoded literal is always the empty / zero /
default member of its type** — `()`, `{}`, `0`, or a fixed enum member. It therefore compiles,
validates, and runs. It just silently does nothing.

Corroboration for the registry case, which is the cleanest instance: `registry.py:477-482`
`_positive_extent` reads `self.num_zones` and raises *"must be positive"* when it is `<= 0`. A grep
for `num_zones`/`num_groups`/`num_message_slots` across **all** of `src/townlet/` returns hits
**only inside `registry.py` itself**. That is exactly why `zone`/`group`/`message` validate at
compile and hard-fail at env construction.

### Shape 2 — the documented route was never built

No hardcoded constant; the path simply does not exist.

- `registry.get()` raises `KeyError` for item-scoped variables — they live in `vfs_profiles.yaml`
  `item_profiles`, never in `_definitions` — `hamlet-f2a37a8c8a`
- `inspect --format json` cannot report observation fields or offsets — `hamlet-53bce4af41`

### Routing

24 trial by-catch tickets (label `prd-0001-trial`), all now accounted for: 8 already WS-4 children,
**13 newly routed to WS-4**, 2 to the docs-truth ticket `hamlet-7a52a63e0b`, and **1 deliberately
held** (see below).

## Rationale

Shape 1 is the **empirical vindication of `PDR-0005`'s *wire, not delete* default**, and it
confirms WS-4's own long-standing claim about the actions case — *"WriteSpec is genuinely consumed
at `vtc.py:409-441` with full dispatch at `:523-558`. Only the YAML path is missing. Largest single
win."* That is not one lucky case. It is the **dominant shape** in the by-catch.

It also gives this project's signature failure mode — *declared but inert* — a **mechanical cause
rather than a descriptive label**. Six trials found this shape independently, none of them named
it, and the tickets read as six unrelated bugs because that is how they were filed. Because the
signature is greppable, the family can now be **enumerated** rather than discovered one trial at a
time — which is the difference between a backlog and a work unit.

Splitting Shape 2 out matters for the same reason in reverse: wiring a constant is a small,
mechanical change with a known consumer; building a missing route is design work. Bundling them
would have made the unit unschedulable.

## One ticket deliberately not routed

`hamlet-a141ab5db3` (`compile` prints success, exits 0, writes **no** cache artifact) was held back
and flagged rather than filed into WS-4. It is **not** an authorability defect — it is a
**provenance-integrity** defect, and it carries an open question about the *other* bet: does it
change the strangler bet's exit condition 3 (*"`Gates green` read on a suite that hides nothing"*)?
It is the second instance of *the gate is green over a hole* and it reproduces on a **shipped**
pack. Routing it into the authoring backlog would have buried a question about a different bet.
Candidate homes are WS-7 (provenance infrastructure) or WS-4 (author-facing tooling); it should be
**placed by a decision, not by a sweep**.

## Reversal trigger

- If a Shape 1 fix at any one of the six sites turns out to require building the consumer as well
  as passing the value, the "consumer exists and works" claim is false at that site, it is not
  Shape 1, and the unit is re-derived.
- If a grep for the signature (a hardcoded `()`, `{}`, `0`, or fixed enum member passed where a
  compiled config value is available) returns **fewer than the six known sites**, the signature is
  not actually mechanical and this PDR has over-generalised from five tickets.
- If the next trial produces a by-catch item matching **neither** shape, the taxonomy is incomplete
  and a third shape is named rather than forcing the item into one of these two.

## Note on the count, which has been quoted three ways

`current-state.md` said **19+**; the `prd-0001-trial` label returns **24**; **15** were unrouted at
the start of this session. These are three different quantities and the drift was itself costing
time. **The trigger is henceforth read on the 24** — the label query — because it is the only one
of the three that is mechanically reproducible.
