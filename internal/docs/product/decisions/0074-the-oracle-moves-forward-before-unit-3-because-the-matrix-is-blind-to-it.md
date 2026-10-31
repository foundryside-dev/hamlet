# PDR-0074 — The oracle moves forward to `4222a917` before unit 3, because the register's suppression has reached its ceiling AND the matrix cannot see unit 3 at all

Date: 2026-08-17   Status: **accepted** (autonomous, within grant — a harness/instrument
change inside the Now bet, the same class as `PDR-0030` and `PDR-0056`; the owner chose *"re-tag
question, then unit 3"* as the session's first DECIDE item at the resume, and this PDR is the
answer. Reported to the owner in-session before any dependent work; not a vision, strategy or
grant change.)
Author: Claude (standing product owner)
Owner sign-off: the *question* was owner-sequenced; the *call* is the agent's under the grant.

Related: `PDR-0056` (the trigger this answers: *"re-tag the oracle if a THIRD cut needs to widen
`hash_fields` again … both costs above dissolve when the tag moves"*), `PDR-0030` (the pin, and
its own trigger: *"move the oracle forward — new tag, old tag retained, register re-stamped"*),
`PDR-0058` (exit condition 1 — every entry terminal; condition 2 — the verdict vocabulary
re-earned; trigger 1 — a knockdown the harness cannot adjudicate; trigger 2 — a register that
only grows), `PDR-0052` (silent-and-green is the failure the fixtures guard against),
`PDR-0037` (record-then-bind), `PDR-0019` (one system at a time), `PDR-0073` (`main` =
`4222a917`, gates read green there)
Tracker: `hamlet-f0ed709ecf` (unit 3, the cut this sequences behind the re-tag);
WS-7 `hamlet-e3af412673` owns the tag. The re-tag unit is filed as a WS-7 child.
Register: DIV-003, DIV-004, DIV-005 → `retired` at the new tag; DIV-001, DIV-002 re-stamped;
DIV-006 (unit 3) is written against the NEW tag, not the old.

## Context — two facts, read at ORIENT, that together decide it

**1. `PDR-0056`'s trigger does not fire by its letter, and that is the worrying part.** The
trigger fires when a third cut *widens* `hash_fields`. Unit 3 will not widen it — because **no
matrix cell can see unit 3.** `configs/default_curriculum/vfs_profiles.yaml` and all three
`configs/differential/` packs declare `variables: []`; unit 3 splits the `obs_vfs` block that
those packs never populate. Run the 16-cell matrix after the cut and it will read exactly as
it reads today — 16/16 `DIVERGED_AS_REGISTERED (DIV-004)`, streams byte-identical — while
measuring nothing about the change. That is `PDR-0052`'s silent-and-green shape and the very
thing `PDR-0058` trigger 1 names (*"a knockdown the harness cannot adjudicate at all"*), not
because the instrument is broken but because it is pointed at packs that do not exercise the
surface. The nine packs that do (`configs/reference/model_pack` with 5 profile variables and a
level; `configs/test/items_smoke`, `effects_smoke`, and six single-file VFS fixtures) are not
in the matrix.

So unit 3 needs a **new matrix cell** on a pack that declares profile variables. At the current
tag that cell would carry **three stacked hash suppressions** — DIV-004 and DIV-005 (the frozen
fixture is at the pre-`clip`, pre-`range_type`, pre-`semantic_type` schema) plus DIV-006 — on
the *only* cell that can see the cut, with `AGREE` unreachable there as everywhere.

**2. `PDR-0056`'s two recorded costs are at their ceiling and every WS-4 unit adds to them.**
Since 2026-08-15: `AGREE` is unreachable on all 16 cells; the pack-drift guard is armed on
zero cells; exit 0 means *"everything diverged exactly as registered"* and nothing stronger.
DIV-005 stacked on DIV-004 without widening the set only because it happened to move the same
four hashes. Every remaining WS-4 unit that touches an observation field will do the same, and
`PDR-0058` trigger 2 (*"the register grows for two consecutive checkpoints without an entry
going terminal"*) is armed at growth #1. Left alone, "retire the oracle" is a receding horizon.

The transitive argument that makes moving forward safe was earned cut by cut: DIV-003 was
adjudicated with all six crash cells flipping to `DIVERGED_AS_REGISTERED` and every standing
cell byte-exact; DIV-004 and DIV-005 were each measured with exactly the declared hashes moved
and **every stream byte-identical** on CPU and CUDA. The tree at `4222a917` therefore *is* the
tree at `0e875d7a` modulo the register — which is precisely what a new oracle tag asserts.

## Options

1. **Keep `oracle-2026-08-13`; add DIV-006 and a new cell.** Preserves the pre-programme
   reference; costs a third suppression on the one cell that matters and leaves `AGREE`
   unreachable and the drift guard disarmed indefinitely. Rejected: it accumulates exactly what
   `PDR-0056` said to stop accumulating, and the new cell's evidence would be the weakest kind.
2. **Move the oracle forward to `4222a917` first; then unit 3 against it.** Chosen.
3. **Move forward AFTER unit 3.** Rejected on `PDR-0037`'s order: the tag is the pre-cut
   reference; a cut needs its oracle before it happens, and unit 3's DIV-006 written against
   the old tag would be retired the moment the tag moved — work that documents nothing.

## The call

**`oracle-2026-08-17` → `4222a917`** (the tip of `main`; the tree `PDR-0073` merged, whose
`Lint`, `Tests` and `Config Validation` are green on the PR's own runs and on the push to
`main`). The old tag stays as history, per `ORACLE.md`. `4222a917` rather than the branch tip
because the two trees differ only under `docs/product/`, and an oracle that *is* `main` is
inspectable by anyone and survives becoming `main` (`PDR-0072`'s rule).

The re-tag is one unit of WS-7, and it is not "just move a string." Its scope, in the order the
register's own discipline demands:

1. **Evidence at the tagged commit, re-earned, not inherited** (`ORACLE.md` § *Evidence*):
   gates read at `4222a917` (CI already: `Tests` 3239/24/0 deselected, `Lint`, `Config
   Validation` — recorded by run id); **determinism re-verified locally CPU and CUDA at that
   commit** through the JIT vtc kernels — the one claim CI does not make.
2. **Register re-stamped.** DIV-001 and DIV-002: oracle behaviour re-verified at `4222a917`
   (`hamlet-2dde1015fe`, `hamlet-df2b972c49` are still open, so it is expected to be present) →
   `tag-stamped` at the new tag. DIV-003, DIV-004, DIV-005 → **`retired`** (*"the divergence
   dissolved"*): the new oracle carries the rebuilt behaviour, so old and new no longer differ.
   Their entries stay in the file with their evidence; the lifecycle line changes.
3. **`oracle_fixtures/` re-frozen** as byte copies of the live packs, so the freeze is a
   provable no-op again (`test_the_freeze_is_a_provable_no_op_today` goes back to meaning it).
   Every standing cell drops `pack_divergence` and `hash_divergence`; the six DIV-003 cells drop
   `expected` and become plain standing cells (those configs run at the new tag).
4. **The matrix gains at least one cell that exercises VFS profile variables** —
   `configs/reference/model_pack` (5 variables, a level) is the first candidate; `items_smoke`
   for item-slot variables if it runs through the driver. Their status at the new tag must be
   **`AGREE`**, which is what proves the cell can see before unit 3 asks it to.
5. **`ORACLE_TAG`, its pinning test, `ORACLE.md`, `README.md:36-37`**, and the
   `.oracle/oracle-2026-08-17` worktree. The tag is annotated and pushed with the branch
   (`PDR-0030` precedent; `PDR-0046` covers the push).
6. **Acceptance:** the full matrix at the new tag on CPU and CUDA reads **`AGREE` on every
   cell, zero suppressions declared, exit 0** — the first time since 2026-08-15 that exit 0
   means "old and new agree". Only then does unit 3 begin, and DIV-006 is the *sole* entry on
   the profile-variable cells.

## What this changes in the exit reading (`PDR-0058`)

- **Condition 1** (every entry terminal): DIV-003/004/005 go terminal by retirement; DIV-001/002
  remain `tag-stamped` and are closed by their own rebuilds (their tracker issues are open).
- **Condition 2** (verdict vocabulary re-earned): **met at the moment of acceptance above** —
  `AGREE` is reachable and read matrix-wide. It stays met only until DIV-006 is declared, and
  then only on the profile-variable cells; that is what "narrow suppression" looks like.
- **Condition 3**: unchanged (`PDR-0073`; the nightly reading is still owed).
- **Trigger 2's counter resets**: three entries go terminal in one checkpoint.

## What is deliberately given up

The ability to diff a *future* rebuild directly against pre-normalization-programme behaviour.
That preservation was verified at each cut and recorded (DIV-004/005 entries, runs
`20260815-175940`, `20260815-180022`, `20260816-225750`); the new tag inherits it
transitively. If a future finding claims the programme silently changed behaviour, the old tag
and its worktree still exist and the comparison can be re-run by hand — it is no longer the
harness's default reference, that is all.

## Reversal trigger

- **Do not tag at `4222a917`** if the CPU+CUDA determinism check fails there. That is a
  pre-tag defect on `ORACLE.md`'s own terms: fix first, tag after the fix — never tag a
  non-deterministic tree as the specification.
- **Stop before unit 3** if any cell — including the new profile-variable cell(s) — reads
  anything but `AGREE` at the new tag with zero suppressions. The transitive claim is then
  false somewhere, and diagnosing that outranks the cut.
- **Reopen the instrument, not the tag,** if a *second* forward move is needed for the same
  reason (suppression accumulation) within the remaining WS-4 queue. Tag-chasing every few
  units means the hash-only register shape is the wrong instrument for a stream whose whole
  purpose is moving hashes; `PDR-0058` condition 2's "successor recorded" is then the answer.
- **Reopen this call** if the owner reads a forward move as weakening the strangler's
  preservation guarantee rather than banking it. The transitive argument is mine; the risk
  appetite is theirs.

## Executed (same session, 2026-08-17)

- Tag `oracle-2026-08-17` → `4222a917` created (annotated) and its worktree at
  `.oracle/oracle-2026-08-17`. Evidence re-earned at that tree: CI `Tests` `31971043702`
  (3239/24/0 deselected), `Lint` `31971043734`, `Config Validation` `31971043687`; local
  `test_determinism.py` 5 passed / 0 skipped (CUDA ran). Trigger 1 did not fire.
- DIV-001/002 re-verified and re-stamped at `4222a917`; DIV-003/004/005 `retired`.
- `oracle_fixtures/` re-frozen as byte copies (`default_curriculum`, the three differential
  packs) and two new fixtures added (`items_smoke`, `effects_smoke`); the matrix is 20 cells
  with no declaration on any cell; `ORACLE_TAG` moved; README and `ORACLE.md` updated.
- `configs/reference/model_pack` was the first-choice profile-variable cell and **does not
  compile** (`spawn_effect` schema rot) — filed `hamlet-7cd887c9e5`; `items_smoke` (item-scope,
  `obs_vfs` width 3) and `effects_smoke` (global-scope, width 1) used instead.
- **Acceptance: run `20260817-072714`, 20/20 `AGREE` on CPU and CUDA, exit 0.** Trigger 2 did
  not fire. Exit condition 2 (`PDR-0058`) reads **met** at this tree. Unit 3 may begin, with
  DIV-006 written against `oracle-2026-08-17` and bound on the four profile-variable cells only.
