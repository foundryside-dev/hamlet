# Current State — HAMLET / Townlet        Checkpoint: 2026-08-13 · seventh checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). **WS-1 is COMPLETE
and CLOSED** (`PDR-0029`, all ten units, tree green at every commit, batch gate 2981/0 at
`e8ad4985`) — the oracle freeze is no longer gated on correctness fixes. **WS-7 is now the
critical path** and is unclaimed. Selection criterion for what gets strangled next,
owner-stated: *"strangle wherever the runtime still knows what the game is"* (`PDR-0019`).

**READ `docs/architecture/vfs.md` BEFORE TOUCHING VFS** (2455 lines, binding). Two confident
diagnoses were corrected by design docs that existed the whole time — **check
`docs/architecture/` before concluding shipped behaviour is simply wrong.**

## Owner state (2026-08-13)

- **Authority grant re-confirmed verbatim** by the owner this session; the standard grant in
  `vision.md` stands unchanged.
- **Nothing is blocked on the owner** except the standing item: the README *push* (drafting
  and committing locally is endorsed).

## In flight / ready

Recovery milestone **`hamlet-1ade187dcc`**. Nothing is claimed right now.

- **WS-7** `hamlet-e3af412673` (P0, READY — unblocked by WS-1's close). **The
  known-divergences register must be its FIRST artifact** (`PDR-0028` reversal trigger fires
  on routing-to-nowhere; `PDR-0022`'s deletion condition depends on it). Waiting to enter the
  register: `hamlet-2dde1015fe` (nine dead hashes) and `hamlet-df2b972c49` (two uncovered
  stamp/compare paths). Then determinism via child `hamlet-834108b55a` (no seeding API — fix
  FIRST per the issue), oracle tag, differential harness, per-unit seam cutting. **Mine
  `docs/plans/2026-05-15-compiler-cleanup-modernization.md` for the knockdown playbook** —
  the owner already ran this operation once on the compiler. First knockdown candidate to
  decide: terrain/substrate.
- **WS-6** `hamlet-5e39fcccb0`, **WS-0** `hamlet-8eeaba1461` — ready, untouched.
- **WS-4 additions** (unchanged): `hamlet-310e336786`, `hamlet-f46e2b381a`,
  `hamlet-fa6bb6da4a`, `hamlet-e979f2ba37` (`PDR-0026` acceptance shape),
  `hamlet-365e996511`, `hamlet-0dd4ac24d9`, `hamlet-0cdb8a6d1a` (`PDR-0024`), and
  `hamlet-0d0115383e` (per-level `architecture`, `PDR-0027`, unblocked).
- Hash-boundary tests remain unwritten: `hamlet-c8c316ba03`.

## Open questions / blocked-on-owner

- **README push** remains the owner's call; drafting and committing locally is endorsed.
- Open, not blocking: the five shipped levels are three universes (WS-3 scoping input); the
  inert-surface baseline (~40) needs one itemized recount before the two counters can merge.

## What this checkpoint did

- **Landed task 3b** (dead agents stop transacting; two-name form per plan §0.1) and **ran
  task 8**, closing WS-1 at `e8ad4985`. Red/green verified; two named mutations each caught
  by its intended test in a detached worktree. One gate-time surprise root-caused: two
  latent CPU-vs-CUDA test defects exposed by the fix, repaired to the file's own pattern.
- **PDR-0029** — WS-1 accepted complete against the plan's §4 definition of done and closed;
  reversal triggers bound to the oracle tag and the differential harness.
- **Metrics re-read**: Gates green 4 of 4 HELD (2981/16/0). No reversal trigger fired.
  Provenance-integrity row still amber pending the register.
- **Tracker reconciled live**: `hamlet-88acec4bb5` and `hamlet-67ffbd282a` closed with full
  landing records (WS-1 comments #125–#127; #127 corrects #126's normalization-mode claim);
  WS-7 auto-unblocked. Smoke record for the freeze owner is in comment #126.

## Next session, start here

**Claim WS-7 (`hamlet-e3af412673`)** and stand up the known-divergences register first —
enter `hamlet-2dde1015fe` and `hamlet-df2b972c49` before anything else routes there. Then
the seeding API (`hamlet-834108b55a`), then the oracle tag. The Provenance-integrity
guardrail row goes green when the two filed gaps are in the register.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before every measurement; verify
red by mutation in a detached worktree (never `git stash` — operator hook); a green test is
not evidence, mutate before believing; enumerate producers, not call shapes; a correction is
not self-verifying — check it against source before recording it (comment #127 is this
session's instance).

Do not re-litigate: `PDR-0006` (strangler), `PDR-0007` (universality), `PDR-0014`–`PDR-0016`
(bounds), `PDR-0022` (deletion, decided), `PDR-0026`–`PDR-0028` (owner-resolved),
`PDR-0029` (WS-1 closed — residuals route to the register or WS-4, not to a reopened WS-1).
Read `vision.md` first: ENDORSED, amended 2026-08-13 with owner sign-off, grant re-confirmed
2026-08-13; changing it further escalates.
