# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 (latest) · nineteenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, and it
**continues** — but its exit is now stated differently, and the last session's framing of it was
wrong in a way worth reading before anything else.

**THE MERGE TO `main` HAPPENED.** PR #32, `07b26ed5`, 2026-08-15 14:09 AEST, by the owner. Both
gates were discharged first at `33bfff51` — nightly cron restored (`PDR-0043` trigger 2 did not
fire), README re-swept **at the merge commit** per `PDR-0039`, finding five more stale claims in
four commits. `main` now carries the recovery. Work continues on **`project-recovery-2`**, branched
from the merge, currently **13 commits ahead** of `main`.

**The bet's exit was mis-stated, and the owner ruled on it** (`PDR-0058`). `roadmap.md` used to say
*"the merge to `main` is the bet's exit"* — so the exit was defined as an event this workspace
neither controls nor performs, no reading was attached to it, and when it fired **four consecutive
checkpoints kept asserting "the merge remains available and untaken."** Restated: **the Now bet
exits when the pinned oracle can be RETIRED** — (1) every `docs/oracle/known-divergences.md` entry
terminal, (2) the harness's verdict vocabulary re-earned or its successor recorded (`PDR-0056`:
`AGREE` is currently unreachable matrix-wide), (3) `Gates green` read on a suite that hides
nothing. **Merging is a publication step inside the bet, not the end of it**, and gate 2 re-fires
at the next merge — 13 commits already owe it. `Config-surface coverage` 7 of 7 is **WS-4's** exit,
not this one.

**READ `docs/architecture/vfs.md` AND `docs/architecture/vfs-current-implementation.md` BEFORE
TOUCHING VFS** (binding, owner-named). Both were corrected at the eighteenth checkpoint — the
ten-kind list is now nine.

## Owner state

- **Grant unchanged.** Re-confirmed again at this session's `/own-product` resume, scope identical;
  stamp stays `2026-08-15`, next review due **2026-09-15**. `vision.md` untouched.
- **`PDR-0046` stands**: commit and push `project-recovery*` freely (the glob covers
  `project-recovery-2`); **the merge to `main` and anything outward-facing stop for the owner.**
  The owner has now exercised that merge once, which does not make the next one routine.
- **Owner rulings still governing:** `PDR-0047` (closed vocabularies), `PDR-0052`
  (underspecification is a compile error; wiring first), `PDR-0053` ruling (a), and now
  **`PDR-0058`** (the merge is an output, not the outcome).
- **Standing directive, still live:** *"the system likely has more ambiguities, this strangulation
  exercise is our chance to clean them all up."* The `PDR-0053` taxonomy is the map.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **`hamlet-a0832f9004`** (P1, filed this session) — **31 tests fail on `main` and no gate can see
  them.** `pyproject.toml`'s default `addopts` carries `-m "not slow"`; the three failing
  integration files are all `slow`-marked, so the local gates and CI's Tests job both deselect
  them. **This is the next unit** (`PDR-0059`), ahead of `semantic_type`; parented to the milestone, labelled **WS-2** (cause-triaged deletion) rather than WS-4 — it is gate hygiene, not authoring surface. Order matters: run the
  three files and diagnose **by execution** first, repair-or-delete second, and only then decide
  the marker's fate — fixing the deselection first turns every local gate red and makes the repair
  unmeasurable.
- **`hamlet-2fe1c34ebb`** (P1) — `semantic_type`, three disagreeing vocabularies, `default="custom"`
  on a parameter feeding a provenance hash. **Displaced by one position, not dropped.** Same shape
  as the surface closed at `PDR-0057`, same `PDR-0047` rules, DIV-004 to extend rather than a new
  register entry, register-first per `PDR-0037`. **Measure the hash movement against a worktree; do
  not predict it.**
- **`hamlet-0dd4ac24d9`** (P1) — presentation hardcoded by variable name. The `PDR-0045`
  name-branch class.
- **`hamlet-f46e2b381a`** (P1) — `clamp_and_validate` is a declared-but-empty transition phase.
- **`hamlet-f9090ec3e8`** (P2) — **rescoped this session** from one flaky test to the class:
  *wall-clock ratio assertions inside the CI gate*, two known instances, both reddening at random
  under always-on `--cov` (`PDR-0060`).
- **`hamlet-cbb747a51e`** (P2) — a pack compiles, exits 0, writes no cache artifact.
- **WS-7** `hamlet-e3af412673` (P0, in progress). Open DECIDE unchanged: close now, or keep as the
  standing knockdown home.
- **WS-3** `hamlet-1f89714685` still gates WS-4 `hamlet-15050f280a` (`PDR-0034`). **WS-6**, **WS-0**,
  **WS-5** ready, untouched.
- **Closed this session:** `hamlet-2090c9f16d` (P0 — the fix landed at `49bdf28e` last session but
  the issue was never moved off `triage`; walked through `confirmed → fixing → verifying → closed`
  with its acceptance evidence recorded).

## Open questions / blocked on owner

- **Nothing is blocked.** No escalation from this session — the two owner-facing items (the grant,
  and the bet's exit) were both put to the owner at the resume and both answered.
- **`Gates green` is NOT green, and the green at HEAD is the evidence for that, not against it.**
  All three CI workflows passed on `d5bfcc38` (Lint, Config Validation, Tests — run
  `31887137993`). The Tests job is the one carrying `-m "not slow"`, so it passed over a suite
  that excludes the 31 known failures. Do not read that run as the row being green; it is what
  being wrong looks like here.
- **The next merge owes `PDR-0039`'s sweep** on 13 commits' worth of drift, and the README on
  `main` is accurate only as of `07b26ed5`.
- **Watch, do not act:** the ~21% `env.step` cost (`PDR-0057`) — escalate only if measured as
  blocking a real training run. Note the interaction `PDR-0060` records: a real performance
  regression and a flaky performance gate now coexist, and the flaky gate is what would make a
  real one unreadable.

## What this checkpoint did

- **Ran ORIENT and found the merge had landed seven hours before the workspace last claimed it
  hadn't.** Recorded the correction, and — more usefully — the structural reason it survived four
  re-readings: an exit defined as someone else's action has no reading attached to it
  (`PDR-0058`).
- **Read the restored nightly and found 31 permanently-red tests behind a marker deselection**
  (`PDR-0059`, `hamlet-a0832f9004`). The deferral `PDR-0043` recorded paid off the first night it
  ran. The lesson entered `metrics.md`: re-reading a guardrail is necessary and not sufficient —
  the command it is read with is part of the reading.
- **Adjudicated `PDR-0043` reversal trigger 1 as NOT FIRED**, with the reasoning written down
  rather than the conclusion (`PDR-0060`), and rescoped `hamlet-f9090ec3e8` from a test to a class.
- **Reconciled the tracker**: closed the P0 that the last brief wrongly recorded as closed, filed
  the new P1, retitled and commented the rescoped P2. One ORIENT flag was **withdrawn** —
  `hamlet-fba56feca5` sits at `done`, which is terminal for a `feature`, so it was correctly closed
  and the drift I reported on it was mine.

## Next session, start here

1. **`hamlet-a0832f9004`** — run `uv run pytest -m "slow or not slow"` on the three files, diagnose
   by execution, repair-or-delete per zero-backcompat, marker decision **last**. If the failures
   turn out to be predominantly live product defects rather than stale tests, **stop and escalate**
   before deleting anything (`PDR-0059` reversal trigger).
2. **Then `hamlet-2fe1c34ebb`** (`semantic_type`), register-first, hash movement measured not
   predicted.
3. **The next merge is the owner's** and owes the `PDR-0039` sweep on 13+ commits.

**Harness gate contract** (carry): `uv run python -m townlet.oracle.harness [--cuda]` — exit 0 iff
every cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its register entry; empty and
all-SKIPPED runs fail. **Read `PDR-0056` before trusting a green run**: exit 0 now means
"everything diverged exactly as registered", which is weaker than "old and new agree". NOT safe to
run concurrently with itself in one checkout.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before measurements; verify red by
mutation; a green test is not evidence; a correction is not self-verifying; a verifier is not
self-verifying; *a red found by reading is not a defect until it executes* (`PDR-0049`); *a red
found by a TOOL is not a defect until the tool is validated against something you already know the
answer for* (`PDR-0053`); *point an instrument at the code BEFORE the design* (`PDR-0057`);
*measure hash movement, never predict it*. **New this session:** *an exit you do not perform is an
exit you will not notice firing* — state a bet's exit as a condition you can read, never as an
event someone else causes. And its sibling: **audit the scope of the command a guardrail is read
with**, because a gate can be run, read, honest, and still blind.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0032`, `PDR-0034`–`PDR-0042`,
`PDR-0043`, `PDR-0044`, `PDR-0045` (principle intact; its two cited instances struck per
`PDR-0049`), `PDR-0046`, `PDR-0047`, `PDR-0048` (its "SATISFIED but NOT BANKED" framing is
answered by `PDR-0058`), `PDR-0049`, `PDR-0050`, `PDR-0051`, `PDR-0052`, `PDR-0053` (Finding A
withdrawn — do not resurrect it), `PDR-0054`–`PDR-0060`.
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-15, unchanged; changing it escalates.
