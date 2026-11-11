# Native owner caller alignment — sealed prerequisite

2026-11-11. Sole authorized test writer; source-writing baton returned to root with this report. Runtime qualification remains pending.

Read/written inventory: exactly five application/test implementation files, originally4259 lines, finally4262, within5000. Production files remained read-only. Only the two named tests and this required report were written; no helpers, tests, runner changes or compatibility arrangements were added.

| Path | Final lines | Final SHA256 |
|---|---:|---|
| `src/townlet/exploration/world_curiosity_state.py` |1253|`8aaa59e919e82ca49431620f25a77ddd5b08f2c9a845e7c4f5593f1eed6072b0`|
| `src/townlet/exploration/rnd.py` |1128|`53cccad55acad4018518bd498206129feddc5f54113560103cab60c94659ac46`|
| `src/townlet/exploration/provider_factory.py` |153|`dc69a831e045bed5c71b5bd448b1e9ff0163e6bce9d816b41d10af0f580708c8`|
| `tests/test_townlet/regressions/bac/test_owned_native_metadata.py` |314|`eab1491f577ab57b19d997ca848d1eada2a2df68569553957510b2aa190045e8`|
| `tests/test_townlet/regressions/bac/test_pw_local_service.py` |1414|`2fed03f1e10f39cbcd34b54aaa2fb938b36c5da3aa288bdb4d485149fc96f11f`|

Original test seals were metadata313:`f2b80206308e82aa0c8c98ece0a40e2e50513b588002b1e97fded51dc765503e` and service1412:`156a01b98eacc4cff1badcb51206f73ebb01af2d2e0abecd4b9348c18e7db674`. All three production seals match their original values exactly.

All56 actual owner lifecycle calls now supply explicit standalone `lineage=None`: metadata27/service29. No nested owner calls required held lineage; raw provider and WorldRNGState calls retain their genuine distinct APIs.

Causal source: `_BackendOwner._scope` requires explicit lineage; ordinary `OwnedWorldBackend.snapshot` and `call` advance revision. `_validate_prepared` refuses consumed handles before destination-currentness checks and rejects observed destinations before publication. Contract facts and R53 missing-lineage failures agree with these sources.

The service continuation test now completes genuine prepare/install and exact next-learning/private-stream continuation before independently preparing and observing a new handle. Its original no-mutation/ambient checks and stale refusal remain, using the current `destination changed` message. The metadata continuation test's consumed-handle control now requires `already consumed` rather than obsolete installed terminology.

Static before/after AST inventories preserve all42 original test function/parameterization identities, all98 total function signatures/decorators,125 assert statements,124 comparison/learning/conservation/metadata calls and15 pytest refusal calls. Comparison removes only newly explicit lineage keywords and normalizes the two documented message corrections; it preserves complete original assertion/oracle subtrees with multiplicity. The stale-control statement order changed intentionally.

Original recursive mapping types/order/metadata, independent native equality, tensor/NumPy ownership, alias mutation, genuine Adam/FIFO/RMS learning, gradients after next learning, private streams, pure-validation refusal and observation-staleness controls remain. Native schemas remain exactv4 and predictor_service.version3; no native validation was weakened.

Read-only evidence included AGENTS.md, the finite brief, relevant R53 log failures and the two named public contract documents. The RNG contract contains two API-guidance code fences, including one tiny illustrative reset_rnd helper; those were exposed by reading that document and reported immediately. Root explicitly acknowledged these as public API guidance, not a sixth application implementation file. No additional implementation/helper/probe body was opened or copied.

Static commands from `/workspace/hamlet`, using only existing `.venv`: `.venv/bin/black --check tests/test_townlet/regressions/bac/test_owned_native_metadata.py tests/test_townlet/regressions/bac/test_pw_local_service.py` PASS, both unchanged; `.venv/bin/ruff check` with the same two paths PASS. Scoped Black formatting preceded those checks.

Inline standard-library AST-only checks: parse all five files PASS; original function/decorator/assertion/oracle/refusal inventory comparison PASS; all56 explicit root lineage sites PASS; production SHA256 equality and per-file/total line caps PASS. No application modules were imported or compiled.

No pytest, application runtime, compiler/import probe, dependency installation, Git/index/commit operation, branch/worktree/checkout, source copy, deletion or subagent was performed. Root owns actual fixed-source qualification: first the23 original failing native nodes, then a coherent affected selection. The separately owned DemoRunner ENV world_roster/training_seed/lane_world_ids prerequisite remains unchanged and unqualified; no other mismatch was established statically.
