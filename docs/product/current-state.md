# Current State — HAMLET / Townlet        Checkpoint: 2026-08-13 · ninth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). The oracle is pinned
(`oracle-2026-08-13` → `0e875d7a`, `PDR-0030`) and **the differential harness that judges every
knockdown against it is BUILT AND ACCEPTED** (`PDR-0032`, `PDR-0033`, `d54ad7df`):
`src/townlet/oracle/`, CLI `uv run python -m townlet.oracle.harness`. WS-7
(`hamlet-e3af412673`, claimed by claude) now has contents **1, 2, 3, 4 done**; remaining:
**5 — per-unit seam cutting**, and the **first knockdown decision** (terrain/substrate
nominated). Selection criterion, owner-stated: *"strangle wherever the runtime still knows what
the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-13)

- Grant re-confirmed at session start, standard scope, unchanged.
- Owner ruled this session on one plan-vs-review conflict: fix a tautological test assertion
  rather than ship the plan's literal text.
- **Blocked on owner (standing, unchanged):** the README push, and **pushing the branch +
  oracle tag to the public repo** — the tag exists locally only; a push is outward-facing.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **WS-7** `hamlet-e3af412673` (P0, in progress, claude). Next: **content 5 — seam cutting,
  per knockdown unit, not globally** (`PDR-0006` §2b), then **DECIDE the first knockdown**.
  Mine `docs/plans/2026-05-15-compiler-cleanup-modernization.md` for the playbook — the owner
  ran this exact operation on the compiler already.
- **WS-3** `hamlet-1f89714685` — **still open, still blocking WS-4.** `PDR-0034` corrects the
  roadmap's old claim that the harness subsumed it: it does not, and cannot.
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched.
- **New this session:** `hamlet-f894ade20a` (P1 — wardline gate inert repo-wide),
  `hamlet-1ec950ee60` (P3 — `load_trace` leading-dim assert).
- **WS-4 additions** (unchanged): `hamlet-310e336786`, `hamlet-f46e2b381a`,
  `hamlet-fa6bb6da4a`, `hamlet-e979f2ba37` (`PDR-0026`), `hamlet-365e996511`,
  `hamlet-0dd4ac24d9`, `hamlet-0cdb8a6d1a` (`PDR-0024`), `hamlet-0d0115383e` (`PDR-0027`).
- Hash-boundary tests remain unwritten: `hamlet-c8c316ba03`. DIV-001/DIV-002 fixes land in the
  rebuild (`hamlet-2dde1015fe`, `hamlet-df2b972c49` stay open as fix trackers).

## Open questions / blocked-on-owner

- **Push of branch + oracle tag** to the public repo — owner's call (see Owner state).
- **The wardline fork (`hamlet-f894ade20a`) — needs the owner, since wardline is theirs.**
  `CLAUDE.md` instructs every agent to run `wardline scan . --fail-on ERROR` as a gate. It
  passes, and `--fail-on-inert` fails: 0 trust boundaries recognized across 1555 functions, no
  boundary decorators anywhere in `src/townlet/`, wardline not even a dependency. The
  instruction is unfalsifiable as written. Wire real boundaries, or delete the instruction?
- Open, not blocking: the inert-surface baseline (~40) still needs one itemized recount.

## What this checkpoint did

- **Built and accepted the differential harness** (`PDR-0032`): trace-only v1, `src/townlet/`
  `oracle/`, injected driver with both sides live — all three structural calls owner-endorsed.
  Nine commits, spec + plan committed, 43 unit + 2 integration tests.
- **Accepted only after an adversarial review wave found two false-AGREE holes** (`PDR-0033`):
  shape-blind byte comparison, and nothing asserting the `PYTHONPATH` injection took effect.
  Both had survived a per-task review *and* a whole-branch review. Standing practice adopted:
  a tool that emits verdicts gets one pass briefed to hunt wrong verdicts before it is trusted.
- **Corrected a scope claim one checkpoint from doing damage** (`PDR-0034`): the harness does
  **not** subsume WS-3. A differential instrument cannot see inertness — inert on both sides
  reads as AGREE — so WS-4 would have proceeded on an acceptance criterion no instrument met.
- **Metrics re-read at `d54ad7df`**: Gates 4/4, full suite **3035 / 16 / 0**. `PDR-0030`'s third
  reversal trigger **tested, did not fire** — the harness reproduces the oracle's traces on both
  CPU and CUDA, so the pin is validated by the instrument it was pinned for.

## Next session, start here

**Cut the seam for the first knockdown, then DECIDE the unit** (WS-7 content 5; terrain/
substrate nominated — three of four substrate crashes collapse to one change at
`compilers/observation.py:64-150`, and it is where the 6-D demo hits its only wall). Record the
knockdown's expected divergences in `docs/oracle/known-divergences.md` **before** cutting —
that is the register's own rule, and the harness adjudicates against it.

**Run the harness before and after every knockdown step:**
`uv run python -m townlet.oracle.harness` (exit 0 iff every cell AGREE or SKIPPED).
**It is NOT safe to run concurrently with itself in one checkout** — a mutation-style step edits
a tracked file in place; two concurrent runs this session produced race artifacts that looked
exactly like real divergences.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before every measurement; verify red by
mutation in a detached worktree (never `git stash`); a green test is not evidence, mutate before
believing; enumerate producers, not call shapes; a correction is not self-verifying — check
against source before recording. **New:** a green *tool* is not evidence either — ask what its
green cannot see.

Do not re-litigate: `PDR-0006` (strangler), `PDR-0019` (selection criterion), `PDR-0022`,
`PDR-0026`–`PDR-0029` (owner-resolved / closed), **`PDR-0030` (the oracle is pinned — a found
pre-tag defect moves the oracle FORWARD via a new tag, it never reopens the pin)**, `PDR-0031`
(seed is config), **`PDR-0032` (harness scope/home/execution — all three owner-endorsed)**,
**`PDR-0034` (the harness does not subsume WS-3)**. Read `vision.md` first: ENDORSED; grant
re-confirmed 2026-08-13; changing it escalates.
