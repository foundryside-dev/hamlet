# Current State — HAMLET / Townlet        Checkpoint: 2026-08-15 (latest) · eighteenth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). This session was
**WS-4 work done for real** — the authoring surface, not the scaffolding around it. The
normalization surface is closed: a meter's `range_type` is now its complete, parameterized
observation type, and all nine VFS normalization kinds are authorable *and executed*.

**Both merge gates to `main` remain SATISFIED but NOT BANKED** (`PDR-0048`). `PDR-0039` re-fires
the README sweep at the merge, unconditionally, and **six commits have landed since**. The merge
is the owner's call.

**READ `docs/architecture/vfs.md` AND `docs/architecture/vfs-current-implementation.md` BEFORE
TOUCHING VFS** (binding, owner-named). Both were corrected this session — the ten-kind list is
now nine.

## Owner state

- **Grant unchanged.** Re-confirmed 2026-08-15 (`PDR-0050`); next review due **2026-09-15**.
- **`PDR-0046` stands**: commit and push `project-recovery*` freely; the merge to `main` and
  anything outward-facing stop for the owner.
- **Owner rulings still governing:** `PDR-0047` (closed vocabularies, authors pick from a
  palette), `PDR-0052` (underspecification is a compile error; wiring comes first), `PDR-0053`
  ruling (a) (`range_type` is the complete type declaration) — **all three are now IMPLEMENTED**,
  not pending.
- **Standing directive, still live:** *"the system likely has more ambiguities, this
  strangulation exercise is our chance to clean them all up."* Three were closed this session;
  the taxonomy in `PDR-0053` is the map for the rest.

## In flight / ready

Recovery milestone `hamlet-1ade187dcc`.

- **`hamlet-2fe1c34ebb`** (P1) — `semantic_type` has three disagreeing vocabularies and no
  authority; `default="custom"` violates No-Defaults on a parameter feeding a provenance hash.
  **This is the next unit**: it is the same shape as the one just closed (a declared surface the
  compiler does not consult), governed by the same `PDR-0047` rules, and `PDR-0057` is now its
  worked example. Hash-moving → `PDR-0037` register-first order, and DIV-004 already exists to
  extend rather than a new entry.
- **`hamlet-0dd4ac24d9`** (P1) — presentation hardcoded by variable name. Same family; the
  `PDR-0045` name-branch class this session deleted one instance of.
- **`hamlet-f46e2b381a`** (P1) — `clamp_and_validate` is a declared-but-empty transition phase,
  bounds enforcement hardcoded in 7 places. Adjacent to the work just done.
- **`hamlet-cbb747a51e`** (P2) — a pack compiles, exits 0, writes **no cache artifact**; CI
  cannot see it because the gate runs `validate`, which writes no cache.
- **`hamlet-f9090ec3e8`** (P2) — `test_vfs_overhead_under_limit` flaky by construction, in the CI
  gate. **Now more relevant**: this session measured a real ~21% `env.step` regression, so a
  flaky perf gate is actively unhelpful.
- **WS-7** `hamlet-e3af412673` (P0, in progress). Open DECIDE unchanged: close now, or keep as
  the standing knockdown home. It has now absorbed two harness units (`49bdf28e`, `ecc37241`).
- **WS-3** `hamlet-1f89714685` still gates WS-4 `hamlet-15050f280a` (`PDR-0034`). **WS-6**,
  **WS-0**, **WS-5** ready, untouched.
- **Closed this session:** `hamlet-2090c9f16d` (P0 blocker), `hamlet-1dba1910c0`,
  `hamlet-fba56feca5`, `hamlet-3d3039f340`, `hamlet-365e996511`, `hamlet-7b126ad3fa`
  (`not_a_bug` — the finding was false).

## Open questions / blocked on owner

- **Nothing is blocked.** No escalation from this session.
- **The merge remains available and untaken** — six commits now sit ahead of the last gate
  reading, and `PDR-0039` re-fires the sweep at the merge regardless.
- **Watch, do not act:** the ~21% `env.step` cost is recorded in `metrics.md` and `PDR-0057`
  with an explicit trigger — escalate only if it is measured as blocking a real training run.
  A number is not a problem until something it gates fails.

## What this checkpoint did

- **Closed the P0 oracle blocker and then the normalization programme behind it.** The oracle's
  *inputs* are now frozen (`49bdf28e`), clamping became a required parameter with the redundant
  clamping member deleted (`PDR-0055`), and `range_type` became the meter's complete type with
  one observation field per meter (`PDR-0057`). Money at 1000 observes **0.5**, not **0.000999**.
- **Gave the oracle a second divergence shape, and recorded what it costs** (`PDR-0056`).
  `compare_traces` short-circuited on hash inequality *before* comparing any stream, so WS-4
  would have blinded the harness at the moment of use. Fixed — but `AGREE` is now unreachable
  matrix-wide and the pack-drift guard is armed on zero cells. Both recorded in DIV-004 with
  re-tagging as the reversal trigger.
- **Ran two multi-agent passes and both changed the outcome.** A pre-cut census changed the
  *design* three times (a VTC namespace collision, a silent contiguity hazard, a checkpoint
  mismatch that warned and loaded anyway). A post-cut adversarial review returned 23 findings, of
  which **21 were refuted with executed repros** — and proved the thing that mattered: **9/9
  kinds compile, observe and step**.
- **Corrected the tracker record for `hamlet-1dba1910c0`**, which read `not_a_bug` for a bug that
  was fixed. The workflow only offers `wont_fix`/`not_a_bug` from `triage`; the correct route is
  `triage → confirmed → fixing → verifying → closed`.

## Next session, start here

1. **`hamlet-2fe1c34ebb`** (`semantic_type`), register-first. It is the same shape just closed,
   under the same ruling, with `PDR-0057` as the worked example and DIV-004 to extend rather than
   a new register entry. **Measure the hash movement against a worktree, do not predict it.**
2. **Then `hamlet-0dd4ac24d9`** — the sibling name-branch defect.
3. **The merge is available but not taken.** Both gates satisfied; gate 2 re-fires at the merge.

**Harness gate contract** (carry): `uv run python -m townlet.oracle.harness [--cuda]` — exit 0 iff
every cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its register entry; empty and
all-SKIPPED runs fail. **Read `PDR-0056` before trusting a green run**: exit 0 now means
"everything diverged exactly as registered", which is weaker than "old and new agree". NOT safe
to run concurrently with itself in one checkout.

Carry-ins that keep paying: purge `configs/**/*.msgpack` before measurements; verify red by
mutation; a green test is not evidence; a correction is not self-verifying; a verifier is not
self-verifying; *a red found by reading is not a defect until it executes* (`PDR-0049`); *a red
found by a TOOL is not a defect until the tool is validated against something you already know
the answer for* (`PDR-0053`). **New this session, and the one that paid best:** *point an
instrument at the code BEFORE the design, not only after it* — the pre-cut census changed the
design three times, and every one of those would otherwise have been found by a failing test at
best and by silent breakage at worst. Also: **measure hash movement, never predict it** — the
prediction was recorded first precisely so a surprise would be visible as one, and the fourth
mover appeared exactly where predicted.

Do not re-litigate: `PDR-0006`, `PDR-0019`, `PDR-0022`, `PDR-0026`–`PDR-0032`, `PDR-0034`–`PDR-0042`,
`PDR-0043`, `PDR-0044`, `PDR-0045` (principle intact; its two cited instances struck per
`PDR-0049`), `PDR-0046`, `PDR-0047`, `PDR-0048`, `PDR-0049`, `PDR-0050`, `PDR-0051`, `PDR-0052`,
`PDR-0053` (Finding A withdrawn — do not resurrect it), `PDR-0054`–`PDR-0057`.
Read `vision.md` first: ENDORSED; grant re-confirmed 2026-08-15, unchanged; changing it escalates.
