# PW04 source fix round 1: sealed production repair

Status: stationary repaired candidate for root-owned ICM prerequisite check, full262 execution, guards and same-reviewer actual-source rereview. No candidate runtime PASS is claimed. Implements the finite PW04-R1-FIX-brief.md material findings and required prerequisite/typing/default repairs, after root verified causal RED and closed all runtime. Current review SHA52e89742e0ad6acf4d7d254080a0aab94b0458f95533a852c0c02f88906d44b6 is root-confirmed append-only successor to original8b3e81b4454fda2a9526a6c67c43b521322280af2744a0dca260db84a6e2908e.

Root's attributed R2 evidence:262 collected; new48 FAIL in49.2004s, classified36 actual causal failures (12 bounded over-capacity spies,16 RND/adaptive raw-moment cases,8 RND/adaptive ID aliases) plus12 ICM comparison prerequisites blocked at pristine MappingProxy deepcopy (8 moment/4 ID), not credited as additional validator defects. Separate corrected owned sequence2 PASS in5.5663s proved stale-token refusal followed by fresh preparation/installation for RND/adaptive. Root verified193 source/573 config/13 artifact/3 process/index/import/Torch1/14 registry with MAIN1 available. This author ran none of those processes.

## Sealed whole-file inventory

| Path | Lines | Bytes | SHA256 | Ceiling |
| --- | ---: | ---: | --- | ---: |
| src/townlet/exploration/rnd.py | 834 | 41220 | 0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d | 1000 |
| src/townlet/exploration/icm.py | 481 | 27406 | eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f | 750 |
| src/townlet/exploration/adaptive_intrinsic.py | 315 | 14372 | cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 | 500 |
| tests/test_townlet/regressions/bac/test_pw_local_service.py | 1412 | 58793 | 3dcc780c36c15b553272246ac605f9ca6a89cbd732f0142552fd1ee0df4f9dc7 | 1800 |

Actual4/3042, approved named ceilings4/4050, hard5/5000. Adaptive source and all262 regression cases/assertions/new owned protocol remain byte-identical to the tests-first seal. RND and ICM are the only production edits. No extra helper/source, copied repository, new branch/worktree or deletion occurred.

## Repairs and covering rationale

R1-S1: RND admit_and_service_at now checks existing buffer occupancy against validated resolved capacity before clock/counter mutation or any service callback. Over-capacity input raises ValueError. Both explicit shared admit_and_service and configured update reach this preflight; adaptive delegates the real RND path. No service algorithm/drop ordering changed. Public update_predictor continues substantive one-minibatch direct training without this bounded-admission cap, and unconfigured direct tails remain supported. The12 bounded forward/Adam-spy regression cases cover all selected overflow policies and both shared entrypoints without executing the former unbounded loop.

R1-S2: raw optimizer state is validated before Adam.load_state_dict can coerce tensors. For each exact saved group/parameter pair, check the original moment dictionary/required fields; dense concrete CPU/CUDA tensor layout; original shape and parameter dtype; finiteness; scalar floating nonnegative integral step; and nonnegative exp_avg_sq/max_exp_avg_sq. Check full dense coverage and common step. Only then load the off-side optimizer. Loaded optimizer state and disposable execution-probe state/parameters also receive finite checks, supplementing rather than replacing raw validation. This closes float64/int/bool normalization, finite1e300 overflow and tiny-negative variance rounding paths while preserving valid actual LR/settings/offset and warm continuation. Adaptive inherits the repair through its actual nested RND. The16 causal RND/adaptive raw cases cover all three public native entrypoints; ICM's eight cases remain comparisons after its prerequisite repair.

R1-S3: raw optimizer state mapping keys now require type(identifier) is int before set membership/equality or loading, rejecting bool/integral-float aliases instead of normalizing them. Existing exact-int param_group checks and parameter ordering remain. Eight RND/adaptive alias cases and four ICM comparison cases exercise validate_state/prepare_state/load_state with full input/live custody. Exact-int warm positive controls remain.

ICM MappingProxy prerequisite: added a provider-owned __deepcopy__(memo) that reconstructs its frozen policy only through type(policy).from_dict(policy.to_dict()), memoizes that independent policy and the off-side backend, then deepcopies the complete attribute graph with the same memo. This preserves encoder/inverse/forward/Adam parameter-reference pairing and all native state without invoking random model construction or retaining an RNG owner. Native preparation seeds the memo with the already validated off-side policy rather than attempting to pickle the live mapping hierarchy. The hook also serves OwnedWorldBackend's external backend deepcopy. Root must first verify a lawful ICM native/owned continuation before crediting its malformed-state comparisons. No WS/RP source or private policy representation was inspected or modified.

Owned typing: renamed the RND constructor's second validation-loop locals to scalar_name/scalar_value, avoiding reuse of the int-inferred first-loop value for float configuration. No typing ignore/suppression was added. Mypy has not been run by this author; existing external caller errors remain separately required.

No-defaults: removed the four flagged structural ternaries. RunningMeanStd uses the NumPy array's actual size via int(x.size); RND and ICM service origin initialization uses explicit branches on the validated required unit; native RND options require a configured destination before accessing its model_dump. No default, whitelist, ratchet exemption or old-signature adapter was introduced. Constructor rng/unit remain required. Root owns verification that the default guard returns to its accepted <=601 bound; no actual guard PASS is asserted here.

## API and ownership receipt

There is no public constructor/service signature or native schema/key-set change in this round. Required explicit rng and service_clock_unit remain; shared None/vector_tick and private candidate RNG/world_eligible_admission are preserved. Current-only schemas remain rnd-state-v2 with predictor_service version2, icm-state-v2, and adaptive-intrinsic-state-v2, with exact fields documented in PW04-BACKEND-PRODUCTION-REPORT.md. Service unit/position/counters/budget, FIFO/drop conservation, positive-LR learning, complete optimizer/RMS/history/weight continuation and destination-bound single-install candidates remain the accepted contract.

RND/adaptive still use target/predictor allocation domains, with model_init/service unused for provider random draws; ICM still uses model_init for encoder then inverse and predictor for forward, with target/service unused. No new seed/domain, random reinitialization, copied model engine or retained RNG owner was added. ICM's copy protocol is the sole new Python copy hook; it transports the existing complete state through the documented portable policy ABI.

Prepared validation remains off-side. Raw Adam validation now precedes the coercing loader; all live installation still occurs only through checked prepared-candidate installation. Parent-wide atomicity, bank EventId/phase dedup and actual accepted ENV authority are not implemented by these local changes.

## Actual scoped static checks

Formatting command:

`/workspace/hamlet/.venv/bin/black --config /workspace/hamlet/pyproject.toml /workspace/hamlet/src/townlet/exploration/rnd.py /workspace/hamlet/src/townlet/exploration/icm.py /workspace/hamlet/src/townlet/exploration/adaptive_intrinsic.py /workspace/hamlet/tests/test_townlet/regressions/bac/test_pw_local_service.py`

Exit0:4 files left unchanged.

Final format check:

`/workspace/hamlet/.venv/bin/black --check --config /workspace/hamlet/pyproject.toml /workspace/hamlet/src/townlet/exploration/rnd.py /workspace/hamlet/src/townlet/exploration/icm.py /workspace/hamlet/src/townlet/exploration/adaptive_intrinsic.py /workspace/hamlet/tests/test_townlet/regressions/bac/test_pw_local_service.py`

Exit0:4 files would be left unchanged.

Lint command:

`/workspace/hamlet/.venv/bin/ruff check --config /workspace/hamlet/pyproject.toml /workspace/hamlet/src/townlet/exploration/rnd.py /workspace/hamlet/src/townlet/exploration/icm.py /workspace/hamlet/src/townlet/exploration/adaptive_intrinsic.py /workspace/hamlet/tests/test_townlet/regressions/bac/test_pw_local_service.py`

Exit0:All checks passed!

No pytest/project imports, mypy/default/qualification/CLI execution, Git/index/staging/commit/push, new branch/worktree, repository copy, deletion or subagents were performed. Only authorized source edits, scoped static tools and this ignored receipt were written/executed. Source/test hashes above are stationary for root's next checks.

## Required next evidence and limits

Root first verifies the ICM lawful preparation/owned-copy prerequisite, then the full262 candidate cases, relevant owner suites/coverage, six guards and same-Sol actual-source rereview/independent execution. RND/adaptive malformed-state RED is distinct from ICM prerequisite failure; these classifications must remain explicit in fixed-candidate results. Static checks alone do not establish the fix.

External required-constructor callers, current parent exact schema migration/dispatch/whole-parent prepare-commit, known external mypy errors, bank/context/lifecycle completion custody and actual ordinary runner/native save/load/next-real-update/deep-refusal qualification remain REQUIRED OPEN. test_shared_runner_checkpoint_still_roundtrips remains owned by the actual integration owner, never a backend stub/skip. CUDA and integrated PW04/BAC release are not qualified by this receipt. Original66 packets/28 releases and final gates remain unchanged.
