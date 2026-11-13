# CUDA core R89 independent actual-source verification

2026-11-13. **Scoped SPEC: APPROVED. Scoped QUALITY: APPROVED. Independent execution: 67 PASS, zero failures/skips/xfails/xpasses/warnings; all run and child custody verifiers PASS.** This completes the requested independent CPU core protocol verification at the frozen R89 source. It is not full BAC, producer integration, B6 or hardware acceptance.

This reviewer previously inspected the actual core/test implementation and finite production fix1. Retained source remains exactly two bodies: core821 and test1409, total2230 within reserved3000 and hard5/5000. No additional helper source body was read. Only the expressly authorized locked harness and verifier commands were executed; no application/tool/guarded-document edits, direct Git/index commands, new checkout/copy or delegation occurred. The authorized qualification harness owns its existing custody/index operations. This report is the sole authored output.

## Exact frozen identity

- Base: `e880ab6bd3bd8ec6c16ee6c5ace123b2ed1b6a32`.
- Candidate tree: `8416a6c8f887153d02ce8e19be9328d0fafe661e`.
- Manifest SHA256: `c6c679c633d7f47c185b3cb78996ad22b93607958ebbbc48c2214e21ee38e035`.
- Core SHA256: `0a0f19d37ac85b1584ea028e7e7268a04d18e9f39db0e41b9780181913aae477`.
- Test SHA256: `b044538dfe656976c0171d81fae4c3d44bba9b47f8b5072d846cfe2d9acf962e`.
- Locked harness SHA256: `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.
- Strong child verifier SHA256: `872ed3a110789627d28b97af2eb64d7c8e15f6f46bad14942c52b0f529787ac4`.

Every run verifier confirmed817 source guards,573 config digests,13 protected artifacts,14 worktree-registry records, one available worktree, one controller identity, and source/index/import/thread/fixture custody PASS. Every child verifier independently matched exact role/node/message, source/import/hash/manifest and actual PID/PPID ancestry. All process sessions completed with exit0.

## Actual invocation and ordering

Working directory was `/workspace/hamlet`. Define `Q=/workspace/bac-review-2026-11-01/qualification` and `PY=/workspace/hamlet/.venv/bin/python` only as abbreviations for the following exact executed command form:

```sh
env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=/workspace/bac-review-2026-11-01/qualification:/workspace/hamlet/src /workspace/hamlet/.venv/bin/python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py SPEC
```

First executed `Q/wave35-r89-independent-core-current-spec.json`, then verified it with `PY Q/verify_bac_run.py SPEC`. It selected the test file with `-k 'not test_isolated'`, normal single-controller pytest, `--no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q -x`:57 PASS.

Then executed each exact `Q/wave35-r89-independent-cuda-core-CASE-spec.json`, where CASE follows the table below. Each spec contains one job/workers1 and selects one exact node with `--no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q`; no xdist. At most two separate harness invocations ran concurrently. Pairs were bootstrap/runtime-query, single/multiple-body, unknown-ready/ready-qualified, healthy-only/operation-body, and duplicate-parent/inherited-PID. After each completed job, ran sequentially:

```sh
PY Q/verify_bac_run.py SPEC
PY Q/verify_bac_replay_spawn_identity.py SPEC
```

All11 harness invocations, all11 run verifications and all10 strong child verifications returned0. The unused workers2 batch spec was never executed or relaxed. Root's earlier ten pytest passes rejected for harness concurrency remain unqualified historical evidence, not results of this independent run.

## Hash-bound result references

For each job J below, exact spec is `Q/wave35-r89-independent-J-spec.json`; exact result and run custody files are `Q/wave35-r89-independent-J/J-result.json` and `.../J-custody.json`. The result records bind the actual log hash and exact command. All hashes below were independently read from emitted files after verification.

| Job | PASS | Spec SHA256 | Result SHA256 | Run custody SHA256 |
| --- | ---: | --- | --- | --- |
| `core-current` | 57 | `0e4863cedccc2e2747d256fa8493eb465b89b852d5d46bdc5b6d0101e62a674c` | `942bca13e006d84fda33b9d3b6c18f078eeebde9b5b91dcbe2fdb01e6df423e2` | `78b17cd5ae4bee32db8e731a4e1285cf9ff164fd093c6273858bd93e1e76cae1` |
| `cuda-core-bootstrap-failure` | 1 | `e66a4eb022a58db3d1e0806fb0f4bd3b98eeb48827c87dfa723daa705b93fab6` | `2b0ad96aed6340ccd00a34e531a724caa3d5c20f332b59c7b49033062d3209e0` | `c74c990ecc52bbcc850bd7ddf1f99b12d72c91ed4bfcd1337515e51e93ebd21e` |
| `cuda-core-runtime-query-failure` | 1 | `a87c73caeccbd373d1548781e377d4d68e3d42f6f0cafaba0f2ac2bf742e1bf3` | `5324ef37aa39b6c48ff4ab5f61bc698247c2a24b7fddd9cc8271a692dacce730` | `c3d224e04824e974bada4c9a7cc60aa2738c0b6f9b4d28cf8a0d6672faaff11c` |
| `cuda-core-local-completion-single` | 1 | `6d501bdc2598d177c08362808d0bc49bc7bf71cf74bf387f23d351693ecdb070` | `e3d3a3135710fb182662f839123284b1b4de0625bbcc63b151650c994ebacf28` | `bfab86a01d12c41c76721af5aa316559e5730918b5187bcfbde1e9139ab537a1` |
| `cuda-core-local-completion-multiple-body` | 1 | `e86ea76df0c0499247b04198c58005363e76174966c109bb820d7f01ecb2fa93` | `257bbe2450a07ebe9381952a6c078741c0156ea96d9fd2deafceea7798b4f0e6` | `15bc2f118d7484eaedeab0948e1e2590c5f896682adfa3f9dc77688b8bdee42c` |
| `cuda-core-poison-unknown-ready` | 1 | `ecf3db7781e67def1f99b6446c7eaa6a143bec61e5a2f5bc057f82cbbb70634e` | `4817962ed6d30bb700a1809ad9e5e051116ce19d22e2fe900591064634e2f9fe` | `54088f0a7c181be20995449242d32506947fcb942b8be98763be3b3e11dcefd6` |
| `cuda-core-poison-ready-qualified` | 1 | `65bad10939c89e080455dd960c7cbbbe7437d299f6a083b1098550daaa991e90` | `f2ced93321fbeb8dd1f32a0f125c35b6036aa4e564ae14102ef6d382b2593de6` | `4426198efa4b1ddd1625bb93f265c75d387b5012a287658be8f0c1f2e0faf050` |
| `cuda-core-poison-ready-healthy-only` | 1 | `8b1e4140e9029d1d828b7f45ac17004702b12e6f555f6819cdfa2e797ba7b908` | `49b921b760a5ad076fba7b4b1bbda53c55ada123724c49dd147d40035732a752` | `138a1a8c6e17008cfaef72f43534619348521ad6d642b44f1619b57601ba6531` |
| `cuda-core-operation-body-completion` | 1 | `ba9ab6a7091727610ff697bbc24910ef15830c127016c5fc42a5b63411c41532` | `04d427cad5ffbeec3783ecaca1f5872e1fc43f980130dda8d0f4e07a56adafa6` | `dcfba276148a58b2b5896c51da900f88c334e455e569b8ade29d9bca5fdec99a` |
| `cuda-core-local-completion-duplicate-parent` | 1 | `0c44558c16c871cc1a4d1868deddf6e41a856e86814744ebb4679ce3af3b54cf` | `bfcc926e20a75af5560657f2fe524748ef33dec17206d121a5d3169959efad5a` | `1f5329af1677fea07766dfcfd18af40e95f9db8d17a62869defa801a96aa0723` |
| `cuda-core-inherited-pid` | 1 | `25c7b990df85f03e6af999de2da7ce6c57c1387e63c95755212dde79fee5cce5` | `7f4a98244b1efdfc9f5d235efa36a0dfb73a6ec3afa732ec5e4af1fd3cbd2a0b` | `6c7366cb9ed9cf5f43f81c6b7a228e9cbedafdc971c793b0f68d45dfef2d0d1a` |

For child CASE below, job J is `cuda-core-CASE`, role R is `cuda_core_` plus CASE with hyphens replaced by underscores. Exact strong receipt is `Q/wave35-r89-independent-J/J/replay-spawn-custody-R.json`; it binds child-owned identity, parent observation, source and verifier hashes. Every child PPID equals the actual parent PID shown. Full spawn profile was Torch2.11.0+cu130, intraop1/interop5, debugtrue.

| CASE | Actual pytest parent PID | Actual spawn child PID | Strong child custody SHA256 |
| --- | ---: | ---: | --- |
| `bootstrap-failure` | 104926 | 105005 | `f0873f5f6203210abbdce5590835eb96e185ef4d1b2ea836af6089ae32bfdf5d` |
| `runtime-query-failure` | 104902 | 105030 | `d56cfe575eb45546cbc9612c577e42472ac0ac1a7e274b7cc85ef7d14188c575` |
| `local-completion-single` | 105404 | 105456 | `4d3696bd9c34d5a6659edc897b0a824a856e3d03fd387163667bb03ed4a2ee66` |
| `local-completion-multiple-body` | 105406 | 105481 | `3ad223dfdf54b6f59795a06fea2051f27b7908efef58215a0f50e43cecb8ebd3` |
| `poison-unknown-ready` | 105834 | 105887 | `9470efe99c48857af80648388301ffc5136431975a2655099107e845770caf4f` |
| `poison-ready-qualified` | 105836 | 105912 | `16450bd3b67abfd35591a3c1e96344b44d2b6a88540e5664c901b2a2661abd14` |
| `poison-ready-healthy-only` | 106328 | 106383 | `d582919a8176c06fb2deab4b06c0f2de603e1415d5a406ccb9af9cd7f4c8bef1` |
| `operation-body-completion` | 106326 | 106385 | `42542effb10bf415160337828f0795d3a765cee9f21d6cebad056bf3ccbac514` |
| `local-completion-duplicate-parent` | 106763 | 106840 | `e003c5f8676dcd996ddd7ded537c2046e085d3a2d294a9f357553525626d065d` |
| `inherited-pid` | 106765 | 106838 | `62d42e11631d9142dd93e4278af1dc1872ccfa712e42e3919ded2277a0ab415a` |

## Genuine inherited-PID evidence

The actual inherited coordinator was spawn106838 with actual parent/PPID106765. Its two live-gate fork trials had actual PID/PPID admission106892/106838 and local106895/106838. Strict verifier accepted their separate `linux-fork-inherited-guard-only-v1` profile, actual OS task count1 before each fork and in each grandchild, actual inherited domain PID106838, exact source-owner RuntimeError diagnostic for every action, zero measured domain/owner acquisition/CUDA/body counters and unchanged observed state. Null Torch profile is explicit; no Torch/CUDA work in the fork grandchild is claimed or needed.

- Admission child identity SHA256 `22fcc8dbd73011f0a06e0904f70f081d89bd7f2b201b39cbfb02d51c4e30ac2e`; parent observation `4fe493d535e21979e38995a473d883ea80d614b778810494eb2a7a6019bb4a24`.
- Local child identity SHA256 `5779d3994cf1e3413f5a21b792ce1aebb7eed3a859aed285ba35c23a49fded58`; parent observation `5e10b7167e5537acb94f7798d92e2a7302e2efba464bb7d03fbb253d1909ba9d`.

These are actual independent fork results, not synthetic receipts or PID patches. Their zero-effect interpretation is supported by the earlier independent review of production PID-first ordering, all actual lock routes/probe delegation and complete added gate/state observation. Parent/spawn health and ambient-state assertions also passed. The fork trials are evidence within one pytest node; they do not add two unique tests to the accounting.

## Scope and outstanding work

The independent selection is exactly57 ordinary plus10 isolated nodes =67 unique PASS. All67 overlap root's67; the combined unique selection remains67, **not134**. No new material implementation or qualification gap was found in this finite CPU core verification. The controls cover authentic admission/currentness/enrollment, explicit subsets and full-member nesting, local class/route binding, failure phases/identity/deduplication, owner-held quarantine, readiness/post-poison boundaries, pins and genuine inherited-process refusal.

Root separately reports global Ruff/Black/default600 and owned/public types PASS, plus the required coherent old selection1290 PASS and2 CUDA-unavailable SKIP. Those checks were not re-executed here, are not added to this67 count, and the still-deselected existing runner remains a required later gate. Preserve that distinction and the earlier failed/unqualified attempts.

No production GPU contract is enabled by these finite fixtures. Real producer dispatch/inventory/revision/preflight integration, Torch initialization/query RNG side effects, asynchronous CUDA completion and one-/two-device hardware qualification remain open. No CUDA hardware pass, B6, full BAC, package release or programme closure follows. Absolute UTC timestamps absent from producer records are not inferred.
