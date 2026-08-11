# Current State — HAMLET / Townlet        Checkpoint: 2026-08-12 · fourth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) — freeze the current
system as an oracle, then knock down and rebuild one design-space unit at a time against it.
Guarded by **Provenance integrity**, which was BREACHED in three places and is now **2 of 3
closed** (task 5 closes the third).

The owner's framing of what the strangler is *for*, recorded 2026-08-11: *"the original 'game
engine' needs to be strangled out by the engine engine"* — VFS and the dynamic engine parts are
the guiding star, not `health = 0..100`. That converts the strangler from an ordering question
into a **selection criterion**: strangle wherever the runtime still knows what the game is.

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS.** 2455 lines, current enough to be
binding, and it pre-answers questions that look open. Chapter 9 (normalisation) prescribes
`clipped_log_scaled` for money — already implemented, never wired — and states money is
normalised such that `1.0 ≈ $100`, which the shipped dollar-denominated configs contradict.
The owner's framing of what VFS is *for*, 2026-08-12: *"end users don't need to think too hard
about the mechanics under the hood, it's effectively like a 'complex type' that they can trust
to be enforced mechanically."* Authors declare **intent**; VFS owns the mechanics. Two
confident diagnoses have now been corrected by a design doc that existed the whole time —
**check `docs/architecture/` before concluding shipped behaviour is simply wrong.**

**Sequencing is deliberately open (`PDR-0019`, owner-stated).** WS-N numbering is an
**inventory, not a required order** — pin one system, then choose the next on the selection
criterion (*where does the runtime still know what the game is?*), not by stream number.
Observation encoding is a named live candidate (`PDR-0017`). Two constraints hold: **one system
at a time**, and the work must be **replacing, refactoring or fixing**. Real blocking edges
(WS-1 gates WS-7) are unaffected.

## In flight

Recovery milestone **`hamlet-1ade187dcc`**, work streams WS-0…WS-7.

- **WS-1** `hamlet-67ffbd282a` (P0, claimed, `fixing`) — **6 of 10 units landed, tree green at
  every commit.** Grew 7 → 10 units across two reviews (`PDR-0015`, `PDR-0016`).
  Order: ~~gates(1)~~ → ~~a(2)~~ → ~~d(3)~~ → ~~bounds+normalization(3a)~~ → ~~new1(4)~~ →
  **new2(5) ← next** → b(6) → c(7) → close(8), plus sibling `3b` (`hamlet-88acec4bb5`).
  **Provenance integrity: 2 of 3 breaches closed.** Task 5 closes the third.
- **WS-7** `hamlet-e3af412673` (P0) — the strangler's enabling stream. Blocked by WS-1.
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched.
- **WS-4** gained `hamlet-f46e2b381a` (`clamp_and_validate` declared-but-empty),
  `hamlet-fa6bb6da4a` (token observations, blocked by `hamlet-0d0115383e`),
  `hamlet-e979f2ba37` (author the curriculum — the five levels are three universes),
  `hamlet-365e996511` (`range_type` inert + money unit ambiguous, `PDR-0020`).
- **Filed, deliberately NOT in WS-1** (`PDR-0021`): `hamlet-2dde1015fe` (the dead-hash set is
  nine, not four) and `hamlet-df2b972c49` (P1 — two further checkpoint stamp/compare paths).
  Both must enter WS-7's known-divergences register before the freeze.
- **New this session, from the owner's framings:** `hamlet-0dd4ac24d9` (P1 — presentation is
  hardcoded by variable name; make it **declared**, honest by default, `PDR-0023`+`PDR-0025`) and
  `hamlet-0cdb8a6d1a` (P1 — **no model export path**; TASK-008 designed 2025-11, never built,
  `PDR-0024`). `hamlet-365e996511` is now **unblocked** and re-scoped to `range_type` alone.
  Two **Later** bets added to `roadmap.md` as intent: model+contract export, and the "locked"
  showcase experiment (the one place prettified presentation belongs).

## Open questions / blocked-on-owner

- ⚠️ **AMEND `vision.md`'s "Who it serves" to name the prototyping game developer?**
  (`PDR-0024`, **proposed** — `vision.md` NOT touched.) Owner-stated core use case: *game devs
  rapidly throwing a prototype together, getting a model and an interface contract, and taking
  the model to their own game code.* `vision.md`'s novice author *"watches agents attack it"* —
  the journey ends inside HAMLET. This one ends in the dev's own engine, and that handoff step
  is nowhere in the vision. It also exposes a metric gap: the north-star measures **authoring**
  cost, so a product could score perfectly and still be useless to a game dev who can't get the
  model out. **Accept, alter, or reject the proposed wording.**
- ⚠️ **`config_hash_warning` — delete it, or make it raise?** (`PDR-0022`, **proposed**) The plan
  contradicts itself: §0's W4 says resolve it this batch, task 4's text says don't touch it. A
  *warning* is the silent acceptance the Provenance guardrail forbids — but `config_hash` is the
  broadest signal we have, covering five surfaces that have no hard check of their own. My
  recommendation is **delete**, conditional on `hamlet-2dde1015fe` entering the known-divergences
  register. Task 5 needs the answer to state its final check count.
- ⚠️ **`vision.md`'s FLAGSHIP DEMONSTRATOR IS NOT IMPLEMENTED — does that change the vision, or
  the packs?** `vision.md:94` calls "Low Energy Delirium" *"the flagship demonstrator of the
  substrate: the proof that the thing works."* Measured 2026-08-12 (`PDR-0018`): `L0_0` and
  `L0_5` `drive.yaml` are **byte-identical**, both `constant_base_with_shaped_bonus`, and **no
  shipped level declares a `multiplicative` extrinsic** — the contrast the lesson needs has never
  existed. `vision.md` is ENDORSED and was **not** touched. This is the owner's call.
- ⚠️ **WHEN DO WE STOP ADDING TO WS-1 AND FREEZE?** WS-1 has grown 7 → 10 units. Each addition
  was justified individually and none was optional under `PDR-0012`. `PDR-0014`'s reversal
  trigger 2 (*"the bounds wiring materially delays the oracle freeze"*) is **approaching, not
  definitively tripped**. `PDR-0018` removes the largest reason to go slowly — there is no
  calibrated behaviour at risk — so the argument now leans toward freezing sooner.
- **Design fork inside `PDR-0009`** — per-level `architecture` override, or make `brain.yaml`
  level-overridable the way `training.yaml` is? Now has **three** consumers (`PDR-0017`,
  `PDR-0018`). A level cannot currently vary its grid *or* its brain, which bounds what any
  curriculum can express. Decide before implementing.
- **README push** remains the owner's call; drafting and committing locally is endorsed.
- **Open, not blocking** — the five shipped levels are **three universes**, a thin coverage set
  for WS-3's differential harness. An input to WS-3 scoping; does **not** reopen `PDR-0006`.

Closed: the poisoned-cache hazard (WS-1(a) landed); CUDA blocked (was an unused dependency);
*"what is the real test coverage?"* (**81%**, `PDR-0010`); *"who re-authors the packs?"* —
**premise was false** (`PDR-0018`), the packs were never tuned, so there is nothing to re-author;
authoring one for the first time is filed as `hamlet-e979f2ba37` (WS-4, downstream of the freeze).

## What this checkpoint did

- **Landed 6 of 10 WS-1 units** — gates (`c2f61beb`), cache identity (`22b7616d` + `cf122ff1`),
  declared costs gate (`30c433e3`), bounds + normalization (`7065729a` + `174914d3`), content
  hashes + effective `brain_hash` (`31c17111` + `39026beb`) — plus an unplanned dependency
  remediation (`e082afd5`). Full suite **2962 passed, 0 failed**; all four gates green.
  *(This section spans work since the last formal checkpoint, not one session.)*
- **Recorded `PDR-0015` … `PDR-0022`.** Since the last formal checkpoint: 0018 (the packs are
  test infrastructure, never a curriculum — two escalations corrected, a larger one raised),
  0019 (sequencing is open: pin one system, then float), 0020 (`vfs.md` is design authority; the
  money diagnosis was wrong — `range_type` is inert, not the ceiling), 0021 (task 4's two adjacent
  provenance gaps are filed, **not** folded into WS-1), 0022 (**proposed** — `config_hash_warning`).
- **Adversarial orchestration ran four times and changed the work every time.** Recon before
  task 4 found its spec's change 1 was a `TypeError` as written (§0.3). Verification after found
  three weak tests — including one where a wrong-level `brain_hash` left **all 2957 tests green**.
  Three refuter agents died on a rate limit; all three of their findings were about my own tests,
  and all three held when I re-measured by hand.
- **Moved two guardrails for the first time since May** — Gates green **1 of 4 → 4 of 4**, and
  Provenance integrity **1 of 3 breaches closed**. Also first movement on Config-surface
  coverage, and the first Pre-release hygiene recount since 2026-05-16.
- **Used adversarial verification twice, and it paid both times** — it caught a real miss in my
  own task 2 fix (`metadata_for_level`, found independently by two agents), and recon before
  task 3a overturned **four** of its spec's claims including three wrong red-baseline literals.

## Next session, start here

**Implement task 5** (`hamlet-1029f99f4b`) — route the serving path through the shared identity
guard. **Breach 3 of 3**, and the last WS-1 provenance unit. Plan §2 task 5, and read **§0.3
corrections 13, 19 and 21 first** — they are task-5-relevant:

- **Task 5 owns `assert_checkpoint_identity`**, which does not exist yet (its only mention in
  the repo is a comment at `checkpoint_utils.py:36`). Task 4's D5 test deliberately stops at
  stamp-plus-collision; the `pytest.raises(match="primary_level")` leg is task 5's, and it
  must run against a pack whose L1 `run_metadata.output_subdir` is normalised to L0_5's —
  otherwise `training_hash` fires first and the test passes for the wrong reason.
- **Ordering hazard, live right now:** task 4 deleted `runner.py`'s dead `brain_hash` write but
  deliberately left the `if universe is not None:` gate for task 5. Until task 5 lands, a path
  where `universe is None` writes a checkpoint with **zero** provenance keys.
- **`config_hash_warning` is unresolved and escalated** — §0's W4 says resolve it in this batch,
  Task 4's text says don't touch it. §0 outranks task text, but "resolve" ≠ "delete". Options:
  delete it (now largely redundant) or make it raise (a *warning* is the silent acceptance the
  guardrail forbids, and `config_hash` is the broadest signal we have). **Owner's call.**

**Task 4 is done** (`31c17111` + `39026beb`) — the four content hashes stamped and hard-compared,
`brain_hash` now covering the effective config at the primary level. Recon (42 agents) overturned
enough of the spec that §0.3 exists; verification (15 agents) refuted 8 findings and lost 3 to a
rate limit, all 3 about my own tests, all 3 upheld on re-measurement and fixed.

**Task 3a is done** (`7065729a` + `174914d3`) — bounds at all six runtime sites *and* the VFS
normalization ABI given its first production callers. Measured on L1: money `1.000000 →
22.500000` per tick, money affordances `1 of 7 → 7 of 7`.

Carry these into task 5:

1. `find configs -name '*.msgpack' -delete` before **every** measurement, red and green —
   provenance uses `git rev-parse HEAD` and ignores dirty state.
2. **Verify red by mutation in a detached worktree**, never `git stash` (hard-blocked by an
   operator hook that has caused silent work loss). `git worktree add --detach <path> HEAD`,
   copy the test in, run with `PYTHONPATH=<wt>/src` and the main venv's python.
3. **A green test is not evidence.** Three units running, **five** weak tests found by mutating
   the implementation and re-running — and in task 4 the three that mattered most were found
   only because three refuter agents died on a rate limit and I re-measured their findings by
   hand instead of dropping them. Mutate before believing.
4. **Run review agents in isolated worktrees** (`isolation: 'worktree'`). Task 3a's pass ran
   mutations in the live tree while another agent was reading it; task 4's left four stray
   worktrees behind when it was killed mid-flight. Nothing was lost either time, but neither
   was by design.
5. **A correction is not self-verifying.** §0.3 correction 17 came out of a pass whose whole
   purpose was catching wrong spec claims — and was itself wrong (retracted in place). An
   "X is inert" claim needs the same measurement as the claim it replaces.

**A recurring lesson, now seen three times — carry it into task 5 and into
`hamlet-df2b972c49`, which both touch exactly this kind of structure:** grep finds *the shape of a call*, not the set of places a
value is produced. `grep torch.clamp(` missed compile-time tuple literals. `grep
UniverseMetadata(` missed a `dataclasses.replace()`. A grep against a *documented* filename
(`drive_as_code.yaml`) returned zero hits and falsely confirmed a claim, because every pack
actually uses `drive.yaml`. **Enumerate producers, not call shapes.**

**A fourth instance, in a new costume (`PDR-0018`): a name is not evidence of the thing it names.**
Five directories named for five pedagogical stages contained three universes; I escalated a
question premised on their being tuned without running the one `diff` that refutes it. Before
escalating on a property of an artifact, verify the artifact has that property.

Do not re-litigate `PDR-0006` (strangler), `PDR-0007` (universality), `PDR-0014`/`PDR-0015`
(bounds scope) or `PDR-0016` (bounds+normalization together) — all decided on measured evidence.
Read `vision.md` first: it is ENDORSED, and changing it escalates.
