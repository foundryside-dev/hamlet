# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 (latest) · sixteenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). The first knockdown
is COMPLETE and accepted (`PDR-0041`, `b7574132`). Merge gate 1 (CI restoration, `PDR-0043`,
`cb865af4`) is EXECUTED and `hamlet-2100105c9a` sits in **verifying** — it closes on the
**first green CI run**, which this checkpoint's push fires. A gate restored is not a gate
verified.

**This checkpoint began the `docs/` triage** and, chasing one contradiction inside it, landed
two owner-stated principles: the token-observation direction was authoritative all along
(`PDR-0044`), and **the compiler must be name-blind** (`PDR-0045`). The second is a new
standing rule with measured violations *inside the compiler*, and it generalises the
`vtc.py` social-residue sighting the last checkpoint left as a knockdown candidate.

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-15)

- **Grant standing, unchanged** (re-confirmed 2026-08-14).
- ⚠️ **The "owner pushes the branch themselves" practice was set aside this session, by the
  owner, explicitly:** *"please commit all your updates including your checkpoint and sync to
  remote."* So this checkpoint **committed and pushed**, which also fired the **first CI run in
  this branch's history**. Treat as a one-time direction, not a standing change: the next
  session should assume the owner pushes unless told otherwise again.
- Was ahead of `origin/project-recovery` by 4 commits (`cb865af4` CI restoration; `3191cd90`
  **owner-committed mid-session** — CLAUDE.md rewrite + `REVIEW-2026-08-15-architecture-docs-and-hld.md`,
  a 14-agent docs review that feeds WS-5 `hamlet-7a52a63e0b`, read it before docs work;
  `d77e0610` worktree-gitlink cleanup; the fifteenth checkpoint). **All pushed by this
  checkpoint** along with its own commits.
- **A concurrent session was committing to this branch during this one** (`5f012175`,
  `cb865af4`, `d77e0610`, `3191cd90` all landed mid-session). Consequence to expect again:
  `PDR-0043` was claimed underneath this session's draft, forcing a renumber to `PDR-0044` /
  `PDR-0045`. **Check the highest PDR number immediately before writing, not when you started.**
- Bookkeeping still owed to `vision.md` (never edited silently): grant block reads
  `Last reviewed: 2026-08-11`; owner re-confirmed 2026-08-14. Fix at next approved touch.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **`hamlet-2100105c9a`** (P1, **verifying**, claude) — CI restoration. Close on the first
  green run of Lint + Tests + Config Validation on `project-recovery` (after owner push):
  `gh run list --branch project-recovery`. Optional full matrix afterward:
  `gh workflow enable 203224930 && gh workflow run full-tests.yml --ref project-recovery`.
- **`hamlet-c4ce5515cc`** (P2) — adjudicate the PROVISIONAL no-defaults whitelist
  entries (`vtc.py` raw-mapping parse defaults; `metadata.py` hasattr-guarded cost). Carries
  a `PDR-0019` sighting: `vtc.py` hardcodes social-residue telemetry labels — the compiler
  still knows what the game is. **`PDR-0045` now names that sighting's rule**, and
  `hamlet-60dd3c4b53` covers the same `metadata.py:83` line from the name-blindness angle —
  coordinate, do not fix twice.
- **`hamlet-60dd3c4b53`** (P1, new, triage) — the compiler infers variable semantics by
  substring-matching English meter names (`vfs_adapter.py:31-41`), **and the result is hashed
  into the observation field UUID**. A pack naming its currency `credits` gets a different
  observation schema hash for no structural reason. Also satisfies `hamlet-0dd4ac24d9`'s
  "enumerate the name-special-casing sites" precondition; sequence the compiler before the
  frontend, since only the compiler one moves artifact identity.
- **`hamlet-7a52a63e0b`** (WS-5 docs) — **partially done and released, deliberately.** Its own
  notes gate the body ("do NOT start doc rewriting yet"); that gate is intact and untouched.
  Only the orthogonal slice ran — removing false completion signals. See comments 139/140.
- **WS-7** `hamlet-e3af412673` (P0, in progress, claude — claim expires 2026-08-16 17:29 UTC,
  NOT refreshed this session; re-claim if lapsed). Open DECIDE unchanged: close now
  (infrastructure proven) or keep as the standing knockdown home. Nothing blocks on it.
- **WS-3** `hamlet-1f89714685` still gates WS-4 `hamlet-15050f280a` (`PDR-0034`). **WS-6**,
  **WS-0** ready, untouched. Tooling P3s: `hamlet-312f75963b`, `hamlet-5e2032b166`.

## Two gates on the merge to `main` (`PDR-0039`)

1. **CI restoration — EXECUTED, verifying** (above). The merge checklist inherits `PDR-0043`
   trigger 2: restore the nightly cron at merge (or PDR its death) — the deferral must not
   decay into silent capability loss.
2. **README re-verification by the same method, not a re-read** — unchanged.

## What this checkpoint did

- **Began the `docs/` triage.** Measured first: the live surface is **320 files, not 573** —
  253 are already inside `archive/`/`closed/`/`done/`. `plans/` is 179 but only **20** live.
  Rewrote `docs/README.md`, which was the front door and the worst file in the corpus: it
  claimed "85+ files across 9 categories" and routed developers to three of the worst
  documents, one of which (`architecture/TOWNLET_HLD.md`) **does not exist**. Replaced with
  trust tiers (current / design-intent / historical), a known-traps list, and the "check
  `src/townlet/` first" rule; every link verified to resolve.
- **Killed the observation-dimension contradiction at its root.** The three irreconcilable
  tables were never reconcilable, because **"observation dim" is two quantities**: allocated
  (124, constant at every level — this *is* the transfer-learning mechanism) and active
  (95 / 56 / 99). Measured. The three activity profiles match the three real universes
  exactly — independent confirmation of "five levels, three universes" from an unrelated
  direction. POMDP does **not** shrink the tensor; it zeroes the 64-dim grid block and lights
  the 25-dim window. Root cause of the false table: `observation-dimension-manual-validation.md`
  ticked ✓ against 3×3 / 7×7 grids that no level can express — it validated the *intended*
  curriculum against *shipped* code, and `vfs.md` §2.3 imported the result as "Validated".
- **Recorded `PDR-0044`** — the token-observation direction was authoritative from 2026-08-11.
  `PDR-0017` read *"orthogonal"* as a disclaimer of authority; the owner corrected it. Its
  sequencing survives on its own merits; one premise is struck. `PDR-0017` corrected by
  pointer, not overwritten (the `PDR-0020` practice).
- **Recorded `PDR-0045`** — *the author sets the scale; the compiler is name-blind.* New
  standing rule, testable: no engine or compiler code may branch on a variable's **name**.
  Filed `hamlet-60dd3c4b53` with two compiler violations and the in-tree fix model
  (`money_bar: str`, required, no default — engine holds the role, author binds the referent).
- **Corrected two errors of my own**, both load-bearing: the artifact accessor added to
  CLAUDE.md last session was wrong twice (`.levels` does not exist; the field is `total_dims`),
  and my own first measurement was reported as "all five levels identical", which is true of
  allocated width and false of everything a reader would infer from it. Fixed in all six
  places before reporting.
- Superseded banners (not corrections) on the two `docs/vfs/observation-dimension-*.md` files
  and the orphaned `docs/vfs-integration-guide.md` — under `PDR-0044` the **method** is
  obsolete, not the arithmetic. **No reversal trigger fired.** Nothing escalated.

## Next session, start here

1. **Verify the CI runs this checkpoint's push fired** — three workflows, first run in this
   branch's history. Then close `hamlet-2100105c9a` naming the run IDs and `close_commit`. If
   any run is red for a cause the local set covers, `PDR-0043` trigger 1 has fired — reopen and
   re-examine the verification protocol itself.
2. **The standing DECIDE** (unchanged): next knockdown unit on `PDR-0019`'s criterion — the
   `vtc.py` social-residue sighting is a fresh candidate, and **`PDR-0045` now supplies its
   rule**, which strengthens it — and WS-7 close-or-keep in the same DECIDE. Playbook fixed:
   `PDR-0037`+`PDR-0041`.
3. **`docs/` triage continues if wanted.** `plans/` (20 live of 179) is next; `bugs/` (60 of
   119) and `tasks/` (31) after. Convention set by this checkpoint: **banner in place, do not
   move or delete** — relocations are proposed, not executed. One deletion candidate is
   proposed and not executed: `docs/vfs-integration-guide.md`, orphaned and wrong three ways.

**Harness gate contract** (carry): `uv run python -m townlet.oracle.harness` — exit 0 iff
every cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its register entry; empty and
all-SKIPPED runs fail. NOT safe to run concurrently with itself in one checkout. DIV-003
cells stay suppressed until the oracle moves forward.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before measurements; verify red by
mutation in a detached worktree; a green test is not evidence — mutate first; enumerate
producers, not call shapes; a correction is not self-verifying; ask what a green tool cannot
see and what its red cannot distinguish; a verifier is not self-verifying — probe the
instrument first; a brief that argues with itself trains distrust (`PDR-0042`). **New
(`PDR-0043`):** *a gate restored is not a gate verified — close on the first green run, not
the ship*; *the scheduler reads the default branch's file — a branch-side cron edit changes
nothing until merge*; *a verification ledger can itself declare dead surface — prune the
whitelist like code*. **New (`PDR-0044`/`PDR-0045`):** *when the owner defers timing, record
the timing deferral and the authority separately — "orthogonal" answers **when**, not
**whether**, and inferring the weaker reading silently discards a directive*; *a doc that
validates the intended config against shipped code finds an agreement that does not exist —
every ✓ in it is false and it is more convincing than a doc with no ticks*; *when two
quantities share a name (allocated vs active width), no table quoting one of them can ever be
reconciled — say which*; *name-based inference is the hardest special-casing to see, because
`if name == "money"` reads as a helpful default rather than a hardcoded domain fact*.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0029`, `PDR-0030`,
`PDR-0031`, `PDR-0032`, `PDR-0034`–`PDR-0042` (per their stated triggers), `PDR-0043` (the
nightly deferral and the provisional-whitelist pattern — reverse only via its three triggers),
`PDR-0044` (the direction's authority — a change of direction supersedes it, nothing else
does), `PDR-0045` (name-blindness — reverse only via its three triggers).
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-14, unchanged; changing it escalates.
