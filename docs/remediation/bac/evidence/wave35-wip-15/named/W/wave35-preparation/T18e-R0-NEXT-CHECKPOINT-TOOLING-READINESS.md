# Next checkpoint tooling readiness — finite proposal, not execution approval

2026-11-13. Existing WIP14 selector cannot select the next R73 interval merely
by changing a receipt or passing WIP14 as predecessor. Propose one newly named,
checkpoint-neutral tool version with a sealed checkpoint contract; preserve the
historical selector/tests and evidence bytes. No implementation was changed or
run. No assembler, application import, Git/index action, source copy, branch,
worktree or delegation occurred. No terminal round or destination is selected.

W=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades;
P=W/wave35-preparation. Measured before reading the two newly authorized whole
bodies; no sixth implementation dependency was read:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| W/evidence-management/bac_checkpoint_delta.py | 469 | 33e992e31a2bfcdb0fa70fac315acc92ec3e961831b0d612c2ba8148c16ef8f8 |
| W/evidence-management/test_checkpoint_delta.py | 389 | 8af61971bf01a7e2045d344fabad87905af4aaf0b5004418ecf98fa9e13941e2 |

Together with this reviewer's existing three500-line verifier bodies, retained
source scope is **five bodies /1358 lines**. The selector imports only standard
library modules; the test imports that selector. There is no unread local
implementation dependency required for this readiness conclusion. Additional
reads were published manifest/plan/chain DATA and already supplied process prose.

## Exact existing constraints

- `_lookup` and `plan` require published `wave35-wip-13.json` and its exact
  selection-plan path, plus current chain tip WIP13. Lookup seeds the baseline
  inventory and folds only WIP13's objects. It validates WIP13's `artifacts`
  path map and `predecessor`, baseline inventory hash, plan link/status, previous
  checkpoint and chain pointers. It cannot see later newly archived objects.
- `validate_receipt` requires `bac-wip14-terminal-receipt-v1`, interval_start59,
  contiguous rounds59..terminal and exact observed qualification top membership.
  The discovery regex uses `wave35-rN`; candidate/preflight paths also hard-code
  wave35. Terminal>=67 additionally forces W/r64-stageA and R67-owner-capture
  component receipt paths regardless of the selected interval.
- `plan` discovers from59, imports each round's candidate and fixture preflight,
  and puts new objects below `wave35-wip-14/`. Output schema and interval remain
  WIP14/[59,terminal], and predecessor-plan metadata is named
  `wip13_selection_plan`. Draft mode still requires an explicit integer terminal;
  it skips full receipt validation and is never assemblable.
- `assemble` accepts only the WIP14 plan schema and copy prefix. It rebuilds the
  plan and requires exact equality, then rechecks source/reuse bytes and writes
  exclusively. CLI exposes `--wip13-manifest` and `--wip13-plan`.
- Tests build synthetic WIP12 baseline/WIP13 predecessor and rounds59–60;
  paths, fixtures, method signatures and interval assertions depend on those
  names. They already exercise the important evidence guarantees below.

Actual published WIP14 DATA is **not** WIP13's layout with a new filename:
`schema=bac-incremental-checkpoint-evidence-v2`, `previous_record`, `objects`
keyed by SHA, `inputs`, `interval=[59,72]`, round72 and hash-bound selection_plan.
It has no `artifacts`/`predecessor` pair expected by `_lookup`. Its selection plan
retains `previous_checkpoint` and `wip13_selection_plan`; chain tip/current pointer
correctly identify WIP14. Therefore path substitution alone is insufficient.
This is a tooling readiness mismatch, not a finding that historical publication
was invalid. Its schema was authored by root after the assembly proposal.

## Smallest coherent new input contract

Use one required, hash-bound `--contract` JSON for both plan and assemble, with a
neutral schema (proposed `bac-checkpoint-selection-contract-v1`). Keep existing
root/work/qualification/chain/receipt/plan/output responsibilities. Put the
following explicit choices in that contract rather than independent switches
that can disagree:

1. `checkpoint_id` and `series` (current series is wave35), normalized safe
   identifiers; derive the one new evidence directory and manifest pathname
   under the fixed evidence prefix. Root supplies the future ID later. Reject
   collision with any existing checkpoint/catalog or output. Do not infer the
   ID by incrementing the highest filename.
2. `interval_start` and explicit `terminal_round`, exact positive integers.
   For the next finite packet start73; terminal remains unknown now. Require
   agreement with receipt and previous published interval end+1; no missing,
   overlapping or silently truncated rounds. Every round still needs its
   candidate and fixture-resource-preflight metadata and exact observed
   qualification top/member inventory. Never derive terminal from live files.
3. Baseline inventory path/hash and an **ordered authenticated list of published
   manifest/selection-plan pairs** from that baseline anchor to the current
   predecessor. First use consumes existing WIP13 then WIP14 metadata, not their
   full object trees. Each pair includes explicit format/schema identification;
   final pair must equal both chain tip and current pointer. Fold their catalogs
   into the existing hash→(path,size) lookup, validating predecessor links,
   manifest/plan agreement, copy-directory containment and earlier-catalog reuse.
   Reject reorder, omission, duplicate checkpoint, hash/size disagreement or
   unanchored reuse. Only selected reused object bytes need rehashing, as today.
4. Explicit required bounded-component references for this interval, including
   actual replay stage receipts and any consciously reused earlier component
   evidence. Require receipt coverage of the sealed list, exact hashes, scope
   and candidate identity. Replace the unconditional R64/R67 path rule with this
   contract binding; do not silently drop those historical obligations from
   their already published checkpoint or manufacture them as new execution.

Support the two actual historical metadata layouts through explicit format
readers, selected by declared and checked schema/format, with no permissive
“try artifacts, else objects” fallback. This is parsing immutable historical
archives, not an application compatibility layer. WIP13's exact observed format
must be pinned from its DATA when implementing. Normalize each publication to
previous-reference, plan-reference and checked object rows. Future publications
use one neutral object-map format consistently, avoiding another per-label code
rewrite. Appending a published metadata pair to the contract is bounded catalog
extension, not a new baseline audit or recursive old-wave copy. A cumulative
catalog cache is unnecessary for this finite change.

## New schema bindings; old evidence invariants stay mandatory

Use neutral versioned receipt/plan/assembly schema names, keeping existing attempt,
review, custody and dependency field requirements. Add checkpoint/series/contract
reference and interval to the sealed receipt; include the contract in the frozen
qualification review subject before terminal review. New plan binds contract
path/hash, ordered publication catalog refs, current predecessor/plan, chain hash
and existing receipt/input/object/interval inventory. Assembly recomputes using
those exact inputs; it never accepts a different contract at materialization.
New published manifest exposes the same checked object rows, aliases and plan
reference, predecessor and interval. Keep execution identity separate from
publication identity and keep root's final publication/navigation ownership.

Retain every existing guard: unique check/attempt/record identities, all failed/
interrupted/unrun/partial attempts, shared-directory MIXED reconciliation and
exact structured result agreement; per-attempt source manifests; qualifying
terminal runtime counts/duration/clock limitation/controller/import/thread and
actual worker topology; required child's exact terminal attempt/source binding;
component scope; independently identified producer/reviewer, independence
evidence and both candidate plus frozen qualification-subject hashes; named
helper closure and immutable document hashes; exact complete descendants including
empty directories; safe normalized paths and ancestor symlink refusal; content
hash deduplication with all logical aliases; existing target path/size/hash
verification; Python snapshots ending .py.txt; exclusive new destinations;
post-plan exact recomputation and post-copy verification. Draft output still
cannot assemble. Integrity readiness still cannot approve qualification or Git.

One existing narrow gap observed during reading: qualifying duration checks exact
int/float and >0 but not finiteness, so positive infinity is not rejected there
(the replay verifier's separate D1 fix does not change this selector). If the new
version carries this rule, add the same finite-positive check and a focused
negative control; no historical receipt needs rewriting and no broader audit is
proposed. Root still verifies substantive qualification and count overlap; the
selector does not independently prove the asserted physics/test observations.

## Finite regression plan, all UNRUN here

Port the existing synthetic scenarios to the new contract while preserving the
historical test bytes. Exercise two consecutive synthetic future checkpoints
with different IDs/intervals using identical implementation: baseline+two prior
metadata formats, an R73-style interval and another next interval. Include reuse
from baseline, each intervening checkpoint and repeated current logical aliases;
same-name changed bytes must become a new object. No real archive, Git or
application execution is needed.

Add focused failures for contract/receipt interval or ID disagreement; inferred/
missing terminal; gap/overlap and omitted round; omitted/reordered catalog;
wrong metadata format; manifest/plan/object disagreement; wrong chain tip;
missing required component; destination escape/collision; contract changes after
planning; and nonfinite duration. Preserve the existing failures for descendant
and empty-directory drift, missing semantic record, shared mixed commands,
terminal child from wrong attempt, structured results, stale document/review,
independence, unsupported worker claim, missing duration/UTC explanation,
symlink/traversal, draft assembly and duplicate output. Require post-copy bytes
and exact no-change regeneration for a successful synthetic plan/assembly.

Separately owned inputs remain root's new checkpoint ID/terminal seal, finite
actual interval/attempt inventory, actual predecessor DATA schema confirmation,
review subject and independent terminal review, process/child/source verification,
publication manifest/chain/index updates and exact remote/CI checks. A future
bounded tooling writer and independent reviewer must be granted the new source
packet when the application writer is frozen; no implementation baton is granted
by this document. Current readiness is **design identified; implementation,
regressions, independent review and actual next-checkpoint selection UNRUN**.
