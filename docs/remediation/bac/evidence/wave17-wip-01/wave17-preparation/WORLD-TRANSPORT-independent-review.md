# Independent current-world transport review

## Candidate and scope

Reviewed requirements WORLD-TRANSPORT-brief.md, author report, supplied actual R1 diff package, both public current-world/current-compiled contracts, and actual changed code with its constructor validation context. Base supplied by root: 86ee0d91c463adb7ac14a7949ee7b67f91c6c171. Frozen R1 tree supplied by root: 6f46f449b2c851dc8838e00f48e7fddc8e436dc1. I did not independently query Git/index. Independently measured whole-file inventory and SHA256:

| Path | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/environment/vectorized_env.py | 2343 | f2b50300ae9d51fa9d6e4b069091ddd1064ce09f3f5e24df1c5917453237c784 |
| src/townlet/universe/compiled.py | 1663 | d8e2734b0845c7d23ac79180a724b216d7c881e079352356f108cb294d2b7384 |
| src/townlet/environment/env_factory.py | 88 | aa1b2cdf00ed25fcc63b57b944876504d77219d147b3265e820ff2ad88b2d2f0 |
| tests/test_townlet/regressions/bac/test_world_constructor_transport.py | 211 | daad8f762000886969762d52e2a415cc4a853d875621daf24449b9815bc61592 |

Exactly four counted files, 4305 lines, within individual 2400/1800/150/600 and aggregate 4950 ceilings. All measured values match the sealed author R1 report. No fifth implementation/helper/probe/fixture source, source edits, runtime/import probes, Git/index operations, branches/worktrees, source copies, deletions or subagents used. Only this ignored report was written.

## Spec verdict

APPROVE bounded source compliance. No P1/P2/P3 material defect found in this transport change. Runtime qualification remains pending independent guarded execution and root receipts.

CU.create_environment at compiled.py:768 requires all three world inputs and passes each unchanged through ENV.from_universe. ENV.from_universe at vectorized_env.py:1039 retains explicit-level refusal and passes the actual cls, universe, level, count, device, roster, seed and binding to EF. EF.from_universe at env_factory.py:57 requires the inputs, retains string-device normalization and level refusal, and calls the actual env_cls with the same identity inputs. There are no inferred IDs/seeds, optional defaults, compatibility probes, hidden bootstrap/reset/activation or owner substitutions. Subclasses still instantiate as their actual cls; constructor device normalization now occurs before subclass construction on this route, as required by the explicit factory route.

The unchanged actual constructor at vectorized_env.py:289 calls identity validation before substrate construction or randomness. Its validation at :1919 rejects wrong roster, malformed binding/count/seed and membership mismatch before installing even local identity fields. Missing device and absent selected level refuse before substrate/tensor/random work. The factory itself normalizes string devices without RNG or live-object mutation. Constructor failure may populate a fresh unpublished object's identity before later device/level refusal; this is existing behavior, not mutation of an accepted environment.

The supplied actual diff changes only argument declarations, forwarding, type-only imports, CU argument documentation and the new tests. Affordance/meter helpers, compiled schema/native/cache/policy calculations and constructor capability code are untouched. No evidence of introduced cross-interface breakage was found within these four sources. Global caller compatibility outside this inventory still requires root's guard receipt.

## Quality verdict

APPROVE bounded implementation and test design. The implementation is small and reuses the existing validation authority instead of duplicating world semantics. Type-only imports are consistent with deferred annotations and avoid a new runtime dependency cycle.

The test file exercises actual current 1.42 compilation with use_cache=False and real constructions through all three public routes. Positive tests assert concrete level/device/identity/membership/fresh-phase/cursor/tensor results. Reversed binding keeps authored roster order and semantic membership; changed seed changes identity without changing compiled policy. Instance independence is checked by actual tensor mutation. Missing and malformed inputs assert refusal plus unchanged CPU Torch RNG; malformed cases also compare an existing live environment and authored declaration. The subclass-routing witness wraps the real factory and additionally requires a real specialized environment, so it is not a spy-only implementation test. Runtime reset remains refused without reservation. Source-level parameterization accounts for 88 cases, consistent with root's collection receipt.

## Evidence limits and outstanding checks

No independent pytest/import/runtime was run in this review phase; no R1 PASS is inferred from the supplied R0 failures or prior producer receipts. Root's stated R0 causal failures are received evidence, not my executions. Root's focused7, joint193, six global guards and custody results were pending when this report was written. Independent execution requires the later exact spec/CPU-slot clearance.

The 88 cases use one CPU smoke pack and one selected level. They do not independently qualify non-primary multi-level selection, every selected family/static/adversarial/zero-width capability, non-CPU device execution or every RNG backend. Source forwarding preserves those existing constructor paths; broader claims need their existing guard receipts. Tests establish identity and fresh construction, not simulator/reorder independence, real lifecycle sink integration, actual learning or native restart/E2E.

The pre-change 13 global caller errors are not waived. The six missing arguments owned by CU/EF are repaired in source; the remaining oracle constructors/reset, POP reset/activation, VFS world draws, bank and parent/manifest/native integration plus final gates remain required named work. This approval does not declare coherent runtime, global mypy success or whole BAC closure.

## Independent guarded execution completed

After root supplied exact spec and one-CPU clearance, I executed the authorized positional runner followed by its verifier against /workspace/bac-review-2026-11-01/qualification/wave17-r1-independent-spec.json. Helpers were executed without opening their source. This ran the complete counted constructor-transport test file on the frozen R1 candidate, controller-only workers=1.

Actual result: **88 passed, 0 skipped, 0 xfailed, 0 xpassed, 0 warnings**, exit0, wall12.537709951400757s. Verifier exit0 reports source/index/import/threads/fixture custody PASS:185 source guards,573 config digests,13 protected artifacts,1 process identity,14 worktree registry records,1 available worktree. Candidate tree6f46f449b2c851dc8838e00f48e7fddc8e436dc1/base86ee0d91c463adb7ac14a7949ee7b67f91c6c171 match the reviewed candidate.

Execution log: /workspace/bac-review-2026-11-01/qualification/wave17-r1-independent/independent.log; runner-recorded log SHA256656d282d3efc1080612780e939adbb08e57e1987b692e721d5b39401bad74f06. Manifest SHA256a84e6f0563f2f33b122ef82e8812f6a2b0189a2b4e2f459f407b5f88221bb425; harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791. Runner session88228 finished exit0; verifier completed synchronously, with no remaining execution session owned by this reviewer.

Spec and quality verdicts remain APPROVE, now supported by independent actual88-case execution on the measured candidate. Root additionally reports focused7 PASS and global mypy7 errors in oracle/POP only, closing all six owned constructor errors; those are received root results. Root broader193 and compilerCLI were running at clearance time and are not asserted here. Remaining callers and all downstream integration/final BAC gates remain open; this result qualifies only the named bounded transport evidence.
