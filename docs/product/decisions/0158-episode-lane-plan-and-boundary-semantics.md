# PDR-0158 — Plan episode lanes and resolve boundary semantics

Date: 2026-10-02 Australia/Canberra. Status: **accepted — implementation plan**.
Author: Codex. Owner input: “great work, kick off that next task” following the
PRD-0005 planning handoff. Standing authority permits product shaping and delivery
handoffs within recovery; this checkpoint completes planning, not runtime acceptance.
Related: PDR-0157/0058, PRD-0005, planning `hamlet-87d3ef8e23`, execution
`hamlet-78ad37dd49`, confirmed engine bug `hamlet-d6fc84d147`.

## Evidence and call

The planning source is `ec463fdaaa632e4e1f778b938ace94f53a73a745`, whose runtime,
tests and configs equal merged main `95b2f828`. Read-only probes now execute the
previously missing authored configuration, actual gradients, persisted sinks and
pinned-oracle boundary. [Planning receipt](../evidence/episode-lanes/planning/receipt.md)
retains scripts, commands, hashes and limits. The accounting target remains unmet.

Choose the [source-validated implementation plan](../../plans/2026-10-02-truthful-episode-lanes.md).
The environment exposes authoritative entry eligibility and new terminal/retirement
masks. Population owns once-only completion and owned final snapshots. Runner
consumes them through its existing batch curriculum route and explicit survivor
completion. No extra replay payload or per-agent database is required.

Authored death and genuine retirement are MDP terminals. Caller cap/budget/shutdown
and existing checkpoint cuts close nonempty surviving episodes without changing
the final replay `done=False`: successor bootstrap stays valid. Death wins a
coincident lifespan boundary; genuine retirement preserves its final live DAC
reward and adds its bonus once in total and extrinsic component. RND normalization
and predictor admission use exactly the eligible rows, including terminal rows.

Normal runner cap equals configured environment lifespan, so that route remains
retirement. A lower caller horizon and budget-six witness separately qualify
truncation. Reset must refuse a pending nonempty episode before mutation until
its caller completes it with an explicit reason; empty/completed resets remain
valid. This prevents shortened loops from discarding unfinished recurrent sequences.

Preserve scheduling units: Q train frequency/PER progress are vector ticks,
target synchronization optimizer updates, epsilon once per batch episode and
adaptive history once per completed lane. RND update timing follows eligible
sample occupancy. Shared world progression and valid shared gradients continue;
completed outcomes/contributions freeze by value rather than suspending the universe.
Full recurrent forward retains the existing Q-value/curriculum interface while
restoring inactive hidden rows. An adversarial unequal-ending witness checks its
blast radius; zero Q placeholders are not accepted as an innocuous implementation.

## Artifact and consumer boundaries

Population checkpoint format5→6 refuses artifacts trained with contaminated
replay/history before any mutation, even when content hashes match. Outer format6
and replay formats remain unchanged; nested gates already cover training and
serving. Resume remains learned state at a fresh episode. Do not add exact partial
rollout continuation or checkpoint atomicity to this package.

Fresh database schema separates slot-0 survival, batch vector ticks, live
transitions and completion reason. Recording format2 requires completion reason,
with periodic recording-selection reason kept separate. Strict schema/version
checks refuse old artifacts without migration or deletion. Historical M4 CSVs,
event files, databases and checkpoints retain their original source/semantics.

Reality review mechanically reproduced a current recording-boundary mismatch:
ordinary producer metadata contains `{positions, ordering, position_dim}`, while
the DTO/deserializer and observer expect flat named coordinates. Strict format2
validation therefore requires owned flat recording coordinates and a real ordinary
artifact → ReplayManager → observer witness. Keep the environment/checkpoint
envelope unchanged. This is a direct artifact-boundary prerequisite, not a spatial
API redesign or general playback rebuild.

DB/TensorBoard/curriculum/recording probes now reproduce inflated early-lane outcomes;
budget accounting and checkpoint transition counters remain correct. Final-meter
CPU aliasing is reproduced. The runner sink probe deliberately waited for real
recording persistence to isolate accounting; ordinary shutdown durability remains
unqualified. If it blocks the candidate, retain the failure and amend scope before
repairing that separate lifecycle. A sleep in the test is not a product repair.

## Review and handoff

Four reviewer lenses cover reality, architecture, quality and systems. The plan
review record beside the plan retains original blocking findings, revisions and
final verdicts. Resolved findings include schema/metadata ordering, test command
ownership, non-vacuous target categories, reset loss, curriculum Q placeholders
and recording layout. Approval qualifies planning feasibility only.

Execution `hamlet-78ad37dd49` depends on completed planning, remains unclaimed and
requires all PRD criteria on one candidate. Before cuts, retain clean-parent
trace/hash/reset inputs and preregister exact intended coordinates plus the next
free divergence entry, currently DIV-016. The 100-tick standing format4 matrix
cannot measure survival/replay/RND/sinks or the configured 1000-tick retirement
boundary; controlled pinned-oracle and independent runtime witnesses supplement it.
No broad stream allowance, frozen-input rewrite or oracle re-freeze is authorized.

Product review remains October9 or the first proposed candidate earlier; no delivery
forecast is invented. Candidate gates include real Q/RND updates, actual loss targets,
eligible identities, persisted sinks, negative controls, fleet/lint/type/no-defaults,
an unfiltered full suite and independent criteria acceptance. The existing prerequisite
gate passed 20 tests with one existing stochastic-affordance skip; no new full suite,
CUDA, hosted CI or convergence reading is claimed here.

PDR-0058's exit/instrument review `hamlet-4554a428b2` remains separately open.
Effect reset, initial-item/cache fidelity, ownership, RNG policy, warmup redesign,
BAC and a learning campaign remain out of scope. This local branch checkpoint
changes documentation only; no runtime implementation, push, PR, main merge,
release or artifact deletion occurs in this planning task.

## Reversal and backout

Reject execution acceptance if a terminal row is lost, phantom experience persists,
completion repeats, a truncation target suppresses bootstrap, ordinary sinks
contradict the ledger, or exact attribution fails. Re-scope in a PDR when an excluded
subsystem becomes a demonstrated prerequisite. Missing the review window requires
an explicit scope/forecast review and leaves the package unaccepted.

Backout restores a prior source checkpoint while retaining all produced artifacts;
use fresh run/database paths rather than consuming incompatible newer data or
migrating it. No prior decision is rewritten, and no recovery exit changes here.
