# Current State — HAMLET / Townlet        Checkpoint: 2026-08-16 (latest) · twenty-second checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`, owner-ruled) — not
when anything merges. Merging is a publication step *inside* the bet.

The three exit conditions, read rather than asserted:

| # | condition | status 2026-08-16 (`a2f349d7`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open (DIV-001..005; DIV-003/004/005 `built`, DIV-001/002 `tag-stamped`) |
| 2 | harness verdict vocabulary re-earned or successor recorded (`PDR-0056`) | open — matrix 16/16 `DIVERGED_AS_REGISTERED`, 0 `AGREE`, by construction until DIV-004 (and now DIV-005, same fixture) closes |
| 3 | `Gates green` read on a suite that hides nothing (`PDR-0059`) | **MET ON THE BRANCH** (`PDR-0065`), re-read green at `a2f349d7`: 3220 / 16 / 0, nothing deselected |

Work continues on **`project-recovery-2`**, now **23 commits ahead** of `main` (`07b26ed5`): 21 at
resume + `a2f349d7` (unit 1) + `0da08142` (owner: doc removal). `main` still carries all 33
formerly-hidden tests behind the marker; its nightly stays red until the merge — which is
**deliberately sequenced after the authoring queue** (`PDR-0068`, owner-chosen) and owes
`PDR-0039`'s README re-sweep on all 23.

## What this checkpoint did

- **Unit 1 of the authoring queue LANDED (`PDR-0066`, `a2f349d7`).** `hamlet-2fe1c34ebb` +
  `hamlet-45b35cfee5` closed with verification. `semantic_type`: one closed vocabulary
  (`townlet/vfs/semantic_type.py`), compiled DTO typed and required (the DTO now constrains the
  compiler), `environment.yaml` variables declare it and the compiler obeys with a group-order
  stable partition (identity on every shipped pack — measured), `bars` reserved to meters at
  compile time, `effects` admitted, the mirror's silent `effects→custom` remap gone; the five
  declarations that reached no compiled field are **deleted** (`VariableDef`, three profile
  classes, `CompiledVariable`). `interaction_type`: one vocabulary, required, both `or "instant"`
  coalesces gone, the zero-importer module that admitted `continuous` deleted.
- **DIV-005 registered → tag-stamped → built in `PDR-0037` order.** Oracle probed at the tag
  before any code changed; movers predicted first, then measured (pre-cut worktree vs live, five
  levels + `effects_smoke`) — matched on every row; matrix `20260816-225750` 16/16 exit 0 with
  exactly DIV-004's four movers, `hash_fields` **not** widened.
- **Docs backflowed on the owner's request:** `vfs.md`, `vfs-current-implementation.md`,
  `UNIVERSE_AS_CODE.md` (three interaction types, not four; `required_ticks → duration_ticks`).
  Owner's diagnosis recorded: VFS was extended late and the docs never followed.
- **Grant re-confirmed and stamp corrected** at an approved touch (`PDR-0067`); sequencing choice
  recorded (`PDR-0068`). Pushed under `PDR-0046`; branch CI Lint + Config Validation green, Tests
  in progress at checkpoint.
- Filed `hamlet-f0ed709ecf` (split `obs_vfs` per variable — where the profile-variable
  declaration returns; also kills a `PDR-0045` name branch); routed two doc gaps to WS-5.

## Reversal triggers — read this session

- **`PDR-0047` trigger 2** (*every pack writes the same value*): reads fired — 50 `custom` lines —
  but did **not**: values were chosen to hold behaviour byte-identical inside a knockdown. Stays
  **armed**, with a protocol: measure it on the first pack authored *fresh* under this surface.
- **`PDR-0058` trigger 2** (*register grows two consecutive checkpoints without an entry going
  terminal*): DIV-005 is growth #1 with nothing terminal. **Armed** — a DIV-006 at the next
  checkpoint with DIV-001..005 all still open fires it, and the answer is a re-tag, not a sixth
  entry (DIV-004's own note says the same).
- **DIV-004's "third widening → re-tag"**: did not fire; DIV-005 did not widen `hash_fields`.

## Blocked on nothing. Flagged for the owner (not blocking, but you should know)

- **`CLAUDE.md:65` cites `docs/architecture/REVIEW-2026-08-15-architecture-docs-and-hld.md`,
  which you deleted in `0da08142`.** Dangling; not fixed here because `CLAUDE.md` is your
  instructions file. One line.
- **The profile-variable `semantic_type` deletion is the one judgment call inside `PDR-0047`**
  (`PDR-0066` §Rationale). Recorded, defensible on the north star, and reversible: if you want
  the field back *before* `hamlet-f0ed709ecf` lands, say so and the fallback is to split the
  block for the scope you need, not to make it required-and-inert.
- **Nothing escalated.** No vision/grant change (the stamp correction was owner-approved,
  `PDR-0067`), no release, no deprecation-with-users, no pricing, no data deletion, no external
  party; the push is inside `PDR-0046`.

## Open questions

- The merge owes `PDR-0039`'s re-sweep on 23 commits; `PDR-0068` says bank it before the next
  queue unit if commits ahead pass ~30 or README decay is measured again.
- `tests/README.md` / `tests/test_townlet/README.md` known-false beyond the marker (WS-5,
  comment 156); no schema doc for `variables[].semantic_type` or `interaction_type` (WS-5,
  comment 157).
- Unchanged: no shipped pack declares a `multi_tick` affordance or wrapping schedule
  (`PDR-0061` trigger armed); an agent cannot observe its own interaction progress
  (`hamlet-266a0a41f0`).

## Next session starts here

**`hamlet-0dd4ac24d9`** (P1, presentation hardcoded by variable name — make it declared with an
honest default; do not moneyfy by default) is next in the authoring queue. It is `PDR-0045`'s
shape (a name branch) resolved to `PDR-0047`'s shape (a declared parameter from a closed set):
scope it that way, check whether it touches a compiled hash (register first if so), and read
`PDR-0025` (the "locked" showcase is the one place prettified presentation belongs).

If the preference flips to banking exit condition 3 on `main`, `PDR-0068`'s trigger states the
price: `PDR-0039`'s README re-sweep by method at the merge commit, then the owner merges.
