# Cold-import TOOL implementation — frozen for independent review

2026-11-14. Implementation and synthetic qualification complete within the root TOOL grant. **Independent tooling review and root adoption remain required before actual cold application runs.** No APP source/test body was read, imported, executed, copied, or changed. No Git command, index/branch/worktree/remote action, server, delegation, or R114 runtime namespace write occurred. The repository guard is exercised with inert metadata subprocess stubs; its real use remains root-owned.

Grant, accepted v2 plan and Astra review hashes match the supplied anchors. The immutable freeze is `E/cold-import-tool-qualification/implementation-freeze-v1.json`, where E is `W/evidence-management`. It binds every attempt record/log, final source counts, runtime supplier facts and the exact tool seal proposal.

## Exact final bodies

| Body | Lines | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| `/workspace/bac-review-2026-11-01/qualification/test_verify_bac_cold_import_identity.py` | 702 | 38421 | `1e3c9272c28af735f6f64e8ad9f53ebbdce02c27741a73749893c72fbfd8e1c0` |
| `/workspace/bac-review-2026-11-01/qualification/verify_bac_cold_import_identity.py` | 605 | 35312 | `5263c63dd4881a9d2b4af951819e89876b76b8c63cd724ba36d953fa515fb9cb` |
| `/workspace/bac-review-2026-11-01/qualification/bac_cold_worker_identity.py` | 105 | 5130 | `eadc46dd32ec17e74f59d53293d4e5a774eefa3af489146335bd5c2be3a4379a` |
| `/workspace/bac-review-2026-11-01/qualification/verify_bac_replay_spawn_identity.py` | 752 | 38090 | `6006c7247d79a99226a74756a2266a2966fce800f9f84af802f2990db4606173` |
| `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/test_replay_spawn_verifier.py` | 1536 | 68009 | `469a6a5708a384f0563eebf950bc981485e2a64c4e7ffb41a6d51ac8b85b8f08` |

New bodies total 1412 lines; four-body TOOL packet including unchanged verifier totals 2164 lines. Including the admitted unchanged strict synthetic suite yields 3700 lines/five bodies, below 4338/five. Individual maxima1000/250/800 are respected. Existing verifier and strict suite hashes remain unchanged. These paths are the final exact executable bodies; no application/source execution copies were created.

## Behavior and tests

- `verify(spec_path, role)` and exact two-argument CLI accept only the five v2 role/node/mode/entry rows. Five separate authenticated one-job harness specs are required, but only the selected result is required. Root spec/result/log/worker marker, candidate inventories, all file references, runtime binary, source-derived module allowlist, worker PID/start ticks, nine argv elements and exclusive final custody output are bound. Source/input drift is rechecked after the established repository guard. Unknown/duplicate roles, files, paths and symlinks refuse.
- JSON uses recursive duplicate-key and nonfinite rejection. Closed nested schemas and typed comparison reject bool-as-int substitutions, missing/extra fields, wrong scalar types, bad durations, source/argv/proc/hash mismatches and incomplete cleanup. The recursive tests mutate every nested child scalar and every nested record object; mutation helpers preserve deliberate malformed bytes while updating only their provenance links.
- Literal extraction uses AST and tokenization without executing the probe/test. Exactly one ASCII string assignment is required; adjacent/dynamic strings, assignment/delete, function/class/import/argument/exception/match/namespace rebinding are rejected. Exact fault assertion/raise and designated caller sites are derived from inert source AST. Fault stderr must contain one complete terminal traceback with the exact caller/site frames and exact final diagnostic.
- Positive checks require cold checkpoints, manifest-derived origins, fixed18 descriptors, two missing-export recoveries, four canonical gates, exact ordered caches,16 unresolved contracts, resolver2→3/3→4/4→4/4→4, repeated owner/participant/descriptor/policy/cache identity, state/RNG equality, single-thread child profile, zero CUDA observations and successful cleanup. Tests mutate each named semantic control plus fault phase/count/site/exception/inventory.
- Stdlib worker plugin emits actual PID/PPID/start_ticks/cwd/interpreter/argv/thread facts and an exact byte-hash marker. Qualified env failures never downgrade, including BAC_COLD_SPEC alone. Synthetic plugin tests exercise actual PID/proc-start/binary/thread observations; argv/proc argv and qualification context are explicitly substituted inert fixture boundaries. Unqualified absence is a no-op. No Torch or Townlet import occurs in this plugin.

## Immutable attempts

| Attempt | Result | Disposition |
| --- | --- | --- |
|01-red|1 setup error|Missing validator caught in fixture setup; retained, not claimed as causal test FAIL.|
|02-red|1 failed|Direct behavior test fails because validator implementation is absent; causal initial RED.|
|03-plugin-red|1 failed|Worker behavior test fails because authoritative plugin is absent; causal plugin RED.|
|04-synthetic|106 passed|Initial bounded parser/provenance matrix GREEN.|
|05-matrix-red|11 failed,152 passed|Nine fixture helper repairs of intended mutations, plus missing launch/binary check and validation-time input drift checks. All retained and corrected.|
|06-matrix|163 passed|Expanded recursive object, argv, source, fault and drift matrix GREEN.|
|07-binding-red|8 failed,172 passed|AST named-binding bypasses identified and closed.|
|08-final-boundaries-red|2 failed,186 passed|BAC_COLD_SPEC-only downgrade and duplicate role-directory omissions identified and closed.|
|09-final-green|269 passed|188 new synthetic nodes plus81 unchanged strict-profile synthetic nodes; disjoint file selections. Strict suite ran once.|

Exact argv, working directory, absolute UTC times, exit, elapsed time, environment and source hashes are in each exclusive attempt `record.json`; complete output is in its `pytest.log`. Final XML records every selected node. No failed/setup attempt is discarded or treated as runtime qualification.

Final command:

```sh
/workspace/hamlet/.venv/bin/python -B -m pytest -c /dev/null --confcutdir=/workspace/bac-review-2026-11-01/qualification --no-cov -p no:cacheprovider /workspace/bac-review-2026-11-01/qualification/test_verify_bac_cold_import_identity.py /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/test_replay_spawn_verifier.py -v --junitxml=/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/cold-import-tool-qualification/attempt-09-final-green/pytest.xml
```

Final process PID172826, CPU affinity[0], observed OS task counts[1]; OMP/MKL/OPENBLAS=1, PYTHONDONTWRITEBYTECODE=1. Venv invocation spelling is preserved. UTC2026-11-14T05:12:39.443669+00:00 to2026-11-14T05:12:53.150972+00:00; wall13.707290s, pytest13.06s, exit0. Final before/after source inventories are identical. Pytest8.4.2, Python `3.13.5 (main, Aug 10 2026, 12:06:59) [GCC 14.2.0]`.

Existing strict fixture provenance: unchanged `E/test_replay_spawn_verifier.py` authors literal inert data (`SYNTHETIC DATA; NEVER IMPORT OR EXECUTE`) and stubs external Git metadata commands. The selected existing verifier retains bootstrap imports, its closed role table and interop=5 checks byte-for-byte. Synthetic data does not execute those represented application modules.

## Tool seal proposal and remaining limits

`E/cold-import-tool-qualification/tool-seal-proposal-v2.json` SHA256 `dc0694e146e2c74c984efb51c86ce19d3047e33e0f6533e50eaacaa2b958b3a1` has exactly the accepted tool/runtime grammar and is pending independent review/root adoption. Runtime observations are root-supplied from `E/cold-import-runtime-facts-v1.json` SHA256 `0deb2e44d9ddb8cb2137fc20b5639042ad6b54e9658d253c3a832405316e02a8`; this implementer verified referenced binary/Torch/NumPy file hashes without importing dependencies. Full `sys.version` is preserved.

The accepted runtime grammar has a binary hash but only Torch/NumPy path/version fields. Their independently observed file hashes remain in the root runtime-facts record; no unauthorized schema extension is introduced. Descriptor rationale nonemptiness and agreement are parser checks; exact source semantics, observer ordering, actual Popen use of the extracted literal, real owner locks/gates, actual zero effects and fault causality still require independent APP source review and root execution. Parsed synthetic zeros cannot prove runtime purity.

AST caller interface supplied to APP: unique `_cold_boundary()` within the explicit preflight_preloaded branch; unique direct `torch.cuda.is_initialized` attribute within explicit preflight_cuda_touch branch. Enclosing function or <module> and literal source lines determine witness sites. Worker env is the established BAC_QUAL_* set; APP/root own BAC_COLD_SPEC lookup and runtime equality. No source/profile fallback exists.

Root must independently review these frozen tool bodies, qualify the exact tools, adopt a final seal, freeze final APP/candidate/spec bytes, execute both negative jobs before the three positives, and preserve required final existing89/activation/producer/profile selections and union accounting. This packet proves only synthetic parser/provenance behavior and the unchanged strict synthetic profile. It proves no actual cold application run, GPU hardware behavior, producer leaf purity, post-poison permission, B6/R0 or package/programme acceptance. Implementation edits are stopped for review.
