# PDR-0071 — The merge is banked before unit 3, because `PDR-0068`'s trigger lit on both prongs

Date: 2026-08-17   Status: **accepted** (owner-chosen at the 2026-08-17 `/own-product` resume,
offered as the recommended option; the merge itself remains the owner's action under `PDR-0046`,
so the sequencing was theirs to make)
Author: Claude (standing product owner)
Owner sign-off: **yes** (*"Merge first, then unit 3"*)

Related: `PDR-0068` (the queue runs before the merge is banked — with this trigger), `PDR-0058`
(the merge is publication inside the bet, not its exit), `PDR-0039` (every merge owes the README
re-sweep by method), `PDR-0046` (the merge is the reversibility boundary), `PDR-0065` (exit
condition 3 met on the branch)
Tracker: `hamlet-f0ed709ecf` (unit 3, deferred behind the merge, still `open` P2),
`hamlet-102db4c2e0` (`AffordanceGraph.vue`, cheap follow-on)

## Context

`PDR-0068` chose the authoring queue over the merge and named its own reversal: *bank the merge
before the next queue unit if commits ahead of `main` pass ~30, or if a second consecutive session
ends with `Documentation truth` moving because a README claim decayed*. At the 2026-08-17 resume:

- `origin/main...HEAD` read **0 / 27** — three short of the line, exactly as the previous brief
  predicted.
- The previous brief said README decay *"was not measured this session"*. Measured at ORIENT:
  `README.md` had not been touched since the merge sweep (`33bfff51`, 27 commits ago) and carried
  at least two claims the last two units had falsified — *"the frontend cannot be built as
  shipped … no `package.json`"* (false since `a5cca764`) and *"the full matrix has not yet
  completed a run against the merged tree"* (it had run twice against `main`, 31 failures each).

Both prongs of the trigger were therefore lit — not past the literal ~30, but the trigger's own
wording (*the re-sweep's cost is compounding faster than the queue is paying out*) was true.
Unit 3 (`hamlet-f0ed709ecf`) additionally touches compiled observation fields, so it needs a
DIV-006 register entry, which fires `PDR-0058` trigger 2 and forces the re-tag question — a
second sequencing question stacked on the first.

## Options

(a) **Merge first**: run `PDR-0039`'s re-sweep by method over the 27 commits, hand the owner a
merge-ready branch, then take unit 3 with its DIV-006 entry and the re-tag decision.
(b) **Unit 3 first**: take `hamlet-f0ed709ecf` now, accept the re-sweep growing past 30 commits,
record the trigger override.
(c) Only the cheap `AffordanceGraph.vue` cleanup / housekeeping.

## The call

**(a).** Owner-chosen. The re-sweep's price rises per commit; unit 3 raises a *second* decision
(re-tag) that is easier to take on a `main` that already carries the branch; and the nightly on
`main` has been red for two mornings on failures the branch has already fixed — the publication is
overdue on its own terms.

## Rationale

`PDR-0068` deferred the merge on the argument that product work moving the input metrics ranks
ahead of a publication step. That ranking still holds in general — but the PDR pre-committed the
condition under which it stops holding, and the condition arrived. Reading a trigger as fired
when its stated reasoning is true, rather than waiting for the literal number, is what the
trigger is for. The queue is not abandoned: unit 3 is next in line the moment the merge lands.

## Reversal trigger

- If the owner does **not** merge within the session after gate 2 is executed (`PDR-0072`) and
  further code commits land on the branch, the sweep is owed again at the merge (`PDR-0039`,
  unconditional) — do not cite `PDR-0072` as the satisfied gate for a later commit.
- If unit 3 turns out not to need a register entry after all (the split leaves every compiled
  hash unchanged), the re-tag pressure this PDR cited disappears; the merge-first ordering still
  stands on the first prong alone.
