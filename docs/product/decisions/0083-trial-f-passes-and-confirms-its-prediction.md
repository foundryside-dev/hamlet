# PDR-0083 — Trial F runs second, PASSES, and confirms its pre-registered prediction: the aggregate prediction is now at its ceiling

Date: 2026-08-18   Status: **accepted** (owner chose the session's bet item — "Run trial two",
option 1 of the resume brief's proposals, at the same session's grant re-confirmation; the
executor selected F from the eight remaining; the verdict itself is the protocol's)
Author: Claude (standing product owner)
Owner sign-off: **yes** on the bet item ("run trial two"); idea selection and execution
autonomous within grant under the ACTIVE protocol

Related: `PDR-0077` (the bet), `PDR-0080` (the corpus and draw), `PDR-0081` (the protocol),
`PDR-0082` (Trial L — the precedent this record follows, and the falsified-prediction lesson
Trial F now counterweights)
Tracker: `hamlet-5fa1f7bfc0` (comment 163); by-catch filed `hamlet-fba3d5aa3c` (routed WS-4),
`hamlet-6f27878731` (routed to the docs-truth task `hamlet-7a52a63e0b`), both labeled
`prd-0001-trial`
Artifacts: trial record `docs/product/trials/0001/F-20260818.md` (pin `e5f7dd7a`, executor the
standing agent, not blind); pack `configs/trial_f_durability/` (+ probe); commit `fb56fbbd`,
pushed per `PDR-0046`. Full suite green 3281/16/0 before the commit (protocol §10).

## Context

The owner chose "run trial two" at this session's resume. The protocol names no draw order for
the remaining eight, so idea selection was the executor's call — recorded here because it is the
one degree of freedom the mechanical draw left open. **F (tool durability) was chosen for:**
(1) axis diversity — the items bucket was untouched by any trial; (2) prediction stress — F is
the only predicted-PASS in the remaining set, and after Trial L the aggregate pre-registration
("1, possibly 2, pass") stood at 1, so F tested its ceiling in whichever direction it landed.

## What the trial established

**Headline PASS on all four pre-committed facets, both legs** (zero `src/townlet/` diff; every
declared behavior observed at runtime): the wear state is a declared item-scoped VFS variable
(`vfs_profiles.yaml` alone — `durability`, initial 3.0, `exposed_to: [agent]`); USE decrements
it by exactly the declared amount (3→2→1→0) while idle ticks leave it untouched; at zero the
guarded `on_use` effect stops firing (breaks-as-stops-working — no despawn/destroy effects
command exists, so physical destruction was not attempted; the pre-committed facet accepted
either consequence); and `obs_item_slots` (compiled offset 58) tracks the wear value in the
encoded observation at every step.

**The prediction (PASS) is CONFIRMED — the corpus's first confirmed prediction** (1 confirmed,
1 falsified, of 2 run). **The aggregate pre-registration ("1, possibly 2, pass; INERT count
1–2") now stands at its ceiling**: 2 passes banked, 7 trials remaining, INERT count 0. Any
further pass falsifies the aggregate — which the `PDR-0082` calibration lesson (predictions
were made against the first surface an author would reach, not the space of declared surfaces)
already suggests is the likely direction.

**North-star state after this trial: 2 of 2 run (denominator 9, no voids), 0 ABSENT / 0 INERT /
0 BLOCKED.** INERT escalation counter (threshold 3): 0 — by-catch defects do not count ideas.

## Rationale for accepting the verdict

The protocol held on its second outing: preflight pasted (corpus hash byte-identical), facets
and evidence pre-committed before authoring, gaps filed rather than fixed, guardrails run before
the commit. Two mid-authoring events, both recorded as pack work rather than facet failures per
§1's BLOCKED definition: the stale copied `.compiled` cache was deleted preemptively (the exact
Trial L mistake), and the zero-affordance crash was a pack-shape edge outside idea F's facets —
worked around with one inert affordance and filed (`hamlet-fba3d5aa3c`). Neither refused the
idea's declaration, so neither is BLOCKED; the line `PDR-0081`'s triggers watch was not
stressed.

## Reversal trigger

- This PDR records an executed measurement; the *instrument's* reversal triggers live in
  `PDR-0081` and none fired: 0 budget-limited records in 2 trials, no blind re-run yet.
- Pack-disposition clock: `configs/trial_f_durability/` must be promoted to a regression
  fixture or deleted by **2026-10-06**, or PRD-0001 criterion 7 rejects the bet — the same
  clock `PDR-0082` started for `configs/trial_l_cooldown/`. Two packs now sit on it.
- If a blind re-run of L or F (criterion 3) disagrees on headline or per-facet classification,
  the instrument is not accepted and no reading publishes (PRD criterion 3 reject branch).
