# Source provenance

Reviewed design/source-preparation provenance. This document is not executable proof or John approval; source budgets/status in its body are historical where superseded by the final binding and actual qualification.

Original `T14-estimator-owner-causal-r2.md`, SHA256 `eb0429849ae739488ed4bcc179ea1152f0a157a98fef51790d6a07f0edba01e4`, retained unchanged. Portable rendering normalizes execution paths.

# T14 estimator-owner causal review R2 — source frozen

This is a static causal investigation and a proposed test-only repair. It is not a runtime result, a qualification decision, or an implementation-complete claim. The proposed patch below has not been applied. The existing `/workspace/hamlet` checkout remains the only source checkout used, at observed HEAD `01f2f64f42c2932177729607b337419355cb2720`.

Root supplied the failed full R1 candidate tree `324438ad58d9d5a85bba54e18be1ee225ada5969`. The recorded failure is `tests/test_townlet/regressions/bac/test_per_estimator.py::test_hc_historical_per4_domain_and_standard_sequence_policy_versions_stay_distinct`, call phase, worker `gw3`, at line 995: `pytest.raises(ValueError)` did not raise. Its immutable input record is `qualification/wave08-full-r1/full/failure-gw3-5b924e926cfe75bf.json`, SHA-256 `c8c470a9140e9fc1db88ecaf67758223830d0c1b746d26e810c3bee3289244d1`.

## Bounded source custody

Both authorized sources were read in full. No other implementation, test, fixture source, helper or conftest was opened.

| Source | Actual lines | Actual SHA-256 |
| --- | ---: | --- |
| `tests/test_townlet/regressions/bac/test_per_estimator.py` | 1234 | `6a60791ace134851ae464cbef4b12244e950065996f5e0a135da7cfa38e77fc9` |
| `src/townlet/training/historical_checkpoint.py` | 675 | `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4` |
| Total | 1909 | Two whole source files |

Applicable prose read: project `AGENTS.md`, `CLAUDE.md`, remediation `STATUS.md`, BAC `STATUS.md`, accepted `wave08-preparation/T14-interface-proposal-r1.md`, and the earlier existing-owner maintenance receipt. Proposal SHA-256: `d6708084cb8bb63ba3febf8860b24a5f8b7a846da609c18ac2988aca35e77239`. Its historical preparation status is not a new approval request; root identified it as the accepted T14 contract for this bounded review.

The only authorized output of this investigation is this ignored prose. `git check-ignore -v` confirms its directory is covered by `.git/info/exclude:7:/.superpowers/`. No branches, worktrees, source copies, index operations, commits, project imports, runtime execution, pytest or collection were performed. All 14 existing worktrees remain untouched. The source freeze remains in force until root gives explicit runtime-closed clearance.

## Causal finding

The failure is a stale test expectation, not a demonstrated HC contract defect.

The test's nested loop uses `("standard", 5)` and `("sequential", 6)`, then assumes `current + 1` must be rejected for both kinds. Standard 6 is still unsupported. Sequential 7 is now intentionally supported, so the sequential branch reaches the line-995 rejection context with a valid current version. The failure record matches that exact contradiction.

The complete HC source has one shared `_CURRENT_REPLAY_VERSIONS` table at line 41: standard `(5,)`, prioritized `(5, 6)`, sequential `(6, 7)`. `_supported_formats` accepts either the exact historical `(demo9, population6, kind-specific pre-capture version)` tuple or exact current demo10/population7 plus membership in that table. Both `_formats` and `HistoricalAccessPolicy.__post_init__` validate exact integer version types and the known replay kind before using this shared predicate. The staged HC diff against HEAD changes only sequential `(6,)` to `(6, 7)`.

This is the additive behavior required by accepted proposal sections 4, 5 and 6, and acceptance item 10. Uniform captured sequential 6 remains current; prioritized sequential 7 is additive and retains `replay_kind='sequential'`. Flat prioritized 5/6 remains a separate kind and format domain. Genuine historical PER4 remains archive/fresh-zero, with recorded-full-resume refusal. Reverting the HC tuple to satisfy the old assertion would violate the accepted sequential-7 boundary.

HC classification is only classification. This investigation does not establish complete replay-schema validity, native demo10/population7 admission, automatic recurrent-PER selection, raw population6 relabeling, evolved optimizer continuation, inference-mode loading or C07 closure. Those distinctions in the accepted proposal remain intact.

## Smallest preservation-consistent proposed repair

Change only the affected test's current-format table and its positive assertion. Leave HC unchanged. Retain both nested loops and every historic PER4 assertion; replace the inferred version boundary with an explicit per-kind accepted/refused matrix.

```diff
--- a/tests/test_townlet/regressions/bac/test_per_estimator.py
+++ b/tests/test_townlet/regressions/bac/test_per_estimator.py
@@
-    for kind, current in (("standard", 5), ("sequential", 6)):
-        for version in (current, current + 1):
+    for kind, supported, refused in (
+        ("standard", (5,), (6, 7)),
+        ("sequential", (6, 7), (5, 8, 6.0, 7.0, True, "7")),
+        ("unknown", (), (7,)),
+    ):
+        for version in (*supported, *refused):
             kwargs = dict(
@@
-            if version == current:
-                assert history.HistoricalAccessPolicy(**kwargs).source_formats["replay"] == current
+            if type(version) is int and version in supported:
+                assert history.HistoricalAccessPolicy(**kwargs).source_formats["replay"] == version
             else:
                 with pytest.raises(ValueError):
                     history.HistoricalAccessPolicy(**kwargs)
```

This keeps all original behaviors except the intentionally obsolete sequential-7 refusal, which becomes an explicit positive. The original standard5 positive, standard6 refusal, sequential6 positive, genuine PER4 archive/count/fresh-zero assertions and historical recorded-full-resume refusal stay present. Added refusals prove that sequential5 cannot be mislabeled current, sequential8 is a true future version, standard7 cannot borrow sequential7's allowance, and an unknown kind cannot borrow it either. Float `6.0`/`7.0`, bool `True`, and string `"7"` exercise the exact-integer replay-version boundary. The positive branch also uses `type(version) is int` so Python's numeric equality cannot misclassify the float/bool negative controls.

The neighboring `test_hc_explicit_current_per_classification_policy_and_codec` is untouched: genuine flat-PER5/6 resolution/codec assertions, wrong PER4/7/bool refusals at both resolver and decoded-policy gateways, and original-input equality remain. Every other estimator, preservation, archive, corruption, purity, mask, receipt, priority, dtype, RNG and native-fixture assertion in the 1234-line owner file remains unchanged.

## Static audit actually performed

A standard-library-only `ast`/`hashlib`/`pathlib` audit parsed the two allowed source files and constructed the above proposed test text in memory. It did not import project code, write a source copy or execute tests. Actual owner-file inventory: 47 test functions, 119 `assert` nodes, 25 `pytest.raises` call sites. The proposed inventory is the same. All top-level function names and order remain, and AST comparison identifies only `test_hc_historical_per4_domain_and_standard_sequence_policy_versions_stay_distinct` as changed.

The in-memory proposal would make the owner test 1238 lines; HC remains 675 lines, giving a proposed whole-source total of two files / 1913 lines. Proposed test SHA-256, if applied exactly: `2e08f44397d626a95b4b0f5142021e408250b50067fbfc16c01f2c6ae4459866`. This is an in-memory proposal hash, not an actual source hash or qualification artifact.

No runtime reproduction was attempted because root expressly froze source and prohibited project runtime/imports in this dispatch. The supplied full-R1 failure is preserved as the causal runtime evidence. After explicit runtime-closed clearance, the bounded authoring step can apply this exact patch and statically check only the owned test. Root then owns candidate identity, fresh review and authorized runtime validation. The specific changed selector and the existing flat-PER HC codec selector should execute, followed by the applicable fixed-tree full gate; this note records no result for them.

## Governance and disposition

User preservation and approved History A override conflicting blanket deletion guidance. The earlier failed durable-rule save grants and restricts nothing: no durable rule was saved, no user-only fallback was adopted, and no new creation is authorized by this note. Existing instructions and actual tool approvals remain controlling.

No source edit or implementation completion is claimed. Returned stationary, with this concrete proposed repair ready for root review and explicit runtime-closed clearance.
