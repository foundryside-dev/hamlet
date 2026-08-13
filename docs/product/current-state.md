# Current State — HAMLET / Townlet        Checkpoint: 2026-08-14 · tenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Oracle pinned
(`oracle-2026-08-13` → `0e875d7a`), differential harness built and accepted (`PDR-0032`,
`PDR-0033`, `d54ad7df`). WS-7 (`hamlet-e3af412673`, claimed by claude) has contents
**1, 2, 3, 4 done**. Content **5 is now scoped**: the first knockdown unit is **the
substrate→observation-dim seam** (`PDR-0035`) — but it does **not** start with the seam; see
*Next session*. Selection criterion, owner-stated: *"strangle wherever the runtime still knows
what the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-14)

- **Grant re-confirmed at session start, standard scope, unchanged.**
- **The push question is CLOSED: the owner pushes the branch themselves.** Confirmed this
  session. `origin/project-recovery` has tracked HEAD through four pushes (2026-08-08, 08-11,
  08-13, and 08-13 20:16 UTC — the last one carrying the ninth checkpoint). This is no longer
  an agent gate and no longer a blocker; do not re-raise it.
- **Blocked on owner (standing, narrowed):** the **README** (`hamlet-6730ba7915` — the public
  face of a public repo), the **oracle tag** (`git push origin oracle-2026-08-13`, owner's
  push to make when convenient), the **wardline fork**, and the **`vision.md` URL** (below).

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`. 22 ready, 5 blocked.

- **WS-7** `hamlet-e3af412673` (P0, in progress, claude; lease to 2026-08-15 20:52 UTC).
  Content 5, re-ordered — see *Next session*.
- **`hamlet-56ec575ae2`** (P0, **new, BLOCKING the first knockdown**) — the harness cannot
  pass a divergence it predicted (`PDR-0037`).
- **WS-3** `hamlet-1f89714685` — still open, still blocking the rest of WS-4. `PDR-0034`
  stands; the harness does not subsume it.
- **WS-4** `hamlet-15050f280a` — **narrowed by exactly one item** (`PDR-0035`): the substrate
  observation-dim delegation moved into WS-7's knockdown. Everything else stays behind WS-3.
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched for three
  checkpoints. Both sit on the WS-3 → WS-4 chain; under `PDR-0019` the order is open, so
  starting them is a live option, not a deviation.
- Open, unchanged: `hamlet-f894ade20a` (P1, wardline inert), `hamlet-1ec950ee60` (P3),
  `hamlet-c8c316ba03` (hash-boundary tests), `hamlet-2dde1015fe` / `hamlet-df2b972c49`
  (DIV-001 / DIV-002 fix trackers), and the WS-4 additions.

## Open questions / blocked-on-owner

- **The `vision.md` repo URL is stale and was deliberately NOT corrected.** It says
  `github.com/tachyon-beep/hamlet`; `origin` is `github.com/foundryside-dev/hamlet`. Both
  resolve and both are `PUBLIC`, so nothing about the grant's reach changes. The fix was
  offered alongside the grant confirmation and not taken, and `vision.md` is ENDORSED — its own
  header makes an unrequested edit a vision change. Recorded in `metrics.md` → Documentation
  truth. **One-word fix whenever you want it.**
- **The wardline fork (`hamlet-f894ade20a`) — needs the owner, since wardline is theirs.**
  `CLAUDE.md` instructs every agent to run `wardline scan . --fail-on ERROR` as a gate. It
  passes, and `--fail-on-inert` fails: 0 trust boundaries across 1555 functions, no boundary
  decorators in `src/townlet/`, wardline not even a dependency. Unfalsifiable as written.
  Wire real boundaries, or delete the instruction?
- Open, not blocking: the inert-surface baseline (~40) still needs one itemized recount.

## What this checkpoint did

- **Decided the first knockdown's unit boundary** (`PDR-0035`) — the substrate→observation-dim
  seam, verified against source, not inherited from the nomination. The compiler switches on
  `substrate.type` strings at `observation.py:64-76` and `:135-145` while `:146-155` already
  asks the substrate instance for `continuous`/`continuousnd`: the right pattern, same
  function, 2 of 5 types. Consequence: WS-4's line-227 item is subsumed and no longer waits on
  WS-3.
- **Settled whether the substrate crashes belong in the register** (`PDR-0036`) rather than
  stepping over the exclusion clause that plausibly sent them to WS-4. *Declared-and-crashing*
  is a third category: inert surfaces are excluded **because** they produce no divergence
  (`PDR-0034` from the other side), and that reason does not reach a crash the rebuild fixes.
  DIV-003 authorized — **not yet written**, see below.
- **Found the blocking hole before it cost a knockdown** (`PDR-0037`, `hamlet-56ec575ae2`):
  the harness's `exit_code` passes only `AGREE`/`SKIPPED`, so a *correctly* rebuilt substrate
  would exit 1 on every cell. `PDR-0033`'s practice paid off inverted — not *what a green tool
  cannot see* but **what its red cannot distinguish**.
- **Closed the push question and narrowed the blocked-on-owner list** from four standing items
  to three-plus-one-new. No code committed this session; `Gates green` correctly not re-read.

## Next session, start here

**Do NOT cut the seam first.** Content 5's order, per `PDR-0037`:

1. **`hamlet-56ec575ae2` — teach the harness to pass a registered divergence.** Declare
   expectations per cell, populate `CellVerdict.register_refs` (the hook exists at
   `trace_io.py:96` and is already serialized at `harness.py:201`), widen `exit_code` so a
   matched divergence passes and an unmatched one — including an unmatched `OLD_SIDE_ERROR` —
   still fails. **Mandatory `PDR-0033` adversarial pass, briefed to hunt WRONG PASSES**: a
   loose match is a false-AGREE machine.
2. **Append DIV-003.** **Re-verify the oracle behaviour at `0e875d7a` first** — the three
   crashes (`observation_encoding: scaled`; `cubic` + `partial`; `width != height`) are
   executed evidence from 2026-08-11, *pre-tag*, and the register forbids copying from a filed
   issue unchecked. Expected diff shape is unusual: the oracle side **fails to produce a trace
   at all**, the rebuild produces one.
3. **Extend the declared matrix.** `matrix.py:36-58` is hardcoded to `default_curriculum` × 5
   levels × {cpu, cuda}; none of the three crashing configs is in any cell, so the divergence
   is currently unexercised. `RunParams.pack` is per-cell — a pack fixture plus declarations.
4. **Cut the seam.** The fourth crash (`type: grid3d` has no factory branch, `factory.py:152`)
   is inside the same seam and goes with it. WS-4's issue text notes this change is what
   *"unfinished plan phase 9 prescribed"* — check WS-6's run sheets before designing it.

**Run the harness before and after every knockdown step:**
`uv run python -m townlet.oracle.harness` (exit 0 iff every cell AGREE or SKIPPED — **until
step 1 lands, that contract is the problem, not the gate**). **It is NOT safe to run
concurrently with itself in one checkout.**

**Checked, do not re-check:** `PDR-0032` reversal trigger 2 does **not** fire — schema
unchanged, both sides parse the same pack, the oracle fails at `env.reset()`, not at parse.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before every measurement; verify red
by mutation in a detached worktree (never `git stash`); a green test is not evidence, mutate
before believing; enumerate producers, not call shapes; a correction is not self-verifying —
check against source before recording; a green *tool* is not evidence either — ask what its
green cannot see. **New:** and ask what its **red** cannot distinguish.

Do not re-litigate: `PDR-0006` (strangler), `PDR-0019` (selection criterion), `PDR-0022`,
`PDR-0026`–`PDR-0029`, **`PDR-0030` (the oracle is pinned — a found pre-tag defect moves the
oracle FORWARD via a new tag, it never reopens the pin)**, `PDR-0031` (seed is config),
`PDR-0032` (harness scope/home/execution — owner-endorsed), `PDR-0034` (the harness does not
subsume WS-3), **`PDR-0035` (the knockdown unit), `PDR-0036` (declared-and-crashing is a
divergence), `PDR-0037` (harness before seam)**. Read `vision.md` first: ENDORSED; grant
re-confirmed 2026-08-14, unchanged; changing it escalates.
