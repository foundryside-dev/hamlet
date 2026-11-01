# Source provenance

Original scoped review/execution retains its recorded actual identity. The final source binding verifies the reviewed files are identical in qualified source `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; no execution is relabeled as occurring at a later HEAD.

Original `T14-estimator-independent-execution-r2.md`, SHA256 `0ac11cee217f456d4e6f38eb5418b2b6d23f73014f4e6854d95e2871b8449dd7`, retained unchanged. Portable rendering normalizes execution paths.

# T14 estimator independent execution R2

PASS for the independently executed estimator owner suite: **146 passed, one warning**, zero failures/skips. The actual `estimator-result.json` records exit code **0**; the verdict does not rely solely on the outer wrapper's exit. Pytest elapsed time was 6.89 seconds; measured wrapper job time was 12.991772413253784 seconds. Runtime has closed and this reviewer is stationary.

Root explicitly cleared one CPU of actual spare capacity for this execution on frozen HEAD `bb7cf5f9a545fab0f5b4ecfcc042571e44c34cdd`, candidate tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`. Executed exactly:

```text
python qualification/run_bac_packet_checks_locked.py qualification/wave08-astra-estimator-r2-spec.json
```

The recorded child command was `.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_per_estimator.py -q --no-cov -p no:cacheprovider -p bac_source_identity`. The supplied wrapper/spec uses the root's 112-source-guard manifest and locked metadata write-tree custody. No separate or broader runtime was initiated.

Read and checked the actual result, full log and `estimator/identity-controller.json` under `qualification/wave08-astra-estimator-r2/`. Identity records exactly the HEAD/candidate above, module `src/townlet/__init__.py`, worker `controller`, Torch `2.11.0+cu130` and **threads 1**. This is CPU-thread custody, not GPU qualification.

Log SHA-256, independently recomputed: `d1047dc54a5d32f20069e4d324dc23c4b50fd8cc9364cd33f1d7e637a1426f9c`. Result-record manifest SHA-256: `dce3a8771f8af1fc3fdd55cb0c8a1d0043aa670fd998bf3c71bd5ceec07234f5`; harness SHA-256: `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

The one warning is PyTorch's non-writable NumPy tensor-view warning at estimator line 509 (`buffer.observations[batch.sampling.indices]`). It is outside the changed function and the suite passed; this run does not silently erase that warning.

## Exact reviewed source boundary and preservation

Static source scope remains exactly two whole files / **1913 lines**. Runtime imports performed by the authorized pytest process do not expand the independently reviewed source inventory. No extra helper/test/implementation source was opened.

| Reviewed source | Lines | Actual post-execution SHA-256 |
| --- | ---: | --- |
| `tests/test_townlet/regressions/bac/test_per_estimator.py` | 1238 | `2e08f44397d626a95b4b0f5142021e408250b50067fbfc16c01f2c6ae4459866` |
| `src/townlet/training/historical_checkpoint.py` | 675 | `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4` |

The independently reviewed repair preserves 47 test functions, 119 assertions and 25 raises sites. Static review `T14-estimator-independent-review-r2.md` remains byte-preserved at SHA-256 `630f2cafbcc6edf50a279a0f3907d30d7770201930c862e42860cb0faeb27817`, verified after execution. Its no-P1/P2/P3 bounded static verdict stands; this separate receipt supplies the newly authorized runtime result.

Original failed R1 evidence remains attached to original `01f2f64f42c2932177729607b337419355cb2720` and tree `324438ad58d9d5a85bba54e18be1ee225ada5969`: one failed / 6622 passed / 16 skipped. It is not relabeled or replaced by this passing R2 owner-suite result.

Only this new ignored prose was authored. No source/test edits, index staging, metadata edits, commits, branches, worktree creation/removal, source copies or subagents occurred; the permitted wrapper custody operation is the only metadata/cache-tree activity requested. Existing 14 worktrees remain untouched. Root retains integration and full-gate ownership. This bounded execution does not establish T14 release, native-current/C07 acceptance, the full repository gate or whole-BAC completion; those remain open.
