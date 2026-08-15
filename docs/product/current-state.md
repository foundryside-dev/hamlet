# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 (latest) · sixteenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). The first knockdown
is COMPLETE and accepted (`PDR-0041`, `b7574132`). **Merge gate 1 (CI restoration, `PDR-0043`,
`cb865af4`) is DONE — `hamlet-2100105c9a` is CLOSED on remote evidence.** This checkpoint's
push fired the **first CI runs in this branch's history and all three are green**: Lint
(1m11s), Config Validation (1m14s), Tests (24m21s), on `dd94e122`. `PDR-0043` trigger 1 did
**not** fire — nothing was red for a cause the local set covers, so the local-vs-CI gate
correspondence held on first contact. **The nightly cron is still deferred, not fixed**
(the scheduler reads the default branch's file), carried as `PDR-0043` trigger 2 on the merge
checklist. **One merge gate left: README re-verification by method.**

**This checkpoint began the `docs/` triage** and, chasing one contradiction inside it, landed
two owner-stated principles: the token-observation direction was authoritative all along
(`PDR-0044`), and **the compiler must be name-blind** (`PDR-0045`). The second is a new
standing rule with measured violations *inside the compiler*, and it generalises the
`vtc.py` social-residue sighting the last checkpoint left as a knockdown candidate.

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (binding). Check `docs/architecture/`
before concluding shipped behaviour is simply wrong.

## Owner state (2026-08-15)

- **Grant standing, unchanged** (re-confirmed 2026-08-14).
- ✅ **The "owner pushes the branch themselves" practice is RETIRED** (`PDR-0046`; owner, 2026-08-15):
  *"I don't really care who pushes because with git you can generally roll back and forward
  easily anyway."* **The agent may commit and push `project-recovery` without asking.** The
  reasoning is reversibility, and it is right: a pushed commit on a working branch is
  `git revert` / `git reset` away, and the branch is not `main`.
  **The two limits are the ones reversibility does not cover, and they are unchanged:**
  1. **The merge to `main` still gates on `PDR-0039`'s two conditions.** Pushing a branch is
     cheap to undo; merging to the default branch of a **public** repo publishes, and
     publication is not reversible by pushing again.
  2. **Anything genuinely outward-facing still stops for the owner** — releases, issues or PRs
     on the public repo, anything leaving the machine to a third party. Git's undo does not
     reach a reader who already saw it.
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

- ~~**`hamlet-2100105c9a`**~~ — **CLOSED** this checkpoint on its stated criterion
  (`close_commit dd94e122`; runs 31852298597 / 31852298591 / 31852298586). Optional and still
  unrun: the full matrix, `gh workflow enable 203224930 && gh workflow run full-tests.yml
  --ref project-recovery`.
- **`hamlet-c4ce5515cc`** (P2) — adjudicate the PROVISIONAL no-defaults whitelist
  entries (`vtc.py` raw-mapping parse defaults; `metadata.py` hasattr-guarded cost). Carries
  a `PDR-0019` sighting: `vtc.py` hardcodes social-residue telemetry labels — the compiler
  still knows what the game is. **`PDR-0045` now names that sighting's rule**, and
  `hamlet-60dd3c4b53` covers the same `metadata.py:83` line from the name-blindness angle —
  coordinate, do not fix twice.
- ~~**`hamlet-60dd3c4b53`**~~ — **its headline was FALSIFIED by execution on 2026-08-15**
  (`1b25c99d`, recon comment 144). `vfs_adapter.py:31-41` is **dead code** — zero callers, not
  even imported by the compiler — so "the result is hashed into the observation field UUID" and
  "a pack naming its currency `credits` gets a different observation schema hash" are **false in
  the shipped compiler**. The second site (`metadata.py:83`) executes but its output
  (`AffordanceInfo.cost`) has zero consumers. The dead module and its tests were deleted, proved
  inert by an unchanged-hash diff across all five levels. **`PDR-0045` is untouched — only its
  cited instances were struck** (corrected by pointer, `PDR-0020` practice). Do not re-derive
  the hash claim; it was measured false. The live defect the recon found instead is
  `hamlet-2fe1c34ebb`.
- **`hamlet-7a52a63e0b`** (WS-5 docs) — **partially done and released, deliberately.** Its own
  notes gate the body ("do NOT start doc rewriting yet"); that gate is intact and untouched.
  Only the orthogonal slice ran — removing false completion signals. See comments 139/140.
- **WS-7** `hamlet-e3af412673` (P0, in progress, claude — claim expires 2026-08-16 17:29 UTC,
  NOT refreshed this session; re-claim if lapsed). Open DECIDE unchanged: close now
  (infrastructure proven) or keep as the standing knockdown home. Nothing blocks on it.
- **WS-3** `hamlet-1f89714685` still gates WS-4 `hamlet-15050f280a` (`PDR-0034`). **WS-6**,
  **WS-0** ready, untouched. Tooling P3s: `hamlet-312f75963b`, `hamlet-5e2032b166`.

## Merge gates to `main` (`PDR-0039`) — one down, one left

1. ~~**CI restoration**~~ — **DONE AND VERIFIED GREEN** (above). The merge checklist still
   inherits `PDR-0043` trigger 2: restore the nightly cron at merge (or PDR its death) — the
   deferral must not decay into silent capability loss. **Closing the issue did not close the
   deferral.**
2. **README re-verification by the same method, not a re-read** — unchanged, and now the only
   gate standing between this branch and `main`.

**The merge is the reversibility boundary.** Pushing this branch is freely undoable and the
owner has said so (`Owner state`, above); merging to the default branch of a **public** repo
publishes, and no push undoes a reader. Gate 2 is not a formality.

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
- **Committed and pushed** (`f7ef6691` work, `dd94e122` checkpoint), owner-directed — which
  fired the branch's first-ever CI runs, all green, closing `hamlet-2100105c9a` and merge
  gate 1 within the same session that pushed. The "owner pushes" practice is **retired**, not
  suspended: the owner's reason is reversibility (see `Owner state`).

## Next session, start here

1. **Merge gate 2 is the only one left** — README re-verification *by method, not a re-read*
   (`PDR-0039`). Gate 1 closed green this session. Note what the closure does **not** cover:
   the nightly cron is still deferred to the merge (`PDR-0043` trigger 2), and the full-matrix
   workflow remains unrun.
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
`if name == "money"` reads as a helpful default rather than a hardcoded domain fact*. **New
(`PDR-0046`), and the sharpest of the session:** *do not read an observed regularity as a rule —
"the owner has always pushed" became "only the owner may push" became "this push is an
exception", none of which the owner ever said. **Treating a description of what happened as a
prescription about what is permitted** is the same mis-inference as `PDR-0044`'s, running the
other way, and it invents ceremony where there was none.* And its replacement: ***gate on
reversibility, not on the verb** — "who does it" is a weak control and is satisfiable vacuously;
"can this be undone, and by what" names the real boundary, which is why the merge gate is strict
while the push gate is gone.*

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0029`, `PDR-0030`,
`PDR-0031`, `PDR-0032`, `PDR-0034`–`PDR-0042` (per their stated triggers), `PDR-0043` (the
nightly deferral and the provisional-whitelist pattern — reverse only via its three triggers),
`PDR-0044` (the direction's authority — a change of direction supersedes it, nothing else
does), `PDR-0045` (name-blindness — reverse only via its three triggers), `PDR-0046` (the agent
may push the branch; do not re-derive a push gate — the boundary is the merge).
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-14, unchanged; changing it escalates.
