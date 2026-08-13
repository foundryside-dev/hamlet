# Current State — HAMLET / Townlet        Checkpoint: 2026-08-13 · eighth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). **THE ORACLE IS
PINNED: tag `oracle-2026-08-13` → `0e875d7a`** (`PDR-0030`, owner-endorsed GPU-first
sequencing). The tagged tree is now the spec for preserved behaviour; the freeze record is
`docs/oracle/ORACLE.md`, the register `docs/oracle/known-divergences.md` (DIV-001/DIV-002,
tag-stamped). WS-7 (`hamlet-e3af412673`, claimed by claude, in progress) has contents 1
(determinism), 2 (oracle tag) and 4 (register) **done**; remaining: **3 — differential
harness** (reshapes WS-3) and **5 — per-unit seam cutting**. Selection criterion for
knockdowns, owner-stated: *"strangle wherever the runtime still knows what the game is"*
(`PDR-0019`); the issue nominates **terrain/substrate** as first candidate.

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check
`docs/architecture/` before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-13)

- Grant re-confirmed at session start, standard scope, unchanged.
- Owner endorsed verifying GPU determinism before pinning the tag (recorded in `PDR-0030`).
- **Blocked on owner:** the README push (standing), and now **pushing the branch + oracle
  tag to the public repo** — the tag exists locally only; a push is outward-facing.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **WS-7** `hamlet-e3af412673` (P0, **in progress**, claude). Next unit: the **differential
  harness** — old worktree at `oracle-2026-08-13` vs new, same `CompiledUniverse`, assert
  agreement everywhere the register doesn't say otherwise. Runs are now reproducible
  (`seed_all`, config-declared seed), so trace comparison is real. Then the first knockdown
  decision (terrain/substrate); **mine `docs/plans/2026-05-15-compiler-cleanup-modernization.md`
  for the playbook**. Child `hamlet-834108b55a` CLOSED at `6f60060e`.
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched.
- **WS-4 additions** (unchanged): `hamlet-310e336786`, `hamlet-f46e2b381a`,
  `hamlet-fa6bb6da4a`, `hamlet-e979f2ba37` (`PDR-0026`), `hamlet-365e996511`,
  `hamlet-0dd4ac24d9`, `hamlet-0cdb8a6d1a` (`PDR-0024`), `hamlet-0d0115383e` (`PDR-0027`).
- Hash-boundary tests remain unwritten: `hamlet-c8c316ba03`. DIV-001/DIV-002 fixes land in
  the rebuild (`hamlet-2dde1015fe`, `hamlet-df2b972c49` stay open as fix trackers).

## Open questions / blocked-on-owner

- **Push of branch + oracle tag** to the public repo — owner's call (see Owner state).
- Open, not blocking: the five shipped levels are three universes (WS-3 scoping input); the
  inert-surface baseline (~40) still needs one itemized recount.

## What this checkpoint did

- **Stood up the known-divergences register** (`ce9288c0`) as WS-7's first artifact; entered
  and source-verified DIV-001/DIV-002; `PDR-0028`'s trigger unfireable, `PDR-0022`'s
  precondition met. **Provenance-integrity guardrail is GREEN** for the first time.
- **Closed the seeding bug** (`hamlet-834108b55a`, `6f60060e`): `seed_all` single door,
  required `training.seed` in all 25 packs (`PDR-0031`), env off the global RNG, runner
  seeds at construction. TDD throughout; three named mutations caught in a detached worktree.
- **Verified GPU + TorchScript-JIT determinism** (`0e875d7a`): same seed → bit-identical
  CUDA trace. GPU *training-loop* determinism explicitly unclaimed.
- **Pinned the oracle** (`PDR-0030`): clean full suite at the exact commit (2992/16/0);
  `PDR-0029` trigger 1 tested and did not fire. `PDR-0030`, `PDR-0031` appended.

## Next session, start here

**Build the differential harness** (WS-7 content 3, reshapes WS-3 `hamlet-1f89714685`):
old side = worktree at `oracle-2026-08-13`, new side = working tree, same compiled
universe + same seed, assert trace agreement, adjudicate diffs against the register. Then
DECIDE the first knockdown unit (terrain/substrate nominated). Do not fix DIV-001/DIV-002
pre-harness — they are registered divergences the rebuild owns.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before every measurement; verify
red by mutation in a detached worktree (never `git stash`); a green test is not evidence,
mutate before believing; enumerate producers, not call shapes; a correction is not
self-verifying — check against source before recording.

Do not re-litigate: `PDR-0006` (strangler), `PDR-0019` (selection criterion), `PDR-0022`,
`PDR-0026`–`PDR-0029` (owner-resolved / closed), **`PDR-0030` (the oracle is pinned — a
found pre-tag defect moves the oracle FORWARD via a new tag, it never reopens the pin)**,
`PDR-0031` (seed is config). Read `vision.md` first: ENDORSED; grant re-confirmed
2026-08-13; changing it escalates.
