# APP-C1 repaired freeze for R120

Supersedes implementation-v1-handoff only for current source bytes, repaired review findings, selector fixture and witness schema. The earlier record and every RED/failure remain preserved.

Root R118 independently reproduced foreign lookup expiry race; R119 verified both durable owner variants and actual postpublication invalidation failure. Root released one coherent repair. `_local` now tolerates expired foreign lookup via safe registry lookup, preserving strict same-thread handle checks; runtime final install directly calls private `_forward_bank` under its existing delegated guard, then performs only preallocated assignments. Selector test uses real active-on-entry row slices. No other behavioral scope change.

| Body | Lines | SHA256 |
| --- | ---: | --- |
| config/exploration_policy.py | 1313 | 50a738825ae151cbf7a2907660e4cd06df7e42ae78128135eda891b3c6c885f9 |
| exploration/scoped_curiosity.py | 1443 | 55e0ac73ed65932aaf19c0622c8f11c5bb3801fda8957492ccf513d270a104b4 |
| exploration/parent_custody.py | 236 | 5b592ac955d8e45b3369d4dac3a1bc2996093dfaa8427d732183d321aada801a |
| tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py | 827 | 579ade676a5d42a66ee24fcb6aa7743b3cc00739114aec0c685e8fa0bb6043e7 |

Total3819/four, all caps respected. Additional durable nodes: test_ordinary_contender_survives_scope_expiration[runtime]/[bank], test_install_has_no_postpublication_invalidation. No application imports/tests/execution by author. Exact static argv/output/source hashes and preserved failures are author-static-checks-r120.json. Scoped Ruff and four single-file Black checks PASS; syntax AST/compile PASS. Black multi-file default and workers1 attempts were sandbox-refused at SyncManager socket creation; single-file checks/formatting avoid that tooling path. No escalation requested.

Poison witness retains v1 exact keys and additionally requires top-level runtime_profile with exact keys executable,torch_origin,torch_version,intra_op,inter_op,anomaly_enabled. These are actual sys.executable, loaded Torch origin/version and getter values; no thread/anomaly setters, CUDA queries or RNG draws. Existing role/node/receipt/error/source/process assertions remain. Root independently verifies actual values and ancestry; expected source references are not fabricated observations.

Pre-edit snapshots are pre-r120-repair; preformatter input including all failed style attempts is pre-r120-format. R119 executed bytes remain root-owned. New bytes are frozen for root GREEN, full type/static gate, source-matched coherent controls and independent review. Prior nine-group acceptance mapping and all later integration/hardware obligations remain unchanged and required.
