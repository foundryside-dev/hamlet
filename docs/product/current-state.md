# Current State — HAMLET / Townlet        Checkpoint: 2026-08-14 · eleventh checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Oracle pinned
(`oracle-2026-08-13` → `0e875d7a`, now **pushed to origin**), differential harness built and
accepted. WS-7 (`hamlet-e3af412673`, claimed by claude) has contents **1, 2, 3, 4 done**.
Content **5 is scoped** — the first knockdown unit is the **substrate→observation-dim seam**
(`PDR-0035`) — but it does **not** start with the seam; see *Next session*. Selection criterion,
owner-stated: *"strangle wherever the runtime still knows what the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-14)

- **Grant re-confirmed, standard scope, unchanged.**
- **The owner pushes the branch themselves.** Confirmed this session; four pushes to date. Not an
  agent gate. Do not re-raise it.
- **The escalation queue is EMPTY** — first time since bootstrap. All four standing items cleared
  in one turn (`PDR-0038`): oracle tag pushed, wardline instruction deleted, `vision.md` URL
  corrected, README rewritten.
- **The README ships as written** (`PDR-0039`), on the owner's stated reasoning: *"this is on a
  recovery branch and hopefully we'll recover before we push back to main."* That is a scope
  claim, not just an approval — see the merge gates below.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **WS-7** `hamlet-e3af412673` (P0, in progress, claude; lease to 2026-08-15 20:52 UTC).
  Content 5, re-ordered — see *Next session*.
- **`hamlet-56ec575ae2`** (P0, **BLOCKING the first knockdown**) — the harness cannot pass a
  divergence it predicted (`PDR-0037`).
- **`hamlet-2100105c9a`** (P1, **new**) — CI is dead. **A merge gate, not an interrupt**
  (`PDR-0039`).
- **WS-3** `hamlet-1f89714685` — open, still blocking the rest of WS-4. `PDR-0034` stands.
- **WS-4** `hamlet-15050f280a` — narrowed by exactly one item (`PDR-0035`).
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched for three
  checkpoints. Both on the WS-3 → WS-4 chain; under `PDR-0019` starting them is a live option.
- New this session: `hamlet-1073af4d4e` (P3, `--oracle-ref` unvalidated — rescued from the
  wardline issue before it closed). Closed this session: `hamlet-f894ade20a` (`wont_fix`),
  `hamlet-6730ba7915` (README).

## Two gates on the merge to `main`

`PDR-0039`. The owner's *"recover before we push back to main"* names the bet's exit, and two
things must be true at it:

1. **CI restoration** (`hamlet-2100105c9a`). Merging today puts 145 CI-unvalidated commits on the
   default branch. **Ordering trap:** fix `validate_compiler_cli.py`'s input *before* pointing any
   workflow at this branch, or the first run is red on arrival. Note `Full Test Suite` is
   `disabled_inactivity` — sticky, needs an explicit `gh workflow enable`; no push clears it.
2. **README re-verification, by the same method — not a re-read.** Its rough-edges and CI sections
   describe conditions the recovery intends to *fix*; merging them unchanged turns honest status
   into stale claims on `main`. The adversarial pass caught **24 defects in a draft written
   expressly not to lie**; a skim would not have.

## Open questions

- Whether WS-6 / WS-2 should start before the knockdown completes. Order within Now is open
  (`PDR-0019`); both are ready and three checkpoints untouched.
- Open, not blocking: the inert-surface baseline (~40) still needs one itemized recount.

## What this checkpoint did

- **Cleared the entire escalation queue** (`PDR-0038`) and recorded the publish decision that
  followed (`PDR-0039`), which turned an approval into two named merge gates.
- **Rewrote `README.md` from verified source.** 102 confirmed-false claims catalogued in the old
  file; 147 evidence-backed facts gathered; **24 further defects found in the draft itself**
  (8 FALSE, 15 MISLEADING, 1 UNVERIFIABLE) before finalizing. The new file carries no test count,
  coverage figure, observation width or performance number, on purpose.
- **Found CI is dead** (`hamlet-2100105c9a`) while verifying the draft — no workflow has ever run
  on this branch, nothing has passed since 2025-11-28, `Full Test Suite` is `disabled_inactivity`.
  Fourth instance of the `PDR-0010` pattern in four days and the widest yet.
- **Caught two false claims in my own corrections** (`dcc5f803`): `metrics.md` still said the
  `vision.md` URL was unfixed after the owner approved fixing it, and the README's CI paragraph
  inferred a dormancy cause instead of measuring it. Both fixed; the second is now cited from
  `gh workflow list --all`, which also changed the fix.

## Next session, start here

**Do NOT cut the seam first.** Content 5's order, per `PDR-0037`:

1. **`hamlet-56ec575ae2` — teach the harness to pass a registered divergence.** Declare
   expectations per cell, populate `CellVerdict.register_refs` (hook exists at `trace_io.py:96`,
   already serialized at `harness.py:201`), widen `exit_code` so a matched divergence passes and
   an unmatched one — including an unmatched `OLD_SIDE_ERROR` — still fails. **Mandatory
   `PDR-0033` adversarial pass briefed to hunt WRONG PASSES**: a loose match is a false-AGREE
   machine pointed at the programme's own safety net.
2. **Append DIV-003.** **Re-verify the oracle behaviour at `0e875d7a` first** — the three crashes
   (`observation_encoding: scaled`; `cubic` + `partial`; `width != height`) are executed evidence
   from 2026-08-11, *pre-tag*, and the register forbids copying from a filed issue unchecked.
   Expected diff shape is unusual: the oracle side **fails to produce a trace at all**.
3. **Extend the declared matrix.** `matrix.py:36-58` is hardcoded to `default_curriculum` × 5
   levels × {cpu, cuda} and exercises none of the crashing configs. `RunParams.pack` is per-cell.
4. **Cut the seam.** The fourth crash (`grid3d` has no factory branch, `factory.py:152`) is inside
   the same seam. WS-4's issue text notes this change is what *"unfinished plan phase 9
   prescribed"* — check WS-6's run sheets before designing it.

**Run the harness before and after every knockdown step:**
`uv run python -m townlet.oracle.harness` (exit 0 iff every cell AGREE or SKIPPED — **until step 1
lands, that contract is the problem, not the gate**). **NOT safe to run concurrently with itself
in one checkout.**

**Checked, do not re-check:** `PDR-0032` reversal trigger 2 does **not** fire — schema unchanged,
both sides parse the same pack, the oracle fails at `env.reset()`, not at parse.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before every measurement; verify red by
mutation in a detached worktree (never `git stash`); a green test is not evidence, mutate before
believing; enumerate producers, not call shapes; a correction is not self-verifying — check
against source before recording; a green *tool* is not evidence either — ask what its green cannot
see; and ask what its **red** cannot distinguish. **New:** *a correction is not self-verifying
either* — this session shipped two false claims inside the commit that was fixing false claims.
When you correct a document, re-read every other cell that referenced the thing you corrected.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0029`, **`PDR-0030` (the
oracle is pinned — a found pre-tag defect moves the oracle FORWARD via a new tag, never reopens
the pin)**, `PDR-0031`, `PDR-0032`, `PDR-0034`, `PDR-0035` (the knockdown unit), `PDR-0036`
(declared-and-crashing is a divergence), `PDR-0037` (harness before seam), **`PDR-0038` (the
owner's four clearances), `PDR-0039` (the README ships; its claims expire at the merge)**.
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-14, unchanged; changing it escalates.
