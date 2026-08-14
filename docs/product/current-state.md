# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 (later still) · fourteenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). **THE FIRST
KNOCKDOWN IS COMPLETE** (`PDR-0041`, `b7574132`): the substrate→observation-dim seam is cut,
the compiler asks the substrate instance for every observation dim, the three registered
crashing configs run, and the harness adjudicated the whole thing end-to-end — 16-cell matrix
exit 0 on CPU and CUDA, six `DIVERGED_AS_REGISTERED` (DIV-003), ten byte-exact AGREE. The
strangler method — register → bind → cut → adjudicate — is now proven once, which is what
`PDR-0035` chose this unit for. Selection criterion for the next unit, owner-stated:
*"strangle wherever the runtime still knows what the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-15)

- **Grant standing, unchanged** (re-confirmed 2026-08-14). **The owner pushes the branch
  themselves** — not an agent gate; do not re-raise. **The escalation queue is EMPTY.**
- Unpushed (owner's cadence): ahead of `origin/project-recovery` by **12 commits** after this
  checkpoint's commit — the README rewrite, the register-suppression fix, the first knockdown,
  the `/doctor` hygiene commits (`8ffca2ca`, `1c2ab8a0`, owner-committed), and four
  checkpoints exist only on this machine. The oracle *tag* is pushed; the branch tip is not.
- Bookkeeping owed to `vision.md` (never edited silently): its grant block still reads
  `Last reviewed: 2026-08-11`; the owner re-confirmed 2026-08-14. Fix at the next
  owner-approved touch.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **WS-7** `hamlet-e3af412673` (P0, in progress, claude — claim to 2026-08-16 17:29 UTC,
  verified this checkpoint). Contents 1–5 ALL DELIVERED. Remaining child: `hamlet-1073af4d4e`
  (P3, `--oracle-ref` unvalidated). **Open DECIDE: does WS-7 close now** (infrastructure
  proven end-to-end; knockdowns continue as their own issues), or stay open as the standing
  home of per-knockdown seam cutting? Nothing blocks on the answer; the next knockdown needs
  a `PDR-0019` selection either way.
- **`hamlet-2100105c9a`** (P1) — CI is dead. **A merge gate, not an interrupt** (`PDR-0039`).
  With the first knockdown done, this is next in the `PDR-0039` sequence.
- **WS-3** `hamlet-1f89714685` — open, still blocking the rest of WS-4. `PDR-0034` stands.
- **WS-4** `hamlet-15050f280a` — the line-227 item the knockdown subsumed is DONE
  (`PDR-0041`); every other ledger item stays behind WS-3.
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched six
  checkpoints. Starting them remains a live option under `PDR-0019`.
- Tooling housekeeping (P3, from `/doctor`, no bearing on the bet): `hamlet-312f75963b`
  (checked-in hook duplication + timeout-units bug), `hamlet-5e2032b166` (delete vendored
  axiom-* skill packs; yzmir-deep-rl is the opposite pattern — keep it).

## Two gates on the merge to `main` (`PDR-0039`, unchanged)

1. **CI restoration** (`hamlet-2100105c9a`); fix `validate_compiler_cli.py`'s input first;
   `Full Test Suite` is `disabled_inactivity` — sticky, needs explicit `gh workflow enable`.
2. **README re-verification by the same method, not a re-read.**

## What this checkpoint did

- **Recorded the `/doctor` hygiene pass as `PDR-0042`**: the operator brief (`CLAUDE.md`)
  trimmed 26,031 → 20,688 chars, deleting four live self-contradictions (stale claims sitting
  beside their own corrections) and stale `configs/L0_0_minimal` commands; every ⚠️
  verified-finding block and the curriculum reality table survive; inference workflow →
  `live-inference` skill, frontend guidance → `frontend/CLAUDE.md`. Owner approved in-session
  and committed the result themselves (`8ffca2ca`, `1c2ab8a0`).
- **Filed two P3 tooling issues** from the same audit (`hamlet-312f75963b`,
  `hamlet-5e2032b166`); tracker pointers verified (WS-7 status/claim accurate).
- **No product code touched, no bet moved, no metric readings** — `roadmap.md` and
  `metrics.md` deliberately untouched. Nothing escalated.

## Next session, start here

1. **DECIDE: the next knockdown unit** on `PDR-0019`'s criterion (*where does the runtime
   still know what the game is?*) — or DECIDE that the sequenced next step is the merge
   gate instead: **CI restoration** (`hamlet-2100105c9a`), which `PDR-0039` ordered "after
   the current knockdown." That ordering point has now arrived.
2. Settle the **WS-7 close-or-keep** question in the same DECIDE.
3. If a knockdown: the playbook is `PDR-0037`+`PDR-0041` — register first (re-verify at
   the tag through the driver), bind cells, cut, adjudicate. Do not invent a new one.

**Harness gate contract:** `uv run python -m townlet.oracle.harness` — exit 0 iff every cell
is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its register entry; empty and
all-SKIPPED runs fail. **NOT safe to run concurrently with itself in one checkout.** The
DIV-003 cells stay `DIVERGED_AS_REGISTERED` until the oracle moves forward (new tag), at
which point the entry retires.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before measurements (a stale cache
made the post-cut tree report pre-cut dims); verify red by mutation in a detached worktree
(never `git stash`); a green test is not evidence — mutate before believing; enumerate
producers, not call shapes; a correction is not self-verifying; ask what a green tool cannot
see; ask what its red cannot distinguish; a verifier is not self-verifying — probe the
instrument first; *an equivalent-looking surviving mutant indicts the probe input before it
indicts the code* (`PDR-0041`). **New (`PDR-0042`):** *a brief that argues with itself trains
sessions to distrust the parts that are true* — corrections replace stale claims, they do not
sit beside them.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0029`, `PDR-0030`
(the oracle pin moves FORWARD only), `PDR-0031`, `PDR-0032`, `PDR-0034`, `PDR-0035`,
`PDR-0036`, `PDR-0037`, `PDR-0038`, `PDR-0039` (README claims expire at the merge),
`PDR-0040` (the matcher's conjuncts and anchor), `PDR-0041` (the knockdown's design edges —
reverse only via its stated triggers), `PDR-0042` (the operator brief stays trimmed —
restore a section only via its two-incident trigger).
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-14, unchanged; changing it escalates.
