# PRD-0002 — Declaration-store unit, cut A: files are transport            Status: accepted (PDR-0149)

Decision: `PDR-0147` (scope ruling: one unit, two cuts, this is cut A), standing on `PDR-0117`
(the unit's five calls, owner-directed), `PDR-0121` (the declaration-store target shape and the
hash-identical bar), `PDR-0146` (the unit chosen by the owner at the fifth merge)
Bet (`roadmap.md`): **Now** — the strangler rewrite (`PDR-0006`); this cut is its committed next
unit, the first item under Next
Target metric (`metrics.md`): input — **Failure loudness**
Guardrails pulled (`metrics.md`): **Provenance integrity**, **Gates green**, **Pre-release
hygiene**, **Documentation truth**
Tracker: implementation `hamlet-e62029114c`, acceptance `hamlet-41e79fb08b` (accepted at
`75383d18` under PDR-0149), both under `hamlet-15050f280a` (WS-4), filed 2026-09-02; inputs `hamlet-obs-982755441c`, `hamlet-obs-b959ce55c0`, `hamlet-af929afa06` (parked
items); `hamlet-33e520cebd` is cut B's, not this cut's
Written: 2026-09-02, at the fifty-fourth resume, under the grant confirmed the same session

## Problem

**Who.** The pack author — the designer or prototyping modeller `vision.md` names as the person
this substrate is judged by, who writes a universe as YAML and never touches Python. In the near
term that author is John and the standing agent writing test, differential and reference packs;
the aspirational author is the one with a mechanic idea who names files after their own concepts.

**The problem.** The compiler decides what a file *means* from its *name*. Sixteen distinct
filenames are hardcoded across nine compiler modules (measured 2026-09-02: 88 literal
occurrences under `src/townlet/universe/`), and a file the compiler is not looking for is
silently ignored. This is not hypothetical: `configs/test/items_smoke` today carries three files no
loader reads and three pack-root duplicates of level files, and `validate --primary-level
L0_smoke` succeeds in 98 ms with no message. An author who mistypes a mandated name, or names a
file `ship.yaml` because that is what it declares, gets a universe missing the declaration and no
error — the failure `CLAUDE.md` names as the worst one, a wrong key compiling to an empty
catalog. The same file-is-semantics rule forces one fact to be declared twice when two files own
it: `period: 24` in the pack's `vfs_profiles.yaml` and `day_length: 24` in the L3 level's
`curriculum.yaml`, with nothing checking they agree (`PDR-0143`). And when the compiler does
refuse, it cannot always say where the offending declaration came from: file:line provenance was
wired for the main raise sites in `PDR-0121` but parked for the preflight, load-error,
vocabulary-lockstep and limits families.

**The desired outcome.** The author writes declarations in whichever files they like, subfolders
included; every YAML document in the pack is read; a document the compiler cannot place, or a
declaration made twice, is refused at compile time with an error naming both files and lines; a
required thing is a required *declaration*, never a required *filename*; and a fact is declared
once. Nothing about what the packs compile *to* changes — this cut moves where declarations come
from, not what they mean.

**Why now.** Unit 5 landed and the owner chose this unit next (`PDR-0146`). All three forcing
inputs are banked and measured. Cut A is the only part of the unit that can be held to a
byte-identical hash bar, so it goes first, before cut B moves `variable_schema_hash` and makes the
first hash movement unattributable (`PDR-0147` rationale). The stray-file observation expires on
2026-09-16; this cut is what discharges it.

## Success metric (the signal the bet paid off)

**Failure loudness** (`metrics.md`, input): an authoring mistake produces a clear compile-time
error rather than a silent no-op; target 100% of known classes.

- **BASELINE** (last read 2026-08-17, re-confirmed 2026-09-02): the *stray or misplaced
  declaration* class is **SILENT** — `items_smoke` compiles clean with six such files. The
  *duplicated fact* class (`period` / `day_length`) is **SILENT** — no check that the two agree.
- **TARGET**: both classes **LOUD** at compile time, each refusal naming file and line, with a
  committed test per class, on the cut-A checkpoint commit, **by 2026-10-01** (owner-authorized extension in PDR-0149).
- **Falsification**: on 2026-10-01, if any file in a pack can still be ignored without a compile
  error, or a fact can still be declared twice with disagreeing values without one, the bet has
  not paid off.

## Acceptance criteria (falsifiable)

All criteria are read on the cut-A checkpoint commit, and all are due by **2026-10-01**,
end of day Australia/Canberra (PDR-0149, implementing the owner-authorized extension).
The original September 16 window was missed; PDR-0148 records that historical reading.
Missing the revised date without an accepted extension recorded in a PDR is a reject on
every criterion.

1. **SUCCESS — stray declarations are loud.** Compiling `configs/test/items_smoke` as it stands
   at `ea3648db` (strays present) refuses, and the error names every file that no declaration
   family consumes and every pack-root file that duplicates a level file, each with its path and
   line. A committed test pins this refusal against a fixture that keeps the strays; the live pack
   is then corrected so it compiles again.
   Reject branch: any such file survives compile silently, or the pack is "fixed" by deleting the
   strays before a refusal test exists → unmet; `hamlet-obs-982755441c` is promoted to an issue
   rather than discharged.
2. **SUCCESS — one fact, one declaration.** In `configs/default_curriculum` the day-length fact is
   declared exactly once; the compiled L3 level's day length and the `day_phase` token's cyclical
   period both derive from that one declaration; and a pack that declares two disagreeing values
   is refused naming both declarations.
   Reject branch: the pair is still tolerated, or the refusal names only one of the two → unmet.
3. **SUCCESS — required declaration, not required filename.** For at least one level of
   `default_curriculum`: moving a level's `drive` declaration into a differently named file
   compiles to an artifact whose hashes are identical except `config_hash`; omitting the
   declaration entirely refuses with an error that names the missing *declaration*. Pinned by
   test.
   Reject branch: any refusal message that reports a mandated filename as missing → unmet.
4. **SUCCESS — collisions are loud.** Two documents declaring the same declaration id refuse with
   one error naming both file:line locations. Pinned by test, for at least one declaration family
   at pack level and one at level scope.
   Reject branch: last-writer-wins, first-writer-wins, or an error naming one location → unmet.
5. **SUCCESS — provenance reaches every refusal.** Every refusal raised by the discovery and
   merge front end, and every refusal in the four site families `PDR-0121` parked (preflight,
   load-error, vocabulary-lockstep, limits), carries file:line. Measured by a test that walks the
   registered error codes for those families and asserts a source location on each raised
   instance.
   Reject branch: one refusal in the pinned set without a location → unmet.
6. **GUARDRAIL — provenance integrity: the hash bar.** For every pack/level case the
   discovery-driven smoke test enumerates (31 at `a07b889b`), every hash on the compiled level
   artifact **other than `config_hash`** is byte-identical before and after this cut, read from a
   before-snapshot committed before the first source change. `config_hash` — a digest of the
   pack's raw files — may move **only** for the packs whose YAML files this cut edits (the
   `items_smoke` correction and the day-length single-sourcing) and for no other pack.
   Reject branch: any other movement → cut A does not land; `PDR-0147` reversal trigger 1 fires:
   stop, record why, and either fold the movement into cut B's register entry or reinstate
   `PDR-0117`'s thin-manifest fallback. The bar is never lowered to make the cut land.
7. **GUARDRAIL — gates green and harness clean.** On the cut-A commit: ruff, black, mypy, the
   no-defaults lint with no new whitelist entry, the compiler CLI validation over every pack, and
   pytest all pass locally; every CI row at the pushed tip is green by the `PDR-0127` method; and
   a differential-harness cpu matrix run reports every cell `AGREE` or `DIVERGED_AS_REGISTERED`
   with exit 0 and **no new hash or stream divergence**. The two pack edits this cut makes are
   input drift against the frozen fixtures, which the harness refuses undeclared; they are
   registered as one **pack-drift-only** entry in the `DIV-007` shape (no hash fields, no
   streams, cells still `AGREE` on every hash and stream not already covered). That input-axis
   entry is expected and is not the register growth `PDR-0058` trigger 2 counts, because it
   records no behaviour or provenance movement.
   Reject branch: any red row, any cell needing a hash or stream declaration, or an input-drift
   row not described by the entry → the cut changed something it was not allowed to change;
   not acceptable.
8. **GUARDRAIL — pre-release hygiene and documentation truth.** No compatibility path exists: no
   manifest file, no "legacy filename" branch, no warning where an error is specified. No filename
   literal under `src/townlet/universe/` selects a loader, a validator or an error message by
   filename (down from 88 occurrences; any that remain are listed in the acceptance record with
   the reason each is not semantic). Every canonical document that teaches mandated filenames
   (`CLAUDE.md`'s pack layout, `docs/architecture/COMPILER.md`, the affected
   `docs/config-schemas/` pages) is corrected in the same cut.
   Reject branch: a compatibility path, an unexplained semantic filename literal, or a canonical
   doc still teaching a mandated filename → unmet, and the documentation-truth count is read as
   increased.

## Non-goals (this bet)

- **Cut B** in its entirety: unifying `environment.yaml` / `vfs_profiles.yaml` /
  `variables_reference.yaml` into one declaration semantics, entering every declared variable
  into the symbol table (`hamlet-33e520cebd`), and replacing `SlotBinding.filler_ref` with a typed
  scope. Cut A must not need to touch variable semantics to land.
- The three-tier orchestrator, the sub-compiler graph engine, and incremental compilation
  (`PDR-0121` call 2).
- `readable_by` / `writable_by` authoring and any epistemic-access work (`PDR-0120`, second in
  Next). If a declaration cannot be placed without an access-role decision, `PDR-0147` trigger 3
  reopens the ruling; it is not absorbed here.
- Any change to what a pack compiles to, beyond the two content edits the criteria name. No
  engine, environment, training or network changes.
- Fixing `hamlet-obs-b959ce55c0` (dead durability rows) or `hamlet-4b931faaf4` (held items
  invisible). The capacity mismatch is *read* at this cut's capacity review and recorded; both
  stay filed.
- Editing anything under `.oracle/` or the frozen oracle fixtures, including the fixture mirror
  of `items_smoke` that carries the same strays.
- Pack composition features (mixins, mod-packs, override packs). Subfolder *discovery* is in;
  cross-pack *composition* semantics are not.

## Constraints & guardrails

- **Zero backwards compatibility** (`CLAUDE.md`): the mandated-filename contract is deleted, not
  wrapped. Old packs that relied on a filename fail loudly; nothing accommodates them.
- **Determinism**: merge order is canonical and content-independent, so a pack compiles to the
  same artifact on every machine. Criterion 6 is the check.
- **Fail loud, name both sides**: every refusal names the declaration and the location; a
  collision names both locations. This is the house style the token spec's indistinguishability
  check already sets.
- **The oracle never mutates**: the differential harness adjudicates this cut; a diff against the
  oracle is a defect in the rebuild unless the register says otherwise.
- **Execution shape**: the `PDR-0121` pattern — an isolated worktree, a committed before-snapshot
  of every hash across every smoke case, the full gate set on the rebased branch before landing.
  (Process, not design; recorded so the plan inherits it.)
- **No behaviour change under the hash bar**: if a step cannot be done without moving a
  non-`config_hash` hash, it belongs to cut B and is parked, not forced.

## Open questions / assumptions

- **A1 — the date. OWNER-CONFIRMED 2026-09-02** (*"Keep 2026-09-16"*). Chosen because it is
  the expiry of the stray-file observation this cut discharges. **Superseded by PDR-0149:**
  on October 1 the owner authorized extending the date; the agent selected October 1,
  end of day Australia/Canberra, the verified completion date. September 16 remains the
  historical missed window. All technical criteria are unchanged.
- **A2 — `config_hash` is exempt for edited packs. OWNER-CONFIRMED 2026-09-02** (*"Yes, exempt
  config_hash on edited packs"*). `config_hash` digests raw file paths and contents, so any pack
  edit moves it by construction. `PDR-0147`'s bar therefore applies to the semantic hashes on
  every case, with `config_hash` movement permitted only on the packs this cut edits. This is
  the reading criterion 6 and `PDR-0147` trigger 1 are judged against.
- **A3 — the single source for day length.** `day_length` is declared per level in
  `curriculum.yaml` and is `null` on every level without temporal mechanics, while `period: 24`
  is pack-level in `vfs_profiles.yaml` and reaches every level's `day_phase` token. Which
  declaration survives, and what a level without temporal mechanics declares for a cyclical
  token, is solution shape routed to the architect. The criterion only requires one declaration
  and a refusal on disagreement.
- **A4 — `experiment.yaml` classification. RESOLVED 2026-09-02 at source:** the pack loader
  requires it (`raw_configs_v21.py` loads it into `ExperimentConfig`, and the environment
  refuses a pack without `experiment_name`), so it is a consumed declaration, not a stray.
  Criterion 1's stray set in `items_smoke` is therefore `drive_as_code.yaml`, `substrate.yaml`,
  and the three pack-root duplicates of level files. `PDR-0142`'s "litter" remark was about the
  retired trial instrument's use of the file, not the file's standing.
- **A5 — which config tree the harness compiles. RESOLVED 2026-09-02 at source:** the old side
  reads `oracle_fixtures/<pack>` with the oracle's code, the new side always reads the live
  `configs/<pack>` with the rebuild's code, so the new compiler never sees the fixture's strays
  and criterion 1 cannot break a cell that way. What the harness *does* refuse is undeclared
  drift between fixture and live pack — hence criterion 7's pack-drift entry. One consequence
  for the plan: `pack_divergence` is one string per cell and the `items_smoke` cells already
  name `DIV-007`, so the new entry either supersedes `DIV-007` on those cells or enumerates
  the new rows in its own per-pack table, the way `DIV-008` did; no drift is blessed by an
  entry that does not describe it.
- **A6 — "every shipped level" is the smoke test's discovered set.** The 31 pack/level cases are
  the measured population; the five `default_curriculum` levels (95 hash fields in `PDR-0121`)
  are the subset that has been held to this bar before.
- **A7 — declaration identity per family** (what "the same id" means for a bar, an affordance, an
  effect, a level) is not defined by this PRD. It is the architect's first question.

## Handoff

- **Top item → `/axiom-planning`:** the discovery-and-merge front end held to criterion 6, with
  criterion 1 as the forcing case. The first plan step is the instrument, not the change: commit
  the before-snapshot of every hash across all 31 smoke cases, then make `items_smoke` refuse.
- **Solution shape → `/axiom-solution-architect`:** declaration identity per family (A7), merge
  and canonical-order semantics, the single-source shape for day length (A3), and where
  file:line provenance attaches so criterion 5 is mechanical rather than per-site.
- **Sequencing and forecast → `/axiom-program-management`:** this PRD carries no date of
  delivery; the revised 2026-10-01 acceptance window (PDR-0149) is not a forecast.
- **Tracker:** file one implementation issue and one acceptance issue for cut A under
  `hamlet-15050f280a`; link `hamlet-af929afa06` (parked provenance sites, criterion 5),
  `hamlet-obs-982755441c` (discharged by criterion 1 or promoted by its reject branch),
  `hamlet-obs-b959ce55c0` (read at the capacity review, not fixed). `hamlet-33e520cebd` stays
  open and untouched for cut B.
- **Acceptance:** `ACCEPT` reads criteria 1–8 on the cut-A checkpoint commit and records the
  verdict in a PDR; the checkpoint that accepts cut A is the gate before cut B begins
  (`PDR-0132` shape).
