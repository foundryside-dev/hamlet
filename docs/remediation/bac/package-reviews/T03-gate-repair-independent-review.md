# T03 gate repair: scoped SPEC and QUALITY review

Verdict: **SPEC PASS; QUALITY PASS. No actionable defect in the one-line repair.**

The staged delta in `test_scope_surface_cut_bumps_exact_artifact_schema` is exactly the literal `1.40` to `1.41`. The node and exact equality remain intact: future schema drift still fails. No comparison widening, skip, rollback, fixture change, or production change is introduced by this repair. The current production constant is 1.41; its required field set includes `effective_run`, whereas the explicitly known 1.40 reader derives a current view with honest provenance. Pinning the current writer version does not require refusing the separately recognized historical reader version.

Scope: only `src/townlet/universe/compiled.py` (1615 lines) and `tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py` (285 lines), authorized source inventory 1900 lines. Reviewed relevant compiled-reader/writer sections and the complete gate module, patch, candidate, worker receipt, brief, and AGENTS.md. No other implementation/helper/test source was opened. The already reviewed original five-file T03 packet was not reopened. The assignment's explicit historical-loading requirement governs this scoped review; no new compatibility policy is proposed.

Independent execution in existing `/workspace/hamlet`, Python 3.13.5, Torch threads 1, with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/hamlet/src .venv/bin/python`:

- Genuine native 1.40 cache loaded through public `CompiledUniverse.load_from_cache`: `tests/test_townlet/fixtures/bac_historical/uniform-pack/.compiled/universe-L0_0_minimal.msgpack`. Verified SHA256 `917e5374e83227dcbfb4c626da4e5c74a9cab29dd7cdb9651b7d2c93c6019107` against `canonical_artifacts[0].config_files`; decoded original version is 1.40 and lacks effective_run. Derived provenance explicitly says `not historically captured`.
- Serialization yields exact 1.41 with effective_run; `CompiledUniverse.from_dict` roundtrip preserves the effective view exactly.
- Removing effective_run from that current payload raises the expected missing-required-field ValueError.
- Setting version 1.42 raises schema mismatch.
- Exact repaired node executed via `pytest.main(['--no-cov', '-p', 'no:cacheprovider', '-q', 'tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py::test_scope_surface_cut_bumps_exact_artifact_schema'])`: **1 passed in 0.04s**, process exit 0.
- Native cache bytes were identical afterward. Manifest SHA256 matched root's supplied `d1582c8a3b84eff4dca06c7fdf17e12c7b1adfcbf65f8c7b1c1979f1f87bbfe1`. All malformed probes operated only on in-memory dictionaries.

Before and after the independent probe/test execution, asserted identical identities:

- HEAD `049e305df42392373a52c9eb76552abbd74a5b2b`.
- Actual complete staged content tree `d3c1f4993efb73717826f6d4e1bf9e3cf0cd28d0`, computed read-only from all `git ls-files --stage -z` records using Git tree serialization, without write-tree or index mutation.
- Import `/workspace/hamlet/src/townlet/__init__.py`.
- compiled.py SHA256 `494f9676c236349f12c875c82dde821a85a3bf5077cae15654c78e8ac1630710`.
- Gate module SHA256 `cd99a009b217cade1e9896fa4b0e926dadb6b4657ac41c05fd6f89760f963730`.
- Index SHA256 `e673947afa8388ead2a35152af0c11102c347e76502d6daabc74e18c545acd90`.

The worker's node RED, node GREEN, 124-test module GREEN and formatting/static checks are receipt evidence, not independently repeated here except the exact green node. No concern warranted duplicating all 124 tests. Root's first full run was **1 failed, 5510 passed, 15 skipped**, not green. Six guards and the full rerun remain root-owned; this scoped approval does not assert repository green or final T03 acceptance.

No source/index/Git mutations, branch/worktree/repository/source-tree copies, fixture writes, subagents, or paused-work restart occurred. This review report is the only requested output file written.
