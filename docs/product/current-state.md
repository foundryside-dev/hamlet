# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 · twelfth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Oracle pinned
(`oracle-2026-08-13` → `0e875d7a`, pushed). WS-7 (`hamlet-e3af412673`, claimed by claude) has
contents 1–4 done and content 5 **step 1 of 4 done**: the harness can now PASS a divergence the
register predicted (`hamlet-56ec575ae2` closed at `9a75b581`, accepted in `PDR-0040`). The
knockdown unit stands: the **substrate→observation-dim seam** (`PDR-0035`). Selection criterion,
owner-stated: *"strangle wherever the runtime still knows what the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-15)

- **Grant standing, unchanged** (re-confirmed 2026-08-14). **The owner pushes the branch
  themselves** — not an agent gate; do not re-raise. **The escalation queue is EMPTY.**
- Unpushed by agent design: `9a75b581` (the fix) and this checkpoint commit.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **WS-7** `hamlet-e3af412673` (P0, in progress, claude). Content 5 steps 2–4 remain — see
  *Next session*. Closed this session: `hamlet-56ec575ae2` (P0, was BLOCKING the knockdown).
- **`hamlet-2100105c9a`** (P1) — CI is dead. **A merge gate, not an interrupt** (`PDR-0039`).
- **WS-3** `hamlet-1f89714685` — open, still blocking the rest of WS-4. `PDR-0034` stands.
- **WS-4** `hamlet-15050f280a` — narrowed by exactly one item (`PDR-0035`).
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched four
  checkpoints. Starting them remains a live option under `PDR-0019`.
- **`hamlet-1073af4d4e`** (P3, `--oracle-ref` unvalidated) — still open; `9a75b581` did not
  touch the `--oracle-ref` path.

## Two gates on the merge to `main` (`PDR-0039`, unchanged)

1. **CI restoration** (`hamlet-2100105c9a`); fix `validate_compiler_cli.py`'s input first;
   `Full Test Suite` is `disabled_inactivity` — sticky, needs explicit `gh workflow enable`.
2. **README re-verification by the same method, not a re-read.**

## What this checkpoint did

- **Accepted content 5 step 1** (`PDR-0040`): register-suppression seam closed at `9a75b581`.
  Match is conjunctive — old crashed + no trace written + signature inside the **final exception
  text** + new side ran with a valid lone trace (params/shapes/`code_root`). `exit_code` passes
  only AGREE/SKIPPED (empty refs) and `DIVERGED_AS_REGISTERED` (non-empty refs); empty and
  all-SKIPPED runs fail.
- **`PDR-0037` reversal trigger 1 FIRED during the mandatory `PDR-0033` pass** — four wave-through
  routes found (one reproduced), answered by the trigger's own prescription: narrow the match.
- **The pass failed twice as an instrument and was caught** (`PDR-0040`): a session-limit death
  made fail-closed keeps read as "confirmed"; pytest's `pythonpath = ["src"]` ini silently
  defeated the mutation agent's `PYTHONPATH` injection. Battery re-run probe-first: 10/10 killed.
- **Gates re-read at `9a75b581`** (code touched): ruff/black/mypy clean, pytest **3085/0**,
  harness full CPU matrix exit 0 twice. Tracker reconciled at source (WS-7 description updated).

## Next session, start here

Content 5's remaining order (`PDR-0037`):

1. **Append DIV-003.** Re-verify the three crashes (`observation_encoding: scaled`; `cubic` +
   `partial`; `width != height`) **at `0e875d7a`** — the 2026-08-11 evidence is pre-tag and the
   register forbids copying from a filed issue unchecked. The entry **must carry a
   `Harness shape: old-side-crash` line** (the matrix binding test requires it). Record each
   crash's final-exception line verbatim — the cell signatures come from it.
2. **Extend the declared matrix** — pack fixtures for the crashing configs + cells with
   `Cell(params, expected=RegisteredDivergence("DIV-003", <distinctive final-exception
   fragment, ≥12 chars, not a bare exception name>))`. Pre-cut, these cells land
   `NEW_SIDE_ERROR: not (yet) built` — red, honestly; they flip at the cut.
3. **Cut the seam.** The fourth crash (`grid3d` has no factory branch) is inside it. Check
   WS-6's run sheets before designing — WS-4's text says this is what "unfinished plan phase 9
   prescribed".

**Harness gate, updated contract:** `uv run python -m townlet.oracle.harness` — exit 0 iff every
cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its register entry. **NOT safe to run
concurrently with itself in one checkout.**

Carry-ins that keep paying: purge `configs/**/*.msgpack` before measurements; verify red by
mutation in a detached worktree (never `git stash`); a green test is not evidence — mutate before
believing; enumerate producers, not call shapes; a correction is not self-verifying; a green tool
is not evidence — ask what its green cannot see; ask what its **red** cannot distinguish.
**New:** *a verifier is not self-verifying* — probe the instrument before believing its results:
mutation testing needs a loud-probe first (pytest's `pythonpath = ["src"]` ini beats the
`PYTHONPATH` env var), and a multi-agent verdict partition is checked for verifier failures
before its labels are read as verdicts.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0029`, `PDR-0030` (the
oracle pin moves FORWARD only), `PDR-0031`, `PDR-0032`, `PDR-0034`, `PDR-0035`, `PDR-0036`,
`PDR-0037`, `PDR-0038`, `PDR-0039` (README claims expire at the merge), **`PDR-0040` (the
matcher's conjuncts and anchor — loosen nothing without a new adversarial pass)**.
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-14, unchanged; changing it escalates.
