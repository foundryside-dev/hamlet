# PDR-0092 — Trial K is run and FAILS: the world does not act until an agent acts first, and the corpus's summary line is inverted

Date: 2026-08-19   Status: **accepted** (autonomous within grant; the trial-six = K choice was
the owner's, made at this session's resume)
Author: Claude (standing product owner)

Related: `PDR-0077` (the bet), `PDR-0081` (protocol), `PDR-0086` (Appendix A), `PDR-0091`
(the two pre-authoring rulings that governed this trial), `PDR-0079` (classification
vocabulary), `PDR-0090` (the substrate freeze this trial ran under)
Tracker: `hamlet-5fa1f7bfc0` (the bet) · filed this trial: **`hamlet-9e1ae3b7a2`** (P1,
zone/group/message scopes crash at env construction), **`hamlet-a737e444c0`** (P1, effects
cannot read position or time), `hamlet-628e202bf7` (P2, item `on_drop` INERT) · comments
171 (`hamlet-77e4f8b3e3`), 172 (`hamlet-d76684f549`), 173 (`hamlet-f46e2b381a`),
174 (`hamlet-bf42ac60b5`), 175 (`hamlet-02bd5a3eaa`), 176 (`hamlet-e3af412673`)
Artifacts: record `docs/product/trials/0001/K-20260819.md` (pin `3434b2fa`) · pack
`configs/trial_k_cold/` (level `L0_cold`) · probe `configs/trial_k_cold/probe_trial_k.py`

## Context

Sixth of the drawn nine, second under Appendix A. The owner chose **K — "Responding to the
universe"**: the only untouched axis in the corpus, **the world acting on the agent**, with
three mitigation paths each landing in a different subsystem (equip an item, change location,
eat the cost). Appendix A executed in full: preflight (corpus hash byte-exact), A.1
countersigning by a fresh non-executing agent, **A.2 search pre-registration written before the
countersigned list arrived**, A.3 discovery paths, A.4 leg-(c) column, A.5 record integrity.

## The verdict

**Headline FAIL.** Nine countersigned facets, all settled, **not budget-limited**.

PASS: F2 (threshold gate — warm-side magnitude exactly 0.0, cold-side not; equality boundary
exact at 0.5), F3 (world→agent effect — `comfort` falls 0.1/tick while all four agents WAIT,
against a flat warm-side contrast), F4 (observability — `world_temp` at compiled offset 85,
mask active, tracking), F5 (the equipped item modulates the incoming effect's own magnitude:
`0.100000 → 0.040000`, over-mitigation floors at zero, unequip residual exact), F6 (equip is a
runtime verb — `GET` then `USE_SLOT_0` inside one episode), F8 (floor reached, declared terminal
fires at t=12).

FAIL: **F1 (ABSENT)** — over 12 all-WAIT ticks `world_temp` did not move and the declared world
process ran zero times. **F7 (BLOCKED + ABSENT)** — both routes refuse. **F9** — only two of the
three required paths exist.

**The load-bearing structural point:** F2, F3, F4 and F8 were all probed *downstream of the
cheat-#2 ignition F1 rules out*. Four of the six passes are conditional on an ignition the idea
forbids. "Seven of nine facets pass" would materially overstate this substrate, and the record
says so explicitly so a blind re-runner can reproduce the numbers.

## Prediction vs. actual — SPLIT, and the corpus's own summary is inverted

The corpus predicted PARTIAL, summarising: *"an author can express the problem but not the
answers to it."*

- **Falsified:** the equipped-item modifier chain — "a modifier chain I have not seen a path
  for" — **works**, cleanly, first-reach, with exact arithmetic and correct saturation.
- **Confirmed, and worse than predicted:** `zone` scope fails. Not merely "no evidence it is
  live" but compile-clean and run-fatal, across three scopes.
- **Falsified in an unexpected direction:** the pressure is *not* straightforwardly authorable.
  Its **rule** is declarative and exact; its **ignition** is not. Trial 002's precedent held
  only because an agent had already acted.

> **An author can express two of the three answers, and cannot make the problem happen on its
> own.**

## The two P1s

**`hamlet-9e1ae3b7a2`** — a zone-scoped variable validates and compiles (exit 0, full hash set),
then hard-crashes at env construction. `num_zones` / `num_groups` / `num_message_slots` are
`VariableRegistry` kwargs defaulting to 0; `vectorized_env.py:621` never passes them and **no
YAML in the repo sets any of them**. Three of nine declared scopes are unreachable.

**`hamlet-a737e444c0`** — `effects/executor.py:642-726` builds its expression context two ways
and neither passes `agent_positions`, `affordance_positions`, or `temporal`. So the only
engine-ticked surface a pack can declare is **blind to both where the agent is and what time it
is**. Second confirmed instance of the `hamlet-1b9af9088c` pattern: the grammar declares a
capability the execution path never threads data for.

## A coverage finding inside the scope finding

The suite ran **3281 passed / 16 skipped / 0 failed** at this tree while three declared scopes
hard-crash any pack using them — possible only because **no test instantiates them**. The gate
is green over a hole. This bears directly on the strangler bet's exit condition 3 (*gates green
on a suite that hides nothing*): a suite that deselects nothing can still be silent about
vocabulary nothing ever exercises.

## Counters

- North-star: **6 of 9 SETTLED — 4 PASS, 2 FAIL — 3 pending (D, E, J).**
- Idea-level split: `0 ABSENT / 0 INERT / 1 BLOCKED (B)` **+ K unbucketed** — see below.
- **INERT surface by-catch: 4 in 6 trials** (new: item `on_drop`).
- INERT escalation counter (threshold 3): **0**.
- Nothing fixed. File-never-fix held, including at both P1s.

## Open protocol gap — NOT self-adjudicated

**Appendix A.6 under-specifies the mixed case K produced.** It rules that an idea counts as
INERT if *any* failing facet is INERT, but is silent on an idea whose failing facets are
**ABSENT and BLOCKED with no INERT among them** — exactly K (F1 ABSENT, F7 BLOCKED+ABSENT).
Trial B was cleanly BLOCKED, so the case had not arisen. K is recorded as **mixed
ABSENT/BLOCKED pending the owner's bucketing**, and `metrics.md`'s published split carries that
gap explicitly rather than resolving it silently. The INERT escalation counter is unaffected
either way.

## Reversal trigger

If `hamlet-9e1ae3b7a2` or `hamlet-a737e444c0` lands and a re-run turns F7 — or if an ambient
world-process surface is built and turns F1 — **the FAIL stands for this reading** (pinned
substrate, `PDR-0090`); the flip is Trend content, not a re-scoring. Boundary cases 6/7/8/9 are
recorded **deferred, not waived**: they become probeable if `hamlet-9e1ae3b7a2` lands, and a
future re-run must probe rather than assume them.

Separately: **two FAILs in six settled ideas puts the ≥80% target (8 of 9) out of reach for this
corpus.** At most 7 of 9 can now pass, which is 77.8% and misses. Per `PDR-0078` this is a
*finding about the substrate, not a failed bet* — acceptance is on the instrument. The reading
still does not publish until the ninth trial and both blind re-runs are recorded.
