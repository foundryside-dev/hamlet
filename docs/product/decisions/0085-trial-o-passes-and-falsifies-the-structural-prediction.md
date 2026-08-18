# PDR-0085 — Trial O runs fourth, PASSES, and falsifies the corpus's first structural prediction

Date: 2026-08-18   Status: **accepted** (owner chose the session's bet item — "trial four:
multi-agent", from the resume brief's proposals, at the same session's grant re-confirmation;
the executor selected O from the four multi-agent ideas; the verdict itself is the protocol's)
Author: Claude (standing product owner)
Owner sign-off: **yes** on the bet item ("Trial four: multi-agent"); idea selection and
execution autonomous within grant under the ACTIVE protocol

Related: `PDR-0077` (the bet), `PDR-0080` (the corpus and draw), `PDR-0081` (the protocol),
`PDR-0082`/`PDR-0083`/`PDR-0084` (Trials L, F, M — the falsified-prediction run this trial
extends to 4 of 4, and the aggregate falsification this trial deepens)
Tracker: `hamlet-5fa1f7bfc0` (comments 165, 166); by-catch filed `hamlet-4cd664a955` (effect
`scope: global` INERT at spawn) and `hamlet-77e4f8b3e3` (no ambient world-process spawn,
ABSENT), both routed WS-4, labeled `prd-0001-trial`
Artifacts: trial record `docs/product/trials/0001/O-20260818.md` (pin `a3318624`, executor the
standing agent, not blind); pack `configs/trial_o_bidding/` (+ probe); commit `2dcc2273`,
pushed per `PDR-0046`. Full suite green 3281/16/0 before the commit (protocol §10).

## Context

The owner chose "trial four: multi-agent" at this session's resume — deliberately steering the
draw's remaining pool toward the four ideas (D, E, J, O) whose predicted-FAIL reasons are
structural (cross-agent state, heterogeneity, clearing phases) rather than surface-choice,
because the three falsifications so far all had the surface-choice shape. **O (adversarial
bidding) was selected from D, E, J, O for:** (1) the clearing-phase axis is untouched;
(2) its prediction ("FAIL, ABSENT — nothing else in the corpus needs the engine to run a
clearing step") is purely structural, exactly the class the owner's choice targets; (3) it is
the most compact of the four, fitting the one-session budget `PDR-0081` trigger 1 watches.

## What the trial established

**Headline PASS on all six pre-committed facets, both legs** (zero `src/townlet/` diff; every
declared behavior observed at runtime): per-agent bids write from affordance `on_start`
(Trial M's pattern); two agents' simultaneous bids both stand inside a declared 3-tick
collection window; the clearing phase — an effect ticking engine-side — computes a running max
over `for_each: all_agents` into global VFS scratch, awards `wins` to the highest bidder only
(swap-tested: the outcome follows the amounts, not agent index or order), charges exactly the
bid from `credits`, expires every bid, and awards nobody on empty windows; and all auction
state including the global `highest_bid` is observation-encoded. The pack compiled on the
first `validate` attempt and the probe passed every facet on its first run.

**The first-reached surface is unreachable — the `PDR-0082` shape, fourth occurrence**: a
`scope: global` effect is the natural declaration for a world-owned clearing process, and it
validates and compiles — but every spawn path hardcodes agent scope
(`executor.py:228-231`, "scope hardcoded to AGENT for now"), and nothing spawns any effect at
reset, so a standing world process must be bootstrapped by the first agent action. Both filed,
not fixed. The second surface (agent-scoped, long-duration, `renew`-policy effect pinned to
slot 0 by its spawning affordances) expresses the whole idea.

**The prediction is falsified — and this one is different in kind.** L, F, M falsified
surface-choice predictions; O's was structural, and it fell because the effects command
vocabulary (`for_each: all_agents`, global VFS scratch, guarded branches, engine-ticked) *is*
a declarative clearing surface the ledger-derived priors never accounted for. Noted in the
record: the expression vocabulary also carries `max_all`/`argmax`/`count_where` — a possible
*third* clearing surface, unprobed. The corpus's prediction machinery is now 0-for-3 on its
FAIL/PARTIAL calls and the miscalibration mechanism (predictions score the first surface an
author reaches; trials score any declared surface) is consistent across all four records.

**North-star state after this trial: 4 of 4 run (denominator 9, no voids), 0 ABSENT / 0 INERT
/ 0 BLOCKED.** INERT escalation counter (threshold 3): 0. Remaining: B, D, E, J, K — three of
five multi-agent (D, E, J), which still carry the heaviest structural predictions (cross-agent
transfer, heterogeneity, cross-agent writes).

## Also this session (recorded here, no separate PDR)

- **Branch Lint had been red for four consecutive pushes** (two E501s in Trial F's probe,
  introduced at `fb56fbbd`, unnoticed by two checkpoints because the local gate list was run
  on `src/` while the probe lives under `configs/`). Found at this session's ORIENT, fixed at
  `a3318624`, CI green on the fix (all three workflows). Delivery hygiene inside the grant.
- **Two post-freeze corpus candidates captured** — Q (continuous sin/cos day-night forcing)
  and R (heliotropism: orientation-as-state with an alignment reward), owner-raised
  mid-session — in `docs/product/prds/0001-corpus-candidates.md`, deliberately OUTSIDE the
  frozen corpus (an edit there voids the remaining trials). No predictions written; those
  belong to a future freeze. Capability recon recorded: no `sin`/`cos`/`mod` in the
  expression vocabulary; `elapsed_ticks` exists; continuous substrate keeps no orientation
  state.
- **Methodology review dispatched** (owner-directed, end of session): three Fable reviewers —
  construct-validity critic, RL-practitioner lens, statistical-inference lens — examining
  whether the trial instrument tests the right thing. Results land after this checkpoint;
  findings route to the next session's DECIDE (and may become `proposed` PDRs).

## Rationale for accepting the verdict

The protocol held on its fourth outing: preflight pasted (corpus hash byte-identical, tree
clean at `src/townlet/`, pin recorded), six facets and their leg-(b) evidence pre-committed
before authoring, gaps filed rather than fixed, both legs executed and pasted, guardrails run
before the commit. One honesty note in the record: the pre-committed `inspect --format json`
check turned out to emit a metadata summary only, so artifact-side evidence was read from the
compiled artifact directly (`compiled_effect_catalog`, `observation_spec.fields`) — the same
object, stated rather than silently substituted.

## Reversal trigger

- If either blind re-run (criterion 3, 2 of 9 by 2026-10-06) disagrees with its first run on
  headline or per-facet classification, the instrument is NOT accepted and no north-star
  reading publishes — this verdict included (PRD criterion 3 reject branch).
- Pack disposition clock: `configs/trial_o_bidding/` is the FOURTH pack on the 2026-10-06
  clock (with `trial_l_cooldown`, `trial_f_durability`, `trial_m_combo`) — each promoted to a
  fixture or deleted by that date, else PRD criterion 7 rejects the bet.
- The INERT escalation clause (`PDR-0079`, threshold 3) is untouched at 0.
- If the methodology review (three reviewers, dispatched this session) returns a CONFIRMED
  finding that the instrument does not measure the vision's claim, the readings taken so far
  are re-scoped by a new PDR before any publication — the 2026-10-06 reading does not publish
  over an open confirmed validity defect.
