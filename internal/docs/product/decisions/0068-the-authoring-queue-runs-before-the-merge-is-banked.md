# PDR-0068 — the authoring-surface queue runs before exit condition 3 is banked on `main`

Date: 2026-08-16   Status: **accepted** (owner-chosen at the second 2026-08-16 `/own-product`
resume — offered as the recommended option; the merge itself is the owner's action under
`PDR-0046`, so the sequencing was theirs to make)
Author: Claude (standing product owner)
Owner sign-off: **yes** (*"lets do 1 now"*)

Related: `PDR-0058` (the merge is publication inside the bet, not its exit), `PDR-0065` (exit
condition 3 MET ON THE BRANCH), `PDR-0039` (every merge owes the README re-sweep), `PDR-0046`
(the merge is the reversibility boundary), `PDR-0047` (the ruling the queue executes)
Tracker: `hamlet-2fe1c34ebb` + `hamlet-45b35cfee5` (unit 1, closed this session),
`hamlet-0dd4ac24d9` (unit 2, next), `hamlet-f0ed709ecf` (filed by unit 1)

## Context

The resume brief offered two honest next units: (a) the authoring-surface queue — the P1
`semantic_type` finding with its P2 sibling in one pass, then presentation-by-variable-name; or
(b) bank exit condition 3 on `main` — run `PDR-0039`'s README re-sweep by method over the 21
commits ahead, then merge. Both were fully specified; only their order was open.

## The call

**(a) first.** The queue had been displaced for two sessions by the hidden-failure work
(`PDR-0059`..`PDR-0065`); it is the WS-4 product work under an owner ruling with a decided
direction; and it moves the input metrics (`Declared-but-inert`, `Config-surface coverage`,
`Failure loudness`) the north-star depends on. The merge, by contrast, changes the *scope* of a
guardrail reading (`Gates green` from branch to `main`) without moving any input metric — and
its price rises linearly with commits ahead, which is a real cost of deferral, recorded here.

## Rationale

The bet exits when the oracle can be retired, not when `main` goes green (`PDR-0058`); the merge
is publication and can happen any number of times. Product work that moves the authorability
metrics ranks ahead of a publication step whose only urgency is the nightly's redness on a branch
nobody trains from. The recommendation named the cost honestly: the re-sweep is owed on more
commits each session it waits (21 at the choice, 23 after this session).

## Reversal trigger

- **Bank the merge before the next queue unit** if commits ahead of `main` pass ~30, or if a
  second consecutive session ends with `Documentation truth` moving because a README claim
  decayed — both mean the re-sweep's cost is compounding faster than the queue is paying out.
- Also if anyone but the owner needs `main` (a collaborator, a CI consumer): the branch-only
  scope of `Gates green` becomes a real cost the moment there is a second reader.
