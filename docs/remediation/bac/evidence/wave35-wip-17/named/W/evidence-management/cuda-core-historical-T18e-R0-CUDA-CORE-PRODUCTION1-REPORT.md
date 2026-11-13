# CUDA core production round 1 — frozen source/API/probe handoff

2026-11-13. Accepted production grant activated by root after R87 collection67, healthy3 PASS and missing-API3 RED, with scoped tests approval. This author implemented only the admitted two bodies below. No application/helper import, pytest/runtime experiment, mypy, Git/index/branch/worktree action, source execution copy, delegation, hardware access or producer integration was performed. Root owns actual qualification, public-consumer type checks and independent source review.

## Frozen whole bodies and actual development checks

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/exploration/rng_custody.py` | 809 | `8d63b963d39537281dc2f646edf5c1496fe33eef89357f7cafbbd19cc9ae6713` |
| `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py` | 1409 | `b044538dfe656976c0171d81fae4c3d44bba9b47f8b5072d846cfe2d9acf962e` |

Two current whole bodies2218, within individual core1200/test1800 and projected total3000, hard5/5000. No new source/helper body was acquired. The original core371 and test-fix1 1363 were the input; the test change is solely the justified direct-state observation described below. Selector names, parameter cases and exact ten-role/target/message map are unchanged; expected67 collection remains subject to root's actual new-byte collection.

Actual authorized development checks:

- `/workspace/hamlet/.venv/bin/black --line-length 140 <core>` applied formatting during development.
- Final `/workspace/hamlet/.venv/bin/black --check --line-length 140 <core> <test>`: both files unchanged, PASS.
- Final `/workspace/hamlet/.venv/bin/ruff check <core> <test>`: all checks passed.
- Whole-body `wc -l`/`sha256sum` yielded the table. A targeted textual lock/registry search verified the paths enumerated below; no runtime outcome is inferred from it.

No actual GREEN, isolated-child/fork result, real CUDA initialization/completion result or downstream replay behavior is claimed. R87 RED belongs to root's earlier frozen source and is not a result on these new bytes.

## Accepted-contract implementation map

- One existing sole `process_rng_domain()` still owns the actual RLock, membership, weak retirement, operations, tokens and common first-cause poison. Opaque gate/contract identities have no writable instance authority slots; constructor/reinitializer, shallow/deep copy and serialization refuse. Gate authority lives only in the sole domain's open `_gates` registry.
- Existing `operation(*, participant, operation_kind, lineage)` remains the full-member operation. Separate required `device_operation` shares its real participant pinning, lineage, ordinary-kind currency, revision, current-token and completion-union algorithm. It validates the exact sorted/unique tuple as initialized subset of enrolled membership before body effects. Its selected tuple completes at nested exit and contributes to the outer union. Full-member empty CPU and subset-empty CPU routes access no CUDA attributes. No added default, overload or omission compatibility mechanism exists.
- `admission` holds the same actual domain lock across the complete gate scope. None requires idle same-thread custody; active entry requires the exact authentic lineage. Its gate creates no operation/token/draw authority. Idle enrollment replaces only the immutable `_Member` record's exact union, keeping participant, weak owner reference and entrypoint identity. Real expansion increments generation once; no-op union does not. Enrolled owners are strongly pinned to gate exit as well as normal operation pinning.
- Healthy idle CUDA resolution structurally validates a `torch.device` CUDA selector before querying runtime. It explicitly initializes only when needed, advances currency once immediately before the first actual attempt, never fabricates an operation exit/revision and resolves unindexed selection afresh. Successful first init followed by invalid index retains READY and currency invalidation without enrollment/publication. Already-initialized verification/no-op resolution preserves preparations. Unexpected query/init failures clear readiness, retain first cause and propagate the original exception; ordinary argument/index refusal does not itself poison. No seeding, draw, RNG snapshot, guessed index or device-count-wide enrollment was added.
- The frozen `_LocalCUDARecord` and immutable `_LOCAL_CUDA_CONTRACTS` manifest bind each identity to one exact owner class and source route/input/rationale/healthy/post-poison policy. **Production manifest is empty**, with no generic exported GPU constant and no public issuer/registration/purity parameter. The admitted CPU fixture alone supplies one controlled record by private monkeypatch. Actual route enablement, fixed canonical class resolution where needed and producer dispatch remain later reviewed source work.
- Local entry authenticates participant, exact contract and exact `type(owner) is policy.owner_type`, pins that same instance and retains its complete binding. Healthy-use permission is required. Common poison additionally requires previously established READY and the individual post-poison policy; unknown runtime cannot be verified/bootstrapped through that route. Local resolution cannot initialize under an active parent. No successful ordinary local gate work changes core generation/revision/currency; producer mutation revision remains producer-owned. Local helpers reuse their scope; unrelated gate/operation/membership reentry is refused.
- One local `complete` context validates/arms the exact tuple before yielding, performs every declared synchronization in stable order on success or body failure and permits no repeated/overlapping scope or mid-work resolution. Empty completion performs no CUDA query/completion. An unfinished escaped completion makes gate exit refuse/poison rather than claim success. The authentic outcome marker remains inspectable while owner exclusion is held for the producer's quarantine step.
- Gate failure reporting needs no fabricated operation. It retains first poison cause and records distinct failure identities on any genuine active parent. Local completion continues all declared indices, preserving primary/body and distinct completion identities. Shared raising filters repeated exception leaves while retaining unchanged original exception groups; a clean body-only failure is re-raised as that exact exception. Parent exit combines propagated local errors, its normal cleanup and reported causes without duplicating identities. Generic operation completion retains its current normal failure policy; this change does not make its early-stop suffix an API requirement.

## Exact public typed surface

Every listed argument is required. Context-manager functions are annotated as `Iterator[T]` generators under `@contextmanager`; their typed public calls return context managers yielding T.

| Public callable | Parameters | Yield/result |
| --- | --- | --- |
| `AmbientRNGDomain.operation` | keyword `participant: RNGParticipant`, `operation_kind: str`, `lineage: RNGOperation | None` | yields `RNGOperation` |
| `AmbientRNGDomain.device_operation` | same required three plus keyword `cuda_devices: tuple[int, ...]` | yields `RNGOperation` |
| `AmbientRNGDomain.admission` | keyword `lineage: RNGOperation | None` | yields `RNGAdmission` |
| `RNGAdmission.resolve_cuda` | positional-or-keyword `device: torch.device` | `int` |
| `RNGAdmission.enroll` | keywords `participant: RNGParticipant`, `cuda_devices: tuple[int, ...]` | `None` |
| `RNGAdmission.report_failure` | keyword `error: BaseException` | `None` |
| `AmbientRNGDomain.local_cuda_access` | keywords `participant: RNGParticipant`, `contract: LocalCUDAContract` | yields `LocalCUDAGate` |
| `LocalCUDAGate.resolve_cuda` | keyword `device: torch.device` | `int` |
| `LocalCUDAGate.complete` | keyword `cuda_devices: tuple[int, ...]` | yields `None` |
| `LocalCUDAGate.completion_failed` | none | `bool` |
| `LocalCUDAGate.report_failure` | keyword `error: BaseException` | `None` |

Existing `current_token`, `validate_current`, registration, poison and diagnostics signatures remain. Existing same-held versus released operation revision/currentness and genuine nested currency rule remain. `status()` is still blocking diagnostics, never admission or an owner-lock-safe guard. Root's independent public-consumer static type probe remains required; no runtime annotation-spelling assertion substitutes for it.

## Actual PID, scope, readiness and registry fields

`_pid` is actual constructor `os.getpid()` and is never patched by production/tests. `_check_pid` compares it to actual `os.getpid()` and raises exact built-in **RuntimeError**, exact **`RNG custody cannot be inherited by another process`** before any other new-gate effect. Both new domain context entries run it before acquiring their real lock. Every new gate method reaches `_gate_record` first, which runs it before registry/thread/lineage/owner/policy/lock-ownership or CUDA checks. Actual context-manager entry executes this check; construction alone is not a witness. Original register/unregister/adoption/operation/current-token/validate-current also now check PID before their public lock entry. `status` and existing operation `poison` remain diagnostic/operation-specific paths, not the proposed fork guard actions.

Actual state additions:

- `_gates: dict[RNGAdmission | LocalCUDAGate, _Gate]`: presence authenticates the unique open capability. Removal expires it; there is no copied gate state on the capability object.
- Each `_Gate`: `thread`, `lineage`, `participant`, `owner`, `contract`, `policy`, `pins`, `completion` (`unused`, `active`, `done`) and `failed_completion`. Admission has no local binding; enrollment populates pins. Local scope binds the exact member/owner/contract/immutable-policy identity and checks it on every later method. A supplied entry lineage remains authenticated while active. Local gates under a genuine parent retain that actual lineage without inventing one for public ambient consumers.
- `_cuda_ready: bool`: healthy successful initialized-runtime verification/bootstrap establishes it. Observed uninitialized or uncertain runtime clears it. This is a readiness fact, not a member inventory/token/route purity proof. Ordinary successful local scope entry does not change currency. No unknown readiness is established after poison.
- `_cuda_busy: int | None`: actual issuing thread during initialization/runtime inventory queries/enrollment checks and local completion synchronization. Same-thread unrelated initialization/membership/operation reentry refuses. Another thread still waits at the actual RLock. The guard is reset in `finally` and never borrowed as lineage.
- `_Operation.reported: list[BaseException]`: source-authenticated gate/runtime failures under the actual active operation, unique by exception identity. Existing operation fields `thread`, `generation`, `revision`, `participants`, `kinds`, `pins`, `devices`, `issued` remain.

Existing lifecycle fields are `_generation`, `_revision`, `_currency`, `_ambient_revision`, `_poison`; existing registries `_members`, `_operations`, `_tokens`, `_retired` and issuing-thread `_local.operation` remain sole-owned. First-init invalidation changes `_currency`, not `_revision` or a fake ambient sampling commit. Healthy verification/no-op enrollment can establish READY without minting token authority.

## Final actual-lock probe coverage and justified fixture delta

Every actual domain lock acquisition still uses **`with self._lock`**. There is no raw lock cache/alias, direct `.acquire`, Condition path or `_acquire_restore` in this809-line body. `_gate_record` additionally calls only `self._lock._is_owned()` to authenticate continuing actual exclusion; it does not acquire the lock. The finite `LockProbe` already installed before genuine gate entry forwards these routes to the same actual RLock, counts acquisition once and forwards real ownership. No actual source route bypasses that probe. The new core never acquires an owner lock; producer fixtures separately install a forwarding probe on their actual RLock. No lock is fabricated or replaced by fake ownership.

The sole test delta changes `guard_state` plain observations to match actual new source. It now snapshots each `_Gate` registry key/record identity and every field listed above, all `_Operation` fields including `reported`, `_cuda_busy`, direct `_local.operation` identity, member record/weakref/inventory/entrypoints identities, and token record identity/binding/generation/revision/currency. Existing actual PID/lifecycle/first-poison/readiness observations remain. No new action, role, selector, contract issuer or synthetic PID was introduced. No retired queue is drained and no domain diagnostic, import, Torch/NumPy/queue/pytest helper is called in the guard grandchild. Actual module objects/file hashing and plain state reads remain the approved guard-only profile.

Thus the previously provisional cache/state coverage now has this concrete source basis for independent review. It is **not actual fork proof**: root must still run the exact source-qualified witness and verify measured counters, real single-thread applicability, complete ancestry/import/hash/manifest coupling and strict extra-record refusal. All ten role mappings, two exact fork action maps and schemas in the tests fix1 report remain in force with this new test hash; older receipts cannot be reused as current-source evidence.

## Freeze and remaining qualification

Writer relinquishes the sole source baton at the table hashes. No specific accepted-contract ambiguity remains known from this bounded implementation pass. All runtime behavior on new bytes is UNRUN by this author. Root must capture/collect, run phase controls and required existing core/BANK regression gates, execute the public typed consumer check, obtain independent actual-source review and independently reapprove strict child tooling before any qualified child/fork execution. Poison/failure children must remain isolated; real Torch initialization/query RNG effects, asynchronous completion and one-/two-device hardware controls remain separate and required.

No local production GPU leaf is enabled, no replay/parent caller was migrated and no real CUDA execution or B6/R0/B1/package closure is claimed. Preserve these first production-attempt bytes as inert evidence before any later fix round.
