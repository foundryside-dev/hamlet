# Source provenance

Original scoped review/execution retains its recorded actual identity. The final source binding verifies the reviewed files are identical in qualified source `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; no execution is relabeled as occurring at a later HEAD.

Original `T14-native-independent-execution-r1.md`, SHA256 `25fcb814c347d6732a20d8823c44b341da4b93af145d01bad857766010304dc1`, retained unchanged. Portable rendering normalizes execution paths.

# T14 native independent execution R1

**Verdict: PASS for the bounded65 native regression cases at the common R1 candidate.** Actual test-job exit0,65 collected/65 passed in11.55s; harness wall time18.55561113357544s. No new P1/P2 defect or execution gap found within this slice. The R0 codec diagnostic-pattern failure is no longer present. This is independent execution, not an inherited root result.

Existing checkout `/workspace/hamlet`; HEAD `01f2f64f42c2932177729607b337419355cb2720`; candidate `324438ad58d9d5a85bba54e18be1ee225ada5969`. Manifest `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave08/green-r1-candidate.json`, SHA256 `2c60cc34fe84cccefb7041aa9ad67928c8a7184a69bb01935b59b4fba6ccb6e5`. Root explicitly allocated one CPU; the execution has finished and that slot is released.

## Command and evidence

Executed the root-supplied qualification API, without inspecting its implementation or any new application/helper source:

```
.venv/bin/python qualification/run_bac_packet_checks_locked.py qualification/wave08-astra-native-r1-spec.json
```

The external metadata spec names the existing checkout, R1 manifest, workers1, and previously absent output `qualification/wave08-astra-native-r1`. Actual job command:

```
.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_recurrent_per_native.py -q --no-cov -p no:cacheprovider -p bac_source_identity
```

Read the actual job result JSON and complete pytest log, rather than relying on the outer driver exit. Result: `exit_code: 0`, `65 passed in 11.55s`. Identity receipt confirms HEAD/candidate above, imported module `src/townlet/__init__.py`, Torch `2.11.0+cu130`, controller worker, threads1. The supplied harness sets CPU thread limits and CUDA empty, checks exact HEAD/tree/112 guarded hashes before and after, and uses its shared metadata lock; no separate git write-tree command was issued by this reviewer.

| Artifact | SHA256 |
|---|---|
| external `wave08-astra-native-r1-spec.json` | `9394d8c0f0fc127bc5c5d9b54a0c76f76c1739e7b358f5e6e33edddead53bc2d` |
| qualification harness | `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791` |
| `wave08-astra-native-r1/native.log` | `e86f5ce04042ea26e786d760aaf598adf9a9bed174f7629e9f26213aa28457a3` |
| `wave08-astra-native-r1/native/identity-controller.json` | `4385079c379b3f7bd975f54c2d54eae571db405e7a7c9dd81b6fe1bf36487175` |

The identity plugin is root-provided SHA256 `0a376a6454e317104adc4bce2cdc0d268c216de8c67e91e60623e6df7d31719d`; it was used via the supplied API, not opened as an additional source. Detailed machine result is `wave08-astra-native-r1/native-result.json` alongside the log.

## Source custody and preserved review

The complete source review context remains3/3176, within reservation3/3229 and hard5/5000. Runtime did not expand the implementation inspection inventory:

| Whole source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/training/historical_checkpoint.py` |675|`74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`|
| `src/townlet/population/vectorized.py` |1854|`38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b`|
| `tests/test_townlet/regressions/bac/test_recurrent_per_native.py` |647|`a2c6d57a2585f60471f4df8e54867dfa6ac781686d5e4bf2aab21ffd8b66335d`|

R1 static report remains unchanged at SHA256 `019e596df71db1fb371291981e16c937c3719a9819f47677d4ae6a92f5a0f26b`; its STATIC CLEAR verdict and full source/spec reasoning remain historical and separate from this execution. R0 report remains preserved. Post-run read-only cached comparison matches the exact candidate, unstaged tracked diff is empty, and source hashes above remain unchanged. Index SHA256 remains `016996c8213948d48f03468d31871f69f68e685ff863b1d8f559bf343c7fdbc1`.

Only external qualification metadata/results and this ignored execution receipt were written. No source/test/index mutation, staging, commits, branches/worktrees, project-source copies/deletion, new executable probes/helper inspection or subdelegation occurred. All14 existing worktrees remain preserved. Applicable preservation/History A precedence and existing instructions/actual approvals remain unchanged; no durable rule or user-only fallback was adopted.

## Qualified boundary and remaining obligations

The65 passing cases provide actual evidence for both HC classification gateways, complete owned current6/7 envelope transport, rawPOP6 carrying inner7 through real save/validate/load and two physical relocation/resave generations, sampler-state continuation, bounded legal finite greedy use, malformed/configured incompatibility early refusal with unchanged learned state/input/source, genuine native-geometry captured6 active adaptation, unchanged uniform6, separate inspection transport/no-downgrade, and incompatible original118-wide DATA refusal.

Synthetic rows/counters/parameter markers remain transport evidence. This does not establish natural recurrent-PER producer/learner selection, evolved optimizer continuation, mode-specific inference loading, all native resources/RNG restoration, native10/7 identity/archive-union admission or C07. Separate core tests/review and root affected-owner/consumer/guard results are not rerun or claimed as independent evidence here. Whole T14 release, mandatory serialization/public-contract full gate, T15/T24/T25, finalsource/learning/E2E/coverage/slow/hardware/CI remain root-owned OPEN obligations. X04 finite unweighted TD telemetry P1 remains required in T15 before release/G2. Original66 tasks/22 lenses/54 requirements are preserved.

Returned stationary; independent runtime window complete.
