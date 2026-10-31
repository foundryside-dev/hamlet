# Round 02 addendum — independent T01 technical approval

**Verdict: APPROVED — T01 ONLY.**

Exact reviewed plan SHA256: `71a0a08b0659ab3877a7a984844a9d5e158b2fb51940cee9f9c6a4f59e07b671`, verified before and after this scoped review.
Plan: `docs/superpowers/plans/2026-11-01-bac-remediation-upgrades.md`, T01 lines 277–285, with its stated global execution/verification constraints.
Reviewer: same Astra MEDIUM technical reviewer.

This approval authorizes technical release of the already user-authorized **T01 numeric-validation package only**, covering D06, D07, D08 and G06. It does not approve the whole plan, a historical-replay option, any exception to D01/X01 closure, or any other implementation package. Round 02's full-plan CHANGES REQUIRED verdict remains in force. The pending historical decision does not affect T01's schema-only dependency boundary; T01 has no prerequisites in the DAG.

## Approved deliverable and preservation conditions

- Reject negative selected feedforward/dueling widths while preserving every working zero-width constant-policy declaration and its existing bias behavior.
- Diagnose the demonstrated selected-SGD Nesterov/zero-momentum invalid combination before optimizer construction. Do not reject inactive preset combinations merely because a different optimizer is selected.
- Reject nonfinite behavioral numerics at the authored/effective boundary, including the demonstrated infinite learning-rate override; preserve finite working settings and active optimizer/loss families.
- Accept gamma throughout `[0,1]`, including zero, consistently in brain and overriding training declarations.
- Retain strict located diagnostics, complete level-brain replacement, all five existing training overrides, public DTO/helper interfaces and accepted preset content. No architecture, sampling, provider, historical-loader or runtime-mode restriction is authorized.

These choices implement the adopted r2 validation/gamma contracts. They do not remove a working capability; gamma zero is an additive alignment. A newly discovered proposal to narrow an actual working input must return to the coordinator rather than borrowing this approval.

## Exact bounded ownership and acceptance

Both implementer and fresh independent reviewer may inspect only:

| File | Role | Projected full-file ceiling |
|---|---|---:|
| `src/townlet/config/brain_config.py` | Modify | 750 |
| `src/townlet/config/training_v2_config.py` | Modify | 650 |
| `tests/test_townlet/regressions/bac/test_numerics.py` | Create/test | 350 |
| **Total** | **3 implementation/test files** | **1750 lines** |

Recount before dispatch; use owner-provided interface evidence for factories/compiler rather than opening an extra source file. Existing focused suites may execute without reading their implementations. No shared Python fixture file is implicitly included.

The named regressions must prove real full-pack compile → effective override → selected factory behavior, not only DTO construction. Negative width/Nesterov/nonfinite controls fail at the intended boundary before allocation/corrupting update; gamma-zero and zero-width controls construct and execute finite policies. Preserve a finite optimizer-update control and the full-replacement/five-override controls. Run the plan's exact `test_numerics.py` command red then green, relevant B01 suites and standing repository gates; obtain fresh other-model package review and repair findings before committing or releasing dependents. Source/import SHA evidence and actual results are required. This is approval of the plan slice, not a claim that its implementation or tests already pass.

Cumulative reviewer source inspection remains one allowed file / 543 conservatively charged lines from earlier rounds. This scoped review opened no additional implementation/test source and ran no test campaign.
