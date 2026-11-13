# Independent review: CUDA core child verifier extension

2026-11-13. Reviewed only the existing `/workspace/hamlet` checkout on `project-recovery-bac-2026-11-01`. This is a synthetic tooling review. No application or hardware child was run, and no actual child evidence was accepted or published.

## Verdict

- **SPEC: NOT APPROVED.** The verifier accepts an extra unknown nested fork trial record, contrary to the finite two-trial protocol's explicit no-unknown-trial/no-extra-success requirement.
- **QUALITY: NOT APPROVED pending the same bounded repair and an independent repeat.** The 47 synthetic methods pass, but they contain no mutation for an additional fork record. Other examined finite mappings, schemas, process/source/profile checks, and retained replay checks were consistent with the approved protocol.

## Blocking finding: unknown nested record is ignored

`verify_bac_replay_spawn_identity.py:141-145` reads only the fixed `admission` and `local` paths. It does not enumerate or reject other `fork-identity-cuda_core_inherited_pid-*.json` or `fork-observation-cuda_core_inherited_pid-*.json` records in that job directory. `test_replay_spawn_verifier.py:594-614` checks missing/extra *fields* and missing fixed records, but not an extra record. The approved child qualification protocol expressly requires no unknown trial or extra success. The final CHILD-API specifies exactly two named record pairs.

Fixture-only witness, run in a temporary synthetic data root with mocked repository subprocesses: construct the existing `CudaVerifierTests.fixture()` for `inherited_pid`, copy its admission identity bytes to an additional `fork-identity-cuda_core_inherited_pid-unknown.json`, then call `fixture.invoke()`. Actual output: `EXTRA_UNKNOWN_TRIAL_ACCEPTED cuda-core-inherited-pid 2 fork-identity-cuda_core_inherited_pid-unknown.json`. The verifier wrote a custody receipt containing two accepted `fork_guards` while the extra record existed. The fixture was cleaned. No verifier/test/application source was edited. The original tooling author should reject additional matching fork records, including a lone extra observation, and add a synthetic mutation that fails for the intended reason.

## Finite checks reviewed

The closed `CUDA_CASES` list generates the exact nine ordinary CUDA job/node/role/message mappings plus the separate inherited-PID coordinator mapping in the final ten-role CHILD-API. It retains both replay role configurations and their exact arguments. The CUDA outer identity adds the two required import paths and test-byte hash; its observation requires queued PPID. Existing controller, full child Torch/thread/debug, source/config/artifact inventory, manifest, result/log/harness, repository and positive finite elapsed checks remain in the verification path. The inherited coordinator requires both fixed guard identity/observation pairs, exact fields, actions, diagnostic, zero counters, source hashes, manifest, role, ancestry, distinct PIDs, actual single OS thread counts, null Torch profile, identity byte hashes, and integer raw wait status/exit code zero. Boolean integer impersonation is rejected in evaluated PID/count/status fields. Receipt scope states the guard-only and production source-review limitations. The verifier checks recorded facts; it does not independently instrument a production process.

No second blocking issue was identified in the authorized two bodies. In particular, the added CUDA path does not bypass the retained replay checks. The extra-record finding prevents using this frozen verifier for qualified new child custody until repaired and reviewed.

## Independent command and source ledger

Command: `/workspace/hamlet/.venv/bin/python -m unittest discover -s /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management -p test_replay_spawn_verifier.py`

Exit `0`; raw output: `Ran 47 tests in 0.533s` and `OK`. Exact raw log: `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/cuda-core-child-verifier-independent-sol.log`, SHA256 `2777b0fdee07acc232d82e5e6117bc8a187139164d472646a8a18a330cd0fd0e`. The fixture suite mocks Git subprocesses and flock and uses inert synthetic file bytes. These 47 overlap the original author's 47 and any root repeat; they are not additive test counts.

Reviewed frozen verifier: 397 lines, SHA256 `1853e8a56f0f79cd1d413eb5b03898ee0bbe63d512e280c94e0d5530b5c14a6d`. Reviewed frozen tests: 695 lines, SHA256 `f379be75c9a72b65cbe5130d59e8616ec5ababfdcbf4805c3c3d6a96e4b8ae13`. Two-body total 1092; five-body total 2052 using the report's unchanged 960-line retained basis, below the 5000 hard ceiling. The supplier report SHA256 is `dcc75991e32fab0fb53051ecb59598e4bdf5710205381591288957d53895813f`; scoped review diff SHA256 is `8c045d380cfdae6789c7fdf09720779b894dd5b5c4616ef650898a87187d7603`. The final CHILD-API source report SHA256 is `495b1687d65a54fea2462b1d1093d3c0d0e7b68c752caca0b6a01a9660a0eaf3`.

The last captured/executed application candidate was R87; core production writing began after tooling freeze. This fixture-only review neither reads nor qualifies current application bytes. New child execution remains UNRUN. This review makes no CUDA hardware, B6, package or publication claim.
