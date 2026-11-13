# Independent fix1 review: CUDA core child verifier

2026-11-13. Scoped re-review of the frozen two-body tooling fix, on the existing `/workspace/hamlet` checkout. This review executed only inert synthetic fixtures. It neither reads nor qualifies current application source, executes application children, or makes a hardware claim.

## Verdict

- **SPEC: APPROVED for the bounded tooling fix1.** The previously blocking extra-record gap is closed: the verifier requires each nested fork identity and observation filename inventory to equal exactly the admission/local pair before reading or issuing custody.
- **QUALITY: APPROVED for the bounded tooling fix1.** The new tests reject an extra identity, lone extra observation and extra pair with the intended inventory diagnostic, while the full synthetic suite passes. No relaxation or new breakage was identified in the scoped delta.

The four added verifier lines at `verify_bac_replay_spawn_identity.py:137-140` enumerate both matching `fork-identity-cuda_core_inherited_pid-*.json` and `fork-observation-cuda_core_inherited_pid-*.json` files and require each set of names to equal the two fixed trial names. This handles the exact identity-only witness from the first independent review and the observation-only/paired variants. Missing fixed records also fail before custody. The three new methods at `test_replay_spawn_verifier.py:677-695` require `ValueError` with `unexpected fork record inventory` and absence of a custody output. The remaining verifier checks and finite ten CUDA/two replay role maps were unchanged in the 41-line scoped diff.

## Independent execution and ledger

Command: `/workspace/hamlet/.venv/bin/python -m unittest discover -s /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management -p test_replay_spawn_verifier.py`

Exit `0`; raw result `Ran 50 tests in 0.535s` and `OK`. Raw log: `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/cuda-core-child-verifier-fix1-independent-sol.log`, SHA256 `1af472e76eb04ac7036708ef20553b8229172ff290f1a8b4875591c4c1e188d1`. These 50 overlap the author's 50 and any root repeat; they are not additive counts. No application import or actual child execution occurred.

Frozen verifier: 401 lines, SHA256 `872ed3a110789627d28b97af2eb64d7c8e15f6f46bad14942c52b0f529787ac4`. Frozen tests: 714 lines, SHA256 `fdf75f6072f625d8788c5ae4ebe9efc9cfa693f7469aa2db6c339f9816ead683`. Two-body total 1115; five-body total 2075 using the retained 960-line basis, below the hard 5000-line ceiling. Scoped fix diff SHA256 `43c4dbe7d19ca273bca94e7d4220bb1aa3e9583e0a6865a9964c596fe0001a0c`; supplier report SHA256 `51b1807193bc883d99d9da28d2de8a72af157777221eecec1757e0ec3bf09f10`.

This approves the verifier fix only. Full application source qualification and actual new child custody remain separate root-owned gates; no child, CUDA hardware, B6, package or publication result follows.
