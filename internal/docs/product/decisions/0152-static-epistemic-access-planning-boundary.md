# PDR-0152 — Static epistemic access is planned after Cut B

Date: 2026-10-01 Australia/Sydney
Status: **planning checkpoint; proposed implementation contract**
Author: Codex
Owner instruction: “yes” to preparing the next package's scope and acceptance plan.
Related: PDR-0120, PDR-0151, [PRD-0004](../prds/0004-static-epistemic-access.md),
[implementation plan](../../plans/2026-10-01-static-epistemic-access.md).

## Boundary and proposed decisions

Rebase epistemic-access intent to delivered Cut B `bdf64fad`. Lifetime, complete
symbols, explicit exposure and typed token scope are regression gates, not work
to repeat. Canonical required static permissions are the next proposed slice.

Use existing executing actors: engine/agent readers with engine read required;
engine writers or explicit empty writers. This provides denied agent reads and
runtime-immutable state without claiming engine confidentiality. Simulation remains
engine work; policy observation is an agent read. Exposure is a separate explicit
selection and must be compatible with permission. Unknown/unimplemented actors fail.

Include ordinary and item access, permissions in compiled profiles, checked batched
publication, VTC actual write intent, source-aware target refusals, cache coherence
and item-qualified semantic identity. The all-state VTC commit is a prerequisite
repair for meaningful empty writers. Same-value writes remain writes. Defaults and
lifetime reset are trusted lifecycle initialization; authored item overrides require
write permission. Preserve the current token ABI and frozen oracle.

Role permission is not observer visibility. Private exposure remains refused;
owner/floor/distance/brightness policies and shared item-world isolation are separate
contracts. PDR-0120's dynamic counterpart remains visible and unimplemented.

Planning completes only after independent source/quality review and document/link
checks. This record does not accept implemented behavior, move a delivery deadline,
authorize implementation or publish private source. Execution and acceptance tracker
items remain open. No product code, config or test behavior is changed by this plan.
