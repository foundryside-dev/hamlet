# PDR-0156 — Repair refusal atomicity and canonical variable identity

Date: 2026-10-01 Australia/Canberra
Status: **accepted — bounded local refusal/identity qualification**
Author: Codex
Owner input: main `72977928` review, with effect denial ahead of episode-lane work.
Related: PDR-0153/0155; PRD-0004; `hamlet-f75ff623be`, `hamlet-bae419a592`,
`hamlet-940089c925`; proposed episode work `hamlet-d6fc84d147`.

## Context

The review supplied two hypotheses: a denied item `on_spawn` write can leave an
admitted effect behind, and flattened `profile:id` discovery rejects distinct
canonical variables. Both reproduced on unchanged execution source. Reapplication
also changes intensity or scheduled work before a denied lifecycle hook.

The identity probe exposed the same flattening in item symbol registration and
source provenance. An ordinary `tool:charge`, item `(tool, charge)`, and distinct
item pairs containing colons must retain their separate identities and origins.
Genuine duplicates must still fail with both declaration locations.

## Options considered

1. Preflight only each individual command: leaves earlier effect admission and
   lifecycle mutations behind on refusal.
2. Preflight selected immediate lifecycle pipelines before admission/reapplication,
   retaining resolved item-row authority. Repair canonical identity throughout
   discovery, symbols and source-location consumers.
3. Also make immediate nested admissions atomic. An independently reproduced
   parent mutates bars before spawning a child whose item write is denied; direct
   child preflight alone leaves the parent live. Dynamic child targets can depend
   on earlier writes and randomness, so resolving them early changes successful
   execution. One outer admission snapshot preserves normal execution order and
   restores runtime state on permission denial.

## The call

Implement options 2 and 3 as repairs to the existing refusal contract, on local
branch `fix/static-access-review`, implementation **`c3faa4bfa9c4b7a391f530e8c97a45cded908cb3`**.
Allocator follow-up **`7eb7ded3b2f9aa625828a02fe751713e0eed4c9f`** is the final source
qualified by the full-suite run.
The reproduced immediate cascade is included because it violates the same refusal
contract; the standing engineering authority permits the bounded local repair.

Direct preflight checks the hooks actually selected by reapplication policy before
changing IDs, collections, intensity, schedules or state. Renew invokes no hooks;
merge does not authorize an unused spawn hook. Item writes use the attached row's
profile. A denied same-value write is still refused.

Immediate lifecycle cascades capture state once at the outer admission boundary.
Nested targets execute in their normal order and sample once; `PermissionError`
restores bars, ordinary/item VFS and profile rows, effect objects/collections/IDs,
scheduler work, item-spawn bookkeeping, affordance availability and RNG. Original
tensor/container/effect identities are preserved. Disabled item services have no
item state to capture. Branch discovery follows compiled SWITCH authority.

A paired allocation-history probe found that restoring a free-slot set cannot
restore Python's hidden `set.pop()` cursor. Item rows therefore allocate from the
lowest free index explicitly. This changes successful selection after a lower row
is freed, and prevents a rejected cascade from changing the next allocated row.
No compatibility allocator is retained. Frozen trajectory/performance acceptance
of this selection change is not claimed by the runtime regressions.

Canonical comparison uses structured profile/ID tuples. Variable source-location
keys encode those tuples unambiguously; obsolete flattened aliases are removed.

## Evidence and limits

Test-first reproductions and independent counterexamples precede the fixes.
**397 focused item/effect checks pass**, including real item spawning, arena aliases,
private storage replacement, successful dynamic targets and disabled item services.
The paired allocation-history regression fails before deterministic selection and
passes after it.
**988 compiler/oracle/access checks pass**, with a final replay of the declaration
tests after adding full-compiler collision assertions. Ruff, Black (576 files),
mypy (179 source files), no-defaults (695 existing whitelist matches), compiler
fleet validation and diff checks pass. No whitelist entries were added.
[Verification receipt](../evidence/static-access-review/verification.md) records
commands, identities, retained log digests and acceptance limits.

The full default suite passed **4,277 tests / 18 skips / 15 warnings / 85% coverage**
in **989.23s**, exit 0, against unchanged execution source `7eb7ded3`. The 18 skips
have an explicit disposition in the receipt. All three repair issues are closed
against this source. Two earlier full runs
were intentionally interrupted when independent review and allocation probes found
boundary defects; neither is a passing result. These runs are not convergence campaigns.

Snapshot work is linear in supplied runtime tensors and effect/item/scheduler
bookkeeping and is enabled only for immediate cascades. Performance acceptance is
not measured. Initialized CUDA RNG restoration is implemented but the new rollback
regressions run on CPU. Future delayed execution, arbitrary callbacks and whole
environment ticks are outside this admission transaction.

## Rationale and reversal trigger

Refusal must preserve state before learning evidence can be trusted. Repairing
distinct identity and origin paths closes the low-priority finding without
weakening genuine duplicate rejection. These are bounded contract repairs, not
new authoring capabilities or a recovery exit.

Reopen if any supported denied admission changes observable state or aliases, if
successful dynamic target/RNG order changes, or if distinct canonical variables
collide or lose their source origin. A material cascade cost in a declared scenario
requires measurement and design review; no performance result is presumed here.

The next package remains truthful episode lanes. Terminal replay/RND accounting,
effect reset, initial-item cache fidelity, RNG isolation and full BAC cognition
remain open. PDR-0058's fired exit trigger remains unresolved. No main merge, push,
release or deployment is performed by this repair checkpoint.
