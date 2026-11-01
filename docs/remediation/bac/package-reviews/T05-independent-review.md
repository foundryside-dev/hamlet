# T05 independent review r1 — static fixed-source refresh

2026-11-01. Existing `/workspace/hamlet` MAIN; observed HEAD `214408b107730b4511b8a690541569aeca4b7b67`. The original `T05-independent-review.md` is preserved.

## Verdict

No confirmed P1/P2 findings or material regression in the revised resolver. Static fixed-source review passes for the exact four-file inventory below. This is not current-source runtime qualification, dependent release, or final BAC closure.

The resolver's previous two conditional expressions are now an explicit branch with `direct_level: str | None`. For a resolved input whose parent is `levels`, both forms assign `entry.name` and `entry.parent.parent`; otherwise both assign `None` and `entry`. Both variables are assigned before discovery on every path. The change preserves root normalization, structural direct-level selection, explicit-level conflict refusal, declaration discovery and located errors. It adds no filename dispatch, override application, alternate effective view, or hash/provenance change. The five-field public result and keyword-only level-selection contract remain intact.

## Inventory and source budget

Exactly four source/test files remain charged, now 2934 lines. The entire 102-line resolver was reread for this refresh; the other three files retain the exact hashes reviewed whole-file in r0 and were hash-verified again. No additional implementation/test/helper source was inspected.

| File | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/config/resolved_launch.py` | 102 | `b55b4b816b02b167ee963a9a443045bff9b26d2ec5e3a0307026253767fe939d` |
| `src/townlet/universe/compiler.py` | 976 | `521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92` |
| `src/townlet/universe/compiled.py` | 1615 | `494f9676c236349f12c875c82dde821a85a3bf5077cae15654c78e8ac1630710` |
| `tests/test_townlet/regressions/bac/test_discovery.py` | 241 | `eb73ca825614ba593549135253caab0b723cc07b53bf91ac3e2801fd9e73e500` |

The original T05 contract and reference-material assessment in r0 continue to apply. No design reduction or new capability restriction is proposed.

## Evidence and limits

Root reports r0 focused `8 passed`, recorded at `qualification/wave04-green-r0/T05.log` with process identity. This is coordinator-attributed prior-source evidence, not a reviewer rerun and not a current r1 runtime PASS.

This refresh used read-only source inspection, SHA256, line counts, HEAD and ignored-report-path verification. No project imports, pytest, probes, executable helpers, source/index edits, branches, worktrees, source copies or delegation occurred. Only this ignored prose report was written. Current-source focused/full runs and standing guards remain root-owned after the combined repair freezes. Other wave authors were active during this review.
