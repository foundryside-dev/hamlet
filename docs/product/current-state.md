# Current State — HAMLET / Townlet        Checkpoint: 2026-09-02 (fifty-third) · `main` at `ea3648db` (green), branch `project-recovery-4` · scope ruled (`PDR-0147`), recovery progress read

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) remains the Now bet.

- **`main` at `ea3648db` is fully green** (Lint, Config Validation, Tests 33m36s; nightly ✅
  2026-09-01). Active branch **`project-recovery-4`**; at this checkpoint it carries the two
  workspace commits, `a55b5a3f` (settings tracked, `gh pr merge` allowed) and `a8b66984`
  (`loomweave.yaml` untracked), plus this checkpoint. Nothing under `src/townlet/` has changed
  since the merge.
- WS-1/WS-7 closed; WS-0/2/3/4/5/6 open; oracle still required. Critical path unchanged: WS-6
  `hamlet-5e39fcccb0` → WS-2 `hamlet-337b9e80fb` → WS-3 `hamlet-1f89714685` → WS-4
  `hamlet-15050f280a`. Docs rewrite `hamlet-7a52a63e0b` stays gated on WS-4 (`PDR-0125`).
- **Next unit: the declaration-store compiler unit (`PDR-0117`), scope RULED (`PDR-0147`,
  owner-confirmed): one unit, two checkpointed cuts.** Cut A *files are transport* — discovery,
  merge by declared id, loud collision refusal, canonical order, per-declaration file:line,
  "required file" → "required declaration"; bar: every compiled hash byte-identical across every
  shipped level; `items_smoke` strays refused by name (`hamlet-obs-982755441c`); `period`/
  `day_length` collapsed to one declaration. Cut B *one variable declaration semantics* —
  `environment.yaml` / `vfs_profiles.yaml` / `variables_reference.yaml` become one; every
  declared variable enters the symbol table (`hamlet-33e520cebd`); `filler_ref` → typed `scope`;
  expected to move `variable_schema_hash`, lands only with a harness run and a `DIV-0xx` entry.
  Not in either cut: orchestrator tiers, sub-compiler graph engine, incremental compilation,
  `readable_by`/`writable_by` authoring (`PDR-0120` stays second in Next). **Implementation and
  acceptance issues are not yet filed** — that is DISPATCH, per `PDR-0117`.

**2. Recovery progress — read at source 2026-09-02** (`assessments/2026-09-02-recovery-progress-reading.md`).
Midpoint by the program's own yardsticks: 2 of 8 workstreams closed, the critical path unstarted,
WS-4 at 11 of 54 children closed, bet exit (`PDR-0058`) 0 of 3. Config-surface coverage re-read
for the first time since 2026-08-17: **2 closed / 3 partly wired / 2 not started** (DAC and VTC
writes closed-but-unproven; VFS, effects, items partial; substrate topology authoring and
curriculum untouched). BAC 1 of 3 layers; export path absent. The `PDR-0147` unit is the first
that closes a whole surface rather than widening one.

**3. Fifteen P1 bugs in `triage`, none inside a unit.** `hamlet-d6fc84d147` (dead-agent step
counter, needs a register entry, `PDR-0140`) and `hamlet-4b931faaf4` (held items invisible to the
`item` token type, `layout_hash`-moving) still owe a divergence-register triage before any engine
change. The rest are WS-4 authorability gaps; `hamlet-fc78bb49d3`, `hamlet-83a043a9b9`,
`hamlet-33e520cebd` belong to the epistemic-access or declaration-store units.
**Tracker truth:** `hamlet-3381043d2e` (action writes) carries a compiler claim false since
`7cbfbff8`; annotated, reclassified WIRED-UNPROVEN, left in triage. A source pass over the 35
WS-4 triage items is owed before WS-6 assigns causes.

**4. Documentation truth** (`PDR-0125`): README stamped at `1eb347f7` (`PDR-0145`). Pending
observations: `hamlet-obs-982755441c` (stray files, discharged by cut A's refusal test) and
`hamlet-obs-b959ce55c0` (dead durability rows, read at cut A's capacity review); both expire
2026-09-16.

**5. Weft tooling** (`PDR-0139`): loomweave index fresh at `a8b66984` (8,166 entities). Wardline
still uninstalled (server configured, executable absent).

## What this checkpoint did

- Committed `PDR-0147` (written and owner-confirmed at the resume — *"One unit, two cuts"* — but
  left untracked on disk); the brief now reads the scope as ruled, not pending.
- Took the owner-requested recovery progress reading against tracker and source; recorded it as
  an assessment and refreshed `metrics.md`'s config-surface row, unread since 2026-08-17.
- Tracker: one comment (`hamlet-3381043d2e`, stale compiler claim). No issues opened or closed;
  no new PDR — the reading is not a decision.

## Standing gates

1. `PDR-0127` gate set: `main@ea3648db` all green; no local re-run (docs-only commits since the
   3,846-pass reading at `a07b889b`).
2. Dependabot #33 (torch) and #34 (pytest) remain open since 2026-08-15.
3. No release, tag, announcement, 1.0 declaration or external coordination is authorized here.

## Open questions / blocked on owner

- **Nothing escalated.** The reading, the metrics refresh, the tracker comment and this commit
  are inside the grant. `vision.md` untouched.

## Decision checks

- `PDR-0147` trigger 1 is now the live one: if cut A cannot land hash-identical, stop and record
  why before folding movement into cut B.
- `PDR-0143`/`0144` reversal trigger (L2 four-cell floor on a post-unit-5 commit) is **armed and
  unread** — no harness run since unit 5.
- `PDR-0058` trigger 2 (register grows two checkpoints without an entry going terminal): the
  register has grown once since `DIV-011` (`DIV-012`, built) with none terminal; cut B will add
  another. Watch it — a second growth without a terminal entry fires the trigger.
- `PDR-0145` trigger 3: a second "fix at next touch" observation surviving a touch converts
  file-triggered observations into filed issues.

## Next session starts here

1. `/own-product`: confirm the grant; index is fresh, `main` is green — nothing to read there.
2. **DISPATCH cut A of the declaration-store unit** (`PDR-0147`): `/write-prd` against the cut-A
   bar (hash-identical across every shipped level, stray-file refusal, single-source
   `period`/`day_length`, file:line on every refusal) → plan → file implementation and
   acceptance issues under `hamlet-15050f280a` → execute in a worktree, the `PDR-0121` shape.
3. Before cut B or any engine change: triage `hamlet-4b931faaf4` and `hamlet-d6fc84d147` into
   the divergence register.
