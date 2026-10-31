# PDR-0014 — WS-1 plan amendments: take D5, split out the dead-agent defect, and wire `bars.*.bounds` instead of deleting the clamp

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)
Owner sign-off: not required (within grant — accepting/amending a plan against criteria), but **ratified by the owner on 2026-08-11**: *"yes all those three are obviously decisions."* Recorded because "not required" alone would suggest the owner never saw them. The call below is unchanged by the ratification.
Related: PDR-0008 (WS-1 verified), PDR-0012 (no tech debt), PDR-0007 (options not yet enabled), PDR-0006 (oracle freeze), metrics.md (Config-surface coverage, Provenance integrity)
Plan: `docs/zzz. archive/plans/2026-08-11-ws1-fix-set.md` · tracker `hamlet-67ffbd282a`, `hamlet-88acec4bb5`

## Context

The WS-1 fix plan was reviewed by four independent `axiom-planning` lenses and synthesised to
**CHANGES_REQUESTED**. The grounding was exceptional — zero hallucinations across ~45 checked
claims, and two reviewers independently reproduced the gate baselines filename-for-filename — and
the sequencing, decomposition and pinning-test discipline reviewed clean. Three blocking issues
remained, all of them decisions the plan had left open rather than errors it had made.

`PDR-0012` (adopted hours earlier) changes how two of them resolve: it forecloses deferral as an
option, so "open it as a follow-up unit" is only acceptable when the item genuinely belongs to a
different owner, never when it is merely inconvenient.

## Options considered

Per blocker, the live choice was the same shape — **absorb it, defer it, or document it** — and
`PDR-0012` removed the third in all three cases.

**B1 — `primary_level` stamped and compared.** (a) implement in-batch; (b) file as a follow-up unit.
**B2 — the missing dead-agent filter.** (a) fold into task 3; (b) file as its own unit.
**B3 — the meter-bounds clamp.** (a) delete the one clamp as planned; (b) delete all sites together;
(c) keep the clamp as a silent net; (d) wire `bars.*.bounds` and have every site read it.

## The call

**B1 — implement in-batch.** The plan's stated deliverable is *"the provenance guardrail is no
longer breached"*, and without D5 an `L0_5_dual_resource` checkpoint resumes into
`L1_full_observability` with **eight of nine identity fields colliding** and every guard green. It
is ~2 lines, in files three tasks already have open. A batch whose headline claim is false the
moment it lands is debt by `PDR-0012`'s definition, so (b) was not available.

**B2 — file as its own unit** (`hamlet-88acec4bb5`), and **wider than the review found.** Verified
directly: `substrate_mask` is an action-id range mask with no relation to `dones`, so the cost debit
at `action_executor.py:149` sits *upstream* of the instant/multi-tick split — dead agents are
charged interaction costs on **both** paths, not merely allowed to complete instant ones. The
multi-tick `active_mask=~env.dones` guard protects progress but not the debit. This is a split, not
a deferral: task 3 rewrites `affordance_engine.apply_interaction`, and this defect lives in a
different function in a different file. Folding it in would have hidden a second behaviour change
in the hottest path in the runtime.

**B3 — wire `bars.*.bounds`; do not delete the clamp, and do not keep it hardcoded.** The review
gated this on whether effects overshoot `1.0`. **Config settles it: they do, routinely.** Bars ship
`initial: 1.0` with `bounds.max: 1.0`, while `SLEEP` applies `energy + 0.8` (computes 1.8) and
`EAT` applies `satiation + 0.4` (computes 1.4). `torch.clamp(..., 0.0, 1.0)` is the only thing
re-ceilinging them.

Also corrected: **there are four meter-clamp sites, not six** (`affordance_engine.py:209`, `:310`;
`action_executor.py:60`, `:150`). The fifth grep hit is a `smoothstep` maths helper.

## Rationale

B3 is the decision worth explaining, because the obvious readings are all wrong.

Deleting the clamp (a) looked like cleanup and is the opposite: `bars.*.bounds.max` is **inert** —
declared, validated, driving nothing — so the hardcoded clamp is the *only* enforcement of the
declared bound. Deleting it would make `bounds.max: 1.0` a lie at runtime, which under `PDR-0007`
is the worst failure mode available to a declarative product. Keeping it as a silent net (c) was
proposed by one reviewer and is the *"silent fallbacks hide breaking changes that should fail
loudly"* antipattern named in `CLAUDE.md` and reinforced by `PDR-0012`/`PDR-0013`; the synthesis
discounted it on exactly those grounds and this PDR concurs. Moving all four together but leaving
them hardcoded (b) fixes the inconsistency and preserves the magic number.

Option (d) is better than all three because **the defect and the product goal turn out to be the
same work.** A hardcoded `(0.0, 1.0)` is a config value that was never wired; wiring it removes
debt *and* moves **Config-surface coverage**, which is an input metric to the north-star. This is
the first case in the recovery where repaying debt and advancing authorability are one action
rather than competing for capacity — worth noticing, because `PDR-0007`'s second reversal trigger
watches for exactly the opposite (capability work starving the recovery).

It is a deliberate scope increase to WS-1, taken rather than escalated because it falls inside the
grant (reprioritising and accepting against criteria) and because `PDR-0012` is the owner's own
standing policy applied to its first real test. Per `PDR-0007`'s definition-of-done it is not
complete until a pack authors `bounds.max` at a non-default value, it drives observable runtime
behaviour, and a config-in/behaviour-out test pins it: author `bounds.max: 0.5`, apply SLEEP, assert
energy settles at `0.5`.

Warnings W1–W5 are accepted as written and folded into their tasks; none required a product call.

## Consequences

- **WS-1 grows by two units** — D5 in-batch, and `hamlet-88acec4bb5` as a sibling. The batch still
  gates the oracle freeze.
- **`bars.*.bounds` moves from inert to wired**, so the next reading of *Declared-but-inert config
  surfaces* should fall — the first decrement since the count was established at ~40.
- **The plan is now durable in-repo** at `docs/zzz. archive/plans/2026-08-11-ws1-fix-set.md`, carrying a
  post-filigree banner so WS-6's archaeology does not mistake it for the pre-filigree stratum.
- **The review does not carry forward.** Per the synthesis's own caveat, the plan must be
  re-reviewed after these amendments land rather than treated as approved.

## Reversal trigger

Reopen this PDR if **any** of the following:

- **Wiring `bars.*.bounds` turns out to require a runtime special case** — a branch on a bar name,
  or an escape past the compiled contract. Under `PDR-0007`'s limiting principle that is
  presumptively *no*, and it escalates to the owner as a grammar question rather than being solved
  inside WS-1.
- **The bounds wiring materially delays the oracle freeze.** The scope increase was justified on
  *"same work, two benefits"*; if it stops being the same work, the debt half still must land
  (`PDR-0012`) but the authorability half re-sequences to WS-4 and the call belongs to
  `/axiom-program-management`.
- **The `env.dones` semantics question turns out to be a genuine design decision** rather than an
  unfinished one — i.e. someone intended dead agents to keep transacting. That would make
  `hamlet-88acec4bb5` a documentation task, not a defect, and would contradict the multi-tick
  path's existing guard.
