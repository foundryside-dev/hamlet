# PW04 source fix round 1: tests-only seal

Status: stationary tests-only candidate for root-owned focused causal RED. No provider repair or runtime/import execution occurred. Root increased the counted test allowance to1800 before growth; exact named ceilings are RND1000/ICM750/adaptive500/test1800, whole4/4050, hard5/5000. No extra source/helper was opened or written.

Read PW04-R1-FIX-brief.md first and the actual independent source review. Review initially named SHA8b3e81b4454fda2a9526a6c67c43b521322280af2744a0dca260db84a6e2908e; root confirmed its append-only updated/resealed SHA52e89742e0ad6acf4d7d254080a0aab94b0458f95533a852c0c02f88906d44b6, with R1-S1/S2/S3 finding text unchanged. Root also confirmed actual stale-token ValueError text. Neither clarification required a WS/RP fifth-source read.

## Stationary inventory

| Path | Whole lines | Bytes | SHA256 | Ceiling |
| --- | ---: | ---: | --- | ---: |
| src/townlet/exploration/rnd.py | 814 | 39863 | a6d7f5c152f3f00d36f818f9309425ce39655c5098b74e151e1a43bfabe6f0a2 | 1000 |
| src/townlet/exploration/icm.py | 468 | 26848 | 55dec9e755f426c156e8cadadbfeb8d7f234d87a2866f597cdf3dd4ef1e44eed | 750 |
| src/townlet/exploration/adaptive_intrinsic.py | 315 | 14372 | cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 | 500 |
| tests/test_townlet/regressions/bac/test_pw_local_service.py | 1412 | 58793 | 3dcc780c36c15b553272246ac605f9ca6a89cbd732f0142552fd1ee0df4f9dc7 | 1800 |

Actual4/3009. All three source hashes are unchanged from sealed R1. Only the counted test and this ignored prose receipt changed. The test has35 test functions and a static estimate262 parameterized cases: original214 plus48 new. No collection count or runtime result is claimed by this author.

## Exact finite regression delta

1. `test_overcapacity_shared_buffer_refuses_before_service`:12 cases, RND/adaptive × three overflow policies × admit_and_service/configured update. Each starts with eight finite external rows under B2/capacity4/paced cap1. Forward and Adam pre-hook spies immediately fail if any learning is entered, making initial RED bounded before the known room<0 loop. On proper preflight refusal, assert full method-entry state, recorded counters, ambient RNG and no callbacks unchanged. External buffer edits precede the baseline. No subprocess/timeout probe or copied learning implementation is added. Existing valid direct-buffer/unconfigured-tail learning controls remain.

2. `test_raw_adam_moment_dtype_refuses_before_loader_coercion`:24 cases, three actual providers × eight raw-moment mutations. Both exp_avg and exp_avg_sq receive float64/int64/bool mismatches; additional cases use finite float64 exp_avg1e300 (proved to overflow to float32 infinity) and tiny negative float64 exp_avg_sq-1e-300 (proved to round to float32 zero). Each validates refusal through validate_state, prepare_state and load_state with complete live/input/RNG custody and no model callbacks. Existing lawful warm float32 continuation assertions remain intact.

3. `test_native_optimizer_state_ids_refuse_bool_and_float_aliases`:12 cases, three providers × replacements0→False,0→0.0,1→True,1→1.0. Keep all payload/counter geometry valid and explicitly record key types. Each public native entrypoint must refuse unchanged; input key types must not normalize. ICM's existing exact-ID guard is a comparison, not a newly claimed defect.

New native cases call `_warm_native_validation_fixture`, which validates an uncorrupted warm payload before entering any expected-refusal assertion. Its full preparation prerequisite lies outside the malformed-state witness. Therefore current ICM MappingProxy deepcopy failure is explicitly a prerequisite failure and cannot be credited as dtype/ID RED or refusal success. Root's initial focused RED should use causal RND/adaptive cases; coherent ICM comparison follows the authorized production clone repair.

The existing parameterized owned native continuation test retains every positive state/RNG/next-real-update assertion and its before/after preparation purity observation. Observation advances the live owner's revision; the test now explicitly requires the first prepared token to raise ValueError('Prepared backend is already installed or its destination changed'), compares unchanged destination and ambient state, then prepares again and installs the fresh token without an intervening snapshot/call. The sequence applies to all three providers after their preparation prerequisite works. No WS stale guard was weakened and no positive assertion was removed.

Original214 cases, nine current-defect witnesses, exact two producer test names, real learning traces, private partition/idle controls and separate reachable overflow witnesses remain. There is no test_shared_runner_checkpoint_still_roundtrips stub/skip; actual integrated runner/native acceptance remains REQUIRED OPEN.

## Authorized static checks

`/workspace/hamlet/.venv/bin/black --config /workspace/hamlet/pyproject.toml /workspace/hamlet/tests/test_townlet/regressions/bac/test_pw_local_service.py`

Exit0: one file left unchanged.

`/workspace/hamlet/.venv/bin/ruff check --config /workspace/hamlet/pyproject.toml /workspace/hamlet/tests/test_townlet/regressions/bac/test_pw_local_service.py`

Exit0: All checks passed!

No pytest, project imports, provider edits, Git/index operations, branch/worktree/repository-copy/deletion or subagents occurred. Root owns focused RED and subsequent production repair clearance. Remaining source work identified by the brief—over-capacity preflight, raw Adam/ID validation, ICM policy-aware off-side copying, the owned typing error and four structural default ternaries—is not represented as fixed by these tests. External callers/POP/ordinary runner/native and final gates remain required.
