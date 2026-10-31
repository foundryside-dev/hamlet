# VFS + compiler re-review: shared brief

You are a FRESH reviewer. You did not write or verify any of this code. Your verdict decides whether
the VFS and the universe compiler are "green": done enough to lock before the project moves on to
UaC (items/rewards), strata, effects and an end-to-end shakedown.

## The green bar
A subsystem is green when a fresh review finds:
- no P1: wrong behaviour, a crash or silent corruption reachable from an authored pack, or a broken determinism or isolation contract;
- no P2: a claimed or documented contract that doesn't hold, a compile that accepts what the runtime can't serve (a crash at step), a missing refusal, a no-defaults or name-branch violation (CLAUDE.md, PDR-0045), or an unlocated error;
- no spec gap that makes a reasonable mechanic unauthorable without editing Python, where that gap
  is in VFS or compiler scope (not in effects, strata or the training loop, which are later phases).
P3 (nits, doc drift, dead code, perf) does not block green; list it.

## Scope
- In scope: `src/townlet/vfs/`, `src/townlet/universe/` (the compiler, DTOs, validation, cache, CLI), `src/townlet/world/expression/`, the VFS-facing parts of `src/townlet/environment/vectorized_env.py`, `environment/token_publishers.py` and `environment/dac_engine.py` (reads only), and `src/townlet/config/` DTOs as the authoring surface. The docs under test are `docs/config-schemas/{variables,declarations,expressions,transition_rules}.md` and `docs/architecture/{VFS,COMPILER}.md`.
- Out of scope, so don't file it: effects-engine internals beyond how they read VFS, items gameplay, substrate math, the training loop, the population or replay, and the frontend.

## Owner rulings you must not re-litigate
- S1: the batch is N independent single-agent worlds; `global` is per world; pair, message, group, zone and agent_private are deleted.
- Zero backwards compatibility: old configs must fail loudly. No-defaults: `extra="forbid"`, everything explicit.
- Never branch on a variable's name (PDR-0045). Engine names (`tick`, `agent_id`, effect locals) are reserved, not domain names.
- One spelling: `x` is a variable, `bar.m` is a meter, `item.x` is bound item state. Every other spelling refuses.
- Hash movement is free (no checkpoints exist).
- Deferred to the owner, so don't file: meters becoming pointers to VFS variables, bounds and breach policy, the nine-field declaration redesign.

## Known items (do NOT re-report as new; DO classify each against the bar)
Read these first:
- `PHASEA_FOLLOWUPS.md`: the running follow-up list from the sprint.
- `phaseB/verify_B3/RESULTS.md`, `phaseB/verify_B4/RESULTS.md`, `phaseB/verify_B4/RESULTS_repair.md`: verifier records. Defects there were repaired unless the follow-up list says otherwise.
- `findings_vfs.md`, `findings_compiler.md`, `gaps_vfs.md`, `gaps_compiler.md`: the ORIGINAL review that started this sprint. For each finding, say whether it is CLOSED (with evidence), OPEN, or SUPERSEDED.
All are in /tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/.

## Method
- Work in a detached worktree at the SHA you are given, under `scratchpad/rereview/<your-lens>/wt`. Never edit /home/john/hamlet. Never use `git stash`. Remove the worktree at the end.
- Evidence means a probe that runs (a pack fragment that compiles, then a step) or a precise source citation. Do not cite docs as evidence that something is implemented.
- Prefer authored-pack repros: build a minimal pack in scratch (copy `configs/default_curriculum` or `configs/test/*` and edit it), compile it with `UniverseCompiler().compile(path, primary_level=...)`, construct the env, and step it.
- Put probes in `scratchpad/rereview/<lens>/probes/` and write the full record to `scratchpad/rereview/<lens>/REVIEW.md`.

## Output (your final hand-back)
1. VERDICT for your lens: GREEN, or NOT GREEN with the blocking items.
2. NEW findings, most severe first: severity, one-line claim, repro (a command, or a pack fragment plus steps), and file:line.
3. Known-item classification: one line each (id or short name, then P1/P2/P3/closed, then why).
4. Original-review closure table for your lens.
5. What you did not cover.
