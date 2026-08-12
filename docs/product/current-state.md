# Current State — HAMLET / Townlet        Checkpoint: 2026-08-13 · sixth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — freeze the current
system as an oracle, then knock down and rebuild one design-space unit at a time against it.
The **Provenance-integrity** guardrail's three original breaches are **all closed** (`ebb8fa85`);
the row goes green when the two filed adjacent gaps enter WS-7's known-divergences register
(`PDR-0028` routing). Selection criterion for what gets strangled next, owner-stated:
*"strangle wherever the runtime still knows what the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (2455 lines, binding). Two confident
diagnoses were corrected by design docs that existed the whole time — **check
`docs/architecture/` before concluding shipped behaviour is simply wrong.**

**WS-1's scope is FROZEN at ten units (`PDR-0028`).** Nine landed. New findings route by kind:
provenance-shaped → WS-7's register; authoring-surface-shaped → WS-4; else → triage.

## Owner state (2026-08-13)

- **Authority grant re-confirmed verbatim** by the owner this session ("confirmed, lets crack
  on") — the standard grant in `vision.md` stands unchanged; no vision edit was needed or made.
- **Nothing is blocked on the owner.** The only standing owner-gated item remains the README
  *push* (drafting and committing locally is endorsed).

## In flight

Recovery milestone **`hamlet-1ade187dcc`**, work streams WS-0…WS-7.

- **WS-1** `hamlet-67ffbd282a` (P0, claimed, `fixing`, lease to 2026-08-14T17:38Z) — **9 of 10
  units landed, tree green at every commit.** Order: ~~gates~~ → ~~a~~ → ~~d~~ → ~~bounds+norm~~
  → ~~new1~~ → ~~new2(5)~~ → ~~b(6)~~ → ~~c(7)~~ → **close(8) ← next**, plus sibling 3b
  (`hamlet-88acec4bb5`) which must land **before the oracle freeze** (task 8's gate does not
  wait on it). **Tasks b+c landed as one atomic commit (`97e4b16b`)**: the network is stateless
  (`initial_hidden` factory, `hidden` REQUIRED in forward), the population owns `rollout_hidden`,
  training threads hidden state through `_unroll_recurrent`, the post-training clobber is
  deleted, and every sampled-window boundary bootstraps from `next_observations[:, -1]` under
  its own unroll's final hidden (H6 order enforced, hidden states never crossed).
  `SequentialReplayBuffer` format_version 3→4 (`next_observations` REQUIRED); feedforward
  buffers untouched. Full suite **2977 passed, 0 failed**; all four gates green; four named
  mutations each caught by name. Tracker comment #125 carries the full landing record.
- **WS-7** `hamlet-e3af412673` (P0) — the strangler's enabling stream, blocked by WS-1. **The
  known-divergences register must be one of its FIRST artifacts** (`PDR-0028` reversal trigger
  fires on routing-to-nowhere; `PDR-0022`'s deletion condition depends on it).
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched.
- **WS-4 additions** (unchanged from fifth checkpoint): `hamlet-310e336786`,
  `hamlet-f46e2b381a`, `hamlet-fa6bb6da4a`, `hamlet-e979f2ba37` (`PDR-0026` acceptance shape),
  `hamlet-365e996511`, `hamlet-0dd4ac24d9`, `hamlet-0cdb8a6d1a` (`PDR-0024`).
  **`hamlet-0d0115383e` (per-level `architecture`, `PDR-0027`) is now UNBLOCKED** — its
  sequencing constraint was "after WS-1(b)/(c)", which landed this session. Still WS-4-scoped;
  do not fold into WS-1 (scope frozen).
- **Register-routed, NOT WS-1** (`PDR-0021`/`PDR-0028`): `hamlet-2dde1015fe` (nine dead hashes;
  precondition of the `config_hash_warning` deletion) and `hamlet-df2b972c49` (P1 — the two
  remaining stamp/compare paths).

## Open questions / blocked-on-owner

- **README push** remains the owner's call; drafting and committing locally is endorsed.
- **Nothing else is blocked on the owner.**
- Open, not blocking: the five shipped levels are three universes (WS-3 scoping input); the
  inert-surface baseline (~40) needs one itemized recount before the two counters can merge.

## What this checkpoint did

- **Landed WS-1 tasks b(6)+c(7)** as one atomic commit (`97e4b16b`), per plan §0 W1. Red
  verified in a detached worktree at `53d99d5f` (230/230 zero-gradient updates; BPTT depth [1];
  clobber 200/936; 100% of window boundaries collapsed to bare reward on the task-6-only tree);
  green verified by 9 pinning tests + full suite; **four mutations each caught by name**.
- **No new PDRs** — no product decision was made; pure execution inside `PDR-0028`'s frozen
  scope, accepted against the plan's definition-of-done. Owner re-confirmed the grant.
- **Metrics re-read**: Gates green 4 of 4 HELD (2977/0); BAC row annotated (recurrent training
  path fixed; surface count unchanged at 1 of 3). No reversal trigger fired.
- **Tracker reconciled live**: WS-1 heartbeated (lease 2026-08-14T17:38Z), landing comment
  threaded (#125). Roadmap WS-1 count corrected 7→9 (status only, no horizon change).

## Next session, start here

**Task 3b** (`hamlet-88acec4bb5`, sibling unit, spec in plan §0.1) — dead agents stop
transacting. Single file, single function (`ActionExecutor._execute_actions`, INTERACT block);
the two-name form (`interact_intent` / `interact_mask`) is verbatim-specified so it is not
"simplified" back to one; T4 passes on current production code — say so in the commit message;
H8-class note (env.dones IS prev_dones at execution time) goes in the commit message. Test
source of record: `docs/plans/2026-08-11-ws1-pinning-test-sources/test_dead_agent_interaction_gating.py`.
Then **task 8 — batch close**: closing black pass, ruff, mypy, `pytest -q` → 0 failed,
curriculum smoke record (task 3's L0_0 vs L0_5 shift AND task 3a's L1 economy revival),
`find configs -name '*.msgpack'` shows only per-level names, no `.pt` anywhere. Then WS-1
closes and **WS-7 unblocks** (register first).

Carry-ins that keep paying: purge `configs/**/*.msgpack` before every measurement; verify red
by mutation in a detached worktree (never `git stash` — operator hook); a green test is not
evidence, mutate before believing; enumerate producers, not call shapes; **enumerate one-arg
`forward()` call sites by grepping the call, not only by old-API symbol names** — the plan's
16-site migration count missed 3 sites in `test_network_factory.py` that only the full suite
caught; a correction is not self-verifying.

Do not re-litigate: `PDR-0006` (strangler), `PDR-0007` (universality), `PDR-0014`–`PDR-0016`
(bounds), `PDR-0022` (deletion, decided), `PDR-0026`–`PDR-0028` (owner-resolved). Read
`vision.md` first: ENDORSED, amended 2026-08-13 with owner sign-off, grant re-confirmed
2026-08-13; changing it further escalates.
