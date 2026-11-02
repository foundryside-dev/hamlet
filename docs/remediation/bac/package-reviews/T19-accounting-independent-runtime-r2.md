# T19 accounting independent R2 runtime

Executed only root's explicitly sanctioned locked wrapper command from /workspace/hamlet, with TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 and DATA spec /workspace/bac-review-2026-11-01/qualification/wave12-r2-independent-accounting-spec.json. Wrapper and identity plugin implementations were not inspected. Normal process closure exit0.

Actual result: all12 parameter-expanded cases from the five appended public-counter functions PASSED, no skips, pytest10.37s; wrapper wall14.736199855804443s. Four xdist workers, worksteal, unique workspace basetemp /workspace/bac-review-2026-11-01/qualification/scratch/wave12-r2-independent-accounting. Benchmark plugin warned that benchmarking is disabled with xdist; these are functional tests, not benchmark claims.

Result DATA: /workspace/bac-review-2026-11-01/qualification/wave12-r2-independent-accounting/independent-accounting-result.json
Log: /workspace/bac-review-2026-11-01/qualification/wave12-r2-independent-accounting/independent-accounting.log
Verified log SHA256: 2546f2bf0308dcf1496c4d739eae8c48e15aaeddcc091d1a602115ffa4cfefbb
Manifest SHA256 reported by wrapper: c9b0ac7c6aa11e0000bfe7958853bd5dc0a4d6bc0ab640545db0ffb86d17382d
Harness SHA256 reported by wrapper: 180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791

Read and verified all five identity JSONs in the output's independent-accounting directory: identity-controller.json, identity-gw0.json, identity-gw1.json, identity-gw2.json, identity-gw3.json. Each records its corresponding worker, base SHA bc47e44662f7bea953156a668610a20e6bced9f2, candidate tree ed3cf26770875fc28dab25d89567dd65a19764fe, imported module /workspace/hamlet/src/townlet/__init__.py, torch2.11.0+cu130 and threads1. No installed-copy identity or unexpected source binding appeared.

Post-runtime SHA256 independently rechecked and unchanged from reviewed R2 DATA:

- src/townlet/exploration/rnd.py: 821fd3095e896a5b98d44a671906f9c5cbccec2f00fa430a6f5bb8acb24e4109
- src/townlet/config/bac_options.py: 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916
- src/townlet/exploration/adaptive_intrinsic.py: 80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9
- tests/test_townlet/regressions/bac/test_rnd_service.py: 0477b2531b8a1a109bf71285310c0beda725e295f11c51f61f6713005c2f6a62

Interpretation: actual positive legacy parameter change and Adam clocks passed; partial/full direct-update accounting and the documented unserviced append timing passed; configured and legacy real zero-loss Adam updates count independently of the scalar loss; all six configured mode/policy receipt comparisons passed; frozen owned primitives, guarded no-clone/no-service/no-model/no-optimizer observation, queue/model/optimizer/gradient identity/state preservation and Python/NumPy/Torch RNG preservation passed in both configured states. These are bounded producer findings, not wholeT19 or wholeBAC qualification.

No repair required by this runtime. Optional direct new-view assertions after historical/full restore remain optional only, as recorded in the static receipt. Root owns separate POP no-defaults repair, global custody, integration, commits/push and the user's stop-after-T19 instruction. No source/helper/probe/test/index/tracked-doc edits, branch/worktree operations, project source copy/deletion or delegation. Only this ignored runtime receipt authored. Runtime CLOSED; stationary, no next-package work.
