# Invocation outcome — tests-only handoff

Current stage: **PRODUCTION CORE AUTHORED AND FROZEN; STATIC PASS; RUNTIME GREEN UNEXECUTED.** The original tests-only record below is retained. The production-only handoff and actual supplier facts are appended after it; the immutable tests-only snapshot retains seal `7054f6a3e31c881dfd86842d99bea16724c9736fca3366762ef0ec409618878a`.

2026-11-13. Status: **TESTS AUTHORED; RUNTIME/RED UNEXECUTED; PRODUCTION FROZEN.** Worker `/root/bac_core_invocation_impl` acted under `wave35/r104-core-invocation-tests-grant.json` SHA256 `52616d9cc9ed4a65bc457de6d4dca102bb7eb1706562adadaef4ce1741259ad2`. Adopted DESIGN-FIX1 and bounded IMPLEMENTATION-MAP remain the requirements; this stage does not reopen the design.

## Frozen bytes and budget

- Writable test: `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`, 1681 lines, SHA256 `ccc74e6bac55f322d3363ac1e19c820b2b97b0d86839b392dfabedb452647a38`.
- Unchanged production: `src/townlet/exploration/rng_custody.py`, 821 lines, SHA256 `0a0f19d37ac85b1584ea028e7e7268a04d18e9f39db0e41b9780181913aae477`.
- Two retained bodies total 2502 lines, below paired ceilings 1250/2000/3250 and hard ceiling five bodies/5000 lines. No other implementation body was read.
- Baseline test SHA256 `b044538dfe656976c0171d81fae4c3d44bba9b47f8b5072d846cfe2d9acf962e`; the HEAD test blob hashes identically. Inert diff: `T18e-R0-CUDA-INVOCATION-OUTCOME-TESTS-ONLY.diff`, from that baseline, 274 added / 2 replaced import lines. Existing test bodies and empty-production-manifest assertion are preserved.
- Inert diff SHA256 `73be274ebfc2d21319579739c19a61934edb39e1123f390ddef51e6a5015a001`.

## Exact proposed node map

Every ID below has prefix `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py::`. These are authored node names, not a claim that collection succeeded.

| Category | Node suffix | Observable break caught |
| --- | --- | --- |
| OUT-API-RED | `test_device_invocation_required_api` | Missing/optional factory inputs; wrong context/yield/exit/getter types; public construction. |
| OUT-LIFETIME-RED | `test_device_invocation_historical_result_preserves_real_token_and_retirement` | Issuance currency change; replacement lineage; broken genuine token flow; receipt depending on active operation/membership or lock acquisition. |
| OUT-AUTH-RED | `test_device_invocation_lifecycle_refusals_leave_completed_result_stable` | Premature False, duplicate enter/exit, reuse, or refusal corrupting a valid lifecycle/result. |
| OUT-AUTH-RED | `test_device_invocation_entry_failure_has_no_outcome_or_reuse` | Participant retirement between issuance/entry bypasses admission, or failed entry publishes a result/reusable handle. |
| OUT-AUTH-RED | `test_device_invocation_issuance_rejects_forged_arguments_without_cuda` | Unissued participant/lineage, malformed kind/inventory, or mutable inventory gains issuance authority. |
| OUT-AUTH-RED | `test_device_invocation_unissued_subclass_and_copy_refuse` | Unissued/subclass/copy/serialization/attribute forgery or reinitialization gains authority. |
| OUT-AUTH-RED | `test_device_invocation_wrong_thread_refuses_before_held_locks` | Wrong-thread enter/exit/getter waits for held real domain/owner exclusion, at issued/active/exited phases. |
| OUT-LIFETIME-RED | `test_device_invocation_unused_handle_does_not_pin_owner` | Construction pins a weak lifetime owner; expired owner nevertheless permits entry/outcome. |
| OUT-LIFETIME-RED | `test_device_invocation_completed_handle_releases_execution_references` | Completed body-error handle retains owner, operation, original error/generator/traceback cycle, or registry retains its weak key. |

New public names are looked up inside test functions. The existing module import at collection remains unchanged. Factory lookups precede owner registration where applicable so the intended missing API failure does not leave a newly registered owner behind. Empty-inventory controls use NoCUDA; reference tests use real weak owners/operations/errors and collection; token controls use actual source-issued current tokens. Wrong-thread controls use real threads with finite waits while actual domain/owner locks are held. No fake PID or test-issued production contract is introduced.

## Existing healthy CPU controls for root capture

Same full prefix as above:

- `test_existing_cpu_registration_and_completion_query_no_cuda` — preferred prerequisite healthy registration/completion control.
- `test_subset_cpu_path_never_queries_cuda` — existing device-operation empty-inventory parity control.
- `test_existing_released_prepare_install_currentness` — existing genuine token baseline.

Root owns exact-byte capture, actual collection, healthy control execution, and decisive missing-API RED against the frozen core821. None was executed by this worker; no fixture or RED result is claimed here.

## Static verification and execution boundary

Fresh authorized checks on final test bytes:

- `.venv/bin/ruff check tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`: exit 0, all checks passed.
- `.venv/bin/black --check tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`: exit 0, one file unchanged.
- `git diff --check -- tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`: exit 0.

Preserved attempts: bare `ruff` was unavailable in PATH (exit127), then the repository `.venv/bin/ruff` found one import-order issue; its correction precedes the passing final checks. No application import, test collection, pytest, GPU operation, child/fork protocol execution, index mutation, commit, branch/worktree/copy, other source-body read, or delegation occurred. The report/diff are inert handoff artifacts requested by root.

## Next grant boundary

Production remains unchanged until root supplies fixture-healthy causal RED and a production-write grant. Separate later work still owes nonempty success/own-phase failures, same-object body/completion error identity, nested/sibling/token parity, deterministic thread-object alias controls, actual registry/state/reference and lock-path facts, isolated schedules and exact child/fork verifier admission. Public consumer typing and real parent-owner handoff remain root/separate-owner obligations. These nine controls do not claim CUDA hardware, producer integration, B activation, B6, or programme closure.

## Production-only handoff

Authorization: `wave35/r105-core-production-grant.json` SHA256 `92356eebf7237fc05a844729c386e9af1d3f32696eb78ad1a4356c318e2657ff`. Root's exact-byte prerequisite is `wave35/r105-core-tests-disposition.json` SHA256 `39ec104b8f76467fe5ffc50df5f5e920a1bf86a6adf200875859fb2f6c21d9ea`: candidate tree `dc16ff43ae9ad5aa1bd3ca63904fe37c150a38e7`, manifest `f358fe37d8e01925761eedfdd181c4bbce24c6b3e02fe04634487b01db2b7dc9`, 76 collected, three healthy CPU controls passed, nine new controls failed only at their initial missing API lookups, zero fixture errors. These are root-supplied dispositions, not worker-executed results.

Before changing production, preserved `T18e-R0-CUDA-INVOCATION-OUTCOME-TESTS-ONLY-REPORT.md`, SHA256 `7054f6a3e31c881dfd86842d99bea16724c9736fca3366762ef0ec409618878a`. Only the authorized core implementation body changed during this stage. The test remains frozen at SHA256 `ccc74e6bac55f322d3363ac1e19c820b2b97b0d86839b392dfabedb452647a38`.

Frozen core: 948 lines, SHA256 `ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e`. Paired core/test: 2629 lines, two retained bodies, within all stated ceilings. Exact inert diff against the unchanged core821 baseline is `T18e-R0-CUDA-INVOCATION-OUTCOME-CORE.diff`, SHA256 `920a105e28330dbf71d5fc34a56992c383ed3e1fdcbfb65d2498467fc29645b7`, 135 added / 8 replaced lines.

### Actual registry, lifecycle and execution-reference facts

- Public `RNGDeviceInvocation` at core59 is opaque and slotted. It supplies the exact `__enter__`, `__exit__ -> Literal[False]`, and `completion_failed -> bool` surface; context entry returns the genuine unchanged `RNGOperation`. Ordinary construction, reinitialization, copy/deepcopy and serialization share `_Opaque` refusals. Context-manager conformance follows its actual enter/exit methods; public consumer typing remains root-owned.
- `AmbientRNGDomain._invocations` at core216 is `weakref.WeakKeyDictionary[RNGDeviceInvocation, _Invocation]`. Each `_Invocation` stores `thread: threading.Thread`, `state: str`, `participant: RNGParticipant | None`, `operation_kind: str | None`, `lineage: RNGOperation | None`, `cuda_devices: tuple[int, ...]`, `context: AbstractContextManager[RNGOperation] | None`, and `failed_completion: bool`. Values contain no handle/key reference.
- Factory `device_invocation` at core675 checks actual domain PID, authentic participant, exact nonempty string kind, source-issued exact lineage identity when supplied, and immutable sorted/unique explicit inventory shape. It creates no operation/context and pins no owner, takes no exclusion, queries no CUDA, and changes no generation/revision/currency. Membership, entrypoint, poison, active-lineage, busy and runtime/inventory admission are repeated at real entry by the existing `_operation` path.
- `_invocation_record` at core691 checks `_check_pid` before exact class/weak-registry lookup, then compares `record.thread is threading.current_thread()`. Wrong-thread/forged calls raise ValueError before lock/owner/CUDA access. Issuing-thread object identity is stored, rather than a numeric ID or cached numeric-ID check. PID provenance remains the existing immutable domain `_pid`, checked against actual `os.getpid()` on each public path.
- States are `issued -> entering -> active -> exited`, or `entering -> entry_failed`. `_enter_invocation` marks entering before context creation/admission, active only after actual `_operation.__enter__` yields, and failed/cleared on every entry exception. Getter refuses every state except exited. Entry/exit misuse raises RuntimeError without modifying a valid result. Exit takes `record.context` into a local and clears the field before invoking it, so recursive exit refuses while state remains active and outcome unreadable; unconditional finally clears execution fields and seals exited before any outward error reaches the wrapper.
- `_release_invocation` at core702 clears participant, kind, lineage, device tuple and context at failed entry or terminated active exit. Historical registry records retain only issuing thread, lifecycle and result, plus empty/None execution fields. No original exception, traceback, owner, operation or generator is an outcome field. The generator temporarily receives the record through its explicit `completion` argument; the record temporarily owns that generator context only during entry/active execution and releases it at termination. Registry weak-key collection remains independent of completed result lifetime.
- `failed_completion` starts True (uncertified). Only successful return from this actual scope's `_complete` changes it to False, in `_finish`'s else clause at the call site. Errors/interruption before that success leave True. Sealing happens in `_exit_invocation`'s unconditional finally; internal faults continue outward. Getter does not inspect exception identity/structure, poison, reported failures, operation membership/currentness, or `_usable`.

### Actual shared-operation and lock facts

The only shared-operation addition is the required private `_operation(..., completion: _Invocation | None)` argument and matching `_finish(..., completion)` argument. Existing `operation` and `device_operation` wrappers pass explicit None; invocation entry passes its own private record. No new `_Operation` fields, public callback, duplicated operation algorithm, alternate draw authority, defaults, compatibility adapters or fallback paths were added.

Nested completion still receives its admitted subset. Outermost completion still receives `tuple(sorted(record.devices))`, the existing final union including descendants. `_complete` itself is unchanged: the generic loop still stops at its first synchronization exception. `_finish` preserves poison/report/exception aggregation; its sole observation is successful completion certification before later reported-failure aggregation. No retry or second pass exists. Local completion and all-declared-device behavior are unchanged. Empty completion has no CUDA attribute access. Existing `_raise`, admission, local contracts and the empty production contract manifest are unchanged.

There is no new lock acquisition, lock cache, ownership cache, or owner-lock path in issuance, authentication, historical getter, or release. Actual operation entry obtains the existing `_operation` real domain RLock; existing operation exit and `poison` retain their prior acquisitions and ordering. No owner exclusion is acquired by the new API. Producer custody through completion/read/transition remains the producer's obligation. Historical reads use only actual PID, exact handle issuance, issuing thread and exited-state checks, including after poison/member retirement; they neither acquire `_lock` nor call `_is_owned` or CUDA. Existing forwarding LockProbe therefore remains the relevant acquisition probe, but root's future guards must observe this actual invocation registry, its eight fields, and active generator `completion` argument/context reference before claiming expanded state coverage.

### Exact static evidence on final core bytes

All three commands exited zero; logs are retained beside this report:

| Command | Actual output | Log SHA256 |
| --- | --- | --- |
| `.venv/bin/ruff check src/townlet/exploration/rng_custody.py` | `All checks passed!` | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` (`...-CORE-RUFF.log`) |
| `.venv/bin/black --check src/townlet/exploration/rng_custody.py` | `All done!` / `1 file would be left unchanged.` | `1a56c7cd8457fd05d978cfbd139d7bfd86e86acaa9b57668e718ef8bccc0cf48` (`...-CORE-BLACK.log`) |
| `.venv/bin/mypy src/townlet/exploration/rng_custody.py` | `Success: no issues found in 1 source file` | `5d4b6d285b77932e3d08212c3b4974d0a803f98ec60408ac6ccf6a063fa6c19e` (`...-CORE-MYPY.log`) |

`git diff --check -- src/townlet/exploration/rng_custody.py` also exited zero. Earlier exploratory static command `.venv/bin/mypy --follow-imports=skip src/townlet/exploration/rng_custody.py` failed at unchanged `_resolve_cuda`'s `return device.index` (new line572), since skipping torch typing makes that attribute Any. Plain configured mypy then passed, with no source change, type ignore, weakened annotation, altered default or suppression. The failed static attempt is preserved here and is not relabeled as a pass.

No application execution/import, pytest, child/fork runtime, test/verifier edit, other implementation-body read, index mutation, commit, branch/worktree/source copy, or delegation occurred in production stage. The explicitly authorized inert tests-only report snapshot is the sole copied artifact. Root must now independently review/qualify these exact bytes. Expanded nonpoison/isolated schedules, exact child/fork protocol mapping/verifier review, direct state and lock observations, public consumer typing/default guards, clone-stability P2 before B dependency, actual parent-owner handoff, real hardware and broader package obligations remain open.
