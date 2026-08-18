# PDR-0084 — Trial M runs third, PASSES, and falsifies both its own prediction and the aggregate pre-registration

Date: 2026-08-18   Status: **accepted** (owner chose the session's bet item — "Run trial three",
option 1 of the resume brief's proposals, at the same session's grant re-confirmation; the
executor selected M from the seven remaining; the verdict itself is the protocol's)
Author: Claude (standing product owner)
Owner sign-off: **yes** on the bet item ("run trial three"); idea selection and execution
autonomous within grant under the ACTIVE protocol

Related: `PDR-0077` (the bet), `PDR-0080` (the corpus and draw), `PDR-0081` (the protocol),
`PDR-0082` (Trial L — the falsified-prediction shape this trial repeats), `PDR-0083` (Trial F —
whose "the aggregate is at its ceiling" note this trial cashes in)
Tracker: `hamlet-5fa1f7bfc0` (comment 164); by-catch filed `hamlet-f1dec55b9d` (custom-action
surface cannot express effects or preconditions — ABSENT, routed WS-4), labeled `prd-0001-trial`
Artifacts: trial record `docs/product/trials/0001/M-20260818.md` (pin `a519f312`, executor the
standing agent, not blind); pack `configs/trial_m_combo/` (+ probe); commit `790dcb7e`, pushed
per `PDR-0046`. Full suite green 3281/16/0 before the commit (protocol §10).

## Context

The owner chose "run trial three" at this session's resume. Idea selection remained the
executor's one degree of freedom; **M (combo actions) was chosen from B, D, E, J, K, M, O for:**
(1) axis diversity — the action-structure bucket was untouched; (2) it is the corpus's second
live test of the ABSENT/INERT distinction — the authorability ledger's "custom actions are
structural no-ops" and "VTC action-writes have no YAML path" claims meet the metric here, and
`PDR-0079`'s escalation clause watches the INERT count; (3) it is single-agent and compact,
fitting the one-session budget where the remaining multi-agent ideas (D, E, J, O) risk a
budget-limited record (`PDR-0081`'s trigger 1 watches those).

## What the trial established

**Headline PASS on all five pre-committed facets, both legs** (zero `src/townlet/` diff; every
declared behavior observed at runtime): three sequential operations and two per-agent
progression traces compile from config alone; performing A sets its trace on its tick while ten
idle ticks move nothing; B's entire effect sits inside `if: target.bar.did_a >= 1.0` so before A
it applies nothing and leaks nothing; the chain composes to depth 3 (C refused at reset AND
after A alone, applies only after A then B); and the encoded observation tracks both traces,
including the mid-chain [1, 0] state.

**The first-reached surface is incapable, and that is the trial's sharpest finding**: the
custom-action surface (`actions.yaml` — the one a fighting-game author would reach for a combo)
admits only `name`/`description`/`enabled_by_default` with `extra="forbid"`; no effect, no
precondition, and the runtime `reads`/`writes` door into the tested composition engine is
reachable from no YAML. Filed as `hamlet-f1dec55b9d` (ABSENT — `PDR-0007` not-yet-enabled, a
feature not debt), not fixed. The affordance surface (event-trace meters + whole-effect `if`
gates, the Trial L pattern) then expressed the whole idea.

**Both predictions falsified.** M's own (PARTIAL, possibly INERT) → actual PASS — the third
falsification in the `PDR-0082` shape (prediction scored the first surface an author reaches; a
second declared surface expresses the idea). The "possibly INERT" limb never materialized
because the incapable surface refuses extra fields at parse rather than accepting them silently.
**And the AGGREGATE pre-registration ("1, possibly 2, pass; INERT count 1–2") is now formally
FALSIFIED: 3 passes of 3 run, INERT count 0, six trials remaining.** Stated, not smoothed over.
The corpus's prediction machinery has been systematically pessimistic about the substrate so
far — which is itself a finding about the ledger-derived priors the predictions were built on,
and the six remaining trials (four of them multi-agent) are where that read gets its real test:
the passes so far all live in single-agent territory.

**North-star state after this trial: 3 of 3 run (denominator 9, no voids), 0 ABSENT / 0 INERT /
0 BLOCKED.** INERT escalation counter (threshold 3): 0.

## Rationale for accepting the verdict

The protocol held on its third outing: preflight pasted (corpus hash byte-identical, tree
clean, pin recorded), facets and leg-(b) evidence pre-committed before authoring, gaps filed
rather than fixed, both legs executed and pasted, guardrails run before the commit. One
process near-miss, recorded for honesty: the record was initially drafted with placeholder
results and an invented authoring log; the error was caught and blanked **before any authoring
began**, so the pre-commitment discipline (facets and accepted evidence fixed before the pack
existed) held in substance. The facet table was not edited after authoring started.

## Reversal trigger

- If either blind re-run (criterion 3, 2 of 9 by 2026-10-06) disagrees with its first run on
  headline or per-facet classification, the instrument is NOT accepted and no north-star
  reading publishes — this verdict included (PRD criterion 3 reject branch).
- Pack disposition clock: `configs/trial_m_combo/` (now the third pack, with `trial_l_cooldown`
  and `trial_f_durability`) is promoted to a fixture or deleted by 2026-10-06, else PRD
  criterion 7 rejects the bet.
- The INERT escalation clause (`PDR-0079`, threshold 3) is untouched at 0.
