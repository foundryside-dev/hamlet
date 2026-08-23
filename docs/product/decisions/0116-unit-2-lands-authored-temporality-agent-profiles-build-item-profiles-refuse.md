# PDR-0116 — Unit 2 lands authored temporality: the engine tick, live evaluation, agent profiles BUILD, item profiles REFUSE; the register is caught up (DIV-009/DIV-010)

Date: 2026-08-23   Status: **accepted** (within grant: the spec — owner-approved under
`PDR-0114` — explicitly delegated the profile-evaluation scope decision to "unit 2's
plan"; everything else executes the approved spec)
Author: Claude (standing product owner)
Related: `PDR-0114` (spec §6 unit 2, rescoped-as-build), `PDR-0115` (the drift discharge
this executes), `PDR-0045` (declare-don't-hardcode — the temporal block un-freezes),
`PDR-0037`/`PDR-0033` (register discipline)
Tracker: `hamlet-fa6bb6da4a` (comments 236–242) · Commits: `3b72c4c4..30f94f93` (pushed)
Closed: `hamlet-5cc071f4b6`, `hamlet-df3a96bbac`, `hamlet-5d74335111`, `hamlet-bc0a5deeff`
Opened: `hamlet-5628884d7d` (pre-existing test flakiness, controlled at pre-unit commit)

## Context

Ruling 6 of `PDR-0114` ("no hardcoded temporality") had no machinery: no tick variable,
mark-gated evaluation inert on shipped defaults, agent/item profile expressions never
evaluating (three distinct inertness modes), two parallel temporal bookkeepings. Unit 2
built it — seven subagent-driven tasks, three verified fix rounds, final whole-unit
review "ready to merge" after one fix wave.

## The calls

1. **Register catch-up first (`PDR-0115`'s discharge):** the drift was measured per-commit
   (DIV-004's worktree method), which CORRECTED unit 1's hypothesis — three movers
   (`7cbfbff8` actions_hash, `cd3557b6` transition_graph→vfs_hash, `390769af`
   pack_brain_hash), three non-movers, one self-cancelling lockstep fixture re-freeze.
   Registered as **DIV-009**; cells bind composed declarations (new mechanism: a cell
   holds a TUPLE of hash divergences); matrix returned to exit 0 before the unit built
   anything. **DIV-008 stays visibly reserved** for the token cut.
2. **The engine tick** is an always-on, engine-written VFS global, ambient as bare `tick`
   in profile expressions, written at ONE pinned point (top of `step()`). **Semantics
   ruling:** the registry tick is the counter of the step being computed (pre-increment);
   a post-step read shows `global_tick - 1`. That IS the contract — every consumer of a
   step sees one value — and the plan's contrary test assertion was the defect.
3. **`time_of_day` derives from `global_tick`** at the same update point — proven
   byte-identical by independent induction and by the matrix.
4. **Evaluation marks derive from exposure** (expression variables only). Statics are
   STORAGE in every mode: never marked, never written back, and the evaluator's own
   context protected (a review empirically caught dependency-chased statics clobbering
   engine writes; fixed at three layers, pinned by tests). EAGER's old registry-level
   static reinit ended deliberately under this rule.
5. **The delegated scope decision (spec §6 unit 2 (d)): agent profiles BUILD NOW** (same
   compiled machinery, second evaluation call, exact `(num_agents,)` loud write-back) —
   `hamlet-5d74335111` closed; **item profiles REFUSE at compile** (no evaluator exists,
   zero users; evaluate-or-refuse, never silently inert) — `hamlet-bc0a5deeff` closed.
   `hamlet-df3a96bbac` (shipped-default inertness) closed by (4).
6. **DIV-010** registered for unit 2's own provenance movement (exactly
   `variable_schema_hash` + `vfs_hash`; `observation_schema_hash` confirmed unmoved).

## Acceptance evidence

Matrix exit 0 in BOTH modes (runs `20260823-043109` plain, `20260823-043209` scripted);
all 20 trace pairs independently byte-diffed identical (the scripted L3 cell is the
dynamics proof for the temporal change); mypy clean; 3302 unit+integration tests passing;
the one recurring flaky failure reproduced identically at pre-unit-2 `11dee204`
(controlled: pre-existing, filed `hamlet-5628884d7d`). Carry-forwards to units 3/5 are
banked on the tracker (comment 242), not in session memory.

## Reversal triggers

1. An authored pack legitimately needs an agent-profile CONSTANT expression or an
   item-profile expression before an item evaluator exists → the refuse rulings reopen
   (the fix is a build, not a fallback).
2. Unit 5's pack authoring finds the pre-increment tick semantics author-hostile (the
   one-tick observable lag confuses real `day_phase` authoring) → the write-point pin
   reopens; the differential harness makes any change visible.
3. An EAGER debug workflow turns out to depend on registry-level static reinit → ruling
   (4)'s EAGER half reopens as a declared debug flag, never a silent default.
