# Current State — HAMLET / Townlet        Checkpoint: 2026-08-13 · fifth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — freeze the current
system as an oracle, then knock down and rebuild one design-space unit at a time against it.
The **Provenance-integrity** guardrail's three original breaches are **all closed** as of
`ebb8fa85`; the row goes green when the two filed adjacent gaps enter WS-7's known-divergences
register (`PDR-0028` routing). Selection criterion for what gets strangled next, owner-stated:
*"strangle wherever the runtime still knows what the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (2455 lines, binding). Two confident
diagnoses were corrected by design docs that existed the whole time — **check
`docs/architecture/` before concluding shipped behaviour is simply wrong.**

**WS-1's scope is FROZEN at ten units (`PDR-0028`).** Seven landed. New findings route by kind:
provenance-shaped → WS-7's register; authoring-surface-shaped → WS-4; else → triage. The
three-part exception clause is in the PDR; two of three is a filed issue, not a WS-1 unit.

## The owner cleared the escalation queue (2026-08-13)

All four blocked-on-owner questions were answered in one session — record of each:

- **`PDR-0022` accepted**: `config_hash_warning` **deleted** (done, in `ebb8fa85`), conditional
  on `hamlet-2dde1015fe` entering the register. Task 5's check count was four.
- **`PDR-0024` accepted with alteration**: audience **widened** — *"anyone interested in game
  dev, simulations, or modelling the real world in an abstract way."* `vision.md` amended
  (owner-approved): **the prototyping modeller** is a core use case; they leave with a model +
  interface contract. Export cost is now an `UNMEASURED` input metric.
- **`PDR-0026` (new)**: the flagship-demonstrator claim was **mis-tensed intent, not a false
  claim** — *"the idea outran the codebase"*; Townlet Town is one of several tech demos at
  release. `vision.md` re-tagged (owner-approved). Vehicle: `hamlet-e979f2ba37`, with a tripwire:
  if authoring the LED contrast needs Python, escalate immediately — the flagship demo would be
  an authorability counterexample.
- **`PDR-0027` (new)**: `PDR-0009`'s fork resolved — `brain.yaml` becomes **level-overridable**
  like `training.yaml`, PLUS owner's acceptance criterion: a brain override **forks the lineage
  and the fork must be legible at load** (*"I shouldn't be downloading/loading an experiment and
  then finding out it's not what I thought it was"*). `hamlet-0d0115383e` re-scoped; still after
  WS-1(b)/(c).

## In flight

Recovery milestone **`hamlet-1ade187dcc`**, work streams WS-0…WS-7.

- **WS-1** `hamlet-67ffbd282a` (P0, claimed, `fixing`) — **7 of 10 units landed, tree green at
  every commit.** Order: ~~gates~~ → ~~a~~ → ~~d~~ → ~~bounds+norm~~ → ~~new1~~ → ~~new2(5)~~ →
  **b(6) ← next** → c(7) → close(8), plus sibling 3b (`hamlet-88acec4bb5`).
  **Task 5 landed (`ebb8fa85`)**: serving path routes through the new shared
  `assert_checkpoint_identity`; D5 cross-level rejection done end-to-end; `config_hash_warning`
  deleted; both `runner.py` silent skips gone; `unified_server` raises on dead startup.
  `hamlet-1029f99f4b` CLOSED. Full suite **2969 passed, 0 failed**; all four gates green.
- **WS-7** `hamlet-e3af412673` (P0) — the strangler's enabling stream, blocked by WS-1. **The
  known-divergences register must be one of its FIRST artifacts** (`PDR-0028` reversal trigger
  fires on routing-to-nowhere; `PDR-0022`'s deletion condition depends on it).
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched.
- **WS-4** additions: `hamlet-310e336786` (NEW — `AdversarialCurriculum` hardcodes the six bar
  names into engine logic; promoted from the expiring observation; the selection criterion made
  literal), `hamlet-f46e2b381a`, `hamlet-fa6bb6da4a`, `hamlet-e979f2ba37` (now carries
  `PDR-0026`'s acceptance shape), `hamlet-365e996511`, `hamlet-0dd4ac24d9`, `hamlet-0cdb8a6d1a`
  (audience widened, `PDR-0024`).
- **Register-routed, NOT WS-1** (`PDR-0021`/`PDR-0028`): `hamlet-2dde1015fe` (nine dead hashes;
  precondition of the `config_hash_warning` deletion) and `hamlet-df2b972c49` (P1 — the two
  remaining stamp/compare paths: `_validate_checkpoint_compatibility` at `runner.py:181` unpickles
  before any universe exists, and `VectorizedPopulation.get_checkpoint_state/load`).

## Open questions / blocked-on-owner

- **README push** remains the owner's call; drafting and committing locally is endorsed.
- **Nothing else is blocked on the owner.** First time since 2026-08-11.
- Open, not blocking: the five shipped levels are three universes (WS-3 scoping input); the
  inert-surface baseline (~40) needs one itemized recount before the two counters can merge.

## What this checkpoint did

- **Landed task 5** (`ebb8fa85`) — breach 3 of 3 closed; verified red on the pre-fix tree
  (B2/B4/B5 fail exactly as the A/B predicted) and by four named mutations, all caught.
- **Recorded the owner's four resolutions**: `PDR-0022`/`PDR-0024` proposed→accepted (in place,
  with Resolution sections); `PDR-0026`–`PDR-0028` new. `vision.md` amended twice, both
  owner-approved, amendment log updated.
- **Tracker reconciled live**: `hamlet-1029f99f4b` closed with commit anchor; decision comments
  threaded to six issues; the expiring observation promoted (`hamlet-310e336786`); WS-1
  heartbeated.
- **Metrics re-read**: Gates green 4 of 4 held (2969/0); Provenance 3 of 3 closed, row not yet
  green; inert-surface counter canonicalized; export-cost input added (`UNMEASURED`). No
  reversal trigger fired; `PDR-0014` trigger 2 retired unfired by `PDR-0028`.

## Next session, start here

**Task b(6)** — thread LSTM hidden state so the recurrent weights actually train. Plan §2 task 6,
and §3 hazards H3 (vacuity guard is an acceptance condition), H6 (task 7 amends this test —
blocking), H7 (do not "simplify" `batch_size 12 ≠ population 8`), H8 (`no_grad`/return
placement). **Tasks 6+7 are one atomic merge unit (§0 W1)** — the tree is red between them by
design; do not treat task 6's intermediate failure count as a target. Pinning-test source of
record: `scratchpad/PINNING_TEST_b_FINAL_test_recurrent_bptt_runtime.py`.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before every measurement; verify red by
mutation in a detached worktree (never `git stash` — operator hook); a green test is not evidence,
mutate before believing; enumerate producers, not call shapes (it found the third loader this
session — already filed as `hamlet-df2b972c49`); a correction is not self-verifying.

Do not re-litigate: `PDR-0006` (strangler), `PDR-0007` (universality), `PDR-0014`–`PDR-0016`
(bounds), `PDR-0022` (deletion, decided), `PDR-0026`–`PDR-0028` (owner-resolved). Read
`vision.md` first: ENDORSED, amended 2026-08-13 with owner sign-off; changing it further
escalates.
