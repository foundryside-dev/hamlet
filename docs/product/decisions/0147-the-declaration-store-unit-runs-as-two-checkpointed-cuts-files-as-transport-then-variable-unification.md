# PDR-0147 — The declaration-store unit runs as two checkpointed cuts: files-as-transport (hash-identical) first, variable-surface unification (hash-moving) second

Date: 2026-09-02   Status: **accepted** (scope ruling within the grant — prioritisation of a
unit the owner already chose in `PDR-0146`; the cut was offered with a recommendation at the
`/own-product` resume and the owner selected it)
Author: Claude (standing product owner), decision confirmed by John
Owner sign-off: yes (*"One unit, two cuts: A files-as-transport, then B variable unification"*)
Related: `PDR-0117` (the unit's five calls), `PDR-0121` (the declaration-store target shape and
the hash-identical yolo-limiter), `PDR-0132` (the checkpointed-milestone pattern this reuses),
`PDR-0143` / `PDR-0144` (the two banked inputs), `PDR-0146` (the unit chosen)
Tracker: `hamlet-33e520cebd` (symbol-table half, lands in cut B), `hamlet-af929afa06` (closed;
its parked items land in cut A), `hamlet-obs-982755441c` (stray files, the forcing case for
cut A), `hamlet-obs-b959ce55c0` (dead durability rows, read at cut A's capacity review).
Implementation and acceptance issues for each cut are filed at DISPATCH, per `PDR-0117`.

## Context

`PDR-0146` committed the declaration-store compiler unit as the Now bet's next unit and left
its scope ruling to this session. `PDR-0117` and `PDR-0121` both say the file-discovery front
end and the collapse of the three variable-declaration surfaces are *one unit* — the same
compiler front end, the same defect seen from two sides. What was open is whether they are one
*cut*: one branch, one landing, one hash reading — or two.

Three inputs were already banked: the `period: 24` / `day_length: 24` duplication across
`stratum.yaml` and `curriculum.yaml` (`PDR-0143`), the `filler_ref` string contract on
`SlotBinding` wanting a typed `scope` (`PDR-0144`), and `configs/test/items_smoke` carrying
files no loader reads plus pack-root duplicates of level files (`hamlet-obs-982755441c`).

## Options considered

1. **One unit, two checkpointed cuts** — A: files become transport (discovery, merge by
   declared id, loud collision refusal, canonical order, per-declaration provenance,
   "required file" → "required declaration"); B: the three variable surfaces become one
   declaration semantics, every declared variable enters the symbol table, `filler_ref`
   becomes a typed scope. *Pro:* cut A can be held to `PDR-0121`'s bar — compiled hashes
   byte-identical across every shipped level — because it changes where declarations come
   from, not what they compile to; cut B cannot, because unifying `lifetime`/access semantics
   and admitting `variables_reference.yaml` variables moves `variable_schema_hash`, so it needs
   a differential-harness run and a register entry. *Con:* two landings, two checkpoints.
2. **One cut, everything together.** *Pro:* one branch, one PRD. *Con:* the hash-identical
   bar is lost for the whole cut, so a hash movement cannot be attributed to the front end or
   to the unification; the cheapest verification the unit has is spent.
3. **Cut A only, decide B at the next resume.** *Pro:* smallest commitment. *Con:* relitigates
   a ruling `PDR-0117` and `PDR-0121` already made (one unit); the unification is not
   optional, only its timing was.

## The call

**Option 1.** One unit, two cuts, in that order, each with terminal tracker evidence and a
committed product checkpoint before the next begins — the `PDR-0132` shape.

- **Cut A — files are transport.** Bar: compiled hashes (`config_hash`, `layout_hash`,
  `variable_schema_hash`, `environment_hash`) byte-identical across every shipped level before
  and after; every stray file in `items_smoke` refused loudly by name; the `period`/`day_length`
  duplication resolved to one declaration (a single-source rule, not a tolerated pair);
  per-declaration file:line reaches every refusal. `hamlet-obs-982755441c` is discharged by the
  refusal test, not by deleting the files first.
- **Cut B — one variable declaration semantics.** `environment.yaml`, `vfs_profiles.yaml` and
  `variables_reference.yaml` stop being three semantics; every declared variable enters the
  symbol table (`hamlet-33e520cebd` closes); `SlotBinding.filler_ref` becomes a typed `scope`.
  Expected to move `variable_schema_hash`; lands only with a differential-harness run and a
  `DIV-0xx` entry.
- **Explicitly not in either cut** (unchanged from `PDR-0121`): orchestrator tiers, the
  sub-compiler graph engine, incremental compilation. The epistemic-access unit (`PDR-0120`)
  stays second in Next; cut B does not absorb `readable_by`/`writable_by` authoring.

## Rationale

The hash boundary is the reason to split. `PDR-0121` proved the pattern: a cleanup held to a
byte-identical hash bar could be executed fast ("yolo") precisely because the bar made the
result checkable in one diff. Cut A has that property; cut B does not. Landing them together
would mean the first hash movement is ambiguous, and disambiguating it costs more than the
second checkpoint does.

## Also recorded at this resume

- **The authority grant was confirmed unchanged** ("Confirmed, unchanged"). It was reviewed
  today already (`PDR-0146`), so no `Last reviewed` correction is owed and `vision.md` is
  untouched.
- **`PDR-0146` reversal trigger 3 is discharged by the owner**, not the agent: commit
  `a55b5a3f` tracks `.claude/settings.json` and allows `gh pr merge` plus the read-only
  `gh pr` / `gh run` commands; CLAUDE.md now states the `PDR-0101` merge rule and the
  no-compound-command constraint. The autonomous merge is now autonomous in mechanism as well
  as intent. Tags, releases and `gh pr close` remain disallowed by the same rules.
- `main`'s Tests job at `ea3648db` was still `in_progress` at 08:20Z (started 08:03Z; the
  previous run took 29 minutes). `PDR-0145`'s trigger stays armed and unread.

## Reversal trigger

- If cut A cannot be landed hash-identical — if discovery-merge changes any compiled hash on
  any shipped level for a reason other than a pack that was already silently wrong — the split
  has no bar to stand on: stop, record why, and either fold the hash movement into cut B's
  register entry or reinstate `PDR-0117`'s thin-manifest fallback.
- If cut B's harness run shows movement outside `variable_schema_hash` (a `layout_hash` or
  `environment_hash` move), the unification reached further than its scope; it does not land
  until the extra movement is bisected and registered.
- If the epistemic-access work turns out to be unavoidable inside cut B (a declared variable
  cannot enter the symbol table without an access-role decision), reopen this ruling rather
  than absorbing `PDR-0120` silently.
