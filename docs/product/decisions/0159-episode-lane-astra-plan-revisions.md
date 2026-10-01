# PDR-0159 — Resolve Astra's episode-lane plan findings

Date: 2026-10-02 Australia/Canberra. Status: **accepted — planning revision**.
Author: Codex. Owner input: “ok please make the changes” following the requested
independent Astra plan review. This authorizes the concrete plan revisions and
local evidence custody; runtime execution remains a separate handoff.
Related: PDR-0158/0157/0058, PRD-0005, revision `hamlet-272374260c`, execution
`hamlet-78ad37dd49`, confirmed engine bug `hamlet-d6fc84d147`.

## Evidence and decision

The [independent Astra review](../../plans/2026-10-02-truthful-episode-lanes.astra-review.md)
requested changes to original plan hash
`e490ce761885cc1bb3b0d35a27f06ef2ddc518ba7f0ae932065ba95dd1fc10af`.
Its exact SQLite read-only proposal created original WAL/SHM companions on an
ordinary closed historical file. Four of five real recorder-thread shutdown
attempts lost the artifact; those attempts omitted database indexing and were
not complete runner acceptance. Source inspection also exposed raw-vs-composed
recording rewards, a multiplication-based observer cumulative reward and omitted
TensorBoard shaping forwarding. Retain that review and PDR-0158 as history.

Choose the [revised plan](../../plans/2026-10-02-truthful-episode-lanes.md), with
three bounded changes:

1. Preflight never opens the original family with SQLite. Raw header/family reads
   reject old/pending artifacts; a private copy validates a closed current file.
   Any WAL/SHM/journal presence is refused unchanged, including valid committed
   WAL. Current normally closed WAL-mode files with no companions are supported.
   Exclusive caller custody through actual reopen is required; the assertion is
   not an OS lock, and repeated fingerprints do not prove atomic live snapshots.
   Concurrent owners and interrupted-run recovery are excluded. A failure to
   establish custody requires a scope amendment rather than a live-read shortcut.
   S1 also closes the batch-video query owner before individual exports and closes
   each export owner after reader load on every path; sequential real DB/reader
   and failure-cleanup controls qualify this concrete caller conformance.
2. E0a runs ordinary runner/recorder/index/file shutdown witnesses after the clean
   parent bank and before substantial episode implementation. Any loss blocks E1;
   retain the failing witness and admit only a demonstrated queue-drain/publication
   prerequisite through a separate PDR before repair. Repeated ordinary attempts
   cannot be replaced by sleeps, polling, a fake writer or a lucky successful run.
   This decision advances the prerequisite; it does not itself admit a recorder rebuild.
3. Format 2 defines frame total plus required canonical extrinsic, effective
   intrinsic and shaping contributions. Metadata/database/TensorBoard retain
   shaping explicitly. Actual observer cumulative reward is the eligible prefix
   at the selected playback index, stable through seek/reset, not reward times
   step count. A non-vacuous persisted producer-to-observer witness reconciles
   earlier positive reward, zero terminal reward and nonzero modifiers/shaping.
   No frontend redesign or raw-novelty reconstruction is added.

[Revision evidence](../evidence/episode-lanes/planning/astra-revision/receipt.md)
retains the executed private-copy controls, complete original-family hashes,
source/import identity, commands and byte archives. These are proposal feasibility
and refusal evidence, not runtime repair acceptance. The original discovery and
review receipts remain intact. Runtime/tests/config/scripts are unchanged at
source `ec463fdaaa632e4e1f778b938ace94f53a73a745` through revision parent
`86857eb0e0730c113cbf27f21bd97a308095079b`.

## Review, handoff and limits

Astra [re-review](../../plans/2026-10-02-truthful-episode-lanes.astra-revision-review.md)
returns **APPROVED_WITH_WARNINGS**, no blocking revisions, for final plan SHA256
`159ab22fc58bb43a5c2e9756c5bfbc9546f10ecb1d5a42145a357b104acb1b6c`.
It independently passes the 22 DB controls and eleven numeric refusal controls.
Its separate Markdown/JSON receipts retain the remaining execution gates; they
do not overwrite the original review. Revision `hamlet-272374260c` closes only
with this review and local documentation commit, unblocking execution
`hamlet-78ad37dd49`. Execution remains unclaimed. Its first
steps are a clean-parent E0 capture and E0a; the recorder dependency is a real
execution risk, not accepted durability. No runtime GREEN, new full suite,
convergence, push, PR or main merge is claimed by this revision.

PRD-0005 remains implementation unaccepted; zero accounting error is unmet.
October 9 or the first candidate earlier remains the review window, not a delivery
forecast. PDR-0058's exit/instrument review remains separately open. Scheduling,
bootstrap, checkpoint fresh-episode resume, attribution and excluded effect/item/
RNG/BAC work retain PDR-0158's boundaries.

Reject execution if refused originals change, committed WAL is silently ignored,
ordinary accepted frames/markers are lost, recorded/TensorBoard/observer rewards
disagree, or candidate evidence fails any PRD criterion. Re-scope only from the
retained concrete dependency evidence. Backout restores prior source while keeping
historical artifacts; never migrate, replace or delete them.
