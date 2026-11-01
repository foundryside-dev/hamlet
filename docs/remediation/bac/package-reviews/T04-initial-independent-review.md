# T04 independent SPEC and QUALITY review — initial candidate

Verdict: changes required; not a final candidate PASS or whole-programme acceptance.

## Candidate and scope

- Repository: `/workspace/hamlet`; base HEAD `1f9d831a8fe76ab00e06774ef6888985f6c2aec2`; index tree `ca22c9f84e79828c8f6bc6b4a31a53a6e46ace75`.
- Candidate manifest: `wave03/green-r0-candidate.json` in this programme directory.
- `src/townlet/universe/declarations.py`: 695 lines; SHA256 `e2258ca225ef3ede13518718a1a456c1773e4d3118c5df688cd7ce8e72fa407f`.
- `src/townlet/universe/compiler.py`: 976 lines; SHA256 `521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92`.
- `tests/test_townlet/regressions/bac/test_sidecars.py`: 163 lines; SHA256 `7ded45feec744f52683eafd0287ec25440fcdc5f1241d9efd7415f609e965f69`.
- One independent scratch probe, `wave03/T04-independent-probe.py`: 119 lines. Total source inventory: 4 files / 1,953 lines. No additional implementation/test/helper sources inspected. Public DTO facts came from root; traceback output did not license additional source inspection.
- No production/test/index edits, commits, branches, worktrees, repository/source copies, or subdelegation. Probe fixtures copied native YAML DATA only into temporary directories.

## Evidence and attribution

Owner's work report attributes the original causal RED to root: 14 intended failures and 2 passing controls. This reviewer did not independently rerun RED.

Root's frozen-source GREEN receipt `/workspace/bac-review-2026-11-01/qualification/wave03-green-r0/T04-result.json` reports exit 0 for the original regression file; root supplied the 16-passed result. Receipt log: `/workspace/bac-review-2026-11-01/qualification/wave03-green-r0/T04.log`, SHA256 `18192f6b1ae0b16d50e902bf2dc558dfe05234c00f27bb46ee5ead797f2a19df`. Receipt duration is 62.75227165222168 seconds; root described pytest duration as 57.40 seconds. This reviewer reused that evidence rather than rerunning the original 16 tests.

Independent execution after explicit root freeze/authorization:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' .venv/bin/python .superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave03/T04-independent-probe.py > /tmp/T04-independent-probe.log 2>&1
```

Final probe exit: 0. JSON stdout is retained in `/tmp/T04-independent-probe.log`. The probe asserted HEAD, index tree, no unstaged tracked changes, and all three own source hashes before and after execution. It also asserted townlet imports resolve under `/workspace/hamlet/src`, torch thread count is 1, and CUDA visibility is empty. All identity assertions passed. An intermediate extension exited 1 on the existing downstream mixed-key restriction; identity was explicitly rechecked afterward and matched. The final revision caught and reported that restriction rather than assuming isolated mixed-key configurations fully compiled.

## Findings

### P2: Missing dictionary member and explicit null silently compare equal

Location: `src/townlet/universe/declarations.py:303`, `_refuse_sidecar_conflicts`.

The recursive dictionary comparison uses `top.get(field)` and `nested.get(field)`. For arbitrary recording criteria, this conflates missing members with explicit null members. Supply top-level `recording: {enabled: true, criteria: {leaf: null}}` and nested `training.recording: {enabled: true, criteria: {}}`. Both independently validate. Discovery and full authored compilation accept the duplicate and choose the top-level payload. Compiling the two alternatives separately produces unequal training hashes; compiling their duplicate produces the top-level hash. This violates the contract that conflicting duplicates refuse at both origins and demonstrates observable semantic identity loss, not merely dictionary formatting.

Final stdout: `missing_vs_null` outcome `accepted`; `missing_vs_null_full_compile` outcome `silently selected top-level; isolated alternatives have unequal training hashes`.

Repair must distinguish absent keys from explicit null, preserve supported criteria values, and emit a located collision for genuinely unequal mappings.

### P2: Nested mixed-key conflict raises raw TypeError

Location: `src/townlet/universe/declarations.py:302` (also ensure segment rendering at line 305 handles supported key types).

Top-level `recording.criteria.deep: {1: a, x: 2}` and nested `training.recording.criteria.deep: {1: b, x: 2}`, both with `enabled: true`, reach dictionary recursion. Sorting the union of integer and string keys raises `TypeError: '<' not supported between instances of 'str' and 'int'`. Full compile encounters the same raw TypeError in declaration normalization rather than a located CompilationError identifying the conflict origins.

Scope caveat: although the two isolated placements independently pass declaration discovery and the sidecar DTO, full compile later rejects each through the existing `ValueError: exploration authoring mappings require string keys`. The observed traceback places that restriction in `exploration_policy._freeze`; its source was not inspected. This finding establishes insufficient conflict diagnostics, not newly lost support for a fully working mixed-key configuration. Do not claim isolated full-compile success or use this evidence to authorize capability reduction.

Final stdout: `mixed_nested_key_types` outcome `TypeError`; isolated top/nested compile outcomes `downstream ValueError`; duplicate full compile outcome `duplicate raises TypeError during declaration normalization`.

## Passing independent controls

- Recording duplicate with omitted versus explicit `output_dir: null` is accepted.
- Metadata duplicate with whitespace-normalized equal output subdirectories is accepted.
- Unequal optional output directories and ordinary nested criteria leaves produce located CompilationError naming both origins.
- Null sidecar versus mapping produces a located conflict.
- Malformed list, integer, and string sidecars refuse even alongside a valid duplicate.
- Two malformed duplicates report both independently authored extra fields.
- Actual `use_cache=True` cache hit succeeds while stage 6 is mocked to raise on any recompilation, and retains training DTO/hash.
- Relocating both sidecars from nested to top-level retains training identity through cache invalidation/recompilation.
- Changing nested recording.enabled invalidates the cache, changes training hash, and preserves the new consumer value.

The original root GREEN additionally covers both sidecars separately/together/mixed, DTO and MessagePack round trips, equal-duplicate origins, and top-level controls. Those are root test evidence, not extra independent reviewer executions.

## Remaining work

Root has requested permanent regressions and causal RED before implementation repair. No runtime imports or reruns were performed while writing this report. Both conflict findings require repair and fresh review. Three known DS no-default lint violations at original lines 270, 307, and 312 are separately acknowledged, without waiver or ratchet change. No final candidate PASS is issued.
