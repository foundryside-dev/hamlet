# PDR-0153 — Static epistemic access accepted against PRD-0004

Date: 2026-10-01 Australia/Canberra
Status: **accepted at local implementation checkpoint; local integration recorded separately**
Author: Codex
Owner instruction: “please execute the plan and commit and merge the changes”.
Related: [PRD-0004](../prds/0004-static-epistemic-access.md),
[PDR-0152](0152-static-epistemic-access-planning-boundary.md),
`hamlet-a3272e31c0`, `hamlet-e911091cb2`.

## Decision

Accept the bounded static epistemic access contract at qualified implementation
**`b70fda104e5061ed2735e8b31b7f8f9caaf99f19`**. Each of the eight criteria is read
individually in the [acceptance report](../evidence/static-epistemic-access/acceptance.md)
and the retained cross-review decisions. This decision records the verified outcome;
a commit by itself is not qualification.

Full local suite: **4,250 passed, 18 skipped, 15 warnings**, 1561.29 seconds, **85% coverage**, terminal exit 0 at the qualified source. Skipped tests are not passes.
Ruff, Black, mypy, no-defaults and compiler CLI fleet checks returned zero at that
same clean source. The 31-case parent comparison qualifies all 884 readings, ten CPU
trajectories and eleven reset recipes with exactly 150 attributed identity changes,
no numeric-stream/reset differences and no stale/unexplained movement. Frozen CPU
qualification returned zero with ten registered divergences and ten explicit CUDA
skips. All historical output allowances are preserved; DIV-015 adds only the measured
variable/VFS policy identity causes. Exact input inventories and independent raw
trajectory reconstruction are retained.

## Contract and review

Canonical declarations require finite explicit engine/agent readers and engine/empty
writers, with independent explicit exposure. Runtime access, attempted writes,
publication, cache coherence and checkpoint identity agree. Immutable literals can
initialize/reset; authored/runtime writes cannot bypass policy by preserving the old
value. Ordinary and item policy identities are qualified and include hidden state.
The committed witness exercises actual public/hidden mutation and a hidden-state
reward through direct and serialized artifacts, across two rows and two episodes.

Reviews declare authorship: policy authored Tasks 2/5 and independently reviewed
Tasks 3/4/6; intent authored Task 4 and independently reviewed Tasks 2/5; instrumentation
authored comparator/identity work and independently reconstructed evidence and
command counterexamples. Root reviewed the complete package. Fresh Loomweave and
supplemental AST/manual caller reconciliation are retained with extractor limits.
This is cross-review, not an author-free whole-package review.

## Delivery boundary

Implementation commits and local merge into `project-recovery-4` are authorized.
Local integration will be recorded in a separate receipt after the actual merge and
postmerge checks. This accepting documentation changes no execution source from the
qualified checkpoint. Nothing is pushed, published, deployed or accepted through
hosted CI by this decision. No frozen oracle source/tag/fixture or defaults-whitelist
change is permitted; unrelated parent edits remain preserved.

Static engine/agent roles do not implement owner/spatial privacy, Python sandboxing,
engine confidentiality or noninterference: public derived values and rewards may
reveal hidden inputs. No learning/convergence, browser, CUDA, Murk, BAC cognition,
shared-world isolation, held-item/locality/capacity, appearance-cache, effects-reset
or terminal-lane completion is claimed. Runtime initial-state override APIs are
checked; the current authored item DTOs do not admit an initial-state field.
