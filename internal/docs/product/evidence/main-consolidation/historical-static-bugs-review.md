# Historical static-access bug closure review

Read-only at `project-recovery-4@ea9fc5fafe451cd59e7231ccef06d221e73ff99d`. The qualified static execution tree is b70fda10; PDR-0153 and its separate local receipt record acceptance/integration. No tracker/docs mutations in this review.

**GO to close the three historical defects, with explicit bounded closure reasons.** This does not implement arbitrary old actors or owner/spatial privacy. `hamlet-83a043a9b9` remains open as instructed.

| Historical issue | Current source and behavioral evidence | Recommended closure reading |
| --- | --- | --- |
| `hamlet-fc78bb49d3`: no permission-authoring door; compiler hardcodes all variables | [canonical DTO](/home/john/hamlet/src/townlet/config/variables_config.py:49) requires readable_by/writable_by/exposed_to; [lowering](/home/john/hamlet/src/townlet/universe/compilers/vfs.py:95) copies declaration policy, without rewriting it. Internal engine tick has an explicit engine-owned policy; it is not an alternative authored variable route. Required/missing/duplicate/unknown/exposure contradiction tests and real cold/cache hidden/mutable/immutable witness pass. | Closed by canonical permission authoring and policy-preserving lowering under PRD-0004. Old environment/profile authoring routes are removed, not kept compatible. Engine read remains required; engine/agent readers and engine/empty writers are the supported surface. |
| `hamlet-1a520475f4`: fictitious action/vtc/social_model/acs roles, no actual agent reader, convenience bypass | [finite validation](/home/john/hamlet/src/townlet/vfs/access_policy.py:6) rejects unsupported roles, rather than allowing them until step1. [checked convenience accessor](/home/john/hamlet/src/townlet/vfs/registry.py:969) delegates with required explicit actor; ordinary/item publisher plans call agent authorization before gathers ([ordinary](/home/john/hamlet/src/townlet/environment/token_publishers.py:823), [item](/home/john/hamlet/src/townlet/environment/token_publishers.py:982)). Tests deny hidden agent reads, reject unknown actors and omitted actors, preserve storage on denied same-value writes, and prove immutable snapshots despite mutable source-list edits. | Closed by retiring the unsupported role vocabulary, explicitly authoring executing actors, and checking agent publication/convenience/item access consistently. Simulation legitimately continues to execute as engine. Closure does not promise those retired roles now execute, nor engine-confidential state. |
| `hamlet-c78fbf32a3`: empty exposure rewritten to agent | Canonical DTO has required explicit exposure and no fail-open rewrite. [real witness](/home/john/hamlet/tests/test_townlet/integration/test_static_epistemic_access.py:33) asserts the sole compiled observation binding is public_state while hidden_score and readable_unexposed are absent; readable_unexposed remains agent-readable and equals7. Actual ADVANCE updates hidden_score, which supplies named reward, through two rows/two episodes/direct and MessagePack paths. This distinguishes hidden-but-active state from dead storage. | Closed; historical duplicate of already closed `hamlet-d97b4d6b4a`, now requalified under canonical authoring/static access. Explicit[] remains unexposed, independent of permitted readers. No owner/locality privacy claim. |

Independent current-checkout verification:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=/home/john/hamlet/src \
 /tmp/hamlet-static-epistemic-access/.venv/bin/python -m pytest --no-cov \
 tests/test_townlet/unit/config/test_variables_dto.py \
 tests/test_townlet/unit/vfs/test_static_access.py \
 tests/test_townlet/integration/test_static_epistemic_access.py -q
```

Terminal exit0: **55 passed in1.35s**. Log `/tmp/hamlet-historical-static-bugs-verification.log`. Interpreter is the task-owned locked environment; import origin checked as `/home/john/hamlet/src/townlet/__init__.py`. No new full-suite, CUDA, browser or convergence claim. Tests include positive runtime witnesses and purposeful independent negative controls; closure is not inferred from the presence of DTO fields alone.

Broader historical privacy issue83 stays open: role-level denial and no observation binding do not implement a per-owner/per-observer visibility contract or shared-world item isolation.
