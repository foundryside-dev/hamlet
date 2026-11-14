# PW04 outer native RNG owner

2026-11-14. Work in progress; no production module or execution yet. Root owns qualification. Existing branch/checkouts only; no Git, runtime, source copies or new worktrees performed by this owner.

Inventory: `exploration/rng_custody.py` 1195 lines; `exploration/action_selection.py` 120; `tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py` 900; new `test_native_rng_state.py` 99. The new implementation is reserved as the fifth body, within 5000 cumulative lines. Transitive fixture and POP/C implementations were not opened; their APIs below are supplied by their source owners.

## Portable state and receiving profile

The agreed `native_boundary.rng_state` is exactly `{schema: 'native-rng-v1', torch_cpu: tensor, torch_cuda: {index: tensor}}`. Every tensor is an owned ordinary contiguous one-dimensional CPU uint8 vector. CUDA keys are exact nonnegative integers (not bool), exactly matching the explicitly declared sorted receiving CUDA inventory. CPU is always represented because actual ENV placement and flat replay use CPU Torch; selected action operations use their actual tensor device. Action selection source uses global Torch rand, randint and multinomial. Root's bounded search of runner/ENV/POP/curriculum found no Python/NumPy global draw; explicit replay NumPy generators remain replay child state. This is not a whole-repository transitive randomness audit or GPU qualification.

`validate_native_rng_payload(payload, *, cuda_devices)` will be a pure structural validator without domain operation, admission, CUDA, generator construction or state mutation. `NativeRNGState.validate_payload(payload)` will additionally clone and validate state bytes using detached CPU and declared-device generators under actual domain device custody. No global generator is changed by validation. Malformed bytes and wrong receiving profile refuse before child publication.

## Intended source-owned route

Construct the helper before child sealing, with explicit CUDA inventory; resolve/enroll devices using actual domain admission. `capture()` returns owned portable state under a real device invocation. No portable token, private stream/bootstrap rewind or invented world role is involved.

`prepare(payload, *, parent, parent_plan)` must verify the actual VectorizedPopulation and its source-issued data plan, then retain owned validated payload in an opaque source-issued data record pinned to helper revision, exact parent/plan, PID and issuing Thread. It has no ambient current token or install permission, so unrelated legitimate BANK operations do not manufacture or stale its nonexistent authority.

`install(*, prepared, parent_plan, attempt, restored)` must authenticate the genuine data record, unchanged receiving parent/plan and C finalizer. It then uses a fresh actual domain device install invocation, consumes the one-use record, sets CPU and explicit CUDA generator states, and records actual ambient publication. An exception after publication begins is uncertain/partial: poison the actual domain and let the genuine C attempt fence the receiver; never rollback or return success. Actual device completion remains required.

POP supplier API: `validate_native_population_data(*, plan, owner=actual_population)` authenticates source issuance, actual registry, PID/Thread/revision and pinned role/parameter identities; it does not require fresh ENV phase during FINALIZING. Keep POP revision and plan live until RNG installation completes. Native finalizer consumes/advances them afterward.

C supplier API: `validate_restore_finalizer(*, attempt, owner=actual_population, restored)` authenticates exact live source-entered FINALIZING callback and installed world/release. Repeated genuine child validations do not consume a shared owner allowance. After the fixed callback C performs metadata/escrow/gate-exit work only, without RNG draws. RNG must therefore be the last native child installation, after all other construction/materialization/publication that might draw.

## Evidence owed

Sixteen initial RED nodes are authored in `test_native_rng_state.py`, frozen for root execution: owned capture, side-effect-free structural and semantic validation, seven malformed payloads, forged parent refusal and five invalid device inventories. Tests import the not-yet-existing module inside bodies, preserving collection. No result is claimed.

Positive staged-plan/one-use/refusal controls will use actual ParentFixture plus native POP plans. Successful global-state restore and resumed action/sample/learning require the real native POP/C path and original DemoRunner acceptance. C's component journal and identity-only owner fixture cannot substitute for that proof. CPU component tests do not qualify CUDA; device checks remain explicitly owed.

## R161 implementation handoff

Root reports all sixteen initial nodes failed for the intended missing native_rng module on exact R161; collection and execution custody passed. After that source-qualified RED, implementation was authorized and written. New `src/townlet/training/native_rng.py` is 212 lines; test file is now 137, with two additional genuine POP plan controls (staging without rewind, foreign-finalizer refusal, noncopyability and reassociation refusal). Those two controls are unrun, not claimed observed RED. Total five complete bodies: 2564 lines.

Implemented the API above, including pure schema validator, explicit-device admission/registration, owned capture, detached-generator compatibility validation and genuine parent-bound staged data. Install uses the actual POP validator and C finalizer hook, checks private registry/PID/Thread/revision/exact plan identity, consumes once only after invocation entry, performs real CPU then declared CUDA setters, and calls the domain's actual ambient-commit marker. Any setter/publication exception poisons the actual domain without rollback. Actual device completion remains owned by the core invocation. Ordinary capture/validation/staging never changes global RNG bytes.

Source and tests are frozen/write-ready for root static/runtime qualification. No imports, tests or formatter were run by this owner. Successful native C finalization, exact continued action/sample/learning, foreign-thread/stale/consumed controls, actual poison-child failure evidence and CUDA remain owed. These are not silently covered by the initial capture/refusal tests.

## R162 qualification and R163 independent P2 repair

Root reports all 18 native RNG component cases passed on R162 with custody PASS. This does not establish native finalizer success or runner continuation. Independent Astra review then identified a real P2: an exact ordinary Tensor can carry per-instance `clone` or `is_contiguous` overrides, so exact-type checking alone allowed callbacks and clone aliases.

Four regressions were added across the pure schema and semantic ownership routes. Root reports all four failed as intended (`DID NOT RAISE ValueError`) on R163 candidate `34d6bace`, with custody PASS. The fix rejects any per-instance attributes using `object.__getattribute__(tensor, '__dict__')` before any tensor method; subsequent contiguity and clone operations use canonical unbound Tensor methods. Honest input ownership remains unchanged.

Fixed implementation is 219 lines, SHA256 `cc0959e6deed8a5b57947ff456fcd838ee3762fc2a530c30dcf3cc197f073088`; tests are 164 lines/22 nodes, SHA256 `feab54a5a88ccc68de4602179930c768bc1a6077b01573b9a24d71bdb79d231f`. Five-body cumulative inventory is 2598 lines. Source is frozen for root rerun and independent fixed-source review. No new GREEN claim or package closure is made.
