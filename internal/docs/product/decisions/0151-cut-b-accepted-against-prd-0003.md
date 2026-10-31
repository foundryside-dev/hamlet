# PDR-0151 — Cut B accepted against PRD-0003

Date: 2026-10-01 Australia/Canberra
Status: **accepted at implementation checkpoint; final documentation-head verification remains separately tracked**
Author: Codex
Owner instructions: “excellent work, please plan and execute B”; explicit **yes** to publishing `feat/declaration-store-cut-b` to GitHub's `foundryside-dev/hamlet` and opening a draft PR stacked on Cut A.
Related: [PRD-0003](../prds/0003-declaration-store-cut-b-one-variable-contract.md), PDR-0147, PDR-0149, [PDR-0150](0150-cut-b-local-qualification-and-hosted-acceptance-boundary.md), `hamlet-61e3de957f`

## Decision

Accept Cut B at published implementation checkpoint **`22924d0a6f11c0d9a3222567e4fb1188ea0071de`**.
All three hosted workflows at that exact SHA are completed/success: [Config Validation 36781512698](https://github.com/foundryside-dev/hamlet/actions/runs/36781512698), [Lint 36781512796](https://github.com/foundryside-dev/hamlet/actions/runs/36781512796), [Tests 36781512782](https://github.com/foundryside-dev/hamlet/actions/runs/36781512782).
Their [receipt](../evidence/declaration-cut-b/hosted-implementation-checks.json) was observed at
`2026-09-30T22:12:26.362956+00:00` and retains workflow IDs, URLs, terminal states, exact head and owner authorization.

This source is execution-identical to `baced7dba659ab2024a3f164f18c450695000362`, which passed
4,055 local tests with 18 skips and 84% coverage, the five static/compiler CLI gates and the clean
CPU comparisons. Parent integration passed 87 additional checks. Independent specification and
quality review read the criteria individually and found no local blocker. No deadline or
technical criterion is weakened.

## Criterion readings

| PRD criterion | Verdict | Evidence |
| --- | --- | --- |
| 1: One model | PASS | Canonical required variables catalog; old readers/DTOs/aliases deleted, live packs and executable positive fixtures converted, path-aware negative controls. |
| 2: State semantics | PASS | Explicit literals/null/tensor initialization and lifetime/derived-state witnesses, direct and cache-loaded; item and expression limitations refuse early. |
| 3: Symbols | PASS within supported consumers | Complete canonical registry/profile-qualified roster; configured writes and named rewards share state; unknown names/collisions refuse with origins. |
| 4: Typed scope | PASS | Scope drives mixed publisher routing, dotted registry IDs remain registry state, invalid/missing bindings refuse; schema 1.28 requires persisted fields. |
| 5: Attribution | PASS | 31 cases / 884 readings, 212 exact attributed movements, ten byte-exact trajectories and eleven reset censuses; frozen matrix: ten registered CPU cells / ten explicit CUDA skips, exit 0. |
| 6: Gates | PASS | Full local suite/static/CLI gates and post-integration checks; all three exact published-head hosted workflows completed/success. |
| 7: Hygiene | PASS | Active canonical docs and examples corrected; obsolete authoring callers/tests removed; internal profiles remain compiler-owned products. |
| 8: Independent checkpoint | PASS | Independent criterion/source/quality reviews, committed before/after evidence, explicit local/publication/hosted checkpoints and this accepting decision. |

Full commands, causal checkpoints and limits are in the
[acceptance evidence](../evidence/declaration-cut-b/acceptance.md).
Frozen source and fixtures, the no-defaults whitelist and unrelated dirty skill files are unchanged.

## Delivery and consequence

[Draft PR #41](https://github.com/foundryside-dev/hamlet/pull/41) stacks on Cut A's
`feat/declaration-store-cut-a` ([#40](https://github.com/foundryside-dev/hamlet/pull/40)).
Only the B feature branch is published. Local `project-recovery-4` includes B; parent/main were
not pushed or merged on GitHub. The initial publication rejection was resolved by the owner's
explicit destination-specific approval, without bypassing the review.

This accepting record is documentation/evidence only. It does not claim the earlier CI jobs
ran at a later documentation SHA. The final published PR-head checks are verified separately;
close `hamlet-61e3de957f` only after this decision/receipt are committed and those checks are
terminal-success. Retain the issue in progress while delivery verification is pending.

No learned convergence, browser, CUDA execution, Murk, BAC cognition, full privacy/relational
consumer or separately tracked item/reset/terminal-lane completion is claimed.
